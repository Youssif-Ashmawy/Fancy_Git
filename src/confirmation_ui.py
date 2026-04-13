from src.colors import Colors, color_command, color_success, color_error, color_warning, color_info, color_ai, color_branch


class ConfirmationUI:
    """Renders the interactive confirmation panel."""

    RISK_ICONS = {
        "Safe": "🟢",
        "Warning": "🟡",
        "Dangerous": "🔴",
        "Unknown": "⚪",
    }

    RISK_REASONS = {
        "Safe": "Read-only command.",
        "Warning": "Modifies repository state.",
        "Dangerous": "May cause irreversible changes!",
    }

    def __init__(self, command, branch, risk_level, status_lines,
                 recent_commits, ai_explanation, dry_output, dry_mode):
        self.command = command
        self.branch = branch
        self.risk_level = risk_level
        self.risk_reason = self.RISK_REASONS.get(risk_level, "")
        self.status_lines = status_lines
        self.recent_commits = recent_commits
        self.ai_explanation = ai_explanation
        self.dry_output = dry_output
        self.dry_mode = dry_mode

    def render(self):
        """Print the formatted confirmation panel."""
        self._render_header()
        self._render_command_info()
        self._render_risk()
        self._render_files()
        self._render_commits()
        self._render_ai_explanation()

    def _render_header(self):
        """Render the FancyGit header bar."""
        print()
        print(Colors.colorize("─" * 16 + " FancyGit " + "─" * 16, Colors.PRIMARY, Colors.BOLD))

    def _render_command_info(self):
        """Render command and branch info."""
        print()
        print(f"  {Colors.colorize('Command:', Colors.MUTED)} {color_command(self.command)}")
        print(f"  {Colors.colorize('Branch:', Colors.MUTED)}  {color_branch(self.branch, current=True)}")

    def _render_risk(self):
        """Render risk level with icon and reason."""
        icon = self.RISK_ICONS.get(self.risk_level, "⚪")
        risk_color_fn = {
            "Safe": color_success,
            "Warning": color_warning,
            "Dangerous": color_error,
        }.get(self.risk_level, color_info)

        print()
        print(f"  {Colors.colorize('Risk:', Colors.MUTED)} {icon} {risk_color_fn(self.risk_level.upper())}")
        if self.risk_reason:
            print(f"  {Colors.colorize('Reason:', Colors.MUTED)} {self.risk_reason}")

    def _render_files(self):
        """Render the file status list."""
        if not self.status_lines:
            return

        print()
        print(f"  {Colors.colorize('Files:', Colors.MUTED)}")
        for line in self.status_lines[:10]:  # cap display at 10 files
            line = line.strip()
            if not line:
                continue
            status_code = line[:2].strip()
            filename = line[2:].strip()
            print(f"    {Colors.git_status(status_code)} {Colors.file_path(filename)}")

        remaining = len(self.status_lines) - 10
        if remaining > 0:
            print(f"    {Colors.colorize(f'... and {remaining} more files', Colors.MUTED)}")

    def _render_commits(self):
        """Render recent commits (max 3)."""
        if not self.recent_commits:
            return

        commits = [c.strip() for c in self.recent_commits.split("\n") if c.strip()][:3]
        if not commits:
            return

        print()
        print(f"  {Colors.colorize('Recent commits:', Colors.MUTED)}")
        for commit in commits:
            print(f"    {Colors.colorize(commit, Colors.DIM)}")

    def _render_ai_explanation(self):
        """Render the AI explanation section."""
        print()
        print(Colors.colorize("─" * 12 + " AI Explanation " + "─" * 12, Colors.SECONDARY, Colors.BOLD))
        print()
        if self.ai_explanation:
            for line in self.ai_explanation.strip().split("\n"):
                print(f"  {color_ai(line)}")
        else:
            print(f"  {Colors.colorize('No AI explanation available.', Colors.MUTED)}")
        print()
        print(Colors.colorize("─" * 42, Colors.MUTED))

    def prompt_action(self, command):
        """Show interactive action menu and return user choice."""
        print()
        print(f"  {Colors.colorize('Actions:', Colors.BRIGHT_WHITE + Colors.BOLD)}")
        print(f"  {Colors.colorize('[y]', Colors.SUCCESS + Colors.BOLD)} Execute")
        print(f"  {Colors.colorize('[n]', Colors.ERROR + Colors.BOLD)} Cancel")
        print(f"  {Colors.colorize('[d]', Colors.INFO + Colors.BOLD)} View diff")
        # Only show interactive staging for 'add' commands
        if "add" in command:
            print(f"  {Colors.colorize('[i]', Colors.WARNING + Colors.BOLD)} Interactive staging")
        print()
        choice = input(f"  {Colors.colorize('Choice:', Colors.BRIGHT_WHITE + Colors.BOLD)} ").strip().lower()
        return choice
