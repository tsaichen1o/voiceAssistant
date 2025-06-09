# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional, AsyncGenerator
from app.utils.gemini_client import generate_chat_completion
from app.models.schemas import Message, ChatRequest, ChatResponse, RAGRequest, Usage, CompletionTokensDetails, PromptTokensDetails
from app.config import settings
import google.generativeai as genai
from app.services.session_service import create_session, get_session, update_session, redis_client
from datetime import datetime, UTC
import uuid
import asyncio
import json


# Configure Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)

async def stream_chat_response(messages: list, stream_id: str) -> AsyncGenerator[str, None]:
    """
    An async generator that streams responses from the Gemini model.
    (Optimized to use structured conversation history)
    """
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # TODO: modify the system prompt to be more specific to the user's request
        system_prompt = """
        You are a helpful assistant. All your responses must be formatted using Markdown.
        - Use headings (##, ###) for main topics.
        - Use bullet points (*) or numbered lists (1.) for lists.
        - Use bold (**) and italics (*) for emphasis.
        - Use code blocks (```) for code snippets.
        - Respond in the user's language.
        - No redundant gap between paragraphs.
        """

        # Build the conversation history for Gemini
        gemini_history = []
        for message in messages:
            # Map our 'assistant' role to Gemini's 'model' role
            role = "model" if message.get('role') == "assistant" else "user"
            gemini_history.append({
                "role": role,
                "parts": [{"text": message.get('content', '')}]
            })
            
        # Add the system prompt as the first part of the conversation
        # A good approach is to add it before the actual conversation content
        # Note: Gemini's conversation must alternate between user/model,
        # so we add the system prompt content before the latest user message
        if gemini_history:
            last_message_content = gemini_history[-1]['parts'][0]['text']
            gemini_history[-1]['parts'][0]['text'] = f"{system_prompt}\n---\n{last_message_content}"

        # Call the API, this time passing in a list of dicts, not a single string
        response_stream = model.generate_content(
            gemini_history,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000,
            )
        )

        for chunk in response_stream:
            if chunk.text:
                data_payload = {"content": chunk.text}
                yield f"data: {json.dumps(data_payload)}\n\n"
                await asyncio.sleep(0.02)

    except Exception as e:
        print(f"Error during stream generation: {e}")
        yield f"data: [error] An error occurred while generating the response.\n\n"
    finally:
        redis_client.delete(f"stream_request:{stream_id}")
        print(f"Cleaned up Redis key for stream: {stream_id}")
        yield "data: [done]\n\n"


async def get_chat_response(request: ChatRequest, user_info: Optional[Dict[str, Any]] = None) -> ChatResponse:
    """
    Process a chat request and return a response from the Gemini model.
    
    Args:
        request: The chat request containing messages and parameters
        user_info: User authentication information (optional for backward compatibility)
        
    Returns:
        ChatResponse: The model's response
    """
    session_id = request.session_id
    user_id = user_info.get("user_id") if user_info else None
    
    if not session_id:
        if user_info and user_info.get("auth_type") == "supabase":
            session_id = create_session(user_id=user_id)
        else:
            session_id = create_session()
    else:
        if user_info and user_info.get("auth_type") == "supabase":
            session = get_session(session_id, user_id=user_id)
        else:
            session = get_session(session_id)
            
        if not session:
            if user_info and user_info.get("auth_type") == "supabase":
                session_id = create_session(user_id=user_id)
            else:
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
    # TODO: add system prompt
    response = model.generate_content(
        conversation_text,
        generation_config=genai.types.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )
    )
    
    # Extract the response message
    assistant_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=response.text,
        created_at=datetime.now(UTC).isoformat()
    )
    
    # Update session with message history - include user context
    messages = [m.model_dump() for m in request.messages]
    messages.append(assistant_message.model_dump())
    
    if user_info and user_info.get("auth_type") == "supabase":
        update_session(session_id, messages, user_id=user_id)
    else:
        update_session(session_id, messages)
    
    # Convert usage to our Usage model if available
    usage_data = None
    if response.usage_metadata:
        usage_data = Usage(
            completion_tokens=response.usage_metadata.candidates_token_count,
            prompt_tokens=response.usage_metadata.prompt_token_count,
            total_tokens=response.usage_metadata.total_token_count,
            completion_tokens_details=None,
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
    # TODO: add system prompt
    session_id = request.session_id or "rag_placeholder_session"
    assistant_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content="RAG-enhanced chat is coming soon. This feature will allow the model to reference external documents.",
        created_at=datetime.now(UTC).isoformat()
    )
    
    return ChatResponse(
        message=assistant_message,
        model="placeholder",
        usage=None,
        session_id=session_id
    )


# Placeholder for future voice-related functionality
async def transcribe_audio():
    """Placeholder for future voice transcription functionality."""
    pass


async def get_session_history(session_id: str, user_id: Optional[str] = None):
    """
    Retrieve chat history for a session.
    
    Args:
        session_id: The session ID to retrieve history for
        user_id: Optional user ID for access control
        
    Returns:
        dict: The session data including message history
        None: If session not found or access denied
    """
    if user_id:
        return get_session(session_id, user_id=user_id)
    else:
        return get_session(session_id) 