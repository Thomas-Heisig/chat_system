"""
Add Performance Indexes Migration

This migration adds database indexes to improve query performance.
Based on common query patterns identified in the application.

Author: Chat System Team
Date: 2025-12-06
"""

from sqlalchemy import Index, MetaData, Table

# Index definitions for common query patterns
INDEXES = [
    # Messages table indexes
    {
        "table": "messages",
        "name": "idx_messages_username_created",
        "columns": ["username", "created_at"],
        "description": "Optimize queries filtering by username and sorting by date",
    },
    {
        "table": "messages",
        "name": "idx_messages_created_at",
        "columns": ["created_at"],
        "description": "Optimize queries sorting/filtering by creation date",
    },
    {
        "table": "messages",
        "name": "idx_messages_type",
        "columns": ["type"],
        "description": "Optimize queries filtering by message type",
    },
    # Projects table indexes
    {
        "table": "projects",
        "name": "idx_projects_status_created",
        "columns": ["status", "created_at"],
        "description": "Optimize project status filtering and date sorting",
    },
    {
        "table": "projects",
        "name": "idx_projects_owner_id",
        "columns": ["owner_id"],
        "description": "Optimize queries filtering by project owner",
    },
    # Tickets table indexes
    {
        "table": "tickets",
        "name": "idx_tickets_project_id_status",
        "columns": ["project_id", "status"],
        "description": "Optimize queries for tickets by project and status",
    },
    {
        "table": "tickets",
        "name": "idx_tickets_assigned_to",
        "columns": ["assigned_to"],
        "description": "Optimize queries for tickets assigned to users",
    },
    {
        "table": "tickets",
        "name": "idx_tickets_priority_status",
        "columns": ["priority", "status"],
        "description": "Optimize queries for high-priority open tickets",
    },
    {
        "table": "tickets",
        "name": "idx_tickets_due_date",
        "columns": ["due_date"],
        "description": "Optimize queries for upcoming/overdue tickets",
    },
    # Files table indexes
    {
        "table": "files",
        "name": "idx_files_project_id",
        "columns": ["project_id"],
        "description": "Optimize queries for files by project",
    },
    {
        "table": "files",
        "name": "idx_files_ticket_id",
        "columns": ["ticket_id"],
        "description": "Optimize queries for files by ticket",
    },
    {
        "table": "files",
        "name": "idx_files_file_type",
        "columns": ["file_type"],
        "description": "Optimize queries filtering by file type",
    },
    # Users table indexes
    {
        "table": "users",
        "name": "idx_users_username",
        "columns": ["username"],
        "description": "Optimize user lookup by username (if not already unique)",
    },
    {
        "table": "users",
        "name": "idx_users_role",
        "columns": ["role"],
        "description": "Optimize queries filtering by user role",
    },
]


def create_indexes(engine):
    """
    Create performance indexes on database tables

    Args:
        engine: SQLAlchemy engine

    Returns:
        Number of indexes created
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)

    created_count = 0

    for index_def in INDEXES:
        table_name = index_def["table"]
        index_name = index_def["name"]
        columns = index_def["columns"]

        # Check if table exists
        if table_name not in metadata.tables:
            print(
                f"Warning: Table '{table_name}' not found, skipping index '{index_name}'"
            )
            continue

        table = metadata.tables[table_name]

        # Check if index already exists
        existing_index_names = {idx.name for idx in table.indexes}
        if index_name in existing_index_names:
            print(f"Index '{index_name}' already exists, skipping")
            continue

        # Check if all columns exist in table
        table_columns = {col.name for col in table.columns}
        missing_columns = set(columns) - table_columns
        if missing_columns:
            print(
                f"Warning: Columns {missing_columns} not found in table '{table_name}', "
                f"skipping index '{index_name}'"
            )
            continue

        try:
            # Create index
            index = Index(
                index_name,
                *[table.c[col] for col in columns],
            )

            with engine.begin() as conn:
                index.create(conn)

            print(f"Created index: {index_name} on {table_name}({', '.join(columns)})")
            print(f"  Purpose: {index_def['description']}")
            created_count += 1

        except Exception as e:
            print(f"Error creating index '{index_name}': {e}")

    return created_count


def drop_indexes(engine):
    """
    Drop performance indexes from database tables

    Args:
        engine: SQLAlchemy engine

    Returns:
        Number of indexes dropped
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)

    dropped_count = 0

    for index_def in INDEXES:
        table_name = index_def["table"]
        index_name = index_def["name"]

        # Check if table exists
        if table_name not in metadata.tables:
            print(
                f"Warning: Table '{table_name}' not found, skipping index '{index_name}'"
            )
            continue

        table = metadata.tables[table_name]

        # Check if index exists
        existing_index = None
        for idx in table.indexes:
            if idx.name == index_name:
                existing_index = idx
                break

        if existing_index is None:
            print(f"Index '{index_name}' does not exist, skipping")
            continue

        try:
            # Drop index
            with engine.begin() as conn:
                existing_index.drop(conn)

            print(f"Dropped index: {index_name}")
            dropped_count += 1

        except Exception as e:
            print(f"Error dropping index '{index_name}': {e}")

    return dropped_count


if __name__ == "__main__":
    """
    Run migration from command line
    
    Usage:
        python -m database.migrations.add_performance_indexes [create|drop]
    """
    import sys

    from database.connection import get_engine

    if len(sys.argv) < 2:
        print("Usage: python -m database.migrations.add_performance_indexes [create|drop]")
        sys.exit(1)

    action = sys.argv[1].lower()

    engine = get_engine()

    if action == "create":
        print("Creating performance indexes...")
        count = create_indexes(engine)
        print(f"\nCreated {count} indexes successfully")
    elif action == "drop":
        print("Dropping performance indexes...")
        count = drop_indexes(engine)
        print(f"\nDropped {count} indexes successfully")
    else:
        print(f"Unknown action: {action}")
        print("Usage: python -m database.migrations.add_performance_indexes [create|drop]")
        sys.exit(1)
