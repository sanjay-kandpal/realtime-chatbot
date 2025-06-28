"""
HTTP routes for the chat application.
"""
from flask import Blueprint, render_template

# Create a Blueprint for main routes

# Create a Blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')
