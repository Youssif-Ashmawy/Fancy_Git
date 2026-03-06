import re
from src.git_error import GitError
class GitErrorParser:
    def __init__(self) -> None:
        pass

    def detect_warnings_errors(self, stdout, stderr):
        """Detect warnings and errors in git output"""
        messages = []

        def scan_patterns(patterns, text, type, source):
            for pattern in patterns:
                for match in re.findall(f'{pattern}.*', text, re.IGNORECASE):
                    messages.append(GitError(severity = type, source=source, message=match))
        
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

        scan_patterns(error_patterns, stdout, "error", "stdout")
        scan_patterns(warning_patterns, stdout, "warning", "stdout")
        scan_patterns(error_patterns, stderr, "error", "stderr")
        scan_patterns(warning_patterns, stderr, "warning", "stderr")

        return messages