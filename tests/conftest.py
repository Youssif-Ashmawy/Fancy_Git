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
        
        # Initialize git repo
        os.system("git init")
        os.system("git config user.name 'Test User'")
        os.system("git config user.email 'test@example.com'")
        
        # Create initial commit
        with open("README.md", "w") as f:
            f.write("# Test Repository\n")
        os.system("git add README.md")
        os.system("git commit -m 'Initial commit'")
        
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
