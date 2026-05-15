import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional
from loguru import logger

class EncryptionService:
    def __init__(self, key: Optional[str] = None):
        # In production, this key must come from an environment variable or Secret Manager
        self.key = key or os.getenv("QB_ENCRYPTION_KEY") or os.getenv("ENCRYPTION_KEY")
        
        if not self.key:
            logger.warning("Neither QB_ENCRYPTION_KEY nor ENCRYPTION_KEY set. Generating a temporary key.")
            self.key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        else:
            logger.info("Encryption key loaded successfully from environment.")
        
        try:
            self.key_bytes = base64.urlsafe_b64decode(self.key.encode())
            if len(self.key_bytes) != 32:
                logger.warning("ENCRYPTION_KEY is not 32 raw bytes; deriving a stable AES-256 key with SHA-256.")
                self.key_bytes = hashlib.sha256(self.key.encode()).digest()
            self.aesgcm = AESGCM(self.key_bytes)
            try:
                self.legacy_fernet = Fernet(self.key.encode())
            except Exception:
                self.legacy_fernet = None
        except Exception as e:
            logger.error(f"Invalid encryption key provided: {str(e)}")
            raise ValueError("Invalid encryption key")

    def encrypt(self, data: str) -> str:
        if not data: return ""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data.encode(), None)
        return "gcm:" + base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data: return ""
        try:
            if encrypted_data.startswith("gcm:"):
                payload = base64.urlsafe_b64decode(encrypted_data[4:].encode())
                nonce, ciphertext = payload[:12], payload[12:]
                return self.aesgcm.decrypt(nonce, ciphertext, None).decode()

            # Backward-compatible decrypt for credentials created before AES-GCM migration.
            if self.legacy_fernet:
                return self.legacy_fernet.decrypt(encrypted_data.encode()).decode()
            raise ValueError("Legacy Fernet payload cannot be decrypted with this key format")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Decryption failed. Check key integrity.")

# Global instance
encryption_service = EncryptionService()
