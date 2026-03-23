import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ai_engine import AIEngine
from src.config_manager import ConfigManager
from src.model_provider import ModelProvider
from src.providers.base_model import BaseModel

@pytest.mark.integration
class TestAIIntegration:
    """Integration tests for AI architecture components"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Create a mock config manager with realistic settings
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.config.analysis_provider = "ollama"
        self.mock_config_manager.config.explanation_provider = "openai"
        self.mock_config_manager.config.translation_provider = "anthropic"
        self.mock_config_manager.config.ai_analysis_enabled = True
        self.mock_config_manager.config.ollama_max_retries = 3
        self.mock_config_manager.config.ollama_host = "http://localhost:11434"
        self.mock_config_manager.config.ollama_model = "llama2"
        self.mock_config_manager.config.openai_api_key = "test-key"
        self.mock_config_manager.config.openai_model = "gpt-3.5-turbo"
        self.mock_config_manager.config.anthropic_api_key = "test-key"
        self.mock_config_manager.config.anthropic_model = "claude-3-sonnet-20240229"
    
    @patch('src.providers.ollama_model.OllamaModel')
    @patch('src.providers.openai_model.OpenAIModel')
    @patch('src.providers.anthropic_model.AnthropicModel')
    def test_ai_engine_with_different_providers(self, mock_anthropic, mock_openai, mock_ollama):
        """Test AI Engine initialization with different providers for different tasks"""
        # Setup mock providers
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_instance.test_connection.return_value = True
        mock_ollama_instance._call_model.return_value = "Ollama analysis response"
        
        mock_openai_instance = MagicMock(spec=BaseModel)
        mock_openai_instance.test_connection.return_value = True
        mock_openai_instance._call_model.return_value = "OpenAI explanation response"
        
        mock_anthropic_instance = MagicMock(spec=BaseModel)
        mock_anthropic_instance.test_connection.return_value = True
        mock_anthropic_instance._call_model.return_value = "Anthropic translation response"
        
        mock_ollama.return_value = mock_ollama_instance
        mock_openai.return_value = mock_openai_instance
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Create AI Engine
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Test that different providers are used for different tasks
        messages = [{"severity": "error", "message": "Test error"}]
        analysis_result = ai_engine.analyze_error_messages(messages)
        assert analysis_result == "Ollama analysis response"
        
        explanation_result = ai_engine.explain_command("add")
        assert explanation_result == "OpenAI explanation response"
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_ai_engine_provider_failure_handling(self, mock_ollama):
        """Test AI Engine behavior when providers fail"""
        # Setup mock provider that fails
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_instance.test_connection.return_value = False
        mock_ollama_instance._call_model.side_effect = Exception("Provider unavailable")
        mock_ollama.return_value = mock_ollama_instance
        
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Test error analysis with failing provider
        messages = [{"severity": "error", "message": "Test error"}]
        result = ai_engine.analyze_error_messages(messages)
        assert "Failed to get AI analysis" in result
        
        # Test command explanation with failing provider
        with pytest.raises(Exception):
            ai_engine.explain_command("commit")
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_ai_engine_model_switching_workflow(self, mock_ollama):
        """Test AI Engine model switching workflow for Ollama"""
        # Setup mock Ollama provider
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_instance.model = "llama2"
        mock_ollama_instance.test_connection.return_value = True
        mock_ollama_instance._call_model.return_value = "Code explanation"
        mock_ollama_instance.set_model.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        # Configure to use Ollama for explanations
        self.mock_config_manager.config.explanation_provider = "ollama"
        
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Test command explanation (should trigger model switching)
        result = ai_engine.explain_command("status")
        assert result == "Code explanation"
        
        # Verify model switching was attempted
        mock_ollama_instance.set_model.assert_called_with('codellama')
    
    @patch('src.model_provider.ModelProvider.get_model')
    def test_model_provider_factory_integration(self, mock_get_model):
        """Test ModelProvider factory integration with AI Engine"""
        # Setup mock provider
        mock_provider = MagicMock(spec=BaseModel)
        mock_provider.test_connection.return_value = True
        mock_provider._call_model.return_value = "Test response"
        mock_get_model.return_value = mock_provider
        
        # Test that AI Engine uses ModelProvider factory
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Verify ModelProvider.get_model was called for each provider
        assert mock_get_model.call_count == 3
        
        # Test that the factory was called with correct parameters
        calls = mock_get_model.call_args_list
        assert all(call[0][0] == self.mock_config_manager for call in calls)
        assert any(call[0][1] in ["ollama", "openai", "anthropic"] for call in calls)
    
    def test_config_manager_integration_with_ai_engine(self):
        """Test ConfigManager integration with AI Engine"""
        # Create a real config manager with temporary config
        import tempfile
        from pathlib import Path
        
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / ".fancygit_config"
        
        try:
            # Create config file
            config_content = """analysis_provider=ollama
explanation_provider=openai
translation_provider=anthropic
ai_analysis_enabled=true
ollama_max_retries=5
"""
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            # Create real config manager
            config_manager = ConfigManager(config_path=config_path)
            
            # Verify config values
            assert config_manager.config.analysis_provider == "ollama"
            assert config_manager.config.explanation_provider == "openai"
            assert config_manager.config.translation_provider == "anthropic"
            assert config_manager.config.ai_analysis_enabled == True
            assert config_manager.config.ollama_max_retries == 5
            
            # Test with mocked providers
            with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
                mock_provider = MagicMock(spec=BaseModel)
                mock_provider._call_model.return_value = "Test response"
                mock_get_model.return_value = mock_provider
                
                ai_engine = AIEngine(config_manager)
                assert ai_engine.max_retries == 5  # Should use config value
                
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @patch('src.providers.ollama_model.OllamaModel')
    def test_ai_engine_end_to_end_workflow(self, mock_ollama):
        """Test end-to-end AI Engine workflow"""
        # Setup realistic mock provider
        mock_ollama_instance = MagicMock(spec=BaseModel)
        mock_ollama_instance.test_connection.return_value = True
        mock_ollama_instance._call_model.return_value = """
        💡 WHAT IT DOES:
        Adds files to the staging area for commit.
        
        🎯 WHEN TO USE IT:
        When you want to prepare changes for the next commit.
        
        🚀 HOW TO USE IT:
        git add <file> or git add .
        
        -A: Add all files
        -i: Interactive mode
        """
        mock_ollama.return_value = mock_ollama_instance
        
        # Configure to use Ollama for all providers
        self.mock_config_manager.config.explanation_provider = "ollama"
        
        ai_engine = AIEngine(self.mock_config_manager)
        
        # Test complete workflow
        messages = [
            {"severity": "error", "message": "fatal: not a git repository", "type": "NOT_GIT_REPO"},
            {"severity": "warning", "message": "warning: LF will be replaced by CRLF", "type": "LINE_ENDING", "file": "test.py"}
        ]
        
        # Analyze errors
        analysis = ai_engine.analyze_error_messages(messages)
        assert "Test response" in analysis
        
        # Explain command
        explanation = ai_engine.explain_command("add")
        assert "💡 WHAT IT DOES:" in explanation
        assert "🎯 WHEN TO USE IT:" in explanation
        assert "🚀 HOW TO USE IT:" in explanation
    
    def test_ai_engine_error_message_formatting(self):
        """Test AI Engine error message formatting with various message structures"""
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_provider._call_model.return_value = "Analysis complete"
            mock_get_model.return_value = mock_provider
            
            ai_engine = AIEngine(self.mock_config_manager)
            
            # Test with different message formats
            test_cases = [
                # Minimal message
                [{"message": "Simple error"}],
                # Full message
                [{"severity": "error", "message": "Detailed error", "type": "CUSTOM_ERROR", "file": "test.py", "line": 42}],
                # Mixed messages
                [
                    {"severity": "error", "message": "Error 1", "type": "ERROR_TYPE"},
                    {"severity": "warning", "message": "Warning 1", "file": "warn.py"},
                    {"message": "Message without severity"}
                ]
            ]
            
            for messages in test_cases:
                result = ai_engine.analyze_error_messages(messages)
                assert result == "Analysis complete"
                
                # Verify the prompt was built correctly
                call_args = mock_provider._call_model.call_args[0][0]
                assert "You are a Git expert assistant" in call_args
                assert "Messages to analyze:" in call_args
