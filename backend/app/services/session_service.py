import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.models.database import Session, Chat, Message, User
from app.config import settings
from app.db.connection import engine, SessionLocal

# Redis setup
if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
else:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )

# Redis cache expiry (2 hours for active sessions)
ACTIVE_SESSION_EXPIRY = 60 * 60 * 2


def get_db_session():
    """Get database session."""
    return SessionLocal()


def create_session(user_id: Optional[str] = None) -> str:
    """
    Create new session in both PostgreSQL and Redis.
    
    Strategy:
    1. Create permanent record in PostgreSQL
    2. Cache active session in Redis for fast access
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # 1. Store in PostgreSQL (permanent)
    with get_db_session() as db:
        try:
            db_session = Session(
                id=session_id,
                user_id=user_id,
                session_key=session_id,
                created_at=now,
                last_active=now,
                is_active=True
            )
            db.add(db_session)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
    
    # 2. Cache in Redis (fast access)
    session_data = {
        "session_id": session_id,
        "created_at": now.isoformat(),
        "last_active": now.isoformat(),
        "user_id": user_id,
        "messages": []
    }
    
    redis_client.setex(
        f"session:{session_id}",
        ACTIVE_SESSION_EXPIRY,
        json.dumps(session_data)
    )
    
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session with cache-first strategy.
    
    Strategy:
    1. Try Redis cache first (fast)
    2. Fall back to PostgreSQL if not in cache
    3. Re-cache in Redis if found in PostgreSQL
    """
    
    # 1. Try Redis cache first
    cached_session = redis_client.get(f"session:{session_id}")
    if cached_session:
        session_data = json.loads(cached_session)
        # Extend cache TTL for active sessions
        redis_client.expire(f"session:{session_id}", ACTIVE_SESSION_EXPIRY)
        return session_data
    
    # 2. Fall back to PostgreSQL
    with get_db_session() as db:
        try:
            db_session = db.query(Session).filter(Session.id == session_id).first()
            
            if not db_session or not db_session.is_active:
                return None
            
            # Get messages from database
            chats = db.query(Chat).filter(Chat.session_id == session_id).all()
            messages = []
            
            for chat in chats:
                chat_messages = db.query(Message).filter(
                    Message.chat_id == chat.id
                ).order_by(Message.created_at).all()
                
                for msg in chat_messages:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat()
                    })
            
            session_data = {
                "session_id": session_id,
                "created_at": db_session.created_at.isoformat(),
                "last_active": db_session.last_active.isoformat(),
                "user_id": str(db_session.user_id) if db_session.user_id else None,
                "messages": messages
            }
            
            # 3. Re-cache in Redis for next time
            redis_client.setex(
                f"session:{session_id}",
                ACTIVE_SESSION_EXPIRY,
                json.dumps(session_data)
            )
            
            return session_data
            
        except Exception as e:
            return None


def update_session(session_id: str, messages: Optional[List[Dict]] = None) -> bool:
    """
    Update session in both PostgreSQL and Redis.
    
    Strategy:
    1. Update PostgreSQL (permanent record)
    2. Update Redis cache (fast access)
    """
    now = datetime.utcnow()
    
    # 1. Update PostgreSQL
    with get_db_session() as db:
        try:
            db_session = db.query(Session).filter(Session.id == session_id).first()
            
            if not db_session:
                return False
            
            # Update last_active time
            db_session.last_active = now
            
            if messages:
                # Get or create chat
                chat = db.query(Chat).filter(Chat.session_id == session_id).first()
                
                if not chat:
                    chat = Chat(
                        user_id=db_session.user_id,
                        session_id=session_id,
                        title=f"Chat {session_id[:8]}",
                        created_at=now
                    )
                    db.add(chat)
                    db.flush()
                
                # Clear existing messages
                db.query(Message).filter(Message.chat_id == chat.id).delete()
                
                # Add new messages
                for msg in messages:
                    db_message = Message(
                        chat_id=chat.id,
                        role=msg["role"],
                        content=msg["content"],
                        created_at=now
                    )
                    db.add(db_message)
                
                # Update chat title from first user message
                for msg in messages:
                    if msg["role"] == "user":
                        title = msg["content"][:50]
                        if len(msg["content"]) > 50:
                            title += "..."
                        chat.title = title
                        break
                
                chat.updated_at = now
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            return False
    
    # 2. Update Redis cache
    try:
        cached_session = redis_client.get(f"session:{session_id}")
        if cached_session:
            session_data = json.loads(cached_session)
            session_data["last_active"] = now.isoformat()
            
            if messages:
                session_data["messages"] = messages
            
            redis_client.setex(
                f"session:{session_id}",
                ACTIVE_SESSION_EXPIRY,
                json.dumps(session_data)
            )
    except Exception:
        # Redis update failure is not critical
        pass
    
    return True


def delete_session(session_id: str) -> bool:
    """
    Delete session from both PostgreSQL and Redis.
    
    Strategy:
    1. Soft delete in PostgreSQL (keep for history)
    2. Remove from Redis cache
    """
    
    # 1. Soft delete in PostgreSQL
    with get_db_session() as db:
        try:
            db_session = db.query(Session).filter(Session.id == session_id).first()
            
            if not db_session:
                return False
            
            db_session.is_active = False
            db.commit()
            
        except Exception as e:
            db.rollback()
            return False
    
    # 2. Remove from Redis cache
    try:
        redis_client.delete(f"session:{session_id}")
    except Exception:
        # Redis deletion failure is not critical
        pass
    
    return True


def get_all_sessions() -> List[Dict[str, Any]]:
    """
    Get all sessions from PostgreSQL.
    
    Note: We don't cache this in Redis as it's less frequently accessed
    and can be expensive to maintain cache consistency.
    """
    with get_db_session() as db:
        try:
            # Get all active sessions
            db_sessions = db.query(Session).filter(Session.is_active == True).all()
            
            sessions = []
            for db_session in db_sessions:
                # Count messages for this session
                message_count = 0
                title = f"Chat Session {db_session.id[:8]}"
                
                # Get chats for this session
                chats = db.query(Chat).filter(Chat.session_id == db_session.id).all()
                
                for chat in chats:
                    # Count messages in this chat
                    count = db.query(Message).filter(Message.chat_id == chat.id).count()
                    message_count += count
                    
                    # Use chat title if available
                    if chat.title and chat.title != f"Chat {db_session.id[:8]}":
                        title = chat.title
                
                session_data = {
                    "session_id": db_session.id,
                    "created_at": db_session.created_at.isoformat(),
                    "last_active": db_session.last_active.isoformat(),
                    "user_id": str(db_session.user_id) if db_session.user_id else None,
                    "message_count": message_count,
                    "title": title
                }
                
                sessions.append(session_data)
            
            # Sort by last_active (most recent first)
            sessions.sort(key=lambda x: x["last_active"], reverse=True)
            
            return sessions
            
        except Exception as e:
            return []


def get_cache_stats() -> Dict[str, Any]:
    """
    Get Redis cache statistics for monitoring.
    """
    try:
        # Count active sessions in cache
        session_keys = redis_client.keys("session:*")
        active_sessions = len(session_keys)
        
        # Get Redis info
        redis_info = redis_client.info()
        
        return {
            "active_cached_sessions": active_sessions,
            "redis_memory_used": redis_info.get("used_memory_human", "N/A"),
            "redis_connected_clients": redis_info.get("connected_clients", 0),
            "cache_hit_ratio": "Available via Redis monitoring tools"
        }
    except Exception as e:
        return {"error": str(e)}


def cleanup_expired_sessions():
    """
    Background task to clean up expired sessions.
    Can be run periodically via cron or Celery.
    """
    expiry_time = datetime.utcnow() - timedelta(days=30)  # 30 days old
    
    with get_db_session() as db:
        try:
            # Mark old inactive sessions for cleanup
            old_sessions = db.query(Session).filter(
                Session.last_active < expiry_time,
                Session.is_active == True
            ).all()
            
            for session in old_sessions:
                session.is_active = False
            
            db.commit()
            
            return len(old_sessions)
            
        except Exception as e:
            db.rollback()
            return 0 