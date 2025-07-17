from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import asyncio

from app.services.opensource_voice_service import opensource_voice_service
from app.utils.supabase_auth import verify_supabase_token

print("🚀 [OPENSOURCE VOICE] Importing opensource_voice module...")

router = APIRouter(
    prefix="/api/opensource-voice",
    tags=["opensource-voice"],
)

print("✅ [OPENSOURCE VOICE] Router created with prefix /api/opensource-voice")


@router.get("/events/{user_id}")
async def voice_events_stream_opensource(
    user_id: str, 
    is_audio: str = "true",
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Server-Sent Events (SSE) endpoint for opensource voice assistant.
    
    Args:
        user_id: User identifier
        is_audio: Whether to use audio mode ("true" or "false")
        user_info: Authenticated user information
    """
    print(f"🎯 [OPENSOURCE VOICE] GET /events/{user_id} - ENTRY POINT")
    print(f"Voice client {user_id} connecting via OpenSource SSE, audio mode: {is_audio}")
    print(f"✅ Authenticated user: {user_info.get('email', 'unknown')}")
    
    # Authenticate UserID
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    try:
        # Create voice session with opensource service
        is_audio_mode = is_audio.lower() == "true"
        session_data = await opensource_voice_service.create_session(
            user_id=user_id, 
            is_audio=is_audio_mode
        )
        session_id = session_data["session_id"]
        
        async def event_generator():
            try:
                # Send session created event
                yield f"data: {json.dumps({'type': 'session_created', 'session_id': session_id})}\n\n"
                
                # Send initial status message
                status_message = {
                    "type": "text",
                    "data": f"🤖 OpenSource Voice Assistant Ready! Session: {session_id}",
                    "partial": False
                }
                yield f"data: {json.dumps(status_message)}\n\n"
                
                # Heartbeat loop
                last_heartbeat = asyncio.get_event_loop().time()
                heartbeat_interval = 30  # seconds
                
                while True:
                    # Check if session still exists
                    current_session = await opensource_voice_service.get_session(session_id)
                    if not current_session or current_session.get("status") != "active":
                        print(f"📡 Session {session_id} no longer active, ending SSE stream")
                        break
                    
                    # Send heartbeat if needed
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat > heartbeat_interval:
                        heartbeat_event = {
                            "type": "heartbeat",
                            "timestamp": current_session['last_active'],
                            "service": "opensource"
                        }
                        yield f"data: {json.dumps(heartbeat_event)}\n\n"
                        last_heartbeat = current_time
                    
                    # Wait a bit before next check
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error in OpenSource voice SSE stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            finally:
                # Clean up session
                await opensource_voice_service.close_session(session_id)
                print(f"Voice client {user_id} disconnected from OpenSource SSE")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        print(f"Error creating OpenSource voice session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")


@router.post("/send/{session_id}")
async def send_voice_message_opensource(
    session_id: str, 
    request: Request,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    HTTP endpoint for sending messages to the opensource voice assistant.
    
    Args:
        session_id: Session identifier
        request: HTTP request containing the message
        user_info: Authenticated user information
    """
    print(f"🔍 [OPENSOURCE VOICE] POST /send/{session_id} - START")
    print(f"✅ Authenticated user sending OpenSource voice message: {user_info.get('email', 'unknown')}")
    
    try:
        # Parse the message
        print(f"🔍 [OPENSOURCE VOICE] Parsing request JSON...")
        message = await request.json()
        mime_type = message.get("mime_type")
        data = message.get("data")
        print(f"🔍 [OPENSOURCE VOICE] Parsed: mime_type={mime_type}, data_length={len(data) if data else 0}")
        
        if not mime_type or not data:
            print(f"❌ [OPENSOURCE VOICE] Missing mime_type or data")
            raise HTTPException(status_code=400, detail="Missing mime_type or data")
        
        # Verify session exists and belongs to user
        print(f"🔍 [OPENSOURCE VOICE] Verifying session {session_id}...")
        session_data = await opensource_voice_service.get_session(session_id)
        if not session_data:
            print(f"❌ [OPENSOURCE VOICE] Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        print(f"✅ [OPENSOURCE VOICE] Session {session_id} found")
        if session_data.get("user_id") != user_info.get('sub'):
            print(f"❌ [OPENSOURCE VOICE] Session does not belong to user")
            raise HTTPException(status_code=403, detail="Session does not belong to user")
        
        # Stream the response back
        print(f"🔍 [OPENSOURCE VOICE] Starting response stream...")
        async def response_generator():
            try:
                print(f"🔍 [OPENSOURCE VOICE] Calling opensource_voice_service.send_message...")
                async for event_data in opensource_voice_service.send_message(session_id, data, mime_type):
                    print(f"🔍 [OPENSOURCE VOICE] Got event: {event_data}")
                    yield f"data: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(0.01)
                print(f"✅ [OPENSOURCE VOICE] Finished processing events")
            except Exception as e:
                print(f"❌ [OPENSOURCE VOICE] Error in response generator: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        if mime_type == "text/plain":
            print(f"[CLIENT TO OPENSOURCE VOICE] Session {session_id}: {data}")
        elif mime_type == "audio/pcm":
            print(f"[CLIENT TO OPENSOURCE VOICE] Session {session_id}: audio/pcm: {len(data)} chars (base64)")
        
        return StreamingResponse(
            response_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"Error sending OpenSource voice message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/sessions/{user_id}")
async def get_user_opensource_voice_sessions(
    user_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Get all active opensource voice sessions for a user.
    
    Args:
        user_id: User identifier
        user_info: Authenticated user information
    """
    print(f"🔍 [OPENSOURCE VOICE] GET /sessions/{user_id}")
    
    # Authenticate UserID
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    try:
        active_sessions = await opensource_voice_service.list_active_sessions()
        
        # Filter sessions belonging to this user
        user_sessions = []
        for session_id in active_sessions:
            session_data = await opensource_voice_service.get_session(session_id)
            if session_data and session_data.get("user_id") == user_id:
                user_sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "last_active": session_data.get("last_active"),
                    "is_audio": session_data.get("is_audio"),
                    "status": session_data.get("status")
                })
        
        return {"sessions": user_sessions, "count": len(user_sessions)}
        
    except Exception as e:
        print(f"Error getting OpenSource voice sessions for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.delete("/sessions/{session_id}")
async def cleanup_opensource_voice_session(
    session_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Manually cleanup a specific opensource voice session.
    
    Args:
        session_id: Session identifier
        user_info: Authenticated user information
    """
    print(f"🔍 [OPENSOURCE VOICE] DELETE /sessions/{session_id}")
    
    try:
        # Verify session exists and belongs to user
        session_data = await opensource_voice_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session_data.get("user_id") != user_info.get('sub'):
            raise HTTPException(status_code=403, detail="Session does not belong to user")
        
        # Close the session
        success = await opensource_voice_service.close_session(session_id)
        
        if success:
            return {"message": f"Session {session_id} cleaned up successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cleanup session")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error cleaning up OpenSource voice session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup session: {str(e)}")


@router.get("/health")
async def opensource_voice_health_check():
    """
    Health check endpoint for the opensource voice service.
    """
    try:
        health_status = await opensource_voice_service.health_check()
        return health_status
    except Exception as e:
        return {
            "service": "opensource_voice",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "unknown"
        } 