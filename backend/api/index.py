"""
Vercel serverless function entry point for WM Assistant API.
"""
import os
import sys
from pathlib import Path

# Add the backend src directory to Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import our application components
from src.api.chat_endpoints import chat_router
from src.api.health_endpoints import health_router
from src.services.support_db_service import SupportDBService
from src.services.openai_service import OpenAIService
from src.services.rag_service import RAGService

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
rag_service = RAGService()
openai_service = OpenAIService()

# Initialize services
support_db_service.initialize_database()
openai_service.initialize()

# Inject services into routers
chat_router.support_db_service = support_db_service
chat_router.rag_service = rag_service
chat_router.openai_service = openai_service

health_router.support_db_service = support_db_service
health_router.rag_service = rag_service
health_router.openai_service = openai_service

# Include routers
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(health_router, prefix="/api", tags=["health"])

# Serve static files from frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "public"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html file."""
    frontend_file = Path(__file__).parent.parent.parent / "frontend" / "public" / "index.html"
    if frontend_file.exists():
        return FileResponse(str(frontend_file))
    return {"message": "WM Assistant API is running"}

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler."""
    return app(request.scope, request.receive, request.send)
