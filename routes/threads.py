# routes/threads.py
"""Message threading and reply functionality"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config.settings import enhanced_logger
from database.models import Message, MessageType
from database.repositories import MessageRepository

router = APIRouter()

# Initialize repository
message_repo = MessageRepository()

# In-memory thread tracking (in production, add to database)
message_threads: Dict[int, List[int]] = {}  # parent_id -> list of reply_ids
thread_metadata: Dict[int, Dict] = {}  # thread_id -> metadata


# ============================================================================
# Thread Models
# ============================================================================


class ThreadInfo(BaseModel):
    """Thread information model"""

    thread_id: int = Field(..., description="ID of the thread (parent message ID)")
    parent_message_id: int = Field(..., description="Parent message ID")
    reply_count: int = Field(default=0, description="Number of replies in thread")
    participant_count: int = Field(default=0, description="Number of unique participants")
    last_reply_at: Optional[datetime] = Field(None, description="Timestamp of last reply")
    created_at: datetime = Field(default_factory=datetime.now, description="Thread creation time")


class MessageWithThread(BaseModel):
    """Message with thread context"""

    message: Message
    thread_info: Optional[ThreadInfo] = None
    is_thread_parent: bool = False
    parent_message: Optional[Message] = None


# ============================================================================
# Thread Endpoints
# ============================================================================


@router.post("/api/messages/{message_id}/reply")
async def create_thread_reply(
    message_id: int,
    content: str = Query(..., description="Reply content", min_length=1),
    username: str = Query(..., description="Username of the person replying"),
    message_type: MessageType = Query(MessageType.USER, description="Type of message"),
):
    """
    Create a reply to a message (starts or continues a thread)
    
    - **message_id**: ID of the message to reply to
    - **content**: Reply message content
    - **username**: Username of the replier
    - **message_type**: Type of message
    """
    try:
        enhanced_logger.info(
            "Create thread reply",
            parent_id=message_id,
            username=username,
            content_length=len(content),
        )

        # Verify parent message exists
        parent_message = message_repo.get_message(message_id)
        if not parent_message:
            raise HTTPException(status_code=404, detail="Parent message not found")

        # Create reply message
        reply_message = Message(
            id=0,  # Will be auto-generated
            username=username,
            content=content,
            type=message_type,
            reply_to=message_id,  # Link to parent
            room_id=parent_message.room_id,
            project_id=parent_message.project_id,
            ticket_id=parent_message.ticket_id,
            created_at=datetime.now(),
        )

        # Save reply
        created_reply = message_repo.create_message(reply_message)

        # Update thread tracking
        if message_id not in message_threads:
            message_threads[message_id] = []
            thread_metadata[message_id] = {
                "created_at": datetime.now(),
                "participants": set(),
            }

        message_threads[message_id].append(created_reply.id)
        thread_metadata[message_id]["participants"].add(username)
        thread_metadata[message_id]["last_reply_at"] = datetime.now()

        # Build response
        thread_info = ThreadInfo(
            thread_id=message_id,
            parent_message_id=message_id,
            reply_count=len(message_threads[message_id]),
            participant_count=len(thread_metadata[message_id]["participants"]),
            last_reply_at=thread_metadata[message_id]["last_reply_at"],
            created_at=thread_metadata[message_id]["created_at"],
        )

        enhanced_logger.info(
            "Thread reply created",
            reply_id=created_reply.id,
            parent_id=message_id,
            thread_reply_count=thread_info.reply_count,
        )

        return {
            "message": "Reply created successfully",
            "reply": created_reply.model_dump(),
            "thread_info": thread_info.model_dump(),
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to create thread reply", message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create reply")


@router.get("/api/messages/{message_id}/thread")
async def get_message_thread(
    message_id: int,
    include_parent: bool = Query(True, description="Include parent message in response"),
    limit: int = Query(100, description="Maximum replies to return", ge=1, le=500),
):
    """
    Get all replies in a message thread
    
    - **message_id**: ID of the parent message
    - **include_parent**: Whether to include the parent message in response
    - **limit**: Maximum number of replies to return
    """
    try:
        enhanced_logger.info("Get message thread", message_id=message_id, include_parent=include_parent)

        # Get parent message
        parent_message = message_repo.get_message(message_id)
        if not parent_message:
            raise HTTPException(status_code=404, detail="Parent message not found")

        # Get thread replies
        reply_ids = message_threads.get(message_id, [])
        replies = []

        for reply_id in reply_ids[:limit]:
            reply = message_repo.get_message(reply_id)
            if reply:
                replies.append(reply)

        # Get thread info
        metadata = thread_metadata.get(message_id)
        thread_info = None

        if metadata:
            thread_info = ThreadInfo(
                thread_id=message_id,
                parent_message_id=message_id,
                reply_count=len(reply_ids),
                participant_count=len(metadata["participants"]),
                last_reply_at=metadata.get("last_reply_at"),
                created_at=metadata["created_at"],
            )

        enhanced_logger.info(
            "Message thread retrieved",
            message_id=message_id,
            reply_count=len(replies),
        )

        response = {
            "thread_id": message_id,
            "replies": [reply.model_dump() for reply in replies],
            "total_replies": len(reply_ids),
            "returned_replies": len(replies),
            "has_more": len(reply_ids) > limit,
        }

        if include_parent:
            response["parent_message"] = parent_message.model_dump()

        if thread_info:
            response["thread_info"] = thread_info.model_dump()

        return response

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to get message thread", message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve thread")


@router.get("/api/threads")
async def get_all_threads(
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    min_replies: int = Query(1, description="Minimum replies to include thread", ge=0),
    limit: int = Query(50, description="Maximum threads to return", ge=1, le=200),
):
    """
    Get all message threads with optional filtering
    
    - **room_id**: Filter threads by room
    - **project_id**: Filter threads by project
    - **min_replies**: Minimum number of replies to include thread
    - **limit**: Maximum threads to return
    """
    try:
        enhanced_logger.info(
            "Get all threads",
            room_id=room_id,
            project_id=project_id,
            min_replies=min_replies,
        )

        threads = []

        for parent_id, reply_ids in message_threads.items():
            # Skip threads with too few replies
            if len(reply_ids) < min_replies:
                continue

            # Get parent message for filtering
            parent_message = message_repo.get_message(parent_id)
            if not parent_message:
                continue

            # Apply filters
            if room_id and parent_message.room_id != room_id:
                continue
            if project_id and parent_message.project_id != project_id:
                continue

            # Build thread info
            metadata = thread_metadata.get(parent_id, {})
            thread_info = ThreadInfo(
                thread_id=parent_id,
                parent_message_id=parent_id,
                reply_count=len(reply_ids),
                participant_count=len(metadata.get("participants", set())),
                last_reply_at=metadata.get("last_reply_at"),
                created_at=metadata.get("created_at", datetime.now()),
            )

            threads.append(
                {
                    "parent_message": parent_message.model_dump(),
                    "thread_info": thread_info.model_dump(),
                }
            )

        # Sort by last activity (most recent first)
        threads.sort(
            key=lambda x: x["thread_info"]["last_reply_at"]
            if x["thread_info"]["last_reply_at"]
            else x["thread_info"]["created_at"],
            reverse=True,
        )

        # Apply limit
        threads = threads[:limit]

        enhanced_logger.info("Threads retrieved", total=len(threads))

        return {
            "threads": threads,
            "total": len(threads),
            "filters": {
                "room_id": room_id,
                "project_id": project_id,
                "min_replies": min_replies,
            },
        }

    except Exception as e:
        enhanced_logger.error("Failed to get threads", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve threads")


@router.get("/api/messages/{message_id}/thread/participants")
async def get_thread_participants(message_id: int):
    """
    Get list of participants in a message thread
    
    - **message_id**: ID of the parent message
    """
    try:
        enhanced_logger.info("Get thread participants", message_id=message_id)

        # Verify thread exists
        if message_id not in message_threads:
            raise HTTPException(status_code=404, detail="Thread not found")

        metadata = thread_metadata.get(message_id, {})
        participants = list(metadata.get("participants", set()))

        enhanced_logger.info(
            "Thread participants retrieved",
            message_id=message_id,
            participant_count=len(participants),
        )

        return {
            "thread_id": message_id,
            "participants": participants,
            "participant_count": len(participants),
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to get thread participants", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve participants")


@router.get("/api/threads/stats")
async def get_thread_stats():
    """Get overall thread statistics"""
    try:
        total_threads = len(message_threads)
        total_replies = sum(len(replies) for replies in message_threads.values())

        # Calculate average replies per thread
        avg_replies = total_replies / total_threads if total_threads > 0 else 0

        # Find most active threads
        most_active = sorted(
            [
                {"thread_id": tid, "reply_count": len(replies)}
                for tid, replies in message_threads.items()
            ],
            key=lambda x: x["reply_count"],
            reverse=True,
        )[:10]

        stats = {
            "total_threads": total_threads,
            "total_replies": total_replies,
            "average_replies_per_thread": round(avg_replies, 2),
            "most_active_threads": most_active,
        }

        enhanced_logger.info("Thread stats retrieved", total_threads=total_threads)

        return stats

    except Exception as e:
        enhanced_logger.error("Failed to get thread stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.delete("/api/messages/{message_id}/thread")
async def delete_thread(message_id: int, delete_replies: bool = Query(True, description="Delete all replies")):
    """
    Delete a thread (and optionally all its replies)
    
    - **message_id**: ID of the parent message
    - **delete_replies**: If true, delete all reply messages; if false, only unlink the thread
    """
    try:
        enhanced_logger.info(
            "Delete thread",
            message_id=message_id,
            delete_replies=delete_replies,
        )

        if message_id not in message_threads:
            raise HTTPException(status_code=404, detail="Thread not found")

        reply_ids = message_threads[message_id]
        deleted_count = 0

        if delete_replies:
            # Delete all reply messages
            for reply_id in reply_ids:
                try:
                    message_repo.delete_message(reply_id)
                    deleted_count += 1
                except Exception as e:
                    enhanced_logger.warning(f"Failed to delete reply {reply_id}: {e}")

        # Remove thread tracking
        del message_threads[message_id]
        if message_id in thread_metadata:
            del thread_metadata[message_id]

        enhanced_logger.info(
            "Thread deleted",
            message_id=message_id,
            deleted_replies=deleted_count,
        )

        return {
            "message": "Thread deleted successfully",
            "thread_id": message_id,
            "deleted_replies": deleted_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to delete thread", message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete thread")
