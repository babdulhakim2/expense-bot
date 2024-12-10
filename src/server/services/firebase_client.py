import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from config import Config
import logging

logger = logging.getLogger(__name__)

class FirebaseClient:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            FirebaseClient._initialized = True

    def _initialize_firebase(self):
        """Initialize Firebase with appropriate configuration"""
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
                if self._check_emulators():
                    # Set emulator environment variables
                    os.environ["FIRESTORE_EMULATOR_HOST"] = Config.FIREBASE_FIRESTORE_EMULATOR_HOST
                    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = Config.FIREBASE_AUTH_EMULATOR_HOST
                    os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = Config.FIREBASE_STORAGE_EMULATOR_HOST
                    
                    logger.info("Using Firebase emulators:")
                    logger.info(f"Firestore: {Config.FIREBASE_FIRESTORE_EMULATOR_HOST}")
                    logger.info(f"Auth: {Config.FIREBASE_AUTH_EMULATOR_HOST}")
                    logger.info(f"Storage: {Config.FIREBASE_STORAGE_EMULATOR_HOST}")
                else:
                    logger.warning("Development mode but emulators not running! Using production services.")

            # Initialize Firebase with credentials
            cred = credentials.Certificate(json.loads(Config.FIREBASE_SERVICE_ACCOUNT_KEY))
            firebase_admin.initialize_app(cred, {
                'storageBucket': Config.FIREBASE_STORAGE_BUCKET
            })

            # Initialize clients
            self.db = firestore.client()
            self.auth = auth
            self.storage = storage
            self.bucket = storage.bucket()
            
            logger.info(f"Firebase initialized in {'development' if Config.IS_DEVELOPMENT else 'production'} mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    def _check_emulators(self) -> bool:
        """Check if Firebase emulators are running"""
        try:
            import requests
            response = requests.get(
                f"http://{Config.FIREBASE_FIRESTORE_EMULATOR_HOST}/", 
                timeout=1
            )
            return response.status_code == 200
        except:
            return False

# Create a singleton instance
firebase = FirebaseClient() 