import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from config.settings import enhanced_logger


class ConnectionState(Enum):
    """Connection state enumeration"""

    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    INACTIVE = "inactive"


class ConnectionType(Enum):
    """Connection type enumeration"""

    USER = "user"
    AI_ASSISTANT = "ai_assistant"
    SYSTEM = "system"
    GUEST = "guest"


class ConnectionManager:
    """
    Enhanced WebSocket Connection Manager with advanced features:
    - Connection pooling and state management
    - User session tracking
    - Room/channel support
    - Message queuing and delivery guarantees
    - Performance monitoring
    - Security features
    """

    def __init__(self):
        # Active connections
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

        # User and room management
        self.user_connections: Dict[str, Set[WebSocket]] = {}  # username -> set of connections
        self.room_connections: Dict[str, Set[WebSocket]] = {}  # room_id -> set of connections
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}  # connection -> set of rooms

        # Message statistics and monitoring
        self.message_stats = {
            "total_messages_sent": 0,
            "total_broadcasts": 0,
            "total_errors": 0,
            "peak_connections": 0,
            "total_connections": 0,
            "messages_by_type": {},
            "active_rooms": set(),
        }

        # Performance tracking
        self.performance_metrics = {
            "avg_response_time": 0,
            "message_queue_size": 0,
            "concurrent_broadcasts": 0,
        }

        # Message queue for guaranteed delivery
        self.message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        enhanced_logger.info(
            "ConnectionManager initialized",
            features=[
                "connection_pooling",
                "user_session_tracking",
                "room_management",
                "message_queuing",
                "performance_monitoring",
            ],
        )

    async def connect(self, websocket: WebSocket, user_agent: Optional[str] = None) -> str:
        """Accept WebSocket connection with enhanced tracking"""
        start_time = datetime.now()

        try:
            await websocket.accept()
            self.active_connections.append(websocket)

            # Generate unique connection ID
            connection_id = str(uuid.uuid4())
            client_info = self._get_client_info(websocket)

            # Store comprehensive connection info
            self.connection_info[websocket] = {
                "id": connection_id,
                "connected_at": start_time,
                "client_info": client_info,
                "user_agent": user_agent,
                "message_count": 0,
                "last_activity": start_time,
                "username": None,
                "user_id": None,
                "state": ConnectionState.CONNECTED,
                "connection_type": ConnectionType.GUEST,
                "rooms": set(),
                "ping_count": 0,
                "last_ping": None,
                "ip_address": self._get_client_ip(websocket),
            }

            # Update statistics
            current_count = len(self.active_connections)
            self.message_stats["total_connections"] += 1

            if current_count > self.message_stats["peak_connections"]:
                self.message_stats["peak_connections"] = current_count

            connection_duration = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.info(
                "WebSocket connection established",
                connection_id=connection_id,
                client_info=client_info,
                user_agent=user_agent,
                connection_duration_ms=connection_duration,
                active_connections=current_count,
            )

            return connection_id

        except Exception as e:
            connection_duration = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.error(
                "WebSocket connection failed",
                error=str(e),
                client_info=self._get_client_info(websocket),
                connection_duration_ms=connection_duration,
            )
            raise

    def disconnect(self, websocket: WebSocket, reason: str = "normal"):
        """Remove WebSocket connection with comprehensive cleanup"""
        try:
            if websocket in self.active_connections:
                connection_info = self.connection_info.get(websocket, {})
                connection_id = connection_info.get("id", "unknown")
                username = connection_info.get("username")
                client_info = connection_info.get("client_info", "Unknown client")

                # Calculate connection duration
                connection_duration = "N/A"
                if "connected_at" in connection_info:
                    duration = datetime.now() - connection_info["connected_at"]
                    connection_duration = f"{duration.total_seconds():.1f}s"

                # Remove from user connections
                if username and username in self.user_connections:
                    self.user_connections[username].discard(websocket)
                    if not self.user_connections[username]:
                        del self.user_connections[username]

                # Remove from rooms
                if websocket in self.connection_rooms:
                    for room_id in self.connection_rooms[websocket]:
                        if room_id in self.room_connections:
                            self.room_connections[room_id].discard(websocket)
                            if not self.room_connections[room_id]:
                                del self.room_connections[room_id]
                                self.message_stats["active_rooms"].discard(room_id)
                    del self.connection_rooms[websocket]

                # Remove from active connections
                self.active_connections.remove(websocket)

                # Remove connection info
                if websocket in self.connection_info:
                    del self.connection_info[websocket]

                enhanced_logger.info(
                    "WebSocket connection closed",
                    connection_id=connection_id,
                    client_info=client_info,
                    username=username,
                    reason=reason,
                    connection_duration=connection_duration,
                    remaining_connections=len(self.active_connections),
                )

            else:
                enhanced_logger.warning(
                    "Attempted to disconnect non-existent connection",
                    client_info=self._get_client_info(websocket),
                )

        except Exception as e:
            enhanced_logger.error(
                "Error during connection cleanup",
                error=str(e),
                client_info=self._get_client_info(websocket),
            )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket, message_type: str = "chat"
    ) -> bool:
        """Send personal message with delivery confirmation"""
        start_time = datetime.now()

        try:
            if websocket not in self.active_connections:
                enhanced_logger.warning(
                    "Attempted to send message to disconnected client", message_type=message_type
                )
                return False

            # Add metadata to message
            enhanced_message = {
                **message,
                "_metadata": {
                    "message_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "type": message_type,
                },
            }

            await websocket.send_text(json.dumps(enhanced_message))

            # Update connection stats
            if websocket in self.connection_info:
                self.connection_info[websocket]["message_count"] += 1
                self.connection_info[websocket]["last_activity"] = datetime.now()

            # Update message statistics
            self.message_stats["total_messages_sent"] += 1
            self.message_stats["messages_by_type"][message_type] = (
                self.message_stats["messages_by_type"].get(message_type, 0) + 1
            )

            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.debug(
                "Personal message delivered",
                message_type=message_type,
                delivery_time_ms=delivery_time,
                client_info=self._get_client_info(websocket),
            )

            return True

        except Exception as e:
            delivery_time = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.error(
                "Failed to send personal message",
                error=str(e),
                message_type=message_type,
                delivery_time_ms=delivery_time,
                client_info=self._get_client_info(websocket),
            )
            self.message_stats["total_errors"] += 1
            return False

    async def broadcast(
        self,
        message: Dict[str, Any],
        room_id: Optional[str] = None,
        exclude: Optional[List[WebSocket]] = None,
        message_type: str = "broadcast",
    ) -> Dict[str, Any]:
        """
        Enhanced broadcast with room support and exclusions
        Returns delivery statistics
        """
        start_time = datetime.now()

        if exclude is None:
            exclude = []

        # Determine target connections
        if room_id:
            target_connections = self.room_connections.get(room_id, set()) - set(exclude)
        else:
            target_connections = set(self.active_connections) - set(exclude)

        if not target_connections:
            enhanced_logger.debug("No target connections for broadcast", room_id=room_id)
            return {"success": 0, "errors": 0, "total": 0}

        enhanced_logger.debug(
            "Starting broadcast",
            room_id=room_id,
            target_count=len(target_connections),
            message_type=message_type,
        )

        # Add metadata to message
        broadcast_id = str(uuid.uuid4())
        enhanced_message = {
            **message,
            "_metadata": {
                "broadcast_id": broadcast_id,
                "timestamp": datetime.now().isoformat(),
                "type": message_type,
                "room_id": room_id,
            },
        }

        message_json = json.dumps(enhanced_message)
        success_count = 0
        error_count = 0
        disconnected_clients = []

        # Send to all target connections concurrently
        send_tasks = []
        for connection in target_connections:
            task = self._send_to_client(connection, message_json)
            send_tasks.append(task)

        # Wait for all send operations
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                connection = list(target_connections)[i]
                if isinstance(result, Exception):
                    error_count += 1
                    disconnected_clients.append(connection)
                    enhanced_logger.debug(
                        "Broadcast failed for client",
                        client_info=self._get_client_info(connection),
                        error=str(result),
                    )
                else:
                    success_count += 1

        # Clean up disconnected clients
        for connection in disconnected_clients:
            self.disconnect(connection, reason="broadcast_failure")

        # Update statistics
        self.message_stats["total_broadcasts"] += 1
        self.message_stats["total_messages_sent"] += success_count
        self.message_stats["total_errors"] += error_count
        self.message_stats["messages_by_type"][message_type] = (
            self.message_stats["messages_by_type"].get(message_type, 0) + success_count
        )

        broadcast_duration = (datetime.now() - start_time).total_seconds() * 1000
        enhanced_logger.info(
            "Broadcast completed",
            broadcast_id=broadcast_id,
            room_id=room_id,
            success_count=success_count,
            error_count=error_count,
            disconnected_count=len(disconnected_clients),
            duration_ms=broadcast_duration,
        )

        return {
            "success": success_count,
            "errors": error_count,
            "total": len(target_connections),
            "broadcast_id": broadcast_id,
        }

    async def _send_to_client(self, connection: WebSocket, message_json: str) -> bool:
        """Send message to single client with enhanced error handling"""
        try:
            await connection.send_text(message_json)

            # Update connection stats
            if connection in self.connection_info:
                self.connection_info[connection]["message_count"] += 1
                self.connection_info[connection]["last_activity"] = datetime.now()

            return True

        except Exception as e:
            enhanced_logger.debug(
                "Failed to send to client",
                client_info=self._get_client_info(connection),
                error=str(e),
            )
            raise e

    # Room Management Methods
    async def join_room(self, websocket: WebSocket, room_id: str) -> bool:
        """Add connection to a room"""
        try:
            if websocket not in self.active_connections:
                return False

            # Initialize room sets if needed
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
                self.message_stats["active_rooms"].add(room_id)

            if websocket not in self.connection_rooms:
                self.connection_rooms[websocket] = set()

            # Add to room
            self.room_connections[room_id].add(websocket)
            self.connection_rooms[websocket].add(room_id)

            enhanced_logger.info(
                "User joined room",
                room_id=room_id,
                client_info=self._get_client_info(websocket),
                username=self.connection_info[websocket].get("username"),
                room_size=len(self.room_connections[room_id]),
            )

            return True

        except Exception as e:
            enhanced_logger.error(
                "Failed to join room",
                error=str(e),
                room_id=room_id,
                client_info=self._get_client_info(websocket),
            )
            return False

    async def leave_room(self, websocket: WebSocket, room_id: str) -> bool:
        """Remove connection from a room"""
        try:
            if room_id in self.room_connections and websocket in self.room_connections[room_id]:

                self.room_connections[room_id].discard(websocket)
                if websocket in self.connection_rooms:
                    self.connection_rooms[websocket].discard(room_id)

                # Clean up empty room
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
                    self.message_stats["active_rooms"].discard(room_id)

                enhanced_logger.debug(
                    "User left room",
                    room_id=room_id,
                    client_info=self._get_client_info(websocket),
                    username=self.connection_info[websocket].get("username"),
                )

                return True
            return False

        except Exception as e:
            enhanced_logger.error(
                "Failed to leave room",
                error=str(e),
                room_id=room_id,
                client_info=self._get_client_info(websocket),
            )
            return False

    # User Management Methods
    def authenticate_user(
        self, websocket: WebSocket, username: Optional[str], user_id: Optional[str] = None
    ) -> bool:
        """Authenticate user and update connection info"""
        try:
            if websocket in self.connection_info:
                old_username = self.connection_info[websocket].get("username")

                # Update connection info
                self.connection_info[websocket].update(
                    {
                        "username": username,
                        "user_id": user_id,
                        "state": (
                            ConnectionState.AUTHENTICATED if username else ConnectionState.CONNECTED
                        ),
                        "connection_type": (
                            ConnectionType.USER if username else ConnectionType.GUEST
                        ),
                    }
                )

                # Update user connections mapping
                if old_username and old_username in self.user_connections:
                    self.user_connections[old_username].discard(websocket)
                    if not self.user_connections[old_username]:
                        del self.user_connections[old_username]

                if username:
                    if username not in self.user_connections:
                        self.user_connections[username] = set()
                    self.user_connections[username].add(websocket)

                enhanced_logger.info(
                    "User authenticated",
                    username=username,
                    user_id=user_id,
                    client_info=self._get_client_info(websocket),
                    old_username=old_username,
                )

                return True
            return False

        except Exception as e:
            enhanced_logger.error(
                "User authentication failed",
                error=str(e),
                username=username,
                client_info=self._get_client_info(websocket),
            )
            return False

    def get_user_connections(self, username: str) -> List[WebSocket]:
        """Get all connections for a specific user"""
        connections = list(self.user_connections.get(username, set()))
        enhanced_logger.debug(
            "Retrieved user connections", username=username, connection_count=len(connections)
        )
        return connections

    # Statistics and Monitoring Methods
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        stats = {
            "active_connections": len(self.active_connections),
            "total_connections_tracked": len(self.connection_info),
            "active_rooms": len(self.message_stats["active_rooms"]),
            "authenticated_users": len(self.user_connections),
            "message_stats": self.message_stats.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "connections": [],
        }

        for info in self.connection_info.values():
            state = info.get("state")
            connection_type = info.get("connection_type")
            connected_at = info.get("connected_at")
            last_activity = info.get("last_activity")

            connection_stats = {
                "connection_id": info.get("id"),
                "client_info": info.get("client_info"),
                "username": info.get("username"),
                "user_id": info.get("user_id"),
                "state": state.value if isinstance(state, Enum) else None,
                "connection_type": (
                    connection_type.value if isinstance(connection_type, Enum) else None
                ),
                "message_count": info.get("message_count", 0),
                "rooms": list(info.get("rooms", set())),
                "connected_at": (
                    connected_at.isoformat() if isinstance(connected_at, datetime) else None
                ),
                "last_activity": (
                    last_activity.isoformat() if isinstance(last_activity, datetime) else None
                ),
                "connection_duration_seconds": None,
            }

            if info.get("connected_at"):
                duration = datetime.now() - info["connected_at"]
                connection_stats["connection_duration_seconds"] = duration.total_seconds()

            stats["connections"].append(connection_stats)

        return stats

    def get_room_stats(self, room_id: str) -> Dict[str, Any]:
        """Get statistics for a specific room"""
        if room_id not in self.room_connections:
            return {"error": "Room not found"}

        connections = self.room_connections[room_id]
        users = set()

        for connection in connections:
            if connection in self.connection_info:
                username = self.connection_info[connection].get("username")
                if username:
                    users.add(username)

        return {
            "room_id": room_id,
            "connection_count": len(connections),
            "user_count": len(users),
            "users": list(users),
            "active_since": (
                min(
                    [
                        self.connection_info[conn]["connected_at"]
                        for conn in connections
                        if conn in self.connection_info
                    ]
                ).isoformat()
                if connections
                else None
            ),
        }

    # Utility Methods
    def _generate_connection_id(self, websocket: WebSocket) -> str:
        """Generate unique connection ID"""
        return str(uuid.uuid4())

    def _get_client_info(self, websocket: WebSocket) -> str:
        """Get client connection information for logging"""
        try:
            client = websocket.client
            if client and client.host and client.port:
                return f"{client.host}:{client.port}"
            else:
                return "Unknown-Client"
        except Exception:
            return "Unknown-Client"

    def _get_client_ip(self, websocket: WebSocket) -> str:
        """Extract client IP address"""
        try:
            client = websocket.client
            if client and client.host:
                return client.host
            return "unknown"
        except Exception:
            return "unknown"

    def update_activity(self, websocket: WebSocket):
        """Update last activity timestamp for a connection"""
        if websocket in self.connection_info:
            self.connection_info[websocket]["last_activity"] = datetime.now()

    async def cleanup_inactive_connections(self, max_inactive_seconds: int = 300):
        """Clean up connections that have been inactive for too long"""
        current_time = datetime.now()
        inactive_connections = []

        for websocket, info in self.connection_info.items():
            last_activity = info.get("last_activity")
            if last_activity:
                inactive_time = (current_time - last_activity).total_seconds()
                if inactive_time > max_inactive_seconds:
                    # store both connection and its inactive duration
                    inactive_connections.append((websocket, inactive_time))

        for connection, inactive_seconds in inactive_connections:
            username = self.connection_info.get(connection, {}).get("username", "unknown")
            enhanced_logger.warning(
                "Cleaning up inactive connection",
                username=username,
                client_info=self._get_client_info(connection),
                inactive_seconds=inactive_seconds,
            )
            self.disconnect(connection, reason="inactivity_timeout")

        if inactive_connections:
            enhanced_logger.info("Inactive connections cleaned up", count=len(inactive_connections))

    async def send_ping(self, websocket: WebSocket) -> bool:
        """Send ping to check connection health"""
        try:
            ping_id = str(uuid.uuid4())
            ping_message = {
                "type": "ping",
                "ping_id": ping_id,
                "timestamp": datetime.now().isoformat(),
            }

            await websocket.send_text(json.dumps(ping_message))

            if websocket in self.connection_info:
                self.connection_info[websocket]["ping_count"] += 1
                self.connection_info[websocket]["last_ping"] = datetime.now()

            enhanced_logger.debug("Ping sent", ping_id=ping_id)
            return True

        except Exception as e:
            enhanced_logger.debug("Ping failed", error=str(e))
            return False


# Global connection manager instance
manager = ConnectionManager()
