"""
Configuration settings for the realtime chat application.
"""

class Config:
    """Base configuration class."""
    SECRET_KEY = 'your-secret-key'  # In production, use environment variable
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Message settings
    MESSAGE_TIMESTAMP_FORMAT = '%H:%M:%S'
    
    # Room settings
    DEFAULT_ROOM = 'general'

# Create instance of config for import
config = Config()
