import pytest
from unittest.mock import patch, MagicMock
from src.ai_engine import AIEngine
from src.config_manager import ConfigManager
from src.providers.base_model import BaseModel
from src.providers.ollama_model import OllamaModel

@pytest.mark.unit
class TestAIEngine:
    """Test cases for AI Engine class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Create a mock config manager
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        
        # Create mock config object
        mock_config = MagicMock()
        mock_config.analysis_provider = "ollama"
        mock_config.explanation_provider = "ollama"
        mock_config.translation_provider = "ollama"
        mock_config.ollama_max_retries = 3
        
        self.mock_config_manager.config = mock_config
        
        # Mock the provider factory
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_get_model.return_value = mock_provider
            self.ai_engine = AIEngine(self.mock_config_manager)
            self.mock_provider = mock_provider
    
    def test_ai_engine_initialization(self):
        """Test AI Engine initializes with all required providers"""
        assert hasattr(self.ai_engine, 'analysis_provider')
        assert hasattr(self.ai_engine, 'explanation_provider')
        assert hasattr(self.ai_engine, 'translation_provider')
        assert hasattr(self.ai_engine, 'max_retries')
        assert self.ai_engine.max_retries == 3
    
    @patch('src.model_provider.ModelProvider.get_model')
    def test_ai_engine_provider_initialization(self, mock_get_model):
        """Test that providers are initialized correctly via factory"""
        mock_provider = MagicMock(spec=BaseModel)
        mock_get_model.return_value = mock_provider
        
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Verify ModelProvider.get_model was called for each provider type
        assert mock_get_model.call_count == 3
        mock_get_model.assert_any_call(self.mock_config_manager, "ollama")
    
    def test_analyze_error_messages_with_valid_messages(self):
        """Test analyze_error_messages with valid error messages"""
        messages = [
            {"severity": "error", "message": "File not found", "type": "FILE_ERROR", "file": "test.py"},
            {"severity": "warning", "message": "Deprecated function used", "type": "DEPRECATION_WARNING"}
        ]
        
        self.mock_provider._call_model.return_value = "Analysis response"
        
        result = self.ai_engine.analyze_error_messages(messages)
        
        assert result == "Analysis response"
        self.mock_provider._call_model.assert_called_once()
        
        # Check that the prompt contains the expected content
        call_args = self.mock_provider._call_model.call_args[0][0]
        assert "[ERROR] FILE_ERROR" in call_args
        assert "[WARNING] DEPRECATION_WARNING" in call_args
        assert "File not found" in call_args
        assert "Deprecated function used" in call_args
    
    def test_analyze_error_messages_with_empty_list(self):
        """Test analyze_error_messages with empty message list"""
        result = self.ai_engine.analyze_error_messages([])
        
        assert result == "No messages to analyze."
        self.mock_provider._call_model.assert_not_called()
    
    def test_analyze_error_messages_with_provider_error(self):
        """Test analyze_error_messages when provider raises an exception"""
        messages = [{"severity": "error", "message": "Test error"}]
        
        self.mock_provider._call_model.side_effect = Exception("Provider error")
        
        result = self.ai_engine.analyze_error_messages(messages)
        
        assert "Failed to get AI analysis: Provider error" in result
    
    def test_explain_command_with_ollama_provider(self):
        """Test explain_command with Ollama provider (model switching)"""
        mock_ollama_provider = MagicMock(spec=OllamaModel)
        mock_ollama_provider.model = "llama2"
        mock_ollama_provider.test_connection.return_value = True
        mock_ollama_provider._call_model.return_value = "Explanation response"
        
        with patch('src.model_provider.ModelProvider.get_model', return_value=mock_ollama_provider):
            ai_engine = AIEngine(self.mock_config_manager)
            result = ai_engine.explain_command("add")
        
        assert result == "Explanation response"
        
        # Verify model switching logic
        mock_ollama_provider.set_model.assert_any_call('codellama')
        mock_ollama_provider._call_model.assert_called_once()
    
    def test_explain_command_with_non_ollama_provider(self):
        """Test explain_command with non-Ollama provider (no model switching)"""
        mock_provider = MagicMock(spec=BaseModel)
        mock_provider._call_model.return_value = "Explanation response"
        
        with patch('src.model_provider.ModelProvider.get_model', return_value=mock_provider):
            ai_engine = AIEngine(self.mock_config_manager)
            result = ai_engine.explain_command("commit")
        
        assert result == "Explanation response"
        mock_provider._call_model.assert_called_once()
    
    def test_explain_command_with_provider_error(self):
        """Test explain_command when provider raises an exception"""
        self.mock_provider._call_model.side_effect = Exception("Provider error")
        
        with pytest.raises(Exception, match="Provider error"):
            self.ai_engine.explain_command("push")
    
    def test_build_analysis_prompt_structure(self):
        """Test that analysis prompt has correct structure"""
        messages = [
            {"severity": "error", "message": "Test error", "type": "TEST_ERROR", "file": "test.py"},
            {"severity": "warning", "message": "Test warning", "type": "TEST_WARNING"}
        ]
        
        self.mock_provider._call_model.return_value = "Analysis"
        
        self.ai_engine.analyze_error_messages(messages)
        
        call_args = self.mock_provider._call_model.call_args[0][0]
        
        # Check prompt structure
        assert "You are a Git expert assistant" in call_args
        assert "WHAT WENT WRONG:" in call_args
        assert "HOW TO FIX IT:" in call_args
        assert "Messages to analyze:" in call_args
        assert "Analysis:" in call_args
    
    def test_build_explain_prompt_structure(self):
        """Test that explain prompt has correct structure"""
        self.mock_provider._call_model.return_value = "Explanation"
        
        self.ai_engine.explain_command("status")
        
        call_args = self.mock_provider._call_model.call_args[0][0]
        
        # Check prompt structure
        assert "You are an expert developer" in call_args
        assert "rapid crash course on the git command: 'git status'" in call_args
        assert "💡 WHAT IT DOES:" in call_args
        assert "🎯 WHEN TO USE IT:" in call_args
        assert "🚀 HOW TO USE IT:" in call_args
        assert "[1-2 common flags and what they do]" in call_args
    
    def test_analyze_error_messages_with_missing_fields(self):
        """Test analyze_error_messages with messages missing optional fields"""
        messages = [
            {"message": "Simple error message"},  # Missing severity, type, file
            {"severity": "warning", "message": "Warning with type", "type": "WARN_TYPE"},  # Missing file
            {"severity": "error", "message": "Error with file", "file": "error.py"}  # Missing type
        ]
        
        self.mock_provider._call_model.return_value = "Analysis"
        
        result = self.ai_engine.analyze_error_messages(messages)
        
        assert result == "Analysis"
        
        # Check that the prompt handles missing fields gracefully
        call_args = self.mock_provider._call_model.call_args[0][0]
        assert "UNKNOWN" in call_args  # Missing severity should default to UNKNOWN
        assert "file: N/A" not in call_args  # Missing file should not show file info
