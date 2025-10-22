"""
Chat API endpoints for WM Assistant.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..models.customer_query import CustomerQuery
from ..models.assistant_response import AssistantResponse
from ..services.support_db_service import SupportDBService
# from ..services.rag_service import RAGService  # Temporarily disabled
from ..services.openai_service import OpenAIService
from ..config import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])

# Global services (will be injected from main.py)
support_db_service = None
# rag_service = None  # Temporarily disabled
openai_service = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="Customer's question or message")
    context: str = Field(None, description="Previous conversation context")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response_id: str = Field(..., description="Unique response identifier")
    query_id: str = Field(..., description="Original query identifier")
    content: str = Field(..., description="Generated response content")
    sources: list[str] = Field(..., description="IDs of support entries used")
    urls: list[str] = Field(default_factory=list, description="URLs found in response content")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in response accuracy")
    response_time_ms: int = Field(..., ge=0, description="Response generation time in milliseconds")
    timestamp: str = Field(..., description="Response generation timestamp")


@router.post("/chat", response_model=ChatResponse)
async def submit_chat_message(request: ChatRequest) -> ChatResponse:
    """Submit a chat message and receive a response from WM Assistant."""
    start_time = datetime.utcnow()
    
    try:
        # Generate unique IDs
        query_id = str(uuid.uuid4())
        response_id = str(uuid.uuid4())
        
        # Create customer query object
        customer_query = CustomerQuery(
            query_id=query_id,
            session_id=request.session_id,
            message=request.message,
            context=request.context
        )
        
        logger.info(f"Processing chat message: {request.message[:50]}...")
        
        # Initialize services if needed
        if not openai_service.is_initialized():
            if not openai_service.initialize():
                raise HTTPException(status_code=500, detail="Failed to initialize OpenAI service")
        
        # Get similar entries using keyword search (RAG temporarily disabled)
        logger.info(f"Searching for: '{request.message}'")
        similar_entries = support_db_service.search_entries(request.message, limit=3)
        logger.info(f"Found {len(similar_entries)} similar entries")
        similar_entries = [(entry, 0.5) for entry in similar_entries]  # Default confidence
        
        # Generate context for OpenAI
        context = ""
        sources = []
        urls = []
        
        if similar_entries:
            context_parts = []
            for entry, score in similar_entries:
                # Build enhanced context with V2 metadata
                context_entry = f"Title: {entry.title}\nContent: {entry.content}"
                
                # Add action links if available
                if hasattr(entry, 'action_links') and entry.action_links:
                    action_links_text = []
                    for link_name, link_url in entry.action_links.items():
                        if link_url.startswith('http'):
                            action_links_text.append(f"{link_name}: {link_url}")
                        else:
                            action_links_text.append(f"{link_name}: {link_url}")
                    if action_links_text:
                        context_entry += f"\nAction Links: {', '.join(action_links_text)}"
                
                # Add policy notes if available
                if hasattr(entry, 'policy_notes') and entry.policy_notes:
                    context_entry += f"\nPolicy Notes: {'; '.join(entry.policy_notes)}"
                
                context_parts.append(context_entry)
                sources.append(entry.id)
                if entry.url:
                    urls.append(entry.url)
            context = "\n\n".join(context_parts)
        
        # Parse conversation history from context
        conversation_history = []
        if request.context:
            try:
                import json
                conversation_history = json.loads(request.context)
            except:
                pass
        
        # Generate response using OpenAI
        openai_response = openai_service.generate_response(
            query=request.message,
            context=context,
            conversation_history=conversation_history
        )
        
        # Calculate confidence score based on similarity scores
        confidence_score = 0.0
        if similar_entries:
            confidence_score = max(score for _, score in similar_entries)
        
        # If no relevant context found, lower confidence
        if not context:
            confidence_score = 0.1
            # Provide a default response when no context is found
            if not openai_response.get("content"):
                openai_response["content"] = "I understand you're asking about moving services. While I don't have specific information about your exact situation, I'd be happy to help you with general WM service questions. Could you provide more details about what you need help with?"
        
        # Calculate response time
        response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Create assistant response
        assistant_response = AssistantResponse(
            response_id=response_id,
            query_id=query_id,
            content=openai_response["content"],
            sources=sources,
            urls=urls,
            confidence_score=confidence_score,
            response_time_ms=response_time_ms
        )
        
        logger.info(f"Generated response in {response_time_ms}ms with confidence {confidence_score:.2f}")
        
        return ChatResponse(
            response_id=response_id,
            query_id=query_id,
            content=assistant_response.content,
            sources=assistant_response.sources,
            urls=assistant_response.urls,
            confidence_score=assistant_response.confidence_score,
            response_time_ms=assistant_response.response_time_ms,
            timestamp=assistant_response.timestamp.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chat/health")
async def chat_health_check():
    """Health check for chat service."""
    try:
        health_status = {
            "status": "healthy",
            "services": {
                "support_db": support_db_service.is_loaded(),
                "rag_service": rag_service.is_initialized(),
                "openai_service": openai_service.is_initialized()
            },
            "support_entries": support_db_service.get_entry_count(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check if all services are healthy
        all_healthy = all(health_status["services"].values())
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
