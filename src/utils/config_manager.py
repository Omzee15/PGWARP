"""
User Configuration Manager for PgWarp
Handles saving and loading user preferences including theme settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class UserConfig:
    """User configuration data structure"""
    # Theme settings
    default_theme: str = "default"
    theme_mode: str = "light"  # light, dark, system
    
    # Window settings
    window_size: str = "1400x900"
    window_maximized: bool = False
    
    # Database settings
    default_host: str = "localhost"
    default_port: int = 5432
    default_database: str = "postgres"
    remember_last_connection: bool = True
    
    # Query settings
    max_result_rows: int = 10000
    query_timeout: int = 300
    auto_commit: bool = False
    
    # AI settings
    ai_enabled: bool = True
    ai_model: str = "gemini-2.0-flash-exp"
    ai_max_history: int = 20
    
    # Terminal settings
    terminal_font_size: int = 11
    terminal_font_family: str = "Consolas"
    terminal_history_size: int = 100
    
    # UI settings
    show_line_numbers: bool = True
    word_wrap: bool = False
    auto_save_queries: bool = True


class ConfigManager:
    """Manages user configuration persistence"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_file = self.config_dir / "user_config.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # Load existing config or create default
        self.config = self.load_config()
        
    def load_config(self) -> UserConfig:
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create UserConfig from loaded data, filling in defaults for missing keys
                config_data = {}
                default_config = UserConfig()
                
                # Use loaded values or defaults
                for field in default_config.__dataclass_fields__:
                    config_data[field] = data.get(field, getattr(default_config, field))
                
                return UserConfig(**config_data)
            else:
                print("No config file found, creating default configuration")
                return UserConfig()
                
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return UserConfig()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            # Convert config to dictionary and save
            config_dict = asdict(self.config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration saved to: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a configuration value"""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        try:
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                return True
            else:
                print(f"Unknown config key: {key}")
                return False
        except Exception as e:
            print(f"Error setting config {key}: {e}")
            return False
    
    def update(self, **kwargs) -> bool:
        """Update multiple configuration values"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    print(f"Unknown config key: {key}")
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config = UserConfig()
            return self.save_config()
        except Exception as e:
            print(f"Error resetting config: {e}")
            return False
    
    def apply_theme_setting(self) -> bool:
        """Apply the configured default theme"""
        try:
            # Import here to avoid circular imports
            from .theme_manager import theme_manager
            
            theme_name = self.config.default_theme
            
            # Validate theme exists
            available_themes = theme_manager.list_available_themes()
            if theme_name not in available_themes:
                print(f"Theme '{theme_name}' not found, using 'default'")
                theme_name = "default"
                self.config.default_theme = "default"
                self.save_config()
            
            # Apply the theme
            return theme_manager.set_theme(theme_name)
            
        except Exception as e:
            print(f"Error applying theme setting: {e}")
            return False
    
    def get_theme_options(self) -> Dict[str, str]:
        """Get available theme options with display names"""
        try:
            # Import here to avoid circular imports
            from .theme_manager import theme_manager
            return theme_manager.get_theme_display_names()
        except Exception as e:
            print(f"Error getting theme options: {e}")
            return {"default": "Default Theme"}
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a file"""
        try:
            config_dict = asdict(self.config)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate and create new config
            default_config = UserConfig()
            config_data = {}
            
            for field in default_config.__dataclass_fields__:
                config_data[field] = data.get(field, getattr(default_config, field))
            
            self.config = UserConfig(**config_data)
            return self.save_config()
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False


# Global configuration manager instance
config_manager = ConfigManager()


# Convenience functions
def get_config(key: str, default=None):
    """Get a configuration value"""
    return config_manager.get(key, default)


def set_config(key: str, value: Any) -> bool:
    """Set a configuration value and save"""
    if config_manager.set(key, value):
        return config_manager.save_config()
    return False


def save_config() -> bool:
    """Save current configuration"""
    return config_manager.save_config()


def apply_startup_theme() -> bool:
    """Apply the configured startup theme"""
    return config_manager.apply_theme_setting()