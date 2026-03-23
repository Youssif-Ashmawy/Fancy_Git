import json
import os
import re
import textwrap
from datetime import datetime
try:
    import importlib.resources as resources
except ImportError:
    import importlib_resources as resources


class MermaidExporter:
    def __init__(self, runner):
        self.runner = runner
        self._image_base_path = self._get_image_base_path()

    def _get_image_base_path(self) -> str:
        """Get the base path for images, handling both development and installed environments"""
        # Try to get the path from installed package data first
        try:
            # When installed, try to find images in the package
            if resources.is_resource('fancygit', 'images'):
                return resources.files('fancygit').joinpath('images')
        except Exception:
            pass
        
        # Fallback to development environment - look relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        images_path = os.path.join(project_root, 'images')
        
        if os.path.exists(images_path):
            return images_path
        
        # Final fallback - assume images are in the same directory as the HTML
        return '.'

    def _get_image_url(self, image_name: str) -> str:
        """Get proper URL for image files"""
        # First try to get the file as a resource (installed package)
        try:
            if resources.is_resource('fancygit', f'images/{image_name}'):
                # For installed packages, we'll embed the image as base64
                image_path = resources.files('fancygit').joinpath('images', image_name)
                if hasattr(image_path, 'read_bytes'):
                    # Python 3.9+ Path object
                    return self._bytes_to_base64(image_path.read_bytes(), image_name)
                elif os.path.exists(str(image_path)):
                    return self._image_to_base64(str(image_path))
        except Exception:
            pass
        
        # In development, use absolute path
        abs_path = os.path.join(self._image_base_path, image_name)
        if os.path.exists(abs_path):
            return self._image_to_base64(abs_path)
        
        # If not found, return empty string to avoid broken images
        return ''

    def _bytes_to_base64(self, image_bytes: bytes, image_name: str) -> str:
        """Convert image bytes to base64 data URL"""
        try:
            import base64
            encoded = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine MIME type
            if image_name.lower().endswith('.png'):
                mime_type = 'image/png'
            elif image_name.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif image_name.lower().endswith('.gif'):
                mime_type = 'image/gif'
            else:
                mime_type = 'image/png'  # default
            
            return f'data:{mime_type};base64,{encoded}'
        except Exception:
            return ''

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 data URL"""
        try:
            with open(image_path, 'rb') as img_file:
                image_bytes = img_file.read()
                image_name = os.path.basename(image_path)
                return self._bytes_to_base64(image_bytes, image_name)
        except Exception:
            return ''

    def _git(self, args):
        return self.runner.run_git_command(args)

    def _sanitize_node_id(self, value: str) -> str:
        safe = []
        for ch in value:
            if ch.isalnum() or ch == '_':
                safe.append(ch)
            else:
                safe.append('_')
        out = ''.join(safe)
        if not out:
            out = 'node'
        if out[0].isdigit():
            out = f'n_{out}'
        return out

    def _get_node_style(self, node_type: str, importance: str = 'normal') -> str:
        """Get CSS styling for nodes based on type and importance"""
        styles = {
            'critical': 'fill:#dc2626,stroke:#991b1b,color:#fff,font-weight:bold',
            'important': 'fill:#ea580c,stroke:#c2410c,color:#fff,font-weight:bold', 
            'normal': 'fill:#3b82f6,stroke:#2563eb,color:#fff',
            'secondary': 'fill:#6b7280,stroke:#4b5563,color:#fff',
            'success': 'fill:#059669,stroke:#047857,color:#fff',
            'warning': 'fill:#d97706,stroke:#b45309,color:#fff',
            'error': 'fill:#dc2626,stroke:#991b1b,color:#fff'
        }
        return styles.get(importance, styles['normal'])

    def _calculate_file_importance(self, file_path: str) -> str:
        """Calculate file importance for better visualization"""
        file_name = os.path.basename(file_path).lower()
        
        # Critical source files
        if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h')):
            if file_name in ['main.py', 'app.py', 'index.js', 'app.ts', '__init__.py']:
                return 'critical'
            return 'important'
        
        # Configuration and documentation
        elif file_path.endswith(('.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini')):
            if file_name in ['readme.md', 'package.json', 'requirements.txt', 'setup.py']:
                return 'important'
            return 'normal'
        
        # Build and dependency files
        elif file_path.endswith(('.lock', 'pipfile', 'dockerfile', 'makefile')):
            return 'important'
        
        # Hidden and cache files
        elif file_name.startswith('.') or file_path.endswith(('.pyc', '.pyo', '.pyd')):
            return 'secondary'
        
        # Test files
        elif 'test' in file_path.lower() or file_path.endswith(('.test.js', '.spec.js', '_test.py')):
            return 'normal'
        
        return 'normal'

    def _escape_label(self, value: str) -> str:
        """Escape labels for Mermaid diagrams"""
        # Remove all whitespace that could cause line breaks
        value = value.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
        value = value.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
        # Replace multiple spaces with single space
        import re
        value = re.sub(r'\s+', ' ', value)
        # Escape quotes but keep other characters
        return value.replace('"', "'")

    def _parse_gitignore(self, repo_root: str) -> set[str]:
        """Parse .gitignore file and return a set of patterns to ignore"""
        gitignore_path = os.path.join(repo_root, '.gitignore')
        ignore_patterns = set()
        
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Remove trailing slashes for directory matching
                    if line.endswith('/'):
                        line = line[:-1]
                    ignore_patterns.add(line)
        
        # Always add these essential directories for safety
        ignore_patterns.update({'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.fancygit'})
        return ignore_patterns

    def _discover_python_files(self, repo_root: str) -> list[str]:
        out: list[str] = []
        ignore_patterns = self._parse_gitignore(repo_root)
        
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [
                d for d in dirs
                if d not in ignore_patterns
            ]

            for fn in files:
                if fn.endswith('.py'):
                    out.append(os.path.join(root, fn))
        return out

    def _module_name_from_path(self, repo_root: str, path: str) -> str:
        rel = os.path.relpath(path, repo_root)
        rel = rel.replace(os.sep, '/')
        if rel.endswith('.py'):
            rel = rel[:-3]
        if rel.endswith('/__init__'):
            rel = rel[: -len('/__init__')]
        return rel.replace('/', '.')

    def _parse_imports_from_source(self, source: str, current_module: str) -> set[str]:
        imports: set[str] = set()
        for raw in source.splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            m1 = re.match(r'^import\s+([a-zA-Z0-9_\.]+)', line)
            if m1:
                imports.add(m1.group(1))
                continue
            m2 = re.match(r'^from\s+([a-zA-Z0-9_\.]+)\s+import\s+', line)
            if m2:
                base = m2.group(1)
                if base.startswith('.'):
                    dots = len(base) - len(base.lstrip('.'))
                    base_rest = base.lstrip('.')
                    parts = current_module.split('.')
                    if dots <= len(parts):
                        prefix = parts[: len(parts) - dots]
                        resolved = '.'.join([p for p in prefix if p] + ([base_rest] if base_rest else []))
                        if resolved:
                            imports.add(resolved)
                else:
                    imports.add(base)
        return imports

    def python_import_dependency_flowchart(self, repo_root: str) -> str:
        py_files = self._discover_python_files(repo_root)
        module_by_path: dict[str, str] = {}
        path_by_module: dict[str, str] = {}

        for p in py_files:
            m = self._module_name_from_path(repo_root, p)
            module_by_path[p] = m
            path_by_module[m] = p

        edges: set[tuple[str, str]] = set()

        for p in py_files:
            cur_mod = module_by_path[p]
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    src = f.read()
            except Exception:
                continue

            imports = self._parse_imports_from_source(src, cur_mod)
            for imp in imports:
                if imp in path_by_module:
                    edges.add((cur_mod, imp))

        lines = ['flowchart LR']

        def node(mod: str) -> str:
            return self._sanitize_node_id(mod)

        # Calculate importance for modules
        module_imports_count = {}
        for src, dst in edges:
            module_imports_count[src] = module_imports_count.get(src, 0) + 1
            module_imports_count[dst] = module_imports_count.get(dst, 0) + 1

        mods = sorted({m for e in edges for m in e})
        for m in mods:
            importance = self._calculate_module_importance(m, module_imports_count.get(m, 0))
            icon = self._get_module_icon(m)
            label = f'{icon} {self._escape_label(m)}'
            lines.append(f'  {node(m)}["{label}"]')
            lines.append(f'  class {node(m)} {importance}')

        # Add edges with styling
        for a, b in sorted(edges):
            lines.append(f'  {node(a)} --> {node(b)}')

        # Add styling classes
        lines.extend([
            '  classDef critical fill:#dc2626,stroke:#991b1b,color:#fff,font-weight:bold;',
            '  classDef important fill:#ea580c,stroke:#c2410c,color:#fff,font-weight:bold;',
            '  classDef normal fill:#3b82f6,stroke:#2563eb,color:#fff;',
            '  classDef secondary fill:#6b7280,stroke:#4b5563,color:#fff;'
        ])

        return '\n'.join(lines) + '\n'

    def _calculate_module_importance(self, module_name: str, import_count: int) -> str:
        """Calculate importance of a module based on name and usage"""
        # Critical modules
        if module_name in ['main', 'app', '__init__', 'index'] or import_count > 5:
            return 'critical'
        
        # Important modules
        if any(keyword in module_name.lower() for keyword in ['core', 'utils', 'config', 'models']) or import_count > 2:
            return 'important'
        
        # Test modules are secondary
        if 'test' in module_name.lower():
            return 'secondary'
        
        return 'normal'

    def _get_module_icon(self, module_name: str) -> str:
        """Get appropriate icon for module type"""
        if module_name in ['main', 'app', '__init__']:
            return '🚀'
        elif 'test' in module_name.lower():
            return '🧪'
        elif any(keyword in module_name.lower() for keyword in ['config', 'settings']):
            return '⚙️'
        elif any(keyword in module_name.lower() for keyword in ['util', 'helper']):
            return '🛠️'
        elif any(keyword in module_name.lower() for keyword in ['model', 'data']):
            return '📊'
        else:
            return '📦'

    def repo_file_structure_flowchart(self, repo_root: str, max_nodes: int = 75) -> str:
        lines = ['flowchart TB']
        ignore_patterns = self._parse_gitignore(repo_root)

        def skip_dir(name: str) -> bool:
            return name in ignore_patterns

        root_id = 'repo_root'
        root_label = self._escape_label(os.path.basename(os.path.abspath(repo_root)) or 'repo')
        root_style = self._get_node_style('directory', 'critical')
        lines.append(f'  {root_id}["{root_label}"]')
        lines.append(f'  class {root_id} critical')

        node_count = 1
        ids: dict[str, str] = {repo_root: root_id}
        important_files = []
        normal_files = []

        for current_root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if not skip_dir(d)]
            rel_root = os.path.relpath(current_root, repo_root)
            parent_path = repo_root if rel_root == '.' else current_root

            parent_id = ids.get(parent_path)
            if parent_id is None:
                parent_id = self._sanitize_node_id(f'path_{rel_root}')
                ids[parent_path] = parent_id
                label = self._escape_label(rel_root)
                lines.append(f'  {parent_id}["{label}/"]')
                lines.append(f'  {root_id} --> {parent_id}')
                node_count += 1

            # Process directories
            for d in dirs:
                if node_count >= max_nodes:
                    break
                p = os.path.join(current_root, d)
                rel = os.path.relpath(p, repo_root)
                nid = self._sanitize_node_id(f'dir_{rel}')
                ids[p] = nid
                
                # Style important directories differently
                importance = 'important' if d in ['src', 'lib', 'app', 'components'] else 'normal'
                style = self._get_node_style('directory', importance)
                lines.append(f'  {nid}["{self._escape_label(d)}/"]')
                lines.append(f'  {parent_id} --> {nid}')
                node_count += 1

            if node_count >= max_nodes:
                break

            # Categorize files by importance
            show_files = [f for f in sorted(files) if not f.endswith('.pyc') and f != '.DS_Store']
            for f in show_files[:12]:  # Show fewer files per directory for smaller diagrams
                if node_count >= max_nodes:
                    break
                p = os.path.join(current_root, f)
                rel = os.path.relpath(p, repo_root)
                nid = self._sanitize_node_id(f'file_{rel}')
                
                importance = self._calculate_file_importance(p)
                if importance in ['critical', 'important']:
                    important_files.append((nid, f, parent_id, importance))
                else:
                    normal_files.append((nid, f, parent_id, importance))
                
                node_count += 1

            if len(show_files) > 12 and node_count < max_nodes:
                more_id = self._sanitize_node_id(f'file_{rel_root}_more')
                lines.append(f'  {more_id}["... +{len(show_files) - 12} more"]')
                lines.append(f'  {parent_id} --> {more_id}')
                node_count += 1

        # Add important files first with styling
        for nid, f, parent_id, importance in important_files:
            lines.append(f'  {nid}["{self._escape_label(f)}"]')
            lines.append(f'  {parent_id} --> {nid}')
            lines.append(f'  class {nid} {importance}')

        # Add normal files
        for nid, f, parent_id, importance in normal_files:
            lines.append(f'  {nid}["{self._escape_label(f)}"]')
            lines.append(f'  {parent_id} --> {nid}')
            lines.append(f'  class {nid} {importance}')

        if node_count >= max_nodes:
            lines.append(f'  cutoff["(truncated at ~{max_nodes} nodes)"]')
            lines.append(f'  {root_id} --> cutoff')

        # Add CSS classes for styling
        lines.extend([
            '  classDef critical fill:#dc2626,stroke:#991b1b,color:#fff,font-weight:bold;',
            '  classDef important fill:#ea580c,stroke:#c2410c,color:#fff,font-weight:bold;',
            '  classDef normal fill:#3b82f6,stroke:#2563eb,color:#fff;',
            '  classDef secondary fill:#6b7280,stroke:#4b5563,color:#fff;'
        ])

        return '\n'.join(lines) + '\n'

    def repo_status_flowchart(self, repo_state: dict) -> str:
        branch = repo_state.get('branch') or '(detached)'
        ahead = int(repo_state.get('ahead') or 0)
        behind = int(repo_state.get('behind') or 0)

        staged = repo_state.get('staged') or []
        modified = repo_state.get('modified') or []
        untracked = repo_state.get('untracked') or []
        conflicts = repo_state.get('conflicts') or []

        clean = bool(repo_state.get('clean'))

        lines = [
            'flowchart TB',
            f'  repo["📁 Repository"] --> branch["🌿 Branch: {self._escape_label(branch)}"]',
            f'  branch --> sync["🔄 Sync: ↑{ahead} ↓{behind}"]',
            f'  repo --> clean["✨ Clean: {str(clean).lower()}"]',
            '  repo --> buckets{💼 Working Tree}',
            f'  buckets --> staged["📋 Staged ({len(staged)})"]',
            f'  buckets --> modified["✏️ Modified ({len(modified)})"]',
            f'  buckets --> untracked["❓ Untracked ({len(untracked)})"]',
            f'  buckets --> conflicts["⚠️ Conflicts ({len(conflicts)})"]',
        ]

        # Style based on status
        clean_style = 'success' if clean else 'warning'
        sync_style = 'normal' if ahead == 0 and behind == 0 else 'important' if ahead > 0 else 'secondary'
        
        lines.extend([
            f'  class repo critical;',
            f'  class branch important;',
            f'  class sync {sync_style};',
            f'  class clean {clean_style};',
            f'  class staged important;',
            f'  class modified warning;',
            f'  class untracked secondary;',
            f'  class conflicts error;',
        ])

        def add_file_nodes(group_id: str, files: list[str], max_show: int = 5):
            for idx, f in enumerate(files[:max_show]):
                node_id = f'{group_id}_{idx}'
                # Add file type icons and truncate long names
                icon = '🐍' if f.endswith('.py') else '📄' if f.endswith('.md') else '📄'
                clean_name = f.replace('\n', ' ').replace('\r', ' ').strip()
                if len(clean_name) > 25:
                    clean_name = clean_name[:22] + '...'
                lines.append(f'  {group_id} --> {node_id}["{icon} {self._escape_label(clean_name)}"]')
            if len(files) > max_show:
                lines.append(f'  {group_id} --> {group_id}_more["... +{len(files) - max_show} more"]')

        add_file_nodes('staged', staged)
        add_file_nodes('modified', modified)
        add_file_nodes('untracked', untracked)
        add_file_nodes('conflicts', conflicts)

        lines.extend([
            '  classDef critical fill:#dc2626,stroke:#991b1b,color:#fff,font-weight:bold;',
            '  classDef important fill:#ea580c,stroke:#c2410c,color:#fff,font-weight:bold;',
            '  classDef normal fill:#3b82f6,stroke:#2563eb,color:#fff;',
            '  classDef secondary fill:#6b7280,stroke:#4b5563,color:#fff;',
            '  classDef success fill:#059669,stroke:#047857,color:#fff;',
            '  classDef warning fill:#d97706,stroke:#b45309,color:#fff;',
            '  classDef error fill:#dc2626,stroke:#991b1b,color:#fff;',
        ])

        return '\n'.join(lines) + '\n'

    def commit_graph_gitgraph(self, max_commits: int = 15) -> str:
        args = [
            'log',
            f'-n{max_commits}',
            '--date=short',
            '--pretty=format:%H%x1f%h%x1f%d%x1f%ad%x1f%s',
        ]
        returncode, stdout, stderr = self._git(args)
        if returncode != 0:
            msg = (stderr or stdout or '').strip()
            if not msg:
                msg = 'Unable to read git log'
            raise RuntimeError(msg)

        lines = ['flowchart TD']

        commits = []
        for raw in stdout.splitlines():
            parts = raw.split('\x1f')
            if len(parts) != 5:
                continue
            _full, short, decos, date, subject = parts
            
            # Simple clean label
            clean_subject = subject.replace('\n', ' ').replace('\r', ' ').strip()
            if len(clean_subject) > 50:
                clean_subject = clean_subject[:50] + '...'
            
            label = f'{short} {date} {clean_subject}'
            label = self._escape_label(label)
            commits.append((short, label))

        # Create simple nodes
        for i, (short, label) in enumerate(commits):
            node_id = self._sanitize_node_id(f'commit_{short}')
            lines.append(f'  {node_id}["{label}"]')

        # Create connections
        for i in range(len(commits) - 1):
            current_id = self._sanitize_node_id(f'commit_{commits[i][0]}')
            next_id = self._sanitize_node_id(f'commit_{commits[i+1][0]}')
            lines.append(f'  {current_id} --> {next_id}')

        return '\n'.join(lines) + '\n'

    def build_html(self, diagrams: dict, title: str = 'FancyGit Repository Visualization') -> str:
        payload = json.dumps(diagrams)
        now = datetime.now().isoformat(timespec='seconds')
        
        # Get proper image URLs
        light_logo_url = self._get_image_url('light_background_logo.png')
        dark_logo_url = self._get_image_url('dark_background_logo.png')

        return textwrap.dedent(
            f"""\
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width,initial-scale=1" />
                <title>{self._escape_label(title)}</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                <style>
                  :root {{
                    --bg-primary: #ffffff;
                    --bg-secondary: #f8fafc;
                    --bg-tertiary: #f1f5f9;
                    --text-primary: #1e293b;
                    --text-secondary: #64748b;
                    --text-tertiary: #94a3b8;
                    --border: #e2e8f0;
                    --accent: #3b82f6;
                    --accent-hover: #2563eb;
                    --success: #059669;
                    --warning: #d97706;
                    --error: #dc2626;
                    --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
                    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
                  }}

                  [data-theme="dark"] {{
                    --bg-primary: #0f172a;
                    --bg-secondary: #1e293b;
                    --bg-tertiary: #334155;
                    --text-primary: #f8fafc;
                    --text-secondary: #cbd5e1;
                    --text-tertiary: #94a3b8;
                    --border: #334155;
                    --accent: #60a5fa;
                    --accent-hover: #3b82f6;
                  }}

                  * {{
                    box-sizing: border-box;
                  }}

                  body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: var(--bg-secondary);
                    color: var(--text-primary);
                    line-height: 1.6;
                  }}

                  .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                  }}

                  .header {{
                    background: var(--bg-primary);
                    border-bottom: 1px solid var(--border);
                    padding: 20px 0;
                    margin-bottom: 24px;
                    box-shadow: var(--shadow);
                  }}

                  .header-content {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 16px;
                  }}

                  .header-left {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex: 1;
                  }}

                  h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                    color: var(--text-primary);
                  }}

                  .logo {{
                    width: 80px;
                    height: 80px;
                    background-image: url('{light_logo_url}');
                    background-size: contain;
                    background-repeat: no-repeat;
                    background-position: center;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 20px;
                  }}
                  
                  [data-theme="dark"] .logo {{
                    background-image: url('{dark_logo_url}');
                  }}

                  .meta {{
                    color: var(--text-secondary);
                    font-size: 14px;
                  }}

                  .controls {{
                    display: flex;
                    gap: 12px;
                    align-items: center;
                    flex-wrap: wrap;
                  }}

                  .btn {{
                    padding: 8px 16px;
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    background: var(--bg-primary);
                    color: var(--text-primary);
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    text-decoration: none;
                  }}

                  .btn:hover {{
                    background: var(--bg-tertiary);
                    border-color: var(--accent);
                  }}

                  .btn-primary {{
                    background: var(--accent);
                    color: white;
                    border-color: var(--accent);
                  }}

                  .btn-primary:hover {{
                    background: var(--accent-hover);
                    border-color: var(--accent-hover);
                  }}

                  .btn-icon {{
                    padding: 8px;
                    background: transparent;
                    border: 1px solid transparent;
                  }}

                  .btn-icon:hover {{
                    background: var(--bg-tertiary);
                  }}

                  .tabs {{
                    display: flex;
                    gap: 8px;
                    margin-bottom: 24px;
                    border-bottom: 1px solid var(--border);
                    overflow-x: auto;
                  }}

                  .tab {{
                    padding: 12px 20px;
                    background: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    color: var(--text-secondary);
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                  }}

                  .tab:hover {{
                    color: var(--text-primary);
                    background: var(--bg-tertiary);
                  }}

                  .tab.active {{
                    color: var(--accent);
                    border-bottom-color: var(--accent);
                  }}

                  .tab-content {{
                    display: none;
                  }}

                  .tab-content.active {{
                    display: block;
                  }}

                  .card {{
                    background: var(--bg-primary);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: var(--shadow);
                    margin-bottom: 20px;
                  }}

                  .card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                    gap: 12px;
                  }}

                  .card-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: var(--text-primary);
                    margin: 0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                  }}

                  .card-actions {{
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                  }}

                  .mermaid {{
                    min-height: 500px;
                    border-radius: 8px;
                    overflow: auto;
                    background: var(--bg-tertiary);
                    padding: 20px;
                    font-size: 14px;
                  }}

                  .source-code {{
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border);
                    border-radius: 8px;
                    padding: 16px;
                    margin-top: 16px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 12px;
                    line-height: 1.4;
                    overflow: auto;
                    max-height: 400px;
                    white-space: pre-wrap;
                    color: var(--text-primary);
                  }}

                  @media (max-width: 768px) {{
                    .container {{
                      padding: 12px;
                    }}
                    
                    .header-content {{
                      flex-direction: column;
                      align-items: stretch;
                    }}
                    
                    .controls {{
                      justify-content: center;
                    }}
                    
                    .search-box input {{
                      width: 100%;
                    }}
                    
                    .tabs {{
                      gap: 4px;
                    }}
                    
                    .tab {{
                      padding: 8px 12px;
                      font-size: 13px;
                    }}
                  }}

                  svg .cluster > text {{ display: none; }}
                  svg g.cluster-label text {{ display: none; }}
                </style>
              </head>
              <body>
                <div class="header">
                  <div class="header-content">
                    <div class="header-left">
                      <div class="logo"></div>
                      <div>
                        <h1>{self._escape_label(title)}</h1>
                        <div class="meta">Generated: {now}</div>
                      </div>
                    </div>
                    <div class="controls">
                      <button class="btn btn-icon" id="themeToggle" title="Toggle theme">
                        <i class="fas fa-moon"></i>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="container">
                  <div class="tabs" id="tabContainer"></div>
                  <div id="contentContainer"></div>
                </div>

                <script>
                  const diagrams = {payload};
                  const diagramNames = Object.keys(diagrams);
                  let currentTheme = 'light';
                  let activeTab = 0;

                  function initializeTabs() {{
                    const tabContainer = document.getElementById('tabContainer');
                    const contentContainer = document.getElementById('contentContainer');
                    
                    diagramNames.forEach((name, index) => {{
                      const tab = document.createElement('button');
                      tab.className = 'tab' + (index === 0 ? ' active' : '');
                      tab.innerHTML = `<i class="fas fa-diagram-project"></i> ${{name}}`;
                      tab.onclick = () => switchTab(index);
                      tabContainer.appendChild(tab);
                      
                      const content = document.createElement('div');
                      content.className = 'tab-content' + (index === 0 ? ' active' : '');
                      content.innerHTML = createTabContent(name, diagrams[name], index);
                      contentContainer.appendChild(content);
                    }});
                  }}

                  function createTabContent(name, code, index) {{
                    return `
                      <div class="card">
                        <div class="card-header">
                          <h2 class="card-title">
                            <i class="fas fa-diagram-project"></i>
                            ${{name}}
                          </h2>
                          <div class="card-actions">
                            <button class="btn" onclick="copyToClipboard(${{index}})">
                              <i class="fas fa-copy"></i>
                              Copy
                            </button>
                            <button class="btn" onclick="toggleSource(${{index}})">
                              <i class="fas fa-code"></i>
                              Source
                            </button>
                          </div>
                        </div>
                        <div class="mermaid" id="mermaid-${{index}}" data-diagram-index="${{index}}">${{code}}</div>
                        <div class="source-code" id="source-${{index}}" style="display: none;">${{code}}</div>
                      </div>
                    `;
                  }}

                  function renderMermaidInTab(content, index) {{
                    const mermaidDiv = content.querySelector('.mermaid');
                    if (!mermaidDiv || mermaidDiv.getAttribute('data-processed') === 'true') {{
                      return;
                    }}
                    if (typeof mermaid === 'undefined' || !mermaid.render) {{
                      return;
                    }}

                    const code = mermaidDiv.textContent.trim();
                    const diagramId = `mermaid-${{index}}-svg`;

                    mermaid.render(diagramId, code).then(function(result) {{
                      mermaidDiv.innerHTML = result.svg;
                      mermaidDiv.setAttribute('data-processed', 'true');
                    }}).catch(function(error) {{
                      console.error('Mermaid rendering error:', error);
                      mermaidDiv.innerHTML = '<div style="color: red; padding: 20px; border: 1px solid red; border-radius: 4px;">Error rendering diagram: ' + error.message + '</div>';
                    }});
                  }}

                  function switchTab(index) {{
                    const tabs = document.querySelectorAll('.tab');
                    const contents = document.querySelectorAll('.tab-content');
                    
                    tabs.forEach((tab, i) => {{
                      tab.classList.toggle('active', i === index);
                    }});
                    
                    contents.forEach((content, i) => {{
                      const isActive = i === index;
                      content.classList.toggle('active', isActive);
                      
                      if (isActive) {{
                        renderMermaidInTab(content, index);
                      }}
                    }});
                    
                    activeTab = index;
                  }}

                  function copyToClipboard(index) {{
                    const name = diagramNames[index];
                    const code = diagrams[name];
                    navigator.clipboard.writeText(code).then(() => {{
                      showNotification('Copied to clipboard!');
                    }});
                  }}

                  function toggleSource(index) {{
                    const source = document.getElementById(`source-${{index}}`);
                    const isVisible = source.style.display !== 'none';
                    source.style.display = isVisible ? 'none' : 'block';
                  }}

                  function showNotification(message) {{
                    const notification = document.createElement('div');
                    notification.style.cssText = `
                      position: fixed;
                      top: 20px;
                      right: 20px;
                      background: var(--accent);
                      color: white;
                      padding: 12px 20px;
                      border-radius: 8px;
                      box-shadow: var(--shadow-lg);
                      z-index: 1000;
                      animation: slideIn 0.3s ease;
                    `;
                    notification.textContent = message;
                    document.body.appendChild(notification);
                    
                    setTimeout(() => {{
                      notification.remove();
                    }}, 3000);
                  }}

                  function toggleTheme() {{
                    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
                    document.documentElement.setAttribute('data-theme', currentTheme);
                    const icon = document.querySelector('#themeToggle i');
                    icon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
                    localStorage.setItem('theme', currentTheme);
                  }}

                  function expandAll() {{
                    // Function removed - no longer needed
                  }}

                  function exportAll() {{
                    // Function removed - no longer needed
                  }}

                  function setupSearch() {{
                    // Function removed - no longer needed
                  }}

                  function setupFilters() {{
                    // Function removed - no longer needed
                  }}

                  document.addEventListener('DOMContentLoaded', () => {{
                    const savedTheme = localStorage.getItem('theme') || 'light';
                    currentTheme = savedTheme;
                    document.documentElement.setAttribute('data-theme', currentTheme);
                    
                    document.getElementById('themeToggle').onclick = toggleTheme;
                    
                    initializeTabs();
                  }});
                </script>

                <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                <script>
                  // Initialize Mermaid with proper settings
                  document.addEventListener('DOMContentLoaded', function() {{
                    mermaid.initialize({{ 
                      startOnLoad: false,
                      theme: 'default',
                      themeVariables: {{
                        primaryColor: '#3b82f6',
                        primaryTextColor: '#1e293b',
                        primaryBorderColor: '#2563eb',
                        lineColor: '#64748b',
                        secondaryColor: '#f1f5f9',
                        tertiaryColor: '#f8fafc',
                        fontSize: '16px',
                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif'
                      }},
                      flowchart: {{
                        useMaxWidth: false,
                        htmlLabels: true,
                        curve: 'basis',
                        padding: 20,
                        nodeSpacing: 50,
                        rankSpacing: 80
                      }},
                      securityLevel: 'loose',
                      fontSize: 16
                    }});

                    // Render only the active tab on load (inactive tabs render on-demand)
                    const activeContent = document.querySelector('.tab-content.active');
                    if (activeContent) {{
                      const indexAttr = activeContent.querySelector('.mermaid')?.getAttribute('data-diagram-index');
                      const index = indexAttr ? parseInt(indexAttr, 10) : 0;
                      if (typeof renderMermaidInTab === 'function') {{
                        renderMermaidInTab(activeContent, index);
                      }}
                    }}
                  }});
                </script>
              </body>
            </html>
            """
        )

    def export_all(self, output_dir: str, repo_state: dict, max_commits: int = 15) -> dict:
        os.makedirs(output_dir, exist_ok=True)

        repo_root = os.getcwd()

        status_mmd = self.repo_status_flowchart(repo_state)
        graph_mmd = self.commit_graph_gitgraph(max_commits=max_commits)
        deps_mmd = self.python_import_dependency_flowchart(repo_root)
        tree_mmd = self.repo_file_structure_flowchart(repo_root)

        diagrams = {
            'Repo Status': status_mmd,
            'Commit Graph': graph_mmd,
            'Python Import Dependencies': deps_mmd,
            'Repo File Structure': tree_mmd,
        }

        html = self.build_html(diagrams)

        status_path = os.path.join(output_dir, 'repo_status.mmd')
        graph_path = os.path.join(output_dir, 'commit_graph.mmd')
        deps_path = os.path.join(output_dir, 'python_deps.mmd')
        tree_path = os.path.join(output_dir, 'repo_tree.mmd')
        html_path = os.path.join(output_dir, 'repo_visualization.html')

        with open(status_path, 'w', encoding='utf-8') as f:
            f.write(status_mmd)
        with open(graph_path, 'w', encoding='utf-8') as f:
            f.write(graph_mmd)
        with open(deps_path, 'w', encoding='utf-8') as f:
            f.write(deps_mmd)
        with open(tree_path, 'w', encoding='utf-8') as f:
            f.write(tree_mmd)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return {
            'status_mmd': status_path,
            'graph_mmd': graph_path,
            'deps_mmd': deps_path,
            'tree_mmd': tree_path,
            'html': html_path,
        }
