# wsgi.py - Place this file in your project root

# First, apply monkey patching before any other imports
import eventlet
eventlet.monkey_patch()

# Import logging to capture any issues during startup
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Eventlet monkey patching applied")

# Import the application after monkey patching
from app import app as application

# Configure SQLAlchemy to work better with eventlet
try:
    with application.app_context():
        # Use NullPool for SQLAlchemy to avoid threading issues with eventlet
        from sqlalchemy.pool import NullPool
        from flask_sqlalchemy import SQLAlchemy
        from database import db
        
        # Get the engine options from the app config
        engine_options = application.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
        
        # Add NullPool to the options
        engine_options['poolclass'] = NullPool
        
        # Update the app config
        application.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
        
        logger.info("SQLAlchemy configured with NullPool for eventlet compatibility")
except Exception as e:
    logger.exception("Error configuring SQLAlchemy: %s", e)

# This is required for Gunicorn to find the application
if __name__ == "__main__":
    # This block will only execute when running this file directly
    # When running through Gunicorn, Gunicorn will import the 'application' variable
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), application)