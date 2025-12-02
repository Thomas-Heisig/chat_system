"""
🤖 Elyza Service - Local AI Fallback

Rule-based conversational AI service that acts as a fallback when external
AI services (like Ollama or OpenAI) are unavailable.

Inspired by ELIZA, the classic pattern-matching chatbot, but extended with
modern capabilities and German language support.

Features:
- Pattern-based response generation
- Context awareness
- Sentiment detection
- Multi-language support (German/English)
- Configurable via environment variable

Environment Variables:
- ENABLE_ELYZA_FALLBACK: Enable/disable Elyza fallback (default: true)
- ELYZA_LANGUAGE: Preferred language (default: de)

TODO:
- [ ] Add machine learning-based response ranking
- [ ] Implement conversation history tracking
- [ ] Add personalization based on user preferences
- [ ] Integrate with knowledge base for factual responses
- [ ] Add sentiment-based response adaptation
"""

import os
import re
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum

from config.settings import logger


class Language(str, Enum):
    """Supported languages"""
    GERMAN = "de"
    ENGLISH = "en"


class SentimentType(str, Enum):
    """Message sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    QUESTION = "question"


class ElyzaService:
    """
    Local rule-based AI service for fallback responses
    
    Provides basic conversational capabilities when external AI
    services are unavailable.
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_ELYZA_FALLBACK", "true").lower() == "true"
        self.language = Language(os.getenv("ELYZA_LANGUAGE", "de"))
        
        # Response patterns for German
        self.patterns_de = self._init_german_patterns()
        
        # Response patterns for English
        self.patterns_en = self._init_english_patterns()
        
        # Conversation context
        self.context: Dict[str, List[str]] = {}
        
        logger.info(
            f"🤖 Elyza Service initialized "
            f"(enabled={self.enabled}, language={self.language})"
        )
    
    def _init_german_patterns(self) -> List[Tuple[str, List[str]]]:
        """Initialize German response patterns"""
        return [
            # Greetings
            (r'\b(hallo|hi|hey|guten\s+tag|grüß\s+gott|moin)\b', [
                "Hallo! Wie kann ich dir heute helfen?",
                "Hi! Schön, von dir zu hören. Was kann ich für dich tun?",
                "Guten Tag! Wie geht es dir?",
                "Hey! Womit kann ich dir behilflich sein?",
            ]),
            
            # How are you
            (r'\bwie\s+geht\s*es\s+(dir|ihnen)\b', [
                "Mir geht es gut, danke der Nachfrage! Wie geht es dir?",
                "Ausgezeichnet! Ich bin bereit, dir zu helfen.",
                "Sehr gut! Was kann ich heute für dich tun?",
            ]),
            
            # Name questions
            (r'\bwie\s+(heißt|heisst)\s+du\b', [
                "Ich bin Elyza, dein lokaler KI-Assistent.",
                "Man nennt mich Elyza - ein Fallback-Assistent, wenn die großen KI-Modelle nicht verfügbar sind.",
                "Elyza ist mein Name. Ich helfe gerne, wo ich kann!",
            ]),
            
            # Thanks
            (r'\b(danke|dankeschön|vielen\s+dank)\b', [
                "Gerne! Kann ich noch etwas für dich tun?",
                "Bitte, immer gerne!",
                "Kein Problem! Meld dich, wenn du noch Hilfe brauchst.",
            ]),
            
            # Goodbye
            (r'\b(tschüss|tschüß|tschau|ciao|auf\s+wiedersehen|bis\s+bald)\b', [
                "Auf Wiedersehen! Bis zum nächsten Mal!",
                "Tschüss! Komm gut nach Hause!",
                "Bis bald! War schön mit dir zu chatten.",
            ]),
            
            # Help requests
            (r'\b(hilf|hilfe|helfen|brauch|brauche)\b', [
                "Natürlich helfe ich dir! Was genau brauchst du?",
                "Ich bin für dich da. Beschreib mir dein Problem.",
                "Gerne! Worum geht es?",
            ]),
            
            # Questions about capabilities
            (r'\bwas\s+kannst\s+du\b', [
                "Ich bin ein einfacher Fallback-Assistent. Ich kann grundlegende Fragen beantworten und dich durch das Chat-System führen.",
                "Meine Fähigkeiten sind begrenzt, aber ich versuche mein Bestes, dir zu helfen!",
                "Ich kann einfache Konversationen führen und grundlegende Informationen bereitstellen.",
            ]),
            
            # Yes/No
            (r'\b(ja|okay|ok|gut|genau|richtig)\b', [
                "Verstehe! Was möchtest du als Nächstes tun?",
                "Alles klar! Wie kann ich weiterhelfen?",
                "Super! Gibt es noch etwas?",
            ]),
            
            (r'\b(nein|nicht|ne|nö)\b', [
                "Okay, verstanden. Kann ich dir anders helfen?",
                "Kein Problem. Gibt es etwas anderes?",
                "Alles klar. Was möchtest du stattdessen?",
            ]),
            
            # Problems/Errors
            (r'\b(fehler|error|problem|funktioniert\s+nicht|geht\s+nicht)\b', [
                "Das tut mir leid. Kannst du mir mehr Details zum Problem geben?",
                "Ich verstehe, dass etwas nicht funktioniert. Was genau ist das Problem?",
                "Lass uns das Problem gemeinsam lösen. Was genau funktioniert nicht?",
            ]),
            
            # Positive feedback
            (r'\b(toll|super|großartig|wunderbar|perfekt|ausgezeichnet)\b', [
                "Das freut mich zu hören!",
                "Super! Gibt es noch etwas, bei dem ich helfen kann?",
                "Wunderbar! Lass mich wissen, wenn du noch Hilfe brauchst.",
            ]),
        ]
    
    def _init_english_patterns(self) -> List[Tuple[str, List[str]]]:
        """Initialize English response patterns"""
        return [
            # Greetings
            (r'\b(hello|hi|hey|good\s+morning|good\s+afternoon)\b', [
                "Hello! How can I help you today?",
                "Hi! Nice to hear from you. What can I do for you?",
                "Hey! How are you doing?",
            ]),
            
            # How are you
            (r'\bhow\s+are\s+you\b', [
                "I'm doing well, thank you! How are you?",
                "Excellent! I'm ready to help you.",
                "Very good! What can I do for you today?",
            ]),
            
            # Name questions
            (r'\bwhat.*your\s+name\b', [
                "I'm Elyza, your local AI assistant.",
                "They call me Elyza - a fallback assistant when the big AI models aren't available.",
                "Elyza is my name. Happy to help!",
            ]),
            
            # Thanks
            (r'\b(thanks|thank\s+you)\b', [
                "You're welcome! Anything else I can help with?",
                "My pleasure!",
                "No problem! Let me know if you need more help.",
            ]),
            
            # Goodbye
            (r'\b(bye|goodbye|see\s+you|later)\b', [
                "Goodbye! See you next time!",
                "Bye! Take care!",
                "See you later! It was nice chatting with you.",
            ]),
            
            # Help requests
            (r'\b(help|assist|need)\b', [
                "Of course I'll help! What exactly do you need?",
                "I'm here for you. Describe your problem.",
                "Sure! What's the issue?",
            ]),
        ]
    
    def _detect_sentiment(self, message: str) -> SentimentType:
        """
        Detect the sentiment of a message
        
        Args:
            message: Input message
            
        Returns:
            Detected sentiment type
        """
        message_lower = message.lower()
        
        # Check for questions
        if '?' in message or any(word in message_lower for word in ['wer', 'was', 'wann', 'wo', 'wie', 'warum', 'who', 'what', 'when', 'where', 'why', 'how']):
            return SentimentType.QUESTION
        
        # Positive indicators
        positive_words = ['gut', 'toll', 'super', 'großartig', 'perfekt', 'danke', 'good', 'great', 'awesome', 'perfect', 'thanks']
        if any(word in message_lower for word in positive_words):
            return SentimentType.POSITIVE
        
        # Negative indicators
        negative_words = ['fehler', 'problem', 'schlecht', 'nicht', 'error', 'bad', 'problem', 'issue', 'wrong']
        if any(word in message_lower for word in negative_words):
            return SentimentType.NEGATIVE
        
        return SentimentType.NEUTRAL
    
    def _match_pattern(self, message: str, language: Language) -> Optional[str]:
        """
        Match message against patterns and return response
        
        Args:
            message: Input message
            language: Language to use
            
        Returns:
            Matched response or None
        """
        patterns = self.patterns_de if language == Language.GERMAN else self.patterns_en
        message_lower = message.lower()
        
        for pattern, responses in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses)
        
        return None
    
    def _generate_fallback_response(self, message: str, sentiment: SentimentType, language: Language) -> str:
        """
        Generate a fallback response when no pattern matches
        
        Args:
            message: Input message
            sentiment: Detected sentiment
            language: Language to use
            
        Returns:
            Fallback response
        """
        if language == Language.GERMAN:
            if sentiment == SentimentType.QUESTION:
                responses = [
                    "Das ist eine interessante Frage. Leider bin ich als einfacher Fallback-Assistent begrenzt. Versuche es später noch einmal, wenn die erweiterten KI-Dienste verfügbar sind.",
                    "Gute Frage! Dafür bräuchte ich die erweiterten KI-Funktionen. Kann ich dir anders helfen?",
                    "Hmm, das kann ich dir nicht genau beantworten. Hast du eine andere Frage?",
                ]
            elif sentiment == SentimentType.POSITIVE:
                responses = [
                    "Das freut mich! Wie kann ich dir weiterhelfen?",
                    "Super! Was möchtest du als Nächstes tun?",
                    "Toll! Gibt es noch etwas?",
                ]
            elif sentiment == SentimentType.NEGATIVE:
                responses = [
                    "Das tut mir leid. Kann ich dir irgendwie helfen?",
                    "Ich verstehe deine Frustration. Was kann ich für dich tun?",
                    "Lass uns versuchen, das Problem zu lösen. Beschreib mir mehr.",
                ]
            else:
                responses = [
                    "Ich habe verstanden. Wie kann ich dir helfen?",
                    "Interessant. Erzähl mir mehr.",
                    "Okay. Was möchtest du wissen?",
                    "Ich bin hier, um zu helfen. Was brauchst du?",
                ]
        else:  # English
            if sentiment == SentimentType.QUESTION:
                responses = [
                    "That's an interesting question. Unfortunately, as a simple fallback assistant, I'm limited. Try again later when the advanced AI services are available.",
                    "Good question! I'd need the advanced AI features for that. Can I help you differently?",
                    "Hmm, I can't answer that precisely. Do you have another question?",
                ]
            elif sentiment == SentimentType.POSITIVE:
                responses = [
                    "Glad to hear that! How can I help you further?",
                    "Great! What would you like to do next?",
                    "Awesome! Anything else?",
                ]
            elif sentiment == SentimentType.NEGATIVE:
                responses = [
                    "I'm sorry to hear that. Can I help somehow?",
                    "I understand your frustration. What can I do for you?",
                    "Let's try to solve the problem. Tell me more.",
                ]
            else:
                responses = [
                    "I understand. How can I help you?",
                    "Interesting. Tell me more.",
                    "Okay. What would you like to know?",
                    "I'm here to help. What do you need?",
                ]
        
        return random.choice(responses)
    
    async def generate_response(
        self,
        message: str,
        user_id: Optional[str] = None,
        language: Optional[Language] = None
    ) -> Dict[str, Any]:
        """
        Generate a response to a user message
        
        Args:
            message: User input message
            user_id: Optional user identifier for context
            language: Optional language override
            
        Returns:
            Response dict with message and metadata
        """
        if not self.enabled:
            return {
                "response": "Elyza fallback service is disabled.",
                "source": "elyza",
                "enabled": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Use provided language or default
        lang = language or self.language
        
        # Detect sentiment
        sentiment = self._detect_sentiment(message)
        
        # Try pattern matching
        response = self._match_pattern(message, lang)
        
        # Fallback to generic response
        if not response:
            response = self._generate_fallback_response(message, sentiment, lang)
        
        # Store context (simple implementation)
        if user_id:
            if user_id not in self.context:
                self.context[user_id] = []
            self.context[user_id].append(message)
            # Keep only last 5 messages
            self.context[user_id] = self.context[user_id][-5:]
        
        logger.debug(
            f"Elyza response generated: sentiment={sentiment}, "
            f"user_id={user_id}, language={lang}"
        )
        
        return {
            "response": response,
            "source": "elyza",
            "sentiment": sentiment.value,
            "language": lang.value,
            "enabled": self.enabled,
            "timestamp": datetime.now().isoformat(),
            "fallback": True,
            "message": "Response generated by Elyza fallback service"
        }
    
    def is_available(self) -> bool:
        """Check if Elyza service is available"""
        return self.enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "elyza",
            "enabled": self.enabled,
            "language": self.language.value,
            "active_contexts": len(self.context),
            "pattern_count_de": len(self.patterns_de),
            "pattern_count_en": len(self.patterns_en),
            "status": "online" if self.enabled else "disabled"
        }
    
    def clear_context(self, user_id: str) -> bool:
        """Clear conversation context for a user"""
        if user_id in self.context:
            del self.context[user_id]
            return True
        return False


# Singleton instance
_elyza_service: Optional[ElyzaService] = None


def get_elyza_service() -> ElyzaService:
    """
    Get or create the Elyza service singleton
    
    Returns:
        ElyzaService instance
    """
    global _elyza_service
    if _elyza_service is None:
        _elyza_service = ElyzaService()
    return _elyza_service
