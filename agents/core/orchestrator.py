"""
🎭 Agent Orchestrator

Coordinates agent activities and task distribution.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import logger

from .base_agent import AgentStatus
from .messaging import AgentMessage, MessageBus, MessageType
from .registry import AgentRegistry


class TaskStatus:
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentOrchestrator:
    """
    Central orchestrator for the multi-agent system.

    Responsibilities:
    - Task distribution to appropriate agents
    - Agent coordination for complex tasks
    - Workflow execution
    - Load balancing
    - Failure handling and retries
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.max_history = 1000

        logger.info("🎭 Agent Orchestrator initialized")

    async def execute_task(
        self, task: Dict[str, Any], timeout: Optional[float] = 30.0, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a task by assigning it to an appropriate agent.

        Args:
            task: Task description with type and parameters
            timeout: Task timeout in seconds (must be positive)
            retry_count: Number of retries on failure

        Returns:
            Task result
        """
        # Validate timeout
        if timeout is not None and timeout <= 0:
            raise ValueError("Timeout must be a positive number")

        task_id = task.get("task_id", f"task_{datetime.now().timestamp()}")
        task["task_id"] = task_id

        logger.info(f"📋 Executing task: {task_id} (type: {task.get('type', 'unknown')})")

        # Track task
        self.active_tasks[task_id] = {
            "task": task,
            "status": TaskStatus.PENDING,
            "start_time": datetime.now(),
            "retry_count": retry_count,
        }

        try:
            # Find suitable agent
            agents = self.registry.find_agents_for_task(task)

            if not agents:
                logger.warning(f"⚠️ No available agents for task: {task_id}")
                return await self._handle_no_agent(task_id, task, retry_count)

            # Select best agent (currently just first available)
            agent = agents[0]

            # Assign task
            self.active_tasks[task_id]["status"] = TaskStatus.ASSIGNED
            self.active_tasks[task_id]["agent_id"] = agent.agent_id

            # Execute task
            agent.update_status(AgentStatus.BUSY)
            self.active_tasks[task_id]["status"] = TaskStatus.IN_PROGRESS

            try:
                result = await asyncio.wait_for(agent.process(task), timeout=timeout)

                # Task completed successfully
                agent.update_status(AgentStatus.IDLE)
                agent.increment_task_count()

                self.active_tasks[task_id]["status"] = TaskStatus.COMPLETED
                self.active_tasks[task_id]["result"] = result
                self.active_tasks[task_id]["end_time"] = datetime.now()

                # Move to history
                self._move_to_history(task_id)

                logger.info(f"✅ Task completed: {task_id}")
                return result

            except asyncio.TimeoutError:
                logger.error(f"⏱️ Task timeout: {task_id}")
                agent.update_status(AgentStatus.IDLE)
                agent.increment_error_count()

                self.active_tasks[task_id]["status"] = TaskStatus.TIMEOUT

                if retry_count > 0:
                    return await self.execute_task(task, timeout, retry_count - 1)

                return {"error": "Task timeout", "task_id": task_id}

        except Exception as e:
            logger.error(f"❌ Task execution failed: {task_id} - {e}")

            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = TaskStatus.FAILED
                self.active_tasks[task_id]["error"] = str(e)

            if retry_count > 0:
                return await self.execute_task(task, timeout, retry_count - 1)

            return {"error": str(e), "task_id": task_id}

    async def _handle_no_agent(
        self, task_id: str, task: Dict[str, Any], retry_count: int
    ) -> Dict[str, Any]:
        """Handle case when no agent is available"""
        if retry_count > 0:
            # Wait and retry
            await asyncio.sleep(1)
            return await self.execute_task(task, retry_count=retry_count - 1)

        self.active_tasks[task_id]["status"] = TaskStatus.FAILED
        return {"error": "No available agents", "task_id": task_id}

    def _move_to_history(self, task_id: str):
        """Move completed task to history"""
        if task_id in self.active_tasks:
            self.task_history.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]

            # Limit history size
            if len(self.task_history) > self.max_history:
                self.task_history.pop(0)

    async def execute_workflow(
        self, workflow: List[Dict[str, Any]], sequential: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a workflow consisting of multiple tasks.

        Args:
            workflow: List of tasks to execute
            sequential: Execute tasks sequentially (True) or in parallel (False)

        Returns:
            List of task results
        """
        logger.info(f"🔄 Executing workflow with {len(workflow)} tasks (sequential={sequential})")

        if sequential:
            results = []
            for task in workflow:
                result = await self.execute_task(task)
                results.append(result)

                # Stop on error if configured
                if result.get("error") and task.get("stop_on_error", False):
                    break
            return results
        else:
            # Execute tasks in parallel
            tasks = [self.execute_task(task) for task in workflow]
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_event(
        self, event_type: str, event_data: Dict[str, Any], sender_id: str = "orchestrator"
    ):
        """
        Broadcast an event to all subscribed agents.

        Args:
            event_type: Type of event
            event_data: Event data
            sender_id: ID of sender
        """
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=None,
            message_type=MessageType.BROADCAST,
            payload={"event_type": event_type, "event_data": event_data},
        )

        await self.message_bus.send_message(message)
        logger.info(f"📢 Event broadcast: {event_type}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]

        # Search history
        for task in reversed(self.task_history):
            if task["task"]["task_id"] == task_id:
                return task

        return None

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks"""
        return list(self.active_tasks.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        total_tasks = len(self.task_history) + len(self.active_tasks)

        status_counts = {}
        for task in self.task_history:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_tasks": total_tasks,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_history),
            "status_distribution": status_counts,
            "agent_registry": self.registry.health_check(),
            "message_bus": self.message_bus.get_statistics(),
        }

    async def shutdown(self):
        """Shutdown orchestrator and all agents"""
        logger.info("🛑 Shutting down orchestrator")

        # Deregister all agents
        agent_ids = list(self.registry.agents.keys())
        for agent_id in agent_ids:
            await self.registry.deregister_agent(agent_id)

        logger.info("✅ Orchestrator shutdown complete")


# Singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
