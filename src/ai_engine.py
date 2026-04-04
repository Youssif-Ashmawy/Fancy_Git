from src.providers.base_model import BaseModel
from src.model_provider import ModelProvider
from src.providers.ollama_model import OllamaModel
from src.config_manager import ConfigManager
from typing import List, Dict, Optional
import time

class AIEngine:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
        # Initialize providers based on config
        self.analysis_provider = ModelProvider.get_model(
            config_manager, config_manager.config.analysis_provider
        )
        self.explanation_provider = ModelProvider.get_model(
            config_manager, config_manager.config.explanation_provider
        )
        self.translation_provider = ModelProvider.get_model(
            config_manager, config_manager.config.translation_provider
        )
        
        self.max_retries = config_manager.config.ollama_max_retries

    def analyze_error_messages(self, messages: List[Dict]) -> str:
        """
        Analyze error/warning messages using the configured analysis provider
        """
        if not messages:
            return "No messages to analyze."
        
        # Prepare the prompt with error context
        prompt = self._build_analysis_prompt(messages)

        # Resolve the exact model name before calling (handles version tags)
        if hasattr(self.analysis_provider, '_ensure_model_available'):
            self.analysis_provider._ensure_model_available()

        try:
            response = self.analysis_provider._call_model(prompt)
            return response if response else "Unable to get AI analysis."
        except Exception as e:
            return f"Failed to get AI analysis: {str(e)}"

    def explain_command(self, command: str) -> Optional[str]:
        """
        Explain a git command using the configured explanation provider.
        If using Ollama, automatically attempts to switch to codellama.
        """
        previous_model = None
        ollama_provider: Optional[OllamaModel] = None
        
        if isinstance(self.explanation_provider, OllamaModel):
            ollama_provider = self.explanation_provider
            previous_model = ollama_provider.model
            if not ollama_provider.set_model('codellama'):
                # We continue even if switch fails, just with less accuracy
                pass
            else:
                print(f"Switched to `{ollama_provider.model}` for better explanations")

        prompt = self._build_explain_prompt(command)
        
        try:
            response = self.explanation_provider._call_model(prompt)
            
            # Restore previous model if we switched
            if ollama_provider and previous_model:
                ollama_provider.set_model(previous_model)
                
            return response
        except Exception as e:
            if ollama_provider and previous_model:
                ollama_provider.set_model(previous_model)
            raise e

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
        You are an expert developer. Provide a rapid crash course on the git command: 'git {command}'.
        You MUST format your ONLY response exactly like the template below. Do not add any conversational text before or after the template. Do not change the emojis or header names.

        💡 WHAT IT DOES:
        [1-2 sentences explaining the core purpose of {command}]

        🎯 WHEN TO USE IT:
        [A brief real-world scenario where you would use {command}]

        🚀 HOW TO USE IT:
        [The exact command(s) with placeholders]

        [1-2 common flags and what they do]
        """
