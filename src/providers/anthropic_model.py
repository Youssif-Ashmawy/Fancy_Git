from anthropic import Anthropic
from src.config_manager import ConfigManager
from base_model import BaseModel
from typing import Optional, Dict
import requests

class AnthropicModel(BaseModel):
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()

        self.api_key = self.config_manager.config.anthropic_api_key
        self.base_url = self.config_manager.config.anthropic_api_base
        self.max_tokens_timeout = self.config_manager.config.anthropic_max_tokens_timeout

    def test_connection(self) -> bool:
        try:
            # Unfortunately for Anthropic there is no simple endpoint to test the connection without making a full API call
            # so we will just attempt to make a simple API call with an empty prompt to verify the connection and authentication
            client = Anthropic(api_key=self.api_key, base_url=self.base_url)
            response = client.completions.create(model="claude-2", prompt="Test connection", max_tokens_to_sample=self.max_tokens_timeout)
            return True if response else False
        except Exception as e:
            print(f"Error connecting to Anthropic API: {e}")
            return False
        
    def get_model_info(self) -> Dict:
        return {
            "model": self.config_manager.config.default_anthropic_model,
            "base_url": self.base_url,
            "max_tokens": 9000 if self.config_manager.config.default_anthropic_model == "claude-2" else 1000
        }
    
    def _call_model(self, prompt: str) -> Optional[str]:
        try:
            client = Anthropic(api_key=self.api_key, base_url=self.base_url)
            response = client.completions.create(       # returns a dataclass with a 'completion' field that contains the generated text
                model=self.config_manager.config.default_anthropic_model,
                prompt=prompt,
                max_tokens_to_sample=500,
                temperature=0.3,
                top_p=0.9
            )
            return response.completion if response else None
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return None
        