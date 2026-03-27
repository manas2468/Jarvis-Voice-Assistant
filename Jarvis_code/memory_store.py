import os
from datetime import datetime
from typing import List, Dict, Union
import logging
from mem0 import MemoryClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationMemory:
    """Handles persistent conversation memory for users using Mem0 cloud storage"""
    
    def __init__(self, user_id: str, mem0_api_key: str = None):
        self.user_id = user_id
        
        # Initialize Mem0 client
        api_key = mem0_api_key or os.getenv("MEM0_API_KEY")
        if not api_key:
            raise ValueError("Mem0 API key is required. Set MEM0_API_KEY environment variable or pass it to constructor")
        
        self.memory_client = MemoryClient(api_key=api_key)
        logger.info(f"ConversationMemory initialized for user: {user_id} with Mem0 cloud storage")
    
    def load_memory(self) -> List[Dict]:
        """Load all past conversations for this user from Mem0"""
        try:
            # Get all memories for this user
            memories = self.memory_client.get_all(user_id=self.user_id)
            
            conversations = []
            if memories:
                for memory in memories.get('results', []):
                    # Extract metadata which contains our conversation info
                    metadata = memory.get('metadata', {})
                    if metadata:
                        conversations.append({
                            'memory_id': memory.get('id'),
                            'timestamp': metadata.get('timestamp'),
                            'message_count': metadata.get('message_count', 0),
                            'memory_text': memory.get('memory', ''),
                            'metadata': metadata
                        })
            
            logger.info(f"Loaded {len(conversations)} conversations from Mem0 for user {self.user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error loading memory from Mem0: {e}")
            return []
    
    def _conversation_exists(self, new_conversation: Union[Dict, List], existing_conversations: List[Dict]) -> bool:
        """Check if a conversation already exists in memory"""
        # Handle both list and dict formats
        if isinstance(new_conversation, list):
            new_timestamp = max([t.get('timestamp', 0) for t in new_conversation if 'timestamp' in t], default=0)
            new_msg_count = sum([len(t.get('messages', [])) for t in new_conversation])
        else:
            new_conv_data = new_conversation.get('model_dump', lambda: new_conversation)()
            new_timestamp = new_conv_data.get('timestamp', 0)
            new_msg_count = len(new_conv_data.get('messages', []))
        
        for existing_conv in existing_conversations:
            existing_timestamp = existing_conv.get('timestamp', 0)
            existing_msg_count = existing_conv.get('message_count', 0)
            
            # Compare by timestamp and message count
            if (abs(float(new_timestamp) - float(existing_timestamp)) < 1.0 and 
                new_msg_count == existing_msg_count):
                return True
        
        return False
    
    def save_conversation(self, conversation: Union[Dict, List, object]) -> bool:
        """Save a conversation to Mem0 cloud storage - returns True if successful"""
        logger.info(f"save_conversation called for user {self.user_id}")
        
        try:
            # Convert conversation to dict/list if it's an object with model_dump method
            if hasattr(conversation, 'model_dump'):
                conversation_data = conversation.model_dump()
            else:
                conversation_data = conversation
            
            # Handle list format (array of conversation turns)
            if isinstance(conversation_data, list):
                all_messages = []
                
                # Extract all messages from all conversation turns
                for turn in conversation_data:
                    messages_in_turn = turn.get('messages', [])
                    all_messages.extend(messages_in_turn)
                
                # Use the latest timestamp
                latest_timestamp = max([turn.get('timestamp', 0) for turn in conversation_data if 'timestamp' in turn], default=None)
                timestamp = datetime.fromtimestamp(latest_timestamp).isoformat() if latest_timestamp else datetime.now().isoformat()
                
            # Handle dict format (single conversation)
            else:
                all_messages = conversation_data.get('messages', [])
                timestamp = conversation_data.get('timestamp')
                if not timestamp:
                    timestamp = datetime.now().isoformat()
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp).isoformat()
            
            if not all_messages:
                logger.warning("No messages found in conversation, skipping save")
                return False
            
            # Format messages for Mem0 - filter only user and assistant messages with actual content
            formatted_messages = []
            for msg in all_messages:
                msg_type = msg.get('type', 'message')
                role = msg.get('role', 'user')
                content = msg.get('content', [])
                
                # Skip non-message types (like agent_handoff)
                if msg_type != 'message':
                    continue
                
                # Handle content as array or string
                if isinstance(content, list):
                    # Join all content items into a single string
                    content_str = ' '.join([str(c) for c in content if c])
                else:
                    content_str = str(content) if content else ''
                
                # Only add messages with actual content
                if content_str and content_str.strip():
                    formatted_messages.append({
                        "role": role,
                        "content": content_str.strip()
                    })
            
            if not formatted_messages:
                logger.warning("No valid messages with content to save")
                return False
            
            logger.info(f"Formatted {len(formatted_messages)} messages for Mem0")
            
            # Add memory to Mem0
            result = self.memory_client.add(
                messages=formatted_messages,
                user_id=self.user_id,
                metadata={
                    "timestamp": timestamp,
                    "message_count": len(formatted_messages),
                    "total_turns": len(conversation_data) if isinstance(conversation_data, list) else 1
                }
            )
            
            logger.info(f"Successfully saved conversation to Mem0 for user {self.user_id}")
            logger.info(f"Mem0 result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation to Mem0: {e}")
            logger.exception("Full traceback:")
            return False
    

    
    def get_recent_context(self, max_messages: int = 30) -> List[Dict]:
        """Get recent conversation context for the agent"""
        memory = self.load_memory()
        all_messages = []
        
        # Flatten all conversations into a single message list
        for conversation in memory:
            if "messages" in conversation:
                all_messages.extend(conversation["messages"])
        
        # Return the most recent messages
        recent_messages = all_messages[-max_messages:] if all_messages else []
        logger.info(f"Retrieved {len(recent_messages)} recent messages for user {self.user_id}")
        return recent_messages
    
    def get_conversation_count(self) -> int:
        """Get total number of saved conversations"""
        memory = self.load_memory()
        return len(memory)
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """Search through conversation memories using semantic search"""
        try:
            results = self.memory_client.search(
                query=query,
                user_id=self.user_id,
                limit=limit
            )
            logger.info(f"Found {len(results)} memories matching query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def get_all_memories(self) -> List[Dict]:
        """Get all memories for the user"""
        try:
            memories = self.memory_client.get_all(user_id=self.user_id)
            logger.info(f"Retrieved {len(memories)} total memories for user {self.user_id}")
            return memories
        except Exception as e:
            logger.error(f"Error retrieving all memories: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID"""
        try:
            self.memory_client.delete(memory_id=memory_id)
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    def clear_all_memories(self) -> bool:
        """Clear all memories for this user"""
        try:
            self.memory_client.delete_all(user_id=self.user_id)
            logger.info(f"Cleared all memories for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False