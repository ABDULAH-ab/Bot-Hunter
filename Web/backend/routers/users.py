from fastapi import APIRouter, Depends
from routers.auth import get_current_user
from models import UserResponse

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    return current_user
