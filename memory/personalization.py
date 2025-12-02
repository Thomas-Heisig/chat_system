"""
👤 Personalization Engine

Provides personalization capabilities based on user preferences and behavior.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import logger


class PersonalizationEngine:
    """
    Personalization engine for user-specific customization.
    
    Features:
    - User preferences management
    - Behavior tracking
    - Personalized recommendations
    - Adaptive UI/UX
    """
    
    def __init__(self):
        self.user_preferences: Dict[str, Dict] = {}
        self.user_behavior: Dict[str, List] = {}
        
        logger.info("👤 Personalization Engine initialized")
    
    async def set_preference(
        self,
        user_id: str,
        preference_key: str,
        value: Any
    ):
        """
        Set user preference.
        
        Args:
            user_id: User identifier
            preference_key: Preference key
            value: Preference value
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id][preference_key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
    
    async def get_preference(
        self,
        user_id: str,
        preference_key: str,
        default: Optional[Any] = None
    ) -> Any:
        """
        Get user preference.
        
        Args:
            user_id: User identifier
            preference_key: Preference key
            default: Default value if not set
            
        Returns:
            Preference value
        """
        if user_id not in self.user_preferences:
            return default
        
        pref = self.user_preferences[user_id].get(preference_key)
        return pref["value"] if pref else default
    
    async def track_behavior(
        self,
        user_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Track user behavior.
        
        Args:
            user_id: User identifier
            action: Action taken
            context: Optional context
        """
        if user_id not in self.user_behavior:
            self.user_behavior[user_id] = []
        
        behavior_entry = {
            "action": action,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.user_behavior[user_id].append(behavior_entry)
        
        # Keep only recent 1000 entries
        if len(self.user_behavior[user_id]) > 1000:
            self.user_behavior[user_id] = self.user_behavior[user_id][-1000:]
    
    async def get_recommendations(
        self,
        user_id: str,
        recommendation_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations.
        
        Args:
            user_id: User identifier
            recommendation_type: Type of recommendations
            
        Returns:
            List of recommendations
        """
        # TODO: Implement actual recommendation logic
        # This is a placeholder
        return [
            {
                "type": recommendation_type,
                "title": "Sample Recommendation",
                "description": "Based on your activity",
                "relevance_score": 0.8
            }
        ]
    
    async def get_user_profile(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive user profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile
        """
        preferences = self.user_preferences.get(user_id, {})
        behavior_count = len(self.user_behavior.get(user_id, []))
        
        return {
            "user_id": user_id,
            "preferences": {
                k: v["value"]
                for k, v in preferences.items()
            },
            "total_interactions": behavior_count,
            "profile_created": preferences.get("created_at", {}).get("value")
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get personalization statistics"""
        return {
            "total_users": len(self.user_preferences),
            "users_with_behavior": len(self.user_behavior),
            "total_preferences": sum(len(p) for p in self.user_preferences.values()),
            "total_behavior_entries": sum(len(b) for b in self.user_behavior.values())
        }


# Singleton instance
_personalization: Optional[PersonalizationEngine] = None


def get_personalization_engine() -> PersonalizationEngine:
    """Get or create personalization engine singleton"""
    global _personalization
    if _personalization is None:
        _personalization = PersonalizationEngine()
    return _personalization
