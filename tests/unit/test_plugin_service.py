"""Unit tests for PluginService."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services.plugin_service import (
    Plugin,
    PluginPermission,
    PluginSandbox,
    PluginService,
    PluginStatus,
)


class TestPlugin:
    def test_plugin_creation(self):
        plugin = Plugin(
            plugin_id="test-plugin-123",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            permissions=[PluginPermission.FILESYSTEM_READ],
            entry_point="main.py",
            config={"key": "value"},
        )

        assert plugin.plugin_id == "test-plugin-123"
        assert plugin.name == "Test Plugin"
        assert plugin.version == "1.0.0"
        assert plugin.status == PluginStatus.INSTALLED

    def test_plugin_to_dict(self):
        plugin = Plugin(
            plugin_id="test-plugin-123",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            permissions=[PluginPermission.API_ACCESS],
            entry_point="main.py",
        )

        plugin_dict = plugin.to_dict()

        assert plugin_dict["plugin_id"] == "test-plugin-123"
        assert plugin_dict["name"] == "Test Plugin"
        assert "api_access" in plugin_dict["permissions"]


class TestPluginSandbox:
    @pytest.fixture
    def sample_plugin(self):
        return Plugin(
            plugin_id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            permissions=[],
            entry_point="main.py",
        )

    def test_sandbox_initialization(self, sample_plugin):
        sandbox = PluginSandbox(sample_plugin)
        assert sandbox.plugin == sample_plugin
        assert sandbox.container_id is None

    @pytest.mark.asyncio
    async def test_execute_not_enabled(self, sample_plugin):
        """Test that execution raises NotImplementedError when not enabled."""
        sandbox = PluginSandbox(sample_plugin)

        with pytest.raises(NotImplementedError):
            await sandbox.execute("test_function", args=["arg1"], kwargs={"key": "value"})

    @pytest.mark.asyncio
    async def test_execute_stub_mode(self, sample_plugin):
        """Test execution in stub mode when explicitly enabled."""
        sandbox = PluginSandbox(sample_plugin)

        with patch.dict("os.environ", {"ENABLE_PLUGIN_EXECUTION": "true"}):
            result = await sandbox.execute("test_function")
            assert result["success"] is False
            assert "stub" in result
            assert result["stub"] is True

    def test_cleanup_no_container(self, sample_plugin):
        """Test cleanup when no container exists."""
        sandbox = PluginSandbox(sample_plugin)
        sandbox.cleanup()  # Should not raise any errors

    def test_cleanup_with_container_docker_installed(self, sample_plugin):
        """Test cleanup with existing container when docker is available."""
        try:
            import docker

            sandbox = PluginSandbox(sample_plugin)
            sandbox.container_id = "test_container_123"

            # This will fail since container doesn't exist, but we're testing the code path
            sandbox.cleanup()

            # The container_id should still be set if cleanup failed
            # (or None if it was already deleted)
            assert True  # Just verify no exception is raised

        except ImportError:
            # If docker is not installed, skip this test
            pytest.skip("Docker SDK not installed")


class TestPluginService:
    @pytest.fixture
    def temp_plugin_dir(self):
        """Create a temporary plugin directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def service(self, temp_plugin_dir):
        return PluginService(plugin_dir=temp_plugin_dir)

    @pytest.fixture
    def sample_plugin_manifest(self):
        return {
            "id": "sample-plugin-123",
            "name": "Sample Plugin",
            "version": "1.0.0",
            "description": "A sample plugin for testing",
            "author": "Test Author",
            "permissions": ["filesystem_read", "api_access"],
            "entry_point": "main.py",
            "config": {"setting1": "value1"},
        }

    def test_service_initialization(self, service, temp_plugin_dir):
        assert service.plugin_dir == Path(temp_plugin_dir)
        assert len(service.plugins) == 0
        assert len(service.sandboxes) == 0
        assert len(service.hooks) == 0

    def test_load_plugins(self, temp_plugin_dir, sample_plugin_manifest):
        """Test loading plugins from directory."""
        # Create plugin directory with manifest
        plugin_dir = Path(temp_plugin_dir) / "sample-plugin"
        plugin_dir.mkdir()

        manifest_path = plugin_dir / "plugin.json"
        with open(manifest_path, "w") as f:
            json.dump(sample_plugin_manifest, f)

        # Initialize service (should load plugins)
        service = PluginService(plugin_dir=temp_plugin_dir)

        assert len(service.plugins) == 1
        assert "sample-plugin-123" in service.plugins

        plugin = service.plugins["sample-plugin-123"]
        assert plugin.name == "Sample Plugin"
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_install_plugin(self, service):
        """Test plugin installation."""
        result = await service.install_plugin("/path/to/plugin.zip")

        # Installation is a stub, so it returns success: False
        assert result["success"] is False
        assert "stub" in result

    @pytest.mark.asyncio
    async def test_enable_plugin_not_found(self, service):
        """Test enabling non-existent plugin."""
        result = await service.enable_plugin("nonexistent-plugin")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_disable_plugin_not_found(self, service):
        """Test disabling non-existent plugin."""
        result = await service.disable_plugin("nonexistent-plugin")

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_uninstall_plugin_not_found(self, service):
        """Test uninstalling non-existent plugin."""
        result = await service.uninstall_plugin("nonexistent-plugin")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_list_plugins_empty(self, service):
        """Test listing plugins when none are installed."""
        plugins = service.list_plugins()

        assert isinstance(plugins, list)
        assert len(plugins) == 0

    def test_list_plugins_with_plugins(self, temp_plugin_dir, sample_plugin_manifest):
        """Test listing installed plugins."""
        # Create plugin
        plugin_dir = Path(temp_plugin_dir) / "sample-plugin"
        plugin_dir.mkdir()

        manifest_path = plugin_dir / "plugin.json"
        with open(manifest_path, "w") as f:
            json.dump(sample_plugin_manifest, f)

        service = PluginService(plugin_dir=temp_plugin_dir)
        plugins = service.list_plugins()

        assert len(plugins) == 1
        assert plugins[0]["name"] == "Sample Plugin"

    def test_get_plugin_not_found(self, service):
        """Test getting info for non-existent plugin."""
        plugin = service.get_plugin("nonexistent-plugin")

        assert plugin is None

    def test_register_hook(self, service):
        """Test registering a hook."""

        def test_hook():
            pass

        service.register_hook("test_event", test_hook)

        assert "test_event" in service.hooks
        assert test_hook in service.hooks["test_event"]

    @pytest.mark.asyncio
    async def test_trigger_hook(self, service):
        """Test triggering a hook."""

        called = []

        def test_hook(data):
            called.append(data)

        service.register_hook("test_event", test_hook)

        await service.trigger_hook("test_event", {"message": "test"})

        assert len(called) == 1
        assert called[0]["message"] == "test"

    def test_get_status(self, service):
        """Test getting service status."""
        status = service.get_status()

        assert "total_plugins" in status
        assert "enabled_plugins" in status
        assert status["total_plugins"] >= 0
