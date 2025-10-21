"""
Vercel serverless function for WM Assistant API.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Import our application components
from src.api.chat_endpoints import router as chat_router
from src.api.health_endpoints import router as health_router
from src.services.support_db_service import SupportDBService
from src.services.openai_service import OpenAIService

# Create FastAPI app
app = FastAPI(
    title="WM Assistant API",
    description="AI-powered customer support assistant for Waste Management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
support_db_service = SupportDBService()
openai_service = OpenAIService()

# Initialize services
support_db_service.initialize_database()
openai_service.initialize()

# Inject services into routers
from src.api import chat_endpoints, health_endpoints
chat_endpoints.support_db_service = support_db_service
chat_endpoints.openai_service = openai_service
health_endpoints.support_db_service = support_db_service
health_endpoints.openai_service = openai_service

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(health_router, prefix="/api", tags=["health"])

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html file."""
    frontend_file = Path(__file__).parent.parent / "frontend" / "public" / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    return {"message": "WM Assistant API is running"}

# Serve static files
@app.get("/{path:path}")
async def serve_static(path: str):
    """Serve static files from frontend."""
    frontend_dir = Path(__file__).parent.parent / "frontend" / "public"
    file_path = frontend_dir / path
    
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    
    # If not found, serve index.html for SPA routing
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return {"error": "File not found"}

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler."""
    return app(request.scope, request.receive, request.send)
