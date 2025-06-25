from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected users and their rooms
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    user_sid = request.sid
    if user_sid in users:
        username = users[user_sid]['username']
        room = users[user_sid]['room']
        leave_room(room)
        del users[user_sid]
        # Notify the room that the user has disconnected
        emit('message', {
            'username': 'System',
            'message': f'{username} has left the chat.',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=room)
        # Update user status to offline
        emit('user_status', {'username': username, 'status': 'offline'}, room=room)
        print(f'User {username} left room {room}')

@socketio.on('join')
def on_join(data):
    username = data.get('username')
    room = data.get('room', 'general')
    
    # Store user info
    users[request.sid] = {
        'username': username,
        'room': room
    }
    
    join_room(room)
    emit('message', {
        'username': 'System',
        'message': f'{username} has joined the room.',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }, room=room)
    
    # Notify others in the room
    emit('user_status', {'username': username, 'status': 'online'}, room=room)
    print(f'User {username} joined room {room}')

@socketio.on('message')
def handle_message(data):
    user_sid = request.sid
    if user_sid in users:
        user = users[user_sid]
        message_data = {
            'username': user['username'],
            'message': data['message'],
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        emit('message', message_data, room=user['room'])

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
