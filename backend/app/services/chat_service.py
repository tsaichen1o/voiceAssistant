from typing import List, Dict, Any
from app.utils.openai_client import generate_chat_completion
from app.models.schemas import Message, ChatRequest, ChatResponse, RAGRequest, Usage, CompletionTokensDetails, PromptTokensDetails
from app.config import settings
import openai
from app.services.session_service import create_session, get_session, update_session

# Configure OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_chat_response(request: ChatRequest) -> ChatResponse:
    """
    Process a chat request and return a response from the OpenAI model.
    
    Args:
        request: The chat request containing messages and parameters
        
    Returns:
        ChatResponse: The model's response
    """
    # Handle session management
    session_id = request.session_id
    if not session_id:
        # Create a new session if none provided
        session_id = create_session()
    else:
        # Get existing session
        session = get_session(session_id)
        if not session:
            # Create a new session if the provided ID doesn't exist
            session_id = create_session()
    
    # Get OpenAI response
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[m.model_dump() for m in request.messages],
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    # Extract the response message
    assistant_message = Message(
        role="assistant",
        content=response.choices[0].message.content
    )
    
    # Update session with message history
    messages = [m.model_dump() for m in request.messages]
    messages.append(assistant_message.model_dump())
    update_session(session_id, messages)
    
    # Convert usage to our Usage model if available
    usage_data = None
    if response.usage:
        # Handle completion_tokens_details
        completion_details = None
        if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
            completion_details = CompletionTokensDetails(
                accepted_prediction_tokens=getattr(response.usage.completion_tokens_details, 'accepted_prediction_tokens', 0),
                audio_tokens=getattr(response.usage.completion_tokens_details, 'audio_tokens', 0),
                reasoning_tokens=getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0),
                rejected_prediction_tokens=getattr(response.usage.completion_tokens_details, 'rejected_prediction_tokens', 0)
            )
        
        # Handle prompt_tokens_details
        prompt_details = None
        if hasattr(response.usage, 'prompt_tokens_details') and response.usage.prompt_tokens_details:
            prompt_details = PromptTokensDetails(
                audio_tokens=getattr(response.usage.prompt_tokens_details, 'audio_tokens', 0),
                cached_tokens=getattr(response.usage.prompt_tokens_details, 'cached_tokens', 0)
            )
        
        usage_data = Usage(
            completion_tokens=response.usage.completion_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
            completion_tokens_details=completion_details,
            prompt_tokens_details=prompt_details
        )
    
    # Return the response
    return ChatResponse(
        message=assistant_message,
        model=response.model,
        usage=usage_data,
        session_id=session_id
    )


# Placeholder for future RAG-enhanced chat
async def get_rag_chat_response(request: RAGRequest) -> ChatResponse:
    """
    Process a RAG-enhanced chat request.
    This is a placeholder for future RAG implementation.
    
    Args:
        request: The RAG request containing messages, query, and parameters
        
    Returns:
        ChatResponse: The model's response
    """
    # For now, just return a message that this feature is coming soon
    return ChatResponse(
        message=Message(
            role="assistant",
            content="RAG-enhanced chat is coming soon. This feature will allow the model to reference external documents."
        ),
        model="placeholder",
        usage=None
    )


# Placeholder for future voice-related functionality
async def transcribe_audio():
    """Placeholder for future voice transcription functionality."""
    pass


async def get_session_history(session_id: str):
    """
    Retrieve chat history for a session.
    
    Args:
        session_id: The session ID to retrieve history for
        
    Returns:
        dict: The session data including message history
        None: If session not found
    """
    return get_session(session_id) 