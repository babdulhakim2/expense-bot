"""
Configuration for RAG Processor Cloud Function

Reads all configuration from environment variables for security
and flexibility in different deployment environments.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for RAG Processor"""
    
    # Environment
    ENV = os.getenv('ENVIRONMENT', 'production')
    
    # Google Cloud Configuration
    PROJECT_ID = os.getenv('PROJECT_ID', '642983317730')
    
    # LanceDB Configuration (defaults depend on environment)
    LANCEDB_URI = os.getenv('LANCEDB_URI')
    LANCEDB_API_KEY = os.getenv('LANCEDB_API_KEY')
    LANCEDB_REGION = os.getenv('LANCEDB_REGION')
    LANCEDB_TABLE_NAME = os.getenv('LANCEDB_TABLE_NAME')
    
    # RAG Performance Configuration
    ENABLE_PARALLEL_PROCESSING = os.getenv('ENABLE_PARALLEL_PROCESSING', 'true').lower() == 'true'
    AUTO_RETRY_FAILED = os.getenv('AUTO_RETRY_FAILED', 'true').lower() == 'true'
    MAX_INDEXING_RETRIES = int(os.getenv('MAX_INDEXING_RETRIES', '3'))
    CHUNK_BATCH_SIZE = int(os.getenv('CHUNK_BATCH_SIZE', '50'))
    RAG_MAX_WORKERS = int(os.getenv('RAG_MAX_WORKERS', '4'))
    RAG_PROCESSING_TIMEOUT = int(os.getenv('RAG_PROCESSING_TIMEOUT', '300'))  # 5 minutes
    
    # Google Drive Configuration (for document access)
    GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
    GOOGLE_DRIVE_BASE_PATH = os.getenv('GOOGLE_DRIVE_BASE_PATH', 'ExpenseBot-Documents')
    
    # Gemini Configuration (if needed for document processing)
    GOOGLE_GENERATIVE_AI_API_KEY = os.getenv('GOOGLE_GENERATIVE_AI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    @classmethod
    def is_local_development(cls):
        """Check if running in local development mode"""
        return cls.ENV == 'local' or (cls.LANCEDB_URI and cls.LANCEDB_URI.startswith('./'))
    
    @classmethod 
    def get_lancedb_config(cls):
        """Get LanceDB configuration based on environment"""
        # Check if explicit cloud credentials are provided
        if cls.LANCEDB_URI and cls.LANCEDB_URI.startswith('db://'):
            # Force cloud mode if db:// URI is provided
            return {
                'uri': cls.LANCEDB_URI,
                'api_key': cls.LANCEDB_API_KEY,
                'region': cls.LANCEDB_REGION or 'us-east-1',
                'table_name': cls.LANCEDB_TABLE_NAME or 'expense_documents'
            }
        elif cls.is_local_development():
            return {
                'uri': cls.LANCEDB_URI or './.lancedb/data',
                'api_key': None,  # Local doesn't need API key
                'region': None,   # Local doesn't need region
                'table_name': cls.LANCEDB_TABLE_NAME or 'expense_documents_local'
            }
        else:
            # Default cloud configuration with updated credentials
            return {
                'uri': cls.LANCEDB_URI or 'db://expense-bot-yoktc7',
                'api_key': cls.LANCEDB_API_KEY or 'sk_AVWJKGPQRNE4POBU3QZVHWVGCNWART4GP5774NKSDELWCGDTFPYA====',
                'region': cls.LANCEDB_REGION or 'us-east-1',
                'table_name': cls.LANCEDB_TABLE_NAME or 'expense_documents'
            }

    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        # For local development, we don't require cloud credentials
        if cls.is_local_development():
            logger.info("Local development mode - skipping cloud credential validation")
            return
            
        required_keys = [
            'LANCEDB_URI',
            'LANCEDB_API_KEY', 
            'LANCEDB_REGION'
        ]
        
        missing_keys = []
        for key in required_keys:
            value = getattr(cls, key, None)
            if not value:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {', '.join(missing_keys)}")
        
        # Validate JSON format for service account key if provided
        if cls.GOOGLE_SERVICE_ACCOUNT_KEY:
            try:
                json.loads(cls.GOOGLE_SERVICE_ACCOUNT_KEY)
            except json.JSONDecodeError as e:
                logger.warning(f"GOOGLE_SERVICE_ACCOUNT_KEY is not valid JSON: {str(e)}")
        
        logger.info("Configuration validation passed")
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of current configuration (without sensitive data)"""
        return {
            'environment': cls.ENV,
            'project_id': cls.PROJECT_ID,
            'lancedb_uri': cls.LANCEDB_URI,
            'lancedb_region': cls.LANCEDB_REGION,
            'lancedb_table': cls.LANCEDB_TABLE_NAME,
            'max_workers': cls.RAG_MAX_WORKERS,
            'batch_size': cls.CHUNK_BATCH_SIZE,
            'has_service_account': bool(cls.GOOGLE_SERVICE_ACCOUNT_KEY),
            'has_gemini_key': bool(cls.GOOGLE_GENERATIVE_AI_API_KEY)
        }

# Validate configuration on import
try:
    Config.validate_config()
except Exception as e:
    logger.warning(f"Configuration validation failed: {e}")
    # Don't fail completely in case we're just importing for testing