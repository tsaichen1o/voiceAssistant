from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.voice import router as voice_router
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
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(voice_router)


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