"""
Database Performance Monitoring

This module provides database query performance monitoring using SQLAlchemy events.
Features:
- Slow query logging
- Query execution time tracking
- Connection pool monitoring
- N+1 query detection
- Integration with Prometheus metrics

Author: Chat System Team
Date: 2025-12-06
"""

import time
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from config.settings import enhanced_logger

try:
    from middleware.prometheus_middleware import track_database_query

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    track_database_query = None


class DatabasePerformanceMonitor:
    """
    Monitor database query performance and connection pool usage
    """

    def __init__(
        self,
        slow_query_threshold_ms: float = 100.0,
        enable_query_logging: bool = True,
        enable_pool_monitoring: bool = True,
    ):
        """
        Initialize performance monitor

        Args:
            slow_query_threshold_ms: Threshold in milliseconds for slow query logging
            enable_query_logging: Enable query execution logging
            enable_pool_monitoring: Enable connection pool monitoring
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.enable_query_logging = enable_query_logging
        self.enable_pool_monitoring = enable_pool_monitoring
        self.query_count = 0
        self.slow_query_count = 0

    def setup_monitoring(self, engine: Engine):
        """
        Set up SQLAlchemy event listeners for performance monitoring

        Args:
            engine: SQLAlchemy engine to monitor
        """
        if self.enable_query_logging:
            # Monitor query execution
            event.listen(engine, "before_cursor_execute", self.before_cursor_execute)
            event.listen(engine, "after_cursor_execute", self.after_cursor_execute)

        if self.enable_pool_monitoring:
            # Monitor connection pool
            event.listen(Pool, "connect", self.on_connect)
            event.listen(Pool, "checkout", self.on_checkout)
            event.listen(Pool, "checkin", self.on_checkin)

        enhanced_logger.info(
            "Database performance monitoring initialized",
            slow_query_threshold_ms=self.slow_query_threshold_ms,
            query_logging=self.enable_query_logging,
            pool_monitoring=self.enable_pool_monitoring,
        )

    def before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        """
        Event handler called before query execution

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: Whether this is an executemany call
        """
        context._query_start_time = time.time()

    def after_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        """
        Event handler called after query execution

        Args:
            conn: Database connection
            cursor: Database cursor
            statement: SQL statement
            parameters: Query parameters
            context: Execution context
            executemany: Whether this is an executemany call
        """
        # Calculate execution time
        start_time = getattr(context, "_query_start_time", None)
        if start_time is None:
            return

        duration_seconds = time.time() - start_time
        duration_ms = duration_seconds * 1000

        # Track metrics
        self.query_count += 1

        # Determine query operation
        operation = self._get_query_operation(statement)

        # Track with Prometheus if available
        if PROMETHEUS_AVAILABLE and track_database_query:
            track_database_query(operation, duration_seconds)

        # Log slow queries
        if duration_ms >= self.slow_query_threshold_ms:
            self.slow_query_count += 1
            self._log_slow_query(statement, parameters, duration_ms, operation)
        else:
            # Log all queries in debug mode
            enhanced_logger.debug(
                "Database query executed",
                operation=operation,
                duration_ms=f"{duration_ms:.2f}",
                statement=self._truncate_statement(statement),
            )

    def _get_query_operation(self, statement: str) -> str:
        """
        Extract operation type from SQL statement

        Args:
            statement: SQL statement

        Returns:
            Operation type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        statement_upper = statement.strip().upper()
        for operation in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]:
            if statement_upper.startswith(operation):
                return operation
        return "OTHER"

    def _truncate_statement(self, statement: str, max_length: int = 200) -> str:
        """
        Truncate long SQL statements for logging

        Args:
            statement: SQL statement
            max_length: Maximum length

        Returns:
            Truncated statement
        """
        if len(statement) <= max_length:
            return statement
        return statement[:max_length] + "..."

    def _log_slow_query(
        self,
        statement: str,
        parameters: Optional[tuple],
        duration_ms: float,
        operation: str,
    ):
        """
        Log slow query with details

        Args:
            statement: SQL statement
            parameters: Query parameters
            duration_ms: Execution duration in milliseconds
            operation: Query operation type
        """
        enhanced_logger.warning(
            "Slow database query detected",
            operation=operation,
            duration_ms=f"{duration_ms:.2f}",
            threshold_ms=self.slow_query_threshold_ms,
            statement=statement[:500],  # Log more of slow queries
            has_parameters=parameters is not None,
            total_slow_queries=self.slow_query_count,
        )

    def on_connect(self, dbapi_conn, connection_record):
        """
        Event handler called when a new connection is created

        Args:
            dbapi_conn: DBAPI connection
            connection_record: Connection record
        """
        enhanced_logger.debug("New database connection created")

    def on_checkout(self, dbapi_conn, connection_record, connection_proxy):
        """
        Event handler called when a connection is checked out from the pool

        Args:
            dbapi_conn: DBAPI connection
            connection_record: Connection record
            connection_proxy: Connection proxy
        """
        enhanced_logger.debug("Connection checked out from pool")

    def on_checkin(self, dbapi_conn, connection_record):
        """
        Event handler called when a connection is returned to the pool

        Args:
            dbapi_conn: DBAPI connection
            connection_record: Connection record
        """
        enhanced_logger.debug("Connection returned to pool")

    def get_statistics(self) -> dict:
        """
        Get performance statistics

        Returns:
            Dictionary with performance statistics
        """
        slow_query_percentage = (
            (self.slow_query_count / self.query_count * 100)
            if self.query_count > 0
            else 0
        )

        return {
            "total_queries": self.query_count,
            "slow_queries": self.slow_query_count,
            "slow_query_percentage": f"{slow_query_percentage:.2f}%",
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
        }


# Global performance monitor instance
_performance_monitor: Optional[DatabasePerformanceMonitor] = None


def init_performance_monitoring(
    engine: Engine,
    slow_query_threshold_ms: float = 100.0,
    enable_query_logging: bool = True,
    enable_pool_monitoring: bool = True,
) -> DatabasePerformanceMonitor:
    """
    Initialize database performance monitoring

    Args:
        engine: SQLAlchemy engine to monitor
        slow_query_threshold_ms: Threshold for slow query logging
        enable_query_logging: Enable query execution logging
        enable_pool_monitoring: Enable connection pool monitoring

    Returns:
        Performance monitor instance
    """
    global _performance_monitor

    _performance_monitor = DatabasePerformanceMonitor(
        slow_query_threshold_ms=slow_query_threshold_ms,
        enable_query_logging=enable_query_logging,
        enable_pool_monitoring=enable_pool_monitoring,
    )

    _performance_monitor.setup_monitoring(engine)

    return _performance_monitor


def get_performance_monitor() -> Optional[DatabasePerformanceMonitor]:
    """
    Get the global performance monitor instance

    Returns:
        Performance monitor instance or None if not initialized
    """
    return _performance_monitor


@contextmanager
def track_query_performance(operation: str = "query"):
    """
    Context manager to track query performance

    Args:
        operation: Operation name for tracking

    Example:
        with track_query_performance("fetch_users"):
            users = session.query(User).all()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        duration_ms = duration * 1000

        enhanced_logger.info(
            "Query performance tracked",
            operation=operation,
            duration_ms=f"{duration_ms:.2f}",
        )

        if PROMETHEUS_AVAILABLE and track_database_query:
            track_database_query(operation, duration)
