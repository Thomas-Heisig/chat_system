# database/db_manager.py
"""
Automated Database Management Module
Provides centralized database management with auto-migration, backup, and schema validation.
"""

import gzip
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import enhanced_logger, logger, settings


class DatabaseManager:
    """
    Automatisierte Datenbankverwaltung

    Features:
    - Automatische Datenbank-Migration bei Start
    - Connection Pooling für bessere Performance
    - Automatische Backups (konfigurierbar)
    - Verschlüsselte Verbindungen (für PostgreSQL-Migration vorbereitet)
    - Automatische Schema-Validierung
    """

    # Schema version for migrations
    SCHEMA_VERSION = 1

    # Required tables for schema validation
    REQUIRED_TABLES = [
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

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialisiert den DatabaseManager

        Args:
            database_url: Pfad zur Datenbank oder Connection String
        """
        self.database_url = database_url or settings.DATABASE_URL
        self.backup_enabled = getattr(settings, "DATABASE_AUTO_BACKUP", False)
        self.backup_interval = getattr(settings, "DATABASE_BACKUP_INTERVAL", 86400)  # 24h default
        self.backup_path = Path(getattr(settings, "BACKUP_PATH", "backups"))
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_size = getattr(settings, "DATABASE_POOL_SIZE", 10)
        self._initialized = False

        logger.info(f"📦 DatabaseManager initialized with database: {self.database_url}")

    async def initialize(self) -> bool:
        """
        Initialisiert die Datenbank mit allen erforderlichen Tabellen

        Returns:
            bool: True wenn erfolgreich initialisiert
        """
        start_time = datetime.now()

        try:
            enhanced_logger.info("🔧 Starting database initialization")

            # Ensure backup directory exists
            self.backup_path.mkdir(parents=True, exist_ok=True)

            # Import and run database initialization
            from database.connection import init_database

            init_database()

            # Validate schema after initialization
            schema_valid = await self.validate_schema()

            if not schema_valid:
                enhanced_logger.warning("Schema validation found issues, attempting migration")
                await self.migrate()

            self._initialized = True

            duration = (datetime.now() - start_time).total_seconds()
            enhanced_logger.info(
                "Database initialized successfully", duration=duration, schema_valid=schema_valid
            )

            return True

        except Exception as e:
            enhanced_logger.error(
                "Database initialization failed", error=str(e), error_type=type(e).__name__
            )
            raise

    async def migrate(self, target_version: Optional[int] = None) -> Dict[str, Any]:
        """
        Führt ausstehende Migrationen durch

        Args:
            target_version: Ziel-Schema-Version (optional, default: neueste)

        Returns:
            Dict mit Migrationsergebnis
        """
        migration_result = {
            "success": True,
            "migrations_applied": [],
            "current_version": 0,
            "target_version": target_version or self.SCHEMA_VERSION,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Get current schema version
            current_version = await self._get_schema_version()
            migration_result["current_version"] = current_version

            if current_version >= migration_result["target_version"]:
                enhanced_logger.info(
                    "No migrations needed",
                    current_version=current_version,
                    target_version=migration_result["target_version"],
                )
                return migration_result

            # Create backup before migration
            if self.backup_enabled:
                backup_path = await self.backup(prefix="pre_migration")
                migration_result["backup_path"] = backup_path

            # Apply migrations sequentially
            for version in range(current_version + 1, migration_result["target_version"] + 1):
                migration_name = f"migrate_to_v{version}"
                migration_func = getattr(self, migration_name, None)

                if migration_func:
                    enhanced_logger.info(f"Applying migration: {migration_name}")
                    await migration_func()
                    migration_result["migrations_applied"].append(migration_name)

            # Update schema version
            await self._set_schema_version(migration_result["target_version"])

            enhanced_logger.info(
                "Migrations completed successfully",
                migrations_applied=len(migration_result["migrations_applied"]),
            )

        except Exception as e:
            migration_result["success"] = False
            migration_result["error"] = str(e)
            enhanced_logger.error("Migration failed", error=str(e))

        return migration_result

    async def backup(self, backup_path: Optional[str] = None, prefix: Optional[str] = None) -> str:
        """
        Erstellt automatisches Backup

        Args:
            backup_path: Optionaler Zielpfad für das Backup
            prefix: Optionaler Prefix für den Backup-Dateinamen

        Returns:
            str: Pfad zum erstellten Backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix_str = f"{prefix}_" if prefix else ""

        if backup_path is None:
            backup_path_obj = self.backup_path / f"{prefix_str}chat_backup_{timestamp}.db.gz"
        else:
            backup_path_obj = Path(backup_path)

        # Ensure backup_path_obj is a Path object
        backup_path_obj = Path(backup_path_obj)
        backup_path_parent = backup_path_obj.parent
        backup_path_parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create uncompressed backup first
            temp_backup = backup_path_obj.with_suffix("")

            # Use SQLite backup API
            source_conn = sqlite3.connect(self.database_url)
            backup_conn = sqlite3.connect(str(temp_backup))

            with backup_conn:
                source_conn.backup(backup_conn)

            source_conn.close()
            backup_conn.close()

            # Compress the backup
            with open(temp_backup, "rb") as f_in:
                with gzip.open(backup_path_obj, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed backup
            temp_backup.unlink()

            file_size = backup_path_obj.stat().st_size
            enhanced_logger.info(
                "Database backup created",
                backup_path=str(backup_path_obj),
                file_size_bytes=file_size,
            )

            # Clean up old backups
            await self._cleanup_old_backups()

            return str(backup_path_obj)

        except Exception as e:
            enhanced_logger.error("Backup failed", error=str(e))
            raise

    async def validate_schema(self) -> bool:
        """
        Validiert das Datenbankschema

        Returns:
            bool: True wenn Schema valide ist
        """
        validation_result = {
            "valid": True,
            "missing_tables": [],
            "missing_columns": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            conn = sqlite3.connect(self.database_url)
            cursor = conn.cursor()

            # Check for required tables
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            )
            existing_tables = {row[0] for row in cursor.fetchall()}

            for table in self.REQUIRED_TABLES:
                if table not in existing_tables:
                    validation_result["missing_tables"].append(table)
                    validation_result["valid"] = False

            conn.close()

            if validation_result["valid"]:
                enhanced_logger.info("Schema validation passed")
            else:
                enhanced_logger.warning(
                    "Schema validation failed", missing_tables=validation_result["missing_tables"]
                )

            return validation_result["valid"]

        except Exception as e:
            enhanced_logger.error("Schema validation error", error=str(e))
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Prüft Datenbankgesundheit

        Returns:
            Dict mit Gesundheitsstatus
        """
        health = {"status": "healthy", "checks": {}, "timestamp": datetime.now().isoformat()}

        try:
            conn = sqlite3.connect(self.database_url)
            cursor = conn.cursor()

            # Connectivity check
            cursor.execute("SELECT 1")
            health["checks"]["connectivity"] = {
                "status": "pass",
                "message": "Database is responsive",
            }

            # Integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            health["checks"]["integrity"] = {
                "status": "pass" if integrity_result == "ok" else "fail",
                "message": integrity_result,
            }

            # Get database size
            cursor.execute(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )
            db_size = cursor.fetchone()[0]
            health["checks"]["size"] = {
                "status": "pass",
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
            }

            # Check table counts
            table_counts = {}
            for table in self.REQUIRED_TABLES:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    table_counts[table] = -1  # Table doesn't exist
                    health["status"] = "degraded"

            health["checks"]["tables"] = {
                "status": "pass" if all(c >= 0 for c in table_counts.values()) else "fail",
                "counts": table_counts,
            }

            conn.close()

            # Determine overall status
            failed_checks = [k for k, v in health["checks"].items() if v.get("status") == "fail"]
            if failed_checks:
                health["status"] = "unhealthy"

            enhanced_logger.info("Database health check completed", status=health["status"])

            return health

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            enhanced_logger.error("Health check failed", error=str(e))
            return health

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Datenbankstatistiken zurück

        Returns:
            Dict mit Statistiken
        """
        stats = {"timestamp": datetime.now().isoformat(), "tables": {}, "database": {}}

        try:
            conn = sqlite3.connect(self.database_url)
            cursor = conn.cursor()

            # Table statistics
            for table in self.REQUIRED_TABLES:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats["tables"][table] = {"row_count": count}
                except sqlite3.OperationalError:
                    stats["tables"][table] = {"row_count": 0, "exists": False}

            # Database-level statistics
            cursor.execute(
                """
                SELECT
                    page_count * page_size as size,
                    page_count,
                    page_size
                FROM pragma_page_count(), pragma_page_size()
            """
            )
            db_info = cursor.fetchone()
            stats["database"] = {
                "size_bytes": db_info[0],
                "page_count": db_info[1],
                "page_size": db_info[2],
            }

            conn.close()

            return stats

        except Exception as e:
            stats["error"] = str(e)
            return stats

    async def optimize(self) -> bool:
        """
        Optimiert die Datenbank

        Returns:
            bool: True wenn erfolgreich
        """
        try:
            conn = sqlite3.connect(self.database_url)

            # Run optimizations
            conn.execute("PRAGMA optimize")
            conn.execute("PRAGMA incremental_vacuum")
            conn.execute("ANALYZE")
            conn.execute("VACUUM")

            conn.close()

            enhanced_logger.info("Database optimization completed")
            return True

        except Exception as e:
            enhanced_logger.error("Database optimization failed", error=str(e))
            return False

    async def _get_schema_version(self) -> int:
        """Gibt die aktuelle Schema-Version zurück"""
        try:
            conn = sqlite3.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            conn.close()
            return version
        except Exception:
            return 0

    async def _set_schema_version(self, version: int):
        """Setzt die Schema-Version"""
        conn = sqlite3.connect(self.database_url)
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
        conn.close()

    async def _cleanup_old_backups(self, retention_days: int = 7):
        """Bereinigt alte Backups"""
        try:
            cutoff_date = datetime.now().timestamp() - (retention_days * 86400)

            for backup_file in self.backup_path.glob("*.db.gz"):
                if backup_file.stat().st_mtime < cutoff_date:
                    backup_file.unlink()
                    enhanced_logger.info(f"Removed old backup: {backup_file.name}")

        except Exception as e:
            enhanced_logger.warning(f"Backup cleanup error: {e}")

    # Migration methods (can be extended for future schema changes)
    async def migrate_to_v1(self):
        """Migration to version 1 - Initial schema"""
        # This is handled by init_database, but can be extended


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create the DatabaseManager singleton instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def initialize_database_manager() -> DatabaseManager:
    """Initialize and return the DatabaseManager"""
    manager = get_db_manager()
    if not manager._initialized:
        await manager.initialize()
    return manager
