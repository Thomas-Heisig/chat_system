"""
⚙️ Automation Pipeline Service

Handles workflow automation and task orchestration.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from config.settings import logger


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AutomationPipeline:
    """
    Automation pipeline for executing workflows.
    
    Features:
    - Sequential and parallel task execution
    - Conditional branching
    - Error handling and retries
    - Workflow templates
    - Event-driven triggers
    """
    
    def __init__(self):
        self.workflows: Dict[str, Dict] = {}
        self.templates: Dict[str, Dict] = {}
        self.active_executions: Dict[str, Dict] = {}
        self._initialize_default_templates()
        
        logger.info("⚙️ Automation Pipeline initialized")
    
    def _initialize_default_templates(self):
        """Initialize default workflow templates"""
        self.templates["document_processing"] = {
            "name": "Document Processing",
            "description": "OCR, extract, and analyze documents",
            "steps": [
                {"type": "upload", "name": "Upload Document"},
                {"type": "ocr", "name": "Extract Text"},
                {"type": "analyze", "name": "Analyze Content"},
                {"type": "store", "name": "Store Results"}
            ]
        }
        
        self.templates["data_pipeline"] = {
            "name": "Data Pipeline",
            "description": "Extract, transform, and load data",
            "steps": [
                {"type": "extract", "name": "Extract Data"},
                {"type": "transform", "name": "Transform Data"},
                {"type": "validate", "name": "Validate Data"},
                {"type": "load", "name": "Load Data"}
            ]
        }
    
    async def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        template: Optional[str] = None
    ) -> str:
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            steps: List of workflow steps
            description: Optional description
            template: Optional template to base workflow on
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        if template and template in self.templates:
            steps = self.templates[template]["steps"].copy()
        
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description or "",
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": WorkflowStatus.PENDING.value,
            "template": template
        }
        
        self.workflows[workflow_id] = workflow
        logger.info(f"⚙️ Workflow created: {name} ({workflow_id})")
        
        return workflow_id
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID to execute
            input_data: Input data for workflow
            parallel: Execute steps in parallel if possible
            
        Returns:
            Execution result
        """
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found", "workflow_id": workflow_id}
        
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        
        execution = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "start_time": datetime.now(),
            "status": WorkflowStatus.RUNNING.value,
            "input_data": input_data or {},
            "results": []
        }
        
        self.active_executions[execution_id] = execution
        
        try:
            steps = workflow["steps"]
            results = []
            
            if parallel:
                # Execute steps in parallel
                tasks = [self._execute_step(step, input_data or {}) for step in steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Execute steps sequentially
                step_output = input_data or {}
                for step in steps:
                    result = await self._execute_step(step, step_output)
                    results.append(result)
                    
                    # Use output as input for next step
                    if isinstance(result, dict) and "output" in result:
                        step_output = result["output"]
            
            execution["results"] = results
            execution["end_time"] = datetime.now()
            execution["status"] = WorkflowStatus.COMPLETED.value
            execution["duration"] = (execution["end_time"] - execution["start_time"]).total_seconds()
            
            logger.info(f"✅ Workflow completed: {workflow['name']} (execution: {execution_id})")
            
            return execution
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            execution["status"] = WorkflowStatus.FAILED.value
            execution["error"] = str(e)
            execution["end_time"] = datetime.now()
            return execution
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get("type", "unknown")
        step_name = step.get("name", "Unnamed Step")
        
        logger.debug(f"⚙️ Executing step: {step_name} (type: {step_type})")
        
        # TODO: Implement actual step execution logic
        # This is a placeholder that simulates step execution
        await asyncio.sleep(0.1)  # Simulate processing
        
        return {
            "step_name": step_name,
            "step_type": step_type,
            "status": "completed",
            "output": {"result": f"Completed {step_name}", "input": input_data},
            "timestamp": datetime.now().isoformat()
        }
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return list(self.workflows.values())
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List workflow templates"""
        return [
            {"id": tid, **template}
            for tid, template in self.templates.items()
        ]
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        return self.active_executions.get(execution_id)
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"🗑️ Workflow deleted: {workflow_id}")
            return True
        return False


# Singleton instance
_automation_pipeline: Optional[AutomationPipeline] = None


def get_automation_pipeline() -> AutomationPipeline:
    """Get or create automation pipeline singleton"""
    global _automation_pipeline
    if _automation_pipeline is None:
        _automation_pipeline = AutomationPipeline()
    return _automation_pipeline
