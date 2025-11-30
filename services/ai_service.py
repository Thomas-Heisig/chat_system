# services/ai_service.py
"""
AI Service - Centralized AI/LLM Integration
Manages AI models, providers, and generates responses
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import httpx
import json
import asyncio

from config.settings import settings, enhanced_logger


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.available = False
    
    async def check_availability(self) -> bool:
        """Check if provider is available"""
        return self.available
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt"""
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama AI provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("ollama", config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.default_model = config.get('default_model', 'llama2')
        self.timeout = config.get('timeout', 60)
    
    async def check_availability(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self.available = response.status_code == 200
                return self.available
        except Exception as e:
            enhanced_logger.warning("Ollama not available", error=str(e))
            self.available = False
            return False
    
    async def get_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            enhanced_logger.error("Failed to get Ollama models", error=str(e))
        return []
    
    async def generate(self, prompt: str, model: str = None, 
                       temperature: float = 0.7, max_tokens: int = 500,
                       stream: bool = False, **kwargs) -> str:
        """Generate response using Ollama"""
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get('options', {})
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    enhanced_logger.error("Ollama API error", status=response.status_code)
                    return ""
        except Exception as e:
            enhanced_logger.error("Ollama generation failed", error=str(e))
            raise
    
    async def generate_stream(self, prompt: str, model: str = None,
                              **kwargs) -> AsyncGenerator[str, None]:
        """Generate response with streaming"""
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": kwargs.get('options', {})
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    'POST',
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
        except Exception as e:
            enhanced_logger.error("Ollama streaming failed", error=str(e))
            raise


class AIService:
    """
    Centralized AI Service
    Manages multiple AI providers and handles generation requests
    """
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider = None
        self._initialized = False
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'total_tokens_generated': 0,
            'requests_by_provider': {},
            'requests_by_model': {}
        }
    
    async def initialize(self):
        """Initialize AI service and check providers"""
        enhanced_logger.info("Initializing AI Service")
        
        # Initialize Ollama provider
        ollama_config = {
            'base_url': settings.OLLAMA_BASE_URL,
            'default_model': settings.OLLAMA_DEFAULT_MODEL,
            'timeout': 60
        }
        ollama = OllamaProvider(ollama_config)
        
        if await ollama.check_availability():
            self.providers['ollama'] = ollama
            self.default_provider = 'ollama'
            enhanced_logger.info("Ollama provider initialized", 
                               models=await ollama.get_models())
        
        self._initialized = True
        enhanced_logger.info("AI Service initialized", 
                           providers=list(self.providers.keys()),
                           default=self.default_provider)
    
    async def generate_response(self, prompt: str, provider: str = None,
                                model: str = None, **kwargs) -> Dict[str, Any]:
        """
        Generate AI response.
        
        Args:
            prompt: The prompt/question
            provider: AI provider to use (defaults to default_provider)
            model: Model to use
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict with response, metadata, and stats
        """
        start_time = datetime.now()
        provider_name = provider or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            return {
                'success': False,
                'error': 'No AI provider available',
                'response': None
            }
        
        ai_provider = self.providers[provider_name]
        self.stats['total_requests'] += 1
        self.stats['requests_by_provider'][provider_name] = \
            self.stats['requests_by_provider'].get(provider_name, 0) + 1
        
        try:
            response = await ai_provider.generate(prompt, model=model, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            self.stats['successful_responses'] += 1
            if model:
                self.stats['requests_by_model'][model] = \
                    self.stats['requests_by_model'].get(model, 0) + 1
            
            enhanced_logger.info("AI response generated",
                               provider=provider_name,
                               model=model,
                               duration=duration,
                               response_length=len(response))
            
            return {
                'success': True,
                'response': response,
                'provider': provider_name,
                'model': model or ai_provider.default_model,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats['failed_responses'] += 1
            duration = (datetime.now() - start_time).total_seconds()
            
            enhanced_logger.error("AI generation failed",
                                provider=provider_name,
                                error=str(e),
                                duration=duration)
            
            return {
                'success': False,
                'error': str(e),
                'provider': provider_name,
                'duration_seconds': duration
            }
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                              provider: str = None, model: str = None,
                              **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion from message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: AI provider to use
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Dict with response and metadata
        """
        # Build prompt from messages
        prompt = self._build_chat_prompt(messages)
        return await self.generate_response(prompt, provider, model, **kwargs)
    
    def _build_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Build a prompt from chat messages"""
        parts = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                parts.append(f"System: {content}")
            elif role == 'assistant':
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")
        
        parts.append("Assistant:")
        return "\n\n".join(parts)
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models from all providers"""
        models = {}
        
        for name, provider in self.providers.items():
            if isinstance(provider, OllamaProvider):
                models[name] = await provider.get_models()
            else:
                models[name] = []
        
        return models
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AI service statistics"""
        return {
            **self.stats,
            'providers_count': len(self.providers),
            'available_providers': list(self.providers.keys()),
            'default_provider': self.default_provider,
            'initialized': self._initialized
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of AI service"""
        provider_health = {}
        
        for name, provider in self.providers.items():
            available = await provider.check_availability()
            provider_health[name] = {
                'available': available,
                'config': {
                    k: v for k, v in provider.config.items()
                    if k not in ['api_key', 'password']
                }
            }
        
        return {
            'status': 'healthy' if self.providers else 'no_providers',
            'initialized': self._initialized,
            'providers': provider_health,
            'default_provider': self.default_provider,
            'stats': self.get_stats()
        }


# Global AI service instance
ai_service = AIService()


__all__ = ['AIService', 'ai_service', 'OllamaProvider', 'AIProvider']
