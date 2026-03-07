#!/usr/bin/env python3

import sys
import os

# Add script directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from fancygit import FancyGit

def test_get_repo_state():
    """Test the get_repo_state function"""
    print("Testing get_repo_state function...")
    print("=" * 50)
    
    # Create FancyGit instance
    fancy_git = FancyGit()
    
    # Get repository state
    repo_state = fancy_git.get_repo_state()
    
    # Display results
    print(f"Current branch: {repo_state['branch']}")
    print(f"Working directory clean: {repo_state['clean']}")
    print(f"Ahead of remote: {repo_state['ahead']} commits")
    print(f"Behind remote: {repo_state['behind']} commits")
    
    print("\nFile status:")
    if repo_state['staged']:
        print(f"  Staged files: {repo_state['staged']}")
    else:
        print("  Staged files: None")
    
    if repo_state['modified']:
        print(f"  Modified files: {repo_state['modified']}")
    else:
        print("  Modified files: None")
    
    if repo_state['untracked']:
        print(f"  Untracked files: {repo_state['untracked']}")
    else:
        print("  Untracked files: None")
    
    if repo_state['conflicts']:
        print(f"  Conflicts: {repo_state['conflicts']}")
    else:
        print("  Conflicts: None")
    
    print("\nFull repo state dictionary:")
    print(repo_state)
    
    return repo_state

if __name__ == "__main__":
    test_get_repo_state()
