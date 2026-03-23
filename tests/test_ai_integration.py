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
    """Integration tests for AI architecture components - simplified"""
    
    def setup_method(self):
        """Setup method called before each test"""
        # Create a mock config manager with realistic settings
        from src.fancygit_config_dc import FancyGitConfig
        
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_manager.config = FancyGitConfig()
        self.mock_config_manager.config.analysis_provider = "ollama"
        self.mock_config_manager.config.explanation_provider = "openai"
        self.mock_config_manager.config.translation_provider = "anthropic"
        self.mock_config_manager.config.ai_analysis_enabled = True
        self.mock_config_manager.config.ollama_max_retries = 3
    
    def test_ai_engine_initialization(self):
        """Test AI Engine initialization with mock providers"""
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_provider.test_connection.return_value = True
            mock_get_model.return_value = mock_provider
            
            # Create AI Engine
            ai_engine = AIEngine(self.mock_config_manager)
            
            # Verify initialization
            assert ai_engine.config_manager == self.mock_config_manager
            assert ai_engine.max_retries == 3
            assert mock_get_model.call_count == 3
    
    def test_ai_engine_error_handling(self):
        """Test AI Engine behavior when providers fail"""
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_provider.test_connection.return_value = False
            mock_provider._call_model.side_effect = Exception("Provider unavailable")
            mock_get_model.return_value = mock_provider
            
            ai_engine = AIEngine(self.mock_config_manager)
            
            # Test error analysis with failing provider
            messages = [{"severity": "error", "message": "Test error"}]
            result = ai_engine.analyze_error_messages(messages)
            assert "Failed to get AI analysis" in result
    
    def test_ai_engine_basic_functionality(self):
        """Test basic AI Engine functionality"""
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_provider.test_connection.return_value = True
            mock_provider._call_model.return_value = "Test response"
            mock_get_model.return_value = mock_provider
            
            ai_engine = AIEngine(self.mock_config_manager)
            
            # Test error messages analysis
            messages = [{"severity": "error", "message": "Test error"}]
            result = ai_engine.analyze_error_messages(messages)
            assert result == "Test response"
            
            # Test prompt building
            call_args = mock_provider._call_model.call_args[0][0]
            assert "You are a Git expert assistant" in call_args
            assert "Messages to analyze:" in call_args
    
    def test_model_provider_factory_integration(self):
        """Test ModelProvider factory integration with AI Engine"""
        with patch('src.model_provider.ModelProvider.get_model') as mock_get_model:
            mock_provider = MagicMock(spec=BaseModel)
            mock_provider.test_connection.return_value = True
            mock_provider._call_model.return_value = "Test response"
            mock_get_model.return_value = mock_provider
            
            # Test that AI Engine uses ModelProvider factory
            ai_engine = AIEngine(self.mock_config_manager)
            
            # Verify ModelProvider.get_model was called for each provider
            assert mock_get_model.call_count == 3
    
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
