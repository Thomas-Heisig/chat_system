from fastapi import WebSocket, WebSocketDisconnect
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from database.models import WebSocketMessage, Message, MessageType, User, ChatMessageData
from services.message_service import MessageService
from services.project_service import ProjectService
from services.file_service import FileService
from websocket.manager import manager, ConnectionState, ConnectionType
from config.settings import logger, enhanced_logger

class WebSocketHandler:
    """
    Enhanced WebSocket Handler with comprehensive features:
    - Multi-protocol message handling
    - Room/channel management
    - User authentication and session management
    - AI integration
    - File upload support
    - Project and ticket integration
    - Advanced error handling and recovery
    """
    
    def __init__(self, message_service: MessageService, project_service: ProjectService = None, file_service: FileService = None):
        self.message_service = message_service
        self.project_service = project_service
        self.file_service = file_service
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Message type handlers registry
        self.message_handlers = {
            "chat_message": self._handle_chat_message,
            "user_typing": self._handle_typing_indicator,
            "user_join": self._handle_user_join,
            "user_leave": self._handle_user_leave,
            "room_join": self._handle_room_join,
            "room_leave": self._handle_room_leave,
            "ai_request": self._handle_ai_request,
            "file_upload_request": self._handle_file_upload_request,
            "project_update": self._handle_project_update,
            "ticket_update": self._handle_ticket_update,
            "ping": self._handle_ping,
            "authentication": self._handle_authentication
        }
        
        enhanced_logger.info(
            "WebSocketHandler initialized",
            features=[
                "multi_protocol_messages",
                "room_management", 
                "ai_integration",
                "file_upload",
                "project_management",
                "user_authentication"
            ]
        )

    async def handle_websocket(self, websocket: WebSocket, user_agent: str = None):
        """Handle complete WebSocket connection lifecycle with enhanced features"""
        start_time = datetime.now()
        connection_id = None
        
        try:
            # Accept connection with enhanced metadata
            connection_id = await manager.connect(websocket, user_agent)
            client_info = manager._get_client_info(websocket)
            
            # Initialize client session
            self.client_sessions[connection_id] = {
                'websocket': websocket,
                'connected_at': start_time,
                'message_count': 0,
                'username': None,
                'user_id': None,
                'client_info': client_info,
                'user_agent': user_agent,
                'rooms': set(),
                'last_activity': start_time,
                'authenticated': False,
                'connection_type': 'guest'
            }
            
            connection_duration = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.info(
                "WebSocket connection established",
                connection_id=connection_id,
                client_info=client_info,
                user_agent=user_agent,
                connection_duration_ms=connection_duration
            )
            
            # Send welcome package
            await self._send_welcome_package(websocket, connection_id)
            
            # Send recent messages and system status
            await self._send_initial_data(websocket, connection_id)
            
            # Handle incoming messages
            await self._handle_message_loop(websocket, connection_id)
            
        except WebSocketDisconnect:
            enhanced_logger.info(
                "WebSocket disconnected normally",
                connection_id=connection_id,
                client_info=manager._get_client_info(websocket) if websocket else "unknown"
            )
            await self._handle_disconnect(websocket, connection_id)
            
        except Exception as e:
            connection_duration = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_logger.error(
                "WebSocket connection error",
                connection_id=connection_id,
                error=str(e),
                error_type=type(e).__name__,
                connection_duration_ms=connection_duration
            )
            await self._handle_disconnect(websocket, connection_id)

    async def _handle_message_loop(self, websocket: WebSocket, connection_id: str):
        """Enhanced message handling loop with heartbeat and timeout detection"""
        client_session = self.client_sessions.get(connection_id, {})
        client_info = client_session.get('client_info', 'Unknown client')
        
        # Heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_monitor(websocket, connection_id))
        
        try:
            while True:
                try:
                    # Receive message with timeout
                    data = await asyncio.wait_for(
                        websocket.receive_text(), 
                        timeout=300  # 5 minutes timeout
                    )
                    
                    # Update activity timestamp
                    self._update_activity(connection_id)
                    
                    # Process message
                    await self._process_message(data, websocket, connection_id)
                    
                except asyncio.TimeoutError:
                    enhanced_logger.warning(
                        "WebSocket receive timeout",
                        connection_id=connection_id,
                        client_info=client_info
                    )
                    # Send ping to check if connection is still alive
                    if not await manager.send_ping(websocket):
                        raise WebSocketDisconnect()
                    continue
                    
                except WebSocketDisconnect:
                    enhanced_logger.info(
                        "WebSocket disconnected in message loop",
                        connection_id=connection_id,
                        client_info=client_info
                    )
                    raise
                    
                except Exception as e:
                    enhanced_logger.error(
                        "Error in message loop",
                        connection_id=connection_id,
                        client_info=client_info,
                        error=str(e)
                    )
                    await self._send_error(websocket, f"Message processing error: {str(e)}")
                    continue
                    
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _process_message(self, data: str, websocket: WebSocket, connection_id: str):
        """Process individual WebSocket message with enhanced validation and routing"""
        client_session = self.client_sessions.get(connection_id, {})
        client_info = client_session.get('client_info', 'Unknown client')
        
        try:
            enhanced_logger.debug(
                "Received WebSocket message",
                connection_id=connection_id,
                client_info=client_info,
                message_preview=data[:100]
            )
            
            # Parse and validate message
            message_data = WebSocketMessage(**json.loads(data))
            client_session['message_count'] += 1
            
            enhanced_logger.info(
                "Processing WebSocket message",
                connection_id=connection_id,
                message_type=message_data.type,
                client_info=client_info,
                message_count=client_session['message_count']
            )
            
            # Route to appropriate handler
            handler = self.message_handlers.get(message_data.type)
            if handler:
                await handler(message_data, connection_id)
            else:
                enhanced_logger.warning(
                    "Unknown message type",
                    connection_id=connection_id,
                    message_type=message_data.type
                )
                await self._send_error(websocket, f"Unknown message type: {message_data.type}")
                
        except json.JSONDecodeError as e:
            enhanced_logger.error(
                "JSON decode error",
                connection_id=connection_id,
                client_info=client_info,
                error=str(e)
            )
            await self._send_error(websocket, "Invalid JSON format")
            
        except Exception as e:
            enhanced_logger.error(
                "Message processing error",
                connection_id=connection_id,
                client_info=client_info,
                error=str(e),
                message_data=data[:200] if data else "empty"
            )
            await self._send_error(websocket, f"Error processing message: {str(e)}")

    async def _handle_chat_message(self, message_data: WebSocketMessage, connection_id: str):
        """Enhanced chat message handler with project and room support"""
        client_session = self.client_sessions[connection_id]
        websocket = client_session['websocket']
        client_info = client_session['client_info']
        
        # Validation
        validation_error = await self._validate_chat_message(message_data, connection_id)
        if validation_error:
            await self._send_error(websocket, validation_error)
            return
        
        try:
            # Update user session
            if message_data.username and message_data.username != client_session.get('username'):
                await self._update_user_session(connection_id, message_data.username)
            
            # Create message object with enhanced metadata
            message_obj = Message(
                username=message_data.username,
                message=message_data.message,
                message_type=MessageType.USER,
                room_id=message_data.data.get('room_id') if message_data.data else None,
                project_id=message_data.data.get('project_id') if message_data.data else None,
                ticket_id=message_data.data.get('ticket_id') if message_data.data else None,
                metadata={
                    'connection_id': connection_id,
                    'client_info': client_info,
                    'user_agent': client_session.get('user_agent'),
                    'message_type': 'chat'
                }
            )
            
            # Save message to database
            enhanced_logger.debug(
                "Saving chat message",
                connection_id=connection_id,
                username=message_data.username
            )
            
            saved_message = self.message_service.save_message(message_obj)
            
            # Prepare broadcast data
            broadcast_data = {
                "type": "chat_message",
                "username": saved_message.username,
                "message": saved_message.message,
                "timestamp": saved_message.timestamp.isoformat() if saved_message.timestamp else None,
                "message_id": saved_message.id,
                "room_id": saved_message.room_id,
                "project_id": saved_message.project_id,
                "ticket_id": saved_message.ticket_id,
                "metadata": {
                    "connection_id": connection_id,
                    "delivery_status": "sent"
                }
            }
            
            # Broadcast to appropriate audience
            if saved_message.room_id:
                # Broadcast to room
                await manager.broadcast(
                    broadcast_data, 
                    room_id=saved_message.room_id,
                    message_type="room_chat"
                )
                enhanced_logger.info(
                    "Room chat message broadcast",
                    room_id=saved_message.room_id,
                    username=saved_message.username,
                    message_id=saved_message.id
                )
            else:
                # Broadcast to all connected clients
                await manager.broadcast(broadcast_data, message_type="global_chat")
                enhanced_logger.info(
                    "Global chat message broadcast",
                    username=saved_message.username,
                    message_id=saved_message.id
                )
            
            # Handle AI auto-response if enabled
            if (self.message_service.ollama_available and 
                message_data.data and 
                message_data.data.get('ai_auto_respond', False)):
                asyncio.create_task(
                    self._handle_ai_auto_response(saved_message, connection_id)
                )
            
            enhanced_logger.info(
                "Chat message processed successfully",
                connection_id=connection_id,
                username=message_data.username,
                message_id=saved_message.id,
                room_id=saved_message.room_id
            )
            
        except Exception as e:
            enhanced_logger.error(
                "Failed to process chat message",
                connection_id=connection_id,
                username=message_data.username,
                error=str(e)
            )
            await self._send_error(websocket, "Failed to process chat message")

    async def _handle_ai_request(self, message_data: WebSocketMessage, connection_id: str):
        """Handle AI conversation requests"""
        client_session = self.client_sessions[connection_id]
        websocket = client_session['websocket']
        
        if not message_data.message:
            await self._send_error(websocket, "AI request requires a message")
            return
        
        try:
            enhanced_logger.info(
                "Processing AI request",
                connection_id=connection_id,
                username=client_session.get('username'),
                message_preview=message_data.message[:50]
            )
            
            # Get context messages if available
            context_messages = []
            if message_data.data and message_data.data.get('use_context', True):
                context_messages = self.message_service.get_recent_messages(10)
            
            # Generate AI response
            ai_response = self.message_service.generate_ai_response(
                message=message_data.message,
                context_messages=context_messages,
                model_type=message_data.data.get('model_type', 'ollama') if message_data.data else 'ollama',
                model_name=message_data.data.get('model_name', 'llama2') if message_data.data else 'llama2'
            )
            
            # Save AI response as message
            ai_message = Message(
                username="AI Assistant",
                message=ai_response,
                message_type=MessageType.AI,
                is_ai_response=True,
                ai_model_used=message_data.data.get('model_type', 'ollama') if message_data.data else 'ollama',
                room_id=message_data.data.get('room_id') if message_data.data else None,
                project_id=message_data.data.get('project_id') if message_data.data else None,
                metadata={
                    'ai_request': message_data.message,
                    'context_messages': len(context_messages),
                    'connection_id': connection_id
                }
            )
            
            saved_ai_message = self.message_service.save_message(ai_message)
            
            # Send AI response to requesting client
            response_data = {
                "type": "ai_response",
                "username": "AI Assistant",
                "message": ai_response,
                "timestamp": saved_ai_message.timestamp.isoformat() if saved_ai_message.timestamp else None,
                "message_id": saved_ai_message.id,
                "metadata": {
                    "model_used": ai_message.ai_model_used,
                    "context_used": len(context_messages),
                    "response_time": "instant"  # Would be calculated in real implementation
                }
            }
            
            await manager.send_personal_message(response_data, websocket)
            
            enhanced_logger.info(
                "AI response sent",
                connection_id=connection_id,
                message_id=saved_ai_message.id,
                model_used=ai_message.ai_model_used
            )
            
        except Exception as e:
            enhanced_logger.error(
                "AI request failed",
                connection_id=connection_id,
                error=str(e)
            )
            await self._send_error(websocket, f"AI request failed: {str(e)}")

    async def _handle_room_join(self, message_data: WebSocketMessage, connection_id: str):
        """Handle room join requests"""
        client_session = self.client_sessions[connection_id]
        websocket = client_session['websocket']
        
        if not message_data.data or not message_data.data.get('room_id'):
            await self._send_error(websocket, "Room join requires room_id")
            return
        
        room_id = message_data.data['room_id']
        
        try:
            # Join room
            success = await manager.join_room(websocket, room_id)
            
            if success:
                client_session['rooms'].add(room_id)
                
                # Send confirmation
                await manager.send_personal_message({
                    "type": "room_joined",
                    "room_id": room_id,
                    "timestamp": datetime.now().isoformat(),
                    "room_members": len(manager.room_connections.get(room_id, set()))
                }, websocket)
                
                # Broadcast room join notification
                if client_session.get('username'):
                    await manager.broadcast({
                        "type": "user_joined_room",
                        "username": client_session['username'],
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat()
                    }, room_id=room_id)
                
                enhanced_logger.info(
                    "User joined room",
                    connection_id=connection_id,
                    username=client_session.get('username'),
                    room_id=room_id
                )
            else:
                await self._send_error(websocket, f"Failed to join room: {room_id}")
                
        except Exception as e:
            enhanced_logger.error(
                "Room join failed",
                connection_id=connection_id,
                room_id=room_id,
                error=str(e)
            )
            await self._send_error(websocket, f"Room join failed: {str(e)}")

    async def _handle_authentication(self, message_data: WebSocketMessage, connection_id: str):
        """Handle user authentication"""
        client_session = self.client_sessions[connection_id]
        websocket = client_session['websocket']
        
        if not message_data.data or not message_data.data.get('username'):
            await self._send_error(websocket, "Authentication requires username")
            return
        
        try:
            username = message_data.data['username']
            user_id = message_data.data.get('user_id')
            
            # Authenticate user with manager
            success = manager.authenticate_user(websocket, username, user_id)
            
            if success:
                client_session.update({
                    'username': username,
                    'user_id': user_id,
                    'authenticated': True,
                    'connection_type': 'authenticated_user'
                })
                
                # Send authentication success
                await manager.send_personal_message({
                    "type": "authentication_success",
                    "username": username,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
                # Broadcast user online status
                await manager.broadcast({
                    "type": "user_online",
                    "username": username,
                    "timestamp": datetime.now().isoformat()
                })
                
                enhanced_logger.info(
                    "User authenticated successfully",
                    connection_id=connection_id,
                    username=username,
                    user_id=user_id
                )
            else:
                await self._send_error(websocket, "Authentication failed")
                
        except Exception as e:
            enhanced_logger.error(
                "Authentication failed",
                connection_id=connection_id,
                error=str(e)
            )
            await self._send_error(websocket, f"Authentication error: {str(e)}")

    # Additional handler methods
    async def _handle_typing_indicator(self, message_data: WebSocketMessage, connection_id: str):
        """Handle typing indicators with room support"""
        client_session = self.client_sessions[connection_id]
        
        if client_session.get('username'):
            typing_data = {
                "type": "user_typing",
                "username": client_session['username'],
                "timestamp": datetime.now().isoformat(),
                "room_id": message_data.data.get('room_id') if message_data.data else None
            }
            
            room_id = message_data.data.get('room_id') if message_data.data else None
            await manager.broadcast(typing_data, room_id=room_id, message_type="typing_indicator")
            
            enhanced_logger.debug(
                "Typing indicator sent",
                username=client_session['username'],
                room_id=room_id
            )

    async def _handle_user_join(self, message_data: WebSocketMessage, connection_id: str):
        """Handle user join notifications"""
        client_session = self.client_sessions[connection_id]
        
        if message_data.username:
            client_session['username'] = message_data.username
            enhanced_logger.info(
                "User join notification",
                connection_id=connection_id,
                username=message_data.username
            )

    async def _handle_user_leave(self, message_data: WebSocketMessage, connection_id: str):
        """Handle user leave notifications"""
        client_session = self.client_sessions[connection_id]
        username = client_session.get('username')
        
        if username:
            await manager.broadcast({
                "type": "user_left",
                "username": username,
                "timestamp": datetime.now().isoformat()
            })
            
            enhanced_logger.info(
                "User leave notification",
                connection_id=connection_id,
                username=username
            )

    async def _handle_room_leave(self, message_data: WebSocketMessage, connection_id: str):
        """Handle room leave requests"""
        client_session = self.client_sessions[connection_id]
        websocket = client_session['websocket']
        
        if not message_data.data or not message_data.data.get('room_id'):
            await self._send_error(websocket, "Room leave requires room_id")
            return
        
        room_id = message_data.data['room_id']
        
        try:
            success = await manager.leave_room(websocket, room_id)
            
            if success:
                client_session['rooms'].discard(room_id)
                
                await manager.send_personal_message({
                    "type": "room_left",
                    "room_id": room_id,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
                enhanced_logger.info(
                    "User left room",
                    connection_id=connection_id,
                    username=client_session.get('username'),
                    room_id=room_id
                )
            else:
                await self._send_error(websocket, f"Failed to leave room: {room_id}")
                
        except Exception as e:
            enhanced_logger.error(
                "Room leave failed",
                connection_id=connection_id,
                room_id=room_id,
                error=str(e)
            )
            await self._send_error(websocket, f"Room leave failed: {str(e)}")

    async def _handle_file_upload_request(self, message_data: WebSocketMessage, connection_id: str):
        """Handle file upload requests"""
        # Implementation would handle file upload metadata and initiate upload process
        client_session = self.client_sessions[connection_id]
        enhanced_logger.info(
            "File upload request received",
            connection_id=connection_id,
            username=client_session.get('username')
        )
        
        # Send upload authorization
        await manager.send_personal_message({
            "type": "file_upload_auth",
            "upload_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "max_file_size": 10 * 1024 * 1024  # 10MB
        }, client_session['websocket'])

    async def _handle_project_update(self, message_data: WebSocketMessage, connection_id: str):
        """Handle project-related updates"""
        client_session = self.client_sessions[connection_id]
        enhanced_logger.info(
            "Project update received",
            connection_id=connection_id,
            username=client_session.get('username'),
            project_id=message_data.data.get('project_id') if message_data.data else None
        )

    async def _handle_ticket_update(self, message_data: WebSocketMessage, connection_id: str):
        """Handle ticket-related updates"""
        client_session = self.client_sessions[connection_id]
        enhanced_logger.info(
            "Ticket update received",
            connection_id=connection_id,
            username=client_session.get('username'),
            ticket_id=message_data.data.get('ticket_id') if message_data.data else None
        )

    async def _handle_ping(self, message_data: WebSocketMessage, connection_id: str):
        """Handle ping messages"""
        client_session = self.client_sessions[connection_id]
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
            "server_time": datetime.now().isoformat()
        }, client_session['websocket'])

    # Utility methods
    async def _validate_chat_message(self, message_data: WebSocketMessage, connection_id: str) -> Optional[str]:
        """Validate chat message parameters"""
        if not message_data.username or not message_data.message:
            return "Username and message are required"
        
        if len(message_data.username) > 50:
            return "Username too long (max 50 characters)"
        
        if len(message_data.message) > 4000:
            return "Message too long (max 4000 characters)"
        
        # Check if user is authenticated if required
        client_session = self.client_sessions[connection_id]
        if not client_session.get('authenticated') and message_data.data and message_data.data.get('requires_auth'):
            return "Authentication required for this action"
        
        return None

    async def _update_user_session(self, connection_id: str, username: str):
        """Update user session information"""
        client_session = self.client_sessions[connection_id]
        old_username = client_session.get('username')
        client_session['username'] = username
        
        enhanced_logger.info(
            "User session updated",
            connection_id=connection_id,
            old_username=old_username,
            new_username=username
        )

    async def _handle_ai_auto_response(self, user_message: Message, connection_id: str):
        """Handle AI auto-response to user messages"""
        try:
            # Get context for AI response
            context_messages = self.message_service.get_recent_messages(5)
            
            # Generate AI response
            ai_response = self.message_service.generate_ai_response(
                message=user_message.message,
                context_messages=context_messages
            )
            
            # Save and broadcast AI response
            ai_message = Message(
                username="AI Assistant",
                message=ai_response,
                message_type=MessageType.AI,
                is_ai_response=True,
                room_id=user_message.room_id,
                project_id=user_message.project_id
            )
            
            saved_ai_message = self.message_service.save_message(ai_message)
            
            # Broadcast AI response
            broadcast_data = {
                "type": "chat_message",
                "username": "AI Assistant",
                "message": ai_response,
                "timestamp": saved_ai_message.timestamp.isoformat() if saved_ai_message.timestamp else None,
                "is_ai_response": True,
                "message_id": saved_ai_message.id,
                "room_id": user_message.room_id
            }
            
            if user_message.room_id:
                await manager.broadcast(broadcast_data, room_id=user_message.room_id)
            else:
                await manager.broadcast(broadcast_data)
            
            enhanced_logger.info(
                "AI auto-response sent",
                connection_id=connection_id,
                original_message_id=user_message.id,
                ai_message_id=saved_ai_message.id
            )
            
        except Exception as e:
            enhanced_logger.error(
                "AI auto-response failed",
                connection_id=connection_id,
                error=str(e)
            )

    async def _send_welcome_package(self, websocket: WebSocket, connection_id: str):
        """Send comprehensive welcome package to new client"""
        welcome_data = {
            "type": "welcome",
            "message": "Welcome to the Enhanced Chat System!",
            "timestamp": datetime.now().isoformat(),
            "connection_id": connection_id,
            "server_info": {
                "name": "Chat System",
                "version": "2.0.0",
                "features": [
                    "real_time_chat",
                    "ai_assistant", 
                    "room_management",
                    "file_sharing",
                    "project_integration"
                ]
            },
            "system_status": {
                "active_connections": manager.get_connected_count(),
                "active_rooms": len(manager.message_stats['active_rooms']),
                "ai_available": self.message_service.ollama_available
            }
        }
        
        await manager.send_personal_message(welcome_data, websocket)

    async def _send_initial_data(self, websocket: WebSocket, connection_id: str):
        """Send initial data including recent messages and system status"""
        try:
            # Send recent messages
            recent_messages = self.message_service.get_recent_messages(limit=50)
            for msg in recent_messages:
                await manager.send_personal_message({
                    "type": "chat_message",
                    "username": msg.username,
                    "message": msg.message,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "message_id": msg.id,
                    "is_ai_response": msg.is_ai_response,
                    "room_id": msg.room_id
                }, websocket)
            
            enhanced_logger.debug(
                "Initial data sent",
                connection_id=connection_id,
                recent_messages_count=len(recent_messages)
            )
            
        except Exception as e:
            enhanced_logger.error(
                "Failed to send initial data",
                connection_id=connection_id,
                error=str(e)
            )

    async def _handle_disconnect(self, websocket: WebSocket, connection_id: str):
        """Handle client disconnection with comprehensive cleanup"""
        client_session = self.client_sessions.get(connection_id, {})
        username = client_session.get('username')
        client_info = client_session.get('client_info', 'Unknown client')
        
        try:
            # Leave all rooms
            for room_id in client_session.get('rooms', set()):
                await manager.leave_room(websocket, room_id)
            
            # Broadcast user offline status
            if username:
                await manager.broadcast({
                    "type": "user_offline",
                    "username": username,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Remove from sessions
            if connection_id in self.client_sessions:
                del self.client_sessions[connection_id]
            
            # Disconnect from manager
            manager.disconnect(websocket, reason="client_disconnect")
            
            enhanced_logger.info(
                "Client disconnected",
                connection_id=connection_id,
                username=username,
                client_info=client_info,
                remaining_connections=len(self.client_sessions)
            )
            
        except Exception as e:
            enhanced_logger.error(
                "Error during disconnect cleanup",
                connection_id=connection_id,
                error=str(e)
            )

    async def _send_error(self, websocket: WebSocket, error_message: str, error_code: str = None):
        """Send structured error message to client"""
        try:
            error_data = {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
                "error_code": error_code
            }
            await manager.send_personal_message(error_data, websocket)
            
            enhanced_logger.debug(
                "Error message sent to client",
                error_message=error_message,
                error_code=error_code
            )
            
        except Exception as e:
            enhanced_logger.error(
                "Failed to send error message",
                error=str(e)
            )

    async def _heartbeat_monitor(self, websocket: WebSocket, connection_id: str):
        """Monitor connection health with heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if connection_id not in self.client_sessions:
                    break
                    
                client_session = self.client_sessions[connection_id]
                last_activity = client_session.get('last_activity')
                
                if last_activity and (datetime.now() - last_activity).total_seconds() > 60:
                    # Send ping to check connection
                    if not await manager.send_ping(websocket):
                        enhanced_logger.warning(
                            "Heartbeat failed - disconnecting",
                            connection_id=connection_id
                        )
                        await self._handle_disconnect(websocket, connection_id)
                        break
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                enhanced_logger.error(
                    "Heartbeat monitor error",
                    connection_id=connection_id,
                    error=str(e)
                )

    def _update_activity(self, connection_id: str):
        """Update last activity timestamp"""
        if connection_id in self.client_sessions:
            self.client_sessions[connection_id]['last_activity'] = datetime.now()
            manager.update_activity(self.client_sessions[connection_id]['websocket'])

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        stats = {
            "total_connections": len(self.client_sessions),
            "active_connections": manager.get_connected_count(),
            "authenticated_users": len([s for s in self.client_sessions.values() if s.get('authenticated')]),
            "clients": [],
            "manager_stats": manager.get_connection_stats()
        }
        
        for connection_id, session in self.client_sessions.items():
            stats["clients"].append({
                "connection_id": connection_id,
                "username": session.get('username'),
                "user_id": session.get('user_id'),
                "message_count": session.get('message_count', 0),
                "connected_at": session.get('connected_at').isoformat(),
                "last_activity": session.get('last_activity').isoformat(),
                "authenticated": session.get('authenticated', False),
                "rooms": list(session.get('rooms', set())),
                "client_info": session.get('client_info'),
                "user_agent": session.get('user_agent')
            })
        
        return stats