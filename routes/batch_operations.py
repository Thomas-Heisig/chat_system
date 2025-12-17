# routes/batch_operations.py
"""Batch operations API for efficient bulk data manipulation"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config.settings import enhanced_logger
from database.models import Message, MessageType
from database.repositories import MessageRepository, UserRepository

router = APIRouter()

# Initialize repositories
message_repo = MessageRepository()
user_repo = UserRepository()


# ============================================================================
# Request/Response Models
# ============================================================================


class BatchMessageCreate(BaseModel):
    """Model for batch message creation"""

    messages: List[Message]


class BatchMessageUpdate(BaseModel):
    """Model for batch message updates"""

    message_ids: List[int]
    updates: Dict[str, any]


class BatchMessageDelete(BaseModel):
    """Model for batch message deletion"""

    message_ids: List[int]
    soft_delete: bool = True


class BatchOperationResult(BaseModel):
    """Result of a batch operation"""

    success: bool
    total_requested: int
    successful: int
    failed: int
    errors: List[Dict[str, any]] = []
    duration_seconds: float


# ============================================================================
# Batch Message Operations
# ============================================================================


@router.post("/api/batch/messages/create", response_model=BatchOperationResult)
async def batch_create_messages(request: BatchMessageCreate):
    """
    Create multiple messages in a single operation
    
    Useful for importing historical data or bulk message insertion.
    
    - **messages**: List of message objects to create
    """
    start_time = datetime.now()

    try:
        enhanced_logger.info("Batch message creation requested", count=len(request.messages))

        successful = 0
        failed = 0
        errors = []

        for idx, message in enumerate(request.messages):
            try:
                message_repo.create_message(message)
                successful += 1
            except Exception as e:
                failed += 1
                errors.append(
                    {
                        "index": idx,
                        "message_id": message.id,
                        "error": str(e),
                    }
                )

        duration = (datetime.now() - start_time).total_seconds()

        enhanced_logger.info(
            "Batch message creation completed",
            total=len(request.messages),
            successful=successful,
            failed=failed,
            duration=duration,
        )

        return BatchOperationResult(
            success=(failed == 0),
            total_requested=len(request.messages),
            successful=successful,
            failed=failed,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        enhanced_logger.error("Batch message creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch creation failed")


@router.put("/api/batch/messages/update", response_model=BatchOperationResult)
async def batch_update_messages(request: BatchMessageUpdate):
    """
    Update multiple messages with the same changes
    
    Useful for bulk operations like marking messages as read, updating types, etc.
    
    - **message_ids**: List of message IDs to update
    - **updates**: Dictionary of field updates to apply
    """
    start_time = datetime.now()

    try:
        enhanced_logger.info(
            "Batch message update requested",
            count=len(request.message_ids),
            updates=request.updates,
        )

        successful = 0
        failed = 0
        errors = []

        for message_id in request.message_ids:
            try:
                message = message_repo.get_message(message_id)
                if not message:
                    failed += 1
                    errors.append({"message_id": message_id, "error": "Message not found"})
                    continue

                # Apply updates
                for key, value in request.updates.items():
                    if hasattr(message, key):
                        setattr(message, key, value)

                message_repo.update_message(message)
                successful += 1

            except Exception as e:
                failed += 1
                errors.append({"message_id": message_id, "error": str(e)})

        duration = (datetime.now() - start_time).total_seconds()

        enhanced_logger.info(
            "Batch message update completed",
            total=len(request.message_ids),
            successful=successful,
            failed=failed,
            duration=duration,
        )

        return BatchOperationResult(
            success=(failed == 0),
            total_requested=len(request.message_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        enhanced_logger.error("Batch message update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch update failed")


@router.delete("/api/batch/messages/delete", response_model=BatchOperationResult)
async def batch_delete_messages(request: BatchMessageDelete):
    """
    Delete multiple messages at once
    
    Supports both soft delete (mark as deleted) and hard delete (remove from database).
    
    - **message_ids**: List of message IDs to delete
    - **soft_delete**: If true, mark as deleted; if false, remove from database
    """
    start_time = datetime.now()

    try:
        enhanced_logger.info(
            "Batch message deletion requested",
            count=len(request.message_ids),
            soft_delete=request.soft_delete,
        )

        successful = 0
        failed = 0
        errors = []

        for message_id in request.message_ids:
            try:
                if request.soft_delete:
                    # Soft delete: mark as deleted
                    message = message_repo.get_message(message_id)
                    if message:
                        message.is_deleted = True
                        message_repo.update_message(message)
                        successful += 1
                    else:
                        failed += 1
                        errors.append({"message_id": message_id, "error": "Message not found"})
                else:
                    # Hard delete: remove from database
                    success = message_repo.delete_message(message_id)
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        errors.append({"message_id": message_id, "error": "Delete failed"})

            except Exception as e:
                failed += 1
                errors.append({"message_id": message_id, "error": str(e)})

        duration = (datetime.now() - start_time).total_seconds()

        enhanced_logger.info(
            "Batch message deletion completed",
            total=len(request.message_ids),
            successful=successful,
            failed=failed,
            duration=duration,
        )

        return BatchOperationResult(
            success=(failed == 0),
            total_requested=len(request.message_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            duration_seconds=duration,
        )

    except Exception as e:
        enhanced_logger.error("Batch message deletion failed", error=str(e))
        raise HTTPException(status_code=500, detail="Batch deletion failed")


# ============================================================================
# Batch Analysis Operations
# ============================================================================


@router.post("/api/batch/messages/analyze")
async def batch_analyze_messages(
    message_ids: List[int] = Query(..., description="List of message IDs to analyze")
):
    """
    Analyze multiple messages for patterns, sentiment, etc.
    
    Returns aggregated statistics and insights from the message batch.
    
    - **message_ids**: List of message IDs to analyze
    """
    try:
        start_time = datetime.now()

        enhanced_logger.info("Batch message analysis requested", count=len(message_ids))

        messages = []
        for msg_id in message_ids:
            msg = message_repo.get_message(msg_id)
            if msg:
                messages.append(msg)

        if not messages:
            raise HTTPException(status_code=404, detail="No messages found")

        # Analyze messages
        analysis = {
            "total_messages": len(messages),
            "total_characters": sum(len(msg.content) for msg in messages),
            "average_length": sum(len(msg.content) for msg in messages) / len(messages)
            if messages
            else 0,
            "message_types": {},
            "users": set(),
            "time_range": {
                "earliest": min(msg.created_at for msg in messages),
                "latest": max(msg.created_at for msg in messages),
            },
        }

        # Count message types
        for msg in messages:
            msg_type = msg.type
            analysis["message_types"][msg_type] = analysis["message_types"].get(msg_type, 0) + 1
            analysis["users"].add(msg.username)

        analysis["unique_users"] = len(analysis["users"])
        analysis["users"] = list(analysis["users"])

        duration = (datetime.now() - start_time).total_seconds()
        analysis["analysis_duration_seconds"] = duration

        enhanced_logger.info("Batch message analysis completed", duration=duration)

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Batch message analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail="Analysis failed")


# ============================================================================
# Batch Export Operations
# ============================================================================


@router.get("/api/batch/messages/export")
async def export_messages(
    format: str = Query("json", description="Export format: json, csv, txt"),
    limit: int = Query(1000, description="Maximum messages to export", ge=1, le=10000),
    username: Optional[str] = Query(None, description="Filter by username"),
    message_type: Optional[MessageType] = Query(None, description="Filter by type"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
):
    """
    Export messages in various formats
    
    Supports JSON, CSV, and plain text exports with filtering.
    
    - **format**: Export format (json, csv, txt)
    - **limit**: Maximum messages to export
    - **username**: Optional username filter
    - **message_type**: Optional message type filter
    - **date_from**: Optional start date
    - **date_to**: Optional end date
    """
    try:
        from io import StringIO
        import csv
        import json

        enhanced_logger.info(
            "Message export requested", format=format, limit=limit, username=username
        )

        # Get messages
        messages = message_repo.get_messages(limit=limit)

        # Apply filters
        filtered_messages = []
        for msg in messages:
            if username and msg.username != username:
                continue
            if message_type and msg.type != message_type:
                continue
            if date_from and msg.created_at < date_from:
                continue
            if date_to and msg.created_at > date_to:
                continue
            filtered_messages.append(msg)

        enhanced_logger.info("Messages filtered for export", count=len(filtered_messages))

        # Export based on format
        if format == "json":
            from fastapi.responses import JSONResponse

            return JSONResponse(
                content={
                    "messages": [msg.model_dump() for msg in filtered_messages],
                    "total": len(filtered_messages),
                    "exported_at": datetime.now().isoformat(),
                }
            )

        elif format == "csv":
            from fastapi.responses import StreamingResponse

            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                ["ID", "Username", "Content", "Type", "Created At", "Room ID", "Project ID"]
            )

            # Write data
            for msg in filtered_messages:
                writer.writerow(
                    [
                        msg.id,
                        msg.username,
                        msg.content,
                        msg.type,
                        msg.created_at.isoformat(),
                        msg.room_id or "",
                        msg.project_id or "",
                    ]
                )

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=messages_export.csv"},
            )

        elif format == "txt":
            from fastapi.responses import PlainTextResponse

            lines = []
            for msg in filtered_messages:
                lines.append(f"[{msg.created_at}] {msg.username}: {msg.content}")

            return PlainTextResponse(
                content="\n".join(lines),
                headers={"Content-Disposition": "attachment; filename=messages_export.txt"},
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid export format")

    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Message export failed", format=format, error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")
