# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Union
import uuid
import json

from app.models.schemas import ChatRequest, ChatResponse, RAGRequest, Message
from app.services.chat_service import get_chat_response, stream_chat_response
from app.services.session_service import redis_client
from app.utils.supabase_auth import verify_supabase_token


router = APIRouter(
    prefix="/api",
    tags=["chat"],
)

STREAM_REQUEST_EXPIRY = 300

@router.post("/chat")
async def chat(request: ChatRequest, user_info: Dict[str, Any] = Depends(verify_supabase_token)) -> Union[ChatResponse, Dict]:
    """
    Chat with Gemini model.
    If stream is True, return a stream_id and session_id.
    If stream is False, return a ChatResponse.
    """
    if not request.stream:
        try:
            response = await get_chat_response(request, user_info)
            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        stream_id = str(uuid.uuid4())
        print(f"Set redis: stream_request:{stream_id} = {request.model_dump_json(include={'messages'})}")
        
        redis_client.set(
            f"stream_request:{stream_id}",
            request.model_dump_json(include={'messages'}),
            ex=STREAM_REQUEST_EXPIRY 
        )

        # Endpoint for frontend to connect to the stream
        return {"stream_id": stream_id, "session_id": request.session_id}
    


@router.get("/chat/stream/{stream_id}")
async def chat_stream(stream_id: str, user_info: dict = Depends(verify_supabase_token)):
    """
    Provide Server-Sent Events (SSE) streaming.
    Frontend's EventSource will connect to this endpoint.
    """
    stored_request_data = redis_client.get(f"stream_request:{stream_id}")

    # HTTPException of FastAPI will return JSON (application/json),
    # so the frontend will receive a 404 + json response, instead of an SSE stream.
    async def event_gen():
        if not stored_request_data:
            # yield an SSE formatted error
            yield 'data: [error] Stream request not found, it might have expired.\n\n'
            yield 'data: [done]\n\n'
            return
        request_data = json.loads(stored_request_data)
        messages = request_data.get("messages", [])
        print(f"Fetch redis: stream_request:{stream_id} found = {stored_request_data is not None}")
        async for chunk in stream_chat_response(messages, stream_id):
            if isinstance(chunk, bytes):
                yield chunk.decode('utf-8')
            else:
                yield chunk

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/chat_rag", response_model=ChatResponse)
async def chat_rag(request: RAGRequest, user_info: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Chat with RAG (Retrieval-Augmented Generation).
    This is a placeholder endpoint for the future RAG feature.
    """
    return ChatResponse(
        message=Message(
            role="assistant",
            content="RAG-enhanced chat is coming soon. This feature will allow the model to reference external documents."
        ),
        model="placeholder",
        usage=None
    )


@router.post("/chat_voice")
async def chat_voice(user_info: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Voice chat endpoint.
    This is a placeholder endpoint for the future voice interaction feature.
    """
    return {"message": "Voice chat feature is coming soon"}