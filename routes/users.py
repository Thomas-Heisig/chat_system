# routes/users.py
"""User management and presence API endpoints"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from config.settings import enhanced_logger
from database.models import User, UserRole
from database.repositories import UserRepository

router = APIRouter()

# Initialize repository
user_repository = UserRepository()

# In-memory presence tracking (in production, use Redis)
user_presence: Dict[str, Dict[str, any]] = {}


@router.get("/api/users", response_model=List[User])
async def get_all_users(
    limit: int = Query(100, description="Maximum users to return", ge=1, le=500),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """
    Get all users with filtering and pagination
    
    - **limit**: Maximum number of users to return
    - **offset**: Number of users to skip for pagination
    - **role**: Filter by user role (user, admin, moderator, manager)
    - **is_active**: Filter by active status
    """
    try:
        enhanced_logger.info(
            "Get all users requested",
            limit=limit,
            offset=offset,
            role=role,
            is_active=is_active,
        )

        users = user_repository.get_users(
            limit=limit, offset=offset, role=role, is_active=is_active
        )

        enhanced_logger.info("Users retrieved successfully", count=len(users))
        return users

    except Exception as e:
        enhanced_logger.error("Failed to retrieve users", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    try:
        user = user_repository.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        enhanced_logger.info("User retrieved", user_id=user_id)
        return user

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to retrieve user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve user")


@router.post("/api/users", response_model=User, status_code=201)
async def create_user(user: User):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = user_repository.get_user(user.id)
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        created_user = user_repository.create_user(user)
        enhanced_logger.info("User created", user_id=user.id, username=user.username)
        return created_user

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to create user", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.put("/api/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    """Update an existing user"""
    try:
        # Verify user exists
        existing_user = user_repository.get_user(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Ensure ID matches
        user.id = user_id

        updated_user = user_repository.update_user(user)
        enhanced_logger.info("User updated", user_id=user_id)
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to update user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user (soft delete - sets is_active to False)"""
    try:
        user = user_repository.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Soft delete
        user.is_active = False
        user_repository.update_user(user)

        enhanced_logger.info("User deleted", user_id=user_id)
        return {"message": "User deleted successfully", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to delete user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete user")


# ============================================================================
# User Presence and Status Endpoints
# ============================================================================


@router.post("/api/users/{user_id}/presence")
async def update_user_presence(
    user_id: str,
    status: str = Query(..., description="User status: online, away, busy, offline"),
    status_message: Optional[str] = Query(None, description="Custom status message"),
):
    """
    Update user presence status
    
    - **status**: User status (online, away, busy, offline)
    - **status_message**: Optional custom status message
    """
    try:
        # Validate status
        valid_statuses = ["online", "away", "busy", "offline"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        # Update presence
        user_presence[user_id] = {
            "status": status,
            "status_message": status_message,
            "last_seen": datetime.now().isoformat(),
        }

        enhanced_logger.info(
            "User presence updated", user_id=user_id, status=status, message=status_message
        )

        return {
            "user_id": user_id,
            "status": status,
            "status_message": status_message,
            "updated_at": user_presence[user_id]["last_seen"],
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to update user presence", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update user presence")


@router.get("/api/users/{user_id}/presence")
async def get_user_presence(user_id: str):
    """Get user presence status"""
    try:
        if user_id not in user_presence:
            return {
                "user_id": user_id,
                "status": "offline",
                "status_message": None,
                "last_seen": None,
            }

        presence = user_presence[user_id]
        enhanced_logger.info("User presence retrieved", user_id=user_id, status=presence["status"])

        return {
            "user_id": user_id,
            "status": presence["status"],
            "status_message": presence.get("status_message"),
            "last_seen": presence["last_seen"],
        }

    except Exception as e:
        enhanced_logger.error("Failed to get user presence", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user presence")


@router.get("/api/users/presence/online")
async def get_online_users():
    """Get list of all currently online users"""
    try:
        online_users = []
        current_time = datetime.now()

        for user_id, presence in user_presence.items():
            if presence["status"] in ["online", "away", "busy"]:
                # Check if last seen is within last 5 minutes
                last_seen = datetime.fromisoformat(presence["last_seen"])
                if (current_time - last_seen).total_seconds() < 300:  # 5 minutes
                    online_users.append(
                        {
                            "user_id": user_id,
                            "status": presence["status"],
                            "status_message": presence.get("status_message"),
                            "last_seen": presence["last_seen"],
                        }
                    )

        enhanced_logger.info("Online users retrieved", count=len(online_users))
        return {"online_users": online_users, "total_online": len(online_users)}

    except Exception as e:
        enhanced_logger.error("Failed to get online users", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get online users")


# ============================================================================
# User Activity and Statistics
# ============================================================================


@router.get("/api/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    days: int = Query(7, description="Number of days to look back", ge=1, le=90),
):
    """
    Get user activity statistics
    
    - **days**: Number of days to analyze (1-90)
    """
    try:
        from database.repositories import MessageRepository

        message_repo = MessageRepository()

        # Get user's message count
        messages = message_repo.get_messages_by_user(user_id, limit=10000)

        # Calculate activity
        since_date = datetime.now() - timedelta(days=days)
        recent_messages = [msg for msg in messages if msg.created_at >= since_date]

        activity_data = {
            "user_id": user_id,
            "timeframe_days": days,
            "total_messages": len(recent_messages),
            "average_messages_per_day": len(recent_messages) / days if days > 0 else 0,
            "most_active_hour": None,  # Would need more complex calculation
            "first_message": recent_messages[-1].created_at if recent_messages else None,
            "last_message": recent_messages[0].created_at if recent_messages else None,
        }

        enhanced_logger.info("User activity retrieved", user_id=user_id, days=days)
        return activity_data

    except Exception as e:
        enhanced_logger.error("Failed to get user activity", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user activity")


@router.get("/api/users/stats/summary")
async def get_users_summary():
    """Get summary statistics for all users"""
    try:
        users = user_repository.get_users(limit=10000)

        # Calculate statistics
        total_users = len(users)
        active_users = len([u for u in users if u.is_active])
        role_counts = {}

        for user in users:
            role = user.role
            role_counts[role] = role_counts.get(role, 0) + 1

        summary = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts,
            "currently_online": len([uid for uid, p in user_presence.items() if p["status"] == "online"]),
        }

        enhanced_logger.info("User summary retrieved", total_users=total_users)
        return summary

    except Exception as e:
        enhanced_logger.error("Failed to get user summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user summary")
