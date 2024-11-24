import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class Config:
    # Environment
    ENV = os.getenv('ENVIRONMENT', 'development')
    
    # Project Configuration
    PROJECT_ID = os.getenv('PROJECT_ID', '642983317730')
    
    # Gemini Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    GEMINI_GENERATION_CONFIG = {
        "temperature": float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
        "top_p": float(os.getenv('GEMINI_TOP_P', '0.95')),
        "top_k": int(os.getenv('GEMINI_TOP_K', '40')),
        "max_output_tokens": int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192')),
    }

    # Database Configuration
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'expenses.db')
    
    # API Keys and Credentials
    GOOGLE_GENERATIVE_AI_API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')
    SERVICE_ACCOUNT_KEY = os.getenv('SERVICE_ACCOUNT_KEY')
    WANDB_API_KEY = os.getenv('WANDB_API_KEY')
    
    # User Configuration
    DEFAULT_USER_EMAIL = os.getenv('DEFAULT_USER_EMAIL', '')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        required_keys = [
            'GOOGLE_GENERATIVE_AI_API_KEY',
            'SERVICE_ACCOUNT_KEY'
        ]
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        
        # Validate SERVICE_ACCOUNT_KEY is valid JSON
        try:
            if isinstance(cls.SERVICE_ACCOUNT_KEY, str):
                json.loads(cls.SERVICE_ACCOUNT_KEY)
        except json.JSONDecodeError as e:
            raise ValueError(f"SERVICE_ACCOUNT_KEY is not valid JSON: {str(e)}")
        
        # Set additional config values
        cls.GOOGLE_SERVICE_ACCOUNT_KEY = cls.SERVICE_ACCOUNT_KEY

# Load and validate configuration
Config.validate_config()