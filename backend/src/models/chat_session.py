"""
Chat session model.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class ChatSession(BaseModel):
    """Represents a conversation session between customer and assistant."""
    
    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When session started")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last interaction timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")
    context: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    user_agent: Optional[str] = Field(None, description="Browser/client information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate that session_id is a valid identifier."""
        if not v or not v.strip():
            raise ValueError('session_id must be non-empty')
        return v.strip()
    
    @validator('last_activity')
    def validate_last_activity(cls, v, values):
        """Validate that last_activity is after created_at."""
        if 'created_at' in values and v < values['created_at']:
            raise ValueError('last_activity must be after created_at')
        return v
    
    @validator('message_count')
    def validate_message_count(cls, v):
        """Validate that message count is non-negative."""
        if v < 0:
            raise ValueError('message_count must be non-negative')
        return v
    
    @validator('context')
    def validate_context(cls, v):
        """Validate that context is a valid list of message objects."""
        if not isinstance(v, list):
            raise ValueError('context must be a list')
        return v
    
    def add_message(self, role: str, content: str, timestamp: Optional[datetime] = None) -> None:
        """Add a message to the conversation context."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp.isoformat()
        }
        
        self.context.append(message)
        self.message_count += 1
        self.last_activity = timestamp
    
    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation context."""
        return self.context[-limit:] if self.context else []
    
    def clear_context(self) -> None:
        """Clear conversation context."""
        self.context = []
        self.message_count = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
