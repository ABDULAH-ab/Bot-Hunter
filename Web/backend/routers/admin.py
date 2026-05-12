from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from database import get_database
from auth_utils import get_current_admin_user
from bson import ObjectId

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)

# Models for admin operations
class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    google_auth_users: int
    traditional_auth_users: int
    users_last_24h: int
    users_last_week: int

class SystemStats(BaseModel):
    total_tweets: int
    total_hashtags: int
    total_analysis: int
    database_size: str

# User Management Endpoints
@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_admin: Optional[bool] = None,
    is_active: Optional[bool] = None
):
    """Get all users with optional filtering"""
    db = get_database()
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if is_admin is not None:
        query["is_admin"] = is_admin
    if is_active is not None:
        query["is_active"] = is_active
    
    # Get users
    users = list(db.users.find(query).skip(skip).limit(limit))
    total = db.users.count_documents(query)
    
    # Convert ObjectId to string and remove password
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/users/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def get_user_by_id(user_id: str):
    """Get specific user details"""
    db = get_database()
    
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    user.pop("password", None)
    
    return user

@router.patch("/users/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user status or admin privileges"""
    db = get_database()
    
    # Prepare update data
    update_data = {}
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    if user_update.is_admin is not None:
        update_data["is_admin"] = user_update.is_admin
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User updated successfully"}

@router.delete("/users/{user_id}", dependencies=[Depends(get_current_admin_user)])
async def delete_user(user_id: str):
    """Delete a user (soft delete by setting is_active=False)"""
    db = get_database()
    
    try:
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}

# Statistics Endpoints
@router.get("/stats/users", response_model=UserStats, dependencies=[Depends(get_current_admin_user)])
async def get_user_stats():
    """Get user statistics"""
    db = get_database()
    
    # Get current time for date-based queries
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)
    
    total_users = db.users.count_documents({})
    active_users = db.users.count_documents({"is_active": True})
    admin_users = db.users.count_documents({"is_admin": True})
    google_auth_users = db.users.count_documents({"auth_provider": "google"})
    traditional_auth_users = db.users.count_documents({"auth_provider": {"$ne": "google"}})
    users_last_24h = db.users.count_documents({"created_at": {"$gte": last_24h}})
    users_last_week = db.users.count_documents({"created_at": {"$gte": last_week}})
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        google_auth_users=google_auth_users,
        traditional_auth_users=traditional_auth_users,
        users_last_24h=users_last_24h,
        users_last_week=users_last_week
    )

@router.get("/stats/system", response_model=SystemStats, dependencies=[Depends(get_current_admin_user)])
async def get_system_stats():
    """Get system statistics"""
    db = get_database()
    
    total_tweets = db.tweets.count_documents({})
    total_hashtags = db.hashtags.count_documents({})
    total_analysis = db.analysis_results.count_documents({})
    
    # Get database size (approximate)
    stats = db.command("dbStats")
    db_size = f"{stats.get('dataSize', 0) / (1024**2):.2f} MB"
    
    return SystemStats(
        total_tweets=total_tweets,
        total_hashtags=total_hashtags,
        total_analysis=total_analysis,
        database_size=db_size
    )

@router.get("/recent-activity", dependencies=[Depends(get_current_admin_user)])
async def get_recent_activity(limit: int = 20):
    """Get recent user activity"""
    db = get_database()
    
    # Get recently registered users
    recent_users = list(db.users.find(
        {},
        {"username": 1, "email": 1, "created_at": 1, "auth_provider": 1}
    ).sort("created_at", -1).limit(limit))
    
    for user in recent_users:
        user["_id"] = str(user["_id"])
    
    return {
        "recent_users": recent_users
    }
