import pytest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit

@pytest.mark.unit
class TestFancyGitCommands:
    """Test cases for individual FancyGit commands"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Mock all the loading methods to avoid file dependencies
        with patch.object(FancyGit, '_load_commands', return_value=[
            'add', 'commit', 'push', 'pull', 'status', 'branch', 'checkout', 
            'merge', 'rebase', 'reset', 'log', 'diff', 'stash', 'rm', 'mv',
            'welcome', 'confirmation', 'ai', 'colors', 'insights', 'visualize'
        ]):
            with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                with patch.object(FancyGit, '_load_output_coloring_state', return_value=False):
                    with patch.object(FancyGit, '_load_animation_type', return_value='dots'):
                        with patch('builtins.input', return_value='y'):
                            self.fancy_git = FancyGit()
                            # Disable confirmation directly on config
                            self.fancy_git.config_manager.config.confirmation_enabled = False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_add_command_success(self, mock_run_git):
        """Test git add command success"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('add', 'test.txt')
        
        assert result is True
        mock_run_git.assert_called_once_with(['add', 'test.txt'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_add_command_error(self, mock_run_git):
        """Test git add command with error"""
        mock_run_git.return_value = (1, "", "error: pathspec 'nonexistent.txt' did not match any files")
        
        result = self.fancy_git.execute_command('add', 'nonexistent.txt')
        
        assert result is False
        mock_run_git.assert_called_once_with(['add', 'nonexistent.txt'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_commit_command_success(self, mock_run_git):
        """Test git commit command success"""
        mock_run_git.return_value = (0, "[main 1234567] Test commit\n 1 file changed, 1 insertion(+)", "")
        
        result = self.fancy_git.execute_command('commit', '-m', 'Test commit')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', 'Test commit'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_push_command_success(self, mock_run_git):
        """Test git push command success"""
        mock_run_git.return_value = (0, "Enumerating objects: 3, done.\nTo github.com:user/repo.git\n   1234567..abcdefg  main -> main", "")
        
        result = self.fancy_git.execute_command('push', 'origin', 'main')
        
        assert result is True
        mock_run_git.assert_called_once_with(['push', 'origin', 'main'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_pull_command_success(self, mock_run_git):
        """Test git pull command success"""
        mock_run_git.return_value = (0, "Already up to date.", "")
        
        result = self.fancy_git.execute_command('pull', 'origin', 'main')
        
        assert result is True
        mock_run_git.assert_called_once_with(['pull', 'origin', 'main'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_status_command_success(self, mock_run_git):
        """Test git status command success"""
        mock_run_git.return_value = (0, "On branch main\nnothing to commit, working tree clean", "")
        
        result = self.fancy_git.execute_command('status')
        
        assert result is True
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_branch_command_success(self, mock_run_git):
        """Test git branch command success"""
        mock_run_git.return_value = (0, "* main\n  feature-branch", "")
        
        result = self.fancy_git.execute_command('branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_branch_create_command(self, mock_run_git):
        """Test git branch creation command"""
        mock_run_git.return_value = (0, "", "")
        
        result = self.fancy_git.execute_command('branch', 'new-feature')
        
        assert result is True
        mock_run_git.assert_called_once_with(['branch', 'new-feature'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_checkout_command_success(self, mock_run_git):
        """Test git checkout command success"""
        mock_run_git.return_value = (0, "Switched to branch 'feature-branch'", "")
        
        result = self.fancy_git.execute_command('checkout', 'feature-branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['checkout', 'feature-branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_merge_command_success(self, mock_run_git):
        """Test git merge command success"""
        mock_run_git.return_value = (0, "Merge made by the 'recursive' strategy.\n 1 file changed, 1 insertion(+)", "")
        
        result = self.fancy_git.execute_command('merge', 'feature-branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['merge', 'feature-branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_merge_command_conflict(self, mock_run_git):
        """Test git merge command with conflicts"""
        mock_run_git.return_value = (1, "", "error: Merge conflict in README.md\nAutomatic merge failed; fix conflicts and then commit the result.")
        
        result = self.fancy_git.execute_command('merge', 'feature-branch')
        
        assert result is False
        mock_run_git.assert_called_once_with(['merge', 'feature-branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_rebase_command_success(self, mock_run_git):
        """Test git rebase command success"""
        mock_run_git.return_value = (0, "Successfully rebased and updated refs/heads/main.", "")
        
        result = self.fancy_git.execute_command('rebase', 'origin/main')
        
        assert result is True
        mock_run_git.assert_called_once_with(['rebase', 'origin/main'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_reset_command_success(self, mock_run_git):
        """Test git reset command success"""
        mock_run_git.return_value = (0, "Unstaged changes after reset:\nM\ttest.py", "")
        
        result = self.fancy_git.execute_command('reset', 'HEAD~1')
        
        assert result is True
        mock_run_git.assert_called_once_with(['reset', 'HEAD~1'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_log_command_success(self, mock_run_git):
        """Test git log command success"""
        mock_run_git.return_value = (0, "commit 1234567890abcdef\nAuthor: Test User <test@example.com>\nDate:   Mon Jan 1 12:00:00 2024\n\n    Test commit message", "")
        
        result = self.fancy_git.execute_command('log', '--oneline', '-5')
        
        assert result is True
        mock_run_git.assert_called_once_with(['log', '--oneline', '-5'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_diff_command_success(self, mock_run_git):
        """Test git diff command success"""
        mock_run_git.return_value = (0, "diff --git a/test.py b/test.py\nindex 1234567..abcdefg 100644\n--- a/test.py\n+++ b/test.py\n@@ -1,3 +1,4 @@\n+new line", "")
        
        result = self.fancy_git.execute_command('diff', 'test.py')
        
        assert result is True
        mock_run_git.assert_called_once_with(['diff', 'test.py'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_stash_command_success(self, mock_run_git):
        """Test git stash command success"""
        mock_run_git.return_value = (0, "Saved working directory and index state WIP on main: 1234567 Test commit", "")
        
        result = self.fancy_git.execute_command('stash', 'push', '-m', 'WIP')
        
        assert result is True
        mock_run_git.assert_called_once_with(['stash', 'push', '-m', 'WIP'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_rm_command_success(self, mock_run_git):
        """Test git rm command success"""
        mock_run_git.return_value = (0, "rm 'test.txt'", "")
        
        result = self.fancy_git.execute_command('rm', 'test.txt')
        
        assert result is True
        mock_run_git.assert_called_once_with(['rm', 'test.txt'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_mv_command_success(self, mock_run_git):
        """Test git mv command success"""
        mock_run_git.return_value = (0, "Renaming 'old.txt' to 'new.txt'", "")
        
        result = self.fancy_git.execute_command('mv', 'old.txt', 'new.txt')
        
        assert result is True
        mock_run_git.assert_called_once_with(['mv', 'old.txt', 'new.txt'])
    
    def test_unknown_command(self):
        """Test handling of unknown commands"""
        result = self.fancy_git.execute_command('unknown_command')
        
        assert result is False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_no_args(self, mock_run_git):
        """Test command execution with no arguments"""
        mock_run_git.return_value = (0, "Git help output", "")
        
        result = self.fancy_git.execute_command('status')
        
        assert result is True
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_multiple_args(self, mock_run_git):
        """Test command execution with multiple arguments"""
        mock_run_git.return_value = (0, "Branch 'test-branch' set up to track remote branch 'test' from 'origin'.", "")
        
        result = self.fancy_git.execute_command('push', '-u', 'origin', 'test-branch')
        
        assert result is True
        mock_run_git.assert_called_once_with(['push', '-u', 'origin', 'test-branch'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_complex_args(self, mock_run_git):
        """Test command execution with complex arguments containing quotes and special characters"""
        mock_run_git.return_value = (0, "Commit successful", "")
        
        result = self.fancy_git.execute_command('commit', '-m', 'Fix bug #123: Update configuration file')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', 'Fix bug #123: Update configuration file'])

@pytest.mark.unit
class TestFancyGitSpecialCommands:
    """Test cases for FancyGit special commands"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=[
            'welcome', 'confirmation', 'ai', 'colors', 'insights', 'visualize'
        ]):
            with patch('builtins.input', return_value='y'):
                self.fancy_git = FancyGit()
                # Set confirmation to True for testing confirmation commands
                self.fancy_git.config_manager.config.confirmation_enabled = True
    
    def test_welcome_command(self):
        """Test welcome command"""
        result = self.fancy_git.execute_command('welcome')
        
        assert result is True
        # The welcome command should execute without errors
        # We can't easily mock the welcome function due to import issues,
        # but we can verify it returns True (successful execution)
    
    def test_confirmation_command_toggle(self):
        """Test confirmation command toggle"""
        initial_state = self.fancy_git.confirmation_enabled
        
        result = self.fancy_git.execute_command('confirmation')
        
        assert result is not None  # The method returns the current state (bool)
        assert self.fancy_git.confirmation_enabled != initial_state
    
    def test_confirmation_command_enable(self):
        """Test confirmation command enable"""
        result = self.fancy_git.execute_command('confirmation', 'on')
        
        assert result is True
        assert self.fancy_git.confirmation_enabled is True
    
    def test_confirmation_command_disable(self):
        """Test confirmation command disable"""
        result = self.fancy_git.execute_command('confirmation', 'off')
        
        assert isinstance(result, bool)  # The method returns the current state
        assert self.fancy_git.confirmation_enabled is False
    
    def test_confirmation_command_status(self):
        """Test confirmation command status"""
        with patch('builtins.print') as mock_print:
            result = self.fancy_git.execute_command('confirmation', 'status')
            
            assert result is True
            mock_print.assert_called()
    
    def test_ai_command_toggle(self):
        """Test AI command toggle"""
        # Mock the test_connection method on the actual provider
        with patch.object(self.fancy_git.ai_engine.analysis_provider, 'test_connection', return_value=True):
            initial_state = self.fancy_git.ai_analysis_enabled
            
            result = self.fancy_git.execute_command('ai', 'toggle')
            
            assert result is not initial_state  # Returns the new state (opposite of initial)
            assert self.fancy_git.ai_analysis_enabled != initial_state
    
    def test_ai_command_enable(self):
        """Test AI command enable"""
        # Mock the test_connection method on the actual provider
        with patch.object(self.fancy_git.ai_engine.analysis_provider, 'test_connection', return_value=True):
            result = self.fancy_git.execute_command('ai', 'on')
            
            assert result is True
            assert self.fancy_git.ai_analysis_enabled is True
    
    def test_ai_command_disable(self):
        """Test AI command disable"""
        result = self.fancy_git.execute_command('ai', 'off')
        
        assert result is False  # Returns the new state (disabled)
        assert self.fancy_git.ai_analysis_enabled is False
    
    def test_ai_command_status(self):
        """Test AI command status"""
        # Mock the test_connection method on the actual provider
        with patch.object(self.fancy_git.ai_engine.analysis_provider, 'test_connection', return_value=True):
            with patch('builtins.print') as mock_print:
                result = self.fancy_git.execute_command('ai', 'status')
                
                assert isinstance(result, bool)  # The method returns the current state
                mock_print.assert_called()
    
    def test_colors_command_toggle(self):
        """Test colors command toggle"""
        initial_state = self.fancy_git.output_coloring_enabled
        
        result = self.fancy_git.execute_command('colors')
        
        assert result is not initial_state  # Returns the new state (opposite of initial)
        assert self.fancy_git.output_coloring_enabled != initial_state
    
    def test_colors_command_enable(self):
        """Test colors command enable"""
        result = self.fancy_git.execute_command('colors', 'on')
        
        assert result is True
        assert self.fancy_git.output_coloring_enabled is True
    
    def test_colors_command_disable(self):
        """Test colors command disable"""
        result = self.fancy_git.execute_command('colors', 'off')
        
        assert isinstance(result, bool)  # The method returns the current state
        assert self.fancy_git.output_coloring_enabled is False
    
    def test_colors_command_status(self):
        """Test colors command status"""
        with patch('builtins.print') as mock_print:
            result = self.fancy_git.execute_command('colors', 'status')
            
            assert isinstance(result, bool)  # The method returns the current state
            mock_print.assert_called()
    
    @patch('src.git_insights.GitInsights.generate_insights_report')
    def test_insights_command_success(self, mock_generate):
        """Test insights command success"""
        mock_generate.return_value = {
            'generated_at': '2024-01-01T12:00:00Z',
            'analysis_period_days': 30,
            'summary': {'total_commits': 10},
            'commit_frequency': {},
            'branch_analysis': {},
            'file_hotspots': {},
            'contributor_stats': {}
        }
        
        with patch('builtins.print') as mock_print:
            result = self.fancy_git.execute_command('insights')
            
            assert isinstance(result, bool)  # The method returns True/False
            mock_generate.assert_called_once_with(30)
    
    @patch('src.git_insights.GitInsights.generate_insights_report')
    def test_insights_command_with_days(self, mock_generate):
        """Test insights command with custom days"""
        mock_generate.return_value = {
            'generated_at': '2024-01-01T12:00:00Z',
            'analysis_period_days': 7,
            'summary': {'total_commits': 5},
            'commit_frequency': {},
            'branch_analysis': {},
            'file_hotspots': {},
            'contributor_stats': {}
        }
        
        with patch('builtins.print') as mock_print:
            result = self.fancy_git.execute_command('insights', '--days=7')
            
            assert isinstance(result, bool)  # The method returns True/False
            mock_generate.assert_called_once_with(7)
    
    @patch('src.mermaid_export.MermaidExporter.export_all')
    @patch('webbrowser.open')
    def test_visualize_command_success(self, mock_browser, mock_export):
        """Test visualize command success"""
        mock_export.return_value = {
            'status_mmd': '.fancygit/status.mmd',
            'graph_mmd': '.fancygit/graph.mmd',
            'tree_mmd': '.fancygit/tree.mmd',
            'deps_mmd': '.fancygit/deps.mmd',
            'html': '.fancygit/repo_visualization.html'
        }
        
        with patch.object(self.fancy_git, 'get_repo_state', return_value={'branch': 'main'}):
            with patch('builtins.print') as mock_print:
                result = self.fancy_git.execute_command('visualize')
                
                assert result is True
                mock_export.assert_called_once()
                mock_browser.assert_called_once()
    
    @patch('src.mermaid_export.MermaidExporter.export_all')
    def test_visualize_command_no_browser(self, mock_export):
        """Test visualize command without opening browser"""
        mock_export.return_value = {
            'status_mmd': '.fancygit/status.mmd',
            'graph_mmd': '.fancygit/graph.mmd',
            'tree_mmd': '.fancygit/tree.mmd',
            'deps_mmd': '.fancygit/deps.mmd',
            'html': '.fancygit/repo_visualization.html'
        }
        
        with patch.object(self.fancy_git, 'get_repo_state', return_value={'branch': 'main'}):
            with patch('builtins.print') as mock_print:
                result = self.fancy_git.execute_command('visualize', '--no-open')
                
                assert result is True
                mock_export.assert_called_once()

@pytest.mark.unit
class TestFancyGitCommandValidation:
    """Test cases for FancyGit command validation and edge cases"""
    
    def setup_method(self):
        """Setup method called before each test"""
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'status']):
            self.fancy_git = FancyGit()
            # Disable confirmation directly on config to avoid stdin issues
            self.fancy_git.config_manager.config.confirmation_enabled = False
            self.fancy_git.config_manager.config.output_coloring_enabled = False
    
    def test_empty_command(self):
        """Test handling of empty command"""
        result = self.fancy_git.execute_command('')
        
        assert result is False
    
    def test_none_command(self):
        """Test handling of None command"""
        result = self.fancy_git.execute_command(None)
        
        assert result is False
    
    def test_command_not_in_list(self):
        """Test handling of command not in available commands"""
        result = self.fancy_git.execute_command('nonexistent_command')
        
        assert result is False
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_empty_args_list(self, mock_run_git):
        """Test command with empty args list"""
        mock_run_git.return_value = (0, "Git status output", "")
        
        result = self.fancy_git.execute_command('status')
        
        assert result is True
        mock_run_git.assert_called_once_with(['status'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_special_characters_in_args(self, mock_run_git):
        """Test command with special characters in arguments"""
        mock_run_git.return_value = (0, "Commit successful", "")
        
        result = self.fancy_git.execute_command('commit', '-m', 'Fix: Update "config.json" file')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', 'Fix: Update "config.json" file'])
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_command_with_unicode_args(self, mock_run_git):
        """Test command with unicode characters in arguments"""
        mock_run_git.return_value = (0, "Commit successful", "")
        
        result = self.fancy_git.execute_command('commit', '-m', 'Add 🚀 emoji support')
        
        assert result is True
        mock_run_git.assert_called_once_with(['commit', '-m', 'Add 🚀 emoji support'])
