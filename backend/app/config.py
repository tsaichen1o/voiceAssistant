from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # General settings
    APP_NAME: str = "Voice Assistant Backend"
    DEBUG: bool = False
    
    # Google Gemini API settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    # Voice model - use experimental version for better real-time voice performance
    VOICE_MODEL: str = "gemini-2.0-flash-exp"
    
    # Vertex AI Search settings
    VERTEX_AI_SEARCH_PROJECT_ID: str = ""
    VERTEX_AI_SEARCH_LOCATION: str = ""
    VERTEX_AI_SEARCH_DATA_STORE_ID_WEB: str = ""
    VERTEX_AI_SEARCH_DATA_STORE_ID_FAQ: str = ""
    VERTEX_AI_SEARCH_ENGINE_ID: str = ""

    # API Key authentication (former version)
    API_KEY_HEADER: str = "Authorization"
    API_KEY_PREFIX: str = "Bearer"
    API_KEY: str = ""
    
    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # Database settings - only use DATABASE_URL
    DATABASE_URL: str = ""

    # Redis settings (for caching and future message queue)
    REDIS_URL: Optional[str] = None  # Redis connection URL (takes precedence if set)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Email settings (for sending email to human when LLM cannot solve)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""
    DEFAULT_EMAIL_RECIPIENT: str = ""
    TUITION_EMAIL_RECIPIENT: str = ""
    APPLICATION_EMAIL_RECIPIENT: str = ""
    PROGRAM_EMAIL_RECIPIENT: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()