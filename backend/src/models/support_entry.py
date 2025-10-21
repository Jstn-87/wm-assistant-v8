"""
Support database entry model.
"""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, validator


class SupportEntry(BaseModel):
    """Represents a single support topic from the WM support database."""
    
    id: str = Field(..., description="Unique identifier for the support entry")
    title: str = Field(..., description="Human-readable title")
    category: str = Field(..., description="Support category")
    keywords: List[str] = Field(..., description="Search keywords for matching")
    content: str = Field(..., description="Full support content/instructions")
    url: Optional[str] = Field(None, description="Optional URL for additional information")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When entry was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When entry was last updated")
    
    @validator('id')
    def validate_id(cls, v):
        """Validate that ID is URL-safe."""
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('ID must be URL-safe (alphanumeric, hyphens, underscores only)')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate that title is non-empty."""
        if not v or not v.strip():
            raise ValueError('Title must be non-empty')
        return v.strip()
    
    @validator('category')
    def validate_category(cls, v):
        """Validate that category is one of the defined support categories."""
        valid_categories = {
            'Service Changes', 'Container Guidelines', 'Safety & Health',
            'Additional Services', 'Billing', 'Service Issues', 'Recycling', 'Service Questions'
        }
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {", ".join(valid_categories)}')
        return v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate that keywords list is not empty."""
        if not v or len(v) == 0:
            raise ValueError('Keywords must contain at least one keyword')
        return [keyword.strip() for keyword in v if keyword.strip()]
    
    @validator('content')
    def validate_content(cls, v):
        """Validate that content is non-empty and provides actionable information."""
        if not v or not v.strip():
            raise ValueError('Content must be non-empty')
        if len(v.strip()) < 10:
            raise ValueError('Content must provide actionable information (minimum 10 characters)')
        return v.strip()
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format if provided."""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
