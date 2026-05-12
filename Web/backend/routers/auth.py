from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_database
from models import UserCreate, UserLogin, UserResponse, Token
from auth_utils import verify_password, get_password_hash, create_access_token, decode_access_token
from datetime import datetime, timedelta
from bson import ObjectId
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import hashlib

router = APIRouter()
security = HTTPBearer()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def generate_avatar_url(email, username):
    """Generate avatar URL using UI Avatars (always works)"""
    # URL encode the username for safety
    import urllib.parse
    username_encoded = urllib.parse.quote(username)
    
    # Use UI Avatars - simple, reliable, and always works
    avatar_url = f"https://ui-avatars.com/api/?name={username_encoded}&size=200&background=00d9ff&color=0a0e27&bold=true"
    
    return avatar_url

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from token"""
    token = credentials.credentials
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = get_database()
    users_collection = db.users
    user = users_collection.find_one({"username": username})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Convert ObjectId to string for response
    user["_id"] = str(user["_id"])
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_database()
    users_collection = db.users
    
    # Validate password length (bcrypt has 72-byte limit)
    password_bytes = user_data.password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is too long. Maximum 72 bytes allowed. Your password is {len(password_bytes)} bytes. Please use a shorter password."
        )
    
    # Check if username already exists
    if users_collection.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    
    # Generate avatar URL for email/password users
    profile_picture = generate_avatar_url(user_data.email, user_data.username)
    
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "profile_picture": profile_picture,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "is_admin": False
    }
    
    try:
        result = users_collection.insert_one(user_doc)
        # Fetch created user
        user = users_collection.find_one({"_id": result.inserted_id})
        user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access token - supports username or email"""
    db = get_database()
    users_collection = db.users
    
    # Try to find user by username OR email
    user = users_collection.find_one({
        "$or": [
            {"username": credentials.username},
            {"email": credentials.username}
        ]
    })
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/google-login", response_model=Token)
async def google_login(credential: dict):
    """
    Login or signup with Google OAuth
    Body: {"credential": "access_token", "userInfo": {...}}
    """
    try:
        # Get user info from the request (already fetched by frontend)
        user_info = credential.get("userInfo")
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User info not provided"
            )
        
        # Extract user info
        email = user_info.get('email')
        username = user_info.get('name', email.split('@')[0] if email else 'user')
        google_id = user_info.get('sub')
        picture = user_info.get('picture', '')
        
        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or Google ID not provided"
            )
        
        db = get_database()
        users_collection = db.users
        
        # Check if user exists by email or google_id
        user = users_collection.find_one({
            "$or": [
                {"email": email},
                {"google_id": google_id}
            ]
        })
        
        if not user:
            # Create new user (auto-signup)
            # Ensure username is unique by adding suffix if needed
            base_username = username
            counter = 1
            while users_collection.find_one({"username": username}):
                username = f"{base_username}{counter}"
                counter += 1
            
            user_doc = {
                "username": username,
                "email": email,
                "google_id": google_id,
                "profile_picture": picture,
                "hashed_password": None,  # No password for OAuth users
                "created_at": datetime.utcnow(),
                "is_active": True,
                "is_admin": False,
                "auth_provider": "google"
            }
            result = users_collection.insert_one(user_doc)
            user = users_collection.find_one({"_id": result.inserted_id})
        else:
            # Update existing user with Google info if not set
            update_data = {}
            if not user.get("google_id"):
                update_data["google_id"] = google_id
            if not user.get("profile_picture"):
                update_data["profile_picture"] = picture
            if not user.get("auth_provider"):
                update_data["auth_provider"] = "google"
            
            if update_data:
                users_collection.update_one(
                    {"_id": user["_id"]},
                    {"$set": update_data}
                )
                user = users_collection.find_one({"_id": user["_id"]})
        
        # Create JWT access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )
