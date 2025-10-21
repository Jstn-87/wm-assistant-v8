"""
Assistant response model.
"""
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator


class AssistantResponse(BaseModel):
    """Represents the assistant's response to a customer query."""
    
    response_id: str = Field(..., description="Unique identifier for this response")
    query_id: str = Field(..., description="Links to original customer query")
    content: str = Field(..., description="Generated response content")
    sources: List[str] = Field(..., description="IDs of support entries used")
    urls: List[str] = Field(default_factory=list, description="URLs found in response content")
    confidence_score: float = Field(..., description="Confidence in response accuracy (0-1)")
    response_time_ms: int = Field(..., description="Time taken to generate response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When response was generated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")
    
    @validator('response_id')
    def validate_response_id(cls, v):
        """Validate that response_id is a valid UUID format."""
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('response_id must be a valid UUID')
        return v
    
    @validator('query_id')
    def validate_query_id(cls, v):
        """Validate that query_id is a valid UUID format."""
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError('query_id must be a valid UUID')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate that content is non-empty and under 5000 characters."""
        if not v or not v.strip():
            raise ValueError('Content must be non-empty')
        if len(v) > 5000:
            raise ValueError('Content must be under 5000 characters')
        return v.strip()
    
    @validator('sources')
    def validate_sources(cls, v):
        """Validate that sources contain valid support entry IDs."""
        # Allow empty sources list for cases where no relevant entries are found
        if v is None:
            return []
        return [source.strip() for source in v if source.strip()]
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Validate that confidence score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v
    
    @validator('response_time_ms')
    def validate_response_time_ms(cls, v):
        """Validate that response time is positive."""
        if v < 0:
            raise ValueError('Response time must be positive')
        return v
    
    @validator('urls')
    def validate_urls(cls, v):
        """Validate URL format if provided."""
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid URL format: {url}')
        return v
    
    def get_word_count(self) -> int:
        """Get the word count of the response content."""
        return len(self.content.split())
    
    def is_conversational_length(self, max_words: int = 200) -> bool:
        """Check if response is within conversational length limits."""
        return self.get_word_count() <= max_words
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
