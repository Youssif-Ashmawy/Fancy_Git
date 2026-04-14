import subprocess

class GitRunner:
    # dependency injection of history manager to record commands
    def __init__(self, history_manager) -> None:
        self.git_cmd = "git"
        self.history_manager = history_manager  # Store the history manager instance for later use

    def run_git_command(self, args, record_history=True):
        """Run git command and capture output"""
        try:
            cmd = [self.git_cmd] + args
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            if record_history:
                self.history_manager.add_entry(args)
            return result.returncode, result.stdout, result.stderr

        except Exception as e:
            return -1, "", str(e)
    