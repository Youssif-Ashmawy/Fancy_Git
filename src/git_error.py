# this class will be an immutable dataclass
# it will represent like the format of the data so we can then
# pass it to the ai models so they can be fed a consistent and organized
# json format that is both readable and can be easily extracted and 
# worked on

# dataclasses are suitable here because we will primarily use it to store the 
# data and represent it
# moreover to make it look cleaner without having to write an init method


# the format will be like the following
# {
#   "type": "MERGE_CONFLICT",
#   "source" : stdout || stderr
#   "message": "error: Merge conflict in README.md",
#   "severity": "error" || "warning",
#   "file": "README.md",
#   "line": null
# }
from dataclasses import dataclass
from src.colors import Colors, color_error, color_warning, color_info, color_file

@dataclass(frozen = True)   # we freeze it to make it immutable
class GitError:
    source: str 
    message: str
    severity: str = "unknown"
    
    type: str | None = None
    file: str | None = None
    line: int | None = None

    def __str__(self) -> str:
        severity_color = {
            'error': color_error,
            'warning': color_warning,
            'info': color_info,
            'unknown': lambda x: x
        }.get(self.severity, lambda x: x)
        
        type_str = str(self.type) if self.type is not None else 'None'
        file_str = str(self.file) if self.file is not None else 'N/A'
        line_str = str(self.line) if self.line is not None else 'N/A'
        
        return (
            f"{Colors.divider('=', 60)}\n"
            f"type: {type_str}\n"
            f"source: {str(self.source)}\n"
            f"message: {str(self.message)}\n"
            f"severity: {str(self.severity)}\n"
            f"file: {file_str}\n"
            f"line: {line_str}\n"
            f"{Colors.divider('=', 60)}"
        )