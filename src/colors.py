#!/usr/bin/env python3
"""
FancyGit Color System
Provides vibrant colors and styling for the CLI interface
"""

class Colors:
    """ANSI color codes for vibrant terminal output"""
    
    # Reset
    RESET = '\033[0m'
    
    # Check if terminal supports colors
    SUPPORTS_COLOR = True
    
    @classmethod
    def check_color_support(cls):
        """Check if terminal supports colors"""
        import os
        # Check if NO_COLOR environment variable is set
        if os.environ.get('NO_COLOR'):
            cls.SUPPORTS_COLOR = False
            return False
        
        # Check if TERM environment variable suggests no color support
        term = os.environ.get('TERM', '').lower()
        no_color_terms = ['dumb', 'unknown', 'unknown']
        if any(no_color_term in term for no_color_term in no_color_terms):
            cls.SUPPORTS_COLOR = False
            return False
        
        # Check if we're not in a TTY
        import sys
        if not sys.stdout.isatty():
            cls.SUPPORTS_COLOR = False
            return False
            
        cls.SUPPORTS_COLOR = True
        return True
    
    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Bright background colors
    BG_BRIGHT_BLACK = '\033[100m'
    BG_BRIGHT_RED = '\033[101m'
    BG_BRIGHT_GREEN = '\033[102m'
    BG_BRIGHT_YELLOW = '\033[103m'
    BG_BRIGHT_BLUE = '\033[104m'
    BG_BRIGHT_MAGENTA = '\033[105m'
    BG_BRIGHT_CYAN = '\033[106m'
    BG_BRIGHT_WHITE = '\033[107m'
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # FancyGit theme colors
    PRIMARY = BRIGHT_BLUE
    SECONDARY = BRIGHT_CYAN
    ACCENT = BRIGHT_YELLOW
    SUCCESS = BRIGHT_GREEN
    WARNING = BRIGHT_YELLOW
    ERROR = BRIGHT_RED
    INFO = BRIGHT_MAGENTA
    MUTED = BRIGHT_BLACK
    
    # Git-specific colors
    GIT_ADD = SUCCESS
    GIT_MODIFY = WARNING
    GIT_DELETE = ERROR
    GIT_RENAME = INFO
    GIT_COPY = SECONDARY
    GIT_CONFLICT = BG_BRIGHT_RED + WHITE + BOLD
    
    # Status indicators
    STATUS_SUCCESS = '✅'
    STATUS_ERROR = '❌'
    STATUS_WARNING = '⚠️'
    STATUS_INFO = 'ℹ️'
    STATUS_LOADING = '🔄'
    STATUS_AI = '🤖'
    STATUS_BRAIN = '🧠'
    
    @classmethod
    def colorize(cls, text: str, color: str, style: str = '') -> str:
        """Apply color and style to text"""
        if not cls.SUPPORTS_COLOR:
            return text
        return f"{style}{color}{text}{cls.RESET}"
    
    @classmethod
    def command(cls, text: str) -> str:
        """Color for command names"""
        return cls.colorize(text, cls.PRIMARY, cls.BOLD)
    
    @classmethod
    def success(cls, text: str) -> str:
        """Color for success messages"""
        return cls.colorize(text, cls.SUCCESS)
    
    @classmethod
    def error(cls, text: str) -> str:
        """Color for error messages"""
        return cls.colorize(text, cls.ERROR, cls.BOLD)
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Color for warning messages"""
        return cls.colorize(text, cls.WARNING)
    
    @classmethod
    def info(cls, text: str) -> str:
        """Color for info messages"""
        return cls.colorize(text, cls.INFO)
    
    @classmethod
    def ai_response(cls, text: str) -> str:
        """Color for AI responses"""
        return cls.colorize(text, cls.SECONDARY, cls.ITALIC)
    
    @classmethod
    def highlight(cls, text: str) -> str:
        """Color for highlighted text"""
        return cls.colorize(text, cls.ACCENT, cls.BOLD)
    
    @classmethod
    def muted(cls, text: str) -> str:
        """Color for muted text"""
        return cls.colorize(text, cls.MUTED)
    
    @classmethod
    def git_status(cls, status: str) -> str:
        """Color for git status indicators"""
        status_colors = {
            'A': cls.GIT_ADD,      # Added
            'M': cls.GIT_MODIFY,   # Modified
            'D': cls.GIT_DELETE,   # Deleted
            'R': cls.GIT_RENAME,   # Renamed
            'C': cls.GIT_COPY,     # Copied
            '??': cls.MUTED,       # Untracked
            'UU': cls.GIT_CONFLICT # Conflict
        }
        color = status_colors.get(status, cls.WHITE)
        return cls.colorize(status, color, cls.BOLD)
    
    @classmethod
    def branch_name(cls, branch: str, is_current: bool = False) -> str:
        """Color for branch names"""
        if is_current:
            return cls.colorize(branch, cls.BRIGHT_GREEN, cls.BOLD)
        return cls.colorize(branch, cls.PRIMARY)
    
    @classmethod
    def file_path(cls, path: str) -> str:
        """Color for file paths"""
        return cls.colorize(path, cls.BRIGHT_CYAN)
    
    @classmethod
    def header(cls, text: str) -> str:
        """Color for headers"""
        return cls.colorize(text, cls.PRIMARY, cls.BOLD)
    
    @classmethod
    def subheader(cls, text: str) -> str:
        """Color for subheaders"""
        return cls.colorize(text, cls.SECONDARY)
    
    @classmethod
    def divider(cls, char: str = '=', length: int = 60) -> str:
        """Create a colored divider"""
        return cls.colorize(char * length, cls.MUTED)
    
    @classmethod
    def progress_bar(cls, current: int, total: int, width: int = 20) -> str:
        """Create a colored progress bar"""
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        return cls.colorize(f'[{bar}] {current}/{total}', cls.SUCCESS)
    
    @classmethod
    def rainbow_text(cls, text: str) -> str:
        """Create rainbow-colored text"""
        colors = [cls.RED, cls.BRIGHT_YELLOW, cls.GREEN, cls.CYAN, cls.BLUE, cls.MAGENTA]
        result = []
        for i, char in enumerate(text):
            color = colors[i % len(colors)]
            result.append(f"{color}{char}")
        return ''.join(result) + cls.RESET
    
    @classmethod
    def gradient_text(cls, text: str, start_color: str, end_color: str) -> str:
        """Create gradient-colored text (simplified version)"""
        # This is a simplified gradient - in a full implementation,
        # you'd interpolate between RGB values
        mid_point = len(text) // 2
        first_half = text[:mid_point]
        second_half = text[mid_point:]
        
        return f"{start_color}{first_half}{end_color}{second_half}{cls.RESET}"

# Convenience functions for common color operations
def color_command(text: str) -> str:
    return Colors.command(text)

def color_success(text: str) -> str:
    return Colors.success(text)

def color_error(text: str) -> str:
    return Colors.error(text)

def color_warning(text: str) -> str:
    return Colors.warning(text)

def color_info(text: str) -> str:
    return Colors.info(text)

def color_ai(text: str) -> str:
    return Colors.ai_response(text)

def color_header(text: str) -> str:
    return Colors.header(text)

def color_file(text: str) -> str:
    return Colors.file_path(text)

def color_branch(text: str, current: bool = False) -> str:
    return Colors.branch_name(text, current)
