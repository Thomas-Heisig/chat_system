"""
🔐 Authentication & Authorization Module

Provides JWT-based authentication and Role-Based Access Control (RBAC)
for the Chat System.

TODO:
- [ ] Implement OAuth2 provider integration (Google, GitHub, etc.)
- [ ] Add multi-factor authentication (MFA)
- [ ] Implement refresh token rotation
- [ ] Add session management with Redis
- [ ] Implement audit logging for auth events
- [ ] Add rate limiting for login attempts
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config.settings import logger, settings


# Security configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


class Role(str, Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class Permission(str, Enum):
    """Granular permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MODERATE_CHAT = "moderate_chat"
    MANAGE_PLUGINS = "manage_plugins"
    MANAGE_ROOMS = "manage_rooms"
    ADMIN_ACCESS = "admin_access"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.ADMIN: list(Permission),  # All permissions
    Role.MODERATOR: [
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.MODERATE_CHAT,
        Permission.MANAGE_ROOMS,
    ],
    Role.USER: [
        Permission.READ,
        Permission.WRITE,
    ],
    Role.GUEST: [
        Permission.READ,
    ],
}


class User(BaseModel):
    """User model for authentication"""
    id: str
    username: str
    email: str
    role: Role = Role.USER
    is_active: bool = True
    created_at: datetime = datetime.now()


class TokenData(BaseModel):
    """JWT token payload data"""
    sub: str  # Subject (user_id)
    role: str
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


# ==================== Password Hashing ====================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Token Management ====================

def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        user_id: User identifier
        role: User role
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(f"Access token created for user {user_id}")
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object with decoded payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        iat: datetime = datetime.fromtimestamp(payload.get("iat"))
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(sub=user_id, role=role, exp=exp, iat=iat)
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==================== Dependency Injection ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
        
    TODO:
    - [ ] Fetch user from database instead of creating stub
    - [ ] Check user is_active status
    - [ ] Implement token blacklist for logout
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    # TODO: Fetch user from database
    # For now, create a stub user from token data
    user = User(
        id=token_data.sub,
        username=f"user_{token_data.sub}",
        email=f"user_{token_data.sub}@example.com",
        role=Role(token_data.role),
        is_active=True,
    )
    
    logger.debug(f"Authenticated user: {user.username} (role: {user.role})")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# ==================== Authorization / RBAC ====================

def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission
    
    Args:
        user: User object
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def require_permission(permission: Permission):
    """
    Dependency factory to require a specific permission
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
        
    Example:
        @app.get("/admin")
        async def admin_endpoint(user: User = Depends(require_permission(Permission.ADMIN_ACCESS))):
            return {"message": "Admin access granted"}
    """
    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(user, permission):
            logger.warning(
                f"Permission denied for user {user.username}: "
                f"required={permission}, role={user.role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return user
    
    return permission_checker


def require_role(required_role: Role):
    """
    Dependency factory to require a specific role or higher
    
    Args:
        required_role: Minimum required role
        
    Returns:
        Dependency function
        
    Example:
        @app.get("/moderator")
        async def moderator_endpoint(user: User = Depends(require_role(Role.MODERATOR))):
            return {"message": "Moderator access granted"}
    """
    role_hierarchy = {
        Role.GUEST: 0,
        Role.USER: 1,
        Role.MODERATOR: 2,
        Role.ADMIN: 3,
    }
    
    async def role_checker(user: User = Depends(get_current_active_user)) -> User:
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            logger.warning(
                f"Role requirement not met for user {user.username}: "
                f"required={required_role}, actual={user.role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role} or higher"
            )
        return user
    
    return role_checker


# ==================== Authentication Endpoints (Stubs) ====================

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
        
    TODO:
    - [ ] Implement actual database lookup
    - [ ] Add rate limiting for failed attempts
    - [ ] Log authentication attempts
    - [ ] Implement account lockout after N failed attempts
    
    SECURITY WARNING: This is a STUB implementation for development only!
    DO NOT USE IN PRODUCTION without implementing proper database authentication.
    """
    # TODO: Fetch user from database and verify password
    # This is a stub implementation
    logger.warning("authenticate_user is a stub - implement database lookup")
    
    # DEVELOPMENT ONLY: Return None to disable authentication in stub mode
    # Remove this check and implement proper authentication for production
    if os.getenv("APP_ENVIRONMENT") == "production":
        raise NotImplementedError(
            "Authentication stub cannot be used in production. "
            "Implement proper database-backed authentication."
        )
    
    # Development stub: Only allow authentication if explicitly enabled
    if os.getenv("ENABLE_STUB_AUTH", "false").lower() != "true":
        return None
    
    # Stub: Accept specific test user for development
    if username == "test_user" and password == "test_password":
        return User(
            id=f"user_{username}",
            username=username,
            email=f"{username}@example.com",
            role=Role.USER,
        )
    
    return None


async def login(login_request: LoginRequest) -> TokenResponse:
    """
    Login endpoint handler
    
    Args:
        login_request: Login request with username and password
        
    Returns:
        TokenResponse with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await authenticate_user(login_request.username, login_request.password)
    
    if not user:
        logger.warning(f"Failed login attempt for username: {login_request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        user_id=user.id,
        role=user.role.value,
    )
    
    logger.info(f"Successful login for user: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
        }
    )


# ==================== Optional Token from Header ====================

async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """
    Get user from optional authorization header
    Useful for endpoints that work both authenticated and unauthenticated
    
    Args:
        authorization: Optional Authorization header
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        token_data = decode_token(token)
        
        # TODO: Fetch from database
        user = User(
            id=token_data.sub,
            username=f"user_{token_data.sub}",
            email=f"user_{token_data.sub}@example.com",
            role=Role(token_data.role),
            is_active=True,
        )
        return user
    except HTTPException:
        return None


# ==================== Utility Functions ====================

def get_user_permissions(user: User) -> List[Permission]:
    """Get all permissions for a user based on their role"""
    return ROLE_PERMISSIONS.get(user.role, [])


def check_resource_access(user: User, resource_owner_id: str) -> bool:
    """
    Check if user can access a resource
    Users can access their own resources, admins can access all
    
    Args:
        user: User requesting access
        resource_owner_id: ID of the resource owner
        
    Returns:
        True if access allowed
    """
    if user.role == Role.ADMIN:
        return True
    return user.id == resource_owner_id


logger.info("Auth module initialized with RBAC support")
