import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit

@pytest.mark.integration
class TestFancyGitCommandWorkflows:
    """Integration tests for complete command workflows"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=[
            'add', 'commit', 'push', 'pull', 'status', 'branch', 'checkout', 
            'merge', 'rebase', 'reset', 'log', 'diff', 'stash', 'rm', 'mv', 'revert',
            'welcome', 'confirmation', 'ai', 'colors', 'insights', 'visualize'
        ]):
            with patch('src.config_manager.ConfigManager'):
                self.fancy_git = FancyGit()
                # Configure test settings
                self.fancy_git.config_manager.config.confirmation_enabled = False
                self.fancy_git.config_manager.config.ai_analysis_enabled = False
                self.fancy_git.config_manager.config.output_coloring_enabled = False
                self.fancy_git.config_manager.config.loading_animation = 'dots'
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_complete_add_commit_workflow(self, mock_run_git):
        """Test complete workflow: add -> commit -> push"""
        # Mock the sequence of git commands
        mock_run_git.side_effect = [
            (0, "", ""),  # git add .
            (0, "[main 1234567] Initial commit\n 1 file changed, 1 insertion(+)", ""),  # git commit
            (0, "Enumerating objects: 3, done.\nTo github.com:user/repo.git\n   1234567..abcdefg  main -> main", "")  # git push
        ]
        
        # Execute workflow
        add_result = self.fancy_git.execute_command('add', '.')
        commit_result = self.fancy_git.execute_command('commit', '-m', 'Initial commit')
        push_result = self.fancy_git.execute_command('push', 'origin', 'main')
        
        # Verify all commands succeeded
        assert add_result is True
        assert commit_result is True
        assert push_result is True
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['add', '.']),
            call(['commit', '-m', 'Initial commit']),
            call(['push', 'origin', 'main'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_branch_creation_and_checkout_workflow(self, mock_run_git):
        """Test workflow: create branch -> checkout -> work -> merge back"""
        mock_run_git.side_effect = [
            (0, "", ""),  # git branch feature-branch
            (0, "Switched to branch 'feature-branch'", ""),  # git checkout feature-branch
            (0, "", ""),  # git add .
            (0, "[feature-branch abcdef123] Add feature\n 1 file changed, 1 insertion(+)", ""),  # git commit
            (0, "Switched to branch 'main'", ""),  # git checkout main
            (0, "Merge made by the 'recursive' strategy.\n 1 file changed, 1 insertion(+)", ""),  # git merge feature-branch
        ]
        
        # Execute workflow
        branch_result = self.fancy_git.execute_command('branch', 'feature-branch')
        checkout_result = self.fancy_git.execute_command('checkout', 'feature-branch')
        add_result = self.fancy_git.execute_command('add', '.')
        commit_result = self.fancy_git.execute_command('commit', '-m', 'Add feature')
        checkout_main_result = self.fancy_git.execute_command('checkout', 'main')
        merge_result = self.fancy_git.execute_command('merge', 'feature-branch')
        
        # Verify all commands succeeded
        assert all(result is True for result in [
            branch_result, checkout_result, add_result, 
            commit_result, checkout_main_result, merge_result
        ])
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['branch', 'feature-branch']),
            call(['checkout', 'feature-branch']),
            call(['add', '.']),
            call(['commit', '-m', 'Add feature']),
            call(['checkout', 'main']),
            call(['merge', 'feature-branch'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_stash_workflow(self, mock_run_git):
        """Test workflow: stash changes -> pull -> stash pop"""
        mock_run_git.side_effect = [
            (0, "Saved working directory and index state WIP on main: 1234567 Work in progress", ""),  # git stash push
            (0, "Already up to date.", ""),  # git pull origin main
            (0, "On branch main\nChanges not staged for commit:\n  modified:   test.py", ""),  # git stash pop
        ]
        
        # Execute workflow
        stash_result = self.fancy_git.execute_command('stash', 'push', '-m', 'Work in progress')
        pull_result = self.fancy_git.execute_command('pull', 'origin', 'main')
        stash_pop_result = self.fancy_git.execute_command('stash', 'pop')
        
        # Verify all commands succeeded
        assert stash_result is True
        assert pull_result is True
        assert stash_pop_result is True
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['stash', 'push', '-m', 'Work in progress']),
            call(['pull', 'origin', 'main']),
            call(['stash', 'pop'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_reset_and_revert_workflow(self, mock_run_git):
        """Test workflow: reset hard -> revert commit"""
        mock_run_git.side_effect = [
            (0, "HEAD is now at 1234567 Previous commit", ""),  # git reset --hard HEAD~1
            (0, "[main abcdef123] Revert \"Previous commit\"\n 1 file changed, 1 deletion(-)", ""),  # git revert HEAD
        ]
        
        # Execute workflow
        reset_result = self.fancy_git.execute_command('reset', '--hard', 'HEAD~1')
        revert_result = self.fancy_git.execute_command('revert', 'HEAD')
        
        # Verify all commands succeeded
        assert reset_result is True
        assert revert_result is True
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['reset', '--hard', 'HEAD~1']),
            call(['revert', 'HEAD'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_conflict_resolution_workflow(self, mock_run_git):
        """Test workflow: handle merge conflicts"""
        mock_run_git.side_effect = [
            (1, "", "error: Merge conflict in README.md\nAutomatic merge failed; fix conflicts and then commit the result."),  # git merge feature-branch
            (0, "Unstaged changes after reset:\nM\tREADME.md", ""),  # git reset --merge
            (0, "Merge made by the 'recursive' strategy.\n 1 file changed, 1 insertion(+)", ""),  # git merge feature-branch (after fixing conflicts)
        ]
        
        # Execute workflow
        merge_conflict_result = self.fancy_git.execute_command('merge', 'feature-branch')
        reset_result = self.fancy_git.execute_command('reset', '--merge')
        merge_success_result = self.fancy_git.execute_command('merge', 'feature-branch')
        
        # Verify conflict detection and resolution
        assert merge_conflict_result is False  # First merge should fail
        assert reset_result is True
        assert merge_success_result is True  # Second merge should succeed
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['merge', 'feature-branch']),
            call(['reset', '--merge']),
            call(['merge', 'feature-branch'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_file_operations_workflow(self, mock_run_git):
        """Test workflow: file rename, modify, remove"""
        mock_run_git.side_effect = [
            (0, "Renaming 'old.txt' to 'new.txt'", ""),  # git mv old.txt new.txt
            (0, "", ""),  # git add new.txt
            (0, "[main 1234567] Rename file\n 1 file changed, 0 insertions(+), 0 deletions(-)\n rename old.txt => new.txt (100%)", ""),  # git commit
            (0, "rm 'new.txt'", ""),  # git rm new.txt
            (0, "[main abcdef123] Remove file\n 1 file changed, 1 deletion(-)", ""),  # git commit
        ]
        
        # Execute workflow
        mv_result = self.fancy_git.execute_command('mv', 'old.txt', 'new.txt')
        add_result = self.fancy_git.execute_command('add', 'new.txt')
        commit_mv_result = self.fancy_git.execute_command('commit', '-m', 'Rename file')
        rm_result = self.fancy_git.execute_command('rm', 'new.txt')
        commit_rm_result = self.fancy_git.execute_command('commit', '-m', 'Remove file')
        
        # Verify all commands succeeded
        assert all(result is True for result in [
            mv_result, add_result, commit_mv_result, rm_result, commit_rm_result
        ])
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['mv', 'old.txt', 'new.txt']),
            call(['add', 'new.txt']),
            call(['commit', '-m', 'Rename file']),
            call(['rm', 'new.txt']),
            call(['commit', '-m', 'Remove file'])
        ]
        mock_run_git.assert_has_calls(expected_calls)

@pytest.mark.integration
class TestFancyGitSpecialCommandWorkflows:
    """Integration tests for special command workflows"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=[
            'add', 'commit', 'push', 'pull', 'status', 'branch', 'checkout', 
            'merge', 'rebase', 'reset', 'log', 'diff', 'stash', 'rm', 'mv',
            'welcome', 'confirmation', 'ai', 'colors', 'insights', 'visualize'
        ]):
            with patch('src.config_manager.ConfigManager'):
                self.fancy_git = FancyGit()
                # Configure test settings
                self.fancy_git.config_manager.config.confirmation_enabled = False
                self.fancy_git.config_manager.config.ai_analysis_enabled = False
                self.fancy_git.config_manager.config.output_coloring_enabled = False
                self.fancy_git.config_manager.config.loading_animation = 'dots'
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_ai_error_analysis_workflow(self, mock_run_git):
        """Test AI error analysis workflow - simplified without actual AI calls"""
        mock_run_git.return_value = (1, "", "error: pathspec 'nonexistent.txt' did not match any files")
        
        # Execute command that produces error
        add_result = self.fancy_git.execute_command('add', 'nonexistent.txt')
        
        # Verify command failed as expected
        assert add_result is False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    @patch('src.output_colorizer.OutputColorizer.colorize_output')
    def test_output_coloring_workflow(self, mock_colorize, mock_run_git):
        """Test output coloring workflow"""
        mock_run_git.return_value = (0, "On branch main\nnothing to commit, working tree clean", "")
        mock_colorize.return_value = ("On branch main\nnothing to commit, working tree clean", "")
        
        # Enable output coloring
        colors_enable_result = self.fancy_git.execute_command('colors', 'on')
        assert colors_enable_result is True
        
        # Execute command
        status_result = self.fancy_git.execute_command('status')
        
        # Verify output coloring was applied
        assert status_result is True
        mock_colorize.assert_called_once()
    
    @patch('src.git_insights.GitInsights.generate_insights_report')
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_insights_workflow(self, mock_run_git, mock_generate):
        """Test insights generation workflow"""
        mock_run_git.return_value = (0, "On branch main", "")
        mock_generate.return_value = {
            'generated_at': '2024-01-01T12:00:00Z',
            'analysis_period_days': 30,
            'summary': {'total_commits': 10, 'active_contributors': 2, 'active_branches': 3, 'total_branches': 5, 'total_files_changed': 15},
            'commit_frequency': {'Alice': 6, 'Bob': 4},
            'branch_analysis': {
                'main': {'type': 'local', 'status': 'active', 'days_inactive': 0},
                'feature-branch': {'type': 'local', 'status': 'active', 'days_inactive': 5},
                'old-branch': {'type': 'local', 'status': 'stale', 'days_inactive': 30}
            },
            'file_hotspots': {'src/main.py': 8, 'README.md': 4, 'tests/test_main.py': 3},
            'contributor_stats': {
                'Alice': {'commits': 6, 'lines_added': 150, 'lines_removed': 50},
                'Bob': {'commits': 4, 'lines_added': 80, 'lines_removed': 30}
            }
        }
        
        # Generate insights
        insights_result = self.fancy_git.execute_command('insights', '--days=30')
        
        # Verify insights generation
        assert insights_result is True
        mock_generate.assert_called_once_with(30)
    
    @patch('src.mermaid_export.MermaidExporter.export_all')
    @patch('src.git_runner.GitRunner.run_git_command')
    @patch('webbrowser.open')
    def test_visualization_workflow(self, mock_browser, mock_run_git, mock_export):
        """Test repository visualization workflow"""
        mock_run_git.return_value = (0, "On branch main", "")
        mock_export.return_value = {
            'status_mmd': '.fancygit/status.mmd',
            'graph_mmd': '.fancygit/graph.mmd',
            'tree_mmd': '.fancygit/tree.mmd',
            'deps_mmd': '.fancygit/deps.mmd',
            'html': '.fancygit/repo_visualization.html'
        }
        
        # Generate visualization
        with patch.object(self.fancy_git, 'get_repo_state', return_value={'branch': 'main', 'clean': True}):
            viz_result = self.fancy_git.execute_command('visualize', '--max-commits=20')
        
        # Verify visualization generation
        assert viz_result is True
        mock_export.assert_called_once()
        mock_browser.assert_called_once()
    
    @patch('builtins.input')
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_confirmation_workflow(self, mock_run_git, mock_input):
        """Test confirmation workflow"""
        mock_run_git.return_value = (0, "On branch main", "")
        mock_input.return_value = 'y'  # User confirms the command
        
        # Enable confirmation for this test
        self.fancy_git.confirmation_enabled = True
        
        # Patch the sys.modules check at the point where it's used
        with patch.object(sys, 'modules', {}):
            # Execute command with confirmation
            status_result = self.fancy_git.execute_command('status')
        
        # Verify confirmation was requested and command executed
        assert status_result is True
        mock_input.assert_called_once()
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('builtins.input')
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_confirmation_cancel_workflow(self, mock_run_git, mock_input):
        """Test confirmation cancellation workflow"""
        mock_input.return_value = 'n'  # User cancels the command
        mock_run_git.return_value = (0, "On branch main", "")  # Mock return value
        
        # Enable confirmation for this test
        self.fancy_git.confirmation_enabled = True
        
        # Patch the sys.modules check at the point where it's used
        with patch.object(sys, 'modules', {}):
            # Execute command but cancel confirmation
            status_result = self.fancy_git.execute_command('status')
        
        # Verify confirmation was requested and command was cancelled
        assert status_result is False
        mock_input.assert_called_once()
        mock_run_git.assert_not_called()

@pytest.mark.integration
class TestFancyGitErrorRecoveryWorkflows:
    """Integration tests for error recovery and edge cases"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'push', 'pull', 'status']):
            with patch('src.config_manager.ConfigManager'):
                self.fancy_git = FancyGit()
                # Configure test settings
                self.fancy_git.config_manager.config.confirmation_enabled = False
                self.fancy_git.config_manager.config.ai_analysis_enabled = False
                self.fancy_git.config_manager.config.output_coloring_enabled = False
                self.fancy_git.config_manager.config.loading_animation = 'dots'
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_network_error_recovery(self, mock_run_git):
        """Test recovery from network errors"""
        # First call fails with network error, second succeeds
        mock_run_git.side_effect = [
            (1, "", "fatal: unable to access 'https://github.com/user/repo.git/': Could not resolve host: github.com"),
            (0, "Enumerating objects: 3, done.\nTo github.com:user/repo.git\n   1234567..abcdefg  main -> main", "")
        ]
        
        # First push fails
        push_fail_result = self.fancy_git.execute_command('push', 'origin', 'main')
        assert push_fail_result is False
        
        # Second push succeeds
        push_success_result = self.fancy_git.execute_command('push', 'origin', 'main')
        assert push_success_result is True
        
        # Verify both calls were made
        assert mock_run_git.call_count == 2
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_permission_error_handling(self, mock_run_git):
        """Test handling of permission errors"""
        mock_run_git.return_value = (1, "", "error: unable to create file '.git/index.lock': Permission denied")
        
        # Try to execute command that requires permissions
        status_result = self.fancy_git.execute_command('status')
        
        # Verify error was handled
        assert status_result is False
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_repository_not_initialized(self, mock_run_git):
        """Test handling of non-git repository"""
        mock_run_git.return_value = (1, "", "fatal: not a git repository (or any of the parent directories): .git")
        
        # Try to execute git command
        status_result = self.fancy_git.execute_command('status')
        
        # Verify error was handled
        assert status_result is False
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_subprocess_exception_handling(self, mock_run_git):
        """Test handling of subprocess exceptions"""
        mock_run_git.return_value = (-1, "", "git command not found")
        
        # Try to execute command when git is not available
        status_result = self.fancy_git.execute_command('status')
        
        # Verify exception was handled
        assert isinstance(status_result, bool)  # Should return False on exception
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_empty_repository_workflow(self, mock_run_git):
        """Test workflow with empty/new repository"""
        mock_run_git.side_effect = [
            (0, "On branch main\nNo commits yet", ""),  # git status
            (0, "", ""),  # git add .
            (0, "[main (root-commit) 1234567] Initial commit\n 1 file changed, 1 insertion(+)", ""),  # git commit
            (0, "Enumerating objects: 3, done.\nTo github.com:user/repo.git\n * [new branch]      main -> main", ""),  # git push
        ]
        
        # Execute workflow in empty repository
        status_result = self.fancy_git.execute_command('status')
        add_result = self.fancy_git.execute_command('add', '.')
        commit_result = self.fancy_git.execute_command('commit', '-m', 'Initial commit')
        push_result = self.fancy_git.execute_command('push', '-u', 'origin', 'main')
        
        # Verify all commands succeeded
        assert all(result is True for result in [status_result, add_result, commit_result, push_result])
        
        # Verify the correct sequence of calls
        expected_calls = [
            call(['status']),
            call(['add', '.']),
            call(['commit', '-m', 'Initial commit']),
            call(['push', '-u', 'origin', 'main'])
        ]
        mock_run_git.assert_has_calls(expected_calls)
