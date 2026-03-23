import pytest
from unittest.mock import patch, MagicMock
from src.providers.base_model import BaseModel

# Try to import provider modules, but handle missing dependencies gracefully
try:
    from src.providers.anthropic_model import AnthropicModel
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AnthropicModel = None

from src.config_manager import ConfigManager

@pytest.mark.unit
class TestBaseModel:
    """Test cases for BaseModel abstract class"""
    
    def test_base_model_is_abstract(self):
        """Test that BaseModel cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseModel()
    
    def test_base_model_has_abstract_methods(self):
        """Test that BaseModel defines required abstract methods"""
        assert hasattr(BaseModel, 'test_connection')
        assert hasattr(BaseModel, 'get_model_info')
        assert hasattr(BaseModel, '_call_model')
        
        # Verify they are abstract
        assert getattr(BaseModel.test_connection, '__isabstractmethod__', False)
        assert getattr(BaseModel.get_model_info, '__isabstractmethod__', False)
        assert getattr(BaseModel._call_model, '__isabstractmethod__', False)

@pytest.mark.unit
@pytest.mark.skipif(not ANTHROPIC_AVAILABLE, reason="Anthropic dependencies not available")
class TestAnthropicModel:
    """Test cases for Anthropic Model class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        
        # Create mock config object
        mock_config = MagicMock()
        mock_config.anthropic_api_key = "test-api-key"
        mock_config.anthropic_model = "claude-3-sonnet-20240229"
        mock_config.anthropic_timeout = 30
        
        self.mock_config_manager.config = mock_config
        
        with patch('anthropic.Anthropic'):
            self.anthropic_model = AnthropicModel(config_manager=self.mock_config_manager)
    
    def test_anthropic_model_initialization(self):
        """Test Anthropic model initialization"""
        assert self.anthropic_model.config_manager == self.mock_config_manager
        assert hasattr(self.anthropic_model, 'client')
        assert hasattr(self.anthropic_model, 'model')
    
    @patch('anthropic.Anthropic')
    def test_test_connection_success(self, mock_anthropic):
        """Test successful connection test"""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = {"id": "msg_test"}
        mock_anthropic.return_value = mock_client
        
        model = AnthropicModel(config_manager=self.mock_config_manager)
        result = model.test_connection()
        
        assert result is True
    
    @patch('anthropic.Anthropic')
    def test_test_connection_failure(self, mock_anthropic):
        """Test failed connection test"""
        mock_anthropic.side_effect = Exception("API key invalid")
        
        with pytest.raises(Exception):
            AnthropicModel(config_manager=self.mock_config_manager)
    
    def test_get_model_info(self):
        """Test getting model information"""
        info = self.anthropic_model.get_model_info()
        
        assert isinstance(info, dict)
        assert "provider" in info
        assert "model" in info
        assert info["provider"] == "anthropic"
        assert info["model"] == "claude-3-sonnet-20240229"
    
    @patch('anthropic.Anthropic')
    def test_call_model_success(self, mock_anthropic):
        """Test successful model call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content[0].text = "Test response"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        model = AnthropicModel(config_manager=self.mock_config_manager)
        result = model._call_model("Test prompt")
        
        assert result == "Test response"
    
    @patch('anthropic.Anthropic')
    def test_call_model_failure(self, mock_anthropic):
        """Test model call failure"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API call failed")
        mock_anthropic.return_value = mock_client
        
        model = AnthropicModel(config_manager=self.mock_config_manager)
        result = model._call_model("Test prompt")
        
        assert result is None

@pytest.mark.unit
@pytest.mark.skipif(not ANTHROPIC_AVAILABLE, reason="Anthropic dependencies not available")
class TestProviderIntegration:
    """Integration tests for provider system"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
    
    @patch('src.providers.anthropic_model.AnthropicModel')
    def test_provider_factory_integration(self, mock_anthropic):
        """Test that provider factory creates correct instances"""
        from src.model_provider import ModelProvider
        
        mock_anthropic_instance = MagicMock(spec=BaseModel)
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Test available providers
        anthropic = ModelProvider.get_model(self.mock_config_manager, "anthropic")
        
        assert isinstance(anthropic, BaseModel)
    
    def test_all_providers_implement_base_model(self):
        """Test that all providers implement BaseModel interface"""
        # This is a design test - verifies that all providers have the required methods
        required_methods = ['test_connection', 'get_model_info', '_call_model']
        
        available_providers = []
        if ANTHROPIC_AVAILABLE:
            available_providers.append(AnthropicModel)
        
        # Skip test if no providers are available
        if not available_providers:
            pytest.skip("No provider dependencies available")
        
        for provider_class in available_providers:
            for method in required_methods:
                assert hasattr(provider_class, method), f"{provider_class.__name__} missing {method}"
