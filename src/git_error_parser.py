import re

class GitErrorParser:
    def __init__(self) -> None:
        pass

    def detect_warnings_errors(self, stdout, stderr):
        """Detect warnings and errors in git output"""
        warnings = []
        errors = []
        
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
        
        # Check stderr for errors
        for pattern in error_patterns:
            matches = re.findall(f'{pattern}.*', stderr, re.IGNORECASE)
            errors.extend(matches)
        
        # Check stdout for errors
        for pattern in error_patterns:
            matches = re.findall(f'{pattern}.*', stdout, re.IGNORECASE)
            errors.extend(matches)
        
        # Check stderr for warnings
        for pattern in warning_patterns:
            matches = re.findall(f'{pattern}.*', stderr, re.IGNORECASE)
            warnings.extend(matches)
        
        # Check stdout for warnings
        for pattern in warning_patterns:
            matches = re.findall(f'{pattern}.*', stdout, re.IGNORECASE)
            warnings.extend(matches)
        
        return warnings, errors