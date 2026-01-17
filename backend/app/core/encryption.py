"""Encryption utilities for sensitive data."""
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


def get_fernet() -> Fernet:
    """Get Fernet instance with the configured encryption key."""
    key = current_app.config.get('ENCRYPTION_KEY')
    if not key:
        raise EncryptionError("ENCRYPTION_KEY not configured")

    # Ensure key is properly formatted
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise EncryptionError(f"Invalid encryption key: {e}")


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using Fernet symmetric encryption.

    Args:
        password: Plain text password to encrypt

    Returns:
        Base64-encoded encrypted password string
    """
    if not password:
        return ""

    f = get_fernet()
    encrypted = f.encrypt(password.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_password(encrypted: str) -> str:
    """
    Decrypt a password that was encrypted with encrypt_password.

    Args:
        encrypted: Base64-encoded encrypted password string

    Returns:
        Plain text password

    Raises:
        EncryptionError: If decryption fails
    """
    if not encrypted:
        return ""

    try:
        f = get_fernet()
        decrypted = f.decrypt(encrypted.encode('utf-8'))
        return decrypted.decode('utf-8')
    except InvalidToken:
        raise EncryptionError("Failed to decrypt password - invalid token or key")
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt password: {e}")
