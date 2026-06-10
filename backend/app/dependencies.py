from fastapi import Header, HTTPException, status
import jwt
from app.config import JWT_SECRET, JWT_ALGORITHM
import logging

logger = logging.getLogger(__name__)

async def get_current_user(authorization: str = Header(None)):
    """
    FastAPI dependency that validates the Authorization header.
    Expects header format: "Bearer <token>"
    """
    if not authorization:
        logger.warning("Access denied: Authorization header is missing.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied. Please log in first."
        )
        
    try:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format. Expected 'Bearer <token>'."
            )
            
        token = parts[1]
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Access forbidden: Token has expired.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your login session has expired. Please log in again."
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Access forbidden: Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired login session."
        )
