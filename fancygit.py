#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import webbrowser

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
    from src.config_manager import ConfigManager
    from src.risk_analyzer import RiskAnalyzer
    from src.confirmation_ui import ConfirmationUI
    from src.utils import DRY_RUN_SUPPORT, get_dry_run
    from src.history_manager import HistoryManager
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
    from src.config_manager import ConfigManager
    from src.risk_analyzer import RiskAnalyzer
    from src.confirmation_ui import ConfirmationUI
    from src.utils import DRY_RUN_SUPPORT, get_dry_run
    from src.history_manager import HistoryManager
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
        self.history_manager = HistoryManager()
        self.runner = GitRunner(self.history_manager)
        self.parser = GitErrorParser()
        self.mermaid = MermaidExporter(self.runner)
        self.insights = GitInsights(self.runner)
        # self.ollama = OllamaClient()
        self.output_colorizer = OutputColorizer()
        self.config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.fancygit_config')
        self.ai_engine = AIEngine(self.config_manager)
        self.available_commands = self._load_commands()
        self.risk_analyzer = RiskAnalyzer()
        
    @property
    def confirmation_enabled(self):
        """Get confirmation enabled state from config manager"""
        return self.config_manager.config.confirmation_enabled
    
    @confirmation_enabled.setter
    def confirmation_enabled(self, value):
        """Set confirmation enabled state in config manager"""
        self.config_manager.config.confirmation_enabled = value
    
    @property
    def ai_analysis_enabled(self):
        """Get AI analysis enabled state from config manager"""
        return self.config_manager.config.ai_analysis_enabled
    
    @ai_analysis_enabled.setter
    def ai_analysis_enabled(self, value):
        """Set AI analysis enabled state in config manager"""
        self.config_manager.config.ai_analysis_enabled = value
    
    @property
    def output_coloring_enabled(self):
        """Get output coloring enabled state from config manager"""
        return self.config_manager.config.output_coloring_enabled
    
    @output_coloring_enabled.setter
    def output_coloring_enabled(self, value):
        """Set output coloring enabled state in config manager"""
        self.config_manager.config.output_coloring_enabled = value
    
    @property
    def loading_animation_type(self):
        """Get loading animation type from config manager"""
        return self.config_manager.config.loading_animation
    
    @loading_animation_type.setter
    def loading_animation_type(self, value):
        """Set loading animation type in config manager"""
        self.config_manager.config.loading_animation = value
    
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
            site_packages_dir = sys._MEIPASS    # type: ignore
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


                pass
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
        
        # ------------------------------ NEW FEATURE: FANCYGIT HISTORY---------------------------------
        if command == 'history':
            print("──────── FancyGit History ────────")
            history = self.history_manager.get_history()
            if not history:
                print(color_info("No history available."))
                return True
            
            for idx, entry in enumerate(history[::-1], 1):  # reverse to show latest first also start from first index
                if idx == 5:    # Show only the latest 5 commands
                    break
                timestamp = entry.get('timestamp')
                cmd = entry.get('command')
                time_str = f" (Last modified: {timestamp})" if timestamp else ""
                print(f"{idx}. git {' '.join(cmd)}{time_str}")
        
            user_input = input(color_header("Select command number to repeat,\n"
            " or type 'n' followed by a number to execute multiple history commands, \nor 'c' to clear history:")).strip()
            
            if user_input == "":
                return True

            if user_input[0] == 'n':
                try: 
                    num_commands = int(user_input[1:])
                    for entry in history[-num_commands:]:
                        cmd = entry.get('command')
                        print(color_command(f"Re-running: git {' '.join(cmd)}"))
                        code, stdout, stderr = self.runner.run_git_command(cmd)
                        output = (stdout or "") + (stderr + "")
                        print(output)
                except ValueError:
                    print(color_warning("Invalid input. Please enter a valid number after 'n'."))
                    return False
            else:
                try:
                    cmd = history[-int(user_input)].get('command')
                    print(color_command(f"Re-running: git {' '.join(cmd)}"))
                    code, stdout, stderr = self.runner.run_git_command(cmd)
                    output = (stdout or "") + (stderr or "")
                    print(output)
                except:
                    print(color_warning("Invalid input. Please enter a valid number"))
                    return False
                
            return True

        # normal commands do this
        return self._command_handler(command, *args)
    



    # -------------------- NEW PRIVATE FUNCTIONS ------------------- #
    def _gather_info_for_confirmation(self):
        # dont record these info-gathering commands in history since they are just for confirmation and not actual user-invoked commands
        _, status, _ = self.runner.run_git_command(['status', '--short'], record_history=False)
        _, branch, _ = self.runner.run_git_command(['branch', '--show-current'], record_history=False)
        _, recent_commits, _ = self.runner.run_git_command(['log', '-5', '--oneline'], record_history=False)
        return status.strip(), branch.strip(), recent_commits.strip()

    def _dry_run_command(self, command, args):
        full_command = f"git {command} {' '.join(args)}"
        dry_run, dry_mode = get_dry_run(command, full_command)

        if not dry_run:
            return "Dry run not supported for this command", "NONE"

        # dry_run is a string like "git status" — split and remove "git" prefix
        dry_run_parts = dry_run.split()
        if dry_run_parts and dry_run_parts[0] == "git":
            dry_run_parts = dry_run_parts[1:]
        # again dont record dry-run commands in history
        code, stdout, stderr = self.runner.run_git_command(dry_run_parts, record_history=False)

        output = (stdout or "") + (stderr or "")
        return output.strip(), dry_mode

    def _print_colored_risk_level(self, risk_level):
        if risk_level == 'Safe':
            print(color_success("Risk Level: SAFE"))
        elif risk_level == 'Warning':
            print(color_warning("Risk Level: WARNING"))
        elif risk_level == 'Dangerous':
            print(color_error("Risk Level: DANGEROUS"))
        else:
            print(color_info(f"Risk Level: {risk_level.upper()}"))
    # -------------------- END OF NEW PRIVATE FUNCTIONS ------------------- #


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
                # ------------ Interactive Confirmation UI ------------
                full_command = f"git {command} {' '.join(args)}"
                risk_level = self.risk_analyzer.analyze(command_line=full_command, ai_engine=self.ai_engine)
                status, branch, recent_commits = self._gather_info_for_confirmation()
                dry_output, dry_mode = self._dry_run_command(command, args)

                # Get AI explanation
                confirmation_message = self.ai_engine.confirmation_command(
                    command=full_command, status=status, current_branch=branch,
                    recent_commits=recent_commits, command_risk_level=risk_level.value,
                    dry_output=dry_output, dry_mode=dry_mode
                )
                ai_text = self.ai_engine._post_process(confirmation_message, risk_level.value)

                # Parse status into lines
                status_lines = [l for l in status.split("\n") if l.strip()] if status else []

                # Render the confirmation UI
                ui = ConfirmationUI(
                    command=full_command,
                    branch=branch,
                    risk_level=risk_level.value,
                    status_lines=status_lines,
                    recent_commits=recent_commits,
                    ai_explanation=ai_text,
                    dry_output=dry_output,
                    dry_mode=dry_mode,
                )
                ui.render()

                # Interactive action loop
                while True:
                    choice = ui.prompt_action(command)
                    if choice == 'y':
                        response = 'y'
                        break
                    elif choice == 'n':
                        response = 'n'
                        break
                    elif choice == 'd':
                        # Use the DRY_RUN_SUPPORT map to get the right preview command
                        preview_output, preview_mode = self._dry_run_command(command, list(args))

                        if preview_output and preview_mode != "NONE":
                            diff_text = preview_output
                        else:
                            # Fallback for commands not in the map
                            _, diff_out, diff_err = self.runner.run_git_command(['diff', 'HEAD'])
                            diff_text = diff_out or diff_err or "No changes to display."

                        print()
                        print(Colors.colorize("─" * 14 + " Preview " + "─" * 14, Colors.INFO, Colors.BOLD))
                        print()
                        for line in diff_text.strip().split("\n"):
                            print(f"  {line}")
                        print()
                        print(Colors.colorize("─" * 38, Colors.MUTED))
                        continue
                    elif choice == 'i' and 'add' in command:
                        result = ui.interactive_staging(self.runner)
                        if result:
                            return True
                        # If cancelled, loop back to the action menu
                        continue
                    else:
                        print(color_warning("  Invalid choice. Try again."))
                        continue
                # -----------------------------------------------
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
                        with LoadingContext(animation_type=self.config_manager.config.loading_animation):
                            ai_analysis = self.ai_engine.analyze_error_messages(error_data)
                        
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