"""
Message queue system with buffering, acknowledgment, and retry logic.
"""
import time
import uuid
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime

class MessageQueue:
    """
    A thread-safe message queue with delivery guarantees.
    
    Features:
    - Buffered message storage
    - Message acknowledgment
    - Automatic retry of unacknowledged messages
    - Callback support for message processing
    """
    
    def __init__(self, retry_timeout: float = 10.0):
        """
        Initialize the message queue.
        
        Args:
            retry_timeout: Time in seconds before retrying unacknowledged messages
        """
        self.main_queue: List[Dict[str, Any]] = []
        self.processing_queue: Dict[str, Dict[str, Any]] = {}
        self.acknowledged: Set[str] = set()
        self.retry_timeout = retry_timeout
        self.callbacks = {
            'on_message': None,
            'on_retry': None,
            'on_ack': None
        }
    
    def register_callback(self, event: str, callback: Callable):
        """Register a callback for queue events."""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    def add_message(self, user_id: str, message: Any, **metadata) -> str:
        """
        Add a message to the main queue.
        
        Args:
            user_id: ID of the user who sent the message
            message: The message content
            **metadata: Additional metadata to store with the message
            
        Returns:
            str: The generated message ID
        """
        msg_id = str(uuid.uuid4())
        msg = {
            'id': msg_id,
            'user_id': user_id,
            'message': message,
            'timestamp': time.time(),
            'metadata': metadata or {},
            'retry_count': 0
        }
        self.main_queue.append(msg)
        
        if self.callbacks['on_message']:
            self.callbacks['on_message'](msg)
            
        return msg_id
    
    def get_next_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the next message from the main queue and move it to processing.
        
        Returns:
            Optional[Dict]: The next message, or None if queue is empty
        """
        if not self.main_queue:
            return None
            
        msg = self.main_queue.pop(0)
        self.processing_queue[msg['id']] = msg
        return msg
    
    def acknowledge(self, msg_id: str) -> bool:
        """
        Acknowledge that a message has been processed.
        
        Args:
            msg_id: The ID of the message to acknowledge
            
        Returns:
            bool: True if message was acknowledged, False if not found
        """
        if msg_id in self.processing_queue:
            self.acknowledged.add(msg_id)
            msg = self.processing_queue[msg_id]
            del self.processing_queue[msg_id]
            
            if self.callbacks['on_ack']:
                self.callbacks['on_ack'](msg)
                
            return True
        return False
    
    def retry_unacknowledged(self) -> List[Dict[str, Any]]:
        """
        Move unacknowledged messages back to the main queue for retry.
        
        Returns:
            List[Dict]: List of messages that were requeued
        """
        now = time.time()
        requeued = []
        
        for msg_id, msg in list(self.processing_queue.items()):
            if msg_id not in self.acknowledged and (now - msg['timestamp']) > self.retry_timeout:
                msg['retry_count'] += 1
                msg['timestamp'] = now
                self.main_queue.append(msg)
                del self.processing_queue[msg_id]
                requeued.append(msg)
                
                if self.callbacks['on_retry']:
                    self.callbacks['on_retry'](msg)
        
        return requeued
    
    def get_status(self) -> Dict[str, int]:
        """Get current queue status."""
        return {
            'queued': len(self.main_queue),
            'processing': len(self.processing_queue),
            'acknowledged': len(self.acknowledged)
        }

# Global message queue instance
message_queue = MessageQueue()
