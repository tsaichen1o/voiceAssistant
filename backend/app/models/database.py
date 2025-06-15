from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
import uuid


Base = declarative_base()

class Session(Base):
    """Session model for tracking user sessions."""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    chats = relationship("Chat", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sessions")


class Chat(Base):
    """Chat model for storing conversations."""
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # TODO: Add user_id
    user_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    title = Column(String(200))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    session = relationship("Session", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing individual messages in a chat."""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))  # Direct session reference for easier queries
    role = Column(String(20))  # "system", "user", "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Additional fields for tracking
    tokens_used = Column(Integer, nullable=True)
    model = Column(String(50), nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages") 
    

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}
    id = Column(UUID(as_uuid=True), primary_key=True)
    sessions = relationship("Session", back_populates="user")