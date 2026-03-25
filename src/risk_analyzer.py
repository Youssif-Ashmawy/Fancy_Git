import re
from .risk_level_enum import RiskLevel
from .providers.base_model import BaseModel

class RiskAnalyzer:
    def __init__(self):
        # define a dictionary that holds base risk levels for each git command
        self.base_rules = {
            # safe commands : 
            # ones that are read only and do not modify the repository in any way
            "ai": RiskLevel.SAFE,
            "archive": RiskLevel.SAFE,
            "bisect": RiskLevel.SAFE,
            "branch": RiskLevel.SAFE,  # these can be safe or dangerous depending on the context, so we will mark them as safe
            "bundle": RiskLevel.SAFE,
            "colors": RiskLevel.SAFE,
            "config": RiskLevel.SAFE,
            "describe": RiskLevel.SAFE,
            "diff": RiskLevel.SAFE,
            "explain": RiskLevel.SAFE,
            "grep": RiskLevel.SAFE,
            "history": RiskLevel.SAFE,
            "insights": RiskLevel.SAFE,
            "log": RiskLevel.SAFE,
            "shortlog": RiskLevel.SAFE,
            "show": RiskLevel.SAFE,
            "status": RiskLevel.SAFE,
            "visualize": RiskLevel.SAFE,
            "welcome": RiskLevel.SAFE,
            "gui": RiskLevel.SAFE,

            # warning commands : 
            # ones that can be safe or dangerous depending on the context, 
            # but generally have the potential to modify the repository in a way 
            # that can lead to data loss or other issues if not used carefully
            "add": RiskLevel.WARNING,
            "am": RiskLevel.WARNING,
            "checkout": RiskLevel.WARNING,
            "cherry-pick": RiskLevel.WARNING,
            "clean": RiskLevel.WARNING,
            "clone": RiskLevel.WARNING,
            "commit": RiskLevel.WARNING,
            "fetch": RiskLevel.WARNING,
            "format-patch": RiskLevel.WARNING,
            "merge": RiskLevel.WARNING,
            "mv": RiskLevel.WARNING,
            "notes": RiskLevel.WARNING,
            "pull": RiskLevel.WARNING,
            "revert": RiskLevel.WARNING,
            "rm": RiskLevel.WARNING,
            "restore": RiskLevel.WARNING,
            "stash": RiskLevel.WARNING,
            "switch": RiskLevel.WARNING,
            "tag": RiskLevel.WARNING,
            "worktree": RiskLevel.WARNING,
            "sync": RiskLevel.WARNING,
            "sparse-checkout": RiskLevel.WARNING,
            "format-patch": RiskLevel.WARNING,
            "rebase": RiskLevel.WARNING,
            "push": RiskLevel.WARNING,

            # dangerous commands : 
            # writes history and affects remote aka "fadaye7" commands
            "reset" : RiskLevel.DANGEROUS,
            "gc" : RiskLevel.DANGEROUS,     # git commit can be dangerous if it amends history or creates a new commit that overwrites existing commits, so we will mark it as dangerous
            "maintenance" : RiskLevel.DANGEROUS,   # git maintenance can be dangerous if it performs aggressive garbage collection or other operations that can lead to data loss, so we will mark it as dangerous
        }

    # create a regex secondary layer that looks for additions on the base commands 
    # and edits the safety level of the commands
    def _adjust_level_for_flags(self, command_line, base_rule):
        # patterns to look for that are dangerous
        dangerous_patterns = [
            (r'\b(reset|clean)\b.*(--hard|--force|-f|-d|-fd|-fdx|-x|--force-with-lease|-D)', RiskLevel.DANGEROUS),  # these flags can cause data loss
            (r'\b(rebase|merge)\b.*(--force|-f)', RiskLevel.DANGEROUS),  # these flags can cause data loss if used with rebase or merge
            (r'\b(push)\b.*(--force|-f|--force-with-lease)', RiskLevel.DANGEROUS),  # these flags can cause data loss if used with push
            (r'\b(commit)\b.*(--amend)', RiskLevel.DANGEROUS),  # amending a commit can be dangerous if it overwrites existing commits
            (r'\b(gc|maintenance)\b.*(--aggressive)', RiskLevel.DANGEROUS),  # aggressive garbage collection can be dangerous if it leads to data loss
            (r'\b(branch)\b.*(--delete|-d)', RiskLevel.DANGEROUS),  # deleting a branch can be dangerous if it leads to data loss
            (r'\brm\b.*(-f|-r|-rf)', RiskLevel.DANGEROUS),
            (r'\b(branch)\b\s+\w+', RiskLevel.WARNING),  # creating a branch is considered warning
            (r'\b(checkout)\b.*--', RiskLevel.WARNING),  # checking out a branch with -- can be dangerous if it leads to data loss, but we will mark it as warning for now
            (r'\brestore\b.*(--source|--staged|--worktree)', RiskLevel.WARNING),
        ]

        for pattern, risk_level in dangerous_patterns:
            if (re.search(pattern, command_line)):
                return risk_level
            
        # if it doesn't match any dangerous patterns, return the base risk level
        return base_rule
    
    def analyze(self, command_line, ai_engine):  # this will be the only interface between the user and this class, 
        # it will take the command line input and return the risk level
        
        command_parts = command_line.split()  # get the whole command line and split it into parts, then ignore the first part which is "git"
        base_command = command_parts[0] # the base command is the first part of the command line after "git"

        if not command_line:  # if there is no command after "git", return UNKNOWN
            return RiskLevel.UNKNOWN

        base_risk_level = self.base_rules.get(base_command, RiskLevel.UNKNOWN)  # get the base risk level from the dictionary, default to UNKNOWN if not found
        adjusted_risk_level = self._adjust_level_for_flags(command_line, base_risk_level)  # adjust the risk level based on flags

        if base_risk_level == RiskLevel.UNKNOWN:  # if the base risk level is unknown, use the AI engine to classify the command
            try:
                adjusted_risk_level = RiskLevel(ai_engine.classify_command(command_line).strip().capitalize())  # this will return a risk level based on the ai analysis of the command
            except Exception as e:
                print(f"Error occurred while classifying command: {e}")

        return adjusted_risk_level
        