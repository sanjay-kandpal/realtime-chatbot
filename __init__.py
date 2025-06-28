"""
Realtime Chat Application Package

This package provides a real-time chat application using Flask and Socket.IO.
"""

# This file makes the directory a Python package
# Import the create_app function to make it available when importing the package
from .app import create_app

__all__ = ['create_app']
