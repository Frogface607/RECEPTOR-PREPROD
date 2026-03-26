"""
Encryption utilities for sensitive data (API keys, passwords).
Uses Fernet symmetric encryption from the cryptography library.
"""

import os
import logging
from base64 import urlsafe_b64encode
from hashlib import sha256
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Derive Fernet key from ENCRYPTION_KEY env var.
    If not set, falls back to JWT_SECRET_KEY (not ideal but better than plaintext).
    """
    raw_key = os.getenv("ENCRYPTION_KEY") or os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_me")
    # Fernet requires a 32-byte url-safe base64-encoded key
    # Derive one from the raw secret using SHA-256
    derived = sha256(raw_key.encode()).digest()
    return urlsafe_b64encode(derived)


_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_encryption_key())
    return _fernet


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    if not plaintext:
        return plaintext
    try:
        return _get_fernet().encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a previously encrypted value. Returns plaintext string."""
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Value might be stored in plaintext (pre-encryption migration)
        logger.warning("Failed to decrypt value — returning as-is (possibly plaintext from before encryption was enabled)")
        return ciphertext
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise


def is_encrypted(value: str) -> bool:
    """Check if a value looks like a Fernet-encrypted token."""
    if not value:
        return False
    try:
        _get_fernet().decrypt(value.encode())
        return True
    except (InvalidToken, Exception):
        return False
