# Import required packages
from dataclasses import dataclass
from typing import Optional, Dict, List
from dotenv import load_dotenv
import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Load environment variables
load_dotenv()

@dataclass
class LogConfig:
    """Configuration for logging system"""
    # Environment-specific log levels
    env_levels: Dict[str, str] = None
    
    # Default logging settings
    default_level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_dir: str = "Logs"
    
    # Log file settings
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5  # Keep 5 backup files
    
    def __post_init__(self):
        # Initialize environment-specific log levels
        self.env_levels = {
            "development": "DEBUG",
            "testing": "INFO",
            "production": "WARNING"
        }
        
    @property
    def log_file(self) -> str:
        """Generate log filename with current date"""
        return f"assistant_{datetime.now().strftime('%Y%m%d')}.log"
    
    @property
    def full_path(self) -> str:
        """Get full path to current log file"""
        return os.path.join(self.log_dir, self.log_file)

@dataclass
class APIConfig:
    """API configuration settings"""
    # Load from .env with fallback defaults
    cohere_api_key: str = os.getenv('CohereAPIKey', '')
    groq_api_key: str = os.getenv('GroqAPIKey', '')
    huggingface_api_key: Optional[str] = os.getenv('HuggingfaceAPIKey', '')

@dataclass
class AssistantConfig:
    """Assistant-specific configuration"""
    # Load from .env with fallback defaults
    username: str = os.getenv('Username', 'User')
    assistant_name: str = os.getenv('Assistantname', 'EVA')
    input_language: str = os.getenv('InputLanguage', 'en-US')
    assistant_voice: str = os.getenv('AssistantVoice', 'en-CA-LiamNeural')
    
    @property
    def default_message(self) -> str:
        """Generate default welcome message using username and assistant name"""
        return f"Hello {self.username}! I'm {self.assistant_name}. How can I assist you today?"

@dataclass
class PathConfig:
    """Path configuration for various files"""
    base_dir: Path = Path(os.getcwd())
    data_dir: Path = base_dir / "Data"
    temp_dir: Path = base_dir / "Frontend" / "Files"
    graphics_dir: Path = base_dir / "Frontend" / "Graphics"
    
    def __post_init__(self):
        """Ensure all required directories exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.graphics_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def chat_log_path(self) -> Path:
        return self.data_dir / "ChatLog.json"
    
    @property
    def speech_output_path(self) -> Path:
        return self.data_dir / "speech.mp3"
    
    @property
    def voice_html_path(self) -> Path:
        return self.data_dir / "Voice.html"
    
    @property
    def image_gen_status_path(self) -> Path:
        return self.temp_dir / "ImageGeneration.data"

@dataclass
class ModelConfig:
    """Model-specific configuration"""
    cohere_model: str = "command"
    groq_model: str = "mixtral-8x7b-32768"
    stable_diffusion_model: str = "stabilityai/stable-diffusion-2"

class Config:
    """Central configuration management"""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults"""
        # Initialize all configuration components
        self.api = APIConfig()
        self.assistant = AssistantConfig()
        self.paths = PathConfig()
        self.models = ModelConfig()
        self.logging = LogConfig()
        
        # Set up enhanced logging system
        self._setup_logging()
        
        # Log initialization
        self.logger.info(f"Configuration initialized for {self.assistant.assistant_name}")
        self._log_diagnostic_info()
        
    def _setup_logging(self):
        """Configure enhanced logging system"""
        # Create logs directory if needed
        os.makedirs(self.logging.log_dir, exist_ok=True)
        
        # Determine environment and log level
        env = os.getenv('ENVIRONMENT', 'development').lower()
        log_level = self.logging.env_levels.get(env, self.logging.default_level)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.logging.full_path,
            maxBytes=self.logging.max_bytes,
            backupCount=self.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level))
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Console always shows INFO and above
        
        # Create formatter
        formatter = logging.Formatter(
            fmt=self.logging.format,
            datefmt=self.logging.date_format
        )
        
        # Apply formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        root_logger.handlers = []  # Remove existing handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Create logger for this class
        self.logger = logging.getLogger("Config")
        
    def _log_diagnostic_info(self):
        """Log system and configuration diagnostic information"""
        self.logger.debug(f"Python Version: {os.sys.version}")
        self.logger.debug(f"Working Directory: {os.getcwd()}")
        self.logger.debug(f"Log File: {self.logging.full_path}")
        self.logger.debug(f"Data Directory: {self.paths.data_dir}")
        self.logger.debug(f"Assistant Name: {self.assistant.assistant_name}")
        self.logger.debug(f"Input Language: {self.assistant.input_language}")
        self.logger.debug(f"Models: {self.models}")
        
    def validate(self) -> bool:
        """
        Validate configuration settings
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check required API keys
            if not self.api.cohere_api_key:
                raise ValueError("CohereAPIKey is required in .env file")
            if not self.api.groq_api_key:
                raise ValueError("GroqAPIKey is required in .env file")
                
            # Validate paths
            if not self.paths.data_dir.exists():
                raise ValueError(f"Data directory does not exist: {self.paths.data_dir}")
            if not self.paths.temp_dir.exists():
                raise ValueError(f"Temp directory does not exist: {self.paths.temp_dir}")
                
            self.logger.info('Configuration validation successful')
            return True
            
        except Exception as e:
            self.logger.error(f'Configuration validation failed: {e}')
            return False
            
    def load_chat_log(self) -> List[dict]:
        """
        Load chat history from file
        
        Returns:
            List[dict]: List of chat messages
        """
        try:
            if self.paths.chat_log_path.exists():
                with open(self.paths.chat_log_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                self.logger.debug(f"Chat log loaded: {len(messages)} messages")
                return messages
            return []
        except Exception as e:
            self.logger.error(f'Error loading chat log: {e}')
            return []
            
    def save_chat_log(self, messages: List[dict]) -> None:
        """
        Save chat history to file
        
        Args:
            messages (List[dict]): List of chat messages to save
        """
        try:
            with open(self.paths.chat_log_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2)
            self.logger.debug(f"Chat log saved: {len(messages)} messages")
        except Exception as e:
            self.logger.error(f'Error saving chat log: {e}')
            raise

# Create global configuration instance
config = Config()

# Validate configuration on import
if not config.validate():
    config.logger.warning("Configuration validation failed - some features may not work correctly") 