#!/usr/bin/env python3
"""
Example usage of selector.dao.select_topk function.

This script demonstrates how to use the vector-based tool selection
with pgvector semantic search.

Prerequisites:
1. Run migration: make selector.migrate
2. Populate tool table with embeddings
3. Set DATABASE_URL environment variable

Usage:
    export DATABASE_URL="postgresql://user:pass@localhost/db"
    python3 selector/example_dao_usage.py
"""

import asyncio
import os
import sys
import asyncpg

from selector.dao import select_topk
from selector.embeddings import EmbeddingProvider


async def main():
    """Demonstrate select_topk usage."""
    
    # Get database URL from environment
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        print("Example: export DATABASE_URL='postgresql://user:pass@localhost/db'", file=sys.stderr)
        sys.exit(1)
    
    # Connect to database
    print(f"Connecting to database...")
    conn = await asyncpg.connect(dsn=dsn)
    
    try:
        # Create embedding provider (uses deterministic fallback by default)
        provider = EmbeddingProvider()
        
        # Example 1: Basic search
        print("\n" + "="*70)
        print("Example 1: Basic semantic search")
        print("="*70)
        intent = "scan network for open ports and vulnerabilities"
        print(f"Intent: {intent}")
        
        results = await select_topk(conn, intent, k=5, provider=provider)
        
        print(f"\nFound {len(results)} tools:")
        for i, tool in enumerate(results, 1):
            print(f"\n{i}. {tool['key']} - {tool['name']}")
            print(f"   Description: {tool['short_desc']}")
            print(f"   Platforms: {', '.join(tool['platform']) if tool['platform'] else 'N/A'}")
            print(f"   Tags: {', '.join(tool['tags']) if tool['tags'] else 'N/A'}")
        
        # Example 2: Platform-filtered search
        print("\n" + "="*70)
        print("Example 2: Search with platform filter")
        print("="*70)
        intent = "deploy containerized application"
        platforms = ["docker", "kubernetes"]
        print(f"Intent: {intent}")
        print(f"Platforms: {platforms}")
        
        results = await select_topk(
            conn,
            intent,
            platform=platforms,
            k=5,
            provider=provider
        )
        
        print(f"\nFound {len(results)} tools:")
        for i, tool in enumerate(results, 1):
            print(f"\n{i}. {tool['key']} - {tool['name']}")
            print(f"   Description: {tool['short_desc']}")
            print(f"   Platforms: {', '.join(tool['platform']) if tool['platform'] else 'N/A'}")
        
        # Example 3: Different k values
        print("\n" + "="*70)
        print("Example 3: Varying result count (k parameter)")
        print("="*70)
        intent = "monitor system performance"
        
        for k in [3, 5, 10]:
            results = await select_topk(conn, intent, k=k, provider=provider)
            print(f"\nk={k}: Found {len(results)} tools")
            if results:
                print(f"  Top result: {results[0]['key']} - {results[0]['name']}")
        
        # Example 4: Show that same intent gives same results (deterministic)
        print("\n" + "="*70)
        print("Example 4: Deterministic results")
        print("="*70)
        intent = "backup database"
        
        results1 = await select_topk(conn, intent, k=3, provider=provider)
        results2 = await select_topk(conn, intent, k=3, provider=provider)
        
        print(f"Query 1: {[r['key'] for r in results1]}")
        print(f"Query 2: {[r['key'] for r in results2]}")
        print(f"Results match: {results1 == results2}")
        
    finally:
        await conn.close()
        print("\n" + "="*70)
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())