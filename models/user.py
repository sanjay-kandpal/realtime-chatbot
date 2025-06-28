"""
User and session management for the chat application.
"""
from collections import defaultdict

class UserManager:
    """Manages users, their sessions, and offline messages."""
    
    def __init__(self):
        # {socket_id: {'username': str, 'room': str, 'username_lower': str}}
        self.users = {}
        # {username: [list of messages]}
        self.offline_messages = defaultdict(list)
        # {username: socket_id} (stores both original and lowercase usernames)
        self.username_to_sid = {}
        # Set of lowercase usernames for case-insensitive checks
        self.active_usernames = set()
    
    def add_user(self, sid, username, room):
        """Add a new user to the system."""
        username_lower = username.lower()
        
        self.users[sid] = {
            'username': username,
            'room': room,
            'username_lower': username_lower
        }
        
        # Update username to socket_id mapping
        self.username_to_sid[username] = sid
        self.username_to_sid[username_lower] = sid
        self.active_usernames.add(username_lower)
        
        return username_lower
    
    def remove_user(self, sid):
        """Remove a user from the system."""
        if sid not in self.users:
            return None
            
        user_data = self.users[sid]
        username = user_data['username']
        username_lower = user_data.get('username_lower', username.lower())
        room = user_data['room']
        
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
        """Add a message for an offline user."""
        username_lower = target_username.lower()
        self.offline_messages[username_lower].append(message)
    
    def get_offline_messages(self, username):
        """Get and clear offline messages for a user."""
        username_lower = username.lower()
        messages = self.offline_messages.get(username_lower, []).copy()
        if username_lower in self.offline_messages:
            self.offline_messages[username_lower] = []
        return messages
    
    def is_username_taken(self, username):
        """Check if a username is already in use (case-insensitive)."""
        return username.lower() in self.active_usernames

# Create a single instance of UserManager
user_manager = UserManager()
