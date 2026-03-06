# example for this dataclass object
# RepoState(
#  branch="main",
#  ahead_by=2,
#  behind_by=1,
#  staged_files=["parser.py"],
#  unstaged_files=["cli.py"],
#  untracked_files=["test.py"],
#  has_conflicts=True
# )

from dataclasses import dataclass

@dataclass (frozen = True)
class RepoState:
    branch: str
    ahead_by: int
    behind_by: int
    staged_files: list[str]
    unstaged_files: list[str]
    untracked_files: list[str]
    has_conflicts: bool