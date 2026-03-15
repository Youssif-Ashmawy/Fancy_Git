#!/usr/bin/env python3
from base_model import BaseProvider
import requests
import json
from typing import List, Dict, Optional
import time

from src.config_manager import ConfigManager


class OllamaProvider(BaseProvider):
    """Provider for the Ollama AI model"""
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        # use the provided config manager or create a new one if not provided and load configuration values using load() 
        # (which is already done in constructor)
        self.config_manager = config_manager or ConfigManager()
        # load configuration values from config manager
        self.base_url = self.config_manager.config.ollama_api_url
        self.model = self.config_manager.config.default_ollama_model
        self.timeout = self.config_manager.config.ollama_timeout
        self.max_retries = self.config_manager.config.ollama_max_retries
        
        
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
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

    def _call_model(self, prompt: str) -> Optional[str]:
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
                return result.get('response', '').strip()
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
        # Handle cases like 'codellama' checking against 'codellama:latest'
        for available_model in available_models:
            if available_model == model or available_model.startswith(f"{model}:"):
                self.model = available_model
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

    def _build_explain_prompt(self, command: str) -> str:
        """Builds a concise crash course prompt tailored for codellama."""
        return f"""
        You are an expert developer. Provide a rapid crash course on the git command: '{command}'.
        You MUST format your ONLY response exactly like the template below. Do not add any conversational text before or after the template. Do not change the emojis or header names.

        💡 WHAT IT DOES:
        [1-2 sentences explaining the core purpose of {command}]

        🎯 WHEN TO USE IT:
        [A brief real-world scenario where you would use {command}]

        🚀 HOW TO USE IT:
        [The exact command(s) with placeholders]

        [1-2 common flags and what they do]
        """

