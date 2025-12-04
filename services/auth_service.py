# services/auth_service.py
"""
Authentication Service
Handles user authentication, JWT tokens, and authorization
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import enhanced_logger, settings

# Optional imports for authentication
try:
    from passlib.context import CryptContext

    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    CryptContext = None

try:
    from jose import JWTError as JoseJWTError
    from jose import jwt as jose_jwt

    JOSE_AVAILABLE = True
    jwt = jose_jwt
    # Use jose's JWTError if available
    AuthJWTError = JoseJWTError
except ImportError:
    JOSE_AVAILABLE = False
    jwt = None
    # Fallback to base Exception if jose is not available
    AuthJWTError = Exception


class AuthService:
    """
    Authentication and Authorization Service
    Handles user authentication, tokens, and permissions
    """

    def __init__(self):
        self.secret_key = settings.APP_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 7

        # Initialize password hashing
        if PASSLIB_AVAILABLE and CryptContext is not None:
            try:
                self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            except Exception as e:
                enhanced_logger.warning(
                    "Failed to initialize passlib CryptContext, falling back", error=str(e)
                )
                self.pwd_context = None
        else:
            self.pwd_context = None
            enhanced_logger.warning("passlib not available - using fallback hashing")

        # API keys storage (in production, use database)
        self._api_keys: Dict[str, Dict[str, Any]] = {}

        # Session storage
        self._sessions: Dict[str, Dict[str, Any]] = {}

        enhanced_logger.info(
            "AuthService initialized",
            jwt_available=JOSE_AVAILABLE,
            passlib_available=PASSLIB_AVAILABLE,
        )

    # Password Hashing
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        if self.pwd_context:
            return self.pwd_context.hash(password)
        else:
            # Fallback with salt for better security than plain SHA256
            # Note: This is still not recommended for production - install passlib
            import base64
            import os

            salt = base64.b64encode(os.urandom(16)).decode()
            salted_hash = hashlib.sha256(f"{salt}${password}".encode()).hexdigest()
            return f"{salt}${salted_hash}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if self.pwd_context:
            return self.pwd_context.verify(plain_password, hashed_password)
        else:
            # Fallback verification with salt
            if "$" not in hashed_password:
                # Legacy unsalted hash (backward compatibility)
                return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
            salt, stored_hash = hashed_password.split("$", 1)
            computed_hash = hashlib.sha256(f"{salt}${plain_password}".encode()).hexdigest()
            return computed_hash == stored_hash

    # JWT Token Management
    def create_access_token(
        self,
        user_id: str,
        username: str,
        role: str = "user",
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token"""
        if not JOSE_AVAILABLE or jwt is None:
            # Fallback: create a simple token
            return self._create_simple_token(user_id, username, role)

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token"""
        if not JOSE_AVAILABLE or jwt is None:
            return secrets.token_urlsafe(32)

        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4()),  # Unique token ID
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        if not JOSE_AVAILABLE or jwt is None:
            # Fallback to simple token verification
            return self._verify_simple_token(token)

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except AuthJWTError as e:
            enhanced_logger.warning("Token verification failed", error=str(e))
            return None
        except Exception as e:
            enhanced_logger.warning("Token verification failed", error=str(e))
            return None

    def _create_simple_token(self, user_id: str, username: str, role: str) -> str:
        """Create a simple token when JWT is not available"""
        import base64
        import json

        token_data = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": (
                datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            ).isoformat(),
        }

        data_str = json.dumps(token_data)
        signature = hashlib.sha256(f"{data_str}{self.secret_key}".encode()).hexdigest()[:16]

        return base64.urlsafe_b64encode(f"{data_str}|{signature}".encode()).decode()

    def _verify_simple_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a simple token"""
        import base64
        import json

        try:
            decoded = base64.urlsafe_b64decode(token).decode()
            data_str, signature = decoded.rsplit("|", 1)

            expected_signature = hashlib.sha256(
                f"{data_str}{self.secret_key}".encode()
            ).hexdigest()[:16]

            if signature != expected_signature:
                return None

            payload = json.loads(data_str)

            # Check expiration
            exp = datetime.fromisoformat(payload["exp"])
            if exp < datetime.utcnow():
                return None

            return payload
        except Exception:
            return None

    # API Key Management
    def create_api_key(
        self, user_id: str, name: str, permissions: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Create an API key for a user"""
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        key_id = str(uuid.uuid4())

        self._api_keys[api_key] = {
            "id": key_id,
            "user_id": user_id,
            "name": name,
            "permissions": permissions or ["read"],
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "active": True,
        }

        enhanced_logger.info("API key created", key_id=key_id, user_id=user_id, name=name)

        return {"id": key_id, "api_key": api_key, "name": name}

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key and return its data"""
        key_data = self._api_keys.get(api_key)

        if not key_data:
            return None

        if not key_data.get("active", True):
            return None

        # Update last used
        self._api_keys[api_key]["last_used"] = datetime.now().isoformat()

        return key_data

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        if api_key in self._api_keys:
            self._api_keys[api_key]["active"] = False
            enhanced_logger.info("API key revoked", key_id=self._api_keys[api_key]["id"])
            return True
        return False

    def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user"""
        keys = []
        for key, data in self._api_keys.items():
            if data["user_id"] == user_id:
                keys.append({**data, "api_key": f"{key[:8]}...{key[-4:]}"})  # Masked key
        return keys

    # Session Management
    def create_session(
        self, user_id: str, username: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a user session"""
        session_id = str(uuid.uuid4())

        self._sessions[session_id] = {
            "user_id": user_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "metadata": metadata or {},
            "active": True,
        }

        enhanced_logger.debug("Session created", session_id=session_id, user_id=user_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session = self._sessions.get(session_id)

        if session and session.get("active", True):
            # Update last activity
            self._sessions[session_id]["last_activity"] = datetime.now().isoformat()
            return session

        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        if session_id in self._sessions:
            self._sessions[session_id]["active"] = False
            enhanced_logger.debug("Session invalidated", session_id=session_id)
            return True
        return False

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        removed = 0

        expired_sessions = []
        for session_id, data in self._sessions.items():
            last_activity = datetime.fromisoformat(data["last_activity"])
            if last_activity < cutoff:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._sessions[session_id]
            removed += 1

        if removed:
            enhanced_logger.info("Expired sessions cleaned up", count=removed)

        return removed

    # Role-Based Access Control
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if a role has a specific permission"""
        role_permissions = {
            "admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings"],
            "moderator": ["read", "write", "delete", "manage_users"],
            "user": ["read", "write"],
            "guest": ["read"],
        }

        user_permissions = role_permissions.get(user_role, [])
        return required_permission in user_permissions

    def get_role_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role"""
        role_permissions = {
            "admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings"],
            "moderator": ["read", "write", "delete", "manage_users"],
            "user": ["read", "write"],
            "guest": ["read"],
        }
        return role_permissions.get(role, [])

    # Statistics
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        active_sessions = sum(1 for s in self._sessions.values() if s.get("active", True))
        active_api_keys = sum(1 for k in self._api_keys.values() if k.get("active", True))

        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active_sessions,
            "total_api_keys": len(self._api_keys),
            "active_api_keys": active_api_keys,
            "jwt_available": JOSE_AVAILABLE,
            "passlib_available": PASSLIB_AVAILABLE,
        }


# Global auth service instance
auth_service = AuthService()


__all__ = ["AuthService", "auth_service"]
