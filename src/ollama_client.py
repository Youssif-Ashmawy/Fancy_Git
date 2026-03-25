#!/usr/bin/env python3
import requests
import json
from typing import List, Dict, Optional
import time


class OllamaClient:
    """Client for communicating with local Ollama model for error analysis"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self.timeout = 30
        self.max_retries = 2
        
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def analyze_error_messages(self, messages: List[Dict]) -> str:
        """
        Analyze error/warning messages using Ollama model
        
        Args:
            messages: List of dictionaries containing error/warning information
            
        Returns:
            str: Analysis and suggestions from the AI model
        """
        if not messages:
            return "No messages to analyze."
        
        # Prepare the prompt with error context
        prompt = self._build_analysis_prompt(messages)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._call_ollama(prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == self.max_retries:
                    return f"Failed to get AI analysis after {self.max_retries + 1} attempts: {str(e)}"
                time.sleep(1)  # Brief delay before retry
        
        return "Unable to get AI analysis."
    
    def _build_analysis_prompt(self, messages: List[Dict]) -> str:
        """Build the analysis prompt for the AI model"""
        prompt = """You are a Git expert assistant. Analyze the following Git error/warning messages and provide:
        1. A clear summary of what went wrong
        2. Step-by-step instructions on how to resolve the issue
        3. Any preventive measures to avoid this in the future

        Keep your response concise, practical, and focused on solutions.

        Messages to analyze:
        """
        
        for i, msg in enumerate(messages, 1):
            severity = msg.get('severity', 'unknown').upper()
            message_text = msg.get('message', str(msg))
            error_type = msg.get('type', 'Unknown')
            file_info = f" (file: {msg.get('file', 'N/A')})" if msg.get('file') else ""
            
            prompt += f"\n{i}. [{severity}] {error_type}{file_info}\n   {message_text}\n"
        
        prompt += "\n\nAnalysis:"
        return prompt
    
    def generate_commit_message(self, context: Dict) -> str:
        """
        Generate commit message based on git changes
        
        Args:
            context: Dictionary containing branch, staged_files, and diff information
            
        Returns:
            str: Suggested commit message
        """
        if not context:
            return "feat: Add new functionality"
        
        # Build commit message prompt
        prompt = self._build_commit_prompt(context)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._call_ollama(prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == self.max_retries:
                    return f"feat: Add changes to {context.get('branch', 'current')}"
                time.sleep(1)  # Brief delay before retry
        
        return "feat: Update repository"
    
    def _build_commit_prompt(self, context: Dict) -> str:
        """Build commit message generation prompt"""
        prompt = """You are a Git expert. Generate a concise, conventional commit message based on the following changes:

Repository Context:
- Branch: {branch}
- Files being committed: {files}

Changes (git diff):
{diff}

Requirements:
1. Use conventional commit format: type(scope): description
2. Types: feat, fix, docs, style, refactor, test, chore
3. Keep description under 50 characters
4. Be specific about what changed
5. Use imperative mood ("add" not "added")
6. Focus on the "why" not just "what"
7. **CRITICAL: Generate only ONE line - no multiple lines, no line breaks**

Examples:
- feat(auth): add OAuth2 login flow
- fix(api): resolve null pointer in user service
- docs(readme): update installation instructions
- style(ui): fix button alignment
- refactor(utils): simplify validation logic
- test(user): add unit tests for registration
- chore(deps): update dependencies

Generate only the commit message, no explanation, no quotes, no backticks, no formatting - just the plain text:""".format(
            branch=context.get('branch', 'main'),
            files=', '.join(context.get('staged_files', ['files'])),
            diff=context.get('diff', 'No diff available')[:1500]  # Limit for processing
        )
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Make API call to Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                # Remove any surrounding quotes/backticks from AI response
                if (response_text.startswith('"') and response_text.endswith('"')) or \
                   (response_text.startswith("'") and response_text.endswith("'")) or \
                   (response_text.startswith("`") and response_text.endswith("`")):
                    response_text = response_text[1:-1].strip()
                
                # Ensure only first line is used (in case AI generates multiple lines)
                response_text = response_text.split('\n')[0].strip()
                
                return response_text
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request to Ollama timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure it's running.")
        except json.JSONDecodeError:
            raise Exception("Invalid response from Ollama")
        except Exception as e:
            raise Exception(f"Error calling Ollama: {str(e)}")
    
    def set_model(self, model: str) -> bool:
        """Change the model being used"""
        available_models = self.get_available_models()
        if model in available_models:
            self.model = model
            return True
        return False
    
    def get_model_info(self) -> Dict:
        """Get information about current model"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except requests.exceptions.RequestException:
            return {}
