"""
📨 Agent Messaging System

Handles inter-agent communication through a message bus.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from config.settings import logger


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"


class AgentMessage:
    """
    Message passed between agents in the system.
    """
    
    def __init__(
        self,
        sender_id: str,
        recipient_id: Optional[str],
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None
    ):
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.payload = payload
        self.priority = priority
        self.correlation_id = correlation_id or self.message_id
        self.timestamp = datetime.now()
        self.processed = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed
        }


class MessageBus:
    """
    Central message bus for agent communication.
    
    Supports:
    - Point-to-point messaging
    - Broadcast messaging
    - Message queuing with priorities
    - Subscription-based event handling
    """
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history = 1000
        
        logger.info("📨 Message Bus initialized")
    
    async def send_message(self, message: AgentMessage):
        """
        Send a message to a specific agent or broadcast.
        
        Args:
            message: Message to send
        """
        # Store in history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        # Handle broadcast messages
        if message.message_type == MessageType.BROADCAST:
            await self._broadcast(message)
            return
        
        # Send to specific recipient
        if message.recipient_id:
            if message.recipient_id not in self.queues:
                self.queues[message.recipient_id] = asyncio.Queue()
            
            await self.queues[message.recipient_id].put(message)
            logger.debug(
                f"📨 Message sent: {message.sender_id} -> {message.recipient_id} "
                f"(type: {message.message_type.value})"
            )
    
    async def _broadcast(self, message: AgentMessage):
        """Broadcast message to all subscribers"""
        event_type = message.payload.get("event_type", "default")
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"❌ Error in subscriber callback: {e}")
        
        logger.debug(f"📢 Broadcast sent: {event_type}")
    
    async def receive_message(
        self,
        agent_id: str,
        timeout: Optional[float] = None
    ) -> Optional[AgentMessage]:
        """
        Receive a message for a specific agent.
        
        Args:
            agent_id: Agent ID to receive messages for
            timeout: Optional timeout in seconds
            
        Returns:
            AgentMessage or None if timeout
        """
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self.queues[agent_id].get()
            
            message.processed = True
            return message
        except asyncio.TimeoutError:
            return None
    
    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe to broadcast events.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async callback function
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.info(f"📫 Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events"""
        if event_type in self.subscribers:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
    
    def get_queue_size(self, agent_id: str) -> int:
        """Get size of agent's message queue"""
        if agent_id in self.queues:
            return self.queues[agent_id].qsize()
        return 0
    
    def get_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get message history.
        
        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        messages = self.message_history
        
        if agent_id:
            messages = [
                m for m in messages
                if m.sender_id == agent_id or m.recipient_id == agent_id
            ]
        
        return [m.to_dict() for m in messages[-limit:]]
    
    def clear_queue(self, agent_id: str):
        """Clear an agent's message queue"""
        if agent_id in self.queues:
            while not self.queues[agent_id].empty():
                try:
                    self.queues[agent_id].get_nowait()
                except asyncio.QueueEmpty:
                    break
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            "total_agents": len(self.queues),
            "total_subscribers": len(self.subscribers),
            "message_history_size": len(self.message_history),
            "queue_sizes": {
                agent_id: queue.qsize()
                for agent_id, queue in self.queues.items()
            }
        }
