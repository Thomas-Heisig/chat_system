"""
Elyza Service - Simple rule-based fallback for AI responses.

This service provides a lightweight fallback mechanism when external AI services
(like Ollama or OpenAI) are unavailable. It uses simple pattern matching and
predefined responses to maintain basic conversational capability.

Feature Flag: ENABLE_ELYZA_FALLBACK (environment variable)
"""

import os
import random
import re
from typing import Dict, List, Optional

from config.settings import enhanced_logger


class ElyzaService:
    """
    Elyza-inspired fallback service for basic conversational responses.

    This service does NOT require external API calls or AI models.
    It uses pattern matching and predefined responses to provide
    basic conversational capability when AI services are down.

    Features:
    - Pattern-based response matching
    - Context-aware responses
    - Simple sentiment detection
    - No external dependencies
    - Fast response times

    Usage:
        service = ElyzaService()
        response = service.generate_response("Hello, how are you?")
    """

    def __init__(self):
        self.enabled = self._check_feature_flag()
        self.patterns = self._initialize_patterns()
        self.responses = self._initialize_responses()
        self.context: List[str] = []
        self.max_context_size = 5

        enhanced_logger.info(
            "ElyzaService initialized",
            enabled=self.enabled,
            patterns_count=len(self.patterns),
            responses_count=len(self.responses),
        )

    def _check_feature_flag(self) -> bool:
        """Check if Elyza fallback is enabled via environment variable."""
        enabled_str = os.getenv("ENABLE_ELYZA_FALLBACK", "false").lower()
        return enabled_str in ["true", "1", "yes", "on"]

    def _initialize_patterns(self) -> List[Dict]:
        """Initialize pattern-response mappings."""
        return [
            # Greetings
            {
                "pattern": r"\b(hallo|hi|hey|guten\s+tag|moin|servus)\b",
                "responses": [
                    "Hallo! Wie kann ich dir helfen?",
                    "Hi! Was kann ich für dich tun?",
                    "Guten Tag! Wie kann ich behilflich sein?",
                ],
                "category": "greeting",
            },
            # How are you
            {
                "pattern": r"\b(wie\s+geht|wie\s+gehts|how\s+are\s+you)\b",
                "responses": [
                    "Mir geht es gut, danke der Nachfrage! Wie kann ich dir helfen?",
                    "Alles bestens! Was kann ich für dich tun?",
                    "Gut, danke! Wie kann ich dich unterstützen?",
                ],
                "category": "wellbeing",
            },
            # Thanks
            {
                "pattern": r"\b(danke|vielen\s+dank|thank\s+you|thanks)\b",
                "responses": ["Gern geschehen!", "Kein Problem, gerne!", "Immer wieder gerne!"],
                "category": "thanks",
            },
            # Help
            {
                "pattern": r"\b(hilfe|help|unterstützung|helfen)\b",
                "responses": [
                    "Ich bin hier, um zu helfen! Was benötigst du?",
                    "Natürlich helfe ich gerne! Worum geht es?",
                    "Wie kann ich dir helfen? Beschreibe dein Anliegen.",
                ],
                "category": "help",
            },
            # Questions about name/identity
            {
                "pattern": r"\b(wer\s+bist\s+du|dein\s+name|who\s+are\s+you)\b",
                "responses": [
                    "Ich bin ein Fallback-Assistent. Der Haupt-AI-Service ist momentan nicht verfügbar.",
                    "Ich bin Elyza, ein einfacher Antwort-Assistent für den Fall, dass der Haupt-AI-Service ausfällt.",
                    "Ich bin ein Backup-System, das einspringt, wenn der primäre AI-Service nicht erreichbar ist.",
                ],
                "category": "identity",
            },
            # Problems/Issues
            {
                "pattern": r"\b(problem|fehler|error|issue|funktioniert\s+nicht)\b",
                "responses": [
                    "Es tut mir leid, dass es ein Problem gibt. Kannst du es näher beschreiben?",
                    "Das klingt nach einem technischen Problem. Beschreibe es bitte genauer.",
                    "Ich verstehe, dass etwas nicht funktioniert. Mehr Details würden helfen.",
                ],
                "category": "problem",
            },
            # Yes/No
            {
                "pattern": r"\b(ja|yes|genau|richtig|korrekt)\b",
                "responses": ["Verstanden!", "Alles klar!", "Gut zu wissen!"],
                "category": "affirmation",
            },
            {
                "pattern": r"\b(nein|no|nicht|falsch)\b",
                "responses": ["In Ordnung.", "Verstanden.", "Okay, notiert."],
                "category": "negation",
            },
            # Goodbye
            {
                "pattern": r"\b(tschüss|bye|auf\s+wiedersehen|ciao)\b",
                "responses": ["Auf Wiedersehen!", "Tschüss! Bis bald!", "Bis später!"],
                "category": "goodbye",
            },
        ]

    def _initialize_responses(self) -> Dict[str, List[str]]:
        """Initialize fallback responses by category."""
        return {
            "default": [
                "Ich habe deine Nachricht erhalten. Der Haupt-AI-Service ist momentan nicht verfügbar.",
                "Verstanden. Leider kann ich als Fallback-System nur grundlegende Antworten geben.",
                "Ich habe deine Anfrage registriert. Für komplexere Antworten benötigen wir den Haupt-AI-Service.",
                "Deine Nachricht wurde empfangen. Der AI-Service ist temporär nicht erreichbar.",
            ],
            "unknown": [
                "Das kann ich leider nicht beantworten. Der erweiterte AI-Service ist gerade nicht verfügbar.",
                "Dafür bräuchte ich den Haupt-AI-Service, der momentan offline ist.",
                "Das übersteigt meine Fähigkeiten als Fallback-System.",
            ],
        }

    def generate_response(
        self, prompt: str, context: Optional[List[str]] = None, user_id: Optional[str] = None
    ) -> str:
        """
        Generate a response based on pattern matching.

        Args:
            prompt: User input message
            context: Optional conversation context
            user_id: Optional user identifier

        Returns:
            str: Generated response
        """
        if not self.enabled:
            enhanced_logger.warning("ElyzaService called but ENABLE_ELYZA_FALLBACK is false")
            return "AI-Service ist momentan nicht verfügbar."

        # Update context
        self._update_context(prompt)

        # Normalize prompt
        prompt_lower = prompt.lower()

        # Try to match patterns
        for pattern_info in self.patterns:
            pattern = pattern_info["pattern"]
            if re.search(pattern, prompt_lower):
                response = random.choice(pattern_info["responses"])

                enhanced_logger.info(
                    "ElyzaService matched pattern",
                    category=pattern_info["category"],
                    user_id=user_id,
                )

                return response

        # No pattern matched - return default response
        response = random.choice(self.responses["default"])

        enhanced_logger.info("ElyzaService using default response", user_id=user_id)

        return response

    def _update_context(self, message: str):
        """Update conversation context."""
        self.context.append(message)
        if len(self.context) > self.max_context_size:
            self.context.pop(0)

    def get_context(self) -> List[str]:
        """Get current conversation context."""
        return self.context.copy()

    def clear_context(self):
        """Clear conversation context."""
        self.context = []
        enhanced_logger.debug("ElyzaService context cleared")

    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled

    def get_stats(self) -> Dict:
        """Get service statistics."""
        return {
            "enabled": self.enabled,
            "patterns_count": len(self.patterns),
            "responses_count": sum(len(r) for r in self.responses.values()),
            "context_size": len(self.context),
            "max_context_size": self.max_context_size,
        }

    def add_custom_pattern(self, pattern: str, responses: List[str], category: str = "custom"):
        """
        Add a custom pattern-response mapping.

        Args:
            pattern: Regex pattern to match
            responses: List of possible responses
            category: Category name for logging
        """
        self.patterns.append({"pattern": pattern, "responses": responses, "category": category})

        enhanced_logger.info(
            "Custom pattern added to ElyzaService", category=category, pattern=pattern
        )


# Global instance (lazy initialization)
_elyza_service: Optional[ElyzaService] = None


def get_elyza_service() -> ElyzaService:
    """
    Get or create the global ElyzaService instance.

    Returns:
        ElyzaService: The singleton instance
    """
    global _elyza_service
    if _elyza_service is None:
        _elyza_service = ElyzaService()
    return _elyza_service
