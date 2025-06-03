from typing import List, Dict, Any
from app.utils.gemini_client import generate_chat_completion
from app.models.schemas import Message, ChatRequest, ChatResponse, RAGRequest, Usage, CompletionTokensDetails, PromptTokensDetails
from app.config import settings
import google.generativeai as genai
from app.services.session_service import create_session, get_session, update_session

# Configure Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)


async def get_chat_response(request: ChatRequest) -> ChatResponse:
    """
    Process a chat request and return a response from the Gemini model.
    
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
    
    # Initialize Gemini model
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    # Convert messages to Gemini format
    conversation_text = ""
    for message in request.messages:
        if message.role == "user":
            conversation_text += f"User: {message.content}\n"
        elif message.role == "assistant":
            conversation_text += f"Assistant: {message.content}\n"
        elif message.role == "system":
            conversation_text = f"System: {message.content}\n" + conversation_text
    
    # Generate response with Gemini
    response = model.generate_content(
        conversation_text,
        generation_config=genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )
    )
    
    # Extract the response message
    assistant_message = Message(
        role="assistant",
        content=response.text
    )
    
    # Update session with message history
    messages = [m.model_dump() for m in request.messages]
    messages.append(assistant_message.model_dump())
    update_session(session_id, messages)
    
    # Convert usage to our Usage model if available
    usage_data = None
    if response.usage_metadata:
        usage_data = Usage(
            completion_tokens=response.usage_metadata.candidates_token_count,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            total_tokens=response.usage_metadata.total_token_count,
            completion_tokens_details=None,  # Gemini doesn't provide detailed breakdown
            prompt_tokens_details=None
        )
    
    # Return the response
    return ChatResponse(
        message=assistant_message,
        model=settings.GEMINI_MODEL,
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