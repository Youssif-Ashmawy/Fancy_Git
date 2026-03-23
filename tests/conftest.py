import pytest
import tempfile
import os
import shutil
from pathlib import Path

@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing"""
    temp_dir = tempfile.mkdtemp(prefix="fancygit_test_")
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        # Initialize git repo with explicit commands for better Windows compatibility
        import subprocess
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        
        # Create initial commit
        with open("README.md", "w") as f:
            f.write("# Test Repository\n")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
        
        # Ensure working directory is clean
        subprocess.run(["git", "status"], check=True, capture_output=True)
        
        yield temp_dir
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_git_outputs():
    """Sample git command outputs for testing"""
    return {
        "clean_output": {
            "stdout": "On branch main\nnothing to commit, working tree clean\n",
            "stderr": ""
        },
        "error_output": {
            "stdout": "",
            "stderr": "error: pathspec 'nonexistent.txt' did not match any files\n"
        },
        "conflict_output": {
            "stdout": "",
            "stderr": "error: Merge conflict in README.md\n"
        },
        "warning_output": {
            "stdout": "warning: LF will be replaced by CRLF in README.md\n",
            "stderr": ""
        },
        "ahead_behind_output": {
            "stdout": "Your branch is ahead of 'origin/main' by 1 commit\n",
            "stderr": ""
        }
    }

@pytest.fixture
def mock_config_manager():
    """Mock config manager for testing AI components"""
    from unittest.mock import MagicMock
    from src.config_manager import ConfigManager
    
    mock_config = MagicMock()
    mock_config.analysis_provider = "ollama"
    mock_config.explanation_provider = "ollama"
    mock_config.translation_provider = "ollama"
    mock_config.ai_analysis_enabled = True
    mock_config.loading_animation = "dots"
    mock_config.ollama_max_retries = 3
    mock_config.openai_api_key = "test-key"
    mock_config.openai_model = "gpt-3.5-turbo"
    mock_config.openai_timeout = 30
    mock_config.anthropic_api_key = "test-key"
    mock_config.anthropic_model = "claude-3-sonnet-20240229"
    mock_config.anthropic_timeout = 30
    
    mock_cm = MagicMock(spec=ConfigManager)
    mock_cm.config = mock_config
    return mock_cm

@pytest.fixture
def sample_ai_messages():
    """Sample AI messages for testing error analysis"""
    return [
        {
            "severity": "error",
            "message": "fatal: not a git repository",
            "type": "NOT_GIT_REPO",
            "file": None,
            "line": None
        },
        {
            "severity": "warning", 
            "message": "warning: LF will be replaced by CRLF",
            "type": "LINE_ENDING",
            "file": "test.py",
            "line": None
        },
        {
            "severity": "error",
            "message": "error: merge conflict in README.md",
            "type": "MERGE_CONFLICT",
            "file": "README.md",
            "line": 42
        }
    ]

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    import tempfile
    import os
    from pathlib import Path
    
    temp_dir = tempfile.mkdtemp(prefix="fancygit_config_test_")
    config_path = Path(temp_dir) / ".fancygit_config"
    
    # Write sample config
    config_content = """analysis_provider=ollama
explanation_provider=openai
translation_provider=anthropic
ai_analysis_enabled=true
loading_animation=spinner
ollama_max_retries=5
"""
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    yield config_path
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
