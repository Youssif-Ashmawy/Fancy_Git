#!/usr/bin/env python3
import subprocess
import sys
import re

class FancyGit:
    def __init__(self):
        self.git_cmd = "git"
    
    def run_git_command(self, args):
        """Run git command and capture output"""
        try:
            cmd = [self.git_cmd] + args
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def detect_warnings_errors(self, stdout, stderr):
        """Detect warnings and errors in git output"""
        warnings = []
        errors = []
        
        # Common git error patterns
        error_patterns = [
            r'error:',
            r'fatal:',
            r'failed',
            r'rejected',
            r'conflict',
            r'merge conflict',
            r'unable to'
        ]
        
        # Common git warning patterns
        warning_patterns = [
            r'warning:',
            r'WARNING:',
            r'behind',
            r'ahead',
            r'diverged'
        ]
        
        # Check stderr for errors
        for pattern in error_patterns:
            matches = re.findall(f'{pattern}.*', stderr, re.IGNORECASE)
            errors.extend(matches)
        
        # Check stdout for errors
        for pattern in error_patterns:
            matches = re.findall(f'{pattern}.*', stdout, re.IGNORECASE)
            errors.extend(matches)
        
        # Check stderr for warnings
        for pattern in warning_patterns:
            matches = re.findall(f'{pattern}.*', stderr, re.IGNORECASE)
            warnings.extend(matches)
        
        # Check stdout for warnings
        for pattern in warning_patterns:
            matches = re.findall(f'{pattern}.*', stdout, re.IGNORECASE)
            warnings.extend(matches)
        
        return warnings, errors
    
    def push(self, *args):
        """Handle git push command"""
        print(f"Running: git push {' '.join(args)}")
        returncode, stdout, stderr = self.run_git_command(['push'] + list(args))
        
        warnings, errors = self.detect_warnings_errors(stdout, stderr)
        
        if errors:
            print("\n❌ Errors detected:")
            for error in errors:
                print(f"  {error}")
            return False
        elif warnings:
            print("\n⚠️  Warnings detected:")
            for warning in warnings:
                print(f"  {warning}")
            return False
        else:
            print("\n✅ No warnings or errors detected")
            response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
            if response == 'y':
                print("Command executed successfully!")
                return True
            else:
                print("Command cancelled.")
                return False
    
    def pull(self, *args):
        """Handle git pull command"""
        print(f"Running: git pull {' '.join(args)}")
        returncode, stdout, stderr = self.run_git_command(['pull'] + list(args))
        
        warnings, errors = self.detect_warnings_errors(stdout, stderr)
        
        if errors:
            print("\n❌ Errors detected:")
            for error in errors:
                print(f"  {error}")
            return False
        elif warnings:
            print("\n⚠️  Warnings detected:")
            for warning in warnings:
                print(f"  {warning}")
            return False
        else:
            print("\n✅ No warnings or errors detected")
            response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
            if response == 'y':
                print("Command executed successfully!")
                return True
            else:
                print("Command cancelled.")
                return False

    def add(self, *args):
        """Handle git add command"""
        print(f"Running: git add {' '.join(args)}")
        returncode, stdout, stderr = self.run_git_command(['add'] + list(args))
        
        warnings, errors = self.detect_warnings_errors(stdout, stderr)
        
        if errors:
            print("\n❌ Errors detected:")
            for error in errors:
                print(f"  {error}")
            return False
        elif warnings:
            print("\n⚠️  Warnings detected:")
            for warning in warnings:
                print(f"  {warning}")
            return False
        else:
            print("\n✅ No warnings or errors detected")
            response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
            if response == 'y':
                print("Command executed successfully!")
                return True
            else:
                print("Command cancelled.")
                return False
    
    def commit(self, *args):
        """Handle git commit command"""
        print(f"Running: git commit {' '.join(args)}")
        returncode, stdout, stderr = self.run_git_command(['commit'] + list(args))
        
        warnings, errors = self.detect_warnings_errors(stdout, stderr)
        
        if errors:
            print("\n❌ Errors detected:")
            for error in errors:
                print(f"  {error}")
            return False
        elif warnings:
            print("\n⚠️  Warnings detected:")
            for warning in warnings:
                print(f"  {warning}")
            return False
        else:
            print("\n✅ No warnings or errors detected")
            response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
            if response == 'y':
                print("Command executed successfully!")
                return True
            else:
                print("Command cancelled.")
                return False

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
