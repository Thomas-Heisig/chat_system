#!/usr/bin/env python3
"""
WebSocket Client Example

This script demonstrates how to use WebSocket for real-time communication,
including:
- Connecting to WebSocket server
- Sending and receiving messages
- Handling different message types
- Presence tracking
- Typing indicators
- Error handling and reconnection

Usage:
    python examples/websocket_client_example.py

Requirements:
    - Chat system running on localhost:8000
    - Valid authentication token
    - websockets library: pip install websockets
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import websockets
except ImportError:
    print("Error: websockets library not found")
    print("Install it with: pip install websockets")
    sys.exit(1)

import aiohttp  # noqa: E402


class WebSocketClient:
    """WebSocket chat client"""

    def __init__(
        self,
        base_url: str = "ws://localhost:8000",
        http_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url
        self.http_url = http_url
        self.api_key = api_key
        self.websocket = None
        self.running = False
        self.handlers = {}
        self.user_id = None
        self.username = None

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate via HTTP and get JWT token"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.http_url}/api/v1/auth/login",
                json={"username": username, "password": password},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_key = data["access_token"]
                    self.username = username
                    print(f"✅ Authenticated as {username}")
                    return self.api_key
                else:
                    error = await response.text()
                    raise Exception(f"Authentication failed: {error}")

    async def connect(self, channel: str = "general"):
        """Connect to WebSocket server"""
        if not self.api_key:
            raise Exception("Not authenticated. Call authenticate() first.")

        ws_url = f"{self.base_url}/ws?token={self.api_key}&channel={channel}"

        try:
            self.websocket = await websockets.connect(ws_url)
            self.running = True
            print(f"✅ Connected to channel: {channel}")

            # Start message receiver
            asyncio.create_task(self._receive_messages())

        except Exception as e:
            raise Exception(f"Connection failed: {e}")

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected")

    async def _receive_messages(self):
        """Receive messages from server"""
        try:
            while self.running and self.websocket:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)

                    # Handle message based on type
                    msg_type = data.get("type", "message")

                    if msg_type in self.handlers:
                        await self.handlers[msg_type](data)
                    else:
                        await self._default_handler(data)

                except websockets.exceptions.ConnectionClosed:
                    print("⚠️  Connection closed")
                    break
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON: {message}")
                except Exception as e:
                    print(f"⚠️  Error receiving message: {e}")

        finally:
            self.running = False

    async def _default_handler(self, data: dict):
        """Default message handler"""
        msg_type = data.get("type", "unknown")
        print(f"📨 [{msg_type}] {json.dumps(data, indent=2)}")

    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_type] = handler

    async def send_message(
        self, content: str, channel: str = "general", message_type: str = "chat_message"
    ):
        """Send chat message"""
        if not self.websocket:
            raise Exception("Not connected")

        message = {
            "type": message_type,
            "content": content,
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
        }

        await self.websocket.send(json.dumps(message))

    async def send_typing_indicator(self, is_typing: bool, channel: str = "general"):
        """Send typing indicator"""
        if not self.websocket:
            return

        message = {"type": "typing_start" if is_typing else "typing_stop", "channel": channel}

        await self.websocket.send(json.dumps(message))

    async def send_custom(self, data: dict):
        """Send custom message"""
        if not self.websocket:
            raise Exception("Not connected")

        await self.websocket.send(json.dumps(data))


async def example_basic_chat():
    """Example: Basic chat messaging"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Chat Messaging")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    # Define message handler
    async def on_message(data):
        user = data.get("username", "Unknown")
        content = data.get("content", "")
        print(f"💬 {user}: {content}")

    client.on("chat_message", on_message)

    # Connect
    await client.authenticate("admin", "admin")
    await client.connect("general")

    # Send messages
    await client.send_message("Hello, World!")
    await asyncio.sleep(1)

    await client.send_message("This is a test message")
    await asyncio.sleep(1)

    await client.send_message("WebSocket is working!")
    await asyncio.sleep(2)

    await client.disconnect()


async def example_presence_tracking():
    """Example: User presence tracking"""
    print("\n" + "=" * 60)
    print("Example 2: User Presence Tracking")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    # Track online users
    online_users = set()

    async def on_presence(data):
        user_id = data.get("user_id")
        status = data.get("status")

        if status == "online":
            online_users.add(user_id)
            print(f"🟢 User {user_id} is now online")
        elif status == "offline":
            online_users.discard(user_id)
            print(f"🔴 User {user_id} is now offline")

        print(f"   Total online: {len(online_users)}")

    client.on("presence", on_presence)

    # Connect
    await client.authenticate("admin", "admin")
    await client.connect("general")

    # Wait for presence updates
    print("\n👥 Tracking user presence...")
    await asyncio.sleep(5)

    await client.disconnect()


async def example_typing_indicators():
    """Example: Typing indicators"""
    print("\n" + "=" * 60)
    print("Example 3: Typing Indicators")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    async def on_typing_start(data):
        user = data.get("username", "Someone")
        print(f"✍️  {user} is typing...")

    async def on_typing_stop(data):
        user = data.get("username", "Someone")
        print(f"⏸️  {user} stopped typing")

    client.on("typing_start", on_typing_start)
    client.on("typing_stop", on_typing_stop)

    # Connect
    await client.authenticate("admin", "admin")
    await client.connect("general")

    # Simulate typing
    print("\n⌨️  Simulating typing...")

    await client.send_typing_indicator(True)
    await asyncio.sleep(2)

    await client.send_message("I was just typing this message!")

    await client.send_typing_indicator(False)
    await asyncio.sleep(1)

    await client.disconnect()


async def example_multi_channel():
    """Example: Multi-channel communication"""
    print("\n" + "=" * 60)
    print("Example 4: Multi-Channel Communication")
    print("=" * 60 + "\n")

    # Create multiple clients for different channels
    client1 = WebSocketClient()
    client2 = WebSocketClient()

    async def on_message_general(data):
        print(f"[GENERAL] {data.get('username', '?')}: {data.get('content', '')}")

    async def on_message_tech(data):
        print(f"[TECH] {data.get('username', '?')}: {data.get('content', '')}")

    client1.on("chat_message", on_message_general)
    client2.on("chat_message", on_message_tech)

    # Connect to different channels
    await client1.authenticate("admin", "admin")
    await client1.connect("general")

    await client2.authenticate("admin", "admin")
    await client2.connect("tech")

    # Send messages to different channels
    await client1.send_message("Hello from general channel!", "general")
    await asyncio.sleep(1)

    await client2.send_message("Hello from tech channel!", "tech")
    await asyncio.sleep(1)

    # Disconnect
    await client1.disconnect()
    await client2.disconnect()


async def example_ai_integration():
    """Example: AI message integration"""
    print("\n" + "=" * 60)
    print("Example 5: AI Message Integration")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    async def on_message(data):
        msg_type = data.get("message_type", "user")
        user = data.get("username", "Unknown")
        content = data.get("content", "")

        if msg_type == "ai":
            print(f"🤖 AI: {content}")
        else:
            print(f"👤 {user}: {content}")

    async def on_ai_processing(data):
        print("🔄 AI is processing your request...")

    client.on("chat_message", on_message)
    client.on("ai_processing", on_ai_processing)

    # Connect
    await client.authenticate("admin", "admin")
    await client.connect("general")

    # Send message with AI request
    await client.send_custom(
        {"type": "ai_request", "content": "What is Python?", "model": "llama2"}
    )

    # Wait for AI response
    await asyncio.sleep(5)

    await client.disconnect()


async def example_error_handling():
    """Example: Error handling and reconnection"""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling and Reconnection")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"\n🔄 Connection attempt {attempt + 1}/{max_retries}")

            await client.authenticate("admin", "admin")
            await client.connect("general")

            # Test connection
            await client.send_message("Connection test")
            await asyncio.sleep(2)

            print("✅ Connection successful")
            break

        except Exception as e:
            print(f"❌ Connection failed: {e}")

            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("❌ Max retries reached")

    if client.running:
        await client.disconnect()


async def example_file_sharing():
    """Example: File sharing notification"""
    print("\n" + "=" * 60)
    print("Example 7: File Sharing Notifications")
    print("=" * 60 + "\n")

    client = WebSocketClient()

    async def on_file_shared(data):
        filename = data.get("filename", "Unknown")
        user = data.get("username", "Someone")
        file_size = data.get("size", 0)

        print(f"📎 {user} shared: {filename} ({file_size} bytes)")

    client.on("file_shared", on_file_shared)

    # Connect
    await client.authenticate("admin", "admin")
    await client.connect("general")

    # Simulate file share notification
    await client.send_custom(
        {"type": "file_shared", "filename": "document.pdf", "size": 1024000, "file_id": "abc123"}
    )

    await asyncio.sleep(2)

    await client.disconnect()


async def interactive_chat():
    """Interactive chat client"""
    print("\n" + "=" * 60)
    print("Interactive WebSocket Chat")
    print("=" * 60)
    print("\nCommands:")
    print("  /typing - Toggle typing indicator")
    print("  /channel <name> - Switch channel")
    print("  /ai <message> - Send to AI")
    print("  /quit - Exit")
    print("\n" + "=" * 60 + "\n")

    client = WebSocketClient()

    # Message handlers
    async def on_chat_message(data):
        user = data.get("username", "Unknown")
        content = data.get("content", "")
        _ = data.get("timestamp", "")  # Timestamp available but not currently used
        msg_type = data.get("message_type", "user")

        if msg_type == "ai":
            print(f"\n🤖 AI: {content}")
        else:
            print(f"\n💬 {user}: {content}")
        print("You: ", end="", flush=True)

    async def on_typing(data):
        user = data.get("username", "Someone")
        print(f"\n✍️  {user} is typing...")
        print("You: ", end="", flush=True)

    async def on_presence(data):
        user_id = data.get("user_id", "Unknown")
        status = data.get("status", "unknown")
        print(f"\n{'🟢' if status == 'online' else '🔴'} User {user_id} is {status}")
        print("You: ", end="", flush=True)

    client.on("chat_message", on_chat_message)
    client.on("typing_start", on_typing)
    client.on("presence", on_presence)

    # Authenticate
    username = input("Username [admin]: ").strip() or "admin"
    password = input("Password [admin]: ").strip() or "admin"

    try:
        await client.authenticate(username, password)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    # Connect
    channel = input("Channel [general]: ").strip() or "general"
    await client.connect(channel)

    current_channel = channel
    typing = False

    # Message loop
    print("\nYou: ", end="", flush=True)

    try:
        while client.running:
            # Use asyncio to read input without blocking
            try:
                user_input = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, input), timeout=0.1
                )
            except asyncio.TimeoutError:
                continue

            if not user_input.strip():
                print("You: ", end="", flush=True)
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split(maxsplit=1)
                cmd = parts[0].lower()

                if cmd == "quit":
                    break

                elif cmd == "typing":
                    typing = not typing
                    await client.send_typing_indicator(typing, current_channel)
                    print(f"Typing indicator: {'ON' if typing else 'OFF'}")

                elif cmd == "channel" and len(parts) > 1:
                    await client.disconnect()
                    current_channel = parts[1]
                    await client.connect(current_channel)
                    print(f"Switched to channel: {current_channel}")

                elif cmd == "ai" and len(parts) > 1:
                    await client.send_custom(
                        {"type": "ai_request", "content": parts[1], "channel": current_channel}
                    )

                else:
                    print(f"Unknown command: /{cmd}")

            else:
                # Send chat message
                await client.send_message(user_input, current_channel)

            print("You: ", end="", flush=True)

    except KeyboardInterrupt:
        print("\n")

    finally:
        await client.disconnect()


async def main():
    """Run all examples"""

    print("\n" + "=" * 60)
    print("WebSocket Client Examples")
    print("Universal Chat System")
    print("=" * 60)

    # Menu
    print("\nSelect an example:")
    print("  1. Basic Chat Messaging")
    print("  2. User Presence Tracking")
    print("  3. Typing Indicators")
    print("  4. Multi-Channel Communication")
    print("  5. AI Integration")
    print("  6. Error Handling and Reconnection")
    print("  7. File Sharing Notifications")
    print("  8. Interactive Chat")
    print("  9. Run All Examples")

    choice = input("\nEnter choice (1-9) [8]: ").strip() or "8"

    try:
        if choice == "1":
            await example_basic_chat()
        elif choice == "2":
            await example_presence_tracking()
        elif choice == "3":
            await example_typing_indicators()
        elif choice == "4":
            await example_multi_channel()
        elif choice == "5":
            await example_ai_integration()
        elif choice == "6":
            await example_error_handling()
        elif choice == "7":
            await example_file_sharing()
        elif choice == "8":
            await interactive_chat()
        elif choice == "9":
            await example_basic_chat()
            await example_presence_tracking()
            await example_typing_indicators()
            await example_multi_channel()
            await example_ai_integration()
            await example_error_handling()
            await example_file_sharing()
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
