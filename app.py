"""
Main application entry point for the realtime chat application.
"""
from flask import Flask
from flask_socketio import SocketIO

# Import configuration
from config import config
from extensions import socketio

def create_app(socketio):
    """
    Application factory function to create and configure the Flask app.
    This is useful for testing and for creating multiple app instances.
    """
    # Initialize Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # Register blueprints
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    # Initialize SocketIO with the app
    socketio.init_app(app)

    # Import and register socket handlers AFTER app initialization
    # This avoids circular imports
    with app.app_context():
        from sockets.handlers import register_socket_handlers
        register_socket_handlers(socketio)

    return app

# Create the Flask application
app = create_app(socketio)

if __name__ == '__main__':
    print("Starting chat server...")
    print(f"Server running on http://{config.HOST}:{config.PORT}")
    socketio.run(
        app,
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        allow_unsafe_werkzeug=True
    )