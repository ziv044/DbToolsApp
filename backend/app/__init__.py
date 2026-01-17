import os
from flask import Flask

from app.config import config
from app.extensions import db, migrate, cors


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "X-Tenant-Slug"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })

    # Import models to ensure they're registered with SQLAlchemy
    from app import models  # noqa: F401

    # Register blueprints
    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # Initialize tenant middleware
    from app.middleware import TenantMiddleware
    TenantMiddleware(app)

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return {'status': 'healthy'}

    return app
