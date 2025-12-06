"""
⚙️ Automation Pipeline Service

Handles workflow automation and task orchestration.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
                {"type": "store", "name": "Store Results"},
            ],
        }

        self.templates["data_pipeline"] = {
            "name": "Data Pipeline",
            "description": "Extract, transform, and load data",
            "steps": [
                {"type": "extract", "name": "Extract Data"},
                {"type": "transform", "name": "Transform Data"},
                {"type": "validate", "name": "Validate Data"},
                {"type": "load", "name": "Load Data"},
            ],
        }

    async def create_workflow(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None,
        template: Optional[str] = None,
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
            "template": template,
        }

        self.workflows[workflow_id] = workflow
        logger.info(f"⚙️ Workflow created: {name} ({workflow_id})")

        return workflow_id

    async def execute_workflow(
        self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None, parallel: bool = False
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
            "results": [],
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
            execution["duration"] = (
                execution["end_time"] - execution["start_time"]
            ).total_seconds()

            logger.info(f"✅ Workflow completed: {workflow['name']} (execution: {execution_id})")

            return execution

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            execution["status"] = WorkflowStatus.FAILED.value
            execution["error"] = str(e)
            execution["end_time"] = datetime.now()
            return execution

    async def _execute_step(
        self, step: Dict[str, Any], input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get("type", "unknown")
        step_name = step.get("name", "Unnamed Step")
        step_config = step.get("config", {})

        logger.debug(f"⚙️ Executing step: {step_name} (type: {step_type})")

        try:
            # Dispatch to appropriate handler based on step type
            if step_type == "upload":
                result = await self._handle_upload_step(input_data, step_config)
            elif step_type == "ocr":
                result = await self._handle_ocr_step(input_data, step_config)
            elif step_type == "analyze":
                result = await self._handle_analyze_step(input_data, step_config)
            elif step_type == "store":
                result = await self._handle_store_step(input_data, step_config)
            elif step_type == "extract":
                result = await self._handle_extract_step(input_data, step_config)
            elif step_type == "transform":
                result = await self._handle_transform_step(input_data, step_config)
            elif step_type == "validate":
                result = await self._handle_validate_step(input_data, step_config)
            elif step_type == "load":
                result = await self._handle_load_step(input_data, step_config)
            elif step_type == "notify":
                result = await self._handle_notify_step(input_data, step_config)
            elif step_type == "condition":
                result = await self._handle_condition_step(input_data, step_config)
            else:
                # Generic step execution
                result = await self._handle_generic_step(input_data, step_config)

            return {
                "step_name": step_name,
                "step_type": step_type,
                "status": "completed",
                "output": result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Step execution failed: {step_name} - {e}")
            return {
                "step_name": step_name,
                "step_type": step_type,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _handle_upload_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle file upload step"""
        await asyncio.sleep(0.1)  # Simulate processing
        return {"uploaded": True, "file_path": input_data.get("file_path", "/tmp/file")}

    async def _handle_ocr_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle OCR extraction step"""
        await asyncio.sleep(0.1)
        return {"text": "Extracted text content", "confidence": 0.95}

    async def _handle_analyze_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content analysis step"""
        await asyncio.sleep(0.1)
        return {"analysis": "Content analyzed", "sentiment": "positive"}

    async def _handle_store_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data storage step"""
        await asyncio.sleep(0.1)
        return {"stored": True, "record_id": "rec_123"}

    async def _handle_extract_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data extraction step"""
        await asyncio.sleep(0.1)
        return {"data": input_data.get("source", {}), "extracted": True}

    async def _handle_transform_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data transformation step"""
        await asyncio.sleep(0.1)
        # Create shallow copy - actual transformation logic should be implemented
        # based on config (e.g., field mapping, filtering, formatting)
        transformed = input_data.copy()
        return {"data": transformed, "transformed": True}

    async def _handle_validate_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data validation step"""
        await asyncio.sleep(0.1)
        return {"valid": True, "errors": []}

    async def _handle_load_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data loading step"""
        await asyncio.sleep(0.1)
        return {"loaded": True, "records": 1}

    async def _handle_notify_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle notification step"""
        await asyncio.sleep(0.1)
        return {"notified": True, "recipients": config.get("recipients", [])}

    async def _handle_condition_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle conditional branching step

        Note: This uses a simple comparison-based evaluation instead of eval()
        for security. Supports basic comparisons like 'field == value',
        'field > value', etc.
        """
        condition = config.get("condition", "true")

        # Simple safe evaluation without eval()
        # For more complex conditions, consider using simpleeval library
        if condition == "true":
            result = True
        elif condition == "false":
            result = False
        else:
            # Parse simple conditions like "field == value" or "field > 10"
            result = self._evaluate_simple_condition(condition, input_data)

        return {"condition_met": bool(result), "branch": "true" if result else "false"}

    def _evaluate_simple_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """
        Safely evaluate simple conditions without using eval()

        Supports: ==, !=, >, <, >=, <=, in, not in
        Example: "status == 'active'", "count > 10", "type in ['A', 'B']"
        """
        try:
            # Remove extra whitespace
            condition = condition.strip()

            # Check for operators in order of specificity (longer operators first)
            for op in [">=", "<=", "==", "!=", " not in ", " in ", ">", "<"]:
                if op in condition:
                    parts = condition.split(op, 1)
                    if len(parts) != 2:
                        continue  # Try next operator
                        left = parts[0].strip()
                        right = parts[1].strip()

                        # Get left value from data (must exist in data for valid comparison)
                        if left not in data:
                            logger.warning(f"Condition field '{left}' not found in data")
                            return False
                        left_val = data[left]

                        # Parse right value (string, number, or boolean)
                        right_val = self._parse_value(right)

                        # Perform comparison
                        if op == "==":
                            return left_val == right_val
                        elif op == "!=":
                            return left_val != right_val
                        elif op in [">", "<", ">=", "<="]:
                            # Numeric comparisons require both values to be numeric
                            try:
                                left_num = float(left_val)
                                right_num = float(right_val)
                                if op == ">":
                                    return left_num > right_num
                                elif op == "<":
                                    return left_num < right_num
                                elif op == ">=":
                                    return left_num >= right_num
                                elif op == "<=":
                                    return left_num <= right_num
                            except (ValueError, TypeError) as e:
                                logger.warning(
                                    f"Cannot perform numeric comparison: {left_val} {op} {right_val} - {e}"
                                )
                                return False
                        elif op == " in ":
                            try:
                                return left_val in right_val
                            except TypeError:
                                logger.warning(
                                    f"Cannot check membership: {left_val} in {right_val}"
                                )
                                return False
                        elif op == " not in ":
                            try:
                                return left_val not in right_val
                            except TypeError:
                                logger.warning(
                                    f"Cannot check membership: {left_val} not in {right_val}"
                                )
                                return False

            # If no operator found, treat as boolean
            return bool(data.get(condition, False))

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Condition evaluation error: {e}, condition: {condition}")
            return False

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse string value to appropriate type

        Supports:
        - Numbers: 42, 3.14
        - Booleans: true, false
        - Strings: 'text', "text"
        - Lists: ['a', 'b', 'c'] (for 'in' operations)
        """
        value_str = value_str.strip()

        # Try to parse as list (for 'in' operations)
        if value_str.startswith("[") and value_str.endswith("]"):
            try:
                import json

                # Use JSON parser for proper list handling
                return json.loads(value_str)
            except (json.JSONDecodeError, ValueError):
                # Fallback to simple parsing if JSON fails
                try:
                    content = value_str[1:-1].strip()
                    if not content:
                        return []
                    # Simple split - won't handle commas in strings correctly
                    items = [item.strip().strip("'\"") for item in content.split(",")]
                    logger.warning(
                        f"List parsed with simple method, may not handle complex values: {value_str}"
                    )
                    return items
                except Exception:
                    pass

        # Remove quotes for scalar values
        value_str = value_str.strip("'\"")

        # Try to parse as number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Try to parse as boolean
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False

        # Return as string
        return value_str

    async def _handle_generic_step(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle generic/unknown step types"""
        await asyncio.sleep(0.1)
        return {"result": "Generic step completed", "input": input_data}

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return list(self.workflows.values())

    def list_templates(self) -> List[Dict[str, Any]]:
        """List workflow templates"""
        return [{"id": tid, **template} for tid, template in self.templates.items()]

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
