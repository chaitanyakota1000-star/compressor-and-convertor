from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.config import JWT_SECRET, JWT_ALGORITHM
from app.database import users_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class UserAuthRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")

@router.post("/signup")
async def signup(user_data: UserAuthRequest):
    email = user_data.email.lower().strip()
    password = user_data.password
    
    # Simple email validation check (avoiding email-validator package dependency)
    if "@" not in email or "." not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address."
        )
        
    # Check if user already exists
    if email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered."
        )
        
    # Hash password with bcrypt
    try:
        # bcrypt.hashpw expects bytes for both password and salt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error during password security encryption."
        )
        
    # Save user record
    users_db[email] = {
        "id": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "email": email,
        "password": hashed
    }
    
    logger.info(f"New user registered: {email}")
    return {"message": "Registration successful! You can now log in."}

@router.post("/login")
async def login(user_data: UserAuthRequest):
    email = user_data.email.lower().strip()
    password = user_data.password
    
    user = users_db.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    # Check password match
    hashed_password = user["password"]
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    # Generate JWT token signed for 7 days
    try:
        payload = {
            "userId": user["id"],
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Failed to generate JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error generating login session."
        )
        
    logger.info(f"User logged in successfully: {email}")
    return {
        "message": "Login successful!",
        "token": token
    }
