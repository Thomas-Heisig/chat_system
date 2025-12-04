"""
📋 Agent Registry

Central registry for managing all agents in the system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import logger

from .base_agent import AgentCapability, AgentStatus, BaseAgent


class AgentRegistry:
    """
    Central registry for agent management.

    Handles:
    - Agent registration and deregistration
    - Agent discovery by capability
    - Agent health monitoring
    - Agent lifecycle management
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.capability_index: Dict[AgentCapability, List[str]] = {}
        self.registration_time: Dict[str, datetime] = {}

        logger.info("📋 Agent Registry initialized")

    async def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register a new agent in the system.

        Args:
            agent: Agent instance to register

        Returns:
            True if registration successful
        """
        if agent.agent_id in self.agents:
            logger.warning(f"⚠️ Agent already registered: {agent.agent_id}")
            return False

        # Register agent
        self.agents[agent.agent_id] = agent
        self.registration_time[agent.agent_id] = datetime.now()

        # Index by capabilities
        for capability in agent.capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = []
            self.capability_index[capability].append(agent.agent_id)

        # Initialize agent
        await agent.initialize()

        logger.info(
            f"✅ Agent registered: {agent.name} ({agent.agent_id}) "
            f"with capabilities: {[c.value for c in agent.capabilities]}"
        )
        return True

    async def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the system.

        Args:
            agent_id: ID of agent to deregister

        Returns:
            True if deregistration successful
        """
        if agent_id not in self.agents:
            logger.warning(f"⚠️ Agent not found: {agent_id}")
            return False

        agent = self.agents[agent_id]

        # Shutdown agent
        await agent.shutdown()

        # Remove from capability index
        for capability in agent.capabilities:
            if capability in self.capability_index:
                if agent_id in self.capability_index[capability]:
                    self.capability_index[capability].remove(agent_id)

        # Remove agent
        del self.agents[agent_id]
        if agent_id in self.registration_time:
            del self.registration_time[agent_id]

        logger.info(f"🗑️ Agent deregistered: {agent.name} ({agent_id})")
        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_agents_by_capability(
        self, capability: AgentCapability, status: Optional[AgentStatus] = None
    ) -> List[BaseAgent]:
        """
        Get all agents with a specific capability.

        Args:
            capability: Required capability
            status: Optional filter by status

        Returns:
            List of agents with the capability
        """
        agent_ids = self.capability_index.get(capability, [])
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]

        if status:
            agents = [a for a in agents if a.status == status]

        return agents

    def get_available_agent(self, capability: AgentCapability) -> Optional[BaseAgent]:
        """
        Get an available agent with the specified capability.

        Args:
            capability: Required capability

        Returns:
            First available agent or None
        """
        agents = self.get_agents_by_capability(capability, AgentStatus.IDLE)
        return agents[0] if agents else None

    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self.agents.values())

    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return len(self.agents)

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        agent = self.get_agent(agent_id)
        return agent.get_info() if agent else None

    def get_all_agent_info(self) -> List[Dict[str, Any]]:
        """Get information for all agents"""
        return [agent.get_info() for agent in self.agents.values()]

    def get_agents_by_status(self, status: AgentStatus) -> List[BaseAgent]:
        """Get all agents with specific status"""
        return [a for a in self.agents.values() if a.status == status]

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all agents.

        Returns:
            Health status report
        """
        total_agents = len(self.agents)
        status_counts = {}

        for status in AgentStatus:
            count = len(self.get_agents_by_status(status))
            status_counts[status.value] = count

        capability_counts = {
            cap.value: len(agent_ids) for cap, agent_ids in self.capability_index.items()
        }

        return {
            "total_agents": total_agents,
            "status_distribution": status_counts,
            "capability_distribution": capability_counts,
            "healthy": status_counts.get(AgentStatus.ERROR.value, 0) == 0,
            "timestamp": datetime.now().isoformat(),
        }

    def find_agents_for_task(self, task: Dict[str, Any]) -> List[BaseAgent]:
        """
        Find suitable agents for a given task.

        Args:
            task: Task description

        Returns:
            List of agents that can handle the task
        """
        required_capability = task.get("required_capability")

        if not required_capability:
            return self.get_agents_by_status(AgentStatus.IDLE)

        try:
            capability = AgentCapability(required_capability)
            return self.get_agents_by_capability(capability, AgentStatus.IDLE)
        except ValueError:
            logger.error(f"❌ Invalid capability: {required_capability}")
            return []

    async def cleanup_inactive_agents(self, max_idle_hours: int = 24):
        """
        Clean up agents that have been inactive for too long.

        Args:
            max_idle_hours: Maximum idle time in hours
        """
        now = datetime.now()
        inactive_agents = []

        for agent in self.agents.values():
            idle_hours = (now - agent.last_active).total_seconds() / 3600
            if idle_hours > max_idle_hours and agent.status == AgentStatus.IDLE:
                inactive_agents.append(agent.agent_id)

        for agent_id in inactive_agents:
            await self.deregister_agent(agent_id)
            logger.info(f"🧹 Cleaned up inactive agent: {agent_id}")

        return len(inactive_agents)
