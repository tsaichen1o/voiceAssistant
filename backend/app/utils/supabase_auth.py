import jwt
from fastapi import HTTPException, Header
from app.config import settings
from typing import Optional, Dict, Any


async def verify_supabase_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify Supabase JWT token (HS256 for local dev).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid token scheme or missing token")

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token invalid: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


async def verify_auth_flexible(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    # Usually you only use Bearer + JWT, no API KEY
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer":
        return await verify_supabase_token(authorization)
    raise HTTPException(status_code=401, detail="Invalid credentials")