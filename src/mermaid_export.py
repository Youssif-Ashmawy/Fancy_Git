import json
import os
import re
import textwrap
from datetime import datetime


class MermaidExporter:
    def __init__(self, runner):
        self.runner = runner

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

    def _escape_label(self, value: str) -> str:
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

        mods = sorted({m for e in edges for m in e})
        for m in mods:
            lines.append(f'  {node(m)}["{self._escape_label(m)}"]')

        for a, b in sorted(edges):
            lines.append(f'  {node(a)} --> {node(b)}')

        return '\n'.join(lines) + '\n'

    def repo_file_structure_flowchart(self, repo_root: str, max_nodes: int = 250) -> str:
        lines = ['flowchart TB']
        ignore_patterns = self._parse_gitignore(repo_root)

        def skip_dir(name: str) -> bool:
            return name in ignore_patterns

        root_id = 'repo_root'
        root_label = self._escape_label(os.path.basename(os.path.abspath(repo_root)) or 'repo')
        lines.append(f'  {root_id}["{root_label}"]')

        node_count = 1
        ids: dict[str, str] = {repo_root: root_id}

        for current_root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if not skip_dir(d)]
            rel_root = os.path.relpath(current_root, repo_root)
            parent_path = repo_root if rel_root == '.' else current_root

            parent_id = ids.get(parent_path)
            if parent_id is None:
                parent_id = self._sanitize_node_id(f'path_{rel_root}')
                ids[parent_path] = parent_id
                label = self._escape_label(rel_root)
                lines.append(f'  {parent_id}["{label}"]')
                lines.append(f'  {root_id} --> {parent_id}')
                node_count += 1

            for d in dirs:
                if node_count >= max_nodes:
                    break
                p = os.path.join(current_root, d)
                rel = os.path.relpath(p, repo_root)
                nid = self._sanitize_node_id(f'dir_{rel}')
                ids[p] = nid
                lines.append(f'  {nid}["{self._escape_label(d)}/"]')
                lines.append(f'  {parent_id} --> {nid}')
                node_count += 1

            if node_count >= max_nodes:
                break

            show_files = [f for f in sorted(files) if not f.endswith('.pyc') and f != '.DS_Store']
            for f in show_files[:30]:
                if node_count >= max_nodes:
                    break
                p = os.path.join(current_root, f)
                rel = os.path.relpath(p, repo_root)
                nid = self._sanitize_node_id(f'file_{rel}')
                lines.append(f'  {nid}["{self._escape_label(f)}"]')
                lines.append(f'  {parent_id} --> {nid}')
                node_count += 1

            if len(show_files) > 30 and node_count < max_nodes:
                more_id = self._sanitize_node_id(f'file_{rel_root}_more')
                lines.append(f'  {more_id}["... +{len(show_files) - 30} more"]')
                lines.append(f'  {parent_id} --> {more_id}')
                node_count += 1

        if node_count >= max_nodes:
            lines.append(f'  cutoff["(truncated at ~{max_nodes} nodes)"]')
            lines.append(f'  {root_id} --> cutoff')

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
            f'  repo["Repo"] --> branch["Branch: {self._escape_label(branch)}"]',
            f'  branch --> sync["Sync: ahead {ahead} / behind {behind}"]',
            f'  repo --> clean["Clean: {str(clean).lower()}"]',
            '  repo --> buckets{Working Tree}',
            f'  buckets --> staged["Staged ({len(staged)})"]',
            f'  buckets --> modified["Modified ({len(modified)})"]',
            f'  buckets --> untracked["Untracked ({len(untracked)})"]',
            f'  buckets --> conflicts["Conflicts ({len(conflicts)})"]',
        ]

        def add_file_nodes(group_id: str, files: list[str]):
            for idx, f in enumerate(files[:30]):
                node_id = f'{group_id}_{idx}'
                lines.append(f'  {group_id} --> {node_id}["{self._escape_label(f)}"]')
            if len(files) > 30:
                lines.append(f'  {group_id} --> {group_id}_more["... +{len(files) - 30} more"]')

        add_file_nodes('staged', staged)
        add_file_nodes('modified', modified)
        add_file_nodes('untracked', untracked)
        add_file_nodes('conflicts', conflicts)

        lines.extend([
            '  classDef bad fill:#7f1d1d,stroke:#fecaca,color:#fff;',
            '  classDef warn fill:#78350f,stroke:#fed7aa,color:#fff;',
            '  class conflicts bad;',
        ])

        if len(modified) > 0 or len(untracked) > 0:
            lines.append('  class modified,untracked warn;')

        return '\n'.join(lines) + '\n'

    def commit_graph_gitgraph(self, max_commits: int = 40) -> str:
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

        # Use flowchart for vertical layout to improve commit readability
        commits = []
        for raw in stdout.splitlines():
            parts = raw.split('\x1f')
            if len(parts) != 5:
                continue
            _full, short, decos, date, subject = parts
            label = f'{short} {date} {subject}'.strip()
            if decos.strip():
                label = f'{label} {decos.strip()}'
            label = self._escape_label(label)
            commits.append((short, label))

        # Create nodes for each commit
        for i, (short, label) in enumerate(commits):
            node_id = self._sanitize_node_id(f'commit_{short}')
            lines.append(f'  {node_id}["{label}"]')

        # Create vertical connections between commits
        for i in range(len(commits) - 1):
            current_id = self._sanitize_node_id(f'commit_{commits[i][0]}')
            next_id = self._sanitize_node_id(f'commit_{commits[i+1][0]}')
            lines.append(f'  {current_id} --> {next_id}')

        return '\n'.join(lines) + '\n'

    def build_html(self, diagrams: dict, title: str = 'FancyGit Mermaid') -> str:
        payload = json.dumps(diagrams)
        now = datetime.now().isoformat(timespec='seconds')

        return textwrap.dedent(
            f"""\
            <!doctype html>
            <html lang=\"en\">
              <head>
                <meta charset=\"utf-8\" />
                <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
                <title>{self._escape_label(title)}</title>
                <style>
                  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 24px; }}
                  h1 {{ margin: 0 0 6px 0; font-size: 18px; }}
                  .meta {{ color: #6b7280; font-size: 12px; margin-bottom: 16px; }}
                  .grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
                  .card {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; background: #fff; }}
                  .card h2 {{ margin: 0 0 12px 0; font-size: 14px; color: #111827; }}
                  svg .cluster > text {{ display: none; }}
                  svg g.cluster-label text {{ display: none; }}
                  pre {{ overflow: auto; padding: 12px; border-radius: 8px; background: #0b1020; color: #d1d5db; font-size: 12px; }}
                  .toolbar {{ display:flex; gap: 10px; align-items:center; margin-bottom: 12px; }}
                  button {{ padding: 6px 10px; font-size: 12px; border-radius: 8px; border: 1px solid #d1d5db; background:#f9fafb; cursor:pointer; }}
                  button:hover {{ background:#f3f4f6; }}
                </style>
              </head>
              <body>
                <h1>{self._escape_label(title)}</h1>
                <div class=\"meta\">Generated: {now}</div>

                <div id=\"root\" class=\"grid\"></div>

                <script>
                  const diagrams = {payload};
                  const root = document.getElementById('root');

                  function mkCard(name, code) {{
                    const card = document.createElement('div');
                    card.className = 'card';
                    const h2 = document.createElement('h2');
                    h2.textContent = name;

                    const toolbar = document.createElement('div');
                    toolbar.className = 'toolbar';
                    const copyBtn = document.createElement('button');
                    copyBtn.textContent = 'Copy Mermaid';
                    copyBtn.onclick = async () => {{
                      await navigator.clipboard.writeText(code);
                      copyBtn.textContent = 'Copied';
                      setTimeout(() => copyBtn.textContent = 'Copy Mermaid', 900);
                    }};

                    const toggleBtn = document.createElement('button');
                    toggleBtn.textContent = 'Show source';

                    const mermaidDiv = document.createElement('div');
                    mermaidDiv.className = 'mermaid';
                    mermaidDiv.textContent = code;

                    const pre = document.createElement('pre');
                    pre.style.display = 'none';
                    pre.textContent = code;

                    toggleBtn.onclick = () => {{
                      const show = pre.style.display === 'none';
                      pre.style.display = show ? 'block' : 'none';
                      toggleBtn.textContent = show ? 'Hide source' : 'Show source';
                    }};

                    toolbar.appendChild(copyBtn);
                    toolbar.appendChild(toggleBtn);

                    card.appendChild(h2);
                    card.appendChild(toolbar);
                    card.appendChild(mermaidDiv);
                    card.appendChild(pre);
                    return card;
                  }}

                  Object.entries(diagrams).forEach(([name, code]) => root.appendChild(mkCard(name, code)));
                </script>

                <script type=\"module\">
                  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                  mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
                </script>
              </body>
            </html>
            """
        )

    def export_all(self, output_dir: str, repo_state: dict, max_commits: int = 40) -> dict:
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
