import pytest
import subprocess
import os
import sys
from unittest.mock import patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_fancygit():
    """Instantiate FancyGit with mocked file/config dependencies."""
    with patch.object(FancyGit, '_load_commands', return_value=['undo', 'redo']):
        with patch('src.config_manager.ConfigManager'):
            fg = FancyGit()
            fg.confirmation_enabled = False  # skip interactive prompts in all tests
            return fg


def _commit_file(repo_dir, filename, content, message):
    """Helper: write a file, stage it, and commit it in repo_dir."""
    path = os.path.join(repo_dir, filename)
    with open(path, 'w') as f:
        f.write(content)
    subprocess.run(['git', 'add', filename], check=True, capture_output=True, cwd=repo_dir)
    subprocess.run(['git', 'commit', '-m', message], check=True, capture_output=True, cwd=repo_dir)


def _current_commit_msg(repo_dir):
    """Return the subject of the current HEAD commit."""
    result = subprocess.run(
        ['git', 'log', '--oneline', '-n', '1'],
        capture_output=True, text=True, cwd=repo_dir
    )
    return result.stdout.strip()


def _reflog(repo_dir, n=10):
    result = subprocess.run(
        ['git', 'reflog', '--oneline', f'-n{n}'],
        capture_output=True, text=True, cwd=repo_dir
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Unit tests  (mocked git commands — test logic paths only)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUndoUnit:
    def setup_method(self):
        self.fg = _make_fancygit()

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_undo_success_default_mixed(self, mock_git):
        """undo with no args does --mixed reset and returns True."""
        mock_git.side_effect = [
            (0, '.git', ''),                                        # rev-parse --git-dir
            (0, 'abc1234 second\ndef5678 first\n', ''),             # log -n 2
            (0, {'staged': [], 'modified': [], 'untracked': [],     # get_repo_state (no-op)
                  'clean': True}, ''),
            (0, '', ''),                                            # reset --mixed HEAD~1
            (0, 'def5678 first\n', ''),                             # log -n 1 (new HEAD)
            (0, '', ''),                                            # status for repo_state
        ]
        # get_repo_state is a method, not a git command — patch it separately
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}

        mock_git.side_effect = [
            (0, '.git', ''),
            (0, 'abc1234 second\ndef5678 first\n', ''),
            (0, '', ''),                   # reset --mixed HEAD~1
            (0, 'def5678 first\n', ''),    # log after reset
        ]

        result = self.fg.undo()

        assert result is True
        reset_call = call(['reset', '--mixed', 'HEAD~1'])
        assert reset_call in mock_git.call_args_list

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_undo_hard_flag(self, mock_git):
        """undo --hard passes --hard to git reset."""
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, 'abc1234 second\ndef5678 first\n', ''),
            (0, '', ''),
            (0, 'def5678 first\n', ''),
        ]

        self.fg.undo('--hard')

        reset_call = call(['reset', '--hard', 'HEAD~1'])
        assert reset_call in mock_git.call_args_list

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_undo_not_a_git_repo(self, mock_git):
        """undo returns False when not inside a git repository."""
        mock_git.return_value = (128, '', 'fatal: not a git repository')

        result = self.fg.undo()

        assert result is False

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_undo_only_one_commit(self, mock_git):
        """undo returns False when there is no previous commit to undo to."""
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, 'abc1234 initial\n', ''),   # only one commit in log
        ]

        result = self.fg.undo()

        assert result is False

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_undo_git_failure(self, mock_git):
        """undo returns False when the underlying git reset fails."""
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, 'abc1234 second\ndef5678 first\n', ''),
            (1, '', 'error: something went wrong'),
        ]

        result = self.fg.undo()

        assert result is False


@pytest.mark.unit
class TestRedoUnit:
    def setup_method(self):
        self.fg = _make_fancygit()

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_redo_not_a_git_repo(self, mock_git):
        """redo returns False when not inside a git repository."""
        mock_git.return_value = (128, '', 'fatal: not a git repository')

        result = self.fg.redo()

        assert result is False

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_redo_no_undo_in_reflog(self, mock_git):
        """redo returns False when there is no reset in the reflog."""
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, 'abc1234 HEAD@{0}: commit: add feature\n'
                'def5678 HEAD@{1}: commit: initial\n', ''),
        ]

        result = self.fg.redo()

        assert result is False

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_redo_finds_target_and_resets(self, mock_git):
        """redo finds the pre-undo commit in reflog and calls reset --hard on it."""
        reflog = (
            'aaa0001 HEAD@{0}: reset: moving to HEAD~1\n'
            'bbb0002 HEAD@{1}: commit: second commit\n'
            'ccc0003 HEAD@{2}: commit: initial\n'
        )
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}
        mock_git.side_effect = [
            (0, '.git', ''),            # rev-parse
            (0, reflog, ''),            # reflog
            (0, 'commit', ''),          # cat-file -t bbb0002
            (0, 'aaa0001 reset\n', ''), # log -n 1 (current HEAD)
            (0, 'bbb0002 second\n', ''),# log -n 1 bbb0002 (target)
            (0, '', ''),                # reset --hard bbb0002
            (0, 'bbb0002 second\n', ''),# log -n 1 after reset
        ]

        result = self.fg.redo()

        assert result is True
        reset_call = call(['reset', '--hard', 'bbb0002'])
        assert reset_call in mock_git.call_args_list

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_redo_already_at_target(self, mock_git):
        """redo returns True immediately when HEAD is already at the target commit."""
        reflog = (
            'bbb0002 HEAD@{0}: reset: moving to HEAD~1\n'
            'bbb0002 HEAD@{1}: commit: second commit\n'
        )
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, reflog, ''),
            (0, 'commit', ''),           # cat-file
            (0, 'bbb0002 second\n', ''), # current HEAD
            (0, 'bbb0002 second\n', ''), # target commit info
        ]

        result = self.fg.redo()

        assert result is True
        # reset --hard should NOT have been called
        for c in mock_git.call_args_list:
            assert c != call(['reset', '--hard', 'bbb0002'])

    @patch('src.git_runner.GitRunner.run_git_command')
    def test_redo_reset_fails(self, mock_git):
        """redo returns False when git reset --hard fails."""
        reflog = (
            'aaa0001 HEAD@{0}: reset: moving to HEAD~1\n'
            'bbb0002 HEAD@{1}: commit: second commit\n'
        )
        self.fg.get_repo_state = lambda: {'staged': [], 'modified': [], 'untracked': [], 'clean': True}
        mock_git.side_effect = [
            (0, '.git', ''),
            (0, reflog, ''),
            (0, 'commit', ''),
            (0, 'aaa0001 reset\n', ''),
            (0, 'bbb0002 second\n', ''),
            (1, '', 'error: reset failed'),
        ]

        result = self.fg.redo()

        assert result is False


# ---------------------------------------------------------------------------
# Integration tests  (real git repo via temp_git_repo fixture)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestUndoRedoIntegration:
    """End-to-end tests against a real temporary git repository."""

    def _make_fg(self):
        with patch.object(FancyGit, '_load_commands', return_value=['undo', 'redo']):
            with patch('src.config_manager.ConfigManager'):
                fg = FancyGit()
                fg.confirmation_enabled = False
                return fg

    def test_undo_moves_head_back(self, temp_git_repo):
        """undo moves HEAD back to the previous commit."""
        _commit_file(temp_git_repo, 'a.txt', 'hello', 'second commit')
        head_before = _current_commit_msg(temp_git_repo)
        assert 'second commit' in head_before

        fg = self._make_fg()
        result = fg.undo()

        assert result is True
        head_after = _current_commit_msg(temp_git_repo)
        assert 'second commit' not in head_after
        assert 'Initial commit' in head_after

    def test_undo_then_redo_restores_commit(self, temp_git_repo):
        """undo followed by redo brings HEAD back to the undone commit."""
        _commit_file(temp_git_repo, 'a.txt', 'hello', 'second commit')
        original_head = _current_commit_msg(temp_git_repo)

        fg = self._make_fg()
        fg.undo()
        result = fg.redo()

        assert result is True
        restored_head = _current_commit_msg(temp_git_repo)
        # The short hash+message should match the original
        assert original_head == restored_head

    def test_undo_hard_discards_changes(self, temp_git_repo):
        """undo --hard removes staged and working-tree changes."""
        _commit_file(temp_git_repo, 'a.txt', 'v1', 'second commit')
        # Modify the file after the commit
        with open(os.path.join(temp_git_repo, 'a.txt'), 'w') as f:
            f.write('v2 dirty')

        fg = self._make_fg()
        result = fg.undo('--hard')

        assert result is True
        # File should be back to its state before the second commit
        assert not os.path.exists(os.path.join(temp_git_repo, 'a.txt'))

    def test_multiple_undos_then_redo(self, temp_git_repo):
        """redo after two consecutive undos restores only one commit at a time."""
        _commit_file(temp_git_repo, 'a.txt', 'v1', 'second commit')
        _commit_file(temp_git_repo, 'b.txt', 'v1', 'third commit')

        fg = self._make_fg()
        fg.undo()   # back to second commit
        fg.undo()   # back to initial commit

        result = fg.redo()
        assert result is True
        head = _current_commit_msg(temp_git_repo)
        assert 'second commit' in head

    def test_redo_without_prior_undo_returns_false(self, temp_git_repo):
        """redo returns False when no undo has been performed."""
        fg = self._make_fg()
        result = fg.redo()
        assert result is False

    def test_undo_on_single_commit_repo_returns_false(self, temp_git_repo):
        """undo returns False when the repo has only one commit."""
        # temp_git_repo fixture already has exactly one commit
        fg = self._make_fg()
        result = fg.undo()
        assert result is False
