from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid
from pathlib import Path

from database.connection import get_db_connection, transaction
from database.models import (
    Message, MessageType, User, UserRole, Project, ProjectStatus, 
    Ticket, TicketStatus, TicketPriority, TicketType, File, FileType,
    ChatRoom, RoomMember, RoomRole, MessageReaction, AIConversation, AIModel,
    MessageFilter, ProjectFilter, TicketFilter, PaginatedResponse, SearchResults,
    create_message, create_user, create_project, create_ticket, create_file
)
from config.settings import logger, enhanced_logger

class MessageRepository:
    """Enhanced message repository with AI, project, and room support"""
    
    @staticmethod
    def save_message(message: Message) -> int:
        """Save message to database with comprehensive support"""
        start_time = datetime.now()
        
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO messages 
                       (username, message, message_compressed, timestamp, message_type, 
                        parent_id, room_id, project_id, ticket_id,
                        is_ai_response, ai_model_used, context_message_ids, rag_sources,
                        sentiment, is_edited, edit_history, reaction_count, flags, metadata) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        message.username,
                        message.message,
                        message.message_compressed,
                        message.timestamp.isoformat() if message.timestamp else datetime.now().isoformat(),
                        message.message_type,
                        message.parent_id,
                        message.room_id,
                        message.project_id,
                        message.ticket_id,
                        message.is_ai_response,
                        message.ai_model_used,
                        json.dumps(message.context_message_ids),
                        json.dumps(message.rag_sources),
                        json.dumps(message.sentiment) if message.sentiment else None,
                        message.is_edited,
                        json.dumps(message.edit_history),
                        message.reaction_count,
                        message.flags,
                        json.dumps(message.metadata)
                    )
                )
                message_id = cursor.lastrowid
                
                duration = (datetime.now() - start_time).total_seconds()
                enhanced_logger.info(
                    "Message saved successfully",
                    message_id=message_id,
                    username=message.username,
                    message_type=message.message_type,
                    is_ai_response=message.is_ai_response,
                    room_id=message.room_id,
                    project_id=message.project_id,
                    duration=duration
                )
                return message_id
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            enhanced_logger.error(
                "Failed to save message",
                error=str(e),
                username=message.username,
                duration=duration
            )
            raise

    @staticmethod
    def get_message(message_id: int) -> Optional[Message]:
        """Retrieve specific message by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT id, username, message, message_compressed, timestamp, message_type,
                              parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                              context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                              reaction_count, flags, metadata
                       FROM messages WHERE id = ?""",
                    (message_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return MessageRepository._row_to_message(row)
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve message {message_id}: {e}")
            return None

    @staticmethod
    def get_recent_messages(limit: int = 50, room_id: str = None, project_id: str = None) -> List[Message]:
        """Retrieve recent messages with room and project filtering"""
        try:
            query = """SELECT id, username, message, message_compressed, timestamp, message_type,
                              parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                              context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                              reaction_count, flags, metadata
                       FROM messages WHERE 1=1"""
            params = []
            
            if room_id:
                query += " AND room_id = ?"
                params.append(room_id)
                
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                messages = [MessageRepository._row_to_message(row) for row in rows]
                
                logger.debug(f"📨 Retrieved {len(messages)} recent messages "
                           f"(room: {room_id}, project: {project_id})")
                
                return messages[::-1]  # Reverse to chronological order
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve recent messages: {e}")
            return []

    @staticmethod
    def get_messages_by_filter(filters: MessageFilter) -> PaginatedResponse:
        """Retrieve messages using comprehensive filter criteria"""
        start_time = datetime.now()
        
        try:
            query = """SELECT id, username, message, message_compressed, timestamp, message_type,
                              parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                              context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                              reaction_count, flags, metadata
                       FROM messages WHERE 1=1"""
            count_query = "SELECT COUNT(*) FROM messages WHERE 1=1"
            params = []
            
            # Build query based on filters
            if filters.username:
                query += " AND username = ?"
                count_query += " AND username = ?"
                params.append(filters.username)
                
            if filters.message_type:
                query += " AND message_type = ?"
                count_query += " AND message_type = ?"
                params.append(filters.message_type)
                
            if filters.room_id:
                query += " AND room_id = ?"
                count_query += " AND room_id = ?"
                params.append(filters.room_id)
                
            if filters.project_id:
                query += " AND project_id = ?"
                count_query += " AND project_id = ?"
                params.append(filters.project_id)
                
            if filters.ticket_id:
                query += " AND ticket_id = ?"
                count_query += " AND ticket_id = ?"
                params.append(filters.ticket_id)
                
            if filters.start_date:
                query += " AND timestamp >= ?"
                count_query += " AND timestamp >= ?"
                params.append(filters.start_date.isoformat())
                
            if filters.end_date:
                query += " AND timestamp <= ?"
                count_query += " AND timestamp <= ?"
                params.append(filters.end_date.isoformat())
                
            if filters.contains_text:
                query += " AND message LIKE ?"
                count_query += " AND message LIKE ?"
                params.append(f"%{filters.contains_text}%")
                
            if filters.is_ai_response is not None:
                query += " AND is_ai_response = ?"
                count_query += " AND is_ai_response = ?"
                params.append(filters.is_ai_response)
            
            # Get total count
            with get_db_connection() as conn:
                total_count = conn.execute(count_query, params).fetchone()[0]
                
                # Add pagination to main query
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([filters.limit, filters.offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                messages = [MessageRepository._row_to_message(row) for row in rows]
                
                duration = (datetime.now() - start_time).total_seconds()
                enhanced_logger.debug(
                    "Filtered messages retrieved",
                    total_count=total_count,
                    returned_count=len(messages),
                    duration=duration
                )
                
                total_pages = (total_count + filters.limit - 1) // filters.limit
                current_page = (filters.offset // filters.limit) + 1
                
                return PaginatedResponse(
                    items=messages,
                    total=total_count,
                    page=current_page,
                    page_size=filters.limit,
                    total_pages=total_pages
                )
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            enhanced_logger.error(
                "Failed to retrieve filtered messages",
                error=str(e),
                duration=duration
            )
            return PaginatedResponse(items=[], total=0, page=1, page_size=filters.limit, total_pages=0)

    @staticmethod
    def add_message_reaction(message_id: int, user_id: str, reaction: str) -> bool:
        """Add reaction to message"""
        try:
            with get_db_connection() as conn:
                # Insert reaction
                conn.execute(
                    """INSERT INTO message_reactions (message_id, user_id, reaction, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (message_id, user_id, reaction, datetime.now().isoformat())
                )
                
                # Update message reaction count
                conn.execute(
                    "UPDATE messages SET reaction_count = reaction_count + 1 WHERE id = ?",
                    (message_id,)
                )
                
                logger.debug(f"👍 Reaction '{reaction}' added to message {message_id} by user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add reaction: {e}")
            return False

    @staticmethod
    def get_message_reactions(message_id: int) -> List[MessageReaction]:
        """Get all reactions for a message"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT id, message_id, user_id, reaction, created_at 
                       FROM message_reactions WHERE message_id = ?""",
                    (message_id,)
                )
                
                reactions = []
                for row in cursor.fetchall():
                    reactions.append(MessageReaction(
                        id=row['id'],
                        message_id=row['message_id'],
                        user_id=row['user_id'],
                        reaction=row['reaction'],
                        created_at=datetime.fromisoformat(row['created_at'])
                    ))
                
                return reactions
                
        except Exception as e:
            logger.error(f"❌ Failed to get message reactions: {e}")
            return []

    @staticmethod
    def _row_to_message(row) -> Message:
        """Convert database row to Message object"""
        try:
            return Message(
                id=row['id'],
                username=row['username'],
                message=row['message'],
                message_compressed=row['message_compressed'],
                timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
                message_type=row['message_type'],
                parent_id=row['parent_id'],
                room_id=row['room_id'],
                project_id=row['project_id'],
                ticket_id=row['ticket_id'],
                is_ai_response=bool(row['is_ai_response']),
                ai_model_used=row['ai_model_used'],
                context_message_ids=json.loads(row['context_message_ids']) if row['context_message_ids'] else [],
                rag_sources=json.loads(row['rag_sources']) if row['rag_sources'] else [],
                sentiment=json.loads(row['sentiment']) if row['sentiment'] else None,
                is_edited=bool(row['is_edited']),
                edit_history=json.loads(row['edit_history']) if row['edit_history'] else [],
                reaction_count=row['reaction_count'],
                flags=row['flags'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
        except Exception as e:
            logger.error(f"❌ Error converting row to message: {e}")
            raise

    @staticmethod
    def get_all_messages(limit: int = 1000) -> List[Message]:
        """Get all messages (simple compatibility method)"""
        filters = MessageFilter(limit=limit)
        return MessageRepository.get_messages_by_filter(filters).items

    @staticmethod
    def get_message_count() -> int:
        """Get total message count"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM messages")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Failed to get message count: {e}")
            return 0

    @staticmethod
    def search_messages_semantic(query: str, limit: int = 20) -> List[Message]:
        """Search messages using semantic search (keyword fallback)"""
        try:
            filters = MessageFilter(contains_text=query, limit=limit)
            return MessageRepository.get_messages_by_filter(filters).items
        except Exception as e:
            logger.error(f"❌ Failed to search messages: {e}")
            return []

    @staticmethod
    def get_conversation_context(message_id: int, context_window: int = 10) -> List[Message]:
        """Get conversation context around a specific message"""
        try:
            with get_db_connection() as conn:
                # Get the message details including room/project context
                cursor = conn.execute(
                    "SELECT id, timestamp, room_id, project_id FROM messages WHERE id = ?",
                    (message_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return []
                
                msg_id = row['id']
                room_id = row['room_id']
                project_id = row['project_id']
                
                # Build query based on context (room or project)
                if room_id:
                    context_query = """
                        SELECT id, username, message, message_compressed, timestamp, message_type,
                               parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                               context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                               reaction_count, flags, metadata
                        FROM messages 
                        WHERE room_id = ?
                        ORDER BY ABS(id - ?)
                        LIMIT ?
                    """
                    cursor = conn.execute(context_query, (room_id, msg_id, context_window))
                elif project_id:
                    context_query = """
                        SELECT id, username, message, message_compressed, timestamp, message_type,
                               parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                               context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                               reaction_count, flags, metadata
                        FROM messages 
                        WHERE project_id = ?
                        ORDER BY ABS(id - ?)
                        LIMIT ?
                    """
                    cursor = conn.execute(context_query, (project_id, msg_id, context_window))
                else:
                    # General context - get messages around the target message by ID
                    context_query = """
                        SELECT id, username, message, message_compressed, timestamp, message_type,
                               parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                               context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                               reaction_count, flags, metadata
                        FROM messages 
                        ORDER BY ABS(id - ?)
                        LIMIT ?
                    """
                    cursor = conn.execute(context_query, (msg_id, context_window))
                
                # Sort results by timestamp for proper chronological order
                messages = [MessageRepository._row_to_message(r) for r in cursor.fetchall()]
                return sorted(messages, key=lambda m: m.timestamp if m.timestamp else datetime.min)
                
        except Exception as e:
            logger.error(f"❌ Failed to get conversation context: {e}")
            return []

    @staticmethod
    def cleanup_old_messages(days_old: int = 30, preserve_ai: bool = True) -> int:
        """Clean up old messages"""
        try:
            with get_db_connection() as conn:
                if preserve_ai:
                    cursor = conn.execute(
                        """DELETE FROM messages 
                           WHERE timestamp < datetime('now', ?) AND is_ai_response = 0""",
                        (f'-{days_old} days',)
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM messages WHERE timestamp < datetime('now', ?)",
                        (f'-{days_old} days',)
                    )
                deleted_count = cursor.rowcount
                logger.info(f"🧹 Cleaned up {deleted_count} old messages")
                return deleted_count
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old messages: {e}")
            return 0

    @staticmethod
    def get_ai_interaction_stats() -> Dict[str, Any]:
        """Get AI interaction statistics"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_ai_responses,
                        COUNT(DISTINCT ai_model_used) as models_used,
                        AVG(LENGTH(message)) as avg_response_length
                    FROM messages 
                    WHERE is_ai_response = 1
                """)
                row = cursor.fetchone()
                
                # Get model breakdown
                cursor = conn.execute("""
                    SELECT ai_model_used, COUNT(*) as count
                    FROM messages 
                    WHERE is_ai_response = 1 AND ai_model_used IS NOT NULL
                    GROUP BY ai_model_used
                """)
                models = dict(cursor.fetchall())
                
                return {
                    'total_ai_responses': row['total_ai_responses'] or 0,
                    'models_used_count': row['models_used'] or 0,
                    'avg_response_length': row['avg_response_length'] or 0,
                    'models_breakdown': models
                }
        except Exception as e:
            logger.error(f"❌ Failed to get AI interaction stats: {e}")
            return {'total_ai_responses': 0, 'models_used_count': 0, 'avg_response_length': 0, 'models_breakdown': {}}

class UserRepository:
    """Repository for user management operations"""
    
    @staticmethod
    def create_user(user: User) -> str:
        """Create new user"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO users 
                       (id, username, email, password_hash, display_name, avatar_url, role, 
                        is_active, is_verified, last_login, created_at, updated_at, preferences, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user.id,
                        user.username,
                        user.email,
                        user.password_hash,
                        user.display_name,
                        user.avatar_url,
                        user.role,
                        user.is_active,
                        user.is_verified,
                        user.last_login.isoformat() if user.last_login else None,
                        user.created_at.isoformat(),
                        user.updated_at.isoformat(),
                        json.dumps(user.preferences),
                        json.dumps(user.metadata)
                    )
                )
                
                enhanced_logger.info(
                    "User created successfully",
                    user_id=user.id,
                    username=user.username,
                    role=user.role
                )
                return user.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to create user",
                error=str(e),
                username=user.username
            )
            raise

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                return UserRepository._row_to_user(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                return UserRepository._row_to_user(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get user {username}: {e}")
            return None

    @staticmethod
    def update_user_last_login(user_id: str):
        """Update user's last login timestamp"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), datetime.now().isoformat(), user_id)
                )
                logger.debug(f"🕐 Updated last login for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update last login for user {user_id}: {e}")

    @staticmethod
    def _row_to_user(row) -> User:
        """Convert database row to User object"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            display_name=row['display_name'],
            avatar_url=row['avatar_url'],
            role=row['role'],
            is_active=bool(row['is_active']),
            is_verified=bool(row['is_verified']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            preferences=json.loads(row['preferences']) if row['preferences'] else {},
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

class ProjectRepository:
    """Repository for project management operations"""
    
    @staticmethod
    def create_project(project: Project) -> str:
        """Create new project"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO projects 
                       (id, name, description, status, created_by, created_at, updated_at,
                        due_date, tags, members, settings, metadata, ticket_count,
                        completed_ticket_count, progress_percentage)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project.id,
                        project.name,
                        project.description,
                        project.status,
                        project.created_by,
                        project.created_at.isoformat(),
                        project.updated_at.isoformat(),
                        project.due_date.isoformat() if project.due_date else None,
                        json.dumps(project.tags),
                        json.dumps(project.members),
                        json.dumps(project.settings),
                        json.dumps(project.metadata),
                        project.ticket_count,
                        project.completed_ticket_count,
                        project.progress_percentage
                    )
                )
                
                enhanced_logger.info(
                    "Project created successfully",
                    project_id=project.id,
                    project_name=project.name,
                    created_by=project.created_by
                )
                return project.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to create project",
                error=str(e),
                project_name=project.name
            )
            raise

    @staticmethod
    def get_projects_by_filter(filters: ProjectFilter) -> PaginatedResponse:
        """Get projects with filtering and pagination"""
        try:
            query = "SELECT * FROM projects WHERE 1=1"
            count_query = "SELECT COUNT(*) FROM projects WHERE 1=1"
            params = []
            
            if filters.status:
                query += " AND status = ?"
                count_query += " AND status = ?"
                params.append(filters.status)
                
            if filters.created_by:
                query += " AND created_by = ?"
                count_query += " AND created_by = ?"
                params.append(filters.created_by)
                
            if filters.member_id:
                query += " AND json_extract(members, '$') LIKE ?"
                count_query += " AND json_extract(members, '$') LIKE ?"
                params.append(f'%"{filters.member_id}"%')
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([filters.limit, filters.offset])
            
            with get_db_connection() as conn:
                total_count = conn.execute(count_query, params[:-2]).fetchone()[0]
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                projects = [ProjectRepository._row_to_project(row) for row in rows]
                total_pages = (total_count + filters.limit - 1) // filters.limit
                current_page = (filters.offset // filters.limit) + 1
                
                return PaginatedResponse(
                    items=projects,
                    total=total_count,
                    page=current_page,
                    page_size=filters.limit,
                    total_pages=total_pages
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to get projects: {e}")
            return PaginatedResponse(items=[], total=0, page=1, page_size=filters.limit, total_pages=0)

    @staticmethod
    def _row_to_project(row) -> Project:
        """Convert database row to Project object"""
        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            status=row['status'],
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            due_date=datetime.fromisoformat(row['due_date']) if row['due_date'] else None,
            tags=json.loads(row['tags']) if row['tags'] else [],
            members=json.loads(row['members']) if row['members'] else [],
            settings=json.loads(row['settings']) if row['settings'] else {},
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            ticket_count=row['ticket_count'],
            completed_ticket_count=row['completed_ticket_count'],
            progress_percentage=row['progress_percentage']
        )

class TicketRepository:
    """Repository for ticket management operations"""
    
    @staticmethod
    def create_ticket(ticket: Ticket) -> str:
        """Create new ticket"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO tickets 
                       (id, title, description, project_id, created_by, assigned_to,
                        status, priority, type, due_date, created_at, updated_at,
                        resolved_at, estimated_hours, actual_hours, related_tickets,
                        tags, metadata, comment_count, attachment_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ticket.id,
                        ticket.title,
                        ticket.description,
                        ticket.project_id,
                        ticket.created_by,
                        ticket.assigned_to,
                        ticket.status,
                        ticket.priority,
                        ticket.type,
                        ticket.due_date.isoformat() if ticket.due_date else None,
                        ticket.created_at.isoformat(),
                        ticket.updated_at.isoformat(),
                        ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                        ticket.estimated_hours,
                        ticket.actual_hours,
                        json.dumps(ticket.related_tickets),
                        json.dumps(ticket.tags),
                        json.dumps(ticket.metadata),
                        ticket.comment_count,
                        ticket.attachment_count
                    )
                )
                
                # Update project ticket count
                conn.execute(
                    "UPDATE projects SET ticket_count = ticket_count + 1 WHERE id = ?",
                    (ticket.project_id,)
                )
                
                enhanced_logger.info(
                    "Ticket created successfully",
                    ticket_id=ticket.id,
                    title=ticket.title,
                    project_id=ticket.project_id,
                    status=ticket.status
                )
                return ticket.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to create ticket",
                error=str(e),
                title=ticket.title
            )
            raise

    @staticmethod
    def get_tickets_by_filter(filters: TicketFilter) -> PaginatedResponse:
        """Get tickets with comprehensive filtering"""
        try:
            query = "SELECT * FROM tickets WHERE 1=1"
            count_query = "SELECT COUNT(*) FROM tickets WHERE 1=1"
            params = []
            
            if filters.project_id:
                query += " AND project_id = ?"
                count_query += " AND project_id = ?"
                params.append(filters.project_id)
                
            if filters.status:
                query += " AND status = ?"
                count_query += " AND status = ?"
                params.append(filters.status)
                
            if filters.priority:
                query += " AND priority = ?"
                count_query += " AND priority = ?"
                params.append(filters.priority)
                
            if filters.type:
                query += " AND type = ?"
                count_query += " AND type = ?"
                params.append(filters.type)
                
            if filters.assigned_to:
                query += " AND assigned_to = ?"
                count_query += " AND assigned_to = ?"
                params.append(filters.assigned_to)
                
            if filters.created_by:
                query += " AND created_by = ?"
                count_query += " AND created_by = ?"
                params.append(filters.created_by)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([filters.limit, filters.offset])
            
            with get_db_connection() as conn:
                total_count = conn.execute(count_query, params[:-2]).fetchone()[0]
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                tickets = [TicketRepository._row_to_ticket(row) for row in rows]
                total_pages = (total_count + filters.limit - 1) // filters.limit
                current_page = (filters.offset // filters.limit) + 1
                
                return PaginatedResponse(
                    items=tickets,
                    total=total_count,
                    page=current_page,
                    page_size=filters.limit,
                    total_pages=total_pages
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to get tickets: {e}")
            return PaginatedResponse(items=[], total=0, page=1, page_size=filters.limit, total_pages=0)

    @staticmethod
    def _row_to_ticket(row) -> Ticket:
        """Convert database row to Ticket object"""
        return Ticket(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            project_id=row['project_id'],
            created_by=row['created_by'],
            assigned_to=row['assigned_to'],
            status=row['status'],
            priority=row['priority'],
            type=row['type'],
            due_date=datetime.fromisoformat(row['due_date']) if row['due_date'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
            estimated_hours=row['estimated_hours'],
            actual_hours=row['actual_hours'],
            related_tickets=json.loads(row['related_tickets']) if row['related_tickets'] else [],
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            comment_count=row['comment_count'],
            attachment_count=row['attachment_count']
        )

class FileRepository:
    """Repository for file management operations"""
    
    @staticmethod
    def save_file(file: File) -> str:
        """Save file metadata to database"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO files 
                       (id, original_filename, stored_filename, file_path, file_size,
                        file_hash, mime_type, file_type, uploaded_by, project_id,
                        ticket_id, message_id, upload_date, description, download_count,
                        is_public, metadata, tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file.id,
                        file.original_filename,
                        file.stored_filename,
                        file.file_path,
                        file.file_size,
                        file.file_hash,
                        file.mime_type,
                        file.file_type,
                        file.uploaded_by,
                        file.project_id,
                        file.ticket_id,
                        file.message_id,
                        file.upload_date.isoformat(),
                        file.description,
                        file.download_count,
                        file.is_public,
                        json.dumps(file.metadata),
                        json.dumps(file.tags)
                    )
                )
                
                enhanced_logger.info(
                    "File saved successfully",
                    file_id=file.id,
                    filename=file.original_filename,
                    file_size=file.file_size,
                    uploaded_by=file.uploaded_by
                )
                return file.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to save file",
                error=str(e),
                filename=file.original_filename
            )
            raise

    @staticmethod
    def get_file(file_id: str) -> Optional[File]:
        """Get file by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,))
                row = cursor.fetchone()
                return FileRepository._row_to_file(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get file {file_id}: {e}")
            return None

    @staticmethod
    def increment_download_count(file_id: str):
        """Increment file download count"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "UPDATE files SET download_count = download_count + 1 WHERE id = ?",
                    (file_id,)
                )
                logger.debug(f"📥 Incremented download count for file {file_id}")
        except Exception as e:
            logger.error(f"❌ Failed to increment download count for file {file_id}: {e}")

    @staticmethod
    def get_all_files(limit: int = 100) -> List[File]:
        """Get all files with optional limit"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM files ORDER BY upload_date DESC LIMIT ?",
                    (limit,)
                )
                return [FileRepository._row_to_file(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Failed to get all files: {e}")
            return []

    @staticmethod
    def _row_to_file(row) -> File:
        """Convert database row to File object"""
        return File(
            id=row['id'],
            original_filename=row['original_filename'],
            stored_filename=row['stored_filename'],
            file_path=row['file_path'],
            file_size=row['file_size'],
            file_hash=row['file_hash'],
            mime_type=row['mime_type'],
            file_type=row['file_type'],
            uploaded_by=row['uploaded_by'],
            project_id=row['project_id'],
            ticket_id=row['ticket_id'],
            message_id=row['message_id'],
            upload_date=datetime.fromisoformat(row['upload_date']),
            description=row['description'],
            download_count=row['download_count'],
            is_public=bool(row['is_public']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            tags=json.loads(row['tags']) if row['tags'] else []
        )

# Search Repository
class SearchRepository:
    """Repository for cross-model search operations"""
    
    @staticmethod
    def global_search(query: str, limit: int = 20) -> SearchResults:
        """Search across messages, projects, tickets, and files"""
        try:
            results = SearchResults()
            
            # Search messages
            message_filters = MessageFilter(contains_text=query, limit=limit//4)
            message_repo = MessageRepository()
            message_results = message_repo.get_messages_by_filter(message_filters)
            results.messages = message_results.items[:limit//4]
            
            # Search projects
            with get_db_connection() as conn:
                # Project search
                cursor = conn.execute(
                    "SELECT * FROM projects WHERE name LIKE ? OR description LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit//4)
                )
                results.projects = [ProjectRepository._row_to_project(row) for row in cursor.fetchall()]
                
                # Ticket search
                cursor = conn.execute(
                    "SELECT * FROM tickets WHERE title LIKE ? OR description LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit//4)
                )
                results.tickets = [TicketRepository._row_to_ticket(row) for row in cursor.fetchall()]
                
                # File search
                cursor = conn.execute(
                    "SELECT * FROM files WHERE original_filename LIKE ? OR description LIKE ? LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit//4)
                )
                results.files = [FileRepository._row_to_file(row) for row in cursor.fetchall()]
            
            results.total_results = (
                len(results.messages) + len(results.projects) + 
                len(results.tickets) + len(results.files)
            )
            
            logger.info(f"🔍 Global search for '{query}' found {results.total_results} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Global search failed: {e}")
            return SearchResults()

# Statistics Repository
class StatisticsRepository:
    """Repository for system statistics and analytics"""
    
    @staticmethod
    def get_system_statistics() -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            stats = {}
            
            with get_db_connection() as conn:
                # Basic counts
                tables = {
                    'users': 'users',
                    'projects': 'projects', 
                    'tickets': 'tickets',
                    'files': 'files',
                    'messages': 'messages',
                    'chat_rooms': 'chat_rooms'
                }
                
                for key, table in tables.items():
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"total_{key}"] = cursor.fetchone()[0]
                
                # Message statistics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_ai_response = 1 THEN 1 ELSE 0 END) as ai_messages,
                        COUNT(DISTINCT username) as unique_users
                    FROM messages
                """)
                row = cursor.fetchone()
                stats.update({
                    'total_messages': row['total'],
                    'ai_messages': row['ai_messages'],
                    'unique_users': row['unique_users']
                })
                
                # Project statistics
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM projects 
                    GROUP BY status
                """)
                stats['projects_by_status'] = dict(cursor.fetchall())
                
                # Ticket statistics
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tickets 
                    GROUP BY status
                """)
                stats['tickets_by_status'] = dict(cursor.fetchall())
                
                # Recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) as count 
                    FROM messages 
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                stats['messages_last_24h'] = cursor.fetchone()[0]
            
            enhanced_logger.debug("System statistics collected", stats=stats)
            return stats
            
        except Exception as e:
            enhanced_logger.error("Failed to collect system statistics", error=str(e))
            return {}