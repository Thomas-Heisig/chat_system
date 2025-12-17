# services/settings_service.py
"""
Settings Service
Manages application settings with CRUD operations and persistence
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import enhanced_logger, settings


class SettingsService:
    """
    Settings management service.
    Handles reading, writing, and validating application settings.
    """

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = Path(settings_file)
        self._settings: Dict[str, Any] = {}
        self._defaults = self._get_default_settings()
        self._load_settings()

        enhanced_logger.info("SettingsService initialized", settings_file=str(self.settings_file))

    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings structure"""
        return {
            "general": {
                "app_name": settings.APP_NAME,
                "debug_mode": settings.APP_DEBUG,
                "log_level": settings.LOG_LEVEL,
                "log_format": settings.LOG_FORMAT,
                "environment": settings.APP_ENVIRONMENT,
            },
            "ai": {
                "enabled": settings.AI_ENABLED,
                "ollama_url": settings.OLLAMA_BASE_URL,
                "default_model": settings.OLLAMA_DEFAULT_MODEL,
                "temperature": 0.7,
                "max_tokens": 1000,
                "auto_respond": True,
                "context_messages": 10,
            },
            "security": {
                "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
                "rate_limit_requests": settings.RATE_LIMIT_REQUESTS,
                "rate_limit_window": settings.RATE_LIMIT_WINDOW,
                "cors_origins": settings.CORS_ORIGINS,
                "api_keys_enabled": False,
                "session_timeout_minutes": 60,
            },
            "database": {
                "type": "sqlite",
                "host": "localhost",
                "port": 5432,
                "name": "chat_system",
                "pool_size": 10,
                "backup_enabled": True,
                "backup_interval_hours": 24,
            },
            "rag": {
                "enabled": settings.RAG_ENABLED,
                "provider": "chromadb",
                "collection_name": "chat_documents",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "embedding_model": "all-MiniLM-L6-v2",
            },
            "features": {
                "project_management": settings.FEATURE_PROJECT_MANAGEMENT,
                "ticket_system": settings.FEATURE_TICKET_SYSTEM,
                "file_upload": settings.FEATURE_FILE_UPLOAD,
                "user_authentication": settings.FEATURE_USER_AUTHENTICATION,
                "websocket_enabled": settings.WEBSOCKET_ENABLED,
            },
            "ui": {
                "theme": "light",
                "language": "de",
                "show_timestamps": True,
                "enable_sound": True,
                "enable_notifications": True,
            },
        }

    def _load_settings(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    saved_settings = json.load(f)
                    # Merge with defaults
                    self._settings = self._merge_settings(self._defaults, saved_settings)
            else:
                self._settings = self._defaults.copy()

        except Exception as e:
            enhanced_logger.error("Failed to load settings", error=str(e))
            self._settings = self._defaults.copy()

    def _merge_settings(self, defaults: Dict[str, Any], saved: Dict[str, Any]) -> Dict[str, Any]:
        """Merge saved settings with defaults"""
        result = defaults.copy()

        for key, value in saved.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_settings(result[key], value)
                else:
                    result[key] = value

        return result

    def _save_settings(self):
        """Save settings to file"""
        try:
            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.settings_file, "w") as f:
                json.dump(self._settings, f, indent=2)

            enhanced_logger.debug("Settings saved")

        except Exception as e:
            enhanced_logger.error("Failed to save settings", error=str(e))
            raise

    # CRUD Operations
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()

    def get_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get settings for a specific category"""
        return self._settings.get(category, {}).copy()

    def get(self, category: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        return self._settings.get(category, {}).get(key, default)

    def set(self, category: str, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        try:
            if category not in self._settings:
                self._settings[category] = {}

            old_value = self._settings[category].get(key)
            self._settings[category][key] = value
            self._save_settings()

            enhanced_logger.info(
                "Setting updated", category=category, key=key, old_value=old_value, new_value=value
            )

            return True
        except Exception as e:
            enhanced_logger.error("Failed to set setting", error=str(e))
            return False

    def update_category(self, category: str, values: Dict[str, Any]) -> bool:
        """Update multiple settings in a category"""
        try:
            if category not in self._settings:
                self._settings[category] = {}

            self._settings[category].update(values)
            self._save_settings()

            enhanced_logger.info(
                "Category settings updated", category=category, keys=list(values.keys())
            )

            return True
        except Exception as e:
            enhanced_logger.error("Failed to update category", error=str(e))
            return False

    def reset_category(self, category: str) -> bool:
        """Reset a category to defaults"""
        try:
            if category in self._defaults:
                self._settings[category] = self._defaults[category].copy()
                self._save_settings()

                enhanced_logger.info("Category reset to defaults", category=category)
                return True
            return False
        except Exception as e:
            enhanced_logger.error("Failed to reset category", error=str(e))
            return False

    def reset_all(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self._settings = self._defaults.copy()
            self._save_settings()

            enhanced_logger.info("All settings reset to defaults")
            return True
        except Exception as e:
            enhanced_logger.error("Failed to reset all settings", error=str(e))
            return False

    # Specific Category Methods
    def get_general_settings(self) -> Dict[str, Any]:
        """Get general settings"""
        return self.get_category("general") or {}

    def update_general_settings(self, **kwargs) -> bool:
        """Update general settings"""
        return self.update_category("general", kwargs)

    def get_ai_settings(self) -> Dict[str, Any]:
        """Get AI settings"""
        return self.get_category("ai") or {}

    def update_ai_settings(self, **kwargs) -> bool:
        """Update AI settings"""
        return self.update_category("ai", kwargs)

    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings"""
        return self.get_category("security") or {}

    def update_security_settings(self, **kwargs) -> bool:
        """Update security settings"""
        return self.update_category("security", kwargs)

    def get_database_settings(self) -> Dict[str, Any]:
        """Get database settings"""
        return self.get_category("database") or {}

    def update_database_settings(self, **kwargs) -> bool:
        """Update database settings"""
        return self.update_category("database", kwargs)

    def get_rag_settings(self) -> Dict[str, Any]:
        """Get RAG settings"""
        return self.get_category("rag") or {}

    def update_rag_settings(self, **kwargs) -> bool:
        """Update RAG settings"""
        return self.update_category("rag", kwargs)

    def get_feature_settings(self) -> Dict[str, Any]:
        """Get feature flags"""
        return self.get_category("features") or {}

    def update_feature_settings(self, **kwargs) -> bool:
        """Update feature flags"""
        return self.update_category("features", kwargs)

    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings"""
        return self.get_category("ui") or {}

    def update_ui_settings(self, **kwargs) -> bool:
        """Update UI settings"""
        return self.update_category("ui", kwargs)

    # Export/Import
    def export_settings(self) -> str:
        """Export settings as JSON string"""
        return json.dumps(self._settings, indent=2)

    def import_settings(self, settings_json: str) -> bool:
        """Import settings from JSON string"""
        try:
            new_settings = json.loads(settings_json)

            # Validate structure
            if not isinstance(new_settings, dict):
                raise ValueError("Invalid settings format")

            # Merge with defaults to ensure all required keys exist
            self._settings = self._merge_settings(self._defaults, new_settings)
            self._save_settings()

            enhanced_logger.info("Settings imported successfully")
            return True

        except Exception as e:
            enhanced_logger.error("Failed to import settings", error=str(e))
            return False

    def get_available_categories(self) -> List[str]:
        """Get list of available setting categories"""
        return list(self._defaults.keys())


# Global settings service instance
settings_service = SettingsService()


__all__ = ["SettingsService", "settings_service"]
