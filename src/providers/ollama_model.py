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

        if not self._ensure_model_available():
            return "feat: add changes\n- unable to connect to Ollama"

        prompt = self._build_commit_prompt(context)

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

        return "feat: update repository\n- generic commit message"

    def _build_commit_prompt(self, context: Dict) -> str:
        return """You are a Git expert. Generate a commit message based on the following staged changes:

Repository Context:
- Branch: {branch}
- Files being committed: {files}

Staged Changes (git diff --cached):
{diff}

Requirements:
1. Use this EXACT format:
   feat(scope): a short summary
   - point 1
   - point 2

2. Format details:
   - Use conventional commit types: feat, fix, docs, style, refactor, test, chore
   - scope should be the module/area affected
   - summary must be under 50 characters, imperative mood
   - bullet points describe specific changes

Generate ONLY the commit message, no explanation:""".format(
            branch=context.get("branch", "main"),
            files=", ".join(context.get("staged_files", ["files"])),
            diff=context.get("diff", "No diff available")[:2000],
        )

    def _format_commit_response(self, response: str) -> str:
        """Normalise the raw model output into summary + bullet lines"""
        lines = [l.strip() for l in response.split("\n") if l.strip()]
        if not lines:
            return "feat: update repository\n- implementation changes"

        summary = lines[0].strip("`\"'")
        bullets = []
        for line in lines[1:]:
            line = line.strip("`\"'")
            if line and not line.startswith("#"):
                if not line.startswith("- "):
                    line = "- " + line
                bullets.append(line)

        if bullets:
            return summary + "\n" + "\n".join(bullets)
        return summary + "\n- implementation changes"
