"""
🔧 Tool Agent

Specialized agent for tool usage and external API integration.
"""

from typing import Dict, Any, List, Callable
import asyncio
import json

from ..core.base_agent import BaseAgent, AgentCapability
from config.settings import logger


class ToolAgent(BaseAgent):
    """
    Agent specialized in using tools and calling external APIs.
    
    Capabilities:
    - Tool registration and execution
    - API integration
    - Function calling
    - Result formatting
    """
    
    def __init__(self, agent_id: str = "tool_agent_001"):
        super().__init__(
            agent_id=agent_id,
            name="Tool Agent",
            capabilities=[
                AgentCapability.TOOL_USE,
                AgentCapability.ANALYSIS
            ],
            description="Executes tools and integrates with external APIs"
        )
        
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        # Calculator tool
        self.register_tool(
            name="calculator",
            function=self._calculator,
            description="Performs basic arithmetic operations",
            parameters={
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            }
        )
        
        # Weather tool (placeholder)
        self.register_tool(
            name="weather",
            function=self._get_weather,
            description="Gets weather information for a location",
            parameters={
                "location": {"type": "string"}
            }
        )
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Dict[str, Any]
    ):
        """Register a new tool"""
        self.tools[name] = function
        self.tool_metadata[name] = {
            "description": description,
            "parameters": parameters
        }
        logger.info(f"🔧 Tool registered: {name}")
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process tool execution tasks.
        
        Supported task types:
        - execute_tool: Execute a specific tool
        - list_tools: List available tools
        - get_tool_info: Get information about a tool
        """
        task_type = task.get("type", "unknown")
        
        try:
            if task_type == "execute_tool":
                return await self._execute_tool(task)
            elif task_type == "list_tools":
                return await self._list_tools(task)
            elif task_type == "get_tool_info":
                return await self._get_tool_info(task)
            else:
                return {
                    "error": f"Unknown task type: {task_type}",
                    "agent_id": self.agent_id
                }
        except Exception as e:
            logger.error(f"❌ Tool agent error: {e}")
            self.increment_error_count()
            return {
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _execute_tool(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        tool_name = task.get("tool_name")
        parameters = task.get("parameters", {})
        
        if tool_name not in self.tools:
            return {
                "error": f"Tool not found: {tool_name}",
                "agent_id": self.agent_id
            }
        
        try:
            tool_function = self.tools[tool_name]
            result = await tool_function(**parameters) if asyncio.iscoroutinefunction(tool_function) else tool_function(**parameters)
            
            self.increment_task_count()
            
            return {
                "tool_name": tool_name,
                "result": result,
                "success": True,
                "agent_id": self.agent_id
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "error": str(e),
                "success": False,
                "agent_id": self.agent_id
            }
    
    async def _list_tools(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """List all available tools"""
        tools_list = [
            {
                "name": name,
                **metadata
            }
            for name, metadata in self.tool_metadata.items()
        ]
        
        return {
            "tools": tools_list,
            "count": len(tools_list),
            "agent_id": self.agent_id
        }
    
    async def _get_tool_info(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a specific tool"""
        tool_name = task.get("tool_name")
        
        if tool_name not in self.tool_metadata:
            return {
                "error": f"Tool not found: {tool_name}",
                "agent_id": self.agent_id
            }
        
        return {
            "name": tool_name,
            **self.tool_metadata[tool_name],
            "agent_id": self.agent_id
        }
    
    # Tool implementations
    def _calculator(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        """Basic calculator tool"""
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else "Error: Division by zero"
        }
        
        result = operations.get(operation, "Invalid operation")
        
        return {
            "operation": operation,
            "operands": [a, b],
            "result": result
        }
    
    def _get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information (placeholder)"""
        # TODO: Integrate with actual weather API
        return {
            "location": location,
            "temperature": 22,
            "condition": "Partly Cloudy",
            "humidity": 65,
            "note": "This is placeholder data"
        }
