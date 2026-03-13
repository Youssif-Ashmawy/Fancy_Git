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
                for match in re.findall(f'{pattern}.*', text, re.IGNORECASE | re.MULTILINE):
                    messages.append(GitError(severity = type, source=source, message=match.strip()))
        
        # Common git error patterns (more specific to avoid false positives)
        error_patterns = [
            r'fatal:',
            r'error:',
            r'\bfailed\b',
            r'\brejected\b',
            r'merge conflict',
            r'\bconflict\b',
            r'unable to',
            r'\.git.*error:',
            r'^(?!.*error:).*pathspec.*did not match'
        ]
        
        # Common git warning patterns (more specific to avoid false positives)
        warning_patterns = [
            r'warning:',
            r'WARNING:',
            r'.*behind.*by\s+\d+.*',
            r'.*ahead.*by\s+\d+.*',
            r'\bdiverged\b'
        ]

        scan_patterns(error_patterns, stdout, "error", "stdout")
        scan_patterns(warning_patterns, stdout, "warning", "stdout")
        scan_patterns(error_patterns, stderr, "error", "stderr")
        scan_patterns(warning_patterns, stderr, "warning", "stderr")

        return messages