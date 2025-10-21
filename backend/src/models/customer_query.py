"""
Customer query model.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class CustomerQuery(BaseModel):
    """Represents a customer's question or request to the assistant."""
    
    query_id: str = Field(..., description="Unique identifier for this query")
    session_id: str = Field(..., description="Links to chat session")
    message: str = Field(..., description="Customer's question/message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When query was submitted")
    context: Optional[str] = Field(None, description="Previous conversation context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional query metadata")
    
    @validator('query_id')
    def validate_query_id(cls, v):
        """Validate that query_id is a valid UUID format."""
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('query_id must be a valid UUID')
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate that session_id is a valid identifier."""
        if not v or not v.strip():
            raise ValueError('session_id must be non-empty')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        """Validate that message is non-empty and under 1000 characters."""
        if not v or not v.strip():
            raise ValueError('Message must be non-empty')
        if len(v) > 1000:
            raise ValueError('Message must be under 1000 characters')
        return v.strip()
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context if provided."""
        if v is not None and not v.strip():
            return None
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
