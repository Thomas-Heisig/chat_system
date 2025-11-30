# routes/messages.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime, timedelta

from services.message_service import MessageService
from services.project_service import ProjectService
from database.repositories import (
    MessageRepository, UserRepository, ProjectRepository, 
    TicketRepository, StatisticsRepository
)
from database.models import (
    Message, MessageFilter, MessageType, User, Project, Ticket,
    PaginatedResponse, MessageBatch, create_message, create_ai_message
)
from config.settings import logger, enhanced_logger

router = APIRouter()

# Initialize dependencies with comprehensive logging
logger.info("🔄 Initializing enhanced messages API routes dependencies...")
try:
    message_repository = MessageRepository()
    user_repository = UserRepository()
    project_repository = ProjectRepository()
    ticket_repository = TicketRepository()
    stats_repository = StatisticsRepository()
    
    message_service = MessageService(message_repository)
    
    logger.info("✅ Enhanced messages API routes dependencies initialized successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize messages API routes dependencies: {e}")
    raise

# ============================================================================
# Basic Message Endpoints (Enhanced)
# ============================================================================

@router.get("/messages", response_model=PaginatedResponse)
async def get_all_messages(
    limit: int = Query(50, description="Limit number of messages", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    username: Optional[str] = Query(None, description="Filter by username"),
    message_type: Optional[MessageType] = Query(None, description="Filter by message type"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    ticket_id: Optional[str] = Query(None, description="Filter by ticket ID")
):
    """Get all messages with advanced filtering and pagination"""
    start_time = datetime.now()
    
    try:
        filters = MessageFilter(
            username=username,
            message_type=message_type,
            room_id=room_id,
            project_id=project_id,
            ticket_id=ticket_id,
            limit=limit,
            offset=offset
        )
        
        enhanced_logger.info(
            "Get all messages requested",
            limit=limit,
            offset=offset,
            username=username,
            message_type=message_type,
            project_id=project_id,
            ticket_id=ticket_id
        )
        
        result = message_repository.get_messages_by_filter(filters)
        
        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.info(
            "Messages retrieved successfully",
            total_messages=result.total,
            returned_count=len(result.items),
            duration=duration
        )
        
        return result
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.error(
            "Failed to retrieve messages",
            error=str(e),
            duration=duration
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/messages/recent", response_model=List[Message])
async def get_recent_messages(
    limit: int = Query(50, description="Number of recent messages", ge=1, le=100),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get recent messages with room and project filtering"""
    try:
        logger.info(f"🕒 GET /messages/recent - Limit: {limit}, Room: {room_id}, Project: {project_id}")
        
        messages = message_repository.get_recent_messages(limit, room_id, project_id)
        
        # Calculate statistics for logging
        user_count = len(set(msg.username for msg in messages))
        ai_count = sum(1 for msg in messages if msg.is_ai_response)
        
        logger.info(f"✅ Returned {len(messages)} recent messages - "
                   f"Users: {user_count}, AI responses: {ai_count}")
        
        return messages
        
    except Exception as e:
        logger.error(f"❌ Error in get_recent_messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/messages/user/{username}", response_model=PaginatedResponse)
async def get_user_messages(
    username: str,
    limit: int = Query(50, description="Number of messages", ge=1, le=200),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get messages from a specific user with pagination and project filtering"""
    try:
        filters = MessageFilter(
            username=username,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"👤 GET /messages/user/{username} - "
                   f"Limit: {limit}, Offset: {offset}, Project: {project_id}")
        
        result = message_repository.get_messages_by_filter(filters)
        
        logger.info(f"✅ Returned {len(result.items)} messages from user '{username}' "
                   f"(total: {result.total})")
        
        if not result.items:
            logger.warning(f"⚠️ No messages found for user '{username}' with given filters")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting messages for user '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# Advanced Message Endpoints
# ============================================================================

@router.get("/messages/{message_id}")
async def get_message_by_id(message_id: int):
    """Get specific message by ID with full details"""
    try:
        logger.info(f"🔍 GET /messages/{message_id} requested")
        
        message = message_repository.get_message(message_id)
        
        if not message:
            logger.warning(f"⚠️ Message {message_id} not found")
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Get message reactions if any
        reactions = message_repository.get_message_reactions(message_id)
        
        # Pydantic v2 kompatibel: model_dump() statt dict()
        response_data = {
            "message": message.model_dump(),
            "reactions": [reaction.model_dump() for reaction in reactions],
            "reaction_count": len(reactions)
        }
        
        logger.info(f"✅ Message {message_id} retrieved successfully")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/messages/{message_id}/context")
async def get_message_context(
    message_id: int, 
    context_window: int = Query(10, description="Number of context messages", ge=1, le=50)
):
    """Get conversation context around a specific message"""
    try:
        logger.info(f"🔄 GET /messages/{message_id}/context - Window: {context_window}")
        
        context_messages = message_repository.get_conversation_context(message_id, context_window)
        
        response_data = {
            "message_id": message_id,
            "context_window": context_window,
            "context_messages": [msg.model_dump() for msg in context_messages],
            "total_context_messages": len(context_messages)
        }
        
        logger.info(f"✅ Context retrieved for message {message_id} - "
                   f"Found {len(context_messages)} context messages")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting context for message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve message context")

@router.post("/messages/{message_id}/reactions")
async def add_message_reaction(
    message_id: int,
    user_id: str = Query(..., description="User ID adding the reaction"),
    reaction: str = Query(..., description="Reaction emoji or code", min_length=1, max_length=10)
):
    """Add reaction to a message"""
    try:
        logger.info(f"👍 POST /messages/{message_id}/reactions - "
                   f"User: {user_id}, Reaction: {reaction}")
        
        success = message_repository.add_message_reaction(message_id, user_id, reaction)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add reaction")
        
        # Get updated reaction count
        message = message_repository.get_message(message_id)
        
        logger.info(f"✅ Reaction '{reaction}' added to message {message_id} by user {user_id}")
        
        return {
            "message_id": message_id,
            "reaction": reaction,
            "user_id": user_id,
            "reaction_count": message.reaction_count if message else 0,
            "status": "added"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding reaction to message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reaction")

@router.get("/messages/{message_id}/reactions")
async def get_message_reactions(message_id: int):
    """Get all reactions for a message"""
    try:
        logger.info(f"❤️ GET /messages/{message_id}/reactions requested")
        
        reactions = message_repository.get_message_reactions(message_id)
        
        # Group reactions by type
        reaction_summary = {}
        for reaction in reactions:
            reaction_summary[reaction.reaction] = reaction_summary.get(reaction.reaction, 0) + 1
        
        response_data = {
            "message_id": message_id,
            "reactions": [reaction.model_dump() for reaction in reactions],
            "reaction_summary": reaction_summary,
            "total_reactions": len(reactions)
        }
        
        logger.info(f"✅ Retrieved {len(reactions)} reactions for message {message_id}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting reactions for message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reactions")

# ============================================================================
# Statistics and Analytics Endpoints
# ============================================================================

@router.get("/messages/stats")
async def get_message_stats(
    timeframe: str = Query("all_time", description="Timeframe for statistics", 
                          regex="^(all_time|today|week|month|year)$"),
    project_id: Optional[str] = Query(None, description="Filter by project ID")
):
    """Get comprehensive message statistics with timeframe filtering"""
    try:
        logger.info(f"📊 GET /messages/stats - Timeframe: {timeframe}, Project: {project_id}")
        
        # Get system statistics
        system_stats = stats_repository.get_system_statistics()
        
        # Calculate timeframe-specific stats
        all_messages = message_repository.get_all_messages()
        
        # Filter by project if specified
        if project_id:
            all_messages = [msg for msg in all_messages if msg.project_id == project_id]
        
        # Filter by timeframe
        now = datetime.now()
        if timeframe == "today":
            cutoff = now - timedelta(days=1)
            all_messages = [msg for msg in all_messages if msg.timestamp and msg.timestamp >= cutoff]
        elif timeframe == "week":
            cutoff = now - timedelta(weeks=1)
            all_messages = [msg for msg in all_messages if msg.timestamp and msg.timestamp >= cutoff]
        elif timeframe == "month":
            cutoff = now - timedelta(days=30)
            all_messages = [msg for msg in all_messages if msg.timestamp and msg.timestamp >= cutoff]
        elif timeframe == "year":
            cutoff = now - timedelta(days=365)
            all_messages = [msg for msg in all_messages if msg.timestamp and msg.timestamp >= cutoff]
        
        total_messages = len(all_messages)
        
        if total_messages == 0:
            stats = {
                "total_messages": 0,
                "total_users": 0,
                "timeframe": timeframe,
                "project_id": project_id,
                "message": "No messages found for the specified criteria"
            }
            logger.info(f"📊 No messages available for statistics (timeframe: {timeframe})")
            return stats
        
        # Calculate comprehensive statistics
        users = set(msg.username for msg in all_messages)
        total_users = len(users)
        
        # User activity
        user_counts = {}
        for msg in all_messages:
            user_counts[msg.username] = user_counts.get(msg.username, 0) + 1
        
        most_active_user = max(user_counts.items(), key=lambda x: x[1]) if user_counts else ("none", 0)
        
        # Message types
        message_type_counts = {}
        for msg in all_messages:
            msg_type = msg.message_type
            message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1
        
        # AI responses
        ai_responses = sum(1 for msg in all_messages if msg.is_ai_response)
        ai_models_used = {}
        for msg in all_messages:
            if msg.ai_model_used:
                ai_models_used[msg.ai_model_used] = ai_models_used.get(msg.ai_model_used, 0) + 1
        
        # Time-based statistics
        if all_messages and all_messages[0].timestamp:
            messages_sorted = sorted(
                all_messages,
                key=lambda x: x.timestamp if x.timestamp is not None else datetime.min
            )
            first_message = messages_sorted[0].timestamp
            last_message = messages_sorted[-1].timestamp
            time_span = last_message - first_message if first_message and last_message else None
        else:
            first_message = last_message = time_span = None
        
        stats = {
            "timeframe": timeframe,
            "project_id": project_id,
            "total_messages": total_messages,
            "total_users": total_users,
            "most_active_user": {
                "username": most_active_user[0],
                "message_count": most_active_user[1]
            },
            "message_types": message_type_counts,
            "ai_responses": {
                "total": ai_responses,
                "percentage": round((ai_responses / total_messages) * 100, 1) if total_messages > 0 else 0,
                "models_used": ai_models_used
            },
            "time_span": {
                "first_message": first_message.isoformat() if first_message else None,
                "last_message": last_message.isoformat() if last_message else None,
                "duration_days": time_span.days if time_span else None
            },
            "user_activity": user_counts,
            "system_statistics": system_stats.get('message_statistics', {})
        }
        
        logger.info(f"📊 Comprehensive statistics generated - "
                   f"Messages: {total_messages}, Users: {total_users}, "
                   f"Timeframe: {timeframe}")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error generating message statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/messages/count")
async def get_message_count(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    room_id: Optional[str] = Query(None, description="Filter by room ID")
):
    """Get total message count with filtering"""
    try:
        filters = MessageFilter(
            project_id=project_id,
            room_id=room_id,
            limit=1,  # We only need count
            offset=0
        )
        
        result = message_repository.get_messages_by_filter(filters)
        
        count_info = {
            "total_messages": result.total,
            "project_id": project_id,
            "room_id": room_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"🔢 GET /messages/count - Total: {result.total}, "
                   f"Project: {project_id}, Room: {room_id}")
        
        return count_info
        
    except Exception as e:
        logger.error(f"❌ Error getting message count: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/messages/ai/stats")
async def get_ai_message_stats():
    """Get AI-specific message statistics"""
    try:
        logger.info("🤖 GET /messages/ai/stats requested")
        
        ai_stats = message_repository.get_ai_interaction_stats()
        
        enhanced_stats = {
            "ai_interactions": ai_stats,
            "timestamp": datetime.now().isoformat(),
            "ai_configuration": {
                "enabled": True,  # Assuming AI is enabled if this endpoint is called
                "auto_respond": True,
                "default_model": "ollama"
            }
        }
        
        logger.info(f"✅ AI statistics retrieved - "
                   f"Total AI responses: {ai_stats.get('total_ai_responses', 0)}")
        
        return enhanced_stats
        
    except Exception as e:
        logger.error(f"❌ Error getting AI message statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve AI statistics")

# ============================================================================
# Search and Filter Endpoints
# ============================================================================

@router.get("/messages/search")
async def search_messages(
    query: str,
    limit: int = Query(20, description="Number of results", ge=1, le=100),
    search_type: str = Query("semantic", description="Search type", regex="^(semantic|keyword)$")
):
    """Search messages using semantic or keyword search"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        logger.info(f"🔍 GET /messages/search - Query: '{query}', Type: {search_type}, Limit: {limit}")
        
        if search_type == "semantic":
            results = message_repository.search_messages_semantic(query, limit)
        else:
            # Keyword search using filters
            filters = MessageFilter(contains_text=query, limit=limit)
            result_batch = message_repository.get_messages_by_filter(filters)
            results = result_batch.items
        
        response_data = {
            "query": query,
            "search_type": search_type,
            "results": [msg.model_dump() for msg in results],
            "total_results": len(results),
            "search_performed_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Search completed - Found {len(results)} results for '{query}'")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/messages/project/{project_id}")
async def get_project_messages(
    project_id: str,
    limit: int = Query(50, description="Number of messages", ge=1, le=200),
    offset: int = Query(0, description="Offset for pagination", ge=0)
):
    """Get all messages for a specific project"""
    try:
        logger.info(f"📁 GET /messages/project/{project_id} - Limit: {limit}, Offset: {offset}")
        
        filters = MessageFilter(
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        result = message_repository.get_messages_by_filter(filters)
        
        # Get project info if available
        project_info = None
        # Note: You would typically get this from project_repository
        
        response_data = {
            "project_id": project_id,
            "project_info": project_info,
            "messages": result.items,
            "pagination": {
                "total": result.total,
                "page": (offset // limit) + 1,
                "page_size": limit,
                "total_pages": (result.total + limit - 1) // limit
            }
        }
        
        logger.info(f"✅ Retrieved {len(result.items)} messages for project {project_id}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting project messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project messages")

# ============================================================================
# Utility Endpoints
# ============================================================================

@router.delete("/messages/cleanup")
async def cleanup_old_messages(
    days_old: int = Query(30, description="Delete messages older than X days", ge=1, le=365),
    preserve_ai: bool = Query(True, description="Preserve AI-generated messages")
):
    """Clean up old messages (admin functionality)"""
    try:
        logger.info(f"🧹 DELETE /messages/cleanup - Days: {days_old}, Preserve AI: {preserve_ai}")
        
        deleted_count = message_repository.cleanup_old_messages(days_old, preserve_ai)
        
        response_data = {
            "deleted_count": deleted_count,
            "days_old": days_old,
            "preserve_ai": preserve_ai,
            "cleanup_performed_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Cleanup completed - Deleted {deleted_count} messages")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error during message cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

@router.get("/messages/export")
async def export_messages(
    format: str = Query("json", description="Export format", regex="^(json|csv)$"),
    start_date: Optional[str] = Query(None, description="Start date for export"),
    end_date: Optional[str] = Query(None, description="End date for export")
):
    """Export messages in various formats"""
    try:
        logger.info(f"📤 GET /messages/export - Format: {format}, "
                   f"Start: {start_date}, End: {end_date}")
        
        # Apply date filters if provided
        filters = MessageFilter(limit=10000)  # Large limit for export
        
        if start_date:
            try:
                filters.start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start date format")
        
        if end_date:
            try:
                filters.end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
        
        result = message_repository.get_messages_by_filter(filters)
        
        if format == "json":
            export_data = {
                "export_info": {
                    "format": "json",
                    "exported_at": datetime.now().isoformat(),
                    "total_messages": len(result.items),
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    }
                },
                "messages": [msg.model_dump() for msg in result.items]
            }
        else:  # CSV format
            # This would typically generate a CSV file
            # For now, return JSON with CSV info
            export_data = {
                "export_info": {
                    "format": "csv",
                    "exported_at": datetime.now().isoformat(),
                    "total_messages": len(result.items),
                    "csv_columns": ["id", "username", "message", "timestamp", "message_type"]
                },
                "message": "CSV export would be generated here"
            }
        
        logger.info(f"✅ Messages export prepared - Format: {format}, "
                   f"Messages: {len(result.items)}")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error exporting messages: {e}")
        raise HTTPException(status_code=500, detail="Export failed")