"""
WM Assistant FastAPI application entry point.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.services.support_db_service import SupportDBService
# from src.services.rag_service import RAGService  # Temporarily disabled due to dependency issues
from src.services.openai_service import OpenAIService
from src.api.chat_endpoints import router as chat_router
from src.api.health_endpoints import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Global services
support_db_service = SupportDBService()
# rag_service = RAGService()  # Temporarily disabled
openai_service = OpenAIService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting WM Assistant application...")
    
    # Initialize services
    if not support_db_service.initialize_database():
        logger.error("Failed to initialize support database")
        raise RuntimeError("Support database initialization failed")
    
    # Initialize RAG service (temporarily disabled)
    # if not rag_service.initialize():
    #     logger.error("Failed to initialize RAG service")
    #     raise RuntimeError("RAG service initialization failed")
    
    # Add support entries to vector database (temporarily disabled)
    # entries = support_db_service.get_all_entries()
    # if entries:
    #     if not rag_service.add_support_entries(entries):
    #         logger.warning("Failed to add some entries to vector database")
    
    # Initialize OpenAI service
    if not openai_service.initialize():
        logger.error("Failed to initialize OpenAI service")
        raise RuntimeError("OpenAI service initialization failed")
    
    logger.info("WM Assistant application started successfully")
    
    yield
    
    logger.info("Shutting down WM Assistant application...")


# Create FastAPI app
app = FastAPI(
    title="WM Assistant API",
    description="AI-powered chatbot for WM customer support queries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject services into routers
from src.api import chat_endpoints, health_endpoints
chat_endpoints.support_db_service = support_db_service
chat_endpoints.openai_service = openai_service
health_endpoints.support_db_service = support_db_service
health_endpoints.openai_service = openai_service

# Include routers
app.include_router(chat_router)
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "WM Assistant API", "version": "1.0.0"}




@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "timestamp": None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
