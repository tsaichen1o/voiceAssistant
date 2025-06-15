from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship, registry
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.connection import engine


# Create a central registry object that will manage all models
mapper_registry = registry()

# Generate a Declarative Base Class from this registry
Base = mapper_registry.generate_base()

# Reflect the existing auth.users table in the database
users_table = Table(
    'users',
    mapper_registry.metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    schema='auth',
    autoload_with=engine
)

# Create a corresponding, empty User class that "does not" inherit Base
class User:
    pass


class Session(Base):
    """Session model for tracking user sessions."""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(users_table.c.id), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    chats = relationship("Chat", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sessions")

class Chat(Base):
    """Chat model for storing conversations."""
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(users_table.c.id), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    title = Column(String(200), default="New Chat")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    session = relationship("Session", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    """Message model for storing individual messages in a chat."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    chat = relationship("Chat", back_populates="messages") 
    

mapper_registry.map_imperatively(User, users_table, properties={
    'sessions': relationship(Session, back_populates='user')
})