# Voice Assistant Backend

A FastAPI-based backend service that provides ChatGPT functionality using OpenAI API, with session management and API key authentication.

## Features

- **Text Chat**: Conversation using OpenAI GPT-4o model
- **Session Management**: Create, retrieve, and delete chat sessions
- **Persistent Storage**: PostgreSQL + Redis hybrid architecture
- **API Key Authentication**: Secure access to all endpoints
- **Future Extensions**: Reserved interfaces for RAG and voice features

## Technology Stack

- **Backend Framework**: FastAPI
- **AI Model**: OpenAI GPT-4o
- **Database**: PostgreSQL (persistent storage)
- **Cache**: Redis (session cache and message queue)
- **Authentication**: API Key Bearer Token

## Requirements

- Python 3.10+
- PostgreSQL database
- Redis server
- OpenAI API key

## Installation & Setup

### 1. Install Dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file and configure the following variables:

```env
# Application settings
APP_NAME="Voice Assistant Backend"
DEBUG=True

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# API authentication
API_KEY=your_secure_api_key_here

# Database configuration
DATABASE_URL=postgresql://username:password@localhost:5432/voice_assistant

# Redis configuration
REDIS_URL=redis://localhost:6379
# Or use separate configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### 3. Database Initialization

```bash
# Initialize database tables
python -m app.db.init_db
```

### 4. Start the Service

```bash
# Development mode
python main.py

# Or use uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at http://localhost:8000

## API Endpoints

### Authentication

All endpoints require an API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

### Chat Endpoints

#### POST `/api/chat`
Send a message and get AI response

**Request Body**:
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "session_id": "optional_session_id"
}
```

**Response**:
```json
{
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help you today?"
  },
  "model": "gpt-4o",
  "usage": {...},
  "session_id": "session_uuid"
}
```

### Session Management Endpoints

#### GET `/api/sessions`
Get all session list

#### POST `/api/sessions`
Create a new session

#### GET `/api/sessions/{session_id}`
Get chat history for all sessions or a specific session 

#### DELETE `/api/sessions/{session_id}`
Delete a specific session

#### GET `/api/sessions/stats/cache`
Get cache statistics

### Reserved Endpoints

- `POST /api/chat_rag`: RAG-enhanced chat (in development)
- `POST /api/chat_voice`: Voice chat (in development)

## Project Structure

```
backend/
├── app/
│   ├── api/                # API routes
│   │   ├── chat.py        # Chat endpoints
│   │   └── session.py     # Session management endpoints
│   ├── models/            # Data models
│   │   ├── database.py    # Database models
│   │   └── schemas.py     # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── chat_service.py    # Chat service
│   │   └── session_service.py # Session service
│   ├── utils/             # Utility functions
│   │   ├── auth.py        # Authentication utilities
│   │   └── openai_client.py # OpenAI client
│   ├── db/                # Database related
│   │   ├── connection.py  # Database connection
│   │   └── init_db.py     # Database initialization
│   └── config.py          # Configuration management
├── requirements.txt       # Dependencies
├── main.py               # Application entry point
└── README.md             # Project documentation
```

## Development Notes

### Data Storage Strategy

- **PostgreSQL**: Store session metadata and message history
- **Redis**: Cache active sessions and temporary data

### Future Development

The project has reserved interfaces and structure for the following features:

1. **RAG Functionality**: Document retrieval-augmented generation
2. **Voice Features**: Speech-to-text and text-to-speech
3. **Multi-user Support**: User management and permission control

## API Documentation

After starting the service, you can access the auto-generated API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Monitoring & Debugging

- Health check: `GET /health`
- Cache statistics: `GET /api/sessions/stats/cache`

