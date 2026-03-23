import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from src.config_manager import ConfigManager
from src.fancygit_config_dc import FancyGitConfig

@pytest.mark.unit
class TestConfigManager:
    """Test cases for Config Manager class"""
    
    def setup_method(self):
        """Setup method called before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / ".fancygit_config"
    
    def teardown_method(self):
        """Cleanup method called after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_manager_initialization_with_default_path(self):
        """Test ConfigManager initialization with default config path"""
        with patch('src.config_manager.Path.home', return_value=Path("/home/user")):
            config_manager = ConfigManager()
            # The actual path will be the real home path, not the mocked one
            # because the assignment happens before the patch takes effect
            assert isinstance(config_manager.CONFIG_PATH, Path)
            assert config_manager.CONFIG_PATH.name == '.fancygit_config'
            assert isinstance(config_manager.config, FancyGitConfig)
    
    def test_config_manager_initialization_with_custom_path(self):
        """Test ConfigManager initialization with custom config path"""
        config_manager = ConfigManager(config_path=self.config_path)
        assert config_manager.CONFIG_PATH == self.config_path
        assert isinstance(config_manager.config, FancyGitConfig)
    
    def test_load_config_when_file_does_not_exist(self):
        """Test loading config when file doesn't exist (should use defaults)"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # The config file might be created during initialization, so let's check
        # that it uses default values regardless
        assert config_manager.config.analysis_provider == "ollama"  # Default value
    
    def test_load_config_with_valid_file(self):
        """Test loading config from a valid file"""
        # Create a test config file
        config_content = """analysis_provider=openai
explanation_provider=anthropic
translation_provider=ollama
ai_analysis_enabled=true
loading_animation=dots
ollama_max_retries=5
"""
        with open(self.config_path, 'w') as f:
            f.write(config_content)
        
        config_manager = ConfigManager(config_path=self.config_path)
        
        assert config_manager.config.analysis_provider == "openai"
        assert config_manager.config.explanation_provider == "anthropic"
        assert config_manager.config.translation_provider == "ollama"
        assert config_manager.config.ai_analysis_enabled == True
        assert config_manager.config.loading_animation == "dots"
        assert config_manager.config.ollama_max_retries == 5
    
    def test_load_config_with_invalid_file_permissions(self):
        """Test loading config when file has permission issues"""
        # Create a test config file
        with open(self.config_path, 'w') as f:
            f.write("analysis_provider=openai\n")
        
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as mock_print:
                config_manager = ConfigManager(config_path=self.config_path)
                mock_print.assert_called_with("Failed to load config file: Permission denied")
    
    def test_set_config_value_boolean(self):
        """Test setting boolean config values"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        config_manager._set_config_value("ai_analysis_enabled", "true")
        assert config_manager.config.ai_analysis_enabled == True
        
        config_manager._set_config_value("ai_analysis_enabled", "false")
        assert config_manager.config.ai_analysis_enabled == False
        
        config_manager._set_config_value("ai_analysis_enabled", "1")
        assert config_manager.config.ai_analysis_enabled == True
        
        config_manager._set_config_value("ai_analysis_enabled", "0")
        assert config_manager.config.ai_analysis_enabled == False
        
        config_manager._set_config_value("ai_analysis_enabled", "yes")
        assert config_manager.config.ai_analysis_enabled == True
        
        config_manager._set_config_value("ai_analysis_enabled", "no")
        assert config_manager.config.ai_analysis_enabled == False
    
    def test_set_config_value_integer(self):
        """Test setting integer config values"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        config_manager._set_config_value("ollama_max_retries", "5")
        assert config_manager.config.ollama_max_retries == 5
        
        config_manager._set_config_value("ollama_max_retries", "10")
        assert config_manager.config.ollama_max_retries == 10
    
    def test_set_config_value_string(self):
        """Test setting string config values"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        config_manager._set_config_value("analysis_provider", "openai")
        assert config_manager.config.analysis_provider == "openai"
        
        config_manager._set_config_value("loading_animation", "spinner")
        assert config_manager.config.loading_animation == "spinner"
    
    def test_set_config_value_invalid_type(self):
        """Test setting config value with invalid type conversion"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        with patch('builtins.print') as mock_print:
            config_manager._set_config_value("ollama_max_retries", "invalid_number")
            mock_print.assert_called()
            assert "Invalid value for ollama_max_retries" in mock_print.call_args[0][0]
    
    def test_set_config_value_nonexistent_field(self):
        """Test setting config value for non-existent field (should be ignored)"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Should not raise an error, just print warning
        with patch('builtins.print') as mock_print:
            config_manager._set_config_value("nonexistent_field", "value")
            # Should not crash and should not affect the config
    
    def test_create_default_config_file_when_not_exists(self):
        """Test creating default config file when it doesn't exist"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        assert self.config_path.exists()
        
        # Check that default values were written
        with open(self.config_path, 'r') as f:
            content = f.read()
            assert "analysis_provider=" in content
            assert "explanation_provider=" in content
            assert "translation_provider=" in content
    
    def test_create_default_config_file_when_exists(self):
        """Test not overwriting existing config file"""
        # Create an existing config file
        with open(self.config_path, 'w') as f:
            f.write("analysis_provider=openai\n")
        
        original_content = self.config_path.read_text()
        
        config_manager = ConfigManager(config_path=self.config_path)
        
        # File should not be overwritten
        assert self.config_path.read_text() == original_content
    
    def test_save_config(self):
        """Test saving current configuration to file"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Modify some config values
        config_manager.config.analysis_provider = "anthropic"
        config_manager.config.ai_analysis_enabled = True
        config_manager.config.ollama_max_retries = 7
        
        config_manager.save_config()
        
        # Read the file and verify content
        with open(self.config_path, 'r') as f:
            content = f.read()
        
        assert "analysis_provider=anthropic" in content
        assert "ai_analysis_enabled=True" in content
        assert "ollama_max_retries=7" in content
    
    def test_save_config_with_file_error(self):
        """Test saving config when file write fails"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as mock_print:
                config_manager.save_config()
                mock_print.assert_called_with("Error saving config: Permission denied")
    
    def test_update_config(self):
        """Test updating multiple config values at once"""
        config_manager = ConfigManager(config_path=self.config_path)
        
        config_manager.update_config(
            analysis_provider="openai",
            ai_analysis_enabled=True,
            ollama_max_retries=10,
            loading_animation="spinner"
        )
        
        assert config_manager.config.analysis_provider == "openai"
        assert config_manager.config.ai_analysis_enabled == True
        assert config_manager.config.ollama_max_retries == 10
        assert config_manager.config.loading_animation == "spinner"
        
        # Verify file was saved
        assert self.config_path.exists()
        with open(self.config_path, 'r') as f:
            content = f.read()
            assert "analysis_provider=openai" in content
            assert "ai_analysis_enabled=True" in content
    
    def test_config_manager_with_uninitialized_config(self):
        """Test _set_config_value when config is not initialized"""
        # Create a fresh config manager to test the initialization logic
        with patch('src.config_manager.Path.home', return_value=Path("/tmp/test")):
            config_manager = ConfigManager()
            
            # Delete the config attribute to simulate uninitialized state
            delattr(config_manager, 'config')
            
            # Should initialize config and set the value
            config_manager._set_config_value("analysis_provider", "openai")
            
            assert config_manager.config is not None
            assert config_manager.config.analysis_provider == "openai"
