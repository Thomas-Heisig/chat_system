#!/usr/bin/env python3
"""
AI Chat Integration Example

This script demonstrates how to integrate AI capabilities into the chat system,
including:
- Connecting to AI models (Ollama, OpenAI)
- Sending prompts and receiving responses
- Managing conversation context
- Using different AI models
- Streaming responses
- Error handling

Usage:
    python examples/ai_chat_example.py

Requirements:
    - Chat system running on localhost:8000
    - Ollama installed (or OpenAI API key configured)
    - Valid authentication token
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import from project
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp  # noqa: E402
from typing import Optional  # noqa: E402


class AIChatExample:
    """Example AI chat client"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.conversation_history = []

    async def __aenter__(self):
        """Setup async context"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup async context"""
        if self.session:
            await self.session.close()

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate and get JWT token"""
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login", json={"username": username, "password": password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.api_key = data["access_token"]
                print(f"✅ Authenticated as {username}")
                return self.api_key
            else:
                error = await response.text()
                raise Exception(f"Authentication failed: {error}")

    async def send_message(
        self,
        prompt: str,
        model: str = "llama2",
        temperature: float = 0.7,
        max_tokens: int = 500,
        use_context: bool = True,
    ) -> dict:
        """Send message to AI and get response"""

        if not self.api_key:
            raise Exception("Not authenticated. Call authenticate() first.")

        # Build request
        request_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add conversation history if requested
        if use_context and self.conversation_history:
            request_data["conversation_history"] = self.conversation_history[-10:]

        # Send request
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with self.session.post(
            f"{self.base_url}/api/v1/ai/generate", json=request_data, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()

                # Update conversation history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": data["response"]})

                return data
            else:
                error = await response.text()
                raise Exception(f"AI request failed: {error}")

    async def stream_message(self, prompt: str, model: str = "llama2", temperature: float = 0.7):
        """Stream AI response token by token"""

        if not self.api_key:
            raise Exception("Not authenticated. Call authenticate() first.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        request_data = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "stream": True,
        }

        async with self.session.post(
            f"{self.base_url}/api/v1/ai/generate", json=request_data, headers=headers
        ) as response:
            if response.status == 200:
                full_response = ""

                async for line in response.content:
                    if line:
                        token = line.decode("utf-8").strip()
                        print(token, end="", flush=True)
                        full_response += token

                print()  # Newline at end

                # Update history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": full_response})

                return full_response
            else:
                error = await response.text()
                raise Exception(f"Stream failed: {error}")

    async def list_models(self) -> list:
        """Get list of available AI models"""

        if not self.api_key:
            raise Exception("Not authenticated. Call authenticate() first.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with self.session.get(
            f"{self.base_url}/api/v1/ai/models", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["models"]
            else:
                error = await response.text()
                raise Exception(f"Failed to get models: {error}")

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🗑️  Conversation history cleared")


async def example_basic_chat():
    """Example: Basic AI chat"""
    print("\n" + "=" * 60)
    print("Example 1: Basic AI Chat")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        # Authenticate
        await chat.authenticate("admin", "admin")

        # Send a message
        print("\nUser: What is Python?")
        response = await chat.send_message(
            "What is Python? Explain in 2-3 sentences.", model="llama2", temperature=0.7
        )
        print(f"AI: {response['response']}\n")

        # Follow-up question (uses context)
        print("User: What are its main uses?")
        response = await chat.send_message("What are its main uses?", use_context=True)
        print(f"AI: {response['response']}\n")


async def example_model_comparison():
    """Example: Compare different models"""
    print("\n" + "=" * 60)
    print("Example 2: Model Comparison")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        await chat.authenticate("admin", "admin")

        # Get available models
        models = await chat.list_models()
        print(f"Available models: {', '.join(models)}\n")

        prompt = "Explain quantum computing in one sentence."

        # Try each model
        for model in models[:2]:  # Limit to first 2 models
            print(f"\n--- {model} ---")
            print(f"User: {prompt}")

            try:
                response = await chat.send_message(prompt, model=model, use_context=False)
                print(f"AI: {response['response']}")
            except Exception as e:
                print(f"Error with {model}: {e}")


async def example_streaming():
    """Example: Streaming responses"""
    print("\n" + "=" * 60)
    print("Example 3: Streaming Responses")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        await chat.authenticate("admin", "admin")

        print("User: Write a short poem about AI")
        print("AI: ", end="")

        await chat.stream_message(
            "Write a short 4-line poem about artificial intelligence.",
            model="llama2",
            temperature=0.9,  # Higher temperature for creativity
        )


async def example_code_generation():
    """Example: Code generation"""
    print("\n" + "=" * 60)
    print("Example 4: Code Generation")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        await chat.authenticate("admin", "admin")

        # Use codellama if available
        models = await chat.list_models()
        code_model = "codellama" if "codellama" in models else models[0]

        print(f"Using model: {code_model}")
        print("\nUser: Write a Python function to calculate fibonacci numbers")

        response = await chat.send_message(
            "Write a Python function to calculate the nth fibonacci number. "
            "Include docstring and example usage.",
            model=code_model,
            temperature=0.3,  # Lower for more consistent code
            max_tokens=300,
        )

        print(f"\nAI:\n{response['response']}\n")


async def example_multi_turn_conversation():
    """Example: Multi-turn conversation with context"""
    print("\n" + "=" * 60)
    print("Example 5: Multi-Turn Conversation")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        await chat.authenticate("admin", "admin")

        questions = [
            "What is FastAPI?",
            "What are its main advantages?",
            "How does it compare to Flask?",
            "Give me a simple example",
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n[Turn {i}]")
            print(f"User: {question}")

            response = await chat.send_message(
                question, use_context=True, max_tokens=200  # Use conversation history
            )

            print(f"AI: {response['response']}")

        print(f"\nConversation history: {len(chat.conversation_history)} messages")


async def example_error_handling():
    """Example: Error handling"""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60 + "\n")

    async with AIChatExample() as chat:
        await chat.authenticate("admin", "admin")

        # Test 1: Invalid model
        print("Test: Invalid model")
        try:
            await chat.send_message("Hello", model="nonexistent-model")
        except Exception as e:
            print(f"✅ Caught error: {e}\n")

        # Test 2: Very long prompt (might exceed limits)
        print("Test: Very long prompt")
        try:
            long_prompt = "Tell me about " + "Python " * 5000
            await chat.send_message(long_prompt, max_tokens=100)
        except Exception as e:
            print(f"✅ Caught error: {e}\n")

        # Test 3: Successful request
        print("Test: Valid request")
        try:
            response = await chat.send_message("Hello!")
            print(f"✅ Success: {response['response'][:50]}...\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


async def interactive_chat():
    """Interactive chat session"""
    print("\n" + "=" * 60)
    print("Interactive AI Chat")
    print("=" * 60)
    print("\nCommands:")
    print("  /models - List available models")
    print("  /model <name> - Switch model")
    print("  /clear - Clear conversation history")
    print("  /stream - Toggle streaming mode")
    print("  /quit - Exit")
    print("\n" + "=" * 60 + "\n")

    async with AIChatExample() as chat:
        # Authenticate
        username = input("Username [admin]: ").strip() or "admin"
        password = input("Password [admin]: ").strip() or "admin"

        try:
            await chat.authenticate(username, password)
        except Exception as e:
            print(f"Authentication failed: {e}")
            return

        current_model = "llama2"
        streaming = False

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    cmd = user_input[1:].lower().split()

                    if cmd[0] == "quit":
                        print("Goodbye!")
                        break

                    elif cmd[0] == "models":
                        models = await chat.list_models()
                        print(f"Available models: {', '.join(models)}")
                        print(f"Current model: {current_model}")
                        continue

                    elif cmd[0] == "model" and len(cmd) > 1:
                        current_model = cmd[1]
                        print(f"Switched to model: {current_model}")
                        continue

                    elif cmd[0] == "clear":
                        chat.clear_history()
                        continue

                    elif cmd[0] == "stream":
                        streaming = not streaming
                        print(f"Streaming: {'enabled' if streaming else 'disabled'}")
                        continue

                    else:
                        print(f"Unknown command: /{cmd[0]}")
                        continue

                # Send message
                print("AI: ", end="")

                if streaming:
                    await chat.stream_message(user_input, model=current_model)
                else:
                    response = await chat.send_message(user_input, model=current_model)
                    print(response["response"])

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


async def main():
    """Run all examples"""

    print("\n" + "=" * 60)
    print("AI Chat Integration Examples")
    print("Universal Chat System")
    print("=" * 60)

    # Check environment
    print("\nChecking environment...")
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found")

    # Menu
    print("\nSelect an example:")
    print("  1. Basic AI Chat")
    print("  2. Model Comparison")
    print("  3. Streaming Responses")
    print("  4. Code Generation")
    print("  5. Multi-Turn Conversation")
    print("  6. Error Handling")
    print("  7. Interactive Chat")
    print("  8. Run All Examples")

    choice = input("\nEnter choice (1-8) [8]: ").strip() or "8"

    try:
        if choice == "1":
            await example_basic_chat()
        elif choice == "2":
            await example_model_comparison()
        elif choice == "3":
            await example_streaming()
        elif choice == "4":
            await example_code_generation()
        elif choice == "5":
            await example_multi_turn_conversation()
        elif choice == "6":
            await example_error_handling()
        elif choice == "7":
            await interactive_chat()
        elif choice == "8":
            await example_basic_chat()
            await example_model_comparison()
            await example_streaming()
            await example_code_generation()
            await example_multi_turn_conversation()
            await example_error_handling()
        else:
            print("Invalid choice")
            return

        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
