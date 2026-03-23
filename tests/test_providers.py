import pytest
from unittest.mock import patch, MagicMock
from src.providers.base_model import BaseModel
from src.providers.ollama_model import OllamaModel
from src.providers.openai_model import OpenAIModel
from src.providers.anthropic_model import AnthropicModel
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
class TestOllamaModel:
    """Test cases for Ollama Model class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.config.ollama_host = "http://localhost:11434"
        self.mock_config_manager.config.ollama_model = "llama2"
        self.mock_config_manager.config.ollama_timeout = 30
        
        with patch('requests.post'):
            self.ollama_model = OllamaModel(config_manager=self.mock_config_manager)
    
    def test_ollama_model_initialization(self):
        """Test Ollama model initialization"""
        assert self.ollama_model.config_manager == self.mock_config_manager
        assert self.ollama_model.model == "llama2"
        assert hasattr(self.ollama_model, 'base_url')
    
    @patch('requests.post')
    def test_test_connection_success(self, mock_post):
        """Test successful connection test"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"model": "llama2"}
        mock_post.return_value = mock_response
        
        with patch('requests.post', return_value=mock_response):
            result = self.ollama_model.test_connection()
        
        assert result is True
    
    @patch('requests.post')
    def test_test_connection_failure(self, mock_post):
        """Test failed connection test"""
        mock_post.side_effect = Exception("Connection failed")
        
        result = self.ollama_model.test_connection()
        
        assert result is False
    
    def test_get_model_info(self):
        """Test getting model information"""
        info = self.ollama_model.get_model_info()
        
        assert isinstance(info, dict)
        assert "provider" in info
        assert "model" in info
        assert info["provider"] == "ollama"
        assert info["model"] == "llama2"
    
    @patch('requests.post')
    def test_call_model_success(self, mock_post):
        """Test successful model call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Test response",
            "done": True
        }
        mock_post.return_value = mock_response
        
        result = self.ollama_model._call_model("Test prompt")
        
        assert result == "Test response"
    
    @patch('requests.post')
    def test_call_model_failure(self, mock_post):
        """Test model call failure"""
        mock_post.side_effect = Exception("API call failed")
        
        result = self.ollama_model._call_model("Test prompt")
        
        assert result is None
    
    def test_set_model(self):
        """Test setting different model"""
        result = self.ollama_model.set_model("codellama")
        
        assert result is True
        assert self.ollama_model.model == "codellama"
    
    def test_set_model_invalid(self):
        """Test setting invalid model"""
        with patch.object(self.ollama_model, 'test_connection', return_value=False):
            result = self.ollama_model.set_model("invalid_model")
        
        assert result is False
        assert self.ollama_model.model != "invalid_model"

@pytest.mark.unit
class TestOpenAIModel:
    """Test cases for OpenAI Model class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.config.openai_api_key = "test-api-key"
        self.mock_config_manager.config.openai_model = "gpt-3.5-turbo"
        self.mock_config_manager.config.openai_timeout = 30
        
        with patch('openai.OpenAI'):
            self.openai_model = OpenAIModel(config_manager=self.mock_config_manager)
    
    def test_openai_model_initialization(self):
        """Test OpenAI model initialization"""
        assert self.openai_model.config_manager == self.mock_config_manager
        assert hasattr(self.openai_model, 'client')
        assert hasattr(self.openai_model, 'model')
    
    @patch('openai.OpenAI')
    def test_test_connection_success(self, mock_openai):
        """Test successful connection test"""
        mock_client = MagicMock()
        mock_client.models.list.return_value = [{"id": "gpt-3.5-turbo"}]
        mock_openai.return_value = mock_client
        
        model = OpenAIModel(config_manager=self.mock_config_manager)
        result = model.test_connection()
        
        assert result is True
    
    @patch('openai.OpenAI')
    def test_test_connection_failure(self, mock_openai):
        """Test failed connection test"""
        mock_openai.side_effect = Exception("API key invalid")
        
        with pytest.raises(Exception):
            OpenAIModel(config_manager=self.mock_config_manager)
    
    def test_get_model_info(self):
        """Test getting model information"""
        info = self.openai_model.get_model_info()
        
        assert isinstance(info, dict)
        assert "provider" in info
        assert "model" in info
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-3.5-turbo"
    
    @patch('openai.OpenAI')
    def test_call_model_success(self, mock_openai):
        """Test successful model call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        model = OpenAIModel(config_manager=self.mock_config_manager)
        result = model._call_model("Test prompt")
        
        assert result == "Test response"
    
    @patch('openai.OpenAI')
    def test_call_model_failure(self, mock_openai):
        """Test model call failure"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API call failed")
        mock_openai.return_value = mock_client
        
        model = OpenAIModel(config_manager=self.mock_config_manager)
        result = model._call_model("Test prompt")
        
        assert result is None

@pytest.mark.unit
class TestAnthropicModel:
    """Test cases for Anthropic Model class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.config.anthropic_api_key = "test-api-key"
        self.mock_config_manager.config.anthropic_model = "claude-3-sonnet-20240229"
        self.mock_config_manager.config.anthropic_timeout = 30
        
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
class TestProviderIntegration:
    """Integration tests for provider system"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
    
    @patch('src.providers.ollama_model.OllamaModel')
    @patch('src.providers.openai_model.OpenAIModel')
    @patch('src.providers.anthropic_model.AnthropicModel')
    def test_provider_factory_integration(self, mock_anthropic, mock_openai, mock_ollama):
        """Test that provider factory creates correct instances"""
        from src.model_provider import ModelProvider
        
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_openai_instance = MagicMock(spec=BaseModel)
        mock_anthropic_instance = MagicMock(spec=BaseModel)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_openai.return_value = mock_openai_instance
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Test all providers
        ollama = ModelProvider.get_model(self.mock_config_manager, "ollama")
        openai = ModelProvider.get_model(self.mock_config_manager, "openai")
        anthropic = ModelProvider.get_model(self.mock_config_manager, "anthropic")
        
        assert isinstance(ollama, BaseModel)
        assert isinstance(openai, BaseModel)
        assert isinstance(anthropic, BaseModel)
    
    def test_all_providers_implement_base_model(self):
        """Test that all providers implement BaseModel interface"""
        # This is a design test - verifies that all providers have the required methods
        required_methods = ['test_connection', 'get_model_info', '_call_model']
        
        for provider_class in [OllamaModel, OpenAIModel, AnthropicModel]:
            for method in required_methods:
                assert hasattr(provider_class, method), f"{provider_class.__name__} missing {method}"
