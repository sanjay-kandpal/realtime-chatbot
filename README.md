# Real-Time Chat Application

A real-time messaging application built with Flask and WebSocket using Flask-SocketIO.

## Features

- Real-time messaging between users
- Private direct messaging with @mentions
- User status (online/offline) notifications
- Multiple chat rooms support
- Offline message buffering
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
- To send a private message, use @username followed by your message (e.g., `@UserB Hello!`)
- The chat supports multiple users in the same room
- User status (online/offline) is shown at the top of the chat
- Messages to offline users will be delivered when they come back online

## Project Structure

```
realtime_chat/
├── app.py              # Main application entry point
├── config.py           # Application configuration
├── requirements.txt    # Python dependencies
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── models/
│   └── user.py        # User management and session handling
├── routes/
│   └── main.py        # HTTP route handlers
└── sockets/
    └── handlers.py    # WebSocket event handlers
```

## Configuration

Configuration settings can be modified in `config.py`. Available options include:

- `SECRET_KEY`: Secret key for session management
- `DEBUG`: Enable/disable debug mode
- `HOST`: Host address to bind the server to
- `PORT`: Port to run the server on
- `MESSAGE_TIMESTAMP_FORMAT`: Format for message timestamps
- `DEFAULT_ROOM`: Default chat room name

## Development

To run the application in development mode with auto-reload:

```bash
FLASK_APP=app.py FLASK_ENV=development python -m flask run
```

## Testing

To test the application:

1. Open multiple browser windows or use incognito mode
2. Connect with different usernames
3. Test public messages, private messages, and offline message delivery
4. Verify user status updates when users connect/disconnect

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
- `templates/index.html` - Frontend HTML/CSS/JavaScript
- `requirements.txt` - Python dependencies

## License

This project is open source and available under the MIT License.
