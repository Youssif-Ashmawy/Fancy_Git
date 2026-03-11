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
