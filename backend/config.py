import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
# 

# Load .env file from mounted secrets or local file
if os.path.exists('/secrets/.env'):
    load_dotenv('/secrets/.env')
else:
    load_dotenv()  # take environment variables from .env.

logger = logging.getLogger(__name__)

class Config:
    # Environment
    ENV = os.getenv('ENVIRONMENT', 'development')

    AI_BASE_URL = os.getenv('AI_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')
    
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
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
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
    
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    SITE_URL = os.getenv('SITE_URL', 'https://expensebot.xyz')
    
    # Google Drive Base Path
    GOOGLE_DRIVE_BASE_PATH = os.getenv('GOOGLE_DRIVE_BASE_PATH', 'ExpenseBot-Dev')
    
    # RAG Performance Configuration
    ENABLE_PARALLEL_PROCESSING = os.getenv('ENABLE_PARALLEL_PROCESSING', 'true').lower() == 'true'
    AUTO_RETRY_FAILED = os.getenv('AUTO_RETRY_FAILED', 'true').lower() == 'true'
    MAX_INDEXING_RETRIES = int(os.getenv('MAX_INDEXING_RETRIES', '3'))
    CHUNK_BATCH_SIZE = int(os.getenv('CHUNK_BATCH_SIZE', '50'))
    RAG_MAX_WORKERS = int(os.getenv('RAG_MAX_WORKERS', '4'))
    RAG_PROCESSING_TIMEOUT = int(os.getenv('RAG_PROCESSING_TIMEOUT', '300'))  # 5 minutes
    
    # RAG Performance Configuration (legacy - now handled by RAG Cloud Function)
    # These are kept for backward compatibility but should be removed in future versions
    
    # RAG Cloud Function Configuration
    RAG_FUNCTION_URL = os.getenv('RAG_FUNCTION_URL')  # URL of deployed RAG Cloud Function
    RAG_INDEXING_TOPIC = os.getenv('RAG_INDEXING_TOPIC', 'rag-indexing-jobs')
    RAG_RESULT_TOPIC = os.getenv('RAG_RESULT_TOPIC', 'rag-indexing-results')
    USE_CLOUD_FUNCTION_INDEXING = os.getenv('USE_CLOUD_FUNCTION_INDEXING', 'false').lower() == 'true'
    
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

# Load and validate configuration only if not in Cloud Functions
import os
if not os.environ.get('FUNCTION_NAME'):  # Cloud Functions set this automatically
    Config.validate_config()