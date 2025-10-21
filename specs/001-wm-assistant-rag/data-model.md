# Data Model: WM Assistant AI Chatbot

**Feature**: 001-wm-assistant-rag  
**Date**: 2024-10-20  
**Purpose**: Define data structures and relationships for the WM Assistant system

## Core Entities

### Support Database Entry

**Purpose**: Represents a single support topic from the WM support database

```python
class SupportEntry:
    id: str                    # Unique identifier (e.g., "moving-transfer-service")
    title: str                 # Human-readable title
    category: str              # Support category (Service Changes, Billing, etc.)
    keywords: List[str]        # Search keywords for matching
    content: str               # Full support content/instructions
    url: str                   # Optional URL for additional information
    embedding: Optional[Vector] # Vector embedding for semantic search
    created_at: datetime       # When entry was created
    updated_at: datetime       # When entry was last updated
```

**Validation Rules**:
- `id` must be unique and URL-safe
- `title` must be non-empty and descriptive
- `category` must be one of the 8 defined support categories
- `keywords` must contain at least one keyword
- `content` must be non-empty and provide actionable information
- `url` must be valid URL format if provided

**State Transitions**:
- Created → Active (when first added to database)
- Active → Updated (when content is modified)
- Active → Archived (when no longer relevant)

### Customer Query

**Purpose**: Represents a customer's question or request to the assistant

```python
class CustomerQuery:
    query_id: str              # Unique identifier for this query
    session_id: str            # Links to chat session
    message: str               # Customer's question/message
    timestamp: datetime        # When query was submitted
    context: Optional[str]     # Previous conversation context
    metadata: Dict[str, Any]   # Additional query metadata
```

**Validation Rules**:
- `query_id` must be unique UUID
- `session_id` must be valid session identifier
- `message` must be non-empty and under 1000 characters
- `timestamp` must be valid datetime
- `context` must be valid JSON if provided

### Assistant Response

**Purpose**: Represents the assistant's response to a customer query

```python
class AssistantResponse:
    response_id: str           # Unique identifier for this response
    query_id: str              # Links to original customer query
    content: str               # Generated response content
    sources: List[str]         # IDs of support entries used
    urls: List[str]            # URLs found in response content
    confidence_score: float    # Confidence in response accuracy (0-1)
    response_time_ms: int      # Time taken to generate response
    timestamp: datetime        # When response was generated
    metadata: Dict[str, Any]   # Additional response metadata
```

**Validation Rules**:
- `response_id` must be unique UUID
- `query_id` must reference valid customer query
- `content` must be non-empty and under 5000 characters
- `content` should be conversational and under 200 words for optimal user experience
- `sources` must contain valid support entry IDs
- `confidence_score` must be between 0 and 1
- `response_time_ms` must be positive integer

### Chat Session

**Purpose**: Represents a conversation session between customer and assistant

```python
class ChatSession:
    session_id: str            # Unique session identifier
    created_at: datetime       # When session started
    last_activity: datetime    # Last interaction timestamp
    message_count: int         # Number of messages in session
    context: List[Dict]        # Conversation history
    user_agent: Optional[str]  # Browser/client information
    metadata: Dict[str, Any]   # Session metadata
```

**Validation Rules**:
- `session_id` must be unique UUID
- `created_at` must be valid datetime
- `last_activity` must be after `created_at`
- `message_count` must be non-negative integer
- `context` must be valid list of message objects

## Data Relationships

### Primary Relationships

1. **ChatSession → CustomerQuery** (1:N)
   - One session can have multiple queries
   - Each query belongs to exactly one session

2. **CustomerQuery → AssistantResponse** (1:1)
   - Each query generates exactly one response
   - Each response corresponds to exactly one query

3. **SupportEntry → AssistantResponse** (1:N)
   - One support entry can be used in multiple responses
   - Each response can reference multiple support entries

### Data Flow

```
SupportEntry (source) → RAG Retrieval → CustomerQuery → AssistantResponse
     ↓                        ↓              ↓              ↓
  Embedding              Similarity      Context        Generated
  Storage                Search          Processing     Response
```

## Data Storage Strategy

### Support Database
- **Format**: JSON file (`support_database.json`)
- **Location**: `backend/support_database.json`
- **Updates**: Version-controlled, manual updates
- **Backup**: Git versioning, regular backups

### Vector Embeddings
- **Format**: ChromaDB collection
- **Location**: In-memory during runtime
- **Updates**: Regenerated when support database changes
- **Persistence**: Optional disk persistence for performance

### Session Data
- **Format**: Frontend localStorage
- **Location**: Browser storage
- **Updates**: Real-time during conversation
- **Persistence**: Client-side only, no server storage

### Logs and Analytics
- **Format**: Structured JSON logs
- **Location**: Backend logging system
- **Updates**: Real-time during interactions
- **Retention**: Configurable retention period

## Data Validation

### Input Validation
- All user inputs sanitized and validated
- Support database entries validated on load
- API requests validated against schemas

### Data Integrity
- Referential integrity between entities
- Consistent data formats across system
- Regular validation of support database accuracy

### Privacy Compliance
- No personal information stored
- Session data client-side only
- Logs contain no customer PII
- GDPR/CCPA compliant data handling

## Performance Considerations

### Caching Strategy
- Support database cached in memory
- Embeddings cached for fast retrieval
- Response caching for similar queries

### Scalability
- Stateless design supports horizontal scaling
- Vector search optimized for performance
- API rate limiting prevents overload

### Monitoring
- Response time tracking
- Query volume monitoring
- Error rate tracking
- System health metrics
