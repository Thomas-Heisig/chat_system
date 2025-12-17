"""
👤 Personalization Engine

Provides personalization capabilities based on user preferences and behavior.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

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
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.user_behavior: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("👤 Personalization Engine initialized")

    async def set_preference(self, user_id: str, preference_key: str, value: Any):
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
            "updated_at": datetime.now().isoformat(),
        }

    async def get_preference(
        self, user_id: str, preference_key: str, default: Optional[Any] = None
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
        self, user_id: str, action: str, context: Optional[Dict[str, Any]] = None
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
            "timestamp": datetime.now().isoformat(),
        }

        self.user_behavior[user_id].append(behavior_entry)

        # Keep only recent 1000 entries
        if len(self.user_behavior[user_id]) > 1000:
            self.user_behavior[user_id] = self.user_behavior[user_id][-1000:]

    async def get_recommendations(
        self, user_id: str, recommendation_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user preferences and behavior.

        Args:
            user_id: User identifier
            recommendation_type: Type of recommendations (content, features, etc.)

        Returns:
            List of recommendations with relevance scores

        Note:
            This is a basic implementation using preference matching.
            Future enhancements: ML-based recommendations, collaborative filtering.
        """
        recommendations = []

        # Get user preferences
        user_prefs = self.user_preferences.get(user_id, {})
        user_actions = self.user_behavior.get(user_id, [])

        if recommendation_type == "content":
            # Recommend content based on previous interactions
            recent_topics = self._extract_topics_from_behavior(user_actions)

            for topic in recent_topics[:3]:  # Top 3 topics
                recommendations.append(
                    {
                        "type": "content",
                        "title": f"More about {topic}",
                        "description": f"Based on your interest in {topic}",
                        "relevance_score": 0.8,
                        "topic": topic,
                    }
                )

        elif recommendation_type == "features":
            # Recommend features based on usage patterns
            used_features = self._extract_features_from_behavior(user_actions)

            # Suggest related features
            all_features = ["ai_chat", "rag_search", "voice_transcription", "projects", "tickets"]
            unused_features = [f for f in all_features if f not in used_features]

            for feature in unused_features[:3]:
                recommendations.append(
                    {
                        "type": "feature",
                        "title": f"Try {feature.replace('_', ' ').title()}",
                        "description": f"Enhance your workflow with {feature}",
                        "relevance_score": 0.6,
                        "feature": feature,
                    }
                )

        elif recommendation_type == "settings":
            # Recommend settings based on usage patterns
            theme_pref = user_prefs.get("theme", {}).get("value")
            if not theme_pref:
                recommendations.append(
                    {
                        "type": "settings",
                        "title": "Customize Your Theme",
                        "description": "Choose between light and dark mode",
                        "relevance_score": 0.7,
                        "action": "set_theme_preference",
                    }
                )

        # Fallback: generic recommendations
        if not recommendations:
            recommendations = [
                {
                    "type": recommendation_type,
                    "title": "Explore the System",
                    "description": "Try different features to get personalized recommendations",
                    "relevance_score": 0.5,
                }
            ]

        # Sort by relevance score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)

        logger.debug(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations

    def _extract_topics_from_behavior(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from user behavior actions"""
        topics = set()
        for action in actions[-20:]:  # Last 20 actions
            if action.get("action") == "message" and action.get("metadata"):
                # Extract keywords or topics from messages
                message = action.get("metadata", {}).get("content", "")
                # Simple keyword extraction (could be enhanced with NLP)
                if "ai" in message.lower() or "assistant" in message.lower():
                    topics.add("AI Assistance")
                if "project" in message.lower():
                    topics.add("Projects")
                if "search" in message.lower():
                    topics.add("Search")
        return list(topics)

    def _extract_features_from_behavior(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Extract used features from user behavior"""
        features = set()
        for action in actions:
            feature = action.get("feature")
            if feature:
                features.add(feature)
        return list(features)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
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
            "preferences": {k: v["value"] for k, v in preferences.items()},
            "total_interactions": behavior_count,
            "profile_created": preferences.get("created_at", {}).get("value"),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get personalization statistics"""
        return {
            "total_users": len(self.user_preferences),
            "users_with_behavior": len(self.user_behavior),
            "total_preferences": sum(len(p) for p in self.user_preferences.values()),
            "total_behavior_entries": sum(len(b) for b in self.user_behavior.values()),
        }


# Singleton instance
_personalization: Optional[PersonalizationEngine] = None


def get_personalization_engine() -> PersonalizationEngine:
    """Get or create personalization engine singleton"""
    global _personalization
    if _personalization is None:
        _personalization = PersonalizationEngine()
    return _personalization
