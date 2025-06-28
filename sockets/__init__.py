"""
Socket.IO handlers package for the realtime chat application.

This package contains WebSocket event handlers and related functionality.
"""

# Import the register_socket_handlers function to make it available when importing the package
from .handlers import register_socket_handlers

__all__ = ['register_socket_handlers']
