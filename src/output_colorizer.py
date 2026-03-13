#!/usr/bin/env python3
"""
FancyGit Output Colorizer
Intelligently colors git command outputs based on content and context
"""

import re
from typing import List, Tuple
from src.colors import Colors, color_success, color_error, color_warning, color_info, color_file, color_branch, color_header

class OutputColorizer:
    """Intelligent output coloring for git commands"""
    
    def __init__(self):
        # Git status patterns
        self.status_patterns = {
            'modified': r'^\s*modified:',
            'new_file': r'^\s*new file:',
            'deleted': r'^\s*deleted:',
            'renamed': r'^\s*renamed:',
            'copied': r'^\s*copied:',
            'untracked': r'^\s*untracked:',
            'branch': r'^On branch |^Your branch is|^Your branch and |^nothing to commit',
            'changes': r'^Changes not staged for commit|^Changes to be committed',
            'conflict': r'^\s*both |^\s*<<<<<<< |^\s======= |^\s>>>>>>> ',
        }
        
        # Git log patterns
        self.log_patterns = {
            'commit_hash': r'^commit [a-f0-9]{40}',
            'author': r'^Author:',
            'date': r'^Date:',
            'merge': r'^Merge:',
        }
        
        # Git diff patterns
        self.diff_patterns = {
            'addition': r'^\+',
            'deletion': r'^-',
            'file_header': r'^diff --git|^index |^@@ ',
            'context': r'^ ',
        }
        
        # Git branch patterns
        self.branch_patterns = {
            'current': r'^\* ',
            'remote': r'^  remotes/',
            'local': r'^  ',
        }
        
        # General patterns
        self.general_patterns = {
            'error': r'^error:|^fatal:|Failed|Cannot|Unable',
            'warning': r'^warning:|^hint:',
            'success': r'^Successfully|^Already up-to-date|^Everything up-to-date',
            'info': r'^Note:|^INFO:|^hint:',
            'file_path': r'[/\\][\w\-./\\]+\.?\w*',
        }
    
    def colorize_output(self, command: str, stdout: str, stderr: str) -> Tuple[str, str]:
        """Colorize command output based on command type and content"""
        
        if stdout:
            stdout = self._colorize_by_command(command, stdout)
        
        if stderr:
            stderr = self._colorize_stderr(stderr)
        
        return stdout, stderr
    
    def _colorize_by_command(self, command: str, output: str) -> str:
        """Route to appropriate colorizer based on command"""
        
        if command == 'status':
            return self._colorize_status(output)
        elif command == 'log':
            return self._colorize_log(output)
        elif command in ['diff', 'show']:
            return self._colorize_diff(output)
        elif command == 'branch':
            return self._colorize_branch(output)
        elif command in ['add', 'rm', 'mv']:
            return self._colorize_file_operations(output)
        elif command == 'commit':
            return self._colorize_commit(output)
        elif command in ['push', 'pull', 'fetch']:
            return self._colorize_remote(output)
        else:
            return self._colorize_generic(output)
    
    def _colorize_status(self, output: str) -> str:
        """Colorize git status output"""
        lines = output.split('\n')
        colored_lines = []
        in_untracked_section = False
        
        for line in lines:
            colored_line = line
            
            # Branch information
            if re.search(r'^On branch ', line):
                branch_name = line.replace('On branch ', '').strip()
                colored_line = f"On branch {color_branch(branch_name, True)}"
            elif re.search(r'^Your branch is ahead', line):
                colored_line = color_info(line)
            elif re.search(r'^Your branch is behind', line):
                colored_line = color_warning(line)
            elif re.search(r'^Your branch and .* have diverged', line):
                colored_line = color_warning(line)
            elif re.search(r'^nothing to commit', line):
                colored_line = color_success(line)
            
            # Section headers
            elif re.search(r'^Changes to be committed', line):
                colored_line = color_header(line)
            elif re.search(r'^Changes not staged for commit', line):
                colored_line = color_warning(line)
            elif re.search(r'^Untracked files', line):
                colored_line = color_info(line)
                in_untracked_section = True
            
            # File status - untracked files come FIRST (before general file pattern)
            elif in_untracked_section and re.search(r'^\t(.+)$', line):
                # File paths under Untracked files section
                file_path = line.strip()  # Remove tab and get just the filename
                colored_line = f"\t{color_file(file_path)}"
            elif in_untracked_section and re.search(r'^(\s{8}|\t)untracked:', line):
                match = re.search(r'untracked:\s*(.+)', line)
                if match:
                    file_path = match.group(1)
                    # Preserve original indentation
                    indent = line[:line.index('untracked:')]
                    colored_line = f"{indent}untracked: {color_file(file_path)}"
                else:
                    colored_line = Colors.muted(line)
            
            # General file pattern - LAST RESORT
            elif re.search(r'^(\s{8}|\t)(new file: |modified: |deleted: |renamed: )(.+)$', line):
                # Any other file-like line with indentation
                match = re.search(r'^(\s{8}|\t)(new file: |modified: |deleted: |renamed: )(.+)$', line)
                if match:
                    file_path = match.group(3)
                    # Preserve original indentation and file status
                    indent = line[:line.index(match.group(2))]
                    colored_line = f"{indent}{match.group(2)}{color_file(file_path)}"
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_log(self, output: str) -> str:
        """Colorize git log output"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if re.search(r'^commit [a-f0-9]{40}', line):
                # Color commit hash
                hash_match = re.search(r'(commit )([a-f0-9]{40})', line)
                if hash_match:
                    colored_line = f"{hash_match.group(1)}{color_info(hash_match.group(2))}"
            elif re.search(r'^Author:', line):
                colored_line = color_info(line)
            elif re.search(r'^Date:', line):
                colored_line = Colors.muted(line)
            elif re.search(r'^Merge:', line):
                colored_line = color_header(line)
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_diff(self, output: str) -> str:
        """Colorize git diff output"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if line.startswith('+++') or line.startswith('---'):
                # File paths
                colored_line = color_file(line)
            elif line.startswith('+') and not line.startswith('+++'):
                # Added lines
                colored_line = color_success(line)
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted lines
                colored_line = color_error(line)
            elif line.startswith('@@'):
                # Line numbers
                colored_line = color_info(line)
            elif line.startswith('diff --git'):
                colored_line = color_header(line)
            elif line.startswith('index '):
                colored_line = Colors.muted(line)
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_branch(self, output: str) -> str:
        """Colorize git branch output"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if line.startswith('* '):
                # Current branch
                branch_name = line[2:].strip()
                colored_line = f"* {color_branch(branch_name, True)}"
            elif line.startswith('  remotes/'):
                # Remote branches
                branch_name = line.replace('  remotes/', '').strip()
                colored_line = f"  {color_info(branch_name)} (remote)"
            elif line.startswith('  '):
                # Local branches
                branch_name = line[2:].strip()
                colored_line = f"  {color_branch(branch_name, False)}"
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_file_operations(self, output: str) -> str:
        """Colorize file operation outputs (add, rm, mv)"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            # Look for file paths in the output
            file_matches = re.findall(r'[/\\][\w\-./\\]+\.?\w*', line)
            for match in file_matches:
                colored_line = colored_line.replace(match, color_file(match))
            
            # Color success messages
            if re.search(r'added|removed|renamed', line, re.IGNORECASE):
                colored_line = color_success(line)
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_commit(self, output: str) -> str:
        """Colorize git commit output"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if re.search(r'\[master [a-f0-9]+\]|\[main [a-f0-9]+\]|\[develop [a-f0-9]+\]', line):
                # Branch and commit info
                colored_line = color_success(line)
            elif re.search(r'files? changed', line, re.IGNORECASE):
                colored_line = color_info(line)
            elif re.search(r'insertion|deletion', line, re.IGNORECASE):
                colored_line = Colors.muted(line)
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_remote(self, output: str) -> str:
        """Colorize remote operation outputs (push, pull, fetch)"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if re.search(r'From |To |->', line):
                colored_line = color_info(line)
            elif re.search(r'Fast-forward|Already up-to-date', line):
                colored_line = color_success(line)
            elif re.search(r'Fetching |Enumerating objects', line):
                colored_line = Colors.muted(line)
            elif re.search(r'Receiving objects|Resolving deltas', line):
                colored_line = color_info(line)
            elif re.search(r'error:|fatal:', line):
                colored_line = color_error(line)
            elif re.search(r'warning:', line):
                colored_line = color_warning(line)
            
            # Color branch names
            branch_matches = re.findall(r'[\w\-/]+->[\w\-/]+', line)
            for match in branch_matches:
                parts = match.split('->')
                if len(parts) == 2:
                    colored_line = colored_line.replace(
                        match, 
                        f"{color_branch(parts[0])} -> {color_branch(parts[1])}"
                    )
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_generic(self, output: str) -> str:
        """Generic coloring for other git commands"""
        lines = output.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            # Error patterns
            if re.search(r'^error:|^fatal:', line):
                colored_line = color_error(line)
            # Warning patterns
            elif re.search(r'^warning:|^hint:', line):
                colored_line = color_warning(line)
            # Success patterns
            elif re.search(r'^Successfully|^Already up-to-date', line):
                colored_line = color_success(line)
            # Info patterns
            elif re.search(r'^Note:|^INFO:', line):
                colored_line = color_info(line)
            # File paths
            else:
                file_matches = re.findall(r'[/\\][\w\-./\\]+\.?\w*', line)
                for match in file_matches:
                    colored_line = colored_line.replace(match, color_file(match))
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)
    
    def _colorize_stderr(self, stderr: str) -> str:
        """Colorize stderr output"""
        lines = stderr.split('\n')
        colored_lines = []
        
        for line in lines:
            colored_line = line
            
            if re.search(r'^error:|^fatal:', line):
                colored_line = color_error(line)
            elif re.search(r'^warning:|^hint:', line):
                colored_line = color_warning(line)
            else:
                colored_line = Colors.muted(line)
            
            colored_lines.append(colored_line)
        
        return '\n'.join(colored_lines)

# Convenience function
def colorize_output(command: str, stdout: str, stderr: str) -> Tuple[str, str]:
    """Convenience function to colorize output"""
    colorizer = OutputColorizer()
    return colorizer.colorize_output(command, stdout, stderr)
