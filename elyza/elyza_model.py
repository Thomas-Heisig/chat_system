"""
🤖 ELYZA - Evolutionary AI Playground Model

Demonstrates the complete evolution of conversational AI from the 1960s to today:
- Classical ELIZA (1960s): Pattern matching
- Text Analysis (1990s): NLP and sentiment
- RAG Knowledge (2020s): Document retrieval
- Internet Search (Current): Real-time web access

This is not a traditional AI model but rather a "playground" that showcases
how AI has continuously evolved, inspired by Weizenbaum's original ELIZA
but extended with modern capabilities.
"""

import os
from typing import Any, Dict, List, Optional

from config.settings import logger


class ELYZAModel:
    """
    Evolutionary AI Playground Model.
    
    This model represents the continuous evolution of AI from simple
    pattern matching to modern knowledge-augmented systems. It integrates:
    
    1. Classical ELIZA patterns (1960s Weizenbaum)
    2. Text analysis and sentiment detection
    3. RAG (Retrieval Augmented Generation) for knowledge access
    4. Internet search for current information
    
    The model progressively tries more advanced methods while maintaining
    backward compatibility with simple pattern-based responses.

    Features:
    - Multi-stage AI evolution demonstration
    - Offline operation (classical patterns)
    - RAG integration (when enabled)
    - Internet access (when enabled)
    - Graceful degradation through stages
    - Rich response metadata
    """

    def __init__(self):
        # Use centralized configuration
        try:
            from config.settings import ai_config, settings
            self.enabled = ai_config.elyza_enabled
            self.model_path = ai_config.elyza_model_path
            self.use_gpu = ai_config.elyza_use_gpu
            self.max_length = ai_config.elyza_max_length
            self.temperature = ai_config.elyza_temperature
            self.device = ai_config.elyza_device
            self._rag_enabled = settings.RAG_ENABLED
        except Exception:
            # Fallback to environment variables if config import fails
            self.enabled = os.getenv("ELYZA_ENABLED", "false").lower() == "true"
            self.model_path = os.getenv("ELYZA_MODEL_PATH", "./models/elyza")
            self.use_gpu = os.getenv("ELYZA_USE_GPU", "false").lower() == "true"
            self.max_length = int(os.getenv("ELYZA_MAX_LENGTH", "512"))
            self.temperature = float(os.getenv("ELYZA_TEMPERATURE", "0.7"))
            self.device = os.getenv("ELYZA_DEVICE", "cpu")
            self._rag_enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"
        
        self.model_loaded = False
        self.fallback_active = False
        
        # Integration with ElyzaService
        self._elyza_service = None
        
        # Internet capabilities
        self._internet_enabled = os.getenv("ELYZA_INTERNET_SEARCH", "false").lower() == "true"

        if self.enabled:
            self._initialize_model()
        else:
            logger.info("🤖 ELYZA Model is disabled (set ELYZA_ENABLED=true to enable)")

        logger.info(
            f"🤖 ELYZA Evolutionary Model initialized "
            f"(enabled: {self.enabled}, loaded: {self.model_loaded}, "
            f"RAG: {self._rag_enabled}, Internet: {self._internet_enabled})"
        )

    def _initialize_model(self):
        """
        Initialize the ELYZA evolutionary model.
        
        Instead of loading a traditional ML model, this initializes the
        ElyzaService which provides the evolutionary AI playground.
        """
        try:
            # Initialize the ElyzaService for multi-stage responses
            from services.elyza_service import get_elyza_service
            
            self._elyza_service = get_elyza_service()
            self.model_loaded = self._elyza_service.is_enabled()
            
            if self.model_loaded:
                logger.info(
                    f"✅ ELYZA Evolutionary Model loaded with stages: "
                    f"{list(self._elyza_service.stages_enabled.keys())}"
                )
            else:
                logger.warning("⚠️ ELYZA service is disabled")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize ELYZA model: {e}")
            self.model_loaded = False

    async def generate(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        user_id: Optional[str] = None,
        context: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate response using evolutionary AI stages.
        
        This method demonstrates the evolution of AI by progressively trying:
        1. Internet Search (most advanced - if enabled)
        2. RAG Knowledge (modern - if enabled)
        3. Text Analysis (1990s)
        4. Classical ELIZA (1960s - always available)

        Args:
            prompt: Input prompt/question
            max_length: Maximum response length (informational)
            temperature: Sampling temperature (informational)
            user_id: Optional user identifier for context
            context: Optional conversation context

        Returns:
            Dict containing:
                - text: Generated response text
                - model: "elyza_evolutionary"
                - stage: Which AI evolution stage was used
                - language: Detected language
                - sentiment: Detected sentiment
                - fallback_mode: Whether in fallback mode
                - metadata: Rich information about the response generation
        """
        if not self.enabled:
            return {
                "error": "ELYZA fallback is disabled",
                "note": "Set ENABLE_ELYZA_FALLBACK=true to enable",
                "model": "elyza_evolutionary",
            }

        if not self.model_loaded or not self._elyza_service:
            return {
                "error": "ELYZA service not loaded",
                "note": "ElyzaService initialization failed",
                "model": "elyza_evolutionary",
            }

        try:
            # Use the ElyzaService to generate response through evolutionary stages
            result = await self._elyza_service.generate_response(
                prompt=prompt,
                context=context,
                user_id=user_id,
            )
            
            # Enhance result with model-level information
            return {
                "text": result.get("response", ""),
                "model": "elyza_evolutionary",
                "stage": result.get("stage"),
                "language": result.get("language"),
                "sentiment": result.get("sentiment"),
                "fallback_mode": self.fallback_active,
                "prompt_length": len(prompt),
                "max_length": max_length,
                "temperature": temperature,
                "metadata": {
                    **result.get("metadata", {}),
                    "evolution_info": {
                        "classical_available": True,
                        "text_analysis_available": True,
                        "rag_available": self._rag_enabled,
                        "internet_available": self._internet_enabled,
                    },
                    "service_stats": self._elyza_service.get_stats(),
                },
                "status": "success",
            }
            
        except Exception as e:
            logger.error(f"❌ ELYZA generation failed: {e}")
            return {
                "error": str(e),
                "model": "elyza_evolutionary",
                "status": "error",
            }

    def activate_fallback(self):
        """Activate fallback mode"""
        self.fallback_active = True
        logger.info("🔄 ELYZA fallback mode activated")

    def deactivate_fallback(self):
        """Deactivate fallback mode"""
        self.fallback_active = False
        logger.info("✅ ELYZA fallback mode deactivated")

    def is_available(self) -> bool:
        """Check if ELYZA model is available"""
        return self.enabled and self.model_loaded

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information.
        
        Returns information about the evolutionary AI playground,
        including which stages are available and usage statistics.
        """
        base_info = {
            "model": "ELYZA Evolutionary Playground",
            "description": "AI evolution from 1960s ELIZA to modern RAG and Internet",
            "enabled": self.enabled,
            "loaded": self.model_loaded,
            "fallback_active": self.fallback_active,
            "model_path": self.model_path,
            "capabilities": [
                "classical_pattern_matching",
                "text_analysis",
                "sentiment_detection",
                "multilingual_support",
            ],
        }
        
        # Add RAG capability if enabled
        if self._rag_enabled:
            base_info["capabilities"].append("rag_knowledge_retrieval")
            
        # Add Internet capability if enabled
        if self._internet_enabled:
            base_info["capabilities"].append("internet_search")
        
        # Add service statistics if available
        if self._elyza_service:
            base_info["service_stats"] = self._elyza_service.get_stats()
            base_info["evolution_stages"] = {
                "1960s_classical_eliza": "Pattern matching (always available)",
                "1990s_text_analysis": "NLP and sentiment (always available)",
                "2020s_rag_knowledge": f"Document retrieval ({'enabled' if self._rag_enabled else 'disabled'})",
                "current_internet_search": f"Web search ({'enabled' if self._internet_enabled else 'disabled'})",
            }
        
        return base_info

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns health status for all AI evolution stages.
        """
        health = {
            "status": "healthy" if self.is_available() else "unavailable",
            "model_loaded": self.model_loaded,
            "fallback_active": self.fallback_active,
            "stages": {
                "classical_eliza": "healthy" if self.model_loaded else "unavailable",
                "text_analysis": "healthy" if self.model_loaded else "unavailable",
                "rag_knowledge": "healthy" if self._rag_enabled else "disabled",
                "internet_search": "healthy" if self._internet_enabled else "disabled",
            },
        }
        
        # Add service health if available
        if self._elyza_service:
            health["service_enabled"] = self._elyza_service.is_enabled()
            health["total_requests"] = self._elyza_service.stats["total_requests"]
        
        return health


# Singleton instance
_elyza_model: Optional[ELYZAModel] = None


def get_elyza_model() -> ELYZAModel:
    """Get or create ELYZA model singleton"""
    global _elyza_model
    if _elyza_model is None:
        _elyza_model = ELYZAModel()
    return _elyza_model
