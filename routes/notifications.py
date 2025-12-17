# routes/notifications.py
"""Real-time notification system for users"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.settings import enhanced_logger

router = APIRouter()


# ============================================================================
# Notification Models
# ============================================================================


class NotificationType(str, Enum):
    """Types of notifications"""

    MESSAGE = "message"  # New message in a room/channel
    MENTION = "mention"  # User was mentioned in a message
    REPLY = "reply"  # Someone replied to user's message
    REACTION = "reaction"  # Someone reacted to user's message
    PROJECT_UPDATE = "project_update"  # Project status change
    TICKET_ASSIGNED = "ticket_assigned"  # Ticket assigned to user
    TICKET_UPDATE = "ticket_update"  # Ticket updated
    SYSTEM = "system"  # System notification
    ALERT = "alert"  # Important alert
    INFO = "info"  # Informational notification


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Notification model"""

    id: str = Field(..., description="Unique notification ID")
    user_id: str = Field(..., description="User ID who receives the notification")
    type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Priority level"
    )
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message content")
    data: Optional[Dict] = Field(default=None, description="Additional data")
    link: Optional[str] = Field(default=None, description="Link to related resource")
    is_read: bool = Field(default=False, description="Whether notification has been read")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    read_at: Optional[datetime] = Field(default=None, description="When notification was read")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp")


# In-memory notification storage (in production, use Redis or database)
notifications_store: Dict[str, List[Notification]] = {}
notification_settings: Dict[str, Dict] = {}


# ============================================================================
# Notification Endpoints
# ============================================================================


@router.get("/api/notifications")
async def get_notifications(
    user_id: str = Query(..., description="User ID to get notifications for"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    limit: int = Query(50, description="Maximum notifications to return", ge=1, le=200),
    offset: int = Query(0, description="Offset for pagination", ge=0),
):
    """
    Get notifications for a user
    
    - **user_id**: User ID to fetch notifications for
    - **unread_only**: If true, return only unread notifications
    - **limit**: Maximum number of notifications
    - **offset**: Pagination offset
    """
    try:
        enhanced_logger.info(
            "Get notifications requested",
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
        )

        # Get user's notifications
        user_notifications = notifications_store.get(user_id, [])

        # Filter unread if requested
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.is_read]

        # Sort by creation time (newest first)
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(user_notifications)
        paginated = user_notifications[offset : offset + limit]

        enhanced_logger.info(
            "Notifications retrieved",
            user_id=user_id,
            total=total,
            returned=len(paginated),
        )

        return {
            "notifications": [n.model_dump() for n in paginated],
            "total": total,
            "unread_count": len([n for n in user_notifications if not n.is_read]),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        }

    except Exception as e:
        enhanced_logger.error("Failed to get notifications", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


@router.post("/api/notifications", status_code=201)
async def create_notification(notification: Notification):
    """
    Create a new notification for a user
    
    - **notification**: Notification object to create
    """
    try:
        enhanced_logger.info(
            "Create notification requested",
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
        )

        # Initialize user's notification list if needed
        if notification.user_id not in notifications_store:
            notifications_store[notification.user_id] = []

        # Add notification
        notifications_store[notification.user_id].append(notification)

        enhanced_logger.info(
            "Notification created",
            notification_id=notification.id,
            user_id=notification.user_id,
        )

        return {
            "message": "Notification created successfully",
            "notification": notification.model_dump(),
        }

    except Exception as e:
        enhanced_logger.error("Failed to create notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, user_id: str = Query(..., description="User ID")
):
    """
    Mark a notification as read
    
    - **notification_id**: ID of notification to mark as read
    - **user_id**: User ID who owns the notification
    """
    try:
        enhanced_logger.info(
            "Mark notification read",
            notification_id=notification_id,
            user_id=user_id,
        )

        # Find notification
        user_notifications = notifications_store.get(user_id, [])
        notification = next((n for n in user_notifications if n.id == notification_id), None)

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Mark as read
        notification.is_read = True
        notification.read_at = datetime.now()

        enhanced_logger.info("Notification marked as read", notification_id=notification_id)

        return {
            "message": "Notification marked as read",
            "notification": notification.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to mark notification as read", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.put("/api/notifications/read-all")
async def mark_all_notifications_read(user_id: str = Query(..., description="User ID")):
    """
    Mark all notifications as read for a user
    
    - **user_id**: User ID
    """
    try:
        enhanced_logger.info("Mark all notifications read", user_id=user_id)

        user_notifications = notifications_store.get(user_id, [])
        marked_count = 0

        for notification in user_notifications:
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now()
                marked_count += 1

        enhanced_logger.info(
            "All notifications marked as read",
            user_id=user_id,
            marked_count=marked_count,
        )

        return {
            "message": "All notifications marked as read",
            "user_id": user_id,
            "marked_count": marked_count,
        }

    except Exception as e:
        enhanced_logger.error("Failed to mark all notifications as read", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update notifications")


@router.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: str, user_id: str = Query(..., description="User ID")
):
    """
    Delete a notification
    
    - **notification_id**: ID of notification to delete
    - **user_id**: User ID who owns the notification
    """
    try:
        enhanced_logger.info("Delete notification", notification_id=notification_id, user_id=user_id)

        user_notifications = notifications_store.get(user_id, [])
        original_count = len(user_notifications)

        # Remove notification
        notifications_store[user_id] = [
            n for n in user_notifications if n.id != notification_id
        ]

        if len(notifications_store[user_id]) == original_count:
            raise HTTPException(status_code=404, detail="Notification not found")

        enhanced_logger.info("Notification deleted", notification_id=notification_id)

        return {"message": "Notification deleted successfully", "notification_id": notification_id}

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to delete notification", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.delete("/api/notifications/clear-all")
async def clear_all_notifications(user_id: str = Query(..., description="User ID")):
    """
    Clear all notifications for a user
    
    - **user_id**: User ID
    """
    try:
        enhanced_logger.info("Clear all notifications", user_id=user_id)

        deleted_count = len(notifications_store.get(user_id, []))
        notifications_store[user_id] = []

        enhanced_logger.info("All notifications cleared", user_id=user_id, deleted_count=deleted_count)

        return {
            "message": "All notifications cleared",
            "user_id": user_id,
            "deleted_count": deleted_count,
        }

    except Exception as e:
        enhanced_logger.error("Failed to clear notifications", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear notifications")


# ============================================================================
# Notification Settings
# ============================================================================


@router.get("/api/notifications/settings")
async def get_notification_settings(user_id: str = Query(..., description="User ID")):
    """
    Get notification settings for a user
    
    - **user_id**: User ID
    """
    try:
        settings = notification_settings.get(
            user_id,
            {
                "enabled": True,
                "email_notifications": False,
                "push_notifications": True,
                "sound_enabled": True,
                "types_enabled": {
                    "message": True,
                    "mention": True,
                    "reply": True,
                    "reaction": True,
                    "project_update": True,
                    "ticket_assigned": True,
                    "ticket_update": True,
                    "system": True,
                    "alert": True,
                    "info": True,
                },
            },
        )

        enhanced_logger.info("Notification settings retrieved", user_id=user_id)

        return {"user_id": user_id, "settings": settings}

    except Exception as e:
        enhanced_logger.error("Failed to get notification settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")


@router.put("/api/notifications/settings")
async def update_notification_settings(
    user_id: str = Query(..., description="User ID"), settings: Dict = None
):
    """
    Update notification settings for a user
    
    - **user_id**: User ID
    - **settings**: Settings object with preferences
    """
    try:
        enhanced_logger.info("Update notification settings", user_id=user_id)

        if settings is None:
            raise HTTPException(status_code=400, detail="Settings object required")

        notification_settings[user_id] = settings

        enhanced_logger.info("Notification settings updated", user_id=user_id)

        return {
            "message": "Notification settings updated successfully",
            "user_id": user_id,
            "settings": settings,
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to update notification settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update settings")


# ============================================================================
# Notification Statistics
# ============================================================================


@router.get("/api/notifications/stats")
async def get_notification_stats(user_id: str = Query(..., description="User ID")):
    """
    Get notification statistics for a user
    
    - **user_id**: User ID
    """
    try:
        user_notifications = notifications_store.get(user_id, [])

        stats = {
            "total_notifications": len(user_notifications),
            "unread_count": len([n for n in user_notifications if not n.is_read]),
            "read_count": len([n for n in user_notifications if n.is_read]),
            "by_type": {},
            "by_priority": {},
        }

        # Count by type
        for notification in user_notifications:
            stats["by_type"][notification.type] = (
                stats["by_type"].get(notification.type, 0) + 1
            )
            stats["by_priority"][notification.priority] = (
                stats["by_priority"].get(notification.priority, 0) + 1
            )

        enhanced_logger.info("Notification stats retrieved", user_id=user_id)

        return {"user_id": user_id, "stats": stats}

    except Exception as e:
        enhanced_logger.error("Failed to get notification stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
