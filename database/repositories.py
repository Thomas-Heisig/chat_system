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


# Custom Exceptions for consistent error handling
class RepositoryException(Exception):
    """Base exception for repository operations"""
    pass


class EntityNotFoundException(RepositoryException):
    """Raised when an entity is not found"""
    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' not found")


class EntityAlreadyExistsException(RepositoryException):
    """Raised when an entity already exists"""
    def __init__(self, entity_type: str, identifier: Any):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} with identifier '{identifier}' already exists")


class ValidationException(RepositoryException):
    """Raised when validation fails"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


class DatabaseOperationException(RepositoryException):
    """Raised when a database operation fails"""
    def __init__(self, operation: str, details: str = None):
        self.operation = operation
        self.details = details
        super().__init__(f"Database operation '{operation}' failed: {details}")


def _validate_field_name(field: str) -> bool:
    """Validate that a field name only contains safe characters.
    
    This is a defense-in-depth measure to prevent SQL injection,
    even though field names should already be from a whitelist.
    """
    import re
    # Only allow alphanumeric characters and underscores
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field))


def _build_update_query(table: str, fields: dict, id_field: str) -> tuple:
    """Build a safe UPDATE query from validated field names.
    
    Returns (query_string, values_list) tuple.
    Raises ValidationException if any field name is invalid.
    """
    # Validate all field names
    for field in fields.keys():
        if not _validate_field_name(field):
            raise ValidationException(f"Invalid field name: {field}")
    
    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {id_field} = ?"
    values = list(fields.values())
    return query, values


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
    def remove_message_reaction(message_id: int, user_id: str, reaction: str) -> bool:
        """Remove reaction from message"""
        try:
            with get_db_connection() as conn:
                with transaction(conn):
                    # Delete reaction
                    cursor = conn.execute(
                        """DELETE FROM message_reactions 
                           WHERE message_id = ? AND user_id = ? AND reaction = ?""",
                        (message_id, user_id, reaction)
                    )
                    
                    if cursor.rowcount > 0:
                        # Update message reaction count
                        conn.execute(
                            "UPDATE messages SET reaction_count = reaction_count - 1 WHERE id = ? AND reaction_count > 0",
                            (message_id,)
                        )
                        logger.debug(f"👎 Reaction '{reaction}' removed from message {message_id} by user {user_id}")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to remove reaction: {e}")
            return False

    @staticmethod
    def update_message(message_id: int, new_content: str, edit_reason: str = None) -> Optional[Message]:
        """Update message content and track edit history"""
        try:
            with get_db_connection() as conn:
                # First get the current message
                cursor = conn.execute(
                    "SELECT message, edit_history FROM messages WHERE id = ?",
                    (message_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise EntityNotFoundException("Message", message_id)
                
                old_content = row['message']
                edit_history = json.loads(row['edit_history']) if row['edit_history'] else []
                
                # Add to edit history
                edit_history.append({
                    "old_content": old_content,
                    "new_content": new_content,
                    "timestamp": datetime.now().isoformat(),
                    "reason": edit_reason
                })
                
                # Update message
                conn.execute(
                    """UPDATE messages 
                       SET message = ?, is_edited = 1, edit_history = ?
                       WHERE id = ?""",
                    (new_content, json.dumps(edit_history), message_id)
                )
                
                logger.debug(f"📝 Message {message_id} updated")
                return MessageRepository.get_message(message_id)
                
        except EntityNotFoundException:
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update message {message_id}: {e}")
            raise DatabaseOperationException("update_message", str(e))

    @staticmethod
    def delete_message(message_id: int, soft_delete: bool = True) -> bool:
        """Delete message (soft delete by default)"""
        try:
            with get_db_connection() as conn:
                if soft_delete:
                    # Soft delete - set flag
                    cursor = conn.execute(
                        "UPDATE messages SET flags = flags | 1 WHERE id = ?",
                        (message_id,)
                    )
                else:
                    # Hard delete
                    cursor = conn.execute(
                        "DELETE FROM messages WHERE id = ?",
                        (message_id,)
                    )
                
                if cursor.rowcount > 0:
                    logger.debug(f"🗑️ Message {message_id} deleted (soft={soft_delete})")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete message {message_id}: {e}")
            return False

    @staticmethod
    def get_thread_messages(parent_id: int, limit: int = 50) -> List[Message]:
        """Get all messages in a thread (replies to a parent message)"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT id, username, message, message_compressed, timestamp, message_type,
                              parent_id, room_id, project_id, ticket_id, is_ai_response, ai_model_used,
                              context_message_ids, rag_sources, sentiment, is_edited, edit_history,
                              reaction_count, flags, metadata
                       FROM messages 
                       WHERE parent_id = ?
                       ORDER BY timestamp ASC
                       LIMIT ?""",
                    (parent_id, limit)
                )
                rows = cursor.fetchall()
                messages = [MessageRepository._row_to_message(row) for row in rows]
                
                logger.debug(f"🧵 Retrieved {len(messages)} thread messages for parent {parent_id}")
                return messages
                
        except Exception as e:
            logger.error(f"❌ Failed to get thread messages for parent {parent_id}: {e}")
            return []

    @staticmethod
    def get_all_messages() -> List[Message]:
        """Get all messages (simple compatibility method)"""
        filters = MessageFilter(limit=1000)
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
    def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """Update user with given fields"""
        allowed_fields = {
            'email', 'display_name', 'avatar_url', 'role', 
            'is_active', 'is_verified', 'preferences', 'metadata'
        }
        
        try:
            # Filter to only allowed fields
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            if 'preferences' in valid_updates:
                valid_updates['preferences'] = json.dumps(valid_updates['preferences'])
            if 'metadata' in valid_updates:
                valid_updates['metadata'] = json.dumps(valid_updates['metadata'])
            
            valid_updates['updated_at'] = datetime.now().isoformat()
            
            # Build safe update query
            query, values = _build_update_query('users', valid_updates, 'id')
            values.append(user_id)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount == 0:
                    raise EntityNotFoundException("User", user_id)
                
                logger.debug(f"👤 User {user_id} updated")
                return UserRepository.get_user_by_id(user_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update user {user_id}: {e}")
            raise DatabaseOperationException("update_user", str(e))

    @staticmethod
    def delete_user(user_id: str, soft_delete: bool = True) -> bool:
        """Delete user (soft delete by default - sets is_active to False)"""
        try:
            with get_db_connection() as conn:
                if soft_delete:
                    cursor = conn.execute(
                        "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), user_id)
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM users WHERE id = ?",
                        (user_id,)
                    )
                
                if cursor.rowcount > 0:
                    logger.debug(f"🗑️ User {user_id} deleted (soft={soft_delete})")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id}: {e}")
            return False

    @staticmethod
    def get_all_users(include_inactive: bool = False, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with optional filtering"""
        try:
            with get_db_connection() as conn:
                if include_inactive:
                    query = "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
                    params = (limit, offset)
                else:
                    query = "SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?"
                    params = (limit, offset)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                users = [UserRepository._row_to_user(row) for row in rows]
                
                logger.debug(f"👥 Retrieved {len(users)} users")
                return users
                
        except Exception as e:
            logger.error(f"❌ Failed to get all users: {e}")
            return []

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
    def get_project_by_id(project_id: str) -> Optional[Project]:
        """Get project by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                return ProjectRepository._row_to_project(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get project {project_id}: {e}")
            return None

    @staticmethod
    def update_project(project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
        """Update project with given fields"""
        allowed_fields = {
            'name', 'description', 'status', 'due_date', 
            'tags', 'members', 'settings', 'metadata',
            'ticket_count', 'completed_ticket_count', 'progress_percentage'
        }
        
        try:
            # Filter to only allowed fields
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            for json_field in ['tags', 'members', 'settings', 'metadata']:
                if json_field in valid_updates:
                    valid_updates[json_field] = json.dumps(valid_updates[json_field])
            
            # Handle datetime fields
            if 'due_date' in valid_updates and valid_updates['due_date']:
                if isinstance(valid_updates['due_date'], datetime):
                    valid_updates['due_date'] = valid_updates['due_date'].isoformat()
            
            valid_updates['updated_at'] = datetime.now().isoformat()
            
            # Build safe update query
            query, values = _build_update_query('projects', valid_updates, 'id')
            values.append(project_id)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount == 0:
                    raise EntityNotFoundException("Project", project_id)
                
                logger.debug(f"📁 Project {project_id} updated")
                return ProjectRepository.get_project_by_id(project_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update project {project_id}: {e}")
            raise DatabaseOperationException("update_project", str(e))
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update project {project_id}: {e}")
            raise DatabaseOperationException("update_project", str(e))

    @staticmethod
    def delete_project(project_id: str, cascade: bool = False) -> bool:
        """Delete project (with optional cascade to delete related tickets)"""
        try:
            with get_db_connection() as conn:
                with transaction(conn):
                    if cascade:
                        # Delete related tickets first
                        conn.execute(
                            "DELETE FROM tickets WHERE project_id = ?",
                            (project_id,)
                        )
                    
                    cursor = conn.execute(
                        "DELETE FROM projects WHERE id = ?",
                        (project_id,)
                    )
                    
                    if cursor.rowcount > 0:
                        logger.debug(f"🗑️ Project {project_id} deleted (cascade={cascade})")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to delete project {project_id}: {e}")
            return False

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
    def get_ticket_by_id(ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
                row = cursor.fetchone()
                return TicketRepository._row_to_ticket(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get ticket {ticket_id}: {e}")
            return None

    @staticmethod
    def update_ticket(ticket_id: str, updates: Dict[str, Any]) -> Optional[Ticket]:
        """Update ticket with given fields"""
        allowed_fields = {
            'title', 'description', 'assigned_to', 'status', 'priority', 'type',
            'due_date', 'estimated_hours', 'actual_hours', 'related_tickets',
            'tags', 'metadata', 'comment_count', 'attachment_count'
        }
        
        try:
            # Filter to only allowed fields
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            for json_field in ['related_tickets', 'tags', 'metadata']:
                if json_field in valid_updates:
                    valid_updates[json_field] = json.dumps(valid_updates[json_field])
            
            # Handle datetime fields
            if 'due_date' in valid_updates and valid_updates['due_date']:
                if isinstance(valid_updates['due_date'], datetime):
                    valid_updates['due_date'] = valid_updates['due_date'].isoformat()
            
            # Handle status change to resolved
            if valid_updates.get('status') == TicketStatus.RESOLVED:
                valid_updates['resolved_at'] = datetime.now().isoformat()
            
            valid_updates['updated_at'] = datetime.now().isoformat()
            
            # Build safe update query
            query, values = _build_update_query('tickets', valid_updates, 'id')
            values.append(ticket_id)
            
            with get_db_connection() as conn:
                with transaction(conn):
                    # Get the ticket first to check project_id for counter update
                    cursor = conn.execute("SELECT project_id, status FROM tickets WHERE id = ?", (ticket_id,))
                    row = cursor.fetchone()
                    
                    if not row:
                        raise EntityNotFoundException("Ticket", ticket_id)
                    
                    old_status = row['status']
                    project_id = row['project_id']
                    new_status = valid_updates.get('status', old_status)
                    
                    # Update the ticket
                    conn.execute(query, values)
                    
                    # Update project completed count if status changed
                    if old_status != new_status:
                        if new_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                            conn.execute(
                                "UPDATE projects SET completed_ticket_count = completed_ticket_count + 1 WHERE id = ?",
                                (project_id,)
                            )
                        elif old_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                            conn.execute(
                                "UPDATE projects SET completed_ticket_count = completed_ticket_count - 1 WHERE id = ? AND completed_ticket_count > 0",
                                (project_id,)
                            )
                
                logger.debug(f"🎫 Ticket {ticket_id} updated")
                return TicketRepository.get_ticket_by_id(ticket_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update ticket {ticket_id}: {e}")
            raise DatabaseOperationException("update_ticket", str(e))

    @staticmethod
    def delete_ticket(ticket_id: str) -> bool:
        """Delete ticket and update project counters"""
        try:
            with get_db_connection() as conn:
                with transaction(conn):
                    # Get ticket info first
                    cursor = conn.execute(
                        "SELECT project_id, status FROM tickets WHERE id = ?",
                        (ticket_id,)
                    )
                    row = cursor.fetchone()
                    
                    if not row:
                        return False
                    
                    project_id = row['project_id']
                    status = row['status']
                    
                    # Delete the ticket
                    conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                    
                    # Update project counters
                    conn.execute(
                        "UPDATE projects SET ticket_count = ticket_count - 1 WHERE id = ? AND ticket_count > 0",
                        (project_id,)
                    )
                    
                    if status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                        conn.execute(
                            "UPDATE projects SET completed_ticket_count = completed_ticket_count - 1 WHERE id = ? AND completed_ticket_count > 0",
                            (project_id,)
                        )
                    
                    logger.debug(f"🗑️ Ticket {ticket_id} deleted")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to delete ticket {ticket_id}: {e}")
            return False

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
    def update_file(file_id: str, updates: Dict[str, Any]) -> Optional[File]:
        """Update file metadata with given fields"""
        allowed_fields = {
            'description', 'is_public', 'metadata', 'tags',
            'project_id', 'ticket_id'
        }
        
        try:
            # Filter to only allowed fields
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            for json_field in ['metadata', 'tags']:
                if json_field in valid_updates:
                    valid_updates[json_field] = json.dumps(valid_updates[json_field])
            
            # Build safe update query
            query, values = _build_update_query('files', valid_updates, 'id')
            values.append(file_id)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount == 0:
                    raise EntityNotFoundException("File", file_id)
                
                logger.debug(f"📄 File {file_id} updated")
                return FileRepository.get_file(file_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update file {file_id}: {e}")
            raise DatabaseOperationException("update_file", str(e))

    @staticmethod
    def delete_file(file_id: str) -> bool:
        """Delete file record from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM files WHERE id = ?",
                    (file_id,)
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"🗑️ File {file_id} deleted")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete file {file_id}: {e}")
            return False

    @staticmethod
    def get_files_by_filter(
        project_id: str = None,
        ticket_id: str = None,
        uploaded_by: str = None,
        file_type: FileType = None,
        is_public: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[File]:
        """Get files with optional filtering"""
        try:
            query = "SELECT * FROM files WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            if ticket_id:
                query += " AND ticket_id = ?"
                params.append(ticket_id)
            
            if uploaded_by:
                query += " AND uploaded_by = ?"
                params.append(uploaded_by)
            
            if file_type:
                query += " AND file_type = ?"
                params.append(file_type)
            
            if is_public is not None:
                query += " AND is_public = ?"
                params.append(is_public)
            
            query += " ORDER BY upload_date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                files = [FileRepository._row_to_file(row) for row in rows]
                
                logger.debug(f"📁 Retrieved {len(files)} files")
                return files
                
        except Exception as e:
            logger.error(f"❌ Failed to get files: {e}")
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
    
    # Whitelist of allowed table names to prevent SQL injection
    ALLOWED_TABLES = frozenset({
        'users', 'projects', 'tickets', 'files', 
        'messages', 'chat_rooms', 'room_members',
        'message_reactions', 'ai_conversations', 'ai_models'
    })
    
    @staticmethod
    def get_system_statistics() -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            stats = {}
            
            with get_db_connection() as conn:
                # Basic counts - using direct queries (no dynamic SQL)
                stats['total_users'] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                stats['total_projects'] = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
                stats['total_tickets'] = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
                stats['total_files'] = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
                stats['total_messages'] = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
                stats['total_chat_rooms'] = conn.execute("SELECT COUNT(*) FROM chat_rooms").fetchone()[0]
                
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


class ChatRoomRepository:
    """Repository for chat room management operations"""
    
    @staticmethod
    def create_room(room: ChatRoom) -> str:
        """Create new chat room"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO chat_rooms 
                       (id, name, description, is_public, created_by, created_at,
                        member_count, message_count, settings, metadata, allowed_roles, is_archived)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        room.id,
                        room.name,
                        room.description,
                        room.is_public,
                        room.created_by,
                        room.created_at.isoformat() if room.created_at else datetime.now().isoformat(),
                        room.member_count,
                        room.message_count,
                        json.dumps(room.settings),
                        json.dumps(room.metadata),
                        json.dumps([role.value if hasattr(role, 'value') else role for role in room.allowed_roles]),
                        room.is_archived
                    )
                )
                
                enhanced_logger.info(
                    "Chat room created successfully",
                    room_id=room.id,
                    room_name=room.name,
                    created_by=room.created_by
                )
                return room.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to create chat room",
                error=str(e),
                room_name=room.name
            )
            raise

    @staticmethod
    def get_room_by_id(room_id: str) -> Optional[ChatRoom]:
        """Get chat room by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,))
                row = cursor.fetchone()
                return ChatRoomRepository._row_to_room(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get room {room_id}: {e}")
            return None

    @staticmethod
    def get_public_rooms(limit: int = 50, offset: int = 0) -> List[ChatRoom]:
        """Get all public chat rooms"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT * FROM chat_rooms 
                       WHERE is_public = 1 AND is_archived = 0
                       ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                    (limit, offset)
                )
                rows = cursor.fetchall()
                return [ChatRoomRepository._row_to_room(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get public rooms: {e}")
            return []

    @staticmethod
    def update_room(room_id: str, updates: Dict[str, Any]) -> Optional[ChatRoom]:
        """Update chat room with given fields"""
        allowed_fields = {
            'name', 'description', 'is_public', 'settings', 
            'metadata', 'allowed_roles', 'is_archived'
        }
        
        try:
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            for json_field in ['settings', 'metadata', 'allowed_roles']:
                if json_field in valid_updates:
                    valid_updates[json_field] = json.dumps(valid_updates[json_field])
            
            # Build safe update query
            query, values = _build_update_query('chat_rooms', valid_updates, 'id')
            values.append(room_id)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount == 0:
                    raise EntityNotFoundException("ChatRoom", room_id)
                
                logger.debug(f"💬 Room {room_id} updated")
                return ChatRoomRepository.get_room_by_id(room_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update room {room_id}: {e}")
            raise DatabaseOperationException("update_room", str(e))

    @staticmethod
    def delete_room(room_id: str) -> bool:
        """Delete chat room"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM chat_rooms WHERE id = ?",
                    (room_id,)
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"🗑️ Room {room_id} deleted")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete room {room_id}: {e}")
            return False

    @staticmethod
    def add_member(room_id: str, user_id: str, role: RoomRole = RoomRole.MEMBER) -> bool:
        """Add member to chat room"""
        try:
            with get_db_connection() as conn:
                with transaction(conn):
                    conn.execute(
                        """INSERT INTO room_members (room_id, user_id, role, joined_at)
                           VALUES (?, ?, ?, ?)""",
                        (room_id, user_id, role.value if hasattr(role, 'value') else role, datetime.now().isoformat())
                    )
                    
                    conn.execute(
                        "UPDATE chat_rooms SET member_count = member_count + 1 WHERE id = ?",
                        (room_id,)
                    )
                    
                    logger.debug(f"👤 User {user_id} added to room {room_id}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to add member to room: {e}")
            return False

    @staticmethod
    def remove_member(room_id: str, user_id: str) -> bool:
        """Remove member from chat room"""
        try:
            with get_db_connection() as conn:
                with transaction(conn):
                    cursor = conn.execute(
                        "DELETE FROM room_members WHERE room_id = ? AND user_id = ?",
                        (room_id, user_id)
                    )
                    
                    if cursor.rowcount > 0:
                        conn.execute(
                            "UPDATE chat_rooms SET member_count = member_count - 1 WHERE id = ? AND member_count > 0",
                            (room_id,)
                        )
                        logger.debug(f"👤 User {user_id} removed from room {room_id}")
                        return True
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to remove member from room: {e}")
            return False

    @staticmethod
    def get_room_members(room_id: str) -> List[RoomMember]:
        """Get all members of a chat room"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT room_id, user_id, role, joined_at, last_read_at
                       FROM room_members WHERE room_id = ?
                       ORDER BY joined_at""",
                    (room_id,)
                )
                
                members = []
                for row in cursor.fetchall():
                    members.append(RoomMember(
                        room_id=row['room_id'],
                        user_id=row['user_id'],
                        role=row['role'],
                        joined_at=datetime.fromisoformat(row['joined_at']) if row['joined_at'] else None,
                        last_read_at=datetime.fromisoformat(row['last_read_at']) if row['last_read_at'] else None
                    ))
                
                return members
                
        except Exception as e:
            logger.error(f"❌ Failed to get room members: {e}")
            return []

    @staticmethod
    def _row_to_room(row) -> ChatRoom:
        """Convert database row to ChatRoom object"""
        return ChatRoom(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            is_public=bool(row['is_public']),
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            member_count=row['member_count'],
            message_count=row['message_count'],
            settings=json.loads(row['settings']) if row['settings'] else {},
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            allowed_roles=json.loads(row['allowed_roles']) if row['allowed_roles'] else [],
            is_archived=bool(row['is_archived']) if row['is_archived'] else False
        )


class AIConversationRepository:
    """Repository for AI conversation management operations"""
    
    @staticmethod
    def create_conversation(conversation: AIConversation) -> str:
        """Create new AI conversation"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO ai_conversations 
                       (id, title, context, message_count, user_id, created_at, updated_at,
                        is_archived, ai_model, conversation_settings, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        conversation.id,
                        conversation.title,
                        json.dumps(conversation.context) if conversation.context else None,
                        conversation.message_count,
                        conversation.user_id,
                        conversation.created_at.isoformat() if conversation.created_at else datetime.now().isoformat(),
                        conversation.updated_at.isoformat() if conversation.updated_at else datetime.now().isoformat(),
                        conversation.is_archived,
                        conversation.ai_model,
                        json.dumps(conversation.conversation_settings),
                        json.dumps(conversation.metadata)
                    )
                )
                
                enhanced_logger.info(
                    "AI conversation created successfully",
                    conversation_id=conversation.id,
                    title=conversation.title,
                    user_id=conversation.user_id
                )
                return conversation.id
                
        except Exception as e:
            enhanced_logger.error(
                "Failed to create AI conversation",
                error=str(e),
                title=conversation.title
            )
            raise

    @staticmethod
    def get_conversation_by_id(conversation_id: str) -> Optional[AIConversation]:
        """Get AI conversation by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT * FROM ai_conversations WHERE id = ?", (conversation_id,))
                row = cursor.fetchone()
                return AIConversationRepository._row_to_conversation(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get conversation {conversation_id}: {e}")
            return None

    @staticmethod
    def get_conversations_by_user(user_id: str, include_archived: bool = False, limit: int = 50, offset: int = 0) -> List[AIConversation]:
        """Get all AI conversations for a user"""
        try:
            with get_db_connection() as conn:
                if include_archived:
                    query = """SELECT * FROM ai_conversations 
                               WHERE user_id = ?
                               ORDER BY updated_at DESC LIMIT ? OFFSET ?"""
                else:
                    query = """SELECT * FROM ai_conversations 
                               WHERE user_id = ? AND is_archived = 0
                               ORDER BY updated_at DESC LIMIT ? OFFSET ?"""
                
                cursor = conn.execute(query, (user_id, limit, offset))
                rows = cursor.fetchall()
                return [AIConversationRepository._row_to_conversation(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Failed to get conversations for user {user_id}: {e}")
            return []

    @staticmethod
    def update_conversation(conversation_id: str, updates: Dict[str, Any]) -> Optional[AIConversation]:
        """Update AI conversation with given fields"""
        allowed_fields = {
            'title', 'context', 'message_count', 'is_archived',
            'ai_model', 'conversation_settings', 'metadata'
        }
        
        try:
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValidationException("No valid fields to update")
            
            # Handle JSON fields
            for json_field in ['context', 'conversation_settings', 'metadata']:
                if json_field in valid_updates:
                    valid_updates[json_field] = json.dumps(valid_updates[json_field])
            
            valid_updates['updated_at'] = datetime.now().isoformat()
            
            # Build safe update query
            query, values = _build_update_query('ai_conversations', valid_updates, 'id')
            values.append(conversation_id)
            
            with get_db_connection() as conn:
                cursor = conn.execute(query, values)
                
                if cursor.rowcount == 0:
                    raise EntityNotFoundException("AIConversation", conversation_id)
                
                logger.debug(f"🤖 Conversation {conversation_id} updated")
                return AIConversationRepository.get_conversation_by_id(conversation_id)
                
        except (EntityNotFoundException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update conversation {conversation_id}: {e}")
            raise DatabaseOperationException("update_conversation", str(e))

    @staticmethod
    def delete_conversation(conversation_id: str) -> bool:
        """Delete AI conversation"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM ai_conversations WHERE id = ?",
                    (conversation_id,)
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"🗑️ Conversation {conversation_id} deleted")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete conversation {conversation_id}: {e}")
            return False

    @staticmethod
    def increment_message_count(conversation_id: str) -> bool:
        """Increment message count for conversation"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """UPDATE ai_conversations 
                       SET message_count = message_count + 1, updated_at = ?
                       WHERE id = ?""",
                    (datetime.now().isoformat(), conversation_id)
                )
                return True
        except Exception as e:
            logger.error(f"❌ Failed to increment message count: {e}")
            return False

    @staticmethod
    def _row_to_conversation(row) -> AIConversation:
        """Convert database row to AIConversation object"""
        # Convert row keys to set once for efficient lookup
        row_keys = set(row.keys())
        
        return AIConversation(
            id=row['id'],
            title=row['title'],
            context=json.loads(row['context']) if row['context'] else None,
            message_count=row['message_count'],
            user_id=row['user_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            is_archived=bool(row['is_archived']),
            ai_model=row['ai_model'] if 'ai_model' in row_keys else None,
            conversation_settings=json.loads(row['conversation_settings']) if 'conversation_settings' in row_keys and row['conversation_settings'] else {},
            metadata=json.loads(row['metadata']) if 'metadata' in row_keys and row['metadata'] else {}
        )