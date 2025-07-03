from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.voice_redis import router as voice_redis_router
from app.api.email import router as email_router
from app.config import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="ChatGPT-like backend with API key authentication, built with FastAPI",
    version="0.1.0",
)

origins = [
    "https://voice-assistant-gilt.vercel.app",
    "http://localhost:3000",
    "http://localhost:8000",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
print("📋 [MAIN] Including routers...")
app.include_router(chat_router)
print("✅ [MAIN] Chat router included")
app.include_router(session_router)
print("✅ [MAIN] Session router included")
app.include_router(voice_redis_router)
print("✅ [MAIN] Voice Redis router included")
app.include_router(email_router)
print("✅ [MAIN] Email router included")


@app.get("/")
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 