import json
import sqlite3
import threading
import uuid
import zlib
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import enhanced_logger, logger, settings

# Thread-local storage for database connections
thread_local = threading.local()


@contextmanager
def get_db_connection(read_only: bool = False):
    """Enhanced context manager for database connections with connection pooling and retry logic"""
    conn = None
    start_time = datetime.now()

    try:
        # Try to reuse connection from thread local storage
        if hasattr(thread_local, "db_connection") and not read_only:
            conn = thread_local.db_connection
            # Check if connection is still valid
            try:
                conn.execute("SELECT 1")
                logger.debug("♻️ Reusing existing database connection")
            except sqlite3.Error:
                conn = None
                delattr(thread_local, "db_connection")

        if conn is None:
            # Create new connection
            db_uri = f"file:{settings.DATABASE_URL}?mode={'ro' if read_only else 'rwc'}"
            conn = sqlite3.connect(
                db_uri, timeout=settings.DATABASE_TIMEOUT, check_same_thread=False, uri=True
            )
            conn.row_factory = sqlite3.Row

            # Performance optimizations
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory mapping

            # Store connection for reuse in write mode
            if not read_only:
                thread_local.db_connection = conn

            logger.debug("📦 New database connection established")

        yield conn

        # Only commit if not read_only and no exceptions
        if not read_only:
            conn.commit()
            logger.debug("💾 Transaction committed")

    except sqlite3.Error as e:
        if conn and not read_only:
            conn.rollback()
            logger.debug("🔄 Transaction rolled back")

        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.error(
            "Database connection error",
            error_type=type(e).__name__,
            error_message=str(e),
            duration=duration,
            read_only=read_only,
            operation="connection",
        )
        raise

    except Exception as e:
        if conn and not read_only:
            conn.rollback()

        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.error(
            "Unexpected database error",
            error_type=type(e).__name__,
            error_message=str(e),
            duration=duration,
            read_only=read_only,
            operation="connection",
        )
        raise

    finally:
        # Don't close connection if it's stored in thread local
        if conn and (read_only or not hasattr(thread_local, "db_connection")):
            conn.close()
            logger.debug("🔒 Database connection closed")


@contextmanager
def transaction(conn):
    """Context manager for explicit transaction handling"""
    try:
        yield conn
        conn.commit()
        logger.debug("💾 Explicit transaction committed")
    except Exception as e:
        conn.rollback()
        logger.debug("🔄 Explicit transaction rolled back")
        raise


def init_database():
    """Enhanced database initialization with comprehensive table structure"""
    start_time = datetime.now()

    try:
        with get_db_connection() as conn:
            # Enable extension support
            conn.enable_load_extension(True)

            # Core messages table with compression support
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    message TEXT NOT NULL,
                    message_compressed BLOB, -- Compressed message for large texts
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_type TEXT DEFAULT 'user', -- user, ai, system, notification
                    parent_id INTEGER, -- For thread replies
                    room_id TEXT, -- For room/channel support
                    metadata TEXT DEFAULT '{}',
                    is_edited BOOLEAN DEFAULT FALSE,
                    edit_history TEXT DEFAULT '[]', -- JSON array of edits
                    reaction_count INTEGER DEFAULT 0,
                    flags INTEGER DEFAULT 0, -- Bit flags for pinned, deleted, etc.
                    
                    -- Indexes
                    FOREIGN KEY (parent_id) REFERENCES messages (id) ON DELETE SET NULL,
                    CHECK (message IS NOT NULL OR message_compressed IS NOT NULL)
                )
            """
            )

            # Users table for authentication
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    display_name TEXT,
                    avatar_url TEXT,
                    role TEXT DEFAULT 'user', -- user, admin, moderator
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    force_password_change BOOLEAN DEFAULT FALSE,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT DEFAULT '{}' -- JSON user preferences
                )
            """
            )

            # Projects table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active', -- active, archived, completed
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    due_date DATETIME,
                    metadata TEXT DEFAULT '{}',
                    
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """
            )

            # Tickets table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_id TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    assigned_to TEXT,
                    status TEXT DEFAULT 'open', -- open, in_progress, resolved, closed
                    priority TEXT DEFAULT 'medium', -- low, medium, high, critical
                    type TEXT DEFAULT 'task', -- task, bug, feature, question
                    due_date DATETIME,
                    estimated_hours FLOAT,
                    actual_hours FLOAT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    metadata TEXT DEFAULT '{}',
                    
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users (id),
                    FOREIGN KEY (assigned_to) REFERENCES users (id)
                )
            """
            )

            # Files table for uploads
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_hash TEXT NOT NULL, -- MD5 hash for duplicate detection
                    mime_type TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    project_id TEXT,
                    ticket_id TEXT,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    download_count INTEGER DEFAULT 0,
                    is_public BOOLEAN DEFAULT FALSE,
                    metadata TEXT DEFAULT '{}',
                    
                    FOREIGN KEY (uploaded_by) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE SET NULL
                )
            """
            )

            # Message reactions
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_reactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    reaction TEXT NOT NULL, -- emoji or custom reaction
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(message_id, user_id, reaction)
                )
            """
            )

            # Chat rooms/channels
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_rooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_public BOOLEAN DEFAULT TRUE,
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    member_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """
            )

            # Room members
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS room_members (
                    room_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT DEFAULT 'member', -- member, admin, moderator
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_read_at DATETIME,
                    
                    FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    PRIMARY KEY (room_id, user_id)
                )
            """
            )

            # AI conversations for context management
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    context TEXT, -- JSON context for AI
                    message_count INTEGER DEFAULT 0,
                    user_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_archived BOOLEAN DEFAULT FALSE,
                    
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # AI model configurations
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    model_type TEXT NOT NULL, -- ollama, custom, openai, anthropic
                    provider TEXT NOT NULL,
                    config TEXT NOT NULL, -- JSON configuration
                    capabilities TEXT DEFAULT '[]', -- JSON array of capabilities
                    is_active BOOLEAN DEFAULT TRUE,
                    rate_limit_per_minute INTEGER DEFAULT 60,
                    cost_per_token FLOAT DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # API keys and credentials
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_credentials (
                    id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL, -- openai, anthropic, etc.
                    api_key_encrypted TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used_at DATETIME,
                    usage_count INTEGER DEFAULT 0,
                    
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """
            )

            # Audit log for security
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT DEFAULT '{}',
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # Create indexes for performance
            conn.commit()

            # Create indexes for performance (after tables are committed)
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_messages_username ON messages(username)",
                "CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages(parent_id)",
                "CREATE INDEX IF NOT EXISTS idx_tickets_project ON tickets(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
                "CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_files_user ON files(uploaded_by)",
                "CREATE INDEX IF NOT EXISTS idx_reactions_message ON message_reactions(message_id)",
                "CREATE INDEX IF NOT EXISTS idx_room_members_user ON room_members(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            ]

            for index_sql in indexes:
                conn.execute(index_sql)

            conn.commit()
        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.info(
            "Database initialized successfully",
            duration=duration,
            tables_created=len(indexes) + 10,  # Approximate table count
        )

        # Verify table creation and insert default data
        _verify_database_setup()

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.error("Database initialization failed", error=str(e), duration=duration)
        raise


def _verify_database_setup():
    """Verify database setup and insert default data"""
    required_tables = [
        "messages",
        "users",
        "projects",
        "tickets",
        "files",
        "message_reactions",
        "chat_rooms",
        "room_members",
        "ai_conversations",
        "ai_models",
        "api_credentials",
        "audit_log",
    ]

    with get_db_connection() as conn:
        for table in required_tables:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
            )
            if cursor.fetchone():
                logger.info(f"✅ {table.replace('_', ' ').title()} table verified")
            else:
                logger.error(f"❌ {table.replace('_', ' ').title()} table creation failed")

        # Insert default AI models if none exist
        cursor = conn.execute("SELECT COUNT(*) as count FROM ai_models")
        if cursor.fetchone()[0] == 0:
            _insert_default_ai_models(conn)

        # Insert default admin user if no users exist
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()[0] == 0:
            _insert_default_admin_user(conn)


def _insert_default_ai_models(conn):
    """Insert default AI model configurations"""
    default_models = [
        {
            "id": str(uuid.uuid4()),
            "name": "llama2",
            "model_type": "ollama",
            "provider": "ollama",
            "config": json.dumps(
                {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "context_window": 4096,
                }
            ),
            "capabilities": json.dumps(["chat", "completion", "summarization"]),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "mistral",
            "model_type": "ollama",
            "provider": "ollama",
            "config": json.dumps(
                {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "top_p": 0.95,
                    "top_k": 50,
                    "repeat_penalty": 1.0,
                    "context_window": 8192,
                }
            ),
            "capabilities": json.dumps(["chat", "completion", "summarization", "translation"]),
        },
        {
            "id": str(uuid.uuid4()),
            "name": "custom_model",
            "model_type": "custom",
            "provider": "local",
            "config": json.dumps(
                {
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "model_path": "./models/custom_model",
                    "device": "auto",
                }
            ),
            "capabilities": json.dumps(["chat", "completion"]),
        },
    ]

    for model in default_models:
        conn.execute(
            """INSERT INTO ai_models (id, name, model_type, provider, config, capabilities) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                model["id"],
                model["name"],
                model["model_type"],
                model["provider"],
                model["config"],
                model["capabilities"],
            ),
        )

    logger.info("✅ Default AI models inserted")


def _insert_default_admin_user(conn):
    """Insert default admin user (password MUST be changed on first login)"""
    import hashlib

    admin_id = str(uuid.uuid4())

    # Default password is "admin123" - MUST be changed on first login
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()

    conn.execute(
        """INSERT INTO users (id, username, email, password_hash, display_name, role, is_verified, force_password_change)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (admin_id, "admin", "admin@localhost", password_hash, "Administrator", "admin", True, True),
    )

    logger.warning("⚠️ Default admin user created - PASSWORD CHANGE REQUIRED ON FIRST LOGIN")
    logger.info("🔐 Default credentials: admin / admin123 (You will be prompted to change this)")


# Compression utilities for large messages
def compress_text(text: str) -> bytes:
    """Compress text for storage"""
    return zlib.compress(text.encode("utf-8"))


def decompress_text(compressed_data: bytes) -> str:
    """Decompress text from storage"""
    return zlib.decompress(compressed_data).decode("utf-8")


def should_compress(text: str, threshold: int = 1000) -> bool:
    """Determine if text should be compressed based on length"""
    return len(text) > threshold


# Enhanced backup functionality
def backup_database(backup_path: Optional[str] = None, compress: bool = True) -> str:
    """Create a compressed backup of the database"""
    import shutil
    from datetime import datetime

    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backups/chat_backup_{timestamp}.db"

    try:
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

        # Use SQLite backup API for consistent backup
        with get_db_connection() as src_conn:
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                src_conn.backup(backup_conn)
            backup_conn.close()

        if compress:
            compressed_path = backup_path + ".gz"
            import gzip

            with open(backup_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            Path(backup_path).unlink()  # Remove uncompressed backup
            backup_path = compressed_path

        file_size = Path(backup_path).stat().st_size
        enhanced_logger.info(
            "Database backup created",
            backup_path=backup_path,
            file_size=file_size,
            compressed=compress,
        )
        return backup_path

    except Exception as e:
        enhanced_logger.error("Database backup failed", error=str(e), backup_path=backup_path)
        raise


def restore_database(backup_path: str):
    """Restore database from backup"""
    import shutil

    try:
        # Close any existing connections
        if hasattr(thread_local, "db_connection"):
            thread_local.db_connection.close()
            delattr(thread_local, "db_connection")

        # Handle compressed backups
        if backup_path.endswith(".gz"):
            import gzip

            uncompressed_path = backup_path[:-3]
            with gzip.open(backup_path, "rb") as f_in:
                with open(uncompressed_path, "wb") as f_out:
                    f_out.write(f_in.read())
            backup_path = uncompressed_path

        # Replace current database with backup
        Path(settings.DATABASE_URL).unlink(missing_ok=True)
        shutil.copy2(backup_path, settings.DATABASE_URL)

        logger.info(f"✅ Database restored from: {backup_path}")

    except Exception as e:
        logger.error(f"❌ Database restore failed: {e}")
        raise


# Enhanced database operations
def get_database_stats() -> Dict[str, Any]:
    """Get comprehensive database statistics"""
    stats = {"timestamp": datetime.now().isoformat()}

    try:
        with get_db_connection(read_only=True) as conn:
            # Table sizes and row counts
            tables = [
                "messages",
                "users",
                "projects",
                "tickets",
                "files",
                "message_reactions",
                "chat_rooms",
                "room_members",
                "ai_conversations",
                "ai_models",
                "api_credentials",
                "audit_log",
            ]

            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Database size and performance stats
            cursor = conn.execute(
                """
                SELECT 
                    page_count * page_size as size,
                    page_count,
                    page_size,
                    freelist_count
                FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count
            """
            )
            db_info = cursor.fetchone()
            stats.update(
                {
                    "database_size_bytes": db_info[0],
                    "page_count": db_info[1],
                    "page_size": db_info[2],
                    "freelist_count": db_info[3],
                }
            )

            # Recent activity
            time_frames = [("1h", "-1 hour"), ("24h", "-24 hours"), ("7d", "-7 days")]
            for label, interval in time_frames:
                cursor = conn.execute(
                    f"SELECT COUNT(*) as count FROM messages WHERE timestamp > datetime('now', '{interval}')"
                )
                stats[f"recent_messages_{label}"] = cursor.fetchone()[0]

            # Table sizes
            cursor = conn.execute(
                """
                SELECT name, SUM(pgsize) as size
                FROM dbstat 
                GROUP BY name
            """
            )
            for row in cursor.fetchall():
                stats[f"table_size_{row[0]}"] = row[1]

            enhanced_logger.debug("Database statistics collected", stats=stats)
            return stats

    except Exception as e:
        enhanced_logger.error("Error getting database stats", error=str(e))
        return {"error": str(e)}


def optimize_database(aggressive: bool = False):
    """Optimize database performance with various techniques"""
    start_time = datetime.now()

    try:
        with get_db_connection() as conn:
            # Basic optimizations
            conn.execute("PRAGMA optimize")
            conn.execute("PRAGMA incremental_vacuum")
            conn.execute("ANALYZE")

            if aggressive:
                # More aggressive optimizations (takes longer)
                conn.execute("VACUUM")
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.execute("PRAGMA shrink_memory")

            conn.commit()

        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.info(
            "Database optimization completed", duration=duration, aggressive=aggressive
        )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        enhanced_logger.error("Database optimization failed", error=str(e), duration=duration)


# Maintenance tasks
def run_database_maintenance():
    """Run comprehensive database maintenance tasks"""
    maintenance_log = {"timestamp": datetime.now().isoformat(), "tasks": {}, "errors": []}

    try:
        # Clean up old audit logs (keep 90 days)
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM audit_log WHERE timestamp < datetime('now', '-90 days')"
            )
            maintenance_log["tasks"]["cleanup_audit_log"] = cursor.rowcount

        # Clean up temporary files references
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM files WHERE upload_date < datetime('now', '-30 days') 
                AND project_id IS NULL AND ticket_id IS NULL
            """
            )
            maintenance_log["tasks"]["cleanup_orphaned_files"] = cursor.rowcount

        # Update statistics
        optimize_database()
        maintenance_log["tasks"]["optimization"] = "completed"

        # Create backup
        backup_path = backup_database()
        maintenance_log["tasks"]["backup"] = backup_path

        enhanced_logger.info("Database maintenance completed", maintenance_log=maintenance_log)
        return maintenance_log

    except Exception as e:
        maintenance_log["errors"].append(str(e))
        enhanced_logger.error("Database maintenance failed", maintenance_log=maintenance_log)
        return maintenance_log


# Connection pool management
def close_all_connections():
    """Close all database connections in the connection pool"""
    if hasattr(thread_local, "db_connection"):
        thread_local.db_connection.close()
        delattr(thread_local, "db_connection")
        logger.info("🔒 All database connections closed")


# Health check with more comprehensive checks
def check_database_health() -> Dict[str, Any]:
    """Perform comprehensive database health check"""
    health = {
        "status": "healthy",
        "checks": {},
        "timestamp": datetime.now().isoformat(),
        "version": sqlite3.sqlite_version,
    }

    try:
        with get_db_connection() as conn:
            # Basic connectivity
            cursor = conn.execute("SELECT 1 as test")
            if cursor.fetchone()[0] == 1:
                health["checks"]["connectivity"] = {
                    "status": "pass",
                    "message": "Database responsive",
                }

            # Table integrity
            cursor = conn.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            health["checks"]["integrity"] = {
                "status": "pass" if integrity_result == "ok" else "fail",
                "message": integrity_result,
            }

            # Foreign key consistency
            cursor = conn.execute("PRAGMA foreign_key_check")
            fk_issues = cursor.fetchall()
            health["checks"]["foreign_keys"] = {
                "status": "pass" if not fk_issues else "fail",
                "issues": len(fk_issues),
                "details": fk_issues,
            }

            # WAL mode check
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            health["checks"]["journal_mode"] = {
                "status": "pass" if journal_mode == "wal" else "warning",
                "mode": journal_mode,
            }

            # Check for long-running transactions
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM sqlite_master 
                WHERE sql LIKE '%BEGIN%' OR sql LIKE '%COMMIT%'
            """
            )
            long_tx = cursor.fetchone()[0]
            health["checks"]["transactions"] = {
                "status": "warning" if long_tx > 0 else "pass",
                "long_running_transactions": long_tx,
            }

        # Determine overall status
        failed_checks = [
            check for check, details in health["checks"].items() if details["status"] == "fail"
        ]
        warning_checks = [
            check for check, details in health["checks"].items() if details["status"] == "warning"
        ]

        if failed_checks:
            health["status"] = "unhealthy"
        elif warning_checks:
            health["status"] = "degraded"

        enhanced_logger.info(
            "Database health check completed",
            status=health["status"],
            failed_checks=len(failed_checks),
            warning_checks=len(warning_checks),
        )

        return health

    except Exception as e:
        health.update({"status": "unhealthy", "error": str(e)})
        enhanced_logger.error("Database health check failed", error=str(e))
        return health


# Export functionality with compression
def export_database_schema(export_path: Optional[str] = None) -> str:
    """Export database schema to SQL file"""
    if export_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"exports/schema_export_{timestamp}.sql"

    try:
        Path(export_path).parent.mkdir(parents=True, exist_ok=True)

        with get_db_connection(read_only=True) as conn:
            with open(export_path, "w", encoding="utf-8") as f:
                # Export schema for all tables
                cursor = conn.execute(
                    """
                    SELECT name, sql 
                    FROM sqlite_master 
                    WHERE type IN ('table', 'index', 'view') 
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY type, name
                """
                )

                for row in cursor.fetchall():
                    f.write(f"{row[1]};\n\n")

        logger.info(f"📤 Database schema exported to: {export_path}")
        return export_path

    except Exception as e:
        logger.error(f"❌ Schema export failed: {e}")
        raise


# Migration support
def get_database_version() -> str:
    """Get current database schema version"""
    try:
        with get_db_connection(read_only=True) as conn:
            cursor = conn.execute("SELECT value FROM pragma_user_version")
            return str(cursor.fetchone()[0])
    except Exception as e:
        enhanced_logger.warning(f"Failed to get database version: {e}")
        return "unknown"


def set_database_version(version: str):
    """Set database schema version"""
    with get_db_connection() as conn:
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
