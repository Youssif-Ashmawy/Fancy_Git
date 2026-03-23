from src.config_manager import ConfigManager
from src.providers.base_model import BaseModel
from typing import Optional

class ModelProvider:        # implements factory pattern to return appropriate model instance based on config
    @staticmethod
    def get_model(config_manager: Optional[ConfigManager] = None, model_name: str = "ollama") -> BaseModel:
        """Provider factory pattern to return appropriate model instance based on model name
        available models up till now are {"ollama", "openai", "anthropic"}"""
        # model_name = config_manager.config.model_provider.lower()
        model_name = model_name.lower()
        if model_name == "ollama":
            from src.providers.ollama_model import OllamaModel
            return OllamaModel(config_manager=config_manager)
        
        elif model_name == "openai":
            from src.providers.openai_model import OpenAIModel
            return OpenAIModel(config_manager=config_manager)
        
        elif model_name == "anthropic":
            from src.providers.anthropic_model import AnthropicModel
            return AnthropicModel(config_manager=config_manager)
        
        else:
            raise ValueError(f"Unsupported model provider: {model_name}. Please check your .fancygit_config and ensure the model_provider is set to 'ollama', 'openai', or 'anthropic'.")