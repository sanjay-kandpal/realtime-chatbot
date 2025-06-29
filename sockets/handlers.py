"""
Socket.IO event handlers for the chat application.
"""
import time
from flask import request
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import uuid
# Import the shared instances using relative imports to avoid circular imports
from models.user import user_manager  # Changed from app.models.user
from config import config  # Changed from app.config
from message_queue import message_queue  # Import our message queue

def register_socket_handlers(socketio):
    """Register all socket event handlers."""
    # Set up message queue callbacks
    def on_message(msg):
        print(f"[Queue] New message queued: {msg['id']} from user {msg['user_id']}")
    
    def on_retry(msg):
        print(f"[Queue] Retrying message {msg['id']} (attempt {msg['retry_count']})")
    
    def on_ack(msg):
        print(f"[Queue] Message acknowledged: {msg['id']}")
    
    # Register callbacks
    message_queue.register_callback('on_message', on_message)
    message_queue.register_callback('on_retry', on_retry)
    message_queue.register_callback('on_ack', on_ack)
    
    # Start retry thread
    def retry_loop():
        while True:
            retried = message_queue.retry_unacknowledged()
            if retried:
                print(f"[Queue] Retried {len(retried)} unacknowledged messages")
            time.sleep(5)  # Check every 5 seconds
    
    import threading
    retry_thread = threading.Thread(target=retry_loop, daemon=True)
    retry_thread.start()
    
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
        
        # Get any undelivered messages
        buffered_messages = user_manager.get_offline_messages(username)
        if buffered_messages:
            print(f"Found {len(buffered_messages)} buffered messages for {username}")
            for msg in buffered_messages:
                print(f"Delivering buffered message to {username}: {msg}")
                # Mark as delivered in conversation history
                if msg.get('type') == 'direct':
                    user_manager.mark_messages_delivered(
                        msg.get('username'),  # sender
                        username,  # recipient (current user)
                        before_time=msg.get('timestamp')
                    )
                emit('message', {**msg, 'status': 'delivered'}, room=request.sid)
        
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
        temp_msg_id = data.get('tempId')  # Get the temporary ID from frontend
        
        if not message:
            return
            
        print(f"Message from {sender_username} in room {room}: {message}")
        
        # Create message data with unique ID and metadata
        message_data = {
            'id': str(uuid.uuid4()),  # Generate a unique ID for this message
            'username': sender_username,
            'message': message,
            'timestamp': datetime.now().strftime(config.MESSAGE_TIMESTAMP_FORMAT),
            'room': room,
            'tempId': temp_msg_id,  # Include the frontend's temp ID
            'type': 'direct' if message.startswith('@') else 'broadcast'
        }
        
        # Handle direct messages (starting with @username)
        if message.startswith('@'):
            # Extract target username from message
            parts = message[1:].split(' ', 1)
            if len(parts) == 2:
                target_username, message_content = parts
                
                # Update message content to remove the @username
                message_data['message'] = message_content
                message_data['original_message'] = message
                
                # Add to conversation history
                user_manager.add_to_conversation(
                    sender_username, 
                    target_username, 
                    message_data
                )
                
                # Check if target user is online
                target_sid = user_manager.username_to_sid.get(target_username.lower())
                if target_sid and target_sid in user_manager.users:
                    # Target is online, send directly
                    emit('message', {**message_data, 'status': 'delivered'}, room=target_sid)
                    # Send to sender as well
                    emit('message', {**message_data, 'status': 'delivered'}, room=user_sid)
                else:
                    # Target is offline, store for later
                    user_manager.add_offline_message(target_username, message_data)
                    # Let sender know the message was queued
                    emit('message', {**message_data, 'status': 'queued'}, room=user_sid)
        else:
            # Handle broadcast message to room
            room_users = user_manager.get_online_users(room)
            
            # Send to all online users in the room
            for user in room_users:
                if user['username'] != sender_username:  # Don't send back to sender yet
                    user_sid = user_manager.username_to_sid.get(user['username'].lower())
                    if user_sid:
                        emit('message', {**message_data, 'status': 'delivered'}, room=user_sid)
            
            # Send to sender with delivered status
            emit('message', {**message_data, 'status': 'delivered'}, room=user_sid)
        
        # Send acknowledgment back to sender with the message ID
        if temp_msg_id:
            emit('message_ack', {
                'tempId': temp_msg_id,
                'msgId': message_data['id'],
                'status': 'delivered'
            }, room=user_sid)
        
        print(f"[Message] Sent to {len(online_users)} online users, buffered for {len(offline_users)} offline users")
    
    def process_next_message(room):
        """Process the next message in the queue."""
        msg = message_queue.get_next_message()
        if not msg:
            return
            
        try:
            message_data = msg['message']
            target_room = message_data.get('room', room)
            
            # Get all users in the target room
            room_users = [u for u in user_manager.users.values() if u.get('room') == target_room]
            
            # Send to all online users in the room
            for user in room_users:
                user_sid = next((sid for sid, u in user_manager.users.items() 
                               if u.get('username') == user['username']), None)
                if user_sid:
                    emit('message', {**message_data, 'status': 'delivered'}, room=user_sid)
            
            # Acknowledge the message in the queue
            message_queue.acknowledge(msg['id'])
            print(f"[Queue] Processed message {msg['id']} in room {target_room}")
            
        except Exception as e:
            print(f"[Queue] Error processing message {msg.get('id', 'unknown')}: {str(e)}")
            # The message will be automatically retried if not acknowledged
        
        # Check if it's a direct message (format: @username message)
        if message_data.get('message', '').startswith('@'):
            # Extract the target username and message
            parts = message_data[1:].split(' ', 1)
            logging.info(f"Parts: {parts}")
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