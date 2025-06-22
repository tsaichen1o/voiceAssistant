from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import asyncio

from app.services.adk_voice_service import adk_voice_service
from app.utils.supabase_auth import verify_supabase_token

router = APIRouter(
    prefix="/api/voice",
    tags=["voice"],
)


@router.get("/events/{user_id}")
async def voice_events_stream(
    user_id: str, 
    is_audio: str = "true",
    test_mode: str = "false",
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Server-Sent Events (SSE) endpoint for voice assistant communication.
    
    Args:
        user_id: User identifier
        is_audio: Whether to use audio mode ("true" or "false")
        user_info: Authenticated user information
    """
    print(f"Voice client {user_id} connecting via SSE, audio mode: {is_audio}")
    print(f"✅ Authenticated user: {user_info.get('email', 'unknown')}")
    
    # Authenticate UserID
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    try:
        # Create voice session
        is_audio_mode = is_audio.lower() == "true"
        live_events, live_request_queue = await adk_voice_service.create_session(
            user_id=user_id, 
            is_audio=is_audio_mode
        )
        
        async def event_generator():
            try:
                async for event_data in adk_voice_service.process_events(live_events):
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # Add small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in voice SSE stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                # Clean up session
                adk_voice_service.close_session(user_id)
                print(f"Voice client {user_id} disconnected from SSE")
        
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
        print(f"Error creating voice session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")


@router.post("/send/{user_id}")
async def send_voice_message(
    user_id: str, 
    request: Request,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    HTTP endpoint for sending messages to the voice assistant.
    
    Args:
        user_id: User identifier
        request: HTTP request containing the message
        user_info: Authenticated user information
    """
    print(f"✅ Authenticated user sending voice message: {user_info.get('email', 'unknown')}")
    
    # Authenticate UserID
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    try:
        # Parse the message
        message = await request.json()
        mime_type = message.get("mime_type")
        data = message.get("data")
        
        if not mime_type or not data:
            raise HTTPException(status_code=400, detail="Missing mime_type or data")
        
        # Send the message to the voice service
        success = False
        if mime_type == "text/plain":
            success = await adk_voice_service.send_text_message(user_id, data)
            print(f"[CLIENT TO VOICE AGENT] User {user_id}: {data}")
        elif mime_type == "audio/pcm":
            success = await adk_voice_service.send_audio_data(user_id, data, mime_type)
            print(f"[CLIENT TO VOICE AGENT] User {user_id}: audio/pcm: {len(data)} chars (base64)")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mime type: {mime_type}")
        
        if not success:
            raise HTTPException(status_code=404, detail="Voice session not found")
        
        return {"status": "sent"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"Error sending voice message for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/sessions/{user_id}")
async def get_user_voice_session(
    user_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Get user's active voice session.
    """
    
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="Can only access your own sessions")
    
    print(f"✅ User {user_info.get('email', 'unknown')} checking their voice session")
    try:
        sessions = adk_voice_service.get_active_sessions()
        user_session = user_id if user_id in sessions else None
        return {
            "user_id": user_id,
            "has_active_session": user_session is not None,
            "session_id": user_session
        }
    except Exception as e:
        print(f"Error getting user voice session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.delete("/sessions/{user_id}")
async def cleanup_user_voice_session(
    user_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Clean up user's active voice session.
    """
   
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="Can only cleanup your own session")
    
    print(f"✅ User {user_info.get('email', 'unknown')} cleaning up their voice session")
    try:
        sessions = adk_voice_service.get_active_sessions()
        
        if user_id in sessions:
            adk_voice_service.close_session(user_id)
            print(f"✅ Cleaned up voice session for user: {user_id}")
            return {
                "message": f"Cleaned up voice session for user {user_id}",
                "user_id": user_id,
                "success": True
            }
        else:
            return {
                "message": f"No active session found for user {user_id}",
                "user_id": user_id,
                "success": False
            }
    except Exception as e:
        print(f"Error during cleanup for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


