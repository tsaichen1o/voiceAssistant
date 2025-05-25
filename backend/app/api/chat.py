from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, RAGRequest
from app.services.chat_service import get_chat_response, get_rag_chat_response
from app.utils.auth import verify_api_key

router = APIRouter(
    prefix="/api",
    tags=["chat"],
    dependencies=[Depends(verify_api_key)]  # Apply API key auth to all endpoints
)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the OpenAI model.
    
    This endpoint processes a chat request and returns a response from the model.
    """
    try:
        response = await get_chat_response(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat_rag", response_model=ChatResponse)
async def chat_rag(request: RAGRequest):
    """
    Chat with RAG (Retrieval-Augmented Generation).
    
    This is a placeholder endpoint for the future RAG feature.
    Currently returns a message indicating the feature is in development.
    """
    # For now, just return a message that this feature is coming soon
    from app.models.schemas import Message
    
    return ChatResponse(
        message=Message(
            role="assistant",
            content="RAG-enhanced chat is coming soon. This feature will allow the model to reference external documents."
        ),
        model="placeholder",
        usage=None
    )


@router.post("/chat_voice")
async def chat_voice():
    """
    Voice chat endpoint.
    
    This is a placeholder endpoint for the future voice interaction feature.
    Currently returns a message indicating the feature is in development.
    """
    return {"message": "Voice chat feature is coming soon"} 