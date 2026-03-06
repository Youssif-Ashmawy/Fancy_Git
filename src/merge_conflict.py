# example for this dataclass object
# MergeConflict(
#  file="fancygit.py",
#  base_branch="main",
#  incoming_branch="refactor/fancygit.py",
#  current_code="return a + b",
#  incoming_code="return a - b",
#  start_line=12,
#  end_line=34
# )

from dataclasses import dataclass

@dataclass (frozen=True)
class MergeConflict:
    file: str

    # to get hold of which branches
    current_branch: str
    incoming_branch: str

    # to get hold of the line of code itself
    current_code: str
    incoming_code: str
    
    start_line: int
    end_line: int