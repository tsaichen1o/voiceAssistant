import redis
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from app.models.database import Session, Chat, Message
from app.config import settings
from app.db.connection import SessionLocal


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
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def create_session(user_id: Optional[str] = None) -> str:
    """
    Create new session in both PostgreSQL and Redis.
    """
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # 1. Store in PostgreSQL (permanent)
    with get_db_session() as db:
        try:
            # When a session is created, we also create its primary Chat counterpart
            db_session = Session(
                id=session_id,
                user_id=user_id,
                created_at=now,
                last_active=now,
                is_active=True
            )
            db.add(db_session)
            
            # Create the initial Chat associated with this Session
            initial_chat = Chat(
                id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                title="New Chat",
                created_at=now,
                updated_at=now
            )
            db.add(initial_chat)
            
            db.commit()
            
            return session_id
        except Exception as e:
            db.rollback()
            raise e
    
    # TODO: check if Redis is needed
    # 2. Cache in Redis (fast access)
    # session_data = {
    #     "session_id": session_id,
    #     "created_at": now.isoformat(),
    #     "last_active": now.isoformat(),
    #     "user_id": str(user_id) if user_id else None,
    #     "title": "New Chat",
    #     "messages": []
    # }
    
    # redis_client.setex(
    #     f"session:{session_id}",
    #     ACTIVE_SESSION_EXPIRY,
    #     json.dumps(session_data)
    # )
    
    # return session_id


"""
def get_session(session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    
    # Get session with cache-first strategy.
    
    # 1. Try Redis cache first
    cached_session = redis_client.get(f"session:{session_id}")
    if cached_session:
        session_data = json.loads(cached_session)
        # Verify user access if user_id is provided
        if user_id and session_data.get("user_id") != user_id:
            return None
        # Extend cache TTL for active sessions
        redis_client.expire(f"session:{session_id}", ACTIVE_SESSION_EXPIRY)
        return session_data
    
    # 2. Fall back to PostgreSQL if not in cache
    with get_db_session() as db:
        try:
            query = db.query(Session).filter(Session.id == session_id)
            if user_id:
                query = query.filter(Session.user_id == user_id)
            db_session = query.first()

            if not db_session or not db_session.is_active:
                return None

            # In our 3-tier model, a session contains chats, and chats contain messages
            # For simplicity, we assume one primary chat per session for now.
            chat = db.query(Chat).filter(Chat.session_id == session_id).first()
            messages = []
            title = chat.title if chat else "New Chat"

            if chat:
                chat_messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at).all()
                for msg in chat_messages:
                    messages.append({
                        "id": str(msg.id),
                        "session_id": str(msg.session_id),
                        "role": msg.role,
                        "content": msg.content,
                        "chat_id": str(msg.chat_id),
                        "created_at": msg.created_at.isoformat()
                    })

            session_data = {
                "session_id": str(db_session.id),
                "created_at": db_session.created_at.isoformat(),
                "last_active": db_session.last_active.isoformat(),
                "user_id": str(db_session.user_id) if db_session.user_id else None,
                "title": title,
                "messages": messages
            }
            
            # 3. Re-cache in Redis
            # We need to handle the case where `messages` contains datetime objects
            def json_converter(o):
                if isinstance(o, datetime):
                    return o.isoformat()
            redis_client.setex(
                f"session:{session_id}",
                ACTIVE_SESSION_EXPIRY,
                json.dumps(session_data, default=json_converter)
            )
            return session_data
        except Exception as e:
            print(f'DB ERROR in get_session: {e}')
            return None
"""


def update_session(session_id: str, messages: Optional[List[Dict]] = None, user_id: Optional[str] = None) -> bool:
    """
    Update session, chat title, and all messages in PostgreSQL.
    """
    now = datetime.now(timezone.utc)
    with get_db_session() as db:
        try:
            query = db.query(Session).filter(Session.id == session_id)
            if user_id: query = query.filter(Session.user_id == user_id)
            db_session = query.first()
            
            if not db_session: return False
            db_session.last_active = now
            
            if messages:
                chat = db.query(Chat).filter(Chat.session_id == db_session.id).first()
                if not chat:
                    chat = Chat(id=str(uuid.uuid4()), user_id=db_session.user_id, session_id=db_session.id, title="New Chat", created_at=now)
                    db.add(chat)
                    db.flush()

                # To ensure consistency, delete all old messages and add the new complete list
                db.query(Message).filter(Message.chat_id == chat.id).delete(synchronize_session=False)

                for msg_data in messages:
                    created_at_str = msg_data.get("created_at")
                    created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if isinstance(created_at_str, str) else now

                    db_message = Message(
                        id=msg_data.get("id", str(uuid.uuid4())),
                        chat_id=chat.id,
                        session_id=db_session.id,
                        role=msg_data["role"],
                        content=msg_data["content"],
                        created_at=created_at_dt
                    )
                    db.add(db_message)
                
                # Update chat title
                user_messages = [m for m in messages if m["role"] == "user"]
                if user_messages:
                    chat.title = user_messages[0]["content"][:50] + ("..." if len(user_messages[0]["content"]) > 50 else "")
                chat.updated_at = now
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating session in DB: {e}")
            return False
        

def get_session(session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a session and all its related messages directly from PostgreSQL.
    """
    with get_db_session() as db:
        try:
            # 1. Find the session and verify ownership
            query = db.query(Session).filter(Session.id == session_id)
            if user_id:
                query = query.filter(Session.user_id == user_id)
            db_session = query.first()

            if not db_session or not db_session.is_active:
                return None

            # 2. Find the associated chat to get the title
            chat = db.query(Chat).filter(Chat.session_id == session_id).first()
            title = chat.title if chat else "New Chat"
            messages = []

            # 3. If a chat exists, get all its messages
            if chat:
                chat_messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at).all()
                for msg in chat_messages:
                    messages.append({
                        "id": str(msg.id),
                        "session_id": str(msg.session_id),
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat()
                    })

            # 4. Assemble and return the complete session data
            session_data = {
                "session_id": str(db_session.id),
                "created_at": db_session.created_at.isoformat(),
                "last_active": db_session.last_active.isoformat(),
                "user_id": str(db_session.user_id) if db_session.user_id else None,
                "title": title,
                "messages": messages
            }
            return session_data
        except Exception as e:
            print(f'DB ERROR in get_session: {e}')
            return None


"""
def update_session(session_id: str, messages: Optional[List[Dict]] = None, user_id: Optional[str] = None) -> bool:
    
    # Update session and its related Chat and Messages in PostgreSQL and Redis.
    
    now = datetime.now(timezone.utc)
    db = get_db_session()
    try:
        # 1. Get the main session object, ensuring ownership
        query = db.query(Session).filter(Session.id == session_id)
        if user_id:
            query = query.filter(Session.user_id == user_id)
        db_session = query.first()
        
        if not db_session:
            return False
        
        db_session.last_active = now
        
        if messages:
            # 2. Get or create the associated Chat record
            # In this logic, we assume one primary Chat per Session
            chat = db.query(Chat).filter(Chat.session_id == db_session.id).first()
            
            if not chat:
                # This case might happen if creation failed before, let's create it now
                chat = Chat(
                    id=str(uuid.uuid4()),
                    user_id=db_session.user_id,
                    session_id=db_session.id,
                    title="New Chat",
                    created_at=now
                )
                db.add(chat)
                db.flush() # Flush to get the chat.id before creating messages

            # 3. To prevent duplicates, first delete all existing messages for this chat
            db.query(Message).filter(Message.chat_id == chat.id).delete(synchronize_session=False)

            # 4. Add the new, complete list of messages
            for msg_data in messages:
                created_at_str = msg_data.get("created_at")
                if isinstance(created_at_str, str):
                    created_at_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                else:
                    created_at_dt = now

                db_message = Message(
                    id=msg_data.get("id", str(uuid.uuid4())),
                    chat_id=chat.id,
                    session_id=db_session.id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    created_at=created_at_dt
                )
                db.add(db_message)
            
            # 5. Update chat title from the first user message in the list
            user_messages = [m for m in messages if m["role"] == "user"]
            if user_messages:
                new_title = user_messages[0]["content"][:50]
                if len(user_messages[0]["content"]) > 50:
                    new_title += "..."
                chat.title = new_title
            
            chat.updated_at = now
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Error updating session in DB: {e}")
        return False
    finally:
        db.close()


    # 2. Update Redis cache after successful DB commit
    get_session(session_id, user_id) # Calling get_session will automatically refresh the cache
    
    return True
"""


def delete_session(session_id: str, user_id: Optional[str] = None) -> bool:
    """
    Delete session from both PostgreSQL and Redis.
    
    Strategy:
    1. Soft delete in PostgreSQL (keep for history)
    2. Remove from Redis cache
    """
    
    # 1. Soft delete in PostgreSQL
    with get_db_session() as db:
        try:
            db_session = db.query(Session).filter(Session.id == session_id, Session.user_id == user_id).first()
            
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


def get_all_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    # This function should now work correctly because the data links are fixed
    with get_db_session() as db:
        try:
            db_sessions = db.query(Session).filter(Session.is_active == True, Session.user_id == user_id).order_by(Session.last_active.desc()).all()
            sessions_data = []
            for db_session in db_sessions:
                chat = db.query(Chat).filter(Chat.session_id == db_session.id).first()
                title = chat.title if chat else "New Chat"
                message_count = db.query(Message).filter(Message.session_id == db_session.id).count()

                sessions_data.append({
                    "session_id": str(db_session.id),
                    "title": title,
                    "created_at": db_session.created_at.isoformat(),
                    "last_active": db_session.last_active.isoformat(),
                    "user_id": str(db_session.user_id),
                    "message_count": message_count
                })
            return sessions_data
        except Exception as e:
            print(f"Error in get_all_sessions: {e}")
            return []


"""
def get_all_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    
    # Get all sessions for a user, decorated with info from the associated Chat.
    
    with get_db_session() as db:
        try:
            db_sessions = db.query(Session).filter(Session.is_active == True, Session.user_id == user_id).order_by(Session.last_active.desc()).all()
            
            sessions_data = []
            for db_session in db_sessions:
                # Find the associated chat to get the title
                chat = db.query(Chat).filter(Chat.session_id == db_session.id).first()
                title = chat.title if chat else "New Chat"
                
                # Count messages more efficiently
                message_count = db.query(Message).filter(Message.session_id == db_session.id).count()

                sessions_data.append({
                    "session_id": str(db_session.id),
                    "title": title,
                    "created_at": db_session.created_at.isoformat(),
                    "last_active": db_session.last_active.isoformat(),
                    "user_id": str(db_session.user_id),
                    "message_count": message_count
                })
            return sessions_data
        except Exception as e:
            print(f"Error in get_all_sessions: {e}")
            return []
"""


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
    expiry_time = datetime.now(timezone.utc) - timedelta(days=30)  # 30 days old
    
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