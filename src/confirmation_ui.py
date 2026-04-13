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
        self._render_dry_run()
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

    def _render_dry_run(self):
        """Render the dry-run preview output."""
        if not self.dry_output or self.dry_mode == "NONE":
            return

        mode_labels = {
            "REAL": "Dry Run (native)",
            "SIMULATION": "Preview (simulated)",
        }
        label = mode_labels.get(self.dry_mode, f"Dry Run ({self.dry_mode})")

        print()
        print(f"  {Colors.colorize(f'{label}:', Colors.MUTED)}")
        for line in self.dry_output.strip().split("\n")[:15]:
            line = line.strip()
            if line:
                print(f"    {Colors.colorize(line, Colors.DIM)}")

        remaining_lines = len(self.dry_output.strip().split("\n")) - 15
        if remaining_lines > 0:
            print(f"    {Colors.colorize(f'... {remaining_lines} more lines', Colors.MUTED)}")

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

    def interactive_staging(self, runner):
        """Interactive file picker for staging — lets user toggle files on/off.
        
        Args:
            runner: GitRunner instance to execute git add on selected files.
            
        Returns:
            True if files were staged, False if cancelled.
        """
        # Get all unstaged/modified files from status
        _, raw_status, _ = runner.run_git_command(['status', '--short'])
        if not raw_status.strip():
            print(color_warning("\n  No files to stage."))
            return False

        # Parse into (status_code, filename) pairs
        files = []
        for line in raw_status.strip().split("\n"):
            line = line.strip()
            if line:
                status_code = line[:2].strip()
                filename = line[2:].strip()
                files.append((status_code, filename))

        if not files:
            print(color_warning("\n  No files to stage."))
            return False

        # Track selection state — all selected by default
        selected = [True] * len(files)

        while True:
            # Clear and render the file picker
            print()
            print(Colors.colorize("─" * 12 + " Interactive Staging " + "─" * 12, Colors.WARNING, Colors.BOLD))
            print()

            for i, (status_code, filename) in enumerate(files):
                checkbox = Colors.colorize("●", Colors.SUCCESS) if selected[i] else Colors.colorize("○", Colors.MUTED)
                num = Colors.colorize(f"{i + 1:>2}", Colors.BRIGHT_WHITE, Colors.BOLD)
                print(f"  {num}  {checkbox}  {Colors.git_status(status_code)} {Colors.file_path(filename)}")

            count = sum(selected)
            total = len(files)
            print()
            print(f"  {Colors.colorize(f'{count}/{total} selected', Colors.INFO)}")
            print()
            print(f"  {Colors.colorize('[1-' + str(total) + ']', Colors.BRIGHT_WHITE + Colors.BOLD)} Toggle file   "
                  f"{Colors.colorize('[a]', Colors.WARNING + Colors.BOLD)} Toggle all   "
                  f"{Colors.colorize('[s]', Colors.SUCCESS + Colors.BOLD)} Stage selected   "
                  f"{Colors.colorize('[q]', Colors.ERROR + Colors.BOLD)} Cancel")
            print()
            action = input(f"  {Colors.colorize('Pick:', Colors.BRIGHT_WHITE + Colors.BOLD)} ").strip().lower()

            if action == 'q':
                print(color_warning("  Staging cancelled."))
                return False
            elif action == 'a':
                # Toggle all: if all selected → deselect all, else select all
                if all(selected):
                    selected = [False] * len(files)
                else:
                    selected = [True] * len(files)
            elif action == 's':
                # Stage selected files
                selected_files = [files[i][1] for i in range(len(files)) if selected[i]]
                if not selected_files:
                    print(color_warning("  No files selected. Use numbers to toggle files."))
                    continue

                print()
                for f in selected_files:
                    code, _, err = runner.run_git_command(['add', f])
                    if code == 0:
                        print(f"  {color_success('✅')} Staged: {Colors.file_path(f)}")
                    else:
                        print(f"  {color_error('❌')} Failed: {Colors.file_path(f)} — {err.strip()}")

                print()
                print(color_success(f"  Staged {len(selected_files)} file(s)."))
                return True
            else:
                # Try to parse as a number to toggle
                try:
                    idx = int(action) - 1
                    if 0 <= idx < len(files):
                        selected[idx] = not selected[idx]
                    else:
                        print(color_warning(f"  Invalid number. Enter 1-{len(files)}."))
                except ValueError:
                    print(color_warning("  Invalid input. Try a number, 'a', 's', or 'q'."))
