#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import webbrowser
from src.git_runner import GitRunner
from src.git_error_parser import GitErrorParser
from src.git_error import GitError
from src.mermaid_export import MermaidExporter
from src.git_insights import GitInsights
from src.ollama_client import OllamaClient
from src.loading_animation import LoadingContext
from src.config_manager import ConfigManager
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
        self.config_manager = ConfigManager()
        self.runner = GitRunner()
        self.parser = GitErrorParser()
        self.mermaid = MermaidExporter(self.runner)
        self.insights = GitInsights(self.runner)
        self.ollama = OllamaClient()
        self.available_commands = self._load_commands()
    
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
    
    def toggle_confirmation(self, enable=None):
        """Toggle confirmation messages before executing commands
        
        Args:
            enable (bool, optional): If True, enable confirmations. If False, disable confirmations.
                                    If None, toggle current state.
        
        Returns:
            bool: Current confirmation state
        """
        if enable is None:
            self.config_manager.config.confirmation_enabled = not self.config_manager.config.confirmation_enabled
        else:
            self.config_manager.config.confirmation_enabled = enable
        
        # Save the state to file
        self.config_manager.save_config()
        
        status = "enabled" if self.config_manager.config.confirmation_enabled else "disabled"
        print(f"Confirmation messages {status}")
        return self.config_manager.config.confirmation_enabled
    
    def toggle_ai_analysis(self, enable=None):
        """Toggle AI analysis of error messages
        
        Args:
            enable (bool, optional): If True, enable AI analysis. If False, disable AI analysis.
                                    If None, toggle current state.
        
        Returns:
            bool: Current AI analysis state
        """
        if enable is None:
            self.config_manager.config.ai_analysis_enabled = not self.config_manager.config.ai_analysis_enabled
        else:
            self.config_manager.config.ai_analysis_enabled = enable
        
        # Save the state to file
        self.config_manager.save_config()
        
        status = "enabled" if self.config_manager.config.ai_analysis_enabled else "disabled"
        print(f"AI error analysis {status}")
        
        # Check Ollama connection when enabling
        if self.config_manager.config.ai_analysis_enabled and not self.ollama.test_connection():
            print("⚠️  Warning: Cannot connect to Ollama. Make sure Ollama is running on localhost:11434")
            print("   Install Ollama from https://ollama.ai/ and run 'ollama serve'")
            self.config_manager.config.ai_analysis_enabled = False
            self.config_manager.save_config()
            return False
        
        return self.config_manager.config.ai_analysis_enabled
    
    def set_loading_animation(self, animation_type):
        """Set the loading animation type
        
        Args:
            animation_type (str): Type of animation ('run', 'dots', 'progress', 'matrix', 'brain')
        
        Returns:
            bool: True if animation type was set successfully, False otherwise
        """
        valid_types = ['run', 'dots', 'progress', 'matrix', 'brain']
        if animation_type in valid_types:
            self.config_manager.config.loading_animation = animation_type
            self.config_manager.save_config()
            print(f"Loading animation set to: {animation_type}")
            return True
        else:
            print(f"Invalid animation type. Valid options: {', '.join(valid_types)}")
            return False
    

    def _get_remote_branches(self): 
        # first get remote branches 
        code, stdout, stderr = self.runner.run_git_command(['branch', '-r'])

        branches = []
        for line in stdout.splitlines():
            line = line.strip()

            if "->" in line:    # to ignore first line 
                continue

            branch = line.replace("origin/", "")    # to remove the origin thing
            branches.append(branch)

        return branches

    def _get_local_branches(self):
        code, stdout, stderr = self.runner.run_git_command(['branch'])
        
        branches = []
        for line in stdout.splitlines():
            line = line.strip()

            branch = line.replace("*", "")  # to replace the marker for "current branch"
            branches.append(branch)

        return branches

    def _get_new_branches(self):
        remote_branches = self._get_remote_branches()
        local_branches = self._get_local_branches()

        return [new_branch for new_branch in remote_branches if new_branch not in local_branches]

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
        
        if command.startswith('explain'):
            if not args:
                print("Usage: fancygit explain <command>")
                return True
            
            explain_command = args[0]
            previous_model = self.ollama.model  # saves old model

            # first switch model to codellama for better explanation
            if self.ollama.set_model('codellama'):
                print(f"Switched to model: codellama for explanation DISABLE THIS THIS IS A DEV COMMENT ONLY")
            else:
                print(f"Failed to switch to model: codellama. Explanation may be less accurate.")

            prompt = self.ollama._build_explain_prompt(explain_command)
            
            print("\n Explanation for command: git", explain_command)
            print("-" * 40)
            print(self.ollama._call_ollama(prompt))

            self.ollama.set_model(previous_model)
            print('switched back to default model')     # COMMENT THESE
            return True

        # Handle sync command which will 
        # - check for new remote branches
        # - get latest commits from remote
        # - remove deleted remote branches and the local ones that refer to them
        # - update current branch
        # - create local branches for the new remote branches
        # in just a single command "sync"
        if command == "sync":
            
            # by default fetch all first
            print("Fetching all branches and deleting remote ones....")
            code, stdout, stderr = self.runner.run_git_command(['fetch', '--all', '--prune'])
            print(code)
            print("Done completely!!")

            if '--all-branches' in args:
                new_branches = self._get_new_branches() # fetch new branches
                
                if new_branches:
                    print("\nNew remote branches detected:")
                    
                    for branch in new_branches:
                        print("  origin/", branch)

                    user_input = input("Create local branches to track these branches? (Y/n)").lower()

                    if user_input == 'y':
                        print("Creating local branches....")
                        for branch in new_branches:
                            self.runner.run_git_command(['checkout', '-b', branch, f"origin/{branch}"])     # ignore output for now cause well i cant find a use for it
                        
                        print("Done Creating local branches!!")
                        return
            elif '--ai-summary' in args:    # will implement a feature later that will changes smth like this
                # Warning: Your local branch is 12 commits behind origin/main.
                # Large pull detected.
                # Would you like a summary of incoming changes? (AI)
                # Incoming changes summary:
                # • New authentication middleware
                # • Refactor of merge parser
                # • Bug fix in CLI command loader


                None
            return
        
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
                    status = "enabled" if self.config_manager.config.confirmation_enabled else "disabled"
                    print(f"Confirmation messages are {status}")
                    return self.config_manager.config.confirmation_enabled
                else:
                    print("Usage: confirmation [on|off|toggle|status]")
                    return False
            else:
                return self.toggle_confirmation()
        
        # Handle AI analysis command
        if command == 'ai':
            if args:
                arg = args[0].lower()
                if arg in ['on', 'enable', 'true', '1']:
                    return self.toggle_ai_analysis(True)
                elif arg in ['off', 'disable', 'false', '0']:
                    return self.toggle_ai_analysis(False)
                elif arg in ['toggle', 'switch']:
                    return self.toggle_ai_analysis()
                elif arg in ['status', 'check']:
                    status = "enabled" if self.config_manager.config.ai_analysis_enabled else "disabled"
                    print(f"AI error analysis is {status}")
                    if self.config_manager.config.ai_analysis_enabled:
                        if self.ollama.test_connection():
                            models = self.ollama.get_available_models()
                            print(f"Using model: {self.ollama.model}")
                            if models:
                                print(f"Available models: {', '.join(models[:5])}")
                        else:
                            print("⚠️  Ollama is not connected")
                    print(f"Loading animation: {self.config_manager.config.loading_animation}")
                    return self.config_manager.config.ai_analysis_enabled
                elif arg in ['models', 'list']:
                    models = self.ollama.get_available_models()
                    if models:
                        print(f"Available Ollama models: {', '.join(models)}")
                        print(f"Current model: {self.ollama.model}")
                    else:
                        print("No models available. Make sure Ollama is running.")
                    return True
                elif arg.startswith('model='):
                    model_name = arg.split('=', 1)[1]
                    if self.ollama.set_model(model_name):
                        print(f"Switched to model: {model_name}")
                        return True
                    else:
                        print(f"Failed to switch to model: {model_name}")
                        return False
                elif arg.startswith('animation='):
                    anim_type = arg.split('=', 1)[1]
                    return self.set_loading_animation(anim_type)
                elif arg == '--help':
                    print("AI Error Analysis Command")
                    print("Usage: ai [on|off|toggle|status|models|model=<name>|animation=<type>]")
                    print("  on|off|toggle : Enable/disable/toggle AI analysis")
                    print("  status        : Show current AI analysis status")
                    print("  models        : List available Ollama models")
                    print("  model=<name>  : Switch to specific model")
                    print("  animation=<type> : Set loading animation (run|dots|progress|matrix|brain)")
                    print("  --help        : Show this help")
                    return True
                else:
                    print("Usage: ai [on|off|toggle|status|models|model=<name>|animation=<type>|--help]")
                    return False
            else:
                return self.toggle_ai_analysis()

        # Handle insights command
        if command == 'insights':
            days = 30  # default
            output_format = 'console'  # default
            output_file = None
            
            # Parse arguments
            i = 0
            while i < len(args):
                arg = args[i]
                if arg.startswith('--days='):
                    try:
                        days = int(arg.split('=', 1)[1])
                    except ValueError:
                        print("Invalid --days value")
                        return False
                elif arg.startswith('--format='):
                    output_format = arg.split('=', 1)[1].lower()
                    if output_format not in ['console', 'json']:
                        print("Invalid format. Use 'console' or 'json'")
                        return False
                elif arg.startswith('--output='):
                    output_file = arg.split('=', 1)[1]
                elif arg == '--help':
                    print("Git Insights Command")
                    print("Usage: insights [--days=N] [--format=console|json] [--output=filename]")
                    print("  --days=N        : Analysis period in days (default: 30)")
                    print("  --format=...   : Output format (default: console)")
                    print("  --output=...   : Save to file (optional)")
                    print("  --help         : Show this help")
                    return True
                i += 1
            
            try:
                report = self.insights.generate_insights_report(days)
                
                if output_format == 'json':
                    import json
                    output = json.dumps(report, indent=2)
                else:
                    output = self._format_insights_console(report)
                
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(output)
                    print(f"Insights report saved to: {output_file}")
                else:
                    print(output)
                
                return True
            except Exception as e:
                print(f"Failed to generate insights: {e}")
                return False
        # Mermaid repo visualization
        if command == 'visualize':
            output_dir = os.path.join(os.getcwd(), '.fancygit')
            max_commits = 40
            open_browser = True
            
            # Parse arguments properly
            i = 0
            while i < len(args):
                arg = args[i]
                if arg.startswith('--max-commits='):
                    try:
                        max_commits = int(arg.split('=', 1)[1])
                    except ValueError:
                        print("Invalid --max-commits value")
                        return False
                elif arg == '--no-open':
                    open_browser = False
                elif arg == '--help':
                    print("Git Repository Visualization Command")
                    print("Usage: visualize [directory] [options]")
                    print("")
                    print("Arguments:")
                    print("  directory        : Output directory (default: .fancygit)")
                    print("                   Automatically prefixed with '.' to make hidden")
                    print("")
                    print("Options:")
                    print("  --max-commits=N  : Maximum number of commits to include (default: 40)")
                    print("  --no-open        : Don't open HTML in browser automatically")
                    print("  --help           : Show this help message")
                    print("")
                    print("Examples:")
                    print("  visualize                    # Use default settings")
                    print("  visualize my_output           # Create .my_output directory")
                    print("  visualize --max-commits=20    # Limit to 20 commits")
                    print("  visualize --no-open           # Don't open browser")
                    print("  visualize test --max-commits=10 # Create .test with 10 commits")
                    return True
                elif not arg.startswith('--'):
                    # This is the output directory (positional argument)
                    # Automatically prefix with '.' to make it hidden
                    output_dir = '.' + arg if not arg.startswith('.') else arg
                i += 1

            try:
                repo_state = self.get_repo_state()
                paths = self.mermaid.export_all(output_dir=output_dir, repo_state=repo_state, max_commits=max_commits)
                print("Mermaid export created:")
                print(f"  Status: {paths['status_mmd']}")
                print(f"  Graph : {paths['graph_mmd']}")
                print(f"  Tree  : {paths['tree_mmd']}")
                print(f"  Deps  : {paths['deps_mmd']}")
                print(f"  HTML  : {paths['html']}")

                if open_browser:
                    # Convert to absolute path for browser
                    html_path = os.path.abspath(paths['html'])
                    webbrowser.open(f"file://{html_path}")
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
        if self.config_manager.config.confirmation_enabled:
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
            
            # AI Analysis if enabled
            if self.config_manager.config.ai_analysis_enabled:
                print("\n🤖 Analyzing with AI...")
                try:
                    # Convert GitError objects to dictionaries for analysis
                    error_data = []
                    for msg in messages:
                        if msg.severity != 'unknown':
                            error_dict = {
                                'severity': msg.severity,
                                'type': msg.type,
                                'message': msg.message,
                                'file': msg.file,
                                'line': msg.line
                            }
                            error_data.append(error_dict)
                    
                    if error_data:
                        # Start loading animation during AI analysis
                        with LoadingContext(animation_type=self.config_manager.config.loading_animation):
                            ai_analysis = self.ollama.analyze_error_messages(error_data)
                        
                        if ai_analysis:
                            print("\n🧠 AI Analysis & Suggestions:")
                            print("-" * 40)
                            print(ai_analysis)
                            print("-" * 40)
                        else:
                            print("⚠️  AI analysis failed")
                except Exception as e:
                    print(f"⚠️  AI analysis error: {e}")
            
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

    def _format_insights_console(self, report):
        """Format insights report for console display"""
        output = []
        output.append("=" * 60)
        output.append("🔍 GIT INSIGHTS REPORT")
        output.append("=" * 60)
        output.append(f"Generated: {report['generated_at'][:19]}")
        output.append(f"Analysis Period: {report['analysis_period_days']} days")
        output.append("")
        
        # Summary
        summary = report['summary']
        output.append("📊 SUMMARY")
        output.append("-" * 30)
        output.append(f"Total Commits: {summary['total_commits']}")
        output.append(f"Active Contributors: {summary['active_contributors']}")
        output.append(f"Active Branches: {summary['active_branches']}/{summary['total_branches']}")
        output.append(f"Files Changed: {summary['total_files_changed']}")
        output.append("")
        
        # Commit Frequency
        output.append("📈 COMMIT FREQUENCY")
        output.append("-" * 40)
        commit_freq = report['commit_frequency']
        if commit_freq:
            for author, count in sorted(commit_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
                output.append(f"{author:20} : {count:3} commits")
        else:
            output.append("No commits found in the specified period")
        output.append("")
        
        # Branch Analysis
        output.append("🌿 BRANCH ANALYSIS")
        output.append("-" * 30)
        branches = report['branch_analysis']
        local_count = sum(1 for b in branches.values() if b['type'] == 'local')
        remote_count = sum(1 for b in branches.values() if b['type'] == 'remote')
        active_count = sum(1 for b in branches.values() if b['status'] == 'active')
        stale_count = len(branches) - active_count
        output.append(f"Local: {local_count}, Remote: {remote_count}")
        output.append(f"Active: {active_count}, Stale: {stale_count}")
        
        for branch, info in list(branches.items())[:12]:
            status_icon = "🟢" if info['status'] == 'active' else "🔴"
            type_icon = "🏠" if info['type'] == 'local' else "☁️"
            # Show full branch name without truncation
            output.append(f"{status_icon}{type_icon} {branch:25} ({info['days_inactive']} days)")
        output.append("")
        
        # File Hotspots
        output.append("🔥 FILE HOTSPOTS")
        output.append("-" * 30)
        hotspots = report['file_hotspots']
        if hotspots:
            for file_path, count in sorted(hotspots.items(), key=lambda x: x[1], reverse=True)[:10]:
                # Truncate long file paths
                file_name = file_path[:25] + "..." if len(file_path) > 25 else file_path
                output.append(f"{file_name:28} : {count:3} changes")
        else:
            output.append("No file changes found in the specified period")
        output.append("")
        
        # Top Contributors
        output.append("👥 TOP CONTRIBUTORS")
        output.append("-" * 30)
        contributors = report['contributor_stats']
        top_contributors = sorted(contributors.items(), 
                                key=lambda x: x[1]['commits'], reverse=True)[:5]
        
        for name, stats in top_contributors:
            # Truncate long names
            author_name = name[:18] + "..." if len(name) > 18 else name
            output.append(f"{author_name:18} : {stats['commits']:3} commits, "
                        f"+{stats['lines_added']} / -{stats['lines_removed']} lines")
        
        output.append("=" * 60)
        return "\n".join(output)

    def conflict_parser(self):
        """Parse conflict markers in files that have merge conflicts
        
        Returns:
            list: List of GitError objects representing conflict markers found
        """
        conflicts = []
        
        # Get current repository state to identify files with conflicts
        repo_state = self.get_repo_state()
        conflict_files = repo_state.get('conflicts', [])
        
        if not conflict_files:
            return conflicts
        
        # Conflict marker patterns
        conflict_markers = [
            (r'^<<<<<<< (.+)$', 'CONFLICT_START'),
            (r'^=======\s*$', 'CONFLICT_SEPARATOR'),
            (r'^>>>>>>> (.+)$', 'CONFLICT_END')
        ]
        
        for file_path in conflict_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, conflict_type in conflict_markers:
                        match = re.match(pattern, line.strip())
                        if match:
                            # Extract additional info from match if available
                            additional_info = match.group(1) if match.groups() else None
                            
                            error = GitError(
                                source='file_content',
                                message=f"Conflict marker '{conflict_type}' found in {file_path}",
                                severity='error',
                                type='MERGE_CONFLICT',
                                file=file_path,
                                line=line_num
                            )
                            conflicts.append(error)
                            
            except FileNotFoundError:
                # File might have been deleted during merge
                error = GitError(
                    source='file_system',
                    message=f"Conflict file not found: {file_path}",
                    severity='error',
                    type='MERGE_CONFLICT',
                    file=file_path,
                    line=None
                )
                conflicts.append(error)
            except Exception as e:
                error = GitError(
                    source='file_system',
                    message=f"Error reading conflict file {file_path}: {str(e)}",
                    severity='error',
                    type='MERGE_CONFLICT',
                    file=file_path,
                    line=None
                )
                conflicts.append(error)
        
        return conflicts


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
