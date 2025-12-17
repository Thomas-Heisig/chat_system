"""
Elyza Service - Evolutionary AI Playground

This service demonstrates the entire evolution of AI systems:
1. Classical ELIZA: Rule-based pattern matching (Weizenbaum, 1960s)
2. Text Analysis: Sentiment detection and language processing
3. RAG Integration: Knowledge retrieval from document databases
4. Internet Access: Real-time web search capabilities

The service progressively tries more advanced methods while maintaining
backward compatibility with simple pattern-based responses.

Feature Flag: ENABLE_ELYZA_FALLBACK (environment variable)
"""

import os
import random
import re
from enum import Enum
from typing import Any, Dict, List, Optional

from config.settings import enhanced_logger


class Language(str, Enum):
    """Supported languages for Elyza responses"""

    GERMAN = "de"
    ENGLISH = "en"


class SentimentType(str, Enum):
    """Types of sentiment detected in messages"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    QUESTION = "question"


class AIEvolutionStage(str, Enum):
    """Stages in AI evolution - from classical to modern"""

    CLASSICAL_ELIZA = "classical_eliza"  # 1960s: Pattern matching
    TEXT_ANALYSIS = "text_analysis"  # 1990s: NLP and sentiment
    RAG_KNOWLEDGE = "rag_knowledge"  # 2020s: Retrieval augmented
    INTERNET_SEARCH = "internet_search"  # Current: Real-time web search


class ElyzaService:
    """
    Evolutionary AI Playground - Demonstrating AI development from 1960s to today.

    This service showcases the evolution of conversational AI through multiple stages:

    Stage 1 - Classical ELIZA (1960s): Pattern matching and reflective responses
    Stage 2 - Text Analysis (1990s): Sentiment detection and language understanding
    Stage 3 - RAG Knowledge (2020s): Retrieval from document knowledge base
    Stage 4 - Internet Search (Current): Real-time web information

    The service tries stages progressively, providing rich metadata about which
    "generation" of AI was used for each response.

    Features:
    - Multi-stage response generation
    - Pattern-based response matching
    - Sentiment and language detection
    - RAG integration for knowledge retrieval
    - Internet search capability
    - Context-aware responses
    - Evolution tracking and statistics

    Usage:
        service = ElyzaService()
        result = await service.generate_response("What is AI?")
        # result includes: response text, stage used, metadata
    """

    def __init__(self):
        self.enabled = self._check_feature_flag()
        self.patterns = self._initialize_patterns()
        self.responses = self._initialize_responses()
        self.context: Dict[str, List[str]] = {}  # Per-user context
        self.max_context_size = 10

        # Stage configuration - which stages are enabled
        self.stages_enabled = {
            AIEvolutionStage.CLASSICAL_ELIZA: True,  # Always available
            AIEvolutionStage.TEXT_ANALYSIS: True,  # Always available
            AIEvolutionStage.RAG_KNOWLEDGE: self._check_rag_enabled(),
            AIEvolutionStage.INTERNET_SEARCH: self._check_internet_enabled(),
        }

        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "stage_usage": {stage.value: 0 for stage in AIEvolutionStage},
        }

        enhanced_logger.info(
            "ElyzaService initialized - Evolutionary AI Playground",
            enabled=self.enabled,
            patterns_count=len(self.patterns),
            responses_count=len(self.responses),
            stages_enabled={k.value: v for k, v in self.stages_enabled.items()},
        )

    def _check_feature_flag(self) -> bool:
        """Check if Elyza fallback is enabled via environment variable."""
        enabled_str = os.getenv("ENABLE_ELYZA_FALLBACK", "false").lower()
        return enabled_str in ["true", "1", "yes", "on"]

    def _check_rag_enabled(self) -> bool:
        """Check if RAG integration is enabled"""
        return os.getenv("RAG_ENABLED", "false").lower() in ["true", "1", "yes", "on"]

    def _check_internet_enabled(self) -> bool:
        """Check if internet search is enabled"""
        return os.getenv("ELYZA_INTERNET_SEARCH", "false").lower() in ["true", "1", "yes", "on"]

    def _initialize_patterns(self) -> List[Dict]:
        """Initialize pattern-response mappings with multilingual support."""
        return [
            # Greetings (German & English)
            {
                "pattern": r"\b(hallo|hi|hey|guten\s+tag|moin|servus|hello|greetings)\b",
                "responses": {
                    Language.GERMAN: [
                        "Hallo! Wie kann ich dir helfen?",
                        "Hi! Was kann ich für dich tun?",
                        "Guten Tag! Wie kann ich behilflich sein?",
                    ],
                    Language.ENGLISH: [
                        "Hello! How can I help you?",
                        "Hi! What can I do for you?",
                        "Greetings! How may I assist you?",
                    ],
                },
                "category": "greeting",
                "sentiment": SentimentType.POSITIVE,
            },
            # How are you
            {
                "pattern": r"\b(wie\s+geht|wie\s+gehts|how\s+are\s+you|how\s+are\s+things)\b",
                "responses": {
                    Language.GERMAN: [
                        "Mir geht es gut, danke der Nachfrage! Wie kann ich dir helfen?",
                        "Alles bestens! Was kann ich für dich tun?",
                        "Gut, danke! Wie kann ich dich unterstützen?",
                    ],
                    Language.ENGLISH: [
                        "I'm doing well, thank you for asking! How can I help you?",
                        "Everything's great! What can I do for you?",
                        "Good, thanks! How can I support you?",
                    ],
                },
                "category": "wellbeing",
                "sentiment": SentimentType.QUESTION,
            },
            # Thanks
            {
                "pattern": r"\b(danke|vielen\s+dank|thank\s+you|thanks|thx)\b",
                "responses": {
                    Language.GERMAN: [
                        "Gern geschehen!",
                        "Kein Problem, gerne!",
                        "Immer wieder gerne!",
                    ],
                    Language.ENGLISH: [
                        "You're welcome!",
                        "No problem, happy to help!",
                        "Anytime!",
                    ],
                },
                "category": "thanks",
                "sentiment": SentimentType.POSITIVE,
            },
            # Help
            {
                "pattern": r"\b(hilfe|help|unterstützung|helfen|support|assistance)\b",
                "responses": {
                    Language.GERMAN: [
                        "Ich bin hier, um zu helfen! Was benötigst du?",
                        "Natürlich helfe ich gerne! Worum geht es?",
                        "Wie kann ich dir helfen? Beschreibe dein Anliegen.",
                    ],
                    Language.ENGLISH: [
                        "I'm here to help! What do you need?",
                        "Of course I'll help! What's the issue?",
                        "How can I assist you? Please describe your concern.",
                    ],
                },
                "category": "help",
                "sentiment": SentimentType.QUESTION,
            },
            # Questions about name/identity
            {
                "pattern": r"\b(wer\s+bist\s+du|dein\s+name|who\s+are\s+you|what\s+are\s+you)\b",
                "responses": {
                    Language.GERMAN: [
                        "Ich bin Elyza - ein evolutionäres KI-System, das die Entwicklung von den 1960er Jahren bis heute demonstriert.",
                        "Ich bin Elyza, inspiriert von Joseph Weizenbaums ELIZA, aber erweitert um moderne RAG und Internet-Zugriff.",
                        "Mein Name ist Elyza. Ich zeige, wie KI sich von einfachen Mustern zu komplexem Wissen entwickelt hat.",
                    ],
                    Language.ENGLISH: [
                        "I'm Elyza - an evolutionary AI system demonstrating development from the 1960s to today.",
                        "I'm Elyza, inspired by Joseph Weizenbaum's ELIZA but extended with modern RAG and internet access.",
                        "My name is Elyza. I show how AI evolved from simple patterns to complex knowledge.",
                    ],
                },
                "category": "identity",
                "sentiment": SentimentType.QUESTION,
            },
            # Problems/Issues
            {
                "pattern": r"\b(problem|fehler|error|issue|funktioniert\s+nicht|not\s+working|broken)\b",
                "responses": {
                    Language.GERMAN: [
                        "Es tut mir leid, dass es ein Problem gibt. Kannst du es näher beschreiben?",
                        "Das klingt nach einem technischen Problem. Beschreibe es bitte genauer.",
                        "Ich verstehe, dass etwas nicht funktioniert. Mehr Details würden helfen.",
                    ],
                    Language.ENGLISH: [
                        "I'm sorry there's a problem. Can you describe it in more detail?",
                        "That sounds like a technical issue. Please describe it more specifically.",
                        "I understand something isn't working. More details would help.",
                    ],
                },
                "category": "problem",
                "sentiment": SentimentType.NEGATIVE,
            },
            # Yes/No
            {
                "pattern": r"\b(ja|yes|genau|richtig|korrekt|correct|exactly)\b",
                "responses": {
                    Language.GERMAN: ["Verstanden!", "Alles klar!", "Gut zu wissen!"],
                    Language.ENGLISH: ["Understood!", "Got it!", "Good to know!"],
                },
                "category": "affirmation",
                "sentiment": SentimentType.POSITIVE,
            },
            {
                "pattern": r"\b(nein|no|nicht|falsch|wrong|incorrect)\b",
                "responses": {
                    Language.GERMAN: ["In Ordnung.", "Verstanden.", "Okay, notiert."],
                    Language.ENGLISH: ["Alright.", "Understood.", "Okay, noted."],
                },
                "category": "negation",
                "sentiment": SentimentType.NEUTRAL,
            },
            # Goodbye
            {
                "pattern": r"\b(tschüss|bye|auf\s+wiedersehen|ciao|farewell|goodbye)\b",
                "responses": {
                    Language.GERMAN: ["Auf Wiedersehen!", "Tschüss! Bis bald!", "Bis später!"],
                    Language.ENGLISH: ["Goodbye!", "Bye! See you soon!", "See you later!"],
                },
                "category": "goodbye",
                "sentiment": SentimentType.NEUTRAL,
            },
        ]

    def _initialize_responses(self) -> Dict[str, Dict[Language, List[str]]]:
        """Initialize fallback responses by category and language."""
        return {
            "default": {
                Language.GERMAN: [
                    "Ich habe deine Nachricht verstanden. Ich versuche verschiedene KI-Methoden, um zu antworten.",
                    "Interessante Frage! Ich durchlaufe mehrere Wissensebenen, um eine Antwort zu finden.",
                    "Deine Anfrage wurde registriert. Ich kombiniere Pattern-Matching, Textanalyse und Wissenssuche.",
                ],
                Language.ENGLISH: [
                    "I've understood your message. I'm trying various AI methods to respond.",
                    "Interesting question! I'm going through multiple knowledge levels to find an answer.",
                    "Your request has been registered. I'm combining pattern matching, text analysis, and knowledge search.",
                ],
            },
            "unknown": {
                Language.GERMAN: [
                    "Das ist eine komplexe Frage. Mit RAG oder Internet-Zugriff könnte ich mehr dazu sagen.",
                    "Das übersteigt meine aktuellen Wissensgrenzen. Höhere KI-Stufen wären hier hilfreich.",
                    "Für diese Anfrage bräuchte ich Zugriff auf externe Wissensquellen.",
                ],
                Language.ENGLISH: [
                    "That's a complex question. With RAG or internet access I could say more.",
                    "That exceeds my current knowledge boundaries. Higher AI stages would be helpful here.",
                    "For this request I would need access to external knowledge sources.",
                ],
            },
        }

    def _detect_language(self, text: str) -> Language:
        """
        Detect language from text using simple heuristics.

        Args:
            text: Input text to analyze

        Returns:
            Detected language (defaults to German)
        """
        text_lower = text.lower()

        # Common English words/patterns
        english_indicators = [
            "the",
            "is",
            "are",
            "what",
            "how",
            "when",
            "where",
            "why",
            "you",
            "your",
            "my",
            "can",
            "could",
            "would",
            "should",
        ]

        # Common German words/patterns
        german_indicators = [
            "der",
            "die",
            "das",
            "ist",
            "sind",
            "wie",
            "was",
            "wann",
            "wo",
            "warum",
            "du",
            "dein",
            "mein",
            "kann",
            "könnte",
        ]

        english_count = sum(1 for word in english_indicators if f" {word} " in f" {text_lower} ")
        german_count = sum(1 for word in german_indicators if f" {word} " in f" {text_lower} ")

        if english_count > german_count:
            return Language.ENGLISH

        return Language.GERMAN

    def _detect_sentiment(self, text: str) -> SentimentType:
        """
        Detect sentiment from text using pattern matching.

        Args:
            text: Input text to analyze

        Returns:
            Detected sentiment type
        """
        text_lower = text.lower()

        # Question indicators
        question_words = [
            "?",
            "wie",
            "was",
            "wann",
            "wo",
            "warum",
            "wer",
            "welche",
            "how",
            "what",
            "when",
            "where",
            "why",
            "who",
            "which",
        ]
        if any(word in text_lower for word in question_words):
            return SentimentType.QUESTION

        # Positive indicators
        positive_words = [
            "toll",
            "super",
            "gut",
            "klasse",
            "danke",
            "prima",
            "perfekt",
            "great",
            "good",
            "excellent",
            "awesome",
            "thanks",
            "perfect",
        ]
        positive_count = sum(1 for word in positive_words if word in text_lower)

        # Negative indicators
        negative_words = [
            "problem",
            "fehler",
            "schlecht",
            "nicht",
            "falsch",
            "error",
            "bad",
            "wrong",
            "issue",
            "fail",
            "broken",
        ]
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count and positive_count > 0:
            return SentimentType.POSITIVE
        elif negative_count > positive_count and negative_count > 0:
            return SentimentType.NEGATIVE

        return SentimentType.NEUTRAL

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        language: Optional[Language] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response using evolutionary AI stages.

        This method progressively tries different AI "generations":
        1. Internet Search (if enabled) - Most advanced
        2. RAG Knowledge (if enabled) - Modern context-aware
        3. Text Analysis - NLP and sentiment
        4. Classical ELIZA - Pattern matching (always available)

        Args:
            prompt: User input message
            context: Optional conversation context
            user_id: Optional user identifier
            language: Optional language override (auto-detected if not provided)

        Returns:
            Dict containing:
                - response: The generated text response
                - stage: Which AI evolution stage was used
                - language: Detected/used language
                - sentiment: Detected sentiment
                - source: "elyza" identifier
                - fallback: Whether this is fallback mode
                - metadata: Additional information about the response
        """
        if not self.enabled:
            enhanced_logger.warning("ElyzaService called but ENABLE_ELYZA_FALLBACK is false")
            return {
                "response": "AI-Service ist momentan nicht verfügbar.",
                "stage": None,
                "source": "elyza",
                "error": "Service disabled",
            }

        self.stats["total_requests"] += 1

        # Detect language if not provided
        if language is None:
            language = self._detect_language(prompt)

        # Detect sentiment
        sentiment = self._detect_sentiment(prompt)

        # Update context
        self._update_context(prompt, user_id)

        # Try stages progressively (most advanced first)
        stages_to_try = [
            (AIEvolutionStage.INTERNET_SEARCH, self._try_internet_search),
            (AIEvolutionStage.RAG_KNOWLEDGE, self._try_rag_knowledge),
            (AIEvolutionStage.TEXT_ANALYSIS, self._try_text_analysis),
            (AIEvolutionStage.CLASSICAL_ELIZA, self._try_classical_eliza),
        ]

        for stage, method in stages_to_try:
            if not self.stages_enabled.get(stage, False):
                continue

            try:
                result = await method(prompt, language, sentiment, user_id)
                if result:
                    self.stats["stage_usage"][stage.value] += 1

                    enhanced_logger.info(
                        "ElyzaService generated response",
                        stage=stage.value,
                        language=language.value,
                        sentiment=sentiment.value,
                        user_id=user_id,
                    )

                    return {
                        "response": result,
                        "stage": stage.value,
                        "language": language.value,
                        "sentiment": sentiment.value,
                        "source": "elyza",
                        "fallback": True,
                        "metadata": {
                            "stage_description": self._get_stage_description(stage),
                            "context_size": len(self.context.get(user_id or "default", [])),
                        },
                    }
            except Exception as e:
                enhanced_logger.warning(
                    f"Stage {stage.value} failed",
                    error=str(e),
                    user_id=user_id,
                )
                continue

        # Absolute fallback if all stages fail
        fallback_text = random.choice(self.responses["default"][language])
        return {
            "response": fallback_text,
            "stage": "fallback",
            "language": language.value,
            "sentiment": sentiment.value,
            "source": "elyza",
            "fallback": True,
        }

    def _get_stage_description(self, stage: AIEvolutionStage) -> str:
        """Get human-readable description of AI stage"""
        descriptions = {
            AIEvolutionStage.CLASSICAL_ELIZA: "1960s Pattern Matching (Weizenbaum's ELIZA)",
            AIEvolutionStage.TEXT_ANALYSIS: "1990s NLP and Sentiment Analysis",
            AIEvolutionStage.RAG_KNOWLEDGE: "2020s Retrieval Augmented Generation",
            AIEvolutionStage.INTERNET_SEARCH: "Current: Real-time Web Search",
        }
        return descriptions.get(stage, "Unknown stage")

    async def _try_classical_eliza(
        self, prompt: str, language: Language, sentiment: SentimentType, user_id: Optional[str]
    ) -> Optional[str]:
        """
        Stage 1: Classical ELIZA pattern matching (1960s).
        This is the original Weizenbaum approach - simple pattern matching.
        """
        prompt_lower = prompt.lower()

        # Try to match patterns
        for pattern_info in self.patterns:
            pattern = pattern_info["pattern"]
            if re.search(pattern, prompt_lower):
                responses = pattern_info["responses"]

                # Get response for the detected language
                if isinstance(responses, dict):
                    response_list = responses.get(language, responses.get(Language.GERMAN, []))
                else:
                    # Fallback for old-style patterns
                    response_list = responses if isinstance(responses, list) else [responses]

                if response_list:
                    return random.choice(response_list)

        # No pattern matched
        return None

    async def _try_text_analysis(
        self, prompt: str, language: Language, sentiment: SentimentType, user_id: Optional[str]
    ) -> Optional[str]:
        """
        Stage 2: Text analysis with sentiment (1990s).
        Uses NLP techniques to understand and respond based on text analysis.
        """
        # If classical ELIZA didn't match, try sentiment-based responses
        context_messages = self.context.get(user_id or "default", [])

        # Build context-aware response based on sentiment and conversation history
        if sentiment == SentimentType.QUESTION and len(context_messages) > 0:
            # Reference previous context
            if language == Language.GERMAN:
                return "Das ist eine gute Frage. Basierend auf unserem Gespräch würde ich sagen, dass weitere Details helfen würden."
            else:
                return "That's a good question. Based on our conversation, I'd say more details would help."

        # Sentiment-based fallback
        sentiment_responses = {
            SentimentType.POSITIVE: {
                Language.GERMAN: ["Das freut mich zu hören!", "Schön, dass es gut läuft!"],
                Language.ENGLISH: ["Great to hear!", "Nice that things are going well!"],
            },
            SentimentType.NEGATIVE: {
                Language.GERMAN: [
                    "Das tut mir leid. Wie kann ich helfen?",
                    "Ich verstehe die Frustration.",
                ],
                Language.ENGLISH: [
                    "I'm sorry to hear that. How can I help?",
                    "I understand the frustration.",
                ],
            },
            SentimentType.QUESTION: {
                Language.GERMAN: ["Das ist eine interessante Frage!", "Gute Frage!"],
                Language.ENGLISH: ["That's an interesting question!", "Good question!"],
            },
        }

        responses = sentiment_responses.get(sentiment, {}).get(language, [])
        if responses:
            return random.choice(responses)

        return None

    async def _try_rag_knowledge(
        self, prompt: str, language: Language, sentiment: SentimentType, user_id: Optional[str]
    ) -> Optional[str]:
        """
        Stage 3: RAG (Retrieval Augmented Generation) - 2020s.
        Searches knowledge base for relevant information.

        Note: This is a decoupled implementation that doesn't create circular dependencies.
        RAG provider can be injected via set_rag_provider() method for better testability.
        """
        # Check if we have a RAG provider instance
        if not hasattr(self, "_rag_provider") or self._rag_provider is None:
            # Try to initialize RAG provider (only once)
            try:
                from services.rag.chroma_rag import ChromaRAGProvider

                # This is optional - only if RAG is configured
                self._rag_provider = ChromaRAGProvider({"collection_name": "documents"})
                if self._rag_provider.is_initialized:
                    enhanced_logger.info("RAG provider initialized for Elyza")
                else:
                    self._rag_provider = None
            except (ImportError, Exception) as e:
                enhanced_logger.debug(f"RAG provider not available: {e}")
                self._rag_provider = None
                return None

        # Try to use RAG provider
        try:
            if self._rag_provider and hasattr(self._rag_provider, "query"):
                # Query the knowledge base
                results = await self._rag_provider.query(prompt, top_k=3)

                if results and len(results) > 0:
                    # Build response from retrieved knowledge
                    context_snippets = [result.document.content[:200] for result in results[:2]]

                    if language == Language.GERMAN:
                        response = (
                            f"Basierend auf der Wissensdatenbank: {' ... '.join(context_snippets)}"
                        )
                    else:
                        response = f"Based on the knowledge base: {' ... '.join(context_snippets)}"

                    return response

            return None

        except Exception as e:
            enhanced_logger.debug(f"RAG knowledge query failed: {e}")
            return None

    def set_rag_provider(self, provider):
        """
        Inject RAG provider for better testability and decoupling.

        Args:
            provider: Instance of BaseRAGProvider or None
        """
        self._rag_provider = provider

    async def _try_internet_search(
        self, prompt: str, language: Language, sentiment: SentimentType, user_id: Optional[str]
    ) -> Optional[str]:
        """
        Stage 4: Internet search - Current generation.
        Searches the web for real-time information.
        """
        # Check if this looks like a question that needs current information
        current_info_keywords = [
            "aktuell",
            "heute",
            "jetzt",
            "neueste",
            "aktuelle",
            "wetter",
            "news",
            "current",
            "today",
            "now",
            "latest",
            "recent",
            "weather",
            "news",
        ]

        needs_current_info = any(keyword in prompt.lower() for keyword in current_info_keywords)

        if not needs_current_info:
            return None

        try:
            # For now, we'll use a simple placeholder response
            # A real implementation would integrate with:
            # - DuckDuckGo API
            # - Google Custom Search API
            # - Bing Search API
            # - SearxNG instance
            # using httpx.AsyncClient for HTTP requests

            if language == Language.GERMAN:
                response = (
                    f"[Internet-Suche aktiv] Für Ihre Anfrage '{prompt[:50]}...' würde ich "
                    f"normalerweise aktuelle Web-Ergebnisse abrufen. "
                    f"Integration mit Such-APIs (DuckDuckGo, Google, Bing) ist vorbereitet."
                )
            else:
                response = (
                    f"[Internet Search active] For your query '{prompt[:50]}...' I would "
                    f"normally retrieve current web results. "
                    f"Integration with search APIs (DuckDuckGo, Google, Bing) is prepared."
                )

            return response

        except Exception as e:
            enhanced_logger.debug(f"Internet search stage not available: {e}")
            return None

    def _update_context(self, message: str, user_id: Optional[str] = None):
        """Update conversation context per user."""
        key = user_id or "default"
        if key not in self.context:
            self.context[key] = []

        self.context[key].append(message)
        if len(self.context[key]) > self.max_context_size:
            self.context[key].pop(0)

    def get_context(self, user_id: Optional[str] = None) -> List[str]:
        """Get current conversation context for a user."""
        key = user_id or "default"
        return self.context.get(key, []).copy()

    def clear_context(self, user_id: Optional[str] = None) -> bool:
        """
        Clear conversation context for a user.

        Args:
            user_id: User identifier, or None to clear default context

        Returns:
            True if context was cleared
        """
        key = user_id or "default"
        if key in self.context:
            del self.context[key]
            enhanced_logger.debug("ElyzaService context cleared", user_id=user_id)
            return True
        return False

    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled

    def is_available(self) -> bool:
        """Check if service is available (alias for is_enabled for compatibility)."""
        return self.enabled

    def get_stats(self) -> Dict:
        """Get comprehensive service statistics."""
        total_responses = sum(
            len(responses[lang]) for responses in self.responses.values() for lang in responses
        )

        return {
            "enabled": self.enabled,
            "patterns_count": len(self.patterns),
            "responses_count": total_responses,
            "total_requests": self.stats["total_requests"],
            "stage_usage": self.stats["stage_usage"].copy(),
            "stages_enabled": {k.value: v for k, v in self.stages_enabled.items()},
            "active_users": len(self.context),
            "max_context_size": self.max_context_size,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed service status (for compatibility with existing tests).

        Returns:
            Status dictionary with service information
        """
        return {
            "service": "elyza",
            "enabled": self.enabled,
            "pattern_count_de": len(
                [p for p in self.patterns if Language.GERMAN in p.get("responses", {})]
            ),
            "pattern_count_en": len(
                [p for p in self.patterns if Language.ENGLISH in p.get("responses", {})]
            ),
            "stages_available": list(self.stages_enabled.keys()),
            "total_requests": self.stats["total_requests"],
        }

    def add_custom_pattern(
        self,
        pattern: str,
        responses: Dict[Language, List[str]],
        category: str = "custom",
        sentiment: SentimentType = SentimentType.NEUTRAL,
    ):
        """
        Add a custom pattern-response mapping with multilingual support.

        Args:
            pattern: Regex pattern to match
            responses: Dict mapping Language to list of responses
                      e.g., {Language.GERMAN: ["Antwort"], Language.ENGLISH: ["Answer"]}
            category: Category name for logging
            sentiment: Default sentiment type for this pattern
        """
        self.patterns.append(
            {
                "pattern": pattern,
                "responses": responses,
                "category": category,
                "sentiment": sentiment,
            }
        )

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
