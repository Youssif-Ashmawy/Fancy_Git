# example for this dataclass object
# RepoState(
#  branch="main",
#  ahead_by=2,
#  behind_by=1,
#  staged_files=["fancygit.py"],
#  unstaged_files=["git_runner.py"],
#  untracked_files=["test.py"],
#  has_conflicts=True
#  is_merging = True,
#  conflicts = [MergeConflict, .....]etc
# )

from dataclasses import dataclass
from src.merge_conflict import MergeConflict
@dataclass (frozen = True)
class RepoState:
    branch: str
    ahead_by: int
    behind_by: int

    staged_files: list[str]
    unstaged_files: list[str]
    untracked_files: list[str]

    has_conflicts: bool
    is_merging: bool

    conflicts:  list[MergeConflict]  # list of merge conflicts