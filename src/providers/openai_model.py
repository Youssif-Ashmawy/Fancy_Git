import openai
from openai import AuthenticationError
from .base_model import BaseModel
from src.config_manager import ConfigManager
from typing import Optional, Dict
import requests


class OpenAIModel(BaseModel):
    """Provider for the OpenAI API"""
    def __init__(self, config_manager : Optional[ConfigManager] = None):

        self.config_manager = config_manager or ConfigManager()

        self.base_url = self.config_manager.config.open_ai_api_base
        self.api_key = self.config_manager.config.openai_api_key

    def test_connection(self) -> bool:
        """Test if OpenAI API is accessible and working"""
        try:
            # Attempt to list models to verify connection and authentication
            # Fortunately the OpenAI Python client library provides a way to list models
            # this will not waste tokens and is a good way to verify that the API key is valid and the API is reachable
            response = openai.models.list()
            return True
        except AuthenticationError:
            print("Authentication failed. Please check your OpenAI API key.")
            return False
        except Exception as e:
            print(f"Error connecting to OpenAI API: {e}")
            return False
        
    def get_model_info(self) -> Dict:
        """Get information about current model"""
        try:
            response = openai.models.retrieve(self.config_manager.config.default_openai_model)
            return dict(response)
        except AuthenticationError:
            print("Authentication failed: check your OpenAI API key")
            return {}
        except Exception as e:
            print(f"Error retrieving model info: {e}")
            return {}
        
    def _call_model(self, prompt: str) -> Optional[str]:
        """Make API call to OpenAI"""
        try:
            response = openai.completions.create(
                model=self.config_manager.config.default_openai_model,
                prompt=prompt,
                max_tokens=self.config_manager.config.openai_max_tokens_to_sample,
                temperature=self.config_manager.config.openai_temperature,
                top_p=0.9
            )
            return response.choices[0].text.strip() if response.choices else None   # Extract the generated text from the response
        except AuthenticationError:
            print("Authentication failed: check your OpenAI API key")
            return None
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None