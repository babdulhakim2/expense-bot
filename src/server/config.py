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

    # API Keys and Credentials
    GOOGLE_GENERATIVE_AI_API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')
    SERVICE_ACCOUNT_KEY = os.getenv('SERVICE_ACCOUNT_KEY')
    FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    WANDB_API_KEY = os.getenv('WANDB_API_KEY')
    
    # User Configuration
    DEFAULT_USER_EMAIL = os.getenv('DEFAULT_USER_EMAIL', '')
    
    # Firebase Emulator Settings
    FIREBASE_EMULATOR_HOST = os.getenv('FIREBASE_EMULATOR_HOST', 'localhost:8080')
    USE_FIREBASE_EMULATOR = os.getenv('USE_FIREBASE_EMULATOR', 'true').lower() == 'true'
    
    # Firebase Config
    FIREBASE_SERVICE_ACCOUNT_KEY = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')
    
    # Development mode flag
    IS_DEVELOPMENT = os.getenv('FLASK_ENV') == 'development'
    
    # Firebase Emulator ports (for development)
    FIREBASE_AUTH_EMULATOR_HOST = os.getenv('FIREBASE_AUTH_EMULATOR_HOST', 'localhost:9099')
    FIREBASE_FIRESTORE_EMULATOR_HOST = os.getenv('FIREBASE_FIRESTORE_EMULATOR_HOST', 'localhost:8080')
    FIREBASE_STORAGE_EMULATOR_HOST = os.getenv('FIREBASE_STORAGE_EMULATOR_HOST', 'localhost:9199')
    
    # Plaid Configuration
    PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
    PLAID_SECRET = os.getenv('PLAID_SECRET')
    PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')
    PLAID_REDIRECT_URI = os.getenv('PLAID_REDIRECT_URI', 'http://localhost:3000/banking/callback')
    
    # Encryption
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Must be 32 bytes for Fernet
    
    # Webhook
    TRUELAYER_WEBHOOK_SECRET = os.getenv('TRUELAYER_WEBHOOK_SECRET')
    
    # Frontend URLs
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        required_keys = [
            'GOOGLE_GENERATIVE_AI_API_KEY',
            'SERVICE_ACCOUNT_KEY',
            'FIREBASE_SERVICE_ACCOUNT_KEY'
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
        
        # Validate Firebase configuration
        if not cls.FIREBASE_SERVICE_ACCOUNT_KEY:
            raise ValueError("Missing required configuration key: FIREBASE_SERVICE_ACCOUNT_KEY")
        
        # Validate FIREBASE_SERVICE_ACCOUNT_KEY is valid JSON
   
        try:
            if isinstance(cls.FIREBASE_SERVICE_ACCOUNT_KEY, str):
                json.loads(cls.FIREBASE_SERVICE_ACCOUNT_KEY)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"FIREBASE_SERVICE_ACCOUNT_KEY is not valid JSON: {str(e)}")
        
        # Set additional config values
        cls.GOOGLE_SERVICE_ACCOUNT_KEY = cls.SERVICE_ACCOUNT_KEY
        
        required_vars = [
            # ('TRUELAYER_CLIENT_ID', cls.TRUELAYER_CLIENT_ID),
            # ('TRUELAYER_CLIENT_SECRET', cls.TRUELAYER_CLIENT_SECRET),
            # ('TRUELAYER_REDIRECT_URI', cls.TRUELAYER_REDIRECT_URI),
        ]
        
        missing = [var[0] for var in required_vars if not var[1]]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    @classmethod
    def get_frontend_url(cls, path: str) -> str:
        """Get full frontend URL for a path"""
        return f"{cls.FRONTEND_URL}{path}"

# Load and validate configuration
Config.validate_config()