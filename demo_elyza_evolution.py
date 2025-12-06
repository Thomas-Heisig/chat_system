#!/usr/bin/env python3
"""
🤖 ELYZA Evolutionary AI Playground - Demonstration Script

This script demonstrates how ELYZA progresses through different AI generations
to answer questions, from classical 1960s pattern matching to modern internet search.

Run with:
    ENABLE_ELYZA_FALLBACK=true python demo_elyza_evolution.py
    
Or with all stages enabled:
    ENABLE_ELYZA_FALLBACK=true ELYZA_INTERNET_SEARCH=true RAG_ENABLED=true python demo_elyza_evolution.py
"""

import asyncio
import os
from typing import Dict, Any

# Set environment variables for demo
os.environ["ENABLE_ELYZA_FALLBACK"] = "true"
os.environ["ELYZA_INTERNET_SEARCH"] = "true"

from elyza.elyza_model import get_elyza_model
from services.elyza_service import get_elyza_service, Language


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(query: str, result: Dict[str, Any]):
    """Print query result in a nice format"""
    print(f"\n📝 Query: {query}")
    print(f"💬 Response: {result.get('text', result.get('response', 'N/A'))}")
    print(f"🎯 Stage: {result.get('stage', 'unknown')}")
    if 'language' in result:
        print(f"🌍 Language: {result['language']}")
    if 'sentiment' in result:
        print(f"😊 Sentiment: {result['sentiment']}")
    if 'metadata' in result and 'stage_description' in result['metadata']:
        print(f"📚 Stage Info: {result['metadata']['stage_description']}")


async def demo_basic_patterns():
    """Demonstrate Stage 1: Classical ELIZA patterns"""
    print_header("Stage 1: Classical ELIZA (1960s) - Pattern Matching")
    
    service = get_elyza_service()
    
    # German greetings
    queries = [
        "Hallo!",
        "Danke für die Hilfe",
        "Tschüss",
    ]
    
    for query in queries:
        result = await service.generate_response(query, language=Language.GERMAN)
        print_result(query, result)
    
    # English greetings
    queries_en = [
        "Hello!",
        "Thank you",
        "Goodbye",
    ]
    
    print("\n--- English Patterns ---")
    for query in queries_en:
        result = await service.generate_response(query, language=Language.ENGLISH)
        print_result(query, result)


async def demo_text_analysis():
    """Demonstrate Stage 2: Text Analysis with sentiment"""
    print_header("Stage 2: Text Analysis (1990s) - NLP & Sentiment")
    
    service = get_elyza_service()
    
    queries = [
        ("Wie geht es dir?", "question"),
        ("Das ist ein Problem", "negative sentiment"),
        ("Das ist toll!", "positive sentiment"),
        ("Random unmatched text", "neutral/analysis"),
    ]
    
    for query, expected in queries:
        result = await service.generate_response(query)
        print_result(f"{query} (expecting {expected})", result)


async def demo_rag_knowledge():
    """Demonstrate Stage 3: RAG Knowledge (if enabled)"""
    print_header("Stage 3: RAG Knowledge (2020s) - Document Retrieval")
    
    model = get_elyza_model()
    
    print("\n⚙️  RAG Status:")
    info = model.get_model_info()
    rag_enabled = "rag_knowledge_retrieval" in info.get("capabilities", [])
    print(f"   RAG Enabled: {rag_enabled}")
    
    if rag_enabled:
        print("\n   Note: RAG would search document knowledge base for relevant context")
    else:
        print("\n   Note: Enable with RAG_ENABLED=true (requires vector DB setup)")
    
    # Example query that would benefit from RAG
    query = "What is the system architecture?"
    result = await model.generate(query)
    print_result(query, result)


async def demo_internet_search():
    """Demonstrate Stage 4: Internet Search (if enabled)"""
    print_header("Stage 4: Internet Search (Current) - Real-time Web")
    
    model = get_elyza_model()
    
    print("\n⚙️  Internet Search Status:")
    info = model.get_model_info()
    internet_enabled = "internet_search" in info.get("capabilities", [])
    print(f"   Internet Search Enabled: {internet_enabled}")
    
    if internet_enabled:
        print("\n   Note: Triggers on keywords like 'aktuell', 'heute', 'news', 'current', 'latest'")
    else:
        print("\n   Note: Enable with ELYZA_INTERNET_SEARCH=true")
    
    # Queries that would trigger internet search
    queries = [
        "Was sind die aktuellen News?",
        "What is the latest news today?",
        "Wie ist das Wetter heute?",
    ]
    
    for query in queries:
        result = await model.generate(query)
        print_result(query, result)


async def demo_context_management():
    """Demonstrate per-user context management"""
    print_header("Context Management - Conversation Memory")
    
    service = get_elyza_service()
    user_id = "demo_user_123"
    
    print(f"\n👤 User: {user_id}")
    print(f"📊 Initial context size: {len(service.get_context(user_id))}")
    
    # Have a conversation
    conversation = [
        "Hallo!",
        "Wie geht es dir?",
        "Was kannst du tun?",
    ]
    
    for i, msg in enumerate(conversation, 1):
        result = await service.generate_response(msg, user_id=user_id)
        print(f"\n{i}. User: {msg}")
        print(f"   Elyza: {result['response']}")
        print(f"   Context size: {len(service.get_context(user_id))}")
    
    # Clear context
    service.clear_context(user_id)
    print(f"\n🧹 Context cleared")
    print(f"📊 Final context size: {len(service.get_context(user_id))}")


async def demo_statistics():
    """Show usage statistics"""
    print_header("Service Statistics")
    
    service = get_elyza_service()
    stats = service.get_stats()
    
    print("\n📊 Overall Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Active Users: {stats['active_users']}")
    print(f"   Patterns: {stats['patterns_count']}")
    
    print("\n🎯 Stage Usage Breakdown:")
    for stage, count in stats['stage_usage'].items():
        print(f"   {stage}: {count} requests")
    
    print("\n⚙️  Stages Status:")
    for stage, enabled in stats['stages_enabled'].items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"   {stage}: {status}")


async def demo_evolution_info():
    """Show the evolution stages information"""
    print_header("AI Evolution Timeline")
    
    model = get_elyza_model()
    info = model.get_model_info()
    
    print("\n🕰️  Evolution Stages (Joseph Weizenbaum's ELIZA → Today):")
    print()
    
    stages = info.get('evolution_stages', {})
    for stage_key, description in stages.items():
        print(f"   {stage_key}:")
        print(f"      {description}")
        print()


async def main():
    """Run all demonstrations"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        🤖 ELYZA - Evolutionary AI Playground Demo 🤖          ║
    ║                                                                ║
    ║   Demonstrating 60 Years of AI Evolution (1964 - 2024)       ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n🎯 What you'll see:")
    print("   • Classical ELIZA pattern matching (1960s)")
    print("   • Text analysis and sentiment detection (1990s)")
    print("   • RAG knowledge retrieval (2020s)")
    print("   • Internet search capability (Current)")
    print("   • Context management and statistics")
    
    try:
        # Show evolution info first
        await demo_evolution_info()
        
        # Demonstrate each stage
        await demo_basic_patterns()
        await demo_text_analysis()
        await demo_rag_knowledge()
        await demo_internet_search()
        
        # Show advanced features
        await demo_context_management()
        await demo_statistics()
        
        # Final summary
        print_header("Demo Complete ✅")
        print("\n✨ The ELYZA Evolutionary Playground demonstrates:")
        print("   1. How AI has evolved from simple patterns to complex systems")
        print("   2. Progressive fallback through different AI generations")
        print("   3. Rich metadata about which 'era' of AI answered each query")
        print("   4. Backward compatibility - classical patterns still work!")
        print()
        print("💡 Philosophy: What if ELIZA had never stopped evolving?")
        print()
        print("📚 See docs/ELYZA_EVOLUTIONARY_PLAYGROUND.md for full documentation")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
