"""
Socket.IO event handlers for the chat application.
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from datetime import datetime

# Import the shared instances using relative imports to avoid circular imports
from models.user import user_manager  # Changed from app.models.user
from config import config  # Changed from app.config

def register_socket_handlers(socketio):
    """Register all socket event handlers."""
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected:', request.sid)

    @socketio.on('disconnect')
    def handle_disconnect():
        user_sid = request.sid
        user_data = user_manager.remove_user(user_sid)
        
        if not user_data:
            return
            
        username = user_data['username']
        room = user_data['room']
        username_lower = user_data['username_lower']
        
        print(f"User {username} (sid: {user_sid}) is disconnecting...")
        leave_room(room)
        
        print(f"User {username} fully disconnected. Active users: {user_manager.active_usernames}")
        
        # Notify the room that the user has disconnected
        emit('message', {
            'username': 'System',
            'message': f'{username} has left the chat.',
            'timestamp': datetime.now().strftime(config.MESSAGE_TIMESTAMP_FORMAT)
        }, room=room)
        
        # Update user status to offline
        emit('user_status', {
            'username': username,
            'status': 'offline'
        }, room=room)
        
        print(f'User {username} left room {room}')

    @socketio.on('join')
    def on_join(data):
        username = data.get('username')
        room = data.get('room', config.DEFAULT_ROOM)
        
        # Add user to the system
        username_lower = user_manager.add_user(request.sid, username, room)
        
        join_room(room)
        
        # Debug print
        print(f"User {username} (sid: {request.sid}) joined room {room}")
        print(f"Current active users: {user_manager.active_usernames}")
        
        # Check for any buffered messages
        buffered_messages = user_manager.get_offline_messages(username)
        if buffered_messages:
            print(f"Found {len(buffered_messages)} buffered messages for {username}")
            for msg in buffered_messages:
                print(f"Delivering buffered message to {username}: {msg}")
                emit('message', msg, room=request.sid)
        
        # Notify room about the new user
        emit('message', {
            'username': 'System',
            'message': f'{username} has joined the room.',
            'timestamp': datetime.now().strftime(config.MESSAGE_TIMESTAMP_FORMAT)
        }, room=room)
        
        # Update user status to online
        emit('user_status', {
            'username': username,
            'status': 'online'
        }, room=room)
        
        print(f'User {username} joined room {room}')

    @socketio.on('message')
    def handle_message(data):
        user_sid = request.sid
        user_data = user_manager.get_user(user_sid)
        
        if not user_data:
            return
            
        sender_username = user_data['username']
        room = user_data['room']
        message = data.get('message', '').strip()
        
        print(f"Message from {sender_username} in room {room}: {message}")
        
        # Check if it's a direct message (format: @username message)
        if message.startswith('@'):
            # Extract the target username and message
            parts = message[1:].split(' ', 1)
            if len(parts) == 2:
                target_username, message_content = parts
                current_time = datetime.now().strftime(config.MESSAGE_TIMESTAMP_FORMAT)
                
                # Create the message data
                message_data = {
                    'username': sender_username,
                    'message': f'(to {target_username}): {message_content}',
                    'timestamp': current_time,
                    'is_private': True
                }
                
                # Check if target is online
                target_user = user_manager.get_user_by_username(target_username)
                
                if target_user:
                    # Send to target user
                    emit('message', message_data, room=target_user['sid'])
                    # Also send to sender
                    emit('message', message_data, room=user_sid)
                else:
                    # Buffer the message for when the user comes online
                    user_manager.add_offline_message(target_username, {
                        'username': sender_username,
                        'message': f'(Private): {message_content}',
                        'timestamp': current_time,
                        'is_private': True
                    })
                    # Notify sender that the message is buffered
                    emit('message', {
                        'username': 'System',
                        'message': f'User {target_username} is offline. Message will be delivered when they come online.',
                        'timestamp': current_time
                    }, room=user_sid)
                return
        
        # Regular message to the room
        message_data = {
            'username': sender_username,
            'message': message,
            'timestamp': datetime.now().strftime(config.MESSAGE_TIMESTAMP_FORMAT),
            'is_private': False
        }
        emit('message', message_data, room=room)