# Real-Time Chat Application

A real-time messaging application built with Flask and WebSocket using Flask-SocketIO.

## Features

- Real-time messaging between users
- User status (online/offline) notifications
- Multiple chat rooms support
- Simple and responsive UI

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository or download the source code
2. Navigate to the project directory
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the server:

```bash
python app.py
```

2. Open your web browser and navigate to:
   - User A: `http://localhost:5000?username=UserA`
   - User B: `http://localhost:5000?username=UserB`

3. Start chatting in real-time!

## Usage

- Enter a username when prompted (or use the one in the URL)
- Type your message in the input field and press Enter or click Send
- The chat supports multiple users in the same room
- User status (online/offline) is shown at the top of the chat

## Project Structure

- `app.py` - Main Flask application with WebSocket handlers
- `templates/index.html` - Frontend HTML/CSS/JavaScript
- `requirements.txt` - Python dependencies

## License

This project is open source and available under the MIT License.
