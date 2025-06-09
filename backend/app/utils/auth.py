# UNUSED
# This file is used to verify the API key
# When testing without frontend.

from fastapi import HTTPException, Depends, Header
from app.config import settings
from typing import Optional


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """
    Verify that the request has a valid API key in the header.
    To use, add this function as a dependency in your endpoint.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        None if successful, otherwise raises HTTPException
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Please include 'Authorization: Bearer YOUR_API_KEY' header."
        )
    
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != settings.API_KEY_PREFIX.lower():
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication scheme. Expected '{settings.API_KEY_PREFIX}'"
        )
    
    if token != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    
    return None 