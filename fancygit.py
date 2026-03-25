#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import webbrowser
from prompt_toolkit import prompt

# Handle both direct execution and module import
try:
    from src.git_runner import GitRunner
    from src.git_error_parser import GitErrorParser
    from src.git_error import GitError
    from src.mermaid_export import MermaidExporter
    from src.git_insights import GitInsights
    from src.ollama_client import OllamaClient
    from src.loading_animation import LoadingContext
    from src.colors import Colors, color_command, color_success, color_error, color_warning, color_info, color_ai, color_header, color_file, color_branch
    from src.output_colorizer import OutputColorizer
    from welcome import show_welcome
except ImportError:
    # When installed as a module, add the current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from src.git_runner import GitRunner
    from src.git_error_parser import GitErrorParser
    from src.git_error import GitError
    from src.mermaid_export import MermaidExporter
    from src.git_insights import GitInsights
    from src.ollama_client import OllamaClient
    from src.loading_animation import LoadingContext
    from src.colors import Colors, color_command, color_success, color_error, color_warning, color_info, color_ai, color_header, color_file, color_branch
    from src.output_colorizer import OutputColorizer
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
        # Check color support first
        Colors.check_color_support()
        
        # initialize required components
        self.runner = GitRunner()
        self.parser = GitErrorParser()
        self.mermaid = MermaidExporter(self.runner)
        self.insights = GitInsights(self.runner)
        self.ollama = OllamaClient()
        self.output_colorizer = OutputColorizer()
        self.available_commands = self._load_commands()
        self.confirmation_enabled = self._load_confirmation_state()
        self.ai_analysis_enabled = self._load_ai_analysis_state()
        self.output_coloring_enabled = self._load_output_coloring_state()
        self.loading_animation_type = self._load_animation_type()
        self.config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
    
    def _load_commands(self):
        """Dynamically load commands from command-list.txt file"""
        script_dir = os.path.dirname(os.path.realpath(__file__)) # Get the directory where this script is located (real-path)
        commands_file = os.path.join(script_dir, 'command-list.txt')
        
        # Try the current directory first (for development/editable installs)
        if os.path.exists(commands_file):
            with open(commands_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        
        # Try site-packages root directory (for PyPI wheel installs)
        # Get the site-packages directory where this module is installed
        import sys
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            site_packages_dir = sys._MEIPASS
        else:
            # Regular pip install - get the directory containing this module
            site_packages_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        
        commands_file = os.path.join(site_packages_dir, 'command-list.txt')
        
        if os.path.exists(commands_file):
            with open(commands_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        
        print(color_warning(f"Warning: {commands_file} not found. No commands available."))
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
    
    def _load_ai_analysis_state(self):
        """Load AI analysis state from config file"""
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('ai_analysis_enabled='):
                        return line.strip().split('=')[1].lower() == 'true'
        except FileNotFoundError:
            pass
        return True  # Default to enabled
    
    def _load_animation_type(self):
        """Load loading animation type from config file"""
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('loading_animation='):
                        anim_type = line.strip().split('=')[1].strip()
                        valid_types = ['run', 'dots', 'progress', 'matrix', 'brain']
                        if anim_type in valid_types:
                            return anim_type
        except FileNotFoundError:
            pass
        return 'dots'  # Default to dots animation
    
    def _load_output_coloring_state(self):
        """Load output coloring state from config file"""
        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('output_coloring_enabled='):
                        return line.strip().split('=')[1].lower() == 'true'
        except FileNotFoundError:
            pass
        return True  # Default to enabled
    
    def _save_confirmation_state(self):
        """Save confirmation state to config file"""
        try:
            with open(self.config_file, 'w') as f:
                f.write(f'confirmation_enabled={self.confirmation_enabled}\n')
                f.write(f'ai_analysis_enabled={self.ai_analysis_enabled}\n')
                f.write(f'output_coloring_enabled={self.output_coloring_enabled}\n')
                f.write(f'loading_animation={self.loading_animation_type}\n')
        except Exception as e:
            print(color_warning(f"Warning: Could not save confirmation state: {e}"))
    
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
        print(color_info(f"Confirmation messages {status}"))
        return self.confirmation_enabled
    
    def toggle_ai_analysis(self, enable=None):
        """Toggle AI analysis of error messages
        
        Args:
            enable (bool, optional): If True, enable AI analysis. If False, disable AI analysis.
                                    If None, toggle current state.
        
        Returns:
            bool: Current AI analysis state
        """
        if enable is None:
            self.ai_analysis_enabled = not self.ai_analysis_enabled
        else:
            self.ai_analysis_enabled = enable
        
        # Save the state to file
        self._save_confirmation_state()
        
        status = "enabled" if self.ai_analysis_enabled else "disabled"
        print(color_info(f"AI error analysis {status}"))
        
        # Check Ollama connection when enabling
        if self.ai_analysis_enabled and not self.ollama.test_connection():
            print(color_warning("⚠️  Warning: Cannot connect to Ollama. Make sure Ollama is running on localhost:11434"))
            print(color_warning("   Install Ollama from https://ollama.ai/ and run 'ollama serve'"))
            self.ai_analysis_enabled = False
            self._save_confirmation_state()
            return False
        
        return self.ai_analysis_enabled
    
    def toggle_output_coloring(self, enable=None):
        """Toggle intelligent output coloring
        
        Args:
            enable (bool, optional): If True, enable output coloring. If False, disable output coloring.
                                    If None, toggle current state.
        
        Returns:
            bool: Current output coloring state
        """
        if enable is None:
            self.output_coloring_enabled = not self.output_coloring_enabled
        else:
            self.output_coloring_enabled = enable
        
        # Save the state to file
        self._save_confirmation_state()
        
        status = "enabled" if self.output_coloring_enabled else "disabled"
        print(color_info(f"Output coloring {status}"))
        return self.output_coloring_enabled
    
    def set_loading_animation(self, animation_type):
        """Set the loading animation type
        
        Args:
            animation_type (str): Type of animation ('run', 'dots', 'progress', 'matrix', 'brain')
        
        Returns:
            bool: True if animation type was set successfully, False otherwise
        """
        valid_types = ['run', 'dots', 'progress', 'matrix', 'brain']
        if animation_type in valid_types:
            self.loading_animation_type = animation_type
            self._save_confirmation_state()
            print(color_info(f"Loading animation set to: {animation_type}"))
            return True
        else:
            print(color_error(f"Invalid animation type. Valid options: {', '.join(valid_types)}"))
            return False
    
    def execute_command(self, command, *args):
        """Unified dynamic command executor"""
        if command not in self.available_commands:
            print(color_error(f"Unknown command: {command}"))
            print(color_info(f"Available commands: {', '.join(self.available_commands)}"))
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
                    print(color_info(f"Confirmation messages are {status}"))
                    return self.confirmation_enabled
                else:
                    print(color_warning("Usage: confirmation [on|off|toggle|status]"))
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
                    status = "enabled" if self.ai_analysis_enabled else "disabled"
                    print(color_info(f"AI error analysis is {status}"))
                    if self.ai_analysis_enabled:
                        if self.ollama.test_connection():
                            models = self.ollama.get_available_models()
                            print(color_success(f"Using model: {self.ollama.model}"))
                            if models:
                                print(color_info(f"Available models: {', '.join(models[:5])}"))
                        else:
                            print(color_warning("⚠️  Ollama is not connected"))
                    print(color_info(f"Loading animation: {self.loading_animation_type}"))
                    return self.ai_analysis_enabled
                elif arg in ['models', 'list']:
                    models = self.ollama.get_available_models()
                    if models:
                        print(color_info(f"Available Ollama models: {', '.join(models)}"))
                        print(color_success(f"Current model: {self.ollama.model}"))
                    else:
                        print(color_warning("No models available. Make sure Ollama is running."))
                    return True
                elif arg.startswith('model='):
                    model_name = arg.split('=', 1)[1]
                    if self.ollama.set_model(model_name):
                        print(color_success(f"Switched to model: {model_name}"))
                        return True
                    else:
                        print(color_error(f"Failed to switch to model: {model_name}"))
                        return False
                elif arg.startswith('animation='):
                    anim_type = arg.split('=', 1)[1]
                    return self.set_loading_animation(anim_type)
                elif arg == '--help':
                    print(color_header("AI Error Analysis Command"))
                    print(color_info("Usage: ai [on|off|toggle|status|models|model=<name>|animation=<type>]"))
                    print("  on|off|toggle : Enable/disable/toggle AI analysis")
                    print("  status        : Show current AI analysis status")
                    print("  models        : List available Ollama models")
                    print("  model=<name>  : Switch to specific model")
                    print("  animation=<type> : Set loading animation (run|dots|progress|matrix|brain)")
                    print("  --help        : Show this help")
                    return True
                else:
                    print(color_warning("Usage: ai [on|off|toggle|status|models|model=<name>|animation=<type>|--help]"))
                    return False
            else:
                return self.toggle_ai_analysis()

        # Handle output coloring command
        if command == 'colors':
            if args:
                arg = args[0].lower()
                if arg in ['on', 'enable', 'true', '1']:
                    return self.toggle_output_coloring(True)
                elif arg in ['off', 'disable', 'false', '0']:
                    return self.toggle_output_coloring(False)
                elif arg in ['toggle', 'switch']:
                    return self.toggle_output_coloring()
                elif arg in ['status', 'check']:
                    status = "enabled" if self.output_coloring_enabled else "disabled"
                    print(color_info(f"Output coloring is {status}"))
                    return self.output_coloring_enabled
                elif arg == '--help':
                    print(color_header("Output Coloring Command"))
                    print(color_info("Usage: colors [on|off|toggle|status]"))
                    print("  on|off|toggle : Enable/disable/toggle output coloring")
                    print("  status        : Show current output coloring status")
                    print("  --help        : Show this help")
                    return True
                else:
                    print(color_warning("Usage: colors [on|off|toggle|status]"))
                    return False
            else:
                return self.toggle_output_coloring()

        # Handle complete-push command
        if command == 'complete-push':
            return self.complete_push(*args)

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
                        print(color_error("Invalid --days value"))
                        return False
                elif arg.startswith('--format='):
                    output_format = arg.split('=', 1)[1].lower()
                    if output_format not in ['console', 'json']:
                        print(color_error("Invalid format. Use 'console' or 'json'"))
                        return False
                elif arg.startswith('--output='):
                    output_file = arg.split('=', 1)[1]
                elif arg == '--help':
                    print(color_header("Git Insights Command"))
                    print(color_info("Usage: insights [--days=N] [--format=console|json] [--output=filename]"))
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
                    print(color_success(f"Insights report saved to: {output_file}"))
                else:
                    print(output)
                
                return True
            except Exception as e:
                print(color_error(f"Failed to generate insights: {e}"))
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
                        print(color_error("Invalid --max-commits value"))
                        return False
                elif arg == '--no-open':
                    open_browser = False
                elif arg == '--help':
                    print(color_header("Git Repository Visualization Command"))
                    print(color_info("Usage: visualize [directory] [options]"))
                    print("")
                    print(color_info("Arguments:"))
                    print("  directory        : Output directory (default: .fancygit)")
                    print("                   Automatically prefixed with '.' to make hidden")
                    print("")
                    print(color_info("Options:"))
                    print("  --max-commits=N  : Maximum number of commits to include (default: 40)")
                    print("  --no-open        : Don't open HTML in browser automatically")
                    print("  --help           : Show this help message")
                    print("")
                    print(color_info("Examples:"))
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
                print(color_success("Mermaid export created:"))
                print(f"  Status: {color_file(paths['status_mmd'])}")
                print(f"  Graph : {color_file(paths['graph_mmd'])}")
                print(f"  Tree  : {color_file(paths['tree_mmd'])}")
                print(f"  Deps  : {color_file(paths['deps_mmd'])}")
                print(f"  HTML  : {color_file(paths['html'])}")

                if open_browser:
                    # Convert to absolute path for browser
                    html_path = os.path.abspath(paths['html'])
                    webbrowser.open(f"file://{html_path}")
                return True
            except Exception as e:
                print(color_error(f"Failed to visualize repo: {e}"))
                return False
        
        return self._command_handler(command, *args)
 
    # REFACTORED
    def _command_handler(self, command, *args):     # private function
        """A Generic git commands handler"""
        print(color_command(f"Running: git {command} {' '.join(args)}"))

        # Show confirmation before executing the command
        if self.confirmation_enabled:
            response = input(color_info(f"Execute 'git {command} {' '.join(args)}'? [y/N]: ")).strip().lower()
            if response != 'y':
                print(color_warning("Command cancelled."))
                return False

        # Execute the command
        returncode, stdout, stderr = self.runner.run_git_command([command] + list(args))
        messages = self.parser.detect_warnings_errors(stdout, stderr)
        
        # Colorize the output if enabled
        if self.output_coloring_enabled:
            colored_stdout, colored_stderr = self.output_colorizer.colorize_output(command, stdout, stderr)
        else:
            colored_stdout, colored_stderr = stdout, stderr
        
        if not messages:        # IF MSGS ARE EMPTY
            print(color_success("\n✅ No warnings or errors detected"))
            if colored_stdout:
                print(colored_stdout, flush=True)
            if colored_stderr:
                print(colored_stderr, flush=True)
            if not stdout and not stderr:
                print(color_success("Command executed successfully!"), flush=True)
            return True
        else:
            # Print colored output even with errors/warnings
            if colored_stdout:
                print(colored_stdout, flush=True)
            if colored_stderr:
                print(colored_stderr, flush=True)
                
            for message in messages:
                if message.severity != 'unknown':
                    if message.severity == 'error':
                        print(color_error("\n❌ Errors detected:"))
                    elif message.severity == 'warning':
                        print(color_warning("\n⚠️  Warnings detected:"))
                    print(message)
            
            # AI Analysis if enabled
            if self.ai_analysis_enabled:
                print(color_info("\n🤖 Analyzing with AI..."))
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
                        with LoadingContext(animation_type=self.loading_animation_type):
                            ai_analysis = self.ollama.analyze_error_messages(error_data)
                        
                        if ai_analysis:
                            print(color_ai("\n🧠 AI Analysis & Suggestions:"))
                            print(Colors.divider("-", 40))
                            print(color_ai(ai_analysis))
                            print(Colors.divider("-", 40))
                        else:
                            print(color_warning("⚠️  AI analysis failed"))
                    else:
                        print(color_warning("⚠️  No valid error data for AI analysis"))
                except Exception as e:
                    print(color_error(f"⚠️  AI analysis error: {e}"))
            
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
        output.append(Colors.divider("=", 60))
        output.append(color_header("🔍 GIT INSIGHTS REPORT"))
        output.append(Colors.divider("=", 60))
        output.append(color_info(f"Generated: {report['generated_at'][:19]}"))
        output.append(color_info(f"Analysis Period: {report['analysis_period_days']} days"))
        output.append("")
        
        # Summary
        summary = report['summary']
        output.append(color_header("📊 SUMMARY"))
        output.append(Colors.divider("-", 30))
        output.append(color_info(f"Total Commits: {summary['total_commits']}"))
        output.append(color_info(f"Active Contributors: {summary['active_contributors']}"))
        output.append(color_info(f"Active Branches: {summary['active_branches']}/{summary['total_branches']}"))
        output.append(color_info(f"Files Changed: {summary['total_files_changed']}"))
        output.append("")
        
        # Commit Frequency
        output.append(color_header("📈 COMMIT FREQUENCY"))
        output.append(Colors.divider("-", 40))
        commit_freq = report['commit_frequency']
        if commit_freq:
            for author, count in sorted(commit_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
                output.append(f"{color_info(author):20} : {color_success(str(count)):3} commits")
        else:
            output.append(color_warning("No commits found in the specified period"))
        output.append("")
        
        # Branch Analysis
        output.append(color_header("🌿 BRANCH ANALYSIS"))
        output.append(Colors.divider("-", 30))
        branches = report['branch_analysis']
        local_count = sum(1 for b in branches.values() if b['type'] == 'local')
        remote_count = sum(1 for b in branches.values() if b['type'] == 'remote')
        active_count = sum(1 for b in branches.values() if b['status'] == 'active')
        stale_count = len(branches) - active_count
        output.append(color_info(f"Local: {local_count}, Remote: {remote_count}"))
        output.append(color_info(f"Active: {active_count}, Stale: {stale_count}"))
        
        for branch, info in list(branches.items())[:12]:
            status_icon = "🟢" if info['status'] == 'active' else "🔴"
            type_icon = "🏠" if info['type'] == 'local' else "☁️"
            # Show full branch name without truncation
            branch_name = color_branch(branch.replace('local/', '').replace('remote/', ''), info['status'] == 'active')
            output.append(f"{status_icon}{type_icon} {branch_name:25} ({color_info(str(info['days_inactive']))} days)")
        output.append("")
        
        # File Hotspots
        output.append(color_header("🔥 FILE HOTSPOTS"))
        output.append(Colors.divider("-", 30))
        hotspots = report['file_hotspots']
        if hotspots:
            for file_path, count in sorted(hotspots.items(), key=lambda x: x[1], reverse=True)[:10]:
                # Truncate long file paths
                file_name = file_path[:25] + "..." if len(file_path) > 25 else file_path
                output.append(f"{color_file(file_name):28} : {color_warning(str(count)):3} changes")
        else:
            output.append(color_warning("No file changes found in the specified period"))
        output.append("")
        
        # Top Contributors
        output.append(color_header("👥 TOP CONTRIBUTORS"))
        output.append(Colors.divider("-", 30))
        contributors = report['contributor_stats']
        top_contributors = sorted(contributors.items(), 
                                key=lambda x: x[1]['commits'], reverse=True)[:5]
        
        for name, stats in top_contributors:
            # Truncate long names
            author_name = name[:18] + "..." if len(name) > 18 else name
            output.append(f"{color_info(author_name):18} : {color_success(str(stats['commits'])):3} commits, "
                        f"{color_success('+' + str(stats['lines_added']))} / {color_error('-' + str(stats['lines_removed']))} lines")
        
        output.append(Colors.divider("=", 60))
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

    def complete_push(self, *args):
        """Complete push command that pulls changes, stages files, commits, and pushes
        
        Usage: complete-push [files...] [--all] [--message="commit message"] [--no-pull] [--no-push]
        
        Args:
            files: Specific files to stage (optional)
            --all: Stage all changes (default if no files specified)
            --message: Custom commit message (if not provided, will prompt interactively)
            --no-pull: Skip pulling changes before committing
            --no-push: Skip pushing after committing
        """
        # Parse arguments
        files_to_stage = []
        commit_message = None
        pull_changes = True
        push_changes = True
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--all':
                files_to_stage = ['.']  # Stage all changes
            elif arg.startswith('--message='):
                commit_message = arg.split('=', 1)[1]
            elif arg == '--no-pull':
                pull_changes = False
            elif arg == '--no-push':
                push_changes = False
            elif arg == '--help':
                print(color_header("Complete Push Command"))
                print(color_info("Usage: complete-push [files...] [--all] [--message=\"commit message\"] [--no-pull] [--no-push]"))
                print("")
                print(color_info("Options:"))
                print("  files...       : Specific files to stage")
                print("  --all          : Stage all changes (default if no files specified)")
                print("  --message=... : Custom commit message")
                print("  --no-pull      : Skip pulling changes before committing")
                print("  --no-push      : Skip pushing after committing")
                print("  --help         : Show this help")
                print("")
                print(color_info("Examples:"))
                print("  complete-push                           # Interactive mode with all changes")
                print("  complete-push file1.py file2.py         # Stage specific files")
                print("  complete-push --all --message=\"Fix bug\" # Stage all with custom message")
                print("  complete-push --no-pull                 # Skip pulling changes")
                return True
            elif not arg.startswith('--'):
                files_to_stage.append(arg)
            i += 1
        
        # If no files specified, default to all changes
        if not files_to_stage:
            files_to_stage = ['.']
        
        print(color_header("🚀 Complete Push Workflow"))
        print(Colors.divider("=", 40))
        
        # Step 0: Branch selection
        print(color_info("🌿 Checking current branch..."))
        repo_state = self.get_repo_state()
        current_branch = repo_state.get('branch', 'unknown')
        
        print(color_info(f"Current branch: {color_branch(current_branch)}"))
        change_branch = input(color_info("Change branch? [Press Enter to keep current, or enter branch name]: ")).strip()
        
        if change_branch:
            # Switch to specified branch
            print(color_info(f"🔄 Switching to branch: {color_branch(change_branch)}"))
            returncode, stdout, stderr = self.runner.run_git_command(['checkout', change_branch])
            if returncode == 0:
                print(color_success(f"✅ Switched to branch: {change_branch}"))
                current_branch = change_branch
            else:
                print(color_error(f"❌ Failed to switch to branch: {change_branch}"))
                if stderr:
                    print(stderr.strip())
                return False
        else:
            print(color_success(f"✅ Staying on branch: {color_branch(current_branch)}"))
        
        # Step 0.5: Determine files to stage (show in dry run)
        # Check if specific files were provided in command line arguments
        specific_files_provided = any(arg and not arg.startswith('--') for arg in args)
        
        # If no specific files provided, show interactive file selection in dry run
        if not specific_files_provided:
            print(color_info("📋 Checking repository status..."))
            repo_state = self.get_repo_state()
            
            # Collect all available files
            available_files = []
            if repo_state['staged']:
                available_files.extend([('staged', f) for f in repo_state['staged']])
            if repo_state['modified']:
                available_files.extend([('modified', f) for f in repo_state['modified']])
            if repo_state['untracked']:
                available_files.extend([('untracked', f) for f in repo_state['untracked']])
            
            if available_files:
                print(color_header("\n📁 Available files to stage:"))
                for idx, (status, file_path) in enumerate(available_files, 1):
                    status_icon = {
                        'staged': '✅',
                        'modified': '📝', 
                        'untracked': '❓'
                    }.get(status, '📄')
                    print(f"  {idx:2d}. {status_icon} {color_file(file_path)} ({status})")
                
                print(color_info("\nSelect files to stage (Press Enter for all files, or enter numbers like 1,3,5 or 1-5 or 'staged' or 'modified' or 'untracked'):"))
                selection = input(color_info("Your choice: ")).strip()
                
                selected_files = []
                # Default to all files if empty input
                if not selection:
                    selected_files = [f for _, f in available_files]
                    print(color_success("✅ Selected all files"))
                elif selection == 'all':
                    selected_files = [f for _, f in available_files]
                elif selection in ['staged', 'modified', 'untracked']:
                    selected_files = [f for status, f in available_files if status == selection]
                else:
                    # Parse comma-separated numbers and ranges
                    try:
                        indices = []
                        for part in selection.split(','):
                            part = part.strip()
                            if '-' in part:
                                start, end = map(int, part.split('-'))
                                indices.extend(range(start, end + 1))
                            else:
                                indices.append(int(part))
                        
                        for idx in indices:
                            if 1 <= idx <= len(available_files):
                                selected_files.append(available_files[idx - 1][1])
                            else:
                                print(color_warning(f"Invalid index: {idx}"))
                    except ValueError:
                        print(color_error("Invalid selection format"))
                        return False
                
                files_to_stage = selected_files if selected_files else ['.']
            else:
                print(color_warning("No changes to stage"))
                return False
        
        # Step 1: Get commit message for dry run (with AI auto-suggestion)
        print(color_info("\n📝 Generating AI commit message suggestion..."))
        
        # Generate AI suggestion automatically
        ai_suggestion = None
        try:
            # Get repository state and staged changes for AI analysis
            repo_state = self.get_repo_state()
            
            # Get diff of files that will be staged
            diff_output = ""
            if files_to_stage == ['.']:
                # Get diff of all unstaged changes
                returncode, diff_output, stderr = self.runner.run_git_command(['diff'])
                if returncode != 0:
                    diff_output = ""
            else:
                # Get diff for specific files
                for file_path in files_to_stage:
                    returncode, file_diff, stderr = self.runner.run_git_command(['diff', file_path])
                    if returncode == 0 and file_diff:
                        diff_output += file_diff + "\n"
            
            if diff_output.strip():
                # Prepare context for AI
                context = {
                    'branch': current_branch,
                    'staged_files': files_to_stage if files_to_stage != ['.'] else ['all changes'],
                    'diff': diff_output[:2000]  # Limit diff size for AI processing
                }
                
                # Generate AI commit message
                with LoadingContext(animation_type=self.loading_animation_type):
                    ai_suggestion = self.ollama.generate_commit_message(context)
                
                if ai_suggestion:
                    print(color_ai(f"💡 AI Suggestion: '{ai_suggestion}'"))
                else:
                    print(color_warning("⚠️  AI suggestion failed"))
            else:
                print(color_warning("⚠️  No changes found for AI analysis"))
                
        except Exception as e:
            print(color_warning(f"⚠️  AI suggestion error: {e}"))
        
        # Now get user input with three options
        while True:
            if ai_suggestion:
                print(color_info("\nChoose an option:"))
                print(color_info("  1. Press Enter to use AI suggestion"))
                print(color_info("  2. Type your own commit message"))
                print(color_info("  3. Type 'm' to modify AI suggestion"))
                
                user_input = input(color_info("Your choice: ")).strip()
                
                if not user_input:
                    # Option 1: Use AI suggestion
                    commit_message = ai_suggestion
                    print(color_success(f"✅ Using AI suggestion: '{commit_message}'"))
                    break
                elif user_input.lower() == 'm':
                    # Option 3: Modify AI suggestion (like pressing up arrow)
                    commit_message = prompt(
                        "Modified commit message: ",
                        default=ai_suggestion
                    ).strip()
                    
                    if not commit_message:
                        commit_message = ai_suggestion
                        print(color_success(f"✅ Using original AI suggestion: '{commit_message}'"))
                    else:
                        print(color_success(f"✅ Using modified message: '{commit_message}'"))
                    break
                else:
                    # Option 2: User's own message
                    commit_message = user_input
                    print(color_success(f"✅ Using custom message: '{commit_message}'"))
                    break
            else:
                # No AI suggestion available, just ask for input
                commit_message = input(color_info("📝 Enter commit message: ")).strip()
                if commit_message:
                    break
                else:
                    print(color_warning("⚠️  Commit message cannot be empty. Please try again."))
        
        # Step 2: Dry Run - Show planned operations
        print(color_header("\n🔍 DRY RUN - Planned Operations"))
        print(Colors.divider("-", 50))
        
        print(color_info(f"🌿 Branch: {color_branch(current_branch)}"))
        if pull_changes:
            print(color_info("📥 Pull: git pull"))
        else:
            print(color_info("⏭️  Pull: SKIPPED"))
        
        if files_to_stage:
            print(color_info(f"📦 Stage: git add {' '.join(files_to_stage)}"))
        else:
            print(color_info("📦 Stage: No files to stage"))
        
        print(color_info(f"💾 Commit: git commit -m \"{commit_message}\""))
        
        if push_changes:
            print(color_info("📤 Push: git push"))
        else:
            print(color_info("⏭️  Push: SKIPPED"))
        
        print(Colors.divider("-", 50))
        
        # Step 3: Confirmation
        print(color_info("\n❓ Do you want to execute these operations?"))
        confirmation = input(color_info("[y/N]: ")).strip().lower()
        
        if confirmation not in ['y', 'yes']:
            print(color_warning("❌ Operation cancelled by user"))
            return False
        
        print(color_success("✅ Confirmed! Executing operations..."))
        print(Colors.divider("=", 40))
        
        # Step 4: Pull changes if enabled
        if pull_changes:
            print(color_info("📥 Pulling latest changes..."))
            returncode, stdout, stderr = self.runner.run_git_command(['pull'])
            if returncode == 0:
                print(color_success("✅ Pull completed successfully"))
                if stdout:
                    print(stdout.strip())
            else:
                print(color_warning("⚠️  Pull had issues, but continuing..."))
                if stderr:
                    print(stderr.strip())
        else:
            print(color_info("⏭️  Skipping pull changes"))
        
        # Step 5: Stage files
        print(color_info(f"\n📦 Staging files: {', '.join(files_to_stage)}"))
        returncode, stdout, stderr = self.runner.run_git_command(['add'] + files_to_stage)
        if returncode == 0:
            print(color_success("✅ Files staged successfully"))
        else:
            print(color_error("❌ Failed to stage files"))
            if stderr:
                print(stderr.strip())
            return False
        
        # Step 6: Commit changes
        print(color_info(f"\n💾 Committing with message: '{commit_message}'"))
        returncode, stdout, stderr = self.runner.run_git_command(['commit', '-m', commit_message])
        if returncode == 0:
            print(color_success("✅ Changes committed successfully"))
            if stdout:
                print(stdout.strip())
        else:
            print(color_error("❌ Failed to commit changes"))
            if stderr:
                print(stderr.strip())
            return False
        
        # Step 7: Push changes if enabled
        if push_changes:
            print(color_info("\n📤 Pushing changes..."))
            returncode, stdout, stderr = self.runner.run_git_command(['push'])
            if returncode == 0:
                print(color_success("✅ Changes pushed successfully"))
                if stdout:
                    print(stdout.strip())
            else:
                print(color_warning("⚠️  Push had issues"))
                if stderr:
                    print(stderr.strip())
        else:
            print(color_info("⏭️  Skipping push"))
        
        print(Colors.divider("=", 40))
        print(color_success("🎉 Complete push workflow completed!"))
        return True


def main():
    fancy_git = FancyGit()
    
    if len(sys.argv) < 2:
        print(color_error("Usage: python fancygit.py <command> [args...]"))
        print(color_info(f"Available commands: {', '.join(fancy_git.available_commands)}"))
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    fancy_git.execute_command(command, *args)

if __name__ == "__main__":
    main()
