"""Tests for encryption utilities."""
import pytest
from cryptography.fernet import Fernet

from app.core.encryption import encrypt_password, decrypt_password, EncryptionError


class TestEncryption:
    """Tests for password encryption/decryption."""

    def test_encrypt_password(self, app):
        """Test that password encryption returns a different value."""
        with app.app_context():
            password = "my-secret-password"
            encrypted = encrypt_password(password)

            assert encrypted != password
            assert len(encrypted) > 0

    def test_decrypt_password(self, app):
        """Test that decryption returns original password."""
        with app.app_context():
            password = "my-secret-password"
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)

            assert decrypted == password

    def test_encrypt_empty_password(self, app):
        """Test encrypting empty string returns empty string."""
        with app.app_context():
            assert encrypt_password("") == ""

    def test_decrypt_empty_password(self, app):
        """Test decrypting empty string returns empty string."""
        with app.app_context():
            assert decrypt_password("") == ""

    def test_different_passwords_different_ciphertext(self, app):
        """Test that different passwords produce different ciphertexts."""
        with app.app_context():
            encrypted1 = encrypt_password("password1")
            encrypted2 = encrypt_password("password2")

            assert encrypted1 != encrypted2

    def test_same_password_different_ciphertext(self, app):
        """Test that same password produces different ciphertext each time (due to random IV)."""
        with app.app_context():
            password = "my-password"
            encrypted1 = encrypt_password(password)
            encrypted2 = encrypt_password(password)

            # Fernet uses random IV, so encrypting same password should produce different ciphertext
            assert encrypted1 != encrypted2

            # But both should decrypt to the same value
            assert decrypt_password(encrypted1) == password
            assert decrypt_password(encrypted2) == password

    def test_decrypt_invalid_token_raises_error(self, app):
        """Test that decrypting invalid token raises EncryptionError."""
        with app.app_context():
            with pytest.raises(EncryptionError):
                decrypt_password("invalid-encrypted-data")

    def test_unicode_password(self, app):
        """Test encryption of unicode passwords."""
        with app.app_context():
            password = "пароль123"  # Russian for "password"
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)

            assert decrypted == password

    def test_special_characters_password(self, app):
        """Test encryption of passwords with special characters."""
        with app.app_context():
            password = "p@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)

            assert decrypted == password
