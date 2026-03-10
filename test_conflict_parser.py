#!/usr/bin/env python3
"""
Test script for the conflict_parser function
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from fancygit import FancyGit

def create_test_conflict():
    """Create a test repository with merge conflicts"""
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="fancygit_test_")
    print(f"Creating test repository in: {test_dir}")
    
    # Initialize git repo
    os.chdir(test_dir)
    os.system("git init")
    os.system("git config user.name 'Test User'")
    os.system("git config user.email 'test@example.com'")
    
    # Create initial file
    with open("test_file.txt", "w") as f:
        f.write("Original content\nLine 2\nLine 3\n")
    
    os.system("git add test_file.txt")
    os.system("git commit -m 'Initial commit'")
    
    # Create a branch
    os.system("git checkout -b feature-branch")
    
    # Modify file in feature branch
    with open("test_file.txt", "w") as f:
        f.write("Original content\nFeature branch change\nLine 3\n")
    
    os.system("git add test_file.txt")
    os.system("git commit -m 'Feature branch change'")
    
    # Switch back to main and make conflicting change
    os.system("git checkout main")
    with open("test_file.txt", "w") as f:
        f.write("Original content\nMain branch change\nLine 3\n")
    
    os.system("git add test_file.txt")
    os.system("git commit -m 'Main branch change'")
    
    # Attempt merge to create conflict
    os.system("git merge feature-branch --no-edit")
    
    return test_dir

def test_conflict_parser():
    """Test the conflict_parser function"""
    print("=== Testing conflict_parser function ===\n")
    
    # Save current directory
    original_dir = os.getcwd()
    test_dir = None
    
    try:
        # Create test repository with conflicts
        test_dir = create_test_conflict()
        
        # Initialize FancyGit
        fancy_git = FancyGit()
        
        # Test the conflict_parser function
        print("Running conflict_parser...")
        conflicts = fancy_git.conflict_parser()
        
        if conflicts:
            print(f"\n✅ Found {len(conflicts)} conflict markers:")
            for i, conflict in enumerate(conflicts, 1):
                print(f"\n{i}. {conflict}")
        else:
            print("\n❌ No conflict markers found")
        
        # Also test repo state
        print("\n=== Repository State ===")
        repo_state = fancy_git.get_repo_state()
        print(f"Conflicts in repo state: {repo_state['conflicts']}")
        print(f"Working directory clean: {repo_state['clean']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        os.chdir(original_dir)
        if test_dir and os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n🧹 Cleaned up test directory: {test_dir}")

def test_with_existing_repo():
    """Test conflict_parser in current directory if it has conflicts"""
    print("=== Testing in current directory ===\n")
    
    try:
        fancy_git = FancyGit()
        
        # Check if we're in a git repo
        returncode, _, _ = fancy_git.runner.run_git_command(['status'])
        if returncode != 0:
            print("❌ Not in a git repository")
            return False
        
        # Get repo state
        repo_state = fancy_git.get_repo_state()
        
        if repo_state['conflicts']:
            print(f"Found {len(repo_state['conflicts'])} files with conflicts")
            conflicts = fancy_git.conflict_parser()
            
            if conflicts:
                print(f"✅ Found {len(conflicts)} conflict markers:")
                for conflict in conflicts:
                    print(f"  - {conflict.file}:{conflict.line} - {conflict.message}")
            else:
                print("❌ No conflict markers found despite conflicts in repo state")
        else:
            print("ℹ️  No conflicts found in current repository")
            print("To test with conflicts, run:")
            print("  git checkout -b temp-branch")
            print("  # Make conflicting changes")
            print("  git merge temp-branch")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("FancyGit conflict_parser Test Suite")
    print("=" * 50)
    
    # Test 1: Create test repository with conflicts
    print("\n1. Testing with automatically created conflicts:")
    success1 = test_conflict_parser()
    
    print("\n" + "=" * 50)
    
    # Test 2: Test in current directory (if git repo)
    print("\n2. Testing in current directory:")
    success2 = test_with_existing_repo()
    
    print("\n" + "=" * 50)
    print(f"\nTest Results:")
    print(f"  Auto-generated test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Current directory test: {'✅ PASS' if success2 else '❌ FAIL'}")
