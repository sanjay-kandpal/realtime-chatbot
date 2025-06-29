import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
from app import app, socketio

# Gunicorn will use socketio to handle the app
