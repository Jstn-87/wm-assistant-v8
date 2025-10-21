# Quickstart Guide: WM Assistant AI Chatbot

**Feature**: 001-wm-assistant-rag  
**Date**: 2024-10-20  
**Purpose**: Get the WM Assistant up and running quickly

## Prerequisites

- Python 3.11 or higher
- Node.js 16 or higher (for frontend development)
- OpenAI API key for ChatGPT 4o mini
- Git (for version control)

## Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd WM-Assistant_v8

# Checkout the feature branch
git checkout 001-wm-assistant-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Backend Setup

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key-here"
export ENVIRONMENT="development"

# Initialize the support database
python -c "from src.services.support_db_service import SupportDBService; SupportDBService().initialize_database()"

# Start the backend server
python main.py
```

The backend will start on `http://localhost:8000`

### 3. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Start a simple HTTP server (or use your preferred method)
python -m http.server 3000
# Or: npx serve public
# Or: open public/index.html directly in browser
```

The frontend will be available at `http://localhost:3000`

### 4. Verify Installation

```bash
# Test the API health endpoint
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-10-20T14:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 60,
  "support_database_entries": 150,
  "vector_db_status": "ready"
}
```

## First Chat Interaction

### Using the Web Interface

1. Open `http://localhost:3000` in your browser
2. Type a question like "How do I transfer my service when moving?"
3. Click Send
4. You should receive a helpful response with clickable URLs

### Using the API Directly

```bash
# Send a test message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "message": "What materials are not allowed in my dumpster?",
    "context": null
  }'

# Expected response:
{
  "response_id": "660e8400-e29b-41d4-a716-446655440000",
  "query_id": "770e8400-e29b-41d4-a716-446655440000",
  "content": "Here are some general guidelines of items that are NOT allowed in dumpsters: Aerosol cans, All liquids, Animals, Antifreeze...",
  "sources": ["dumpster-materials-not-allowed"],
  "urls": ["https://www.wm.com/us/en/support/faqs/products-and-services/what-materials-are-not-allowed-in-my-dumpster"],
  "confidence_score": 0.95,
  "response_time_ms": 1250,
  "timestamp": "2024-10-20T14:30:00Z"
}
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1000

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=40000

# Vector Database
VECTOR_DB_PERSIST_DIR=./data/vectordb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Support Database

The support database is located at `backend/support_database.json`. To update it:

1. Edit the JSON file with new support entries
2. Restart the backend server
3. The system will automatically rebuild the vector embeddings

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if implemented)
cd frontend
npm test  # or your preferred test runner
```

### Code Quality

```bash
# Backend linting and formatting
cd backend
black src/ tests/
flake8 src/ tests/
mypy src/

# Frontend linting (if using a build system)
cd frontend
npm run lint
npm run format
```

### Hot Reloading

For development with hot reloading:

```bash
# Backend with auto-reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend with live reload (if using a build system)
cd frontend
npm run dev
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   Error: Invalid API key
   Solution: Verify your OpenAI API key is set correctly in environment variables
   ```

2. **Support Database Not Found**
   ```
   Error: support_database.json not found
   Solution: Ensure the file exists in backend/ directory
   ```

3. **Vector Database Initialization Failed**
   ```
   Error: Failed to initialize vector database
   Solution: Check disk space and permissions for vector database directory
   ```

4. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   Solution: Wait for rate limit to reset or increase rate limits in configuration
   ```

### Logs and Debugging

```bash
# View backend logs
cd backend
tail -f logs/app.log

# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

### Performance Monitoring

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health

# Monitor system resources
htop  # or your preferred system monitor
```

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker build -t wm-assistant .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key wm-assistant
```

### Environment Setup

```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export API_HOST=0.0.0.0
export API_PORT=8000
```

## Next Steps

1. **Customize Responses**: Modify the prompt templates in `src/services/rag_service.py`
2. **Add New Support Content**: Update `support_database.json` with new entries
3. **Enhance Frontend**: Customize the UI in `frontend/public/`
4. **Monitor Performance**: Set up logging and monitoring systems
5. **Scale**: Configure load balancing and horizontal scaling

## Support

For issues or questions:
- Check the logs in `backend/logs/`
- Review the API documentation at `http://localhost:8000/docs`
- Consult the constitution and specification documents
- Contact the development team
