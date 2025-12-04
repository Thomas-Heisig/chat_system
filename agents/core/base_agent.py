"""
🤖 Base Agent Class

Provides the base interface and common functionality for all agents in the system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from config.settings import logger


class AgentStatus(Enum):
    """Agent operational status"""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class AgentCapability(Enum):
    """Agent capabilities"""

    DIALOG = "dialog"
    RETRIEVAL = "retrieval"
    TOOL_USE = "tool_use"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    PLANNING = "planning"


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    Each agent must implement the process() method to handle incoming tasks.
    Agents can have capabilities, maintain state, and communicate with other agents.
    """

    def __init__(
        self, agent_id: str, name: str, capabilities: List[AgentCapability], description: str = ""
    ):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.description = description
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.task_count = 0
        self.error_count = 0
        self.metadata: Dict[str, Any] = {}

        logger.info(f"🤖 Agent initialized: {self.name} ({self.agent_id})")

    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming task.

        Args:
            task: Task data containing type, parameters, and context

        Returns:
            Dict containing the result of task processing
        """

    async def can_handle(self, task: Dict[str, Any]) -> bool:
        """
        Check if this agent can handle the given task.

        Args:
            task: Task to evaluate

        Returns:
            True if agent can handle the task
        """
        required_capability = task.get("required_capability")
        if required_capability:
            return AgentCapability(required_capability) in self.capabilities
        return True

    def update_status(self, status: AgentStatus):
        """Update agent status"""
        self.status = status
        self.last_active = datetime.now()

    def increment_task_count(self):
        """Increment task counter"""
        self.task_count += 1
        self.last_active = datetime.now()

    def increment_error_count(self):
        """Increment error counter"""
        self.error_count += 1

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "task_count": self.task_count,
            "error_count": self.error_count,
            "metadata": self.metadata,
        }

    async def initialize(self):
        """Initialize agent resources"""
        logger.info(f"🔄 Initializing agent: {self.name}")

    async def shutdown(self):
        """Cleanup agent resources"""
        logger.info(f"🛑 Shutting down agent: {self.name}")
