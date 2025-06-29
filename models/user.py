"""
User and session management for the chat application.
"""
from collections import defaultdict
import time
class UserManager:
    """
    Manages users, their sessions, offline messages, and conversations.
    
    Data Structures:
    - users: {socket_id: {'username': str, 'room': str, 'username_lower': str}}
    - offline_messages: {username: [message1, message2, ...]}
    - username_to_sid: {username: socket_id} (case-insensitive)
    - active_usernames: set of lowercase usernames
    - conversations: {
        'user1_user2': [
            {'from': 'user1', 'to': 'user2', 'message': '...', 'timestamp': '...', 'delivered': bool},
            ...
        ]
    }
    """
    
    def __init__(self):
        self.users = {}  # Active users by socket ID
        self.offline_messages = defaultdict(list)  # Messages for offline users
        self.username_to_sid = {}  # Username to socket ID mapping
        self.active_usernames = set()  # Set of active usernames (lowercase)
        self.conversations = defaultdict(list)  # Stores conversation history between users
    
    def add_user(self, sid, username, room):
        """
        Add a new user to the system.
        
        Args:
            sid: Socket ID
            username: User's display name
            room: Room name
            
        Returns:
            str: Lowercase username
        """
        username_lower = username.lower()
        
        # If user exists with different socket ID, clean up old connection
        old_sid = self.username_to_sid.get(username_lower)
        if old_sid and old_sid in self.users:
            # Transfer any undelivered messages to the new connection
            old_user_data = self.users[old_sid]
            if 'undelivered_messages' in old_user_data:
                undelivered = old_user_data.get('undelivered_messages', [])
                self.offline_messages[username_lower].extend(undelivered)
        
        # Add/update user
        self.users[sid] = {
            'username': username,
            'room': room,
            'username_lower': username_lower,
            'undelivered_messages': [],
            'last_seen': time.time()
        }
        
        # Update username to socket_id mapping
        self.username_to_sid[username] = sid
        self.username_to_sid[username_lower] = sid
        self.active_usernames.add(username_lower)
        
        # Deliver any pending messages
        self._deliver_pending_messages(username_lower, sid)
        
        return username_lower
    
    def remove_user(self, sid):
        """
        Remove a user from the system.
        
        Args:
            sid: Socket ID of the user to remove
            
        Returns:
            dict: Removed user's data or None if not found
        """
        if sid not in self.users:
            return None
            
        user_data = self.users[sid]
        username = user_data['username']
        username_lower = user_data.get('username_lower', username.lower())
        room = user_data['room']
        
        # Store undelivered messages
        if 'undelivered_messages' in user_data and user_data['undelivered_messages']:
            self.offline_messages[username_lower].extend(user_data['undelivered_messages'])
        
        # Clean up user data
        if username in self.username_to_sid:
            del self.username_to_sid[username]
        if username_lower in self.username_to_sid:
            del self.username_to_sid[username_lower]
        if username_lower in self.active_usernames:
            self.active_usernames.remove(username_lower)
        
        # Remove from users
        del self.users[sid]
        
        return {
            'username': username,
            'room': room,
            'username_lower': username_lower
        }
    
    def get_user(self, sid):
        """Get user data by socket ID."""
        return self.users.get(sid)
    
    def get_user_by_username(self, username):
        """Get user data by username (case-insensitive)."""
        username_lower = username.lower()
        if username_lower not in self.active_usernames:
            return None
            
        sid = self.username_to_sid.get(username_lower)
        return self.users.get(sid) if sid else None
    
    def add_offline_message(self, target_username, message):
        """
        Add a message for an offline user.
        
        Args:
            target_username: Username of the recipient
            message: Message data to store
            
        Returns:
            bool: True if message was stored, False if user is online
        """
        username_lower = target_username.lower()
        
        # If user is online but not in the same room, store as undelivered
        if username_lower in self.active_usernames:
            target_sid = self.username_to_sid.get(username_lower)
            if target_sid and target_sid in self.users:
                user_data = self.users[target_sid]
                if 'undelivered_messages' not in user_data:
                    user_data['undelivered_messages'] = []
                user_data['undelivered_messages'].append(message)
                return True
            return False
            
        # Store the message for when user comes online
        if username_lower not in self.offline_messages:
            self.offline_messages[username_lower] = []
            
        self.offline_messages[username_lower].append(message)
        return True
    
    def _deliver_pending_messages(self, username_lower, sid):
        """Deliver any pending messages to a user who just came online."""
        if username_lower in self.offline_messages and self.offline_messages[username_lower]:
            messages = self.offline_messages[username_lower].copy()
            self.offline_messages[username_lower] = []
            
            # Add to undelivered messages for the user
            if sid in self.users and 'undelivered_messages' in self.users[sid]:
                self.users[sid]['undelivered_messages'].extend(messages)
            return messages
        return []
    
    def get_offline_messages(self, username):
        """
        Get and clear offline messages for a user.
        
        Args:
            username: Username to get messages for
            
        Returns:
            list: List of pending messages for the user
        """
        username_lower = username.lower()
        
        # Get messages from offline storage
        messages = []
        if username_lower in self.offline_messages:
            messages = self.offline_messages[username_lower].copy()
            self.offline_messages[username_lower] = []
            
        # Get undelivered messages if user is online
        if username_lower in self.active_usernames:
            sid = self.username_to_sid.get(username_lower)
            if sid and sid in self.users and 'undelivered_messages' in self.users[sid]:
                messages.extend(self.users[sid]['undelivered_messages'])
                self.users[sid]['undelivered_messages'] = []
                
        return messages
        
    def add_to_conversation(self, sender, recipient, message_data):
        """
        Add a message to the conversation history between two users.
        
        Args:
            sender: Username of the sender
            recipient: Username of the recipient
            message_data: Message data to store
            
        Returns:
            str: Conversation ID
        """
        # Create a consistent conversation ID (alphabetical order)
        user1, user2 = sorted([sender.lower(), recipient.lower()])
        conv_id = f"{user1}_{user2}"
        
        # Add to conversation history
        self.conversations[conv_id].append({
            'from': sender,
            'to': recipient,
            'message': message_data['message'],
            'timestamp': message_data.get('timestamp', time.time()),
            'delivered': False
        })
        
        return conv_id
        
    def get_conversation(self, user1, user2):
        """
        Get conversation history between two users.
        
        Args:
            user1: First username
            user2: Second username
            
        Returns:
            list: Conversation history
        """
        user1, user2 = sorted([user1.lower(), user2.lower()])
        conv_id = f"{user1}_{user2}"
        return self.conversations.get(conv_id, []).copy()
        
    def mark_messages_delivered(self, sender, recipient, before_time=None):
        """
        Mark messages as delivered in a conversation.
        
        Args:
            sender: Username of the message sender
            recipient: Username of the message recipient
            before_time: Only mark messages before this timestamp as delivered
        """
        user1, user2 = sorted([sender.lower(), recipient.lower()])
        conv_id = f"{user1}_{user2}"
        
        if conv_id in self.conversations:
            for msg in self.conversations[conv_id]:
                if msg['from'].lower() == sender.lower() and msg['to'].lower() == recipient.lower():
                    if before_time is None or msg.get('timestamp', 0) <= before_time:
                        msg['delivered'] = True
        
    def get_online_users(self, room=None):
        """
        Get list of online users, optionally filtered by room.
        
        Args:
            room: Optional room to filter users by
            
        Returns:
            list: List of online users
        """
        if room:
            return [u for u in self.users.values() if u.get('room') == room]
        return list(self.users.values())
        
    def is_user_online(self, username):
        """
        Check if a user is currently online.
        
        Args:
            username: Username to check
            
        Returns:
            bool: True if user is online, False otherwise
        """
        return username.lower() in self.active_usernames
    
    def is_username_taken(self, username):
        """Check if a username is already in use (case-insensitive)."""
        return username.lower() in self.active_usernames

# Create a single instance of UserManager
user_manager = UserManager()
