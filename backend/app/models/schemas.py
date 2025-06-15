from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class Message(BaseModel):
    """Chat message model."""
    id: Optional[str] = None                      
    session_id: Optional[str] = None
    chat_id: Optional[str] = None
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: datetime


# OpenAI Usage models to handle the new API response structure
class CompletionTokensDetails(BaseModel):
    """Details about completion tokens."""
    accepted_prediction_tokens: Optional[int] = 0
    audio_tokens: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0
    rejected_prediction_tokens: Optional[int] = 0


class PromptTokensDetails(BaseModel):
    """Details about prompt tokens."""
    audio_tokens: Optional[int] = 0
    cached_tokens: Optional[int] = 0


class Usage(BaseModel):
    """OpenAI API usage information."""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    # TODO: Check if this is needed
    completion_tokens_details: Optional[CompletionTokensDetails] = None
    prompt_tokens_details: Optional[PromptTokensDetails] = None


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    messages: List[Message]
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(1000, gt=0, le=8192)
    stream: Optional[bool] = False
    session_id: Optional[str] = None  # Changed to str for consistency


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    message: Message
    model: str
    usage: Optional[Usage] = None
    session_id: Optional[str] = None  # Changed to str for consistency


# Session models
class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    created_at: datetime
    last_active: datetime
    message_count: int
    title: Optional[str] = None
    user_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str  # Changed to str for consistency
    created: bool = True


class SessionHistoryResponse(BaseModel):
    """Response model for retrieving session chat history."""
    session_id: str  # Changed to str for consistency
    title: Optional[str] = None
    messages: List[Message]
    created_at: datetime
    last_active: datetime


# RAG models
class RAGRequest(ChatRequest):
    """Request model for RAG-enhanced chat (for future use)."""
    query: str
    use_rag: bool = True


# Voice models
class VoiceRequest(BaseModel):
    """Request model for voice transcription (for future use)."""
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = "en"


class TranscriptionResponse(BaseModel):
    """Response model for voice transcription (for future use)."""
    text: str
    confidence: Optional[float] = None 