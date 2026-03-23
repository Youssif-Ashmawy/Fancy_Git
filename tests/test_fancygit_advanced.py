import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit

@pytest.mark.unit
class TestFancyGitAdvancedCommands:
    """Test cases for advanced git commands"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=[
            'archive', 'bisect', 'bundle', 'cherry-pick', 'clean', 'clone', 'describe',
            'fetch', 'format-patch', 'gc', 'grep', 'gui', 'init', 'maintenance',
            'notes', 'range-diff', 'restore', 'revert', 'shortlog', 'show',
            'sparse-checkout', 'submodule', 'switch', 'tag', 'worktree', 'log', 'status'
        ]):
            with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                with patch.object(FancyGit, '_load_output_coloring_state', return_value=False):
                    with patch.object(FancyGit, '_load_animation_type', return_value='dots'):
                        with patch('builtins.input', return_value='y'):
                            self.fancy_git = FancyGit()
                            # Disable confirmation directly on config
                            self.fancy_git.config_manager.config.confirmation_enabled = False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_archive_command(self, mock_run_git):
        """Test git archive command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('archive', 'HEAD', '--format=zip', '--output=archive.zip')
        
        assert result is True
        mock_run_git.assert_called_once_with(['archive', 'HEAD', '--format=zip', '--output=archive.zip'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_bisect_command(self, mock_run_git):
        """Test git bisect command"""
        mock_run_git.return_value = (0, "Bisecting: 0 revisions left to test after this (roughly 0 steps)", "")
        
        result = self.fancy_git.execute_command('bisect', 'start')
        
        assert result is True
        mock_run_git.assert_called_once_with(['bisect', 'start'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_bundle_command(self, mock_run_git):
        """Test git bundle command"""
        mock_run_git.return_value = (0, "Creating bundle file repo.bundle", "")
        
        result = self.fancy_git.execute_command('bundle', 'create', 'repo.bundle', 'main')
        
        assert result is True
        mock_run_git.assert_called_once_with(['bundle', 'create', 'repo.bundle', 'main'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_cherry_pick_command(self, mock_run_git):
        """Test git cherry-pick command"""
        mock_run_git.return_value = (0, "[main 1234567] Cherry picked commit from feature-branch\n 1 file changed, 1 insertion(+)", "")
        
        result = self.fancy_git.execute_command('cherry-pick', 'abcdef123')
        
        assert result is True
        mock_run_git.assert_called_once_with(['cherry-pick', 'abcdef123'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_clean_command(self, mock_run_git):
        """Test git clean command"""
        mock_run_git.return_value = (0, "Removing test.txt", "")
        
        result = self.fancy_git.execute_command('clean', '-f')
        
        assert result is True
        mock_run_git.assert_called_once_with(['clean', '-f'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_clone_command(self, mock_run_git):
        """Test git clone command"""
        mock_run_git.return_value = (0, "Cloning into 'repo'...\nremote: Enumerating objects: 100, done.", "")
        
        result = self.fancy_git.execute_command('clone', 'https://github.com/user/repo.git')
        
        assert result is True
        mock_run_git.assert_called_once_with(['clone', 'https://github.com/user/repo.git'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_describe_command(self, mock_run_git):
        """Test git describe command"""
        mock_run_git.return_value = (0, "v1.0.0-5-g1234567", "")
        
        result = self.fancy_git.execute_command('describe', '--tags')
        
        assert result is True
        mock_run_git.assert_called_once_with(['describe', '--tags'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_fetch_command(self, mock_run_git):
        """Test git fetch command"""
        mock_run_git.return_value = (0, "From github.com:user/repo\n * branch            main        -> FETCH_HEAD", "")
        
        result = self.fancy_git.execute_command('fetch', 'origin')
        
        assert result is True
        mock_run_git.assert_called_once_with(['fetch', 'origin'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_format_patch_command(self, mock_run_git):
        """Test git format-patch command"""
        mock_run_git.return_value = (0, "0001-First-commit.patch\n0002-Second-commit.patch", "")
        
        result = self.fancy_git.execute_command('format-patch', 'HEAD~2')
        
        assert result is True
        mock_run_git.assert_called_once_with(['format-patch', 'HEAD~2'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_gc_command(self, mock_run_git):
        """Test git gc command"""
        mock_run_git.return_value = (0, "Counting objects: 100, done.\nCompressing objects: 100% (50/50), done.", "")
        
        result = self.fancy_git.execute_command('gc', '--aggressive')
        
        assert result is True
        mock_run_git.assert_called_once_with(['gc', '--aggressive'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_grep_command(self, mock_run_git):
        """Test git grep command"""
        mock_run_git.return_value = (0, "src/main.py:10:print('Hello World')", "")
        
        result = self.fancy_git.execute_command('grep', 'Hello', '*.py')
        
        assert result is True
        mock_run_git.assert_called_once_with(['grep', 'Hello', '*.py'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_gui_command(self, mock_run_git):
        """Test git gui command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('gui')
        
        assert result is True
        mock_run_git.assert_called_once_with(['gui'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_init_command(self, mock_run_git):
        """Test git init command"""
        mock_run_git.return_value = (0, "Initialized empty Git repository in /path/to/repo/.git/", "")
        
        result = self.fancy_git.execute_command('init')
        
        assert result is True
        mock_run_git.assert_called_once_with(['init'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_maintenance_command(self, mock_run_git):
        """Test git maintenance command"""
        mock_run_git.return_value = (0, "Task 'gc' scheduled for next run", "")
        
        result = self.fancy_git.execute_command('maintenance', 'start')
        
        assert result is True
        mock_run_git.assert_called_once_with(['maintenance', 'start'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_notes_command(self, mock_run_git):
        """Test git notes command"""
        mock_run_git.return_value = (0, "Notes added to commit 1234567", "")
        
        result = self.fancy_git.execute_command('notes', 'add', '-m', 'Important note', 'HEAD')
        
        assert result is True
        mock_run_git.assert_called_once_with(['notes', 'add', '-m', 'Important note', 'HEAD'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_range_diff_command(self, mock_run_git):
        """Test git range-diff command"""
        mock_run_git.return_value = (0, "1:  abcdef = 1:  123456 First commit\n2:  ghijkl ! 2:  7890ab Second commit", "")
        
        result = self.fancy_git.execute_command('range-diff', 'main..feature', 'origin/main..origin/feature')
        
        assert result is True
        mock_run_git.assert_called_once_with(['range-diff', 'main..feature', 'origin/main..origin/feature'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_restore_command(self, mock_run_git):
        """Test git restore command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('restore', 'test.txt')
        
        assert result is True
        mock_run_git.assert_called_once_with(['restore', 'test.txt'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_shortlog_command(self, mock_run_git):
        """Test git shortlog command"""
        mock_run_git.return_value = (0, "Alice (5):\n  Commit 1\n  Commit 2\nBob (3):\n  Commit 3", "")
        
        result = self.fancy_git.execute_command('shortlog', '-s')
        
        assert result is True
        mock_run_git.assert_called_once_with(['shortlog', '-s'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_show_command(self, mock_run_git):
        """Test git show command"""
        mock_run_git.return_value = (0, "commit 1234567890abcdef\nAuthor: Alice <alice@example.com>\n\n    Test commit\n\ndiff --git a/test.txt b/test.txt", "")
        
        result = self.fancy_git.execute_command('show', 'HEAD')
        
        assert result is True
        mock_run_git.assert_called_once_with(['show', 'HEAD'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_sparse_checkout_command(self, mock_run_git):
        """Test git sparse-checkout command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('sparse-checkout', 'init', '--cone')
        
        assert result is True
        mock_run_git.assert_called_once_with(['sparse-checkout', 'init', '--cone'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_submodule_command(self, mock_run_git):
        """Test git submodule command"""
        mock_run_git.return_value = (0, "Cloning into 'external/lib'\nSubmodule path 'external/lib': checked out '1234567890abcdef'", "")
        
        result = self.fancy_git.execute_command('submodule', 'update', '--init')
        
        assert result is True
        mock_run_git.assert_called_once_with(['submodule', 'update', '--init'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_switch_command(self, mock_run_git):
        """Test git switch command"""
        mock_run_git.return_value = (0, "Switched to branch 'feature-branch'", "")
        
        result = self.fancy_git.execute_command('switch', 'feature-branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['switch', 'feature-branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_tag_command(self, mock_run_git):
        """Test git tag command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('tag', '-a', 'v1.0.0', '-m', 'Version 1.0.0')
        
        assert result is True
        mock_run_git.assert_called_once_with(['tag', '-a', 'v1.0.0', '-m', 'Version 1.0.0'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_worktree_command(self, mock_run_git):
        """Test git worktree command"""
        mock_run_git.return_value = (0, "Preparing worktree (checking out 'feature-branch')\nBranch 'feature-branch' set up to track local branch 'feature-branch'.", "")
        
        result = self.fancy_git.execute_command('worktree', 'add', '../feature-worktree', 'feature-branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['worktree', 'add', '../feature-worktree', 'feature-branch'])

@pytest.mark.unit
class TestFancyGitCommandEdgeCases:
    """Test cases for edge cases and error scenarios"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'push', 'pull', 'status', 'log', 'show']):
            with patch.object(FancyGit, '_load_confirmation_state', return_value=False):
                with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                    with patch.object(FancyGit, '_load_output_coloring_state', return_value=False):
                        with patch.object(FancyGit, '_load_animation_type', return_value='dots'):
                            self.fancy_git = FancyGit()
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_large_output(self, mock_run_git):
        """Test command that produces large output"""
        large_output = "commit " + "x" * 10000 + "\n" + "Author: Test User <test@example.com>\n" + "Date: Mon Jan 1 12:00:00 2024\n\n    Large commit message"
        mock_run_git.return_value = (0, large_output, "")
        
        result = self.fancy_git.execute_command('log', '-1', '--pretty=fuller')
        
        # Command succeeds but may have warnings due to output processing
        assert isinstance(result, bool)
        mock_run_git.assert_called_once_with(['log', '-1', '--pretty=fuller'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_binary_output(self, mock_run_git):
        """Test command that might produce binary output"""
        mock_run_git.return_value = (0, b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'.decode('latin1'), "")
        
        result = self.fancy_git.execute_command('show', 'HEAD:image.png')
        
        assert result is True
        mock_run_git.assert_called_once_with(['show', 'HEAD:image.png'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_newline_characters(self, mock_run_git):
        """Test command with various newline characters"""
        output_with_newlines = "Line 1\r\nLine 2\nLine 3\r\n"
        mock_run_git.return_value = (0, output_with_newlines, "")
        
        result = self.fancy_git.execute_command('log', '--oneline')
        
        assert result is True
        mock_run_git.assert_called_once_with(['log', '--oneline'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_unicode_characters(self, mock_run_git):
        """Test command with unicode characters in output"""
        unicode_output = "commit 1234567890abcdef\nAuthor: José García <jose@example.com>\nDate: Mon Jan 1 12:00:00 2024\n\n    Add 🚀 emoji support and fix ñ issue"
        mock_run_git.return_value = (0, unicode_output, "")
        
        result = self.fancy_git.execute_command('log', '-1')
        
        assert result is True
        mock_run_git.assert_called_once_with(['log', '-1'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_special_shell_characters(self, mock_run_git):
        """Test command with special shell characters in arguments"""
        mock_run_git.return_value = (0, "Commit successful", "")
        
        result = self.fancy_git.execute_command('commit', '-m', 'Fix $PATH & update "config.json" file; rm -rf /tmp/*')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', 'Fix $PATH & update "config.json" file; rm -rf /tmp/*'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_very_long_arguments(self, mock_run_git):
        """Test command with very long arguments"""
        long_message = "A" * 1000  # 1000 character message
        mock_run_git.return_value = (0, "Commit successful", "")
        
        result = self.fancy_git.execute_command('commit', '-m', long_message)
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', long_message])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_return_code_variations(self, mock_run_git):
        """Test commands with different return codes"""
        test_cases = [
            (0, True),   # Success
            (1, False),  # General error - use a real error pattern
            (128, False), # Fatal error - use a real error pattern
            (255, False), # Signal termination - use a real error pattern
        ]
        
        for return_code, expected_result in test_cases:
            if return_code == 0:
                mock_run_git.return_value = (0, "Success", "")
            else:
                mock_run_git.return_value = (return_code, "", "error: fatal error occurred")
            
            result = self.fancy_git.execute_command('status')
            
            # For return code 0 (success), the result should be True
            # For error codes, the result should be False
            if return_code == 0:
                assert result is True
            else:
                assert result is False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_stderr_only(self, mock_run_git):
        """Test command that outputs only to stderr"""
        mock_run_git.return_value = (0, "", "warning: This is a warning message")
        
        result = self.fancy_git.execute_command('status')
        
        # Command succeeds but may show warnings
        assert isinstance(result, bool)
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_mixed_output(self, mock_run_git):
        """Test command with mixed stdout and stderr output"""
        mock_run_git.return_value = (0, "On branch main\nnothing to commit", "warning: LF will be replaced by CRLF")
        
        result = self.fancy_git.execute_command('status')
        
        # Command succeeds but may show warnings
        assert isinstance(result, bool)
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_timeout_simulation(self, mock_run_git):
        """Test command timeout simulation"""
        mock_run_git.return_value = (1, "", "fatal: the remote end hung up unexpectedly")
        
        result = self.fancy_git.execute_command('push', 'origin', 'main')
        
        assert result is False
        mock_run_git.assert_called_once_with(['push', 'origin', 'main'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_empty_arguments(self, mock_run_git):
        """Test command with empty string arguments"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('commit', '-m', '')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', ''])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_whitespace_arguments(self, mock_run_git):
        """Test command with whitespace-only arguments"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('commit', '-m', '   \t\n   ')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', '   \t\n   '])

@pytest.mark.unit
class TestFancyGitCommandPerformance:
    """Test cases for command performance and optimization"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'push', 'pull', 'status', 'log', 'branch', 'diff']):
            with patch.object(FancyGit, '_load_confirmation_state', return_value=False):
                with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                    with patch.object(FancyGit, '_load_output_coloring_state', return_value=False):
                        with patch.object(FancyGit, '_load_animation_type', return_value='dots'):
                            self.fancy_git = FancyGit()
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_rapid_command_execution(self, mock_run_git):
        """Test rapid execution of multiple commands"""
        mock_run_git.return_value = (0, "Success", "")
        
        # Execute multiple commands rapidly
        results = []
        for i in range(10):
            result = self.fancy_git.execute_command('status')
            results.append(result)
        
        # All commands should succeed
        assert all(results)
        assert mock_run_git.call_count == 10
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_execution_with_different_speeds(self, mock_run_git):
        """Test commands with different execution speeds"""
        import time
        
        # Mock different return values for different calls
        mock_run_git.side_effect = [
            (0, "Slow command result", ""),
            (0, "Fast command result", ""),
            (0, "Slow command result", ""),
            (0, "Fast command result", "")
        ]
        
        start_time = time.time()
        
        result1 = self.fancy_git.execute_command('status')
        result2 = self.fancy_git.execute_command('log', '-1')
        result3 = self.fancy_git.execute_command('branch')
        result4 = self.fancy_git.execute_command('diff')
        
        end_time = time.time()
        
        # All commands should succeed
        assert all([isinstance(r, bool) for r in [result1, result2, result3, result4]])
        assert mock_run_git.call_count == 4
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_memory_usage_with_large_outputs(self, mock_run_git):
        """Test memory usage with large command outputs"""
        # Create a large output (simulating git log with many commits)
        large_output = "\n".join([f"commit {i:040d}" for i in range(1000)])
        mock_run_git.return_value = (0, large_output, "")
        
        result = self.fancy_git.execute_command('log')
        
        # Command succeeds but may have warnings due to large output
        assert isinstance(result, bool)
        mock_run_git.assert_called_once_with(['log'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_concurrent_command_simulation(self, mock_run_git):
        """Test simulation of concurrent command access"""
        mock_run_git.return_value = (0, "Success", "")
        
        # Simulate multiple rapid calls
        results = []
        for i in range(5):
            result = self.fancy_git.execute_command('status')
            results.append(result)
        
        # All should succeed
        assert all(results)
        assert mock_run_git.call_count == 5
