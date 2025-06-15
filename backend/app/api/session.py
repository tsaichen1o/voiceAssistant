from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import SessionResponse, SessionHistoryResponse, Message, SessionInfo
from app.services.session_service import create_session, get_session, update_session, delete_session, get_all_sessions, get_cache_stats
from app.services.chat_service import get_session_history
from app.utils.supabase_auth import verify_supabase_token
from datetime import datetime
from typing import List, Dict, Any


router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
)

@router.get("", response_model=List[SessionInfo])
async def get_all_sessions_endpoint(user: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Get all chat sessions.
    
    Returns:
        List of all sessions with basic info
    """
    user_id = user["sub"] 
    sessions_data = get_all_sessions(user_id=user_id)
    
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
async def create_new_session(user: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Create a new chat session.
    
    Returns:
        A SessionResponse with the new session ID
    """
    user_id = user["sub"]
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    session_id = create_session(user_id=user_id)
    return SessionResponse(session_id=session_id, created=True)


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_data(session_id: str, user: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Get data for a specific session, including chat history.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        SessionHistoryResponse with session data and messages
        
    Raises:
        HTTPException: If session not found
    """
    user_id = user["sub"]
    session_data = await get_session_history(session_id, user_id=user_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    # Convert stored messages to Message objects
    messages = [Message(**msg) for msg in session_data["messages"]]
    
    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        created_at=datetime.fromisoformat(session_data["created_at"]),
        last_active=datetime.fromisoformat(session_data["last_active"])
    )


@router.delete("/{session_id}")
async def delete_chat_session(session_id: str, user: Dict[str, Any] = Depends(verify_supabase_token)):
    """
    Delete a chat session.
    
    Args:
        session_id: The session ID to delete
        
    Returns:
        Status message
        
    Raises:
        HTTPException: If session not found
    """
    user_id = user["sub"]
    success = delete_session(session_id, user_id=user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
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
        
        
@router.post("/{session_id}/messages")
async def save_session_messages(
    session_id: str, 
    data: dict,
    user: dict = Depends(verify_supabase_token)
):
    """
    Receives the complete chat history from the frontend and saves it.
    This is called after a stream is complete.
    """
    messages = data.get("messages", [])
    user_id = user.get("sub")

    session = get_session(session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    success = update_session(session_id, messages, user_id=user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update session in database")
        
    return {"message": "Session history saved successfully"}