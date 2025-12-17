#!/usr/bin/env python3
"""
Database Migration: Add Search and Performance Indexes

This migration adds indexes to improve search performance across the application.
These indexes optimize:
- Full-text search on message content
- User lookups by username and email
- Project and ticket searches by name/title
- Date range queries on messages
- Room and project message filtering

Run with:
    python -m database.migrations.add_search_indexes create
    python -m database.migrations.add_search_indexes drop
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.connection import get_database_session
from database.models import Message, Project, Ticket, User
from sqlalchemy import Index, create_engine, text
from sqlalchemy.orm import Session

from config.settings import logger


def create_search_indexes():
    """Create search and performance indexes"""
    logger.info("🔄 Creating search and performance indexes...")

    try:
        session = get_database_session()
        engine = session.get_bind()

        # Track created indexes
        created_indexes = []

        # Message content search indexes
        indexes_to_create = [
            # Message search indexes
            Index("idx_messages_content_search", Message.content),  # Content search
            Index("idx_messages_username_search", Message.username),  # Username lookup
            Index(
                "idx_messages_created_at_desc", Message.created_at.desc()
            ),  # Recent messages
            Index("idx_messages_type_created", Message.type, Message.created_at),  # Type filter
            Index(
                "idx_messages_room_created", Message.room_id, Message.created_at
            ),  # Room messages
            Index(
                "idx_messages_project_created", Message.project_id, Message.created_at
            ),  # Project messages
            Index(
                "idx_messages_ticket_created", Message.ticket_id, Message.created_at
            ),  # Ticket messages
            # User search indexes
            Index("idx_users_username_lower", text("LOWER(username)")),  # Case-insensitive search
            Index("idx_users_email_lower", text("LOWER(email)")),  # Case-insensitive email search
            Index("idx_users_display_name", User.display_name),  # Display name search
            Index("idx_users_is_active", User.is_active),  # Active user filter
            Index("idx_users_role_active", User.role, User.is_active),  # Role filter
            Index("idx_users_last_login", User.last_login),  # Recent activity
            # Project search indexes
            Index("idx_projects_name_lower", text("LOWER(name)")),  # Case-insensitive search
            Index("idx_projects_status_updated", Project.status, Project.updated_at),  # Status filter
            Index("idx_projects_owner_status", Project.owner_id, Project.status),  # Owner projects
            Index("idx_projects_created_at", Project.created_at.desc()),  # Recent projects
            # Ticket search indexes
            Index("idx_tickets_title_lower", text("LOWER(title)")),  # Case-insensitive search
            Index(
                "idx_tickets_project_status", Ticket.project_id, Ticket.status
            ),  # Project tickets
            Index(
                "idx_tickets_assigned_status", Ticket.assigned_to, Ticket.status
            ),  # Assigned tickets
            Index("idx_tickets_priority_status", Ticket.priority, Ticket.status),  # Priority filter
            Index("idx_tickets_due_date", Ticket.due_date),  # Upcoming tickets
            Index("idx_tickets_created_at", Ticket.created_at.desc()),  # Recent tickets
        ]

        # Create indexes
        for index in indexes_to_create:
            try:
                # Check if using SQLite (doesn't support all index features)
                if "sqlite" in str(engine.url):
                    # Skip indexes with expressions for SQLite
                    if any(
                        x in index.name for x in ["_lower", "_desc"]
                    ):  # Skip expression indexes
                        logger.info(f"⏭️  Skipping index {index.name} (not supported in SQLite)")
                        continue

                index.create(engine)
                created_indexes.append(index.name)
                logger.info(f"✅ Created index: {index.name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not create index {index.name}: {e}")

        logger.info(
            f"✅ Search indexes created successfully! Total: {len(created_indexes)}/{len(indexes_to_create)}"
        )
        logger.info(f"📊 Created indexes: {', '.join(created_indexes)}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create search indexes: {e}")
        return False


def drop_search_indexes():
    """Drop search and performance indexes"""
    logger.info("🔄 Dropping search and performance indexes...")

    try:
        session = get_database_session()
        engine = session.get_bind()

        # List of index names to drop
        index_names = [
            "idx_messages_content_search",
            "idx_messages_username_search",
            "idx_messages_created_at_desc",
            "idx_messages_type_created",
            "idx_messages_room_created",
            "idx_messages_project_created",
            "idx_messages_ticket_created",
            "idx_users_username_lower",
            "idx_users_email_lower",
            "idx_users_display_name",
            "idx_users_is_active",
            "idx_users_role_active",
            "idx_users_last_login",
            "idx_projects_name_lower",
            "idx_projects_status_updated",
            "idx_projects_owner_status",
            "idx_projects_created_at",
            "idx_tickets_title_lower",
            "idx_tickets_project_status",
            "idx_tickets_assigned_status",
            "idx_tickets_priority_status",
            "idx_tickets_due_date",
            "idx_tickets_created_at",
        ]

        dropped = []
        for index_name in index_names:
            try:
                # SQLAlchemy 2.0+ compatible execution
                with engine.begin() as conn:
                    conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                dropped.append(index_name)
                logger.info(f"✅ Dropped index: {index_name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not drop index {index_name}: {e}")

        logger.info(f"✅ Search indexes dropped! Total: {len(dropped)}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to drop search indexes: {e}")
        return False


def main():
    """Main migration script"""
    if len(sys.argv) < 2:
        print("Usage: python -m database.migrations.add_search_indexes [create|drop]")
        sys.exit(1)

    command = sys.argv[1].lower()

    logger.info("=" * 80)
    logger.info("🔧 Database Migration: Search and Performance Indexes")
    logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🎯 Command: {command}")
    logger.info("=" * 80)

    if command == "create":
        success = create_search_indexes()
    elif command == "drop":
        success = drop_search_indexes()
    else:
        logger.error(f"❌ Unknown command: {command}")
        logger.info("Valid commands: create, drop")
        sys.exit(1)

    logger.info("=" * 80)
    logger.info(f"✅ Migration completed: {'SUCCESS' if success else 'FAILED'}")
    logger.info(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
