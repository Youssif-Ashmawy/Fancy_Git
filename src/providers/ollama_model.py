#!/usr/bin/env python3
from .base_model import BaseModel
import requests
import json
from typing import List, Dict, Optional
import time

from src.config_manager import ConfigManager

class OllamaClient:
    """Client for communicating with local AI models for error analysis and commit generation"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        self.base_url = base_url
        self.preferred_model = model
        self.model = model
        self.timeout = 30
        self.max_retries = 2
        self.fallback_models = ["llama3.2", "llama3", "mistral"]  # Fallback options
        
    def test_connection(self) -> bool:
        """Test if AI service is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _ensure_model_available(self) -> bool:
        """Ensure we have a working model, try fallbacks if needed"""
        available_models = self.get_available_models()
        
        # Try preferred model first (handle version tags)
        for model in available_models:
            if model.startswith(self.preferred_model):
                self.model = model
                return True
        
        # Try fallback models (handle version tags)
        for fallback_model in self.fallback_models:
            for model in available_models:
                if model.startswith(fallback_model):
                    self.model = model
                    return True
        
        return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
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
                    # Post-process to ensure clean format
                    return self._clean_ai_response(response)
            except Exception as e:
                if attempt == self.max_retries:
                    return f"Failed to get AI analysis after {self.max_retries + 1} attempts: {str(e)}"
                time.sleep(1)  # Brief delay before retry
        
        return "Unable to get AI analysis."
    
    def _build_analysis_prompt(self, messages: List[Dict]) -> str:
        """Build the analysis prompt for the AI model"""
        prompt = """You are a Git expert. Provide ONLY this exact format:

PROBLEM: [1 line description]
SOLUTION: [1-2 line fix]

No extra text, no explanations, no numbered lists.

Messages:
        """
        
        for i, msg in enumerate(messages, 1):
            severity = msg.get('severity', 'unknown').upper()
            message_text = msg.get('message', str(msg))
            error_type = msg.get('type', 'Unknown')
            file_info = f" (file: {msg.get('file', 'N/A')})" if msg.get('file') else ""
            
            prompt += f"\n{i}. [{severity}] {error_type}{file_info}\n   {message_text}\n"
        
        prompt += "\n\nAnalysis:"
        return prompt
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean and format AI response to ensure consistent output"""
        lines = response.strip().split('\n')
        problem = ""
        solution = ""
        
        for line in lines:
            line = line.strip()
            # Remove common prefixes
            clean_line = line
            if clean_line.lower().startswith('problem:'):
                clean_line = clean_line.replace('Problem:', '').replace('PROBLEM:', '').strip()
                problem = clean_line
            elif clean_line.lower().startswith('solution:'):
                clean_line = clean_line.replace('Solution:', '').replace('SOLUTION:', '').strip()
                solution = clean_line
            elif clean_line.startswith('-') or clean_line.startswith('•'):
                clean_line = clean_line.lstrip('-• ').strip()
                if not solution:
                    solution = clean_line
            elif not problem and ('error' in clean_line.lower() or 'issue' in clean_line.lower() or 'fatal' in clean_line.lower()):
                problem = clean_line
            elif not solution and ('fix' in clean_line.lower() or 'run' in clean_line.lower() or 'use' in clean_line.lower() or 'make' in clean_line.lower()):
                solution = clean_line
        
        # Fallback if no structured format found
        if not problem or not solution:
            # Try to extract from unstructured response
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('-') and not line.startswith('•') and not line.startswith('1.') and not line.startswith('2.'):
                    if not problem:
                        problem = line[:100] + '...' if len(line) > 100 else line
                    elif not solution:
                        solution = line[:100] + '...' if len(line) > 100 else line
                        break
        
        # Clean up any remaining formatting issues
        if solution:
            solution = solution.replace('SOLUTION:', '').replace('solution:', '').strip()
            solution = solution.lstrip('-• ').strip()
        
        # Format final output
        if problem and solution:
            return f"PROBLEM: {problem}\n\nSOLUTION: {solution}"
        elif problem:
            return f"PROBLEM: {problem}\n\nSOLUTION: Check the error and try the suggested fix."
        else:
            return response[:200]  # Fallback to truncated response
    
    def generate_commit_message(self, context: Dict) -> str:
        """
        Generate commit message based on git changes using new format
        
        Args:
            context: Dictionary containing branch, staged_files, and diff information
            
        Returns:
            str: Suggested commit message in feat(scope): summary format with bullet points
        """
        if not context:
            return "feat: Add new functionality\n- Initial implementation"
        
        # Ensure we have a working model
        if not self._ensure_model_available():
            return "feat: Add changes\n- Unable to connect to AI service"
        
        # Build commit message prompt
        prompt = self._build_commit_prompt(context)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._call_ollama(prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == self.max_retries:
                    return f"feat: Add changes to {context.get('branch', 'current')}\n- Fallback due to AI error: {str(e)[:50]}"
                time.sleep(1)  # Brief delay before retry
        
        return "feat: Update repository\n- Generic commit message"
    
    def _build_commit_prompt(self, context: Dict) -> str:
        """Build commit message generation prompt with new format requirements"""
        prompt = """You are a Git expert. Generate a commit message based on the following staged changes:

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
   - point 3
   (add more bullet points as needed)

2. Format details:
   - Use conventional commit types: feat, fix, docs, style, refactor, test, chore
   - scope should be the module/area affected (e.g., auth, api, ui, utils)
   - summary must be under 50 characters, imperative mood
   - bullet points should describe specific changes made
   - each bullet point starts with '- '
   - be specific about what changed and why

3. Content guidelines:
   - Focus on staged changes only
   - Include file summary in bullet points when relevant
   - Be concise but descriptive
   - Use technical language appropriate for developers

Examples:
feat(auth): add OAuth2 login flow
- implement OAuth2 provider integration
- add login form with validation
- update session management
- add user profile endpoint

fix(api): resolve null pointer in user service
- add null check for user object
- update error handling in service layer
- add unit tests for edge cases

Generate ONLY the commit message in the specified format, no explanation:""".format(
            branch=context.get('branch', 'main'),
            files=', '.join(context.get('staged_files', ['files'])),
            diff=context.get('diff', 'No diff available')[:2000]  # Limit for processing
        )
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Make API call to AI service"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 200  # Reduced for shorter responses
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
                   (response_text.startswith('`') and response_text.endswith('`')):
                    response_text = response_text[1:-1].strip()
                
                # For new format, keep the full multi-line response
                # But ensure it follows our expected format
                response_text = response_text.replace('``', '').strip()  # Remove any double backticks
                
                lines = response_text.split('\n')
                # Clean up each line
                lines = [line.strip() for line in lines if line.strip()]
                
                if len(lines) >= 1:
                    # First line should be the summary
                    summary_line = lines[0]
                    # Remove any surrounding formatting
                    summary_line = summary_line.strip('`"\'')
                    
                    bullet_lines = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line and not line.startswith('#'):  # Skip comment lines
                            # Remove any surrounding formatting
                            line = line.strip('`"\'')
                            if not line.startswith('- '):
                                line = '- ' + line  # Ensure bullet format
                            bullet_lines.append(line)
                    
                    if bullet_lines:
                        response_text = summary_line + '\n' + '\n'.join(bullet_lines)
                    else:
                        response_text = summary_line + '\n- Implementation changes'
                else:
                    # If no valid content, create a default
                    response_text = "feat: Update repository\n- Implementation changes"
                
                return response_text
            else:
                raise Exception(f"AI API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            raise Exception("Request to AI service timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to AI service. Make sure it's running.")
        except json.JSONDecodeError:
            raise Exception("Invalid response from AI service")
        except Exception as e:
            raise Exception(f"Error calling AI service: {str(e)}")
    


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
    
    def set_model(self, model: str) -> bool:
        """Change the model being used"""
        available_models = self.get_available_models()
        if model in available_models:
            self.preferred_model = model
            self.model = model
            return True
        return False

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
                response = self._call_model(prompt)
                if response:
                    return response
            except Exception as e:
                if attempt == self.max_retries:
                    return f"Failed to get AI analysis after {self.max_retries + 1} attempts: {str(e)}"
                time.sleep(1)  # Brief delay before retry
        
        return "Unable to get AI analysis."
    
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
    
    def get_current_model(self) -> str:
        """Get the currently active model name"""
        return self.model
