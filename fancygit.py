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
        self.available_commands = self._load_commands()
        self.confirmation_enabled = self._load_confirmation_state()
        self.config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
    
    def _load_commands(self):
        """Dynamically load commands from command-list.txt file"""
        script_dir = os.path.dirname(os.path.realpath(__file__)) # Get the directory where this script is located (real-path)
        commands_file = os.path.join(script_dir, 'command-list.txt')
        try:
            with open(commands_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Warning: {commands_file} not found. No commands available.")
            return []
    
    def _load_confirmation_state(self):
        """Load confirmation state from config file"""
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('confirmation_enabled='):
                        return line.strip().split('=')[1].lower() == 'true'
        except FileNotFoundError:
            pass
        return True  # Default to enabled
    
    def _save_confirmation_state(self):
        """Save confirmation state to config file"""
        try:
            with open(self.config_file, 'w') as f:
                f.write(f'confirmation_enabled={self.confirmation_enabled}\n')
        except Exception as e:
            print(f"Warning: Could not save confirmation state: {e}")
    
    def toggle_confirmation(self, enable=None):
        """Toggle confirmation messages before executing commands
        
        Args:
            enable (bool, optional): If True, enable confirmations. If False, disable confirmations.
                                    If None, toggle current state.
        
        Returns:
            bool: Current confirmation state
        """
        if enable is None:
            self.confirmation_enabled = not self.confirmation_enabled
        else:
            self.confirmation_enabled = enable
        
        # Save the state to file
        self._save_confirmation_state()
        
        status = "enabled" if self.confirmation_enabled else "disabled"
        print(f"Confirmation messages {status}")
        return self.confirmation_enabled
    
    def execute_command(self, command, *args):
        """Unified dynamic command executor"""
        if command not in self.available_commands:
            print(f"Unknown command: {command}")
            print(f"Available commands: {', '.join(self.available_commands)}")
            return False
        
        # Handle confirmation command specially
        if command == 'confirmation':
            if args:
                arg = args[0].lower()
                if arg in ['on', 'enable', 'true', '1']:
                    return self.toggle_confirmation(True)
                elif arg in ['off', 'disable', 'false', '0']:
                    return self.toggle_confirmation(False)
                elif arg in ['toggle', 'switch']:
                    return self.toggle_confirmation()
                elif arg in ['status', 'check']:
                    status = "enabled" if self.confirmation_enabled else "disabled"
                    print(f"Confirmation messages are {status}")
                    return self.confirmation_enabled
                else:
                    print("Usage: confirmation [on|off|toggle|status]")
                    return False
            else:
                return self.toggle_confirmation()
        
        return self._command_handler(command, *args)
 
    # REFACTORED
    def _command_handler(self, command, *args):     # private function
        """A Generic git commands handler"""
        print(f"Running: git {command} {' '.join(args)}")

        returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
        messages = self.parser.detect_warnings_errors(stdout, stderr)
        
        if not messages:        # IF MSGS ARE EMPTY
            print("\n✅ No warnings or errors detected")
            
            if self.confirmation_enabled:
                response = input("No warning messages - enter 'y' to run the command: ").strip().lower()
                if response == 'y':
                    # Execute the command again to get actual output
                    returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
                    if stdout:
                        print(stdout)
                    if stderr:
                        print(stderr)
                    if not stdout and not stderr:
                        print("Command executed successfully!")
                    return True
                else:
                    print("Command cancelled.")
                    return False
            else:
                # Execute the command directly without confirmation
                returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
                if stdout:
                    print(stdout)
                if stderr:
                    print(stderr)
                if not stdout and not stderr:
                    print("Command executed successfully!")
                return True
        else:
            for message in messages:
                if message.severity != 'unknown':
                    if message.severity == 'error':
                        print("\n❌ Errors detected:")
                    elif message.severity == 'warning':
                        print("\n⚠️  Warnings detected:")
                    print(message)
            return False


    
    def get_repo_state(self):
        return None

    def parse_conflict(self):
        return None


def main():
    fancy_git = FancyGit()
    
    if len(sys.argv) < 2:
        print("Usage: python fancygit.py <command> [args...]")
        print(f"Available commands: {', '.join(fancy_git.available_commands)}")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    fancy_git.execute_command(command, *args)

if __name__ == "__main__":
    main()
