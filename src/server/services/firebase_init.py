import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from config import Config
import logging

logger = logging.getLogger(__name__)

def is_emulator_running():
    """Check if Firebase emulators are running"""
    try:
        import requests
        # Try to connect to Firestore emulator
        response = requests.get(f"http://{Config.FIREBASE_FIRESTORE_EMULATOR_HOST}/", timeout=1)
        return response.status_code == 200
    except:
        return False

def initialize_firebase():
    """Initialize Firebase with appropriate configuration for dev/prod environments"""
    try:
        # Check if Firebase is already initialized
        if len(firebase_admin._apps) > 0:
            logger.info("Firebase already initialized")
            return

        # Load service account
        if not Config.FIREBASE_SERVICE_ACCOUNT_KEY:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY not found in environment variables")
            
        if not Config.FIREBASE_STORAGE_BUCKET:
            raise ValueError("FIREBASE_STORAGE_BUCKET not found in environment variables")

        # Set up emulators if in development mode
        if Config.IS_DEVELOPMENT:
            if not is_emulator_running():
                logger.warning("Development mode but emulators not running! Using production services.")
            else:
                # Set emulator environment variables
                os.environ["FIRESTORE_EMULATOR_HOST"] = Config.FIREBASE_FIRESTORE_EMULATOR_HOST
                os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = Config.FIREBASE_AUTH_EMULATOR_HOST
                os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = Config.FIREBASE_STORAGE_EMULATOR_HOST
                
                logger.info("Using Firebase emulators:")
                logger.info(f"Firestore: {Config.FIREBASE_FIRESTORE_EMULATOR_HOST}")
                logger.info(f"Auth: {Config.FIREBASE_AUTH_EMULATOR_HOST}")
                logger.info(f"Storage: {Config.FIREBASE_STORAGE_EMULATOR_HOST}")

        # Initialize Firebase with credentials
        cred = credentials.Certificate(json.loads(Config.FIREBASE_SERVICE_ACCOUNT_KEY))
        firebase_admin.initialize_app(cred, {
            'storageBucket': Config.FIREBASE_STORAGE_BUCKET
        })
        
        logger.info(f"Firebase initialized in {'development' if Config.IS_DEVELOPMENT else 'production'} mode")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise

def get_storage_bucket():
    """Get the storage bucket instance"""
    try:
        bucket_name = Config.FIREBASE_STORAGE_BUCKET
        if not bucket_name:
            raise ValueError("Storage bucket name not specified in configuration")
        return storage.bucket(bucket_name)
    except ValueError as e:
        logger.error(f"Storage bucket error: {str(e)}")
        raise