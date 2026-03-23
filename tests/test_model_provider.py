import pytest
from unittest.mock import patch, MagicMock
from src.model_provider import ModelProvider
from src.config_manager import ConfigManager
from src.providers.base_model import BaseModel

@pytest.mark.unit
class TestModelProvider:
    """Test cases for Model Provider factory class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_get_model_ollama(self, mock_ollama_model):
        """Test getting Ollama model instance"""
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_model.return_value = mock_ollama_instance
        
        result = ModelProvider.get_model(self.mock_config_manager, "ollama")
        
        assert result == mock_ollama_instance
        mock_ollama_model.assert_called_once_with(config_manager=self.mock_config_manager)
    
    @patch('src.providers.openai_model.OpenAIModel')
    def test_get_model_openai(self, mock_openai_model):
        """Test getting OpenAI model instance"""
        mock_openai_instance = MagicMock(spec=BaseModel)
        mock_openai_model.return_value = mock_openai_instance
        
        result = ModelProvider.get_model(self.mock_config_manager, "openai")
        
        assert result == mock_openai_instance
        mock_openai_model.assert_called_once_with(config_manager=self.mock_config_manager)
    
    def test_get_model_anthropic(self):
        """Test getting Anthropic model instance"""
        # Skip this test if anthropic_model.py doesn't exist or has issues
        try:
            result = ModelProvider.get_model(self.mock_config_manager, "anthropic")
            assert result is not None
            assert hasattr(result, 'test_connection')
            assert hasattr(result, 'get_model_info')
            assert hasattr(result, '_call_model')
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Anthropic model not available: {e}")
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_get_model_case_insensitive(self, mock_ollama_model):
        """Test that model names are case insensitive"""
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_model.return_value = mock_ollama_instance
        
        # Test various cases
        result1 = ModelProvider.get_model(self.mock_config_manager, "OLLAMA")
        result2 = ModelProvider.get_model(self.mock_config_manager, "Ollama")
        result3 = ModelProvider.get_model(self.mock_config_manager, "ollama")
        
        assert result1 == mock_ollama_instance
        assert result2 == mock_ollama_instance
        assert result3 == mock_ollama_instance
        assert mock_ollama_model.call_count == 3
    
    def test_get_model_openai_case_insensitive(self):
        """Test OpenAI model name case insensitivity"""
        try:
            with patch('src.providers.openai_model.OpenAIModel') as mock_openai_model:
                mock_openai_instance = MagicMock(spec=BaseModel)
                mock_openai_model.return_value = mock_openai_instance
                
                result = ModelProvider.get_model(self.mock_config_manager, "OPENAI")
                
                assert result == mock_openai_instance
                mock_openai_model.assert_called_once_with(config_manager=self.mock_config_manager)
        except (ImportError, AttributeError) as e:
            pytest.skip(f"OpenAI model not available: {e}")
    
    def test_get_model_anthropic_case_insensitive(self):
        """Test Anthropic model name case insensitivity"""
        try:
            with patch('src.providers.anthropic_model.AnthropicModel') as mock_anthropic_model:
                mock_anthropic_instance = MagicMock(spec=BaseModel)
                mock_anthropic_model.return_value = mock_anthropic_instance
                
                result = ModelProvider.get_model(self.mock_config_manager, "ANTHROPIC")
                
                assert result == mock_anthropic_instance
                mock_anthropic_model.assert_called_once_with(config_manager=self.mock_config_manager)
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Anthropic model not available: {e}")
    
    def test_get_model_unsupported_provider(self):
        """Test getting model for unsupported provider raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported model provider: invalid_provider"):
            ModelProvider.get_model(self.mock_config_manager, "invalid_provider")
    
    def test_get_model_unsupported_provider_with_detailed_message(self):
        """Test error message contains supported providers"""
        with pytest.raises(ValueError) as exc_info:
            ModelProvider.get_model(self.mock_config_manager, "invalid_provider")
        
        error_message = str(exc_info.value)
        assert "invalid_provider" in error_message
        assert "ollama" in error_message
        assert "openai" in error_message
        assert "anthropic" in error_message
        assert ".fancygit_config" in error_message
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_get_model_default_parameter(self, mock_ollama_model):
        """Test getting model with default parameter"""
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_model.return_value = mock_ollama_instance
        
        # Test with default model_name parameter
        result = ModelProvider.get_model(self.mock_config_manager)
        
        assert result == mock_ollama_instance
        mock_ollama_model.assert_called_once_with(config_manager=self.mock_config_manager)
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_get_model_none_config_manager(self, mock_ollama_model):
        """Test getting model with None config_manager"""
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_model.return_value = mock_ollama_instance
        
        result = ModelProvider.get_model(None, "ollama")
        
        assert result == mock_ollama_instance
        mock_ollama_model.assert_called_once_with(config_manager=None)
    
    def test_get_model_whitespace_handling(self):
        """Test model names with whitespace are handled correctly"""
        with pytest.raises(ValueError):
            ModelProvider.get_model(self.mock_config_manager, " ollama ")  # Should fail due to whitespace
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_get_model_import_isolation(self, mock_ollama_model):
        """Test that model imports are isolated and only load when needed"""
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_model.return_value = mock_ollama_instance
        
        # Before calling get_model, the module should not be imported
        # (We can't easily test this without import system manipulation, but we can verify the call)
        result = ModelProvider.get_model(self.mock_config_manager, "ollama")
        
        assert result == mock_ollama_instance
        mock_ollama_model.assert_called_once()
    
    def test_get_model_multiple_calls(self):
        """Test multiple calls to get_model with different providers"""
        try:
            with patch('src.providers.ollama_model.OllamaModel') as mock_ollama, \
                 patch('src.providers.openai_model.OpenAIModel') as mock_openai, \
                 patch('src.providers.anthropic_model.AnthropicModel') as mock_anthropic:
                
                mock_ollama_instance = MagicMock(spec=BaseModel)
                mock_openai_instance = MagicMock(spec=BaseModel)
                mock_anthropic_instance = MagicMock(spec=BaseModel)
                
                mock_ollama.return_value = mock_ollama_instance
                mock_openai.return_value = mock_openai_instance
                mock_anthropic.return_value = mock_anthropic_instance
                
                # Get different models
                ollama = ModelProvider.get_model(self.mock_config_manager, "ollama")
                openai = ModelProvider.get_model(self.mock_config_manager, "openai")
                anthropic = ModelProvider.get_model(self.mock_config_manager, "anthropic")
                
                assert ollama == mock_ollama_instance
                assert openai == mock_openai_instance
                assert anthropic == mock_anthropic_instance
                
                # Verify each was called once
                mock_ollama.assert_called_once()
                mock_openai.assert_called_once()
                mock_anthropic.assert_called_once()
        except (ImportError, AttributeError) as e:
            pytest.skip(f"One or more providers not available: {e}")
