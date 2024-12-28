from cryptography.fernet import Fernet
from config import Config
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        """Initialize encryption service with key from config"""
        try:
            # Generate key from secret
            key = base64.urlsafe_b64encode(Config.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0'))
            self.cipher_suite = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            raise

    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        try:
            if not data:
                return None
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        try:
            if not encrypted_data:
                return None
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return None 