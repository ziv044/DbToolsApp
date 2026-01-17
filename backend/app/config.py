import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Encryption key for sensitive data (passwords, etc.)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production-32b=')

    # System database (tenant registry)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:1234@localhost:5432/dbtools_system'
    )

    # Tenant database settings
    TENANT_DB_HOST = os.environ.get('TENANT_DB_HOST', 'localhost')
    TENANT_DB_PORT = os.environ.get('TENANT_DB_PORT', '5432')
    TENANT_DB_USER = os.environ.get('TENANT_DB_USER', 'postgres')
    TENANT_DB_PASSWORD = os.environ.get('TENANT_DB_PASSWORD', '1234')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Valid Fernet key for testing
    ENCRYPTION_KEY = 'vuDxq9ufVa4rOLfsGuFpIpM8BqDjTQTHXWsu3DqK_P4='


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
