"""
Health check endpoints for WM Assistant.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.support_db_service import SupportDBService
# from ..services.rag_service import RAGService  # Temporarily disabled
from ..services.openai_service import OpenAIService
from ..config import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["health"])

# Global services
support_db_service = SupportDBService()
# rag_service = RAGService()  # Temporarily disabled
openai_service = OpenAIService()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    uptime_seconds: int = Field(..., description="Service uptime in seconds")
    support_database_entries: int = Field(..., description="Number of support database entries")
    vector_db_status: str = Field(..., description="Vector database status")
    environment: str = Field(..., description="Environment")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check for WM Assistant service."""
    try:
        settings = get_settings()
        start_time = datetime.utcnow()
        
        # Check support database
        db_validation = support_db_service.validate_database()
        db_healthy = db_validation['is_valid']
        
        # Check RAG service (temporarily disabled)
        rag_healthy = True  # rag_service.is_initialized()
        vector_db_status = "disabled"  # "ready" if rag_healthy else "not_initialized"
        
        # Check OpenAI service
        openai_healthy = openai_service.is_initialized()
        
        # Determine overall status
        if db_healthy and rag_healthy and openai_healthy:
            status = "healthy"
        elif db_healthy:  # At least support DB is working
            status = "degraded"
        else:
            status = "unhealthy"
        
        # Calculate uptime (simplified - in production you'd track actual start time)
        uptime_seconds = int((datetime.utcnow() - start_time).total_seconds())
        
        health_response = HealthResponse(
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            support_database_entries=support_db_service.get_entry_count(),
            vector_db_status=vector_db_status,
            environment=settings.environment
        )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service-specific information."""
    try:
        settings = get_settings()
        
        # Support database health
        db_validation = support_db_service.validate_database()
        db_stats = {
            "status": "healthy" if db_validation['is_valid'] else "unhealthy",
            "total_entries": support_db_service.get_entry_count(),
            "categories": db_validation.get('categories', {}),
            "errors": db_validation.get('errors', []),
            "warnings": db_validation.get('warnings', []),
            "last_loaded": support_db_service.get_last_loaded_time().isoformat() if support_db_service.get_last_loaded_time() else None
        }
        
        # RAG service health (temporarily disabled)
        rag_health = {
            "status": "disabled",
            "initialized": False,
            "stats": {"message": "RAG service temporarily disabled due to dependency issues"}
        }
        
        # OpenAI service health
        openai_health = {
            "status": "healthy" if openai_service.is_initialized() else "unhealthy",
            "initialized": openai_service.is_initialized(),
            "model": settings.openai_model,
            "api_key_configured": settings.openai_api_key != "test-key-for-development"
        }
        
        # Overall health
        overall_healthy = (
            db_validation['is_valid'] and 
            rag_service.is_initialized() and 
            openai_service.is_initialized()
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "services": {
                "support_database": db_stats,
                "rag_service": rag_health,
                "openai_service": openai_health
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }


@router.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness check."""
    try:
        # Check if all critical services are ready
        db_ready = support_db_service.is_loaded() and support_db_service.get_entry_count() > 0
        rag_ready = True  # rag_service.is_initialized()  # Temporarily disabled
        openai_ready = openai_service.is_initialized()
        
        all_ready = db_ready and rag_ready and openai_ready
        
        if all_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {
                "status": "not_ready",
                "services": {
                    "support_database": db_ready,
                    "rag_service": rag_ready,
                    "openai_service": openai_ready
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness check."""
    try:
        # Simple check that the service is responding
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not alive")
