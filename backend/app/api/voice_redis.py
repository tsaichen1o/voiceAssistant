from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import asyncio

from app.services.redis_voice_service import redis_voice_service
from app.utils.supabase_auth import verify_supabase_token

print("🚀 [VOICE REDIS] Importing voice_redis module...")

router = APIRouter(
    prefix="/api/voice-redis",
    tags=["voice-redis"],
)

print("✅ [VOICE REDIS] Router created with prefix /api/voice-redis")


@router.get("/events/{user_id}")
async def voice_events_stream_redis(
    user_id: str, 
    is_audio: str = "true",
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Server-Sent Events (SSE) endpoint for voice assistant using Redis state management.
    
    Args:
        user_id: User identifier
        is_audio: Whether to use audio mode ("true" or "false")
        user_info: Authenticated user information
    """
    print(f"🎯 [VOICE REDIS] GET /events/{user_id} - ENTRY POINT")
    print(f"Voice client {user_id} connecting via Redis SSE, audio mode: {is_audio}")
    print(f"✅ Authenticated user: {user_info.get('email', 'unknown')}")
    
    # Authenticate UserID
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    try:
        # Create voice session with Redis
        is_audio_mode = is_audio.lower() == "true"
        session_data = await redis_voice_service.create_session(
            user_id=user_id, 
            is_audio=is_audio_mode
        )
        session_id = session_data["session_id"]
        
        async def event_generator():
            try:
                # Send session created event
                yield f"data: {json.dumps({'type': 'session_created', 'session_id': session_id})}\n\n"
                
                # If audio mode, process ADK events
                if is_audio_mode and session_id in redis_voice_service.adk_sessions:
                    live_events, live_request_queue = redis_voice_service.adk_sessions[session_id]
                    
                    # Set up concurrent processing of ADK events and heartbeats
                    last_heartbeat = asyncio.get_event_loop().time()
                    heartbeat_interval = 30  # seconds
                    
                    async for event in live_events:
                        # Process ADK event
                        processed_event = await redis_voice_service._process_single_adk_event(event)
                        if processed_event:
                            yield f"data: {json.dumps(processed_event)}\n\n"
                        
                        # Send heartbeat if needed
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_heartbeat > heartbeat_interval:
                            current_session = await redis_voice_service.get_session(session_id)
                            if current_session:
                                heartbeat_event = {
                                    "type": "heartbeat",
                                    "timestamp": current_session['last_active']
                                }
                                yield f"data: {json.dumps(heartbeat_event)}\n\n"
                                last_heartbeat = current_time
                            else:
                                break  # Session no longer exists
                else:
                    # Text-only mode: just heartbeat
                    while True:
                        current_session = await redis_voice_service.get_session(session_id)
                        if not current_session:
                            break
                        
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_session['last_active']})}\n\n"
                        await asyncio.sleep(30)
                    
            except Exception as e:
                print(f"Error in Redis voice SSE stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                # Clean up session
                await redis_voice_service.close_session(session_id)
                print(f"Voice client {user_id} disconnected from Redis SSE")
        
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
        print(f"Error creating Redis voice session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create voice session: {str(e)}")


@router.post("/send/{session_id}")
async def send_voice_message_redis(
    session_id: str, 
    request: Request,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    HTTP endpoint for sending messages to the Redis-based voice assistant.
    
    Args:
        session_id: Session identifier (not user_id!)
        request: HTTP request containing the message
        user_info: Authenticated user information
    """
    print(f"🔍 [VOICE REDIS] POST /send/{session_id} - START")
    print(f"✅ Authenticated user sending Redis voice message: {user_info.get('email', 'unknown')}")
    
    try:
        # Parse the message
        print(f"🔍 [VOICE REDIS] Parsing request JSON...")
        message = await request.json()
        mime_type = message.get("mime_type")
        data = message.get("data")
        print(f"🔍 [VOICE REDIS] Parsed: mime_type={mime_type}, data_length={len(data) if data else 0}")
        
        if not mime_type or not data:
            print(f"❌ [VOICE REDIS] Missing mime_type or data")
            raise HTTPException(status_code=400, detail="Missing mime_type or data")
        
        # Verify session exists and belongs to user
        print(f"🔍 [VOICE REDIS] Verifying session {session_id}...")
        session_data = await redis_voice_service.get_session(session_id)
        if not session_data:
            print(f"❌ [VOICE REDIS] Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        print(f"✅ [VOICE REDIS] Session {session_id} found")
        if session_data.get("user_id") != user_info.get('sub'):
            print(f"❌ [VOICE REDIS] Session does not belong to user")
            raise HTTPException(status_code=403, detail="Session does not belong to user")
        
        # Stream the response back
        print(f"🔍 [VOICE REDIS] Starting response stream...")
        async def response_generator():
            try:
                print(f"🔍 [VOICE REDIS] Calling redis_voice_service.send_message...")
                async for event_data in redis_voice_service.send_message(session_id, data, mime_type):
                    print(f"🔍 [VOICE REDIS] Got event: {event_data}")
                    yield f"data: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(0.01)
                print(f"✅ [VOICE REDIS] Finished processing events")
            except Exception as e:
                print(f"❌ [VOICE REDIS] Error in response generator: {e}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        if mime_type == "text/plain":
            print(f"[CLIENT TO REDIS VOICE] Session {session_id}: {data}")
        elif mime_type == "audio/pcm":
            print(f"[CLIENT TO REDIS VOICE] Session {session_id}: audio/pcm: {len(data)} chars (base64)")
        
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
        print(f"Error sending Redis voice message for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/sessions/{user_id}")
async def get_user_redis_voice_sessions(
    user_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Get user's active Redis voice sessions.
    """
    print(f"🎯 [VOICE REDIS] GET /sessions/{user_id} - ENTRY POINT")
    
    if user_info.get('sub') != user_id:
        raise HTTPException(status_code=403, detail="Can only access your own sessions")
    
    print(f"✅ User {user_info.get('email', 'unknown')} checking their Redis voice sessions")
    try:
        all_sessions = await redis_voice_service.list_active_sessions()
        user_sessions = []
        
        for session_id in all_sessions:
            session_data = await redis_voice_service.get_session(session_id)
            if session_data and session_data.get("user_id") == user_id:
                user_sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "last_active": session_data.get("last_active"),
                    "is_audio": session_data.get("is_audio", True)
                })
        
        return {
            "user_id": user_id,
            "sessions": user_sessions,
            "total_sessions": len(user_sessions)
        }
    except Exception as e:
        print(f"Error getting user Redis voice sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.delete("/sessions/{session_id}")
async def cleanup_redis_voice_session(
    session_id: str,
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
):
    """
    Clean up a specific Redis voice session.
    """
    print(f"🎯 [VOICE REDIS] DELETE /sessions/{session_id} - ENTRY POINT")
    
    print(f"✅ User {user_info.get('email', 'unknown')} cleaning up Redis voice session")
    try:
        # Verify session belongs to user
        session_data = await redis_voice_service.get_session(session_id)
        if not session_data:
            return {
                "message": f"Session {session_id} not found",
                "session_id": session_id,
                "success": False
            }
        
        if session_data.get("user_id") != user_info.get('sub'):
            raise HTTPException(status_code=403, detail="Can only cleanup your own sessions")
        
        success = await redis_voice_service.close_session(session_id)
        
        return {
            "message": f"Cleaned up Redis voice session {session_id}",
            "session_id": session_id,
            "success": success
        }
    except Exception as e:
        print(f"Error during Redis cleanup for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/health")
async def redis_voice_health_check():
    """Health check for Redis voice service."""
    print(f"🎯 [VOICE REDIS] GET /health - ENTRY POINT")
    try:
        # Test Redis connection
        sessions = await redis_voice_service.list_active_sessions()
        return {
            "status": "healthy",
            "service": "redis_voice",
            "active_sessions": len(sessions),
            "redis_connected": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "redis_voice", 
            "error": str(e),
            "redis_connected": False
        } 