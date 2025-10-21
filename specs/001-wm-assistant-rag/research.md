# Research: WM Assistant AI Chatbot

**Feature**: 001-wm-assistant-rag  
**Date**: 2024-10-20  
**Purpose**: Resolve technical decisions and validate architecture choices

## Research Tasks & Findings

### 1. RAG Implementation with ChatGPT 4o mini

**Task**: Research RAG implementation patterns for customer support chatbots using OpenAI API

**Decision**: Use hybrid RAG approach with semantic search + generation
- **Rationale**: 
  - Semantic search ensures responses are grounded in support database
  - ChatGPT 4o mini provides natural language generation capabilities
  - Hybrid approach balances accuracy with conversational quality
- **Alternatives considered**:
  - Pure retrieval (too rigid, poor user experience)
  - Pure generation (risks hallucination, violates constitution)
  - Fine-tuned models (expensive, requires large datasets)

**Implementation Pattern**:
1. Embed support database entries using sentence-transformers
2. Store embeddings in ChromaDB for fast similarity search
3. Retrieve top-k relevant entries for user query
4. Use retrieved context with ChatGPT 4o mini for response generation
5. Validate response contains only information from retrieved context

### 2. Vector Database Selection

**Task**: Evaluate vector database options for embedding storage and retrieval

**Decision**: Use ChromaDB for local embedding storage
- **Rationale**:
  - Lightweight, easy to deploy
  - Good performance for small to medium datasets
  - No external dependencies or costs
  - Supports similarity search and filtering
- **Alternatives considered**:
  - Pinecone (overkill for this scale, additional cost)
  - Weaviate (complex setup, external dependency)
  - FAISS (lower-level, requires more implementation)

### 3. Embedding Model Selection

**Task**: Choose appropriate embedding model for support content

**Decision**: Use sentence-transformers/all-MiniLM-L6-v2
- **Rationale**:
  - Good balance of performance and speed
  - Works well with short text (support entries)
  - Fast inference for real-time queries
  - Proven track record for semantic search
- **Alternatives considered**:
  - OpenAI embeddings (additional API cost, latency)
  - Larger models (slower inference, overkill for this use case)

### 4. API Rate Limiting Strategy

**Task**: Design rate limiting to stay within ChatGPT API limits

**Decision**: Implement token-based rate limiting with caching
- **Rationale**:
  - Prevents API quota exhaustion
  - Caching reduces redundant API calls
  - Token counting ensures accurate usage tracking
- **Implementation**:
  - Track tokens per user session
  - Cache responses for similar queries
  - Implement exponential backoff for rate limit errors
  - Graceful degradation when limits exceeded

### 5. Frontend-Backend Communication

**Task**: Design API communication patterns for chat interface

**Decision**: RESTful API with WebSocket for real-time updates
- **Rationale**:
  - RESTful endpoints for chat submission
  - WebSocket for streaming responses (if needed)
  - Simple, well-understood patterns
  - Easy to test and debug
- **API Design**:
  - POST /api/chat for message submission
  - GET /api/health for system status
  - WebSocket /ws/chat for real-time updates (optional)

### 6. URL Processing and Clickable Links

**Task**: Design system for making URLs clickable in responses

**Decision**: Backend URL detection + frontend link rendering
- **Rationale**:
  - Backend identifies URLs in support content
  - Frontend renders as clickable links
  - Separation of concerns maintains clean architecture
- **Implementation**:
  - Backend: Extract URLs from support database content
  - Backend: Mark URLs in response with special formatting
  - Frontend: Parse marked URLs and render as clickable links
  - Frontend: Open links in new tab for better UX

### 7. Error Handling and Graceful Degradation

**Task**: Design error handling for API failures and edge cases

**Decision**: Multi-level fallback strategy
- **Rationale**:
  - Ensures system remains functional during failures
  - Provides helpful error messages to users
  - Maintains WM's customer service standards
- **Fallback Levels**:
  1. Primary: RAG + ChatGPT 4o mini
  2. Secondary: Direct keyword matching in support database
  3. Tertiary: Generic helpful message (no "contact customer service")
  4. Final: System maintenance message

### 8. Session Management

**Task**: Design conversation context and session handling

**Decision**: Stateless backend with frontend session management
- **Rationale**:
  - Aligns with constitution requirement for stateless architecture
  - Simplifies scaling and deployment
  - Frontend manages conversation history
- **Implementation**:
  - Frontend stores conversation history in localStorage
  - Backend receives conversation context with each request
  - No server-side session storage
  - Context included in RAG retrieval for better responses

### 9. Conversational Design and Response Strategy

**Task**: Design conversational flow and response length management

**Decision**: Brevity-first approach with strategic follow-up questions
- **Rationale**:
  - Maintains user engagement through conversational flow
  - Avoids overwhelming users with verbose responses
  - Enables more targeted assistance through follow-up questions
  - Aligns with modern chat interface expectations
- **Implementation**:
  - Target response length: under 200 words for 90% of queries
  - Use follow-up questions for complex topics to break down information
  - Maintain conversational tone rather than formal documentation style
  - Ask clarifying questions when queries are ambiguous or multi-faceted

## Technical Decisions Summary

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend Framework | FastAPI | Fast, modern, good async support |
| Vector Database | ChromaDB | Lightweight, local, good performance |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 | Fast, accurate, cost-effective |
| AI Model | ChatGPT 4o mini | Cost-effective, good quality |
| Frontend | Vanilla JS/HTML/CSS | Simple, no framework overhead |
| API Pattern | RESTful + WebSocket | Standard, well-understood |
| Session Management | Stateless + Frontend storage | Scalable, constitution-compliant |

## Validation Results

All technical decisions align with constitution requirements:
- ✅ Knowledge Base Integrity: RAG ensures grounding in support database
- ✅ Performance & Reliability: <3s response time achievable with chosen stack
- ✅ Privacy & Security: Stateless design, minimal data retention
- ✅ Architecture Requirements: Clear API boundaries, comprehensive logging
- ✅ Scope Discipline: Limited to support database content only
