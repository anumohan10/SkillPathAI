from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.services.auth_service import (
    hash_password, check_password,
    create_users_table, insert_user,
    get_user_by_username, update_user_password, get_user_profile_by_username
)
from typing import Optional

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Create users table when the API starts
# create_users_table()

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    name: str
    username: str
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str
    
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate):
    # Check if username already exists
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_id = insert_user(
        user_data.name,
        user_data.username,
        user_data.email,
        hashed_password
    )
    
    return {
        "user_id": user_id,
        "name": user_data.name,
        "username": user_data.username,
        "email": user_data.email
    }

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    user = get_user_by_username(login_data.username)
    if not user or not check_password(login_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # In a real implementation, create a JWT token here
    # For now, we'll just return a dummy token
    return {
        "access_token": "dummy_token_" + user["user_id"],
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "name": user["name"],
            "username": login_data.username,
            "email": user.get("email")
        }
    }
@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    user = get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = hash_password(request.new_password)
    success = update_user_password(request.username, hashed_pw)

    if success:
        return {"message": "Password updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update password")

@router.get("/user-profile", response_model=UserResponse)
def get_user_profile(username: str):
    user = get_user_profile_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "username": user["username"],
        "email": user["email"]
    }