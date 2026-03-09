#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import webbrowser
from src.git_runner import GitRunner
from src.git_error_parser import GitErrorParser
from src.mermaid_export import MermaidExporter
from welcome import show_welcome

#region LAUNCHER RELATED IMPORTS
# Add script directory to Python path so imports work from anywhere
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

COMMAND_FILE = BASE_DIR / "command-list.txt"
CONFIG_FILE = BASE_DIR / ".fancygit_config"
#endregion

class FancyGit:
    def __init__(self):
        # initialize required components
        self.runner = GitRunner()
        self.parser = GitErrorParser()
        self.mermaid = MermaidExporter(self.runner)
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
        
        # Handle welcome command
        if command == 'welcome':
            show_welcome()
            return True
        
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

        # Mermaid repo visualization
        if command == 'visualize':
            output_dir = args[0] if len(args) >= 1 else os.path.join(os.getcwd(), '.fancygit')
            max_commits = 40
            open_browser = True

            for a in args[1:]:
                if a.startswith('--max-commits='):
                    try:
                        max_commits = int(a.split('=', 1)[1])
                    except ValueError:
                        print("Invalid --max-commits value")
                        return False
                elif a == '--no-open':
                    open_browser = False

            try:
                repo_state = self.get_repo_state()
                paths = self.mermaid.export_all(output_dir=output_dir, repo_state=repo_state, max_commits=max_commits)
                print("Mermaid export created:")
                print(f"  Status: {paths['status_mmd']}")
                print(f"  Graph : {paths['graph_mmd']}")
                print(f"  HTML  : {paths['html']}")

                if open_browser:
                    webbrowser.open(f"file://{paths['html']}")
                return True
            except Exception as e:
                print(f"Failed to visualize repo: {e}")
                return False
        
        return self._command_handler(command, *args)
 
    # REFACTORED
    def _command_handler(self, command, *args):     # private function
        """A Generic git commands handler"""
        print(f"Running: git {command} {' '.join(args)}")

        # Show confirmation before executing the command
        if self.confirmation_enabled:
            response = input(f"Execute 'git {command} {' '.join(args)}'? [y/N]: ").strip().lower()
            if response != 'y':
                print("Command cancelled.")
                return False

        # Execute the command
        returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
        messages = self.parser.detect_warnings_errors(stdout, stderr)
        
        if not messages:        # IF MSGS ARE EMPTY
            print("\n✅ No warnings or errors detected")
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
        """Get the current state of the git repository
        
        Returns:
            dict: Repository state information including:
                - branch: Current branch name
                - staged: List of staged files
                - modified: List of modified files
                - untracked: List of untracked files
                - conflicts: List of files in conflict
                - clean: Boolean indicating if working directory is clean
                - ahead: Number of commits ahead of remote
                - behind: Number of commits behind remote
        """
        repo_state = {
            'branch': None,
            'staged': [],
            'modified': [],
            'untracked': [],
            'conflicts': [],
            'clean': False,
            'ahead': 0,
            'behind': 0
        }
        
        # Get current branch
        returncode, stdout, stderr = self.runner.run_git_command(['branch', '--show-current'])
        if returncode == 0 and stdout:
            repo_state['branch'] = stdout.strip()
        
        # Get porcelain status for parsing
        returncode, stdout, stderr = self.runner.run_git_command(['status', '--porcelain'])
        if returncode == 0 and stdout:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    status = line[:2]
                    file_path = line[2:].strip()  # Skip 2 chars and strip whitespace
                    
                    if status == 'UU':
                        repo_state['conflicts'].append(file_path)
                    elif status[0] in ['A', 'M', 'D', 'R', 'C']:
                        repo_state['staged'].append(file_path)
                    elif status[1] in ['M', 'D']:
                        repo_state['modified'].append(file_path)
                    elif status == '??':
                        repo_state['untracked'].append(file_path)
        
        # Check if working directory is clean
        repo_state['clean'] = (not repo_state['staged'] and 
                              not repo_state['modified'] and 
                              not repo_state['untracked'] and 
                              not repo_state['conflicts'])
        
        # Get ahead/behind information
        returncode, stdout, stderr = self.runner.run_git_command(['rev-list', '--count', '--left-right', f'@{{u}}...HEAD'])
        if returncode == 0 and stdout:
            counts = stdout.strip().split('\t')
            if len(counts) == 2:
                repo_state['behind'] = int(counts[0])
                repo_state['ahead'] = int(counts[1])
        
        return repo_state

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
