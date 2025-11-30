from typing import List, Dict, Any, Optional
import requests
import json
import os
from datetime import datetime
from pathlib import Path

from database.repositories import MessageRepository
from database.models import Message, MessageType
from config.settings import logger, enhanced_logger

class MessageService:
    """
    Service für Nachrichtenverwaltung mit AI-Funktionalität
    Fokussiert auf Kern-Nachrichtenfunktionen und AI-Integration
    """
    
    def __init__(self, repository: MessageRepository):
        self.repository = repository
        
        # AI Configuration
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_available = self._check_ollama_connection()
        self.custom_model_available = self._check_custom_model()
        
        enhanced_logger.info(
            "MessageService initialized",
            ollama_available=self.ollama_available,
            custom_model_available=self.custom_model_available
        )

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                enhanced_logger.info("Ollama connection established")
                return True
        except Exception as e:
            enhanced_logger.warning("Ollama not available", error=str(e))
        return False

    def _check_custom_model(self) -> bool:
        """Check if custom model is available"""
        try:
            custom_model_path = os.getenv("CUSTOM_MODEL_PATH", "./models/custom_model")
            if os.path.exists(custom_model_path):
                enhanced_logger.info("Custom model detected")
                return True
        except Exception as e:
            enhanced_logger.warning("Custom model not available", error=str(e))
        return False

    # ============================================================================
    # AI Model Management
    # ============================================================================

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available AI models"""
        models = {
            "ollama": [],
            "custom": []
        }
        
        if self.ollama_available:
            try:
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models_data = response.json()
                    models["ollama"] = [model['name'] for model in models_data.get('models', [])]
                    enhanced_logger.debug("Ollama models fetched", count=len(models["ollama"]))
            except Exception as e:
                enhanced_logger.error("Error fetching Ollama models", error=str(e))

        if self.custom_model_available:
            models["custom"] = ["my_custom_model"]
        
        enhanced_logger.info(
            "Available models retrieved",
            ollama_models=len(models["ollama"]),
            custom_models=len(models["custom"])
        )
        return models

    # ============================================================================
    # AI Response Generation
    # ============================================================================

    def generate_ai_response(self, 
                           message: str, 
                           context_messages: List[Message] = None,
                           model_type: str = "ollama",
                           model_name: str = "llama2") -> str:
        """Generate AI response using selected model"""
        
        if not message or not message.strip():
            return "Bitte gib eine Nachricht ein."

        try:
            context = ""
            if context_messages:
                context = "\n".join([
                    f"{msg.username}: {msg.message}" 
                    for msg in context_messages[-10:]  # Last 10 messages for context
                ])

            if model_type == "ollama" and self.ollama_available:
                return self._generate_with_ollama(message, context, model_name)
            elif model_type == "custom" and self.custom_model_available:
                return self._generate_with_custom_model(message, context)
            else:
                return self._generate_fallback_response(message)

        except Exception as e:
            enhanced_logger.error(
                "Error generating AI response",
                error=str(e),
                message_preview=message[:50]
            )
            return "Es ist ein Fehler bei der Antwort-Generierung aufgetreten."

    def _generate_with_ollama(self, message: str, context: str, model_name: str) -> str:
        """Generate response using Ollama"""
        try:
            prompt = self._build_prompt(message, context)
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }

            enhanced_logger.debug(
                "Sending request to Ollama",
                model=model_name,
                prompt_length=len(prompt)
            )
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                enhanced_logger.info(
                    "Ollama response generated",
                    model=model_name,
                    response_length=len(ai_response)
                )
                return ai_response
            else:
                enhanced_logger.error(
                    "Ollama API error",
                    status_code=response.status_code,
                    model=model_name
                )
                return "Ollama konnte keine Antwort generieren."

        except Exception as e:
            enhanced_logger.error(
                "Error with Ollama generation",
                error=str(e),
                model=model_name
            )
            return "Verbindung zu Ollama fehlgeschlagen."

    def _generate_with_custom_model(self, message: str, context: str) -> str:
        """Generate response using custom model (simulated)"""
        try:
            prompt = self._build_prompt(message, context)
            
            # Simulated responses for demonstration
            responses = {
                "hallo": "Hallo! Wie kann ich dir helfen?",
                "wie geht": "Mir geht es gut, danke der Nachfrage! Und dir?",
                "danke": "Gern geschehen! 😊",
                "was kannst": "Ich kann mit dir chatten und Fragen beantworten.",
                "hilf": "Natürlich helfe ich gerne! Was möchtest du wissen?",
            }
            
            message_lower = message.lower()
            for key, response in responses.items():
                if key in message_lower:
                    enhanced_logger.info("Custom model response generated", response_type="simulated")
                    return response
            
            import random
            default_responses = [
                "Das ist eine interessante Frage!",
                "Ich verstehe, was du meinst.",
                "Könntest du das näher erläutern?",
                "Danke für deine Nachricht!",
                "Das klingt spannend!",
            ]
            
            response = random.choice(default_responses)
            enhanced_logger.info("Custom model response generated", response_type="fallback")
            return response

        except Exception as e:
            enhanced_logger.error("Error with custom model generation", error=str(e))
            return "Eigenes Modell ist momentan nicht verfügbar."

    def _build_prompt(self, message: str, context: str) -> str:
        """Build prompt for AI model"""
        if context:
            return f"""Du bist ein hilfreicher Chat-Assistent. Antworte kurz und freundlich.

Chat-Verlauf:
{context}

Benutzer: {message}
Assistant:"""
        else:
            return f"""Du bist ein hilfreicher Chat-Assistent. Antworte kurz und freundlich.

Benutzer: {message}
Assistant:"""

    def _generate_fallback_response(self, message: str) -> str:
        """Generate fallback response when no AI is available"""
        import random
        fallback_responses = [
            "Ich habe deine Nachricht erhalten: '{}'",
            "Danke für deine Nachricht: '{}'",
            "Verstanden: '{}'",
            "Notiert: '{}'"
        ]
        
        response_template = random.choice(fallback_responses)
        return response_template.format(message)

    # ============================================================================
    # Message Management with AI Integration
    # ============================================================================

    def save_message_with_ai_response(self, message: Message, use_ai: bool = True) -> Dict[str, Any]:
        """Save user message and optionally generate AI response"""
        try:
            saved_user_message = self.save_message(message)
            result = {
                "user_message": saved_user_message,
                "ai_response": None,
                "ai_used": False
            }

            if use_ai and (self.ollama_available or self.custom_model_available):
                context_messages = self.get_recent_messages(5)
                
                ai_response_text = self.generate_ai_response(
                    message=message.message,
                    context_messages=context_messages,
                    model_type="ollama" if self.ollama_available else "custom"
                )
                
                ai_message = Message(
                    username="AI Assistant",
                    message=ai_response_text,
                    message_type=MessageType.AI,
                    is_ai_response=True,
                    ai_model_used="ollama" if self.ollama_available else "custom"
                )
                saved_ai_message = self.save_message(ai_message)
                
                result["ai_response"] = saved_ai_message
                result["ai_used"] = True
                result["model_used"] = "ollama" if self.ollama_available else "custom"
                
                enhanced_logger.info(
                    "AI response generated and saved",
                    user_message_id=saved_user_message.id,
                    ai_message_id=saved_ai_message.id
                )

            return result

        except Exception as e:
            enhanced_logger.error(
                "Error in save_message_with_ai_response",
                error=str(e),
                username=message.username
            )
            saved_user_message = self.save_message(message)
            return {
                "user_message": saved_user_message,
                "ai_response": None,
                "ai_used": False,
                "error": str(e)
            }

    def ask_question(self, question: str, username: str, use_context: bool = True, 
                    model_type: str = "ollama", project_id: str = None) -> Dict[str, Any]:
        """Ask AI a question with optional context"""
        try:
            if not question.strip():
                raise ValueError("Question cannot be empty")

            enhanced_logger.info(
                "AI question asked",
                username=username,
                use_context=use_context,
                model_type=model_type,
                project_id=project_id,
                question_preview=question[:50]
            )

            context_messages = []
            if use_context:
                context_messages = self.get_recent_messages(10)

            ai_response = self.generate_ai_response(
                message=question,
                context_messages=context_messages,
                model_type=model_type
            )

            # Save both question and response
            question_message = Message(
                username=username,
                message=question,
                message_type=MessageType.USER,
                project_id=project_id
            )
            saved_question = self.save_message(question_message)

            response_message = Message(
                username="AI Assistant",
                message=ai_response,
                message_type=MessageType.AI,
                is_ai_response=True,
                ai_model_used=model_type,
                project_id=project_id
            )
            saved_response = self.save_message(response_message)

            result = {
                "question": saved_question.dict(),
                "answer": saved_response.dict(),
                "context_used": use_context,
                "context_message_count": len(context_messages),
                "model_used": model_type,
                "timestamp": datetime.now().isoformat()
            }

            enhanced_logger.info(
                "AI question answered",
                question_id=saved_question.id,
                response_id=saved_response.id,
                context_used=use_context
            )

            return result

        except Exception as e:
            enhanced_logger.error(
                "Error asking AI question",
                error=str(e),
                username=username
            )
            raise

    # ============================================================================
    # AI Analysis Features
    # ============================================================================

    def analyze_message_sentiment(self, message: str) -> Dict[str, Any]:
        """Analyze sentiment of a message using AI"""
        if not (self.ollama_available or self.custom_model_available):
            return {
                "sentiment": "neutral", 
                "confidence": 0.0, 
                "ai_available": False,
                "note": "AI service not available"
            }

        try:
            prompt = f"""Analysiere die Stimmung dieser Nachricht und antworte nur mit JSON:

Nachricht: "{message}"

Antworte im Format: {{"sentiment": "positive|neutral|negative", "confidence": 0.95, "keywords": ["wort1", "wort2"]}}"""

            if self.ollama_available:
                payload = {
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate", 
                    json=payload, 
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '{}')
                    try:
                        sentiment_data = json.loads(response_text)
                        sentiment_data["ai_available"] = True
                        sentiment_data["analysis_method"] = "ollama"
                        enhanced_logger.info(
                            "Sentiment analysis completed",
                            sentiment=sentiment_data.get("sentiment"),
                            confidence=sentiment_data.get("confidence")
                        )
                        return sentiment_data
                    except json.JSONDecodeError:
                        enhanced_logger.warning("Invalid JSON response from AI sentiment analysis")

            # Fallback analysis
            return {
                "sentiment": "neutral", 
                "confidence": 0.5, 
                "keywords": [],
                "ai_available": True,
                "analysis_method": "fallback",
                "note": "Basic analysis"
            }

        except Exception as e:
            enhanced_logger.error(
                "Error analyzing sentiment",
                error=str(e),
                message_preview=message[:30]
            )
            return {
                "sentiment": "neutral", 
                "confidence": 0.0, 
                "ai_available": False, 
                "error": str(e)
            }

    # ============================================================================
    # Core Message Operations (Delegated to Repository)
    # ============================================================================

    def save_message(self, message: Message) -> Message:
        """Save a message and return the complete message object with ID"""
        try:
            enhanced_logger.debug(
                "Saving message",
                username=message.username,
                message_length=len(message.message),
                message_type=message.message_type
            )
            
            # Validation
            if not message.username or not message.username.strip():
                raise ValueError("Username cannot be empty")
            
            if not message.message or not message.message.strip():
                raise ValueError("Message cannot be empty")
            
            message_id = self.repository.save_message(message)
            message.id = message_id
            
            enhanced_logger.info(
                "Message saved successfully",
                message_id=message_id,
                username=message.username,
                message_type=message.message_type
            )
            return message
            
        except ValueError as e:
            enhanced_logger.warning(
                "Validation error saving message",
                error=str(e),
                username=message.username
            )
            raise
        except Exception as e:
            enhanced_logger.error(
                "Error saving message",
                error=str(e),
                username=message.username
            )
            raise

    def get_recent_messages(self, limit: int = 50) -> List[Message]:
        """Get recent messages with validation and logging"""
        try:
            if limit <= 0:
                enhanced_logger.warning("Invalid limit requested, using default", requested_limit=limit)
                limit = 50
            elif limit > 1000:
                enhanced_logger.warning("Limit too high, capped", requested_limit=limit, capped_limit=1000)
                limit = 1000
            
            enhanced_logger.debug("Retrieving recent messages", limit=limit)
            
            messages = self.repository.get_recent_messages(limit)
            
            enhanced_logger.info(
                "Recent messages retrieved",
                count=len(messages),
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            enhanced_logger.error("Error retrieving recent messages", error=str(e))
            return []

    def get_all_messages(self) -> List[Message]:
        """Get all messages from the repository"""
        try:
            enhanced_logger.debug("Retrieving all messages")
            
            messages = self.repository.get_all_messages()
            
            enhanced_logger.info("All messages retrieved", count=len(messages))
            
            return messages
            
        except Exception as e:
            enhanced_logger.error("Error retrieving all messages", error=str(e))
            return []

    def get_user_messages(self, username: str, limit: int = 50) -> List[Message]:
        """Get messages from a specific user"""
        try:
            enhanced_logger.debug(
                "Retrieving user messages",
                username=username,
                limit=limit
            )
            
            if not username or not username.strip():
                enhanced_logger.warning("Empty username provided for user messages query")
                return []
            
            all_messages = self.get_all_messages()
            user_messages = [msg for msg in all_messages if msg.username == username]
            
            user_messages = user_messages[:limit]
            
            enhanced_logger.info(
                "User messages retrieved",
                username=username,
                count=len(user_messages)
            )
            
            if not user_messages:
                enhanced_logger.debug("No messages found for user", username=username)
            
            return user_messages
            
        except Exception as e:
            enhanced_logger.error(
                "Error retrieving user messages",
                error=str(e),
                username=username
            )
            return []

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_ai_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        models = self.get_available_models()
        
        return {
            "ai_enabled": self.ollama_available or self.custom_model_available,
            "ollama_available": self.ollama_available,
            "custom_model_available": self.custom_model_available,
            "available_models": models,
            "ollama_base_url": self.ollama_base_url,
            "timestamp": datetime.now().isoformat()
        }

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for message service"""
        try:
            # Test basic functionality
            recent_messages = self.get_recent_messages(5)
            ai_status = self.get_ai_status()
            
            health_status = {
                "status": "healthy",
                "service": "message_service",
                "timestamp": datetime.now().isoformat(),
                "basic_operations": {
                    "message_retrieval": True,
                    "message_count": len(recent_messages)
                },
                "ai_services": ai_status,
                "repository": "connected"
            }
            
            return health_status
            
        except Exception as e:
            enhanced_logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "service": "message_service",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }