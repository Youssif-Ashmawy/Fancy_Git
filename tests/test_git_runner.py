import pytest
from unittest.mock import patch, MagicMock
from src.git_runner import GitRunner

@pytest.mark.unit
class TestGitRunner:
    """Test cases for GitRunner class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.runner = GitRunner()
    
    def test_git_runner_initialization(self):
        """Test GitRunner initialization"""
        assert self.runner.git_cmd == "git"
    
    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_subprocess):
        """Test successful git command execution"""
        # Mock subprocess.run result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "On branch main\nnothing to commit"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        returncode, stdout, stderr = self.runner.run_git_command(['status'])
        
        assert returncode == 0
        assert stdout == "On branch main\nnothing to commit"
        assert stderr == ""
        mock_subprocess.assert_called_once_with(
            ['git', 'status'],
            capture_output=True,
            text=True,
            check=False
        )
    
    @patch('subprocess.run')
    def test_run_git_command_with_error(self, mock_subprocess):
        """Test git command that returns an error"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: pathspec 'test.txt' did not match any files"
        mock_subprocess.return_value = mock_result
        
        returncode, stdout, stderr = self.runner.run_git_command(['add', 'test.txt'])
        
        assert returncode == 1
        assert stdout == ""
        assert stderr == "error: pathspec 'test.txt' did not match any files"
    
    @patch('subprocess.run')
    def test_run_git_command_with_multiple_args(self, mock_subprocess):
        """Test git command with multiple arguments"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Everything up-to-date"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        returncode, stdout, stderr = self.runner.run_git_command(['push', 'origin', 'main'])
        
        assert returncode == 0
        assert stdout == "Everything up-to-date"
        mock_subprocess.assert_called_once_with(
            ['git', 'push', 'origin', 'main'],
            capture_output=True,
            text=True,
            check=False
        )
    
    @patch('subprocess.run')
    def test_run_git_command_exception(self, mock_subprocess):
        """Test handling of subprocess exceptions"""
        mock_subprocess.side_effect = Exception("Command not found")
        
        returncode, stdout, stderr = self.runner.run_git_command(['status'])
        
        assert returncode == -1
        assert stdout == ""
        assert stderr == "Command not found"
    
    @patch('subprocess.run')
    def test_run_git_command_empty_args(self, mock_subprocess):
        """Test git command with no arguments"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Git help output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        returncode, stdout, stderr = self.runner.run_git_command([])
        
        assert returncode == 0
        assert stdout == "Git help output"
        mock_subprocess.assert_called_once_with(
            ['git'],
            capture_output=True,
            text=True,
            check=False
        )
    
    @patch('subprocess.run')
    def test_run_git_command_with_complex_output(self, mock_subprocess):
        """Test git command with complex multi-line output"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "On branch main\nYour branch is up to date with 'origin/main'.\n\nChanges to be committed:\n  modified:   test.py\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        returncode, stdout, stderr = self.runner.run_git_command(['status'])
        
        assert returncode == 0
        assert "Changes to be committed:" in stdout
        assert "modified:   test.py" in stdout
