import jwt
import httpx
from fastapi import HTTPException, Depends, Header
from app.config import settings
from typing import Optional, Dict, Any
from functools import lru_cache
import asyncio


@lru_cache()
def get_supabase_jwt_secret():
    """Get Supabase JWT secret"""
    return settings.SUPABASE_JWT_SECRET


@lru_cache()
async def get_supabase_public_key():
    """Fetch Supabase public key for JWT verification"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.SUPABASE_URL}/.well-known/jwks.json")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Supabase public key: {str(e)}"
        )


async def verify_supabase_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify Supabase JWT token
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Expected 'Bearer'"
        )
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing token"
        )
    
    try:
        # Verify JWT token using Supabase JWT secret
        payload = jwt.decode(
            token,
            get_supabase_jwt_secret(),
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Check if token has expired
        current_time = asyncio.get_event_loop().time()
        if payload.get('exp', 0) < current_time:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        
        # Return user information
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "auth_type": "supabase"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )


async def verify_auth_flexible(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Flexible authentication verification - supports both API Key and Supabase Token
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Dict containing user/auth information
    """
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    scheme, _, token = authorization.partition(" ")
    
    # If Bearer token, try Supabase verification first
    if scheme.lower() == "bearer" and token != settings.API_KEY:
        try:
            return await verify_supabase_token(authorization)
        except HTTPException:
            # If Supabase verification fails, continue to try API Key verification
            pass
    
    # API Key verification (backward compatibility)
    if scheme.lower() == settings.API_KEY_PREFIX.lower() and token == settings.API_KEY:
        return {
            "user_id": "api_user",
            "email": "api@system.local",
            "role": "api_user",
            "auth_type": "api_key"
        }
    
    raise HTTPException(
        status_code=401,
        detail="Invalid credentials"
    ) 