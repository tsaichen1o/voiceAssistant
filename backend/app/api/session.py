from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SessionResponse, SessionHistoryResponse, Message, SessionInfo
from app.services.session_service import create_session, get_session, update_session, delete_session, get_all_sessions, get_cache_stats
from app.services.chat_service import get_session_history
from app.utils.auth import verify_api_key
from datetime import datetime
from typing import List

router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("", response_model=List[SessionInfo])
async def get_all_sessions_endpoint():
    """
    Get all chat sessions.
    
    Returns:
        List of all sessions with basic info
    """
    sessions_data = get_all_sessions()
    
    sessions = []
    for session in sessions_data:
        sessions.append(SessionInfo(
            session_id=session["session_id"],
            created_at=datetime.fromisoformat(session["created_at"]),
            last_active=datetime.fromisoformat(session["last_active"]),
            message_count=session["message_count"],
            title=session["title"],
            user_id=session.get("user_id")
        ))
    
    return sessions


@router.post("", response_model=SessionResponse)
async def create_new_session():
    """
    Create a new chat session.
    
    Returns:
        A SessionResponse with the new session ID
    """
    session_id = create_session()
    return SessionResponse(session_id=session_id, created=True)


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_data(session_id: str):
    """
    Get data for a specific session, including chat history.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        SessionHistoryResponse with session data and messages
        
    Raises:
        HTTPException: If session not found
    """
    session_data = await get_session_history(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert stored messages to Message objects
    messages = [Message(**msg) for msg in session_data["messages"]]
    
    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        created_at=datetime.fromisoformat(session_data["created_at"]),
        last_active=datetime.fromisoformat(session_data["last_active"])
    )


@router.delete("/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        Status message
        
    Raises:
        HTTPException: If session not found
    """
    success = delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}


@router.get("/stats/cache")
async def get_cache_statistics():
    """
    Get Redis cache statistics for monitoring.
    
    Returns:
        Cache statistics including active sessions, memory usage, etc.
    """
    try:
        stats = get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "architecture": "PostgreSQL + Redis Hybrid"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve cache stats: {str(e)}"
        ) 