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

@dataclass(frozen = True)   # we freeze it to make it immutable
class GitError:
    source: str 
    message: str
    severity: str = "unknown"
    
    type: str | None = None
    file: str | None = None
    line: int | None = None

    def __str__(self) -> str:
        return (
            f"{'='*60}\n"
            f"type: {self.type}\n"
            f"source: {self.source}\n"
            f"message: {self.message}\n"
            f"severity: {self.severity}\n"
            f"file: {self.file}\n"
            f"line: {self.line}\n"
            f"{'='*60}"
        )