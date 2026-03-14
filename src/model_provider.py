from src.config_manager import ConfigManager


class ModelProvider:        # implements factory pattern to return appropriate model instance based on config
    @staticmethod
    def get_model(config_manager: ConfigManager) -> object:
        """Provider factory pattern to return appropriate model instance based on model name"""
        model_name = config_manager.config.model_provider.lower()

        if model_name == "ollama":
            from src.providers.ollama_model import OllamaClient
            return OllamaClient(config_manager.config.default_ollama_model)
        
        elif model_name == "openai":
            from src.providers.openai_model import OpenAIModel
            return OpenAIModel(config_manager=config_manager)
        
        elif model_name == "anthropic":
            from src.providers.anthropic_model import AnthropicModel
            return AnthropicModel(config_manager=config_manager)
        
        else:
            raise ValueError(f"Unsupported model provider: {model_name}. Please check your .fancygit_config and ensure the model_provider is set to 'ollama', 'openai', or 'anthropic'.")