DRY_RUN_SUPPORT = {
    # ========================
    # TRUE DRY RUN SUPPORT
    # ========================
    "clean": {
        "type": "TRUE_DRY_RUN",
        "flags": ["-n"]  # or --dry-run
    },
    "push": {
        "type": "TRUE_DRY_RUN",
        "flags": ["--dry-run"]
    },
    "fetch": {
        "type": "TRUE_DRY_RUN",
        "flags": ["--dry-run"]
    },

    # ========================
    # SAFE SIMULATION (SMART PREVIEW)
    # ========================
    "add": {
        "type": "SAFE_SIMULATION",
        "command": "git status"
    },
    "commit": {
        "type": "SAFE_SIMULATION",
        "command": "git diff --cached"
    },
    "merge": {
        "type": "SAFE_SIMULATION",
        "command": "git merge --no-commit --no-ff"
    },
    "pull": {
        "type": "SAFE_SIMULATION",
        "command": "git fetch"
    },
    "rebase": {
        "type": "SAFE_SIMULATION",
        "command": "git rebase --interactive --autosquash"
    },
    "reset": {
        "type": "SAFE_SIMULATION",
        "command": "git log --oneline -n 5"
    },
    "restore": {
        "type": "SAFE_SIMULATION",
        "command": "git status"
    },
    "rm": {
        "type": "SAFE_SIMULATION",
        "command": "git status"
    },
    "mv": {
        "type": "SAFE_SIMULATION",
        "command": "git status"
    },
    "checkout": {
        "type": "SAFE_SIMULATION",
        "command": "git status"
    },
    "switch": {
        "type": "SAFE_SIMULATION",
        "command": "git branch"
    },
    "stash": {
        "type": "SAFE_SIMULATION",
        "command": "git stash list"
    },
    "revert": {
        "type": "SAFE_SIMULATION",
        "command": "git log --oneline -n 3"
    },
    "cherry-pick": {
        "type": "SAFE_SIMULATION",
        "command": "git log --oneline"
    },

    # ========================
    # NO DRY RUN (hard to simulate)
    # ========================
    "clone": {"type": "NO_DRY_RUN"},
    "init": {"type": "NO_DRY_RUN"},
    "gc": {"type": "NO_DRY_RUN"},
    "maintenance": {"type": "NO_DRY_RUN"},
    "worktree": {"type": "NO_DRY_RUN"},
    "submodule": {"type": "NO_DRY_RUN"},
    "bundle": {"type": "NO_DRY_RUN"},
    "archive": {"type": "NO_DRY_RUN"},
    "format-patch": {"type": "NO_DRY_RUN"},
    "range-diff": {"type": "NO_DRY_RUN"},

    # ========================
    # SAFE / READ-ONLY (no need)
    # ========================
    "status": {"type": "NOT_APPLICABLE"},
    "log": {"type": "NOT_APPLICABLE"},
    "diff": {"type": "NOT_APPLICABLE"},
    "show": {"type": "NOT_APPLICABLE"},
    "grep": {"type": "NOT_APPLICABLE"},
    "describe": {"type": "NOT_APPLICABLE"},
    "shortlog": {"type": "NOT_APPLICABLE"},
    "branch": {"type": "NOT_APPLICABLE"},
    "tag": {"type": "NOT_APPLICABLE"},
    "notes": {"type": "NOT_APPLICABLE"},
    "bisect": {"type": "NOT_APPLICABLE"},

    # ========================
    # FANCYGIT CUSTOM COMMANDS
    # ========================
    "ai": {"type": "NOT_APPLICABLE"},
    "explain": {"type": "NOT_APPLICABLE"},
    "insights": {"type": "NOT_APPLICABLE"},
    "history": {"type": "NOT_APPLICABLE"},
    "visualize": {"type": "NOT_APPLICABLE"},
    "confirmation": {"type": "NOT_APPLICABLE"},
    "sync": {"type": "SAFE_SIMULATION", "command": "git fetch"},
    "backfill": {"type": "NO_DRY_RUN"},
    "colors": {"type": "NOT_APPLICABLE"},
    "citool": {"type": "NOT_APPLICABLE"},
    "gui": {"type": "NOT_APPLICABLE"},
    "sparse-checkout": {"type": "NO_DRY_RUN"},
    "welcome": {"type": "NOT_APPLICABLE"},
}

def get_dry_run(command_name: str, full_command: str):
    rule = DRY_RUN_SUPPORT.get(command_name)

    if not rule:
        return None, "UNKNOWN"

    if rule["type"] == "TRUE_DRY_RUN":
        return full_command + " " + " ".join(rule["flags"]), "REAL"

    elif rule["type"] == "SAFE_SIMULATION":
        return rule["command"], "SIMULATION"

    return None, rule["type"]
