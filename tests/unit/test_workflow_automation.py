"""Unit tests for AutomationPipeline."""

import pytest

from workflow.automation_pipeline import AutomationPipeline, WorkflowStatus


class TestAutomationPipeline:
    @pytest.fixture
    def pipeline(self):
        return AutomationPipeline()

    @pytest.fixture
    def sample_steps(self):
        return [
            {"type": "extract", "name": "Extract Data"},
            {"type": "transform", "name": "Transform Data"},
            {"type": "load", "name": "Load Data"},
        ]

    def test_initialization(self, pipeline):
        assert len(pipeline.workflows) == 0
        assert len(pipeline.templates) > 0
        assert len(pipeline.active_executions) == 0

    def test_default_templates_loaded(self, pipeline):
        assert "document_processing" in pipeline.templates
        assert "data_pipeline" in pipeline.templates
        assert pipeline.templates["data_pipeline"]["name"] == "Data Pipeline"

    @pytest.mark.asyncio
    async def test_create_workflow(self, pipeline, sample_steps):
        workflow_id = await pipeline.create_workflow(
            name="Test Workflow", steps=sample_steps, description="Test description"
        )

        assert workflow_id is not None
        assert workflow_id in pipeline.workflows

        workflow = pipeline.workflows[workflow_id]
        assert workflow["name"] == "Test Workflow"
        assert workflow["description"] == "Test description"
        assert len(workflow["steps"]) == 3
        assert workflow["status"] == WorkflowStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_create_workflow_from_template(self, pipeline):
        workflow_id = await pipeline.create_workflow(
            name="Doc Processing", steps=[], template="document_processing"
        )

        workflow = pipeline.workflows[workflow_id]
        assert len(workflow["steps"]) > 0
        assert workflow["template"] == "document_processing"

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, pipeline):
        result = await pipeline.execute_workflow("nonexistent_id")
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_sequential(self, pipeline, sample_steps):
        workflow_id = await pipeline.create_workflow(name="Test Workflow", steps=sample_steps)

        result = await pipeline.execute_workflow(workflow_id, {"data": "test"})

        assert result["workflow_id"] == workflow_id
        assert "execution_id" in result
        assert result["status"] == WorkflowStatus.COMPLETED.value
        assert "results" in result
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_execute_workflow_parallel(self, pipeline, sample_steps):
        workflow_id = await pipeline.create_workflow(name="Test Workflow", steps=sample_steps)

        result = await pipeline.execute_workflow(workflow_id, {"data": "test"}, parallel=True)

        assert result["status"] == WorkflowStatus.COMPLETED.value
        assert len(result["results"]) == 3

    def test_get_workflow(self, pipeline, sample_steps):
        import asyncio

        workflow_id = asyncio.run(
            pipeline.create_workflow(name="Test Workflow", steps=sample_steps)
        )

        workflow = pipeline.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow["id"] == workflow_id
        assert workflow["status"] == WorkflowStatus.PENDING.value

    def test_get_workflow_not_found(self, pipeline):
        workflow = pipeline.get_workflow("nonexistent_id")
        assert workflow is None

    @pytest.mark.asyncio
    async def test_delete_workflow(self, pipeline, sample_steps):
        workflow_id = await pipeline.create_workflow(name="Test Workflow", steps=sample_steps)

        result = await pipeline.delete_workflow(workflow_id)
        assert result is True

        # Verify workflow is deleted
        workflow = pipeline.get_workflow(workflow_id)
        assert workflow is None

    def test_list_workflows(self, pipeline, sample_steps):
        import asyncio

        asyncio.run(pipeline.create_workflow(name="Workflow 1", steps=sample_steps))
        asyncio.run(pipeline.create_workflow(name="Workflow 2", steps=sample_steps))

        workflows = pipeline.list_workflows()
        assert len(workflows) >= 2

    def test_list_templates(self, pipeline):
        templates = pipeline.list_templates()
        assert len(templates) > 0
        assert all("name" in t for t in templates)

    @pytest.mark.asyncio
    async def test_get_execution_status(self, pipeline, sample_steps):
        workflow_id = await pipeline.create_workflow(name="Test Workflow", steps=sample_steps)
        result = await pipeline.execute_workflow(workflow_id)
        execution_id = result["execution_id"]

        status = pipeline.get_execution_status(execution_id)
        assert status is not None
        assert status["execution_id"] == execution_id
        assert status["status"] == WorkflowStatus.COMPLETED.value
