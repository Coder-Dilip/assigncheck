from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....core.security import create_access_token, verify_password, get_password_hash, verify_token
from ....core.config import settings
from ....models.user import User, UserRole
from ....schemas.auth import Token, UserCreate, UserResponse
from ....schemas.user import UserLogin
from datetime import datetime
import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    print(f"DEBUG: get_current_user called with token: {token[:20] if token else 'None'}...")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("DEBUG: No token received by get_current_user")
        # Try to get token from Authorization header directly as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            print(f"DEBUG: Extracted token from Authorization header: {token[:20]}...")
        else:
            print("DEBUG: No token in Authorization header either")
            raise credentials_exception
    
    try:
        user_id = verify_token(token)
        print(f"DEBUG: Token verification result - user_id: {user_id}")
        
        if not user_id:
            print("DEBUG: Token verification failed - invalid token")
            raise credentials_exception
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        print(f"DEBUG: User lookup result: {user.username if user else 'Not found'}")
        
        if not user:
            print("DEBUG: User not found in database")
            raise credentials_exception
            
        if not user.is_active:
            print("DEBUG: User account is inactive")
            raise HTTPException(status_code=400, detail="Inactive user")
        
        print(f"DEBUG: Authentication successful for user: {user.username}")
        return user
        
    except jwt.ExpiredSignatureError:
        print("DEBUG: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"DEBUG: Error during authentication: {str(e)}")
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_teacher(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current teacher user"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Teacher role required."
        )
    return current_user


def get_current_student(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current student user"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Student role required."
        )
    return current_user


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        bio=user_data.bio
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access token"""
    # Debug logging
    print(f"DEBUG: Login attempt - username: {form_data.username}")
    print(f"DEBUG: Form data received: {form_data}")
    
    # Try to find user by username first, then by email
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        # If not found by username, try by email
        user = db.query(User).filter(User.email == form_data.username).first()
        print(f"DEBUG: Tried email lookup for: {form_data.username}")
    
    print(f"DEBUG: User found: {user is not None}")
    
    if user:
        print(f"DEBUG: User details - username: {user.username}, email: {user.email}, active: {user.is_active}")
        password_valid = verify_password(form_data.password, user.hashed_password)
        print(f"DEBUG: Password valid: {password_valid}")
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        print("DEBUG: Authentication failed - incorrect credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        print("DEBUG: Authentication failed - inactive user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    print("DEBUG: Authentication successful, creating token")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Return properly formatted response
    user_data = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        profile_picture=user.profile_picture,
        bio=user.bio,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user
    }
