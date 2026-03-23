from pathlib import Path
from src.fancygit_config_dc import FancyGitConfig
from typing import Optional
class ConfigManager():

    CONFIG_PATH = Path.home() / '.fancygit_config'

    def __init__(self, config_path: Optional[Path] = None):
        self.CONFIG_PATH = config_path or self.CONFIG_PATH
        self.config = FancyGitConfig()
        self.load_config()
        self._create_default_config_file()

    def load_config(self):
        """Load configuration from .fancygit_config file or use defaults"""

        if not self.CONFIG_PATH.exists():
            return
        
        try:
            with open(self.CONFIG_PATH, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        self._set_config_value(key.strip(), value.strip())
        except Exception as e:
            print(f"Failed to load config file: {e}")


    def _set_config_value(self, key: str, value: str):
        """Set a configuration value based on key"""
        if not hasattr(self, 'config'):
            self.config = FancyGitConfig()  # Ensure config is initialized

        if hasattr(self.config, key):
            attr_type = type(getattr(self.config, key))
            try:
                if attr_type == bool:
                    setattr(self.config, key, value.lower() in ['true', '1', 'yes'])
                elif attr_type == int:
                    setattr(self.config, key, int(value))
                else:
                    setattr(self.config, key, value)
            except ValueError as e:
                print(f"Invalid value for {key}: {value}. Error: {e}")


    def _create_default_config_file(self):
        """Create a default .fancygit_config file if it doesn't exist"""
        if not self.CONFIG_PATH.exists():
            self.save_config()

    def save_config(self):
        """Save current configuration to .fancygit_config file"""
        try:
            with open(self.CONFIG_PATH, 'w') as f:
                for field in self.config.__dataclass_fields__:
                    value = getattr(self.config, field)
                    f.write(f"{field}={value}\n")
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_config(self, **kwargs):
        """Update configuration values and save to file"""
        for key, value in kwargs.items():
            self._set_config_value(key, str(value))  # Convert value to string for parsing
        self.save_config()