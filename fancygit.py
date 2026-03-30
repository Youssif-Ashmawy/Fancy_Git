#!/usr/bin/env python3
import subprocess
import re
import sys
import signal
import os
import webbrowser
import json
import random
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from prompt_toolkit import prompt

# Handle both direct execution and module import
try:
    from src.git_runner import GitRunner
    from src.git_error_parser import GitErrorParser
    from src.git_error import GitError
    from src.mermaid_export import MermaidExporter
    from src.git_insights import GitInsights
    # from src.ollama_client import OllamaClient
    from src.ai_engine import AIEngine
    from src.loading_animation import LoadingContext
    from src.colors import Colors, color_command, color_success, color_error, color_warning, color_info, color_ai, color_header, color_file, color_branch
    from src.output_colorizer import OutputColorizer
    from src.quiz_manager import QuizManager
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
    # from src.ollama_client import OllamaClient
    from src.ai_engine import AIEngine
    from src.loading_animation import LoadingContext
    from src.colors import Colors, color_command, color_success, color_error, color_warning, color_info, color_ai, color_header, color_file, color_branch
    from src.output_colorizer import OutputColorizer
    from src.quiz_manager import QuizManager
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
        self.config_manager = ConfigManager()
        self.runner = GitRunner()
        self.parser = GitErrorParser()
        self.mermaid = MermaidExporter(self.runner)
        self.insights = GitInsights(self.runner)
        # self.ollama = OllamaClient()
        self.output_colorizer = OutputColorizer()
        self.config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        
        # Initialize quiz manager
        self.quiz_manager = QuizManager()
    
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
        
        # Check AI provider connection when enabling
        if self.config_manager.config.ai_analysis_enabled and not self.ai_engine.analysis_provider.test_connection():
            print(color_warning("⚠️  Warning: Cannot connect to AI provider. Make sure it's running."))
            self.config_manager.config.ai_analysis_enabled = False
            self.config_manager.save_config()
            return False
        
        return self.config_manager.config.ai_analysis_enabled
    
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
        self.config_manager.save_config()
        
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
            self.config_manager.config.loading_animation = animation_type
            self.config_manager.save_config()
            print(color_info(f"Loading animation set to: {animation_type}"))
            return True
        else:
            print(color_error(f"Invalid animation type. Valid options: {', '.join(valid_types)}"))
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
            print(color_error(f"Unknown command: {command}"))
            print(color_info(f"Available commands: {', '.join(self.available_commands)}"))
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
            
            print(f"\n Explanation for command: git {explain_command}")
            print("-" * 40)
            
            with LoadingContext(animation_type=self.config_manager.config.loading_animation):
                response = self.ai_engine.explain_command(explain_command)
                
            if response:
                print(response)
            else:
                print("⚠️ Failed to get explanation from AI.")

            return True

        # Handle sync command which will 
        # - check for new remote branches
        # - get latest commits from remote
        # - remove deleted remote branches and the local ones that refer to them
        # - update current branch
        # - create local branches for the new remote branches
        # in just a single command "sync"
        if command == "sync":
            print("Fetching all branches and pruning deleted remote branches...")
            code, stdout, stderr = self.runner.run_git_command(['fetch', '--all', '--prune'])
            
            if code == 0:
                if stdout.strip() or stderr.strip():
                    print(stdout.strip() if stdout.strip() else stderr.strip())
                print("✅ Fetch completed successfully!")
            else:
                print("❌ Failed to fetch branches.")
                print(stderr)

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
                    status = "enabled" if self.config_manager.config.ai_analysis_enabled else "disabled"
                    print(color_info(f"AI error analysis is {status}"))
                    if self.config_manager.config.ai_analysis_enabled:
                        if self.ai_engine.analysis_provider.test_connection():
                            # get_available_models and model are Ollama-specific
                            from src.providers.ollama_model import OllamaModel
                            if isinstance(self.ai_engine.analysis_provider, OllamaModel):
                                models = self.ai_engine.analysis_provider.get_available_models()
                                print(color_success(f"Using model: {self.ai_engine.analysis_provider.model}"))
                                if models:
                                    print(color_info(f"Available models: {', '.join(models[:5])}"))
                            else:
                                print(color_info(f"Using provider: {self.config_manager.config.analysis_provider}"))
                        else:
                            print("⚠️  AI provider is not connected")
                    print(f"Loading animation: {self.config_manager.config.loading_animation}")
                    return self.config_manager.config.ai_analysis_enabled
                elif arg in ['models', 'list']:
                    from src.providers.ollama_model import OllamaModel
                    if isinstance(self.ai_engine.analysis_provider, OllamaModel):
                        models = self.ai_engine.analysis_provider.get_available_models()
                        if models:
                            print(color_info(f"Available models: {', '.join(models)}"))
                            print(color_success(f"Current model: {self.ai_engine.analysis_provider.model}"))
                        else:
                            print(color_warning("No models available. Make sure Ollama is running."))
                    else:
                        print(color_warning(f"Model listing not supported for provider: {self.config_manager.config.analysis_provider}"))
                    return True
                elif arg.startswith('model='):
                    model_name = arg.split('=', 1)[1]
                    from src.providers.ollama_model import OllamaModel
                    if isinstance(self.ai_engine.analysis_provider, OllamaModel):
                        if self.ai_engine.analysis_provider.set_model(model_name):
                            print(color_success(f"Switched to model: {model_name}"))
                            return True
                        else:
                            print(color_error(f"Failed to switch to model: {model_name}"))
                            return False
                    else:
                        print(color_warning("Model switching is only supported for the Ollama provider."))
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

        # Handle ship command
        if command == 'ship':
            return self.ship(*args)

        # Handle undo command
        if command == 'undo':
            return self.undo(*args)

        # Handle redo command
        if command == 'redo':
            return self.redo(*args)

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
        
        # Handle quiz command
        if command == 'quiz':
            import subprocess
            import sys
            script_dir = os.path.dirname(os.path.realpath(__file__))
            quiz_server_script = os.path.join(script_dir, 'quiz_server.py')
            
            try:
                # Execute quiz_server.py script and handle KeyboardInterrupt gracefully
                result = subprocess.run([sys.executable, quiz_server_script], check=False)
                return result.returncode == 0
            except KeyboardInterrupt:
                # User pressed Ctrl+C, this is normal behavior
                print(color_info("\n🛑 Quiz server stopped by user"))
                return True
            except FileNotFoundError:
                print(color_error("❌ quiz_server.py not found"))
                return False
            except Exception as e:
                print(color_error(f"❌ Failed to start quiz server: {e}"))
                return False
        
        return self._command_handler(command, *args)
 
    # REFACTORED
    def _command_handler(self, command, *args):     # private function
        """A Generic git commands handler"""
        print(color_command(f"Running: git {command} {' '.join(args)}"))

        # Show confirmation before executing the command
        if self.config_manager.config.confirmation_enabled:
            # Skip confirmation during tests to avoid stdin capture issues
            import sys
            if 'pytest' in sys.modules:
                # During tests, assume 'y' response to avoid stdin capture issues
                response = 'y'
            else:
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
            if self.config_manager.config.ai_analysis_enabled:
                print(color_info("🤖 Analyzing with AI..."))
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
                        try:
                            with LoadingContext(animation_type=self.loading_animation_type):
                                ai_analysis = self.ollama.analyze_error_messages(error_data)
                            
                            if ai_analysis:
                                print(color_ai("🧠 AI:"))
                                print(color_ai(ai_analysis))
                            else:
                                print(color_warning("⚠️  AI analysis failed"))
                        except KeyboardInterrupt:
                            print(color_warning("\n\n⚠️  AI analysis cancelled by user"))
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
        
        # Get porcelain status for parsing (excluding ignored files)
        returncode, stdout, stderr = self.runner.run_git_command(['status', '--porcelain', '--ignored'])
        if returncode == 0 and stdout:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    status = line[:2]
                    file_path = line[2:].strip()  # Skip 2 chars and strip whitespace
                    
                    if status == 'UU':
                        repo_state['conflicts'].append(file_path)
                    elif status[0] in ['A', 'M', 'D', 'R', 'C']:
                        repo_state['staged'].append(file_path)
                    elif status[1] in ['M', 'D'] or status[0] == 'M':
                        repo_state['modified'].append(file_path)
                    elif status == '??':
                        repo_state['untracked'].append(file_path)
                    # Skip ignored files (status starts with '!!')
                    elif status == '!!':
                        continue
        
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

    def ship(self, *args):
        """Ship command that pulls changes, stages files, commits, and pushes
        
        Usage: ship [files...] [--all] [--message="commit message"] [--no-pull] [--no-push]
        
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
                print(color_header("Ship Command"))
                print(color_info("Usage: ship [files...] [--all] [--message=\"commit message\"] [--no-pull] [--no-push]"))
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
                print("  ship                           # Interactive mode with all changes")
                print("  ship file1.py file2.py         # Stage specific files")
                print("  ship --all --message=\"Fix bug\" # Stage all with custom message")
                print("  ship --no-pull                 # Skip pulling changes")
                return True
            elif not arg.startswith('--'):
                files_to_stage.append(arg)
            i += 1
        
        # If no files specified, default to all changes
        if not files_to_stage:
            files_to_stage = ['.']
        
        print(color_header("🚀 Ship Workflow"))
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
        current_model = None
        try:
            print(color_info("🔍 Analyzing selected files for AI..."))
            
            # Save current staging state to restore later
            returncode, current_staged, stderr = self.runner.run_git_command(['diff', '--cached', '--name-only'])
            originally_staged = current_staged.strip().split('\n') if current_staged.strip() else []
            
            # Store cleanup function for signal handling
            temp_staged_files = []
            
            def cleanup_temp_staging():
                """Clean up temporarily staged files"""
                for file_path in temp_staged_files:
                    # Only unstage if it wasn't originally staged
                    if file_path not in originally_staged:
                        try:
                            self.runner.run_git_command(['reset', 'HEAD', file_path])
                        except:
                            pass  # Ignore cleanup errors
            
            def signal_handler(signum, frame):
                """Handle Ctrl+C signal"""
                print(color_warning("\n\n⚠️  Interrupted! Cleaning up temporary staging..."))
                cleanup_temp_staging()
                sys.exit(1)
            
            # Set up signal handler for Ctrl+C
            original_signal = signal.signal(signal.SIGINT, signal_handler)
            
            try:
                # Temporarily stage the selected files for accurate AI analysis
                for file_path in files_to_stage:
                    if file_path != '.':
                        returncode, _, stderr = self.runner.run_git_command(['add', file_path])
                        if returncode == 0:
                            temp_staged_files.append(file_path)
                
                # Now get the real staged diff for AI analysis (only new changes since last commit)
                returncode, diff_output, stderr = self.runner.run_git_command(['diff', '--cached', 'HEAD~1'])
                
                if returncode == 0 and diff_output.strip():
                    # Get list of staged files
                    returncode, staged_files_output, stderr = self.runner.run_git_command(['diff', '--cached', '--name-only'])
                    staged_files = staged_files_output.strip().split('\n') if staged_files_output.strip() else []
                    
                    # Prepare context for AI
                    context = {
                        'branch': current_branch,
                        'staged_files': staged_files if staged_files else ['selected changes'],
                        'diff': diff_output[:2000]  # Limit diff size for AI processing
                    }
                    
                    # Get current AI model for display
                    current_model = self.ollama.get_current_model()
                    
                    # Generate AI commit message
                    try:
                        with LoadingContext(animation_type=self.loading_animation_type):
                            ai_suggestion = self.ollama.generate_commit_message(context)
                    except KeyboardInterrupt:
                        print(color_warning("\n\n⚠️  AI generation cancelled by user"))
                        ai_suggestion = None
                    
                    if ai_suggestion:
                        # Display the AI suggestion in a formatted way
                        print(color_ai(f"\n🤖 AI Suggestion (using {current_model}):"))
                        print(color_ai("─" * 40))
                        for line in ai_suggestion.split('\n'):
                            if line.strip():
                                print(color_ai(f"  {line}"))
                        print(color_ai("─" * 40))
                    else:
                        print(color_warning("⚠️  AI suggestion failed"))
                else:
                    print(color_warning("⚠️  No changes found for AI analysis"))
                
                # Restore original staging state - unstage temporarily staged files
                cleanup_temp_staging()
                
            finally:
                # Restore original signal handler
                signal.signal(signal.SIGINT, original_signal)
                
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
            print(color_info(f"🔍 AI Analysis: Based on mock diff of {len(files_to_stage)} file(s)"))
        else:
            print(color_info("📦 Stage: No files to stage"))
            print(color_info("🔍 AI Analysis: No files to analyze"))
        
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

    def undo(self, *args):
        """Undo command that reverts to the previous state before the latest commit
        
        Usage: undo [--soft] [--mixed] [--hard] [--help]
        
        Args:
            --soft:   Keep changes staged (git reset --soft HEAD~1)
            --mixed:  Unstage changes but keep them in working directory (git reset --mixed HEAD~1) - default
            --hard:   Discard all changes (git reset --hard HEAD~1)
            --help:   Show this help
        """
        # Parse arguments
        reset_type = '--mixed'  # default
        show_help = False
        
        for arg in args:
            if arg in ['--soft', '--mixed', '--hard']:
                reset_type = arg
            elif arg == '--help':
                show_help = True
        
        if show_help:
            print(color_header("Undo Command"))
            print(color_info("Usage: undo [--soft|--mixed|--hard]"))
            print("")
            print(color_info("Options:"))
            print("  --soft   : Keep changes staged (reset --soft HEAD~1)")
            print("  --mixed  : Unstage changes but keep them in working directory (reset --mixed HEAD~1) - default")
            print("  --hard   : Discard all changes (reset --hard HEAD~1)")
            print("  --help   : Show this help")
            print("")
            print(color_info("Examples:"))
            print("  undo           # Reset with --mixed (default)")
            print("  undo --soft    # Keep changes staged")
            print("  undo --hard    # Discard all changes")
            return True
        
        print(color_header("↩️  Undo Command"))
        print(Colors.divider("=", 40))
        
        # Check if we're in a git repository
        returncode, stdout, stderr = self.runner.run_git_command(['rev-parse', '--git-dir'])
        if returncode != 0:
            print(color_error("❌ Not in a git repository"))
            return False
        
        # Get current commit info
        returncode, stdout, stderr = self.runner.run_git_command(['log', '--oneline', '-n', '2'])
        if returncode != 0:
            print(color_error("❌ Failed to get commit history"))
            if stderr:
                print(stderr.strip())
            return False
        
        commits = stdout.strip().split('\n')
        if len(commits) < 2:
            print(color_warning("⚠️  No previous commit to undo to"))
            print(color_info("Current commit is the only commit in the repository"))
            return False
        
        current_commit = commits[0]
        previous_commit = commits[1]
        
        print(color_info("Current commit history:"))
        print(f"  HEAD:     {color_success(current_commit)}")
        print(f"  Previous: {color_info(previous_commit)}")
        
        # Show what will be reset based on reset type
        reset_descriptions = {
            '--soft': 'Keep changes staged',
            '--mixed': 'Unstage changes but keep them in working directory',
            '--hard': 'Discard all changes'
        }
        
        print(color_info(f"\nReset type: {color_success(reset_type)}"))
        print(color_info(f"Action: {reset_descriptions[reset_type]}"))
        
        # Get repository state before reset for warning
        repo_state = self.get_repo_state()
        has_staged = bool(repo_state['staged'])
        has_modified = bool(repo_state['modified'])
        has_untracked = bool(repo_state['untracked'])
        
        if reset_type == '--hard' and (has_staged or has_modified or has_untracked):
            print(color_warning("\n⚠️  WARNING: --hard reset will discard:"))
            if has_staged:
                print(f"  • Staged changes: {len(repo_state['staged'])} files")
            if has_modified:
                print(f"  • Modified files: {len(repo_state['modified'])} files")
            if has_untracked:
                print(f"  • Untracked files: {len(repo_state['untracked'])} files")
        
        # Confirmation
        if self.confirmation_enabled:
            response = input(color_info(f"\nReset to previous commit with {reset_type}? [y/N]: ")).strip().lower()
            if response not in ['y', 'yes']:
                print(color_warning("❌ Undo operation cancelled"))
                return False
        
        # Execute the reset
        print(color_info(f"\n🔄 Resetting to previous commit ({reset_type})..."))
        returncode, stdout, stderr = self.runner.run_git_command(['reset', reset_type, 'HEAD~1'])
        
        if returncode == 0:
            print(color_success("✅ Successfully reset to previous commit"))
            
            # Show new state
            print(color_info("\n📋 New repository state:"))
            returncode, new_stdout, stderr = self.runner.run_git_command(['log', '--oneline', '-n', '1'])
            if returncode == 0:
                print(f"  Current HEAD: {color_success(new_stdout.strip())}")
            
            # Show working directory status
            new_repo_state = self.get_repo_state()
            if new_repo_state['staged']:
                print(f"  Staged files: {len(new_repo_state['staged'])}")
            if new_repo_state['modified']:
                print(f"  Modified files: {len(new_repo_state['modified'])}")
            if new_repo_state['untracked']:
                print(f"  Untracked files: {len(new_repo_state['untracked'])}")
            
            if new_repo_state['clean']:
                print(color_success("  Working directory is clean"))
            
            return True
        else:
            print(color_error("❌ Failed to reset to previous commit"))
            if stderr:
                print(stderr.strip())
            return False

    def redo(self, *args):
        """Redo command that restores commits that were undone using the undo command
        
        Usage: redo [--help]
        
        This command uses git reflog to find and restore the most recent commit
        that was moved away from by a reset operation.
        """
        # Parse arguments
        show_help = False
        
        for arg in args:
            if arg == '--help':
                show_help = True
        
        if show_help:
            print(color_header("Redo Command"))
            print(color_info("Usage: redo"))
            print("")
            print(color_info("Options:"))
            print("  --help   : Show this help")
            print("")
            print(color_info("Description:"))
            print("  Restores the most recent commit that was undone using 'undo'")
            print("  Uses git reflog to find and re-apply the reset commit")
            print("")
            print(color_info("Examples:"))
            print("  redo           # Redo the last undo operation")
            return True
        
        print(color_header("↪️  Redo Command"))
        print(Colors.divider("=", 40))
        
        # Check if we're in a git repository
        returncode, stdout, stderr = self.runner.run_git_command(['rev-parse', '--git-dir'])
        if returncode != 0:
            print(color_error("❌ Not in a git repository"))
            return False
        
        # Get reflog to find the most recent reset operation
        returncode, stdout, stderr = self.runner.run_git_command(['reflog', '--oneline', '-n', '10'])
        if returncode != 0:
            print(color_error("❌ Failed to get reflog"))
            if stderr:
                print(stderr.strip())
            return False
        
        reflog_entries = stdout.strip().split('\n')
        if not reflog_entries or not stdout.strip():
            print(color_error("❌ No reflog entries found"))
            return False
        
        # Find the most recent reset operation and get the commit that was moved to (the newer commit)
        target_commit = None
        for i, entry in enumerate(reflog_entries):
            if 'reset: moving to HEAD~1' in entry:
                # The commit that was reset FROM (the newer commit we want to redo to) 
                # is in the reflog entry right before the reset operation
                if i > 0:
                    prev_entry = reflog_entries[i - 1]
                    # Extract commit hash from the previous entry
                    parts = prev_entry.split()
                    if len(parts) >= 1:
                        commit_hash = parts[0]
                        # Verify this is a valid commit hash
                        returncode, _, _ = self.runner.run_git_command(['cat-file', '-t', commit_hash])
                        if returncode == 0:
                            target_commit = commit_hash
                            break
        if not target_commit:
            print(color_error("❌ Could not determine target commit"))
            return False
        
        # Get current and target commit info for display
        returncode, current_stdout, stderr = self.runner.run_git_command(['log', '--oneline', '-n', '1'])
        returncode, target_stdout, stderr = self.runner.run_git_command(['log', '--oneline', '-n', '1', target_commit])
        
        # Extract current HEAD commit hash for comparison
        current_commit = None
        if current_stdout:
            current_parts = current_stdout.strip().split()
            if len(current_parts) >= 1:
                current_commit = current_parts[0]
        
        # Check if we're already at the target commit
        if current_commit and current_commit.startswith(target_commit[:8]):
            print(color_success("✅ Already at the most recent commit"))
            print(color_info("Current state:"))
            if current_stdout:
                print(f"  HEAD: {color_success(current_stdout.strip())}")
            print(color_info("No redo needed - this is already the latest commit"))
            return True
        
        print(color_info("Current state:"))
        if current_stdout:
            print(f"  HEAD: {color_info(current_stdout.strip())}")
        
        print(color_info("Will restore to:"))
        if target_stdout:
            print(f"  Commit: {color_success(target_stdout.strip())}")
        
        # Get repository state before redo for warning
        repo_state = self.get_repo_state()
        has_staged = bool(repo_state['staged'])
        has_modified = bool(repo_state['modified'])
        has_untracked = bool(repo_state['untracked'])
        
        if has_staged or has_modified or has_untracked:
            print(color_warning("\n⚠️  WARNING: Redo will affect current working directory:"))
            if has_staged:
                print(f"  • Staged changes: {len(repo_state['staged'])} files")
            if has_modified:
                print(f"  • Modified files: {len(repo_state['modified'])} files")
            if has_untracked:
                print(f"  • Untracked files: {len(repo_state['untracked'])} files")
        
        # Confirmation
        if self.confirmation_enabled:
            response = input(color_info(f"\nRestore commit {target_commit[:8]}? [y/N]: ")).strip().lower()
            if response not in ['y', 'yes']:
                print(color_warning("❌ Redo operation cancelled"))
                return False
        
        # Execute the redo using cherry-pick
        print(color_info(f"\n🔄 Restoring commit {target_commit[:8]}..."))
        returncode, stdout, stderr = self.runner.run_git_command(['cherry-pick', target_commit])
        
        if returncode != 0:
            # Check if this is a conflict due to local changes or merge conflicts
            if ("would be overwritten by merge" in stderr or 
                "Your local changes" in stderr or
                "could not apply" in stderr or
                "merge conflict" in stderr.lower() or
                returncode == 1):  # git cherry-pick returns 1 for conflicts
                print(color_warning("⚠️  Conflict detected during redo operation"))
                
                # First abort any in-progress cherry-pick to clean up
                abort_returncode, abort_stdout, abort_stderr = self.runner.run_git_command(['cherry-pick', '--abort'])
                
                # Check if there are still local changes after abort
                repo_state = self.get_repo_state()
                has_changes = (repo_state['staged'] or repo_state['modified'] or repo_state['untracked'])
                
                if has_changes:
                    print(color_info("Choose an option:"))
                    print(color_info("  [Enter] Hard reset to match remote, then redo (default)"))
                    print(color_info("  [s]     Stash changes, redo, then restore stash"))
                    print(color_info("  [c]     Cancel redo operation"))
                    
                    choice = input(color_info("Your choice: ")).strip().lower()
                    
                    if choice == 'c':
                        print(color_warning("❌ Redo operation cancelled"))
                        return False
                    elif choice == 's':
                        # Stash changes
                        print(color_info("� Stashing local changes..."))
                        stash_returncode, stash_stdout, stash_stderr = self.runner.run_git_command(['stash', 'push', '-m', 'Redo operation backup'])
                        if stash_returncode != 0:
                            print(color_error("❌ Failed to stash changes"))
                            if stash_stderr:
                                print(stash_stderr.strip())
                            return False
                        print(color_success("✅ Changes stashed"))
                        
                        # Try redo again
                        print(color_info(f"\n🔄 Retrying restore of commit {target_commit[:8]}..."))
                        returncode, stdout, stderr = self.runner.run_git_command(['cherry-pick', target_commit])
                        
                        if returncode == 0:
                            print(color_success("✅ Successfully restored commit"))
                            
                            # Try to restore stash
                            print(color_info("🔄 Restoring stashed changes..."))
                            pop_returncode, pop_stdout, pop_stderr = self.runner.run_git_command(['stash', 'pop'])
                            if pop_returncode == 0:
                                print(color_success("✅ Stashed changes restored"))
                            else:
                                print(color_warning("⚠️  Could not restore stashed changes"))
                                print(color_info("Run 'git stash pop' manually to restore"))
                                if pop_stderr:
                                    print(pop_stderr.strip())
                        else:
                            print(color_error("❌ Failed to restore commit even after stashing"))
                            if stderr:
                                print(stderr.strip())
                            return False
                    else:
                        # Default: Hard reset to match remote and pull
                        print(color_info("🔄 Resetting to match remote branch..."))
                        reset_returncode, reset_stdout, reset_stderr = self.runner.run_git_command(['reset', '--hard', 'origin/developer'])
                        if reset_returncode == 0:
                            print(color_success("✅ Reset to remote branch"))
                            
                            print(color_info("� Pulling latest changes..."))
                            pull_returncode, pull_stdout, pull_stderr = self.runner.run_git_command(['pull'])
                            if pull_returncode == 0:
                                print(color_success("✅ Pulled latest changes"))
                                
                                # Check if the target commit is already in the history
                                check_returncode, check_stdout, check_stderr = self.runner.run_git_command(['log', '--oneline', '-n', '10'])
                                if check_returncode == 0 and target_commit[:8] in check_stdout:
                                    print(color_success("✅ Target commit is already present in branch history"))
                                    print(color_info("No need to restore - commit already exists"))
                                    return True
                                
                                # Try redo again
                                print(color_info(f"\n🔄 Retrying restore of commit {target_commit[:8]}..."))
                                returncode, stdout, stderr = self.runner.run_git_command(['cherry-pick', target_commit])
                                
                                if returncode != 0:
                                    print(color_error("❌ Failed to restore commit after sync"))
                                    if stderr:
                                        print(stderr.strip())
                                    return False
                            else:
                                print(color_error("❌ Failed to pull changes"))
                                if pull_stderr:
                                    print(pull_stderr.strip())
                                return False
                        else:
                            print(color_error("❌ Failed to reset to remote"))
                            if reset_stderr:
                                print(reset_stderr.strip())
                            return False
                else:
                    # No local changes after abort, just retry directly
                    print(color_info("🔄 Retrying restore of commit..."))
                    returncode, stdout, stderr = self.runner.run_git_command(['cherry-pick', target_commit])
                    
                    if returncode != 0:
                        print(color_error("❌ Failed to restore commit"))
                        if stderr:
                            print(stderr.strip())
                        return False
        
        if returncode == 0:
            print(color_success("✅ Successfully restored commit"))
            
            # Show new state
            print(color_info("\n📋 New repository state:"))
            returncode, new_stdout, stderr = self.runner.run_git_command(['log', '--oneline', '-n', '1'])
            if returncode == 0:
                print(f"  Current HEAD: {color_success(new_stdout.strip())}")
            
            # Show working directory status
            new_repo_state = self.get_repo_state()
            if new_repo_state['staged']:
                print(f"  Staged files: {len(new_repo_state['staged'])}")
            if new_repo_state['modified']:
                print(f"  Modified files: {len(new_repo_state['modified'])}")
            if new_repo_state['untracked']:
                print(f"  Untracked files: {len(new_repo_state['untracked'])}")
            
            if new_repo_state['clean']:
                print(color_success("  Working directory is clean"))
            
            return True
        else:
            print(color_error("❌ Failed to restore commit"))
            if stderr:
                print(stderr.strip())
            
            # Try to provide helpful error information
            if "conflict" in stderr.lower():
                print(color_info("💡 Tip: Resolve conflicts and run 'git cherry-pick --continue'"))
            elif "empty" in stderr.lower():
                print(color_info("💡 This commit might already be applied"))


def main():
    try:
        fancy_git = FancyGit()
        
        if len(sys.argv) < 2:
            print(color_info("Usage: fancygit <command> [args...]"))
            print(color_info("Available commands:"))
            for cmd in fancy_git.available_commands:
                print(f"  {cmd}")
            return
        
        command = sys.argv[1]
        args = sys.argv[2:]
        
        fancy_git.execute_command(command, *args)
    except KeyboardInterrupt:
        print(color_warning("\n\n⚠️  Command cancelled by user"))
        sys.exit(130)  # Standard exit code for SIGINT

if __name__ == "__main__":
    main()
