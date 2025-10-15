"""
Configuration settings for NeuronDB application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Application info
    APP_NAME = "NeuronDB"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "AI-Powered PostgreSQL Desktop Client"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BASE_DIR / "logs"
    CONFIG_DIR = BASE_DIR / "config"
    
    # Logo paths
    DESKTOP_ICON = BASE_DIR / "images" / "Group 5.png"
    APP_LOGO = BASE_DIR / "images" / "Gemini_Generated_Image_5oy95d5oy95d5oy9-removebg-preview 2.png"
    
    # Database defaults
    DEFAULT_HOST = os.getenv("DEFAULT_HOST", "localhost")
    DEFAULT_PORT = int(os.getenv("DEFAULT_PORT", "5432"))
    DEFAULT_DATABASE = os.getenv("DEFAULT_DATABASE", "postgres")
    
    # AI Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    AI_MODEL = "gemini-2.0-flash-exp"  # Latest Gemini 2.0 Flash model
    AI_MAX_HISTORY = 20
    
    # UI Configuration
    THEME_MODE = "dark"  # "light", "dark", "system"
    COLOR_THEME = "blue"  # "blue", "green", "dark-blue"
    
    # Query Configuration
    MAX_RECENT_QUERIES = 50
    QUERY_TIMEOUT = 300  # seconds
    MAX_RESULT_ROWS = 10000
    
    # Terminal Configuration
    TERMINAL_FONT = ("Consolas", 11)
    TERMINAL_HISTORY_SIZE = 100
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "neurondb.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Window Configuration
    DEFAULT_WINDOW_SIZE = "1400x900"
    MIN_WINDOW_SIZE = "1200x800"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.CONFIG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def is_ai_configured(cls) -> bool:
        """Check if AI is properly configured"""
        return bool(cls.GOOGLE_API_KEY)
    
    @classmethod
    def get_connection_file(cls) -> Path:
        """Get path to connections file"""
        return cls.BASE_DIR / "connections.json"
    
    @classmethod
    def get_log_file(cls) -> Path:
        """Get path to log file"""
        return cls.LOGS_DIR / cls.LOG_FILE

# Create directories on import
Config.ensure_directories()