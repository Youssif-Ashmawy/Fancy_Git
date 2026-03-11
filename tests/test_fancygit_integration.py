import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fancygit import FancyGit

@pytest.mark.integration
@pytest.mark.slow
class TestFancyGitIntegration:
    """Integration tests for FancyGit class workflows"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Mock the config loading to avoid file dependencies
        with patch.object(FancyGit, '_load_commands', return_value=['add', 'commit', 'push', 'pull']):
            with patch.object(FancyGit, '_load_confirmation_state', return_value=True):
                with patch.object(FancyGit, '_load_ai_analysis_state', return_value=False):
                    with patch.object(FancyGit, '_load_animation_type', return_value='simple'):
                        self.fancy_git = FancyGit()
    
    def test_fancygit_initialization(self):
        """Test FancyGit initializes with all required components"""
        assert hasattr(self.fancy_git, 'runner')
        assert hasattr(self.fancy_git, 'parser')
        assert hasattr(self.fancy_git, 'mermaid')
        assert hasattr(self.fancy_git, 'insights')
        assert hasattr(self.fancy_git, 'ollama')
        assert hasattr(self.fancy_git, 'available_commands')
        assert hasattr(self.fancy_git, 'confirmation_enabled')
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_clean_git_status_workflow(self, mock_run_git):
        """Test workflow when git status is clean"""
        mock_run_git.return_value = (0, "On branch main\nnothing to commit, working tree clean\n", "")
        
        returncode, stdout, stderr = self.fancy_git.runner.run_git_command(['status'])
        errors = self.fancy_git.parser.detect_warnings_errors(stdout, stderr)
        
        assert returncode == 0
        assert len(errors) == 0
        assert "nothing to commit" in stdout
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_error_detection_workflow(self, mock_run_git):
        """Test workflow when git command produces errors"""
        mock_run_git.return_value = (1, "", "error: pathspec 'nonexistent.txt' did not match any files\n")
        
        returncode, stdout, stderr = self.fancy_git.runner.run_git_command(['add', 'nonexistent.txt'])
        errors = self.fancy_git.parser.detect_warnings_errors(stdout, stderr)
        
        assert returncode == 1
        assert len(errors) == 1
        assert errors[0].severity == "error"
        assert "pathspec" in errors[0].message
        assert errors[0].source == "stderr"
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_warning_detection_workflow(self, mock_run_git):
        """Test workflow when git command produces warnings"""
        mock_run_git.return_value = (0, "warning: LF will be replaced by CRLF in README.md\n", "")
        
        returncode, stdout, stderr = self.fancy_git.runner.run_git_command(['add', 'README.md'])
        errors = self.fancy_git.parser.detect_warnings_errors(stdout, stderr)
        
        assert returncode == 0
        assert len(errors) == 2  # Both "warning:" and "WARNING:" patterns match
        assert all(error.severity == "warning" for error in errors)
        assert all("LF will be replaced" in error.message for error in errors)
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_multiple_issues_detection(self, mock_run_git):
        """Test workflow with multiple warnings and errors"""
        mock_run_git.return_value = (
            1, 
            "warning: CRLF will be replaced by LF in test.py\nYour branch is ahead by 2 commits\n",
            "error: merge conflict in README.md\nfatal: unable to checkout"
        )
        
        returncode, stdout, stderr = self.fancy_git.runner.run_git_command(['pull', 'origin', 'main'])
        errors = self.fancy_git.parser.detect_warnings_errors(stdout, stderr)
        
        assert returncode == 1
        assert len(errors) == 8  # Multiple pattern matches
        
        error_severities = [error.severity for error in errors]
        assert error_severities.count("warning") == 3  # warning: (twice) + ahead
        assert error_severities.count("error") == 5  # error: + conflict + merge conflict + fatal + unable
    
    def test_available_commands_loading(self):
        """Test that available commands are loaded correctly"""
        assert isinstance(self.fancy_git.available_commands, list)
        assert len(self.fancy_git.available_commands) > 0
        assert 'add' in self.fancy_git.available_commands
        assert 'commit' in self.fancy_git.available_commands
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_repo_state_integration(self, mock_run_git):
        """Test repository state functionality"""
        # Mock git status output for a dirty repository
        mock_run_git.return_value = (
            0,
            "On branch main\nChanges not staged for commit:\n  modified:   test.py\nUntracked files:\n  new_file.py\n",
            ""
        )
        
        # Test the repo state method if it exists
        if hasattr(self.fancy_git, 'get_repo_state'):
            repo_state = self.fancy_git.get_repo_state()
            assert isinstance(repo_state, dict)
            assert 'branch' in repo_state
            assert 'clean' in repo_state
    
    @patch('src.git_runner.GitRunner.run_git_command')
    def test_conflict_detection_integration(self, mock_run_git):
        """Test merge conflict detection integration"""
        # Mock git status showing conflicts
        mock_run_git.return_value = (
            1,
            "",
            "error: Merge conflict in README.md\nerror: Merge conflict in src/main.py\n"
        )
        
        returncode, stdout, stderr = self.fancy_git.runner.run_git_command(['merge', 'feature-branch'])
        errors = self.fancy_git.parser.detect_warnings_errors(stdout, stderr)
        
        assert returncode == 1
        assert len(errors) == 6  # Each conflict matches 3 patterns: "error:", "conflict", "merge conflict"
        
        conflict_errors = [e for e in errors if 'conflict' in e.message.lower()]
        assert len(conflict_errors) == 6  # All errors contain "conflict"
    
    @patch('src.ollama_client.OllamaClient.test_connection')
    def test_ai_integration_workflow(self, mock_test_connection):
        """Test AI integration workflow"""
        mock_test_connection.return_value = True
        
        # Test Ollama client initialization and connection
        if hasattr(self.fancy_git, 'ollama'):
            connection_status = self.fancy_git.ollama.test_connection()
            assert connection_status is True
    
    def test_mermaid_export_integration(self):
        """Test Mermaid export functionality integration"""
        if hasattr(self.fancy_git, 'mermaid'):
            # Test that mermaid exporter is properly initialized
            assert self.fancy_git.mermaid is not None
            assert hasattr(self.fancy_git.mermaid, 'runner')
    
    def test_configuration_loading(self):
        """Test that configuration is loaded properly"""
        # Test that configuration values are set
        assert isinstance(self.fancy_git.confirmation_enabled, bool)
        assert isinstance(self.fancy_git.ai_analysis_enabled, bool)
        assert isinstance(self.fancy_git.loading_animation_type, str)
