"""
Configuration management for WM Assistant.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="test-key-for-development", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    openai_max_tokens: int = Field(default=1000, description="Maximum tokens for OpenAI responses")
    
    # Application Configuration
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8001, description="API port")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit for requests per minute")
    rate_limit_tokens_per_minute: int = Field(default=40000, description="Rate limit for tokens per minute")
    
    # Vector Database
    vector_db_persist_dir: str = Field(default="./data/vectordb", description="Vector database persistence directory")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model")
    
    # Support Database
    support_database_path: str = Field(default="./support_database.json", description="Path to support database JSON file")
    
    # Response Configuration
    max_response_length: int = Field(default=200, description="Maximum response length in words")
    conversational_tone: bool = Field(default=True, description="Enable conversational tone")
    enable_followup_questions: bool = Field(default=True, description="Enable follow-up questions")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
