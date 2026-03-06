#!/usr/bin/env python3
import subprocess
import re
import sys
import os

# Add script directory to Python path so imports work from anywhere
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from src.git_runner import GitRunner
from src.git_error_parser import GitErrorParser
class FancyGit:
    def __init__(self):
        # initialize required components
        self.runner = GitRunner()
        self.parser = GitErrorParser()
 
    # REFACTORED
    def _command_handler(self, command, *args):     # private function
        """A Generic git commands handler"""
        print(f"Running: git {command} {' '.join(args)}")

        returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
        messages = self.parser.detect_warnings_errors(stdout, stderr)
        
        if not messages:        # IF MSGS ARE EMPTY
            print("\n✅ No warnings or errors detected")
            response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
            if response == 'y':
                print("Command executed successfully!")
                # return True       # no idea why u did this
            else:
                print("Command cancelled.")
                # return False      # again ill comment it out it has no impact
        else:
            for message in messages:
                if message.severity != 'unknown':
                    if message.severity == 'error':
                        print("\n❌ Errors detected:")
                    elif message.severity == 'warning':
                        print("\n⚠️  Warnings detected:")
                    print(message)

    def push(self, *args):
        """Handle git push command"""
        self._command_handler('push', *args)
    
    def pull(self, *args):
        """Handle git pull command"""
        self._command_handler('pull', *args)

    def add(self, *args):
        """Handle git add command"""
        self._command_handler('add', *args)
    
    def commit(self, *args):
        """Handle git commit command"""
        self._command_handler('commit', *args)
    #-------------------------------------

    
    def get_repo_state(self):
        return None

    def parse_conflict(self):
        return None


def main():
    fancy_git = FancyGit()
    
    if len(sys.argv) < 2:
        print("Usage: python fancygit.py <command> [args...]")
        print("Available commands: add, commit, push, pull")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    if command == 'add':
        fancy_git.add(*args)
    elif command == 'commit':
        fancy_git.commit(*args)
    elif command == 'push':
        fancy_git.push(*args)
    elif command == 'pull':
        fancy_git.pull(*args)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: add, commit, push, pull")
        sys.exit(1)

if __name__ == "__main__":
    main()
