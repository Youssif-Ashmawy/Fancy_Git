import subprocess

class GitRunner:
    def __init__(self) -> None:
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
    