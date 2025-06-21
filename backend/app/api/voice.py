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
    test_mode: str = "false"
):
    """
    Server-Sent Events (SSE) endpoint for voice assistant communication.
    
    Args:
        user_id: User identifier
        is_audio: Whether to use audio mode ("true" or "false")
        test_mode: Skip authentication for testing ("true" or "false")
    """
    print(f"Voice client {user_id} connecting via SSE, audio mode: {is_audio}, test_mode: {test_mode}")
    
    # 暂时跳过认证用于测试
    if test_mode.lower() != "true":
        print("⚠️ Authentication skipped for testing purposes")
        # TODO: 生产环境中需要启用认证
        # raise HTTPException(status_code=401, detail="Authentication required")
    
    user_info = {"user_id": user_id}  # 临时用户信息
    
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
    test_mode: str = "false"
):
    """
    HTTP endpoint for sending messages to the voice assistant.
    
    Args:
        user_id: User identifier
        request: HTTP request containing the message
        test_mode: Skip authentication for testing ("true" or "false")
    """
    # 暂时跳过认证用于测试
    if test_mode.lower() != "true":
        print("⚠️ Authentication skipped for testing purposes")
        # TODO: 生产环境中需要启用认证
        # raise HTTPException(status_code=401, detail="Authentication required")
    
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


@router.get("/sessions")
async def get_active_voice_sessions():
    """
    Get list of active voice sessions (test mode - no auth required).
    """
    try:
        sessions = adk_voice_service.get_active_sessions()
        return {"active_sessions": sessions, "count": len(sessions)}
    except Exception as e:
        print(f"Error getting active voice sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.delete("/sessions")
async def cleanup_all_voice_sessions():
    """
    Clean up all active voice sessions (for debugging).
    """
    try:
        sessions = adk_voice_service.get_active_sessions()
        session_count = len(sessions)
        
        for session_id in sessions:
            try:
                adk_voice_service.close_session(session_id)
                print(f"✅ Cleaned up voice session: {session_id}")
            except Exception as e:
                print(f"❌ Error cleaning up session {session_id}: {e}")
        
        return {
            "message": f"Cleaned up {session_count} voice sessions",
            "cleared_sessions": session_count
        }
    except Exception as e:
        print(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.delete("/session/{user_id}")
async def close_voice_session(
    user_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Close a voice session.
    
    Args:
        user_id: User identifier
        user_info: User authentication information
    """
    try:
        adk_voice_service.close_session(user_id)
        return {"status": "closed"}
    except Exception as e:
        print(f"Error closing voice session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}") 