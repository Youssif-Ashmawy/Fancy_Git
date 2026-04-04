#!/usr/bin/env python3
from .base_model import BaseModel
import requests
import json
from typing import List, Dict, Optional
import time

from src.config_manager import ConfigManager


class OllamaModel(BaseModel):
    """Provider for local Ollama AI models"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        config = self.config_manager.config

        self.base_url = config.ollama_api_url
        self.model = config.default_ollama_model
        self.preferred_model = self.model
        self.timeout = int(config.ollama_timeout)
        self.max_retries = int(config.ollama_max_retries)
        self.temperature = float(config.ollama_temperature)
        self.max_tokens = config.ollama_max_tokens_to_sample
        self.fallback_models = ["llama3.2", "llama3", "mistral", "codellama"]

    # ------------------------------------------------------------------ #
    # BaseModel interface                                                  #
    # ------------------------------------------------------------------ #

    def test_connection(self) -> bool:
        """Test if Ollama service is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except requests.exceptions.RequestException:
            return {}

    def _call_model(self, prompt: str) -> Optional[str]:
        """Make API call to Ollama and return the response text"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": float(self.temperature),
                    "top_p": 0.9,
                    "num_predict": int(self.max_tokens),
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                # Strip surrounding quotes/backticks sometimes added by models
                if len(response_text) >= 2 and response_text[0] == response_text[-1] and response_text[0] in ('"', "'", "`"):
                    response_text = response_text[1:-1].strip()
                response_text = response_text.replace("``", "").strip()
                return response_text if response_text else None
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")

        except requests.exceptions.Timeout:
            raise Exception("Request to Ollama timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure it's running.")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from Ollama")
        except Exception as e:
            raise Exception(f"Error calling Ollama: {str(e)}")

    # ------------------------------------------------------------------ #
    # Extra helpers                                                        #
    # ------------------------------------------------------------------ #

    def get_available_models(self) -> List[str]:
        """Return a list of model names installed in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
        except requests.exceptions.RequestException:
            return []

    def set_model(self, model: str) -> bool:
        """Switch to a different Ollama model (must be installed)"""
        available = self.get_available_models()
        if model in available:
            self.preferred_model = model
            self.model = model
            return True
        # Accept prefix match (e.g. "codellama" matches "codellama:latest")
        for m in available:
            if m.startswith(model):
                self.preferred_model = m
                self.model = m
                return True
        return False

    def get_current_model(self) -> str:
        """Return the currently active model name"""
        return self.model

    def _ensure_model_available(self) -> bool:
        """Resolve the exact installed model name (handles version tags like :latest)"""
        available = self.get_available_models()
        if not available:
            return False

        # Exact match first
        if self.preferred_model in available:
            self.model = self.preferred_model
            return True

        # Prefix match (e.g. "llama3.2" → "llama3.2:latest")
        for m in available:
            if m.startswith(self.preferred_model):
                self.model = m
                return True

        # Try fallbacks
        for fallback in self.fallback_models:
            for m in available:
                if m.startswith(fallback):
                    self.model = m
                    return True

        return False

    def generate_commit_message(self, context: Dict) -> str:
        """Generate a conventional commit message from staged-change context"""
        if not context:
            return "feat: add new functionality\n- initial implementation"

        # Switch to the configured commit model (defaults to codellama)
        previous_model = self.model
        commit_model = self.config_manager.config.default_commit_model
        switched = self.set_model(commit_model)
        if not switched:
            # Commit model not installed, fall back to whatever is available
            if not self._ensure_model_available():
                return "feat: add changes\n- unable to connect to Ollama"

        prompt = self._build_commit_prompt(context)

        # Use a tight token budget so the model can't ramble
        original_max_tokens = self.max_tokens
        self.max_tokens = 150

        try:
            for attempt in range(self.max_retries + 1):
                try:
                    response = self._call_model(prompt)
                    if response:
                        return self._format_commit_response(response)
                except Exception as e:
                    if attempt == self.max_retries:
                        return (
                            f"feat: add changes to {context.get('branch', 'current')}\n"
                            f"- fallback due to AI error: {str(e)[:50]}"
                        )
                    time.sleep(1)
        finally:
            self.max_tokens = original_max_tokens
            # Always restore the original model
            self.set_model(previous_model) or setattr(self, 'model', previous_model)

        return "feat: update repository\n- generic commit message"

    def _build_commit_prompt(self, context: Dict) -> str:
        return """Generate a git commit message for these changes. Reply with ONLY the commit message lines, no commentary.

Files changed: {files}

Diff:
{diff}

Reply with ONLY these lines (no preamble, no explanation):
<type>(<scope>): <summary under 50 chars>
- <specific change referencing actual function/class/variable names>
- <specific change>
- <specific change>""".format(
            files=", ".join(context.get("staged_files", ["files"])),
            diff=context.get("diff", "No diff available")[:2000],
        )

    def _format_commit_response(self, response: str) -> str:
        """Normalise the raw model output into summary + bullet lines"""
        import re

        # If the model wrapped its answer in a fenced code block, extract the contents
        fenced = re.search(r'`+\n?(.*?)\n?`+', response, re.DOTALL)
        if fenced:
            response = fenced.group(1).strip()

        commit_pattern = re.compile(
            r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+?\))?!?:\s+.+',
            re.IGNORECASE
        )

        all_lines = [l.strip() for l in response.split("\n")]

        def clean_summary(line: str) -> str:
            line = line.strip("`\"'")
            line = re.sub(r'^[-*\s]+', '', line)          # strip leading * or -
            line = re.sub(r'\s*\(#\d+\)\s*$', '', line)  # strip trailing (#123)
            # Normalise "(feat)(scope):" → "feat(scope):"
            line = re.sub(r'^\((\w+)\)\((\w+)\):', r'\1(\2):', line)
            # Normalise "(feat)(scope):" or "(feat):" → "feat(scope):" or "feat:"
            line = re.sub(r'^\((\w+)\)(\([\w/]+\))?:', r'\1\2:', line)
            # Normalise "(scope):" with no type → "feat(scope):"
            line = re.sub(r'^\(([^)]+)\):', r'feat(\1):', line)
            return line.strip()

        # Find the first line that looks like a real conventional commit summary
        summary = None
        summary_idx = 0
        for i, line in enumerate(all_lines):
            candidate = clean_summary(line)
            if commit_pattern.match(candidate):
                summary = candidate
                summary_idx = i
                break

        # Fallback: use first non-empty line if no conventional commit found
        if summary is None:
            for i, line in enumerate(all_lines):
                if line:
                    summary = clean_summary(line)
                    summary_idx = i
                    break

        if not summary:
            return "feat: update repository\n- implementation changes"

        # If summary doesn't start with a known commit type, prepend "feat: "
        if not commit_pattern.match(summary):
            summary = "feat: " + re.sub(r'^[\w/()]+:\s*', '', summary)

        # Collect bullet lines that follow the summary
        skip_prefixes = ("breaking change", "also,", "note:", "this commit", "the default",
                         "the message", "fixes #", "closes #", "resolves #")
        bullets = []
        for line in all_lines[summary_idx + 1:]:
            line = line.strip("`\"'").strip()
            if not line or line.startswith("#"):
                continue
            # Normalise "- * foo", "* foo", "+ foo", "- + foo" → "foo"
            line = re.sub(r'^[-*+\s]+', '', line).strip()
            if not line:
                continue
            # If the bullet is itself a commit header (e.g. "fix(x): desc"),
            # extract just the description after the colon
            cm = commit_pattern.match(line)
            if cm:
                colon_pos = line.index(':')
                line = line[colon_pos + 1:].strip()
                if not line:
                    continue
            lower = line.lower()
            if any(lower.startswith(kw) for kw in skip_prefixes):
                continue
            if len(line) > 100:  # suspiciously long = explanation
                continue
            if len(line) < 8:  # too short = truncated
                continue
            line = re.sub(r'\s*\(#\d+\)\s*$', '', line)  # strip trailing (#123)
            bullets.append("- " + line)

        # Deduplicate while preserving order
        seen = set()
        unique_bullets = []
        for b in bullets:
            if b not in seen:
                seen.add(b)
                unique_bullets.append(b)

        if unique_bullets:
            return summary + "\n" + "\n".join(unique_bullets)
        return summary + "\n- implementation changes"
