#!/usr/bin/env python3
"""
Tool catalog upsert utility.

Reads YAML tool definitions and upserts them into the database with embeddings.
Supports dry-run mode for validation before actual writes.

Usage:
    python tools/tools_upsert.py --dsn postgresql://... --glob "config/tools/**/*.yaml"
    python tools/tools_upsert.py --dry-run  # Preview changes without writing
    
Environment:
    DATABASE_URL: Default database connection string
"""

import argparse
import asyncio
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import asyncpg
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from selector.embeddings import EmbeddingProvider


async def load_yaml_tool(filepath: str) -> Optional[dict[str, Any]]:
    """
    Load and validate a tool definition from YAML file.
    
    Args:
        filepath: Path to YAML file
        
    Returns:
        Tool dict with validated fields, or None if invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            print(f"⚠️  Empty file: {filepath}")
            return None
        
        # Validate required fields
        required = ['key', 'name', 'short_desc']
        missing = [field for field in required if field not in data]
        if missing:
            print(f"❌ Validation error in {filepath}: Missing required fields {missing}")
            return None
        
        # Validate field types and values
        if not isinstance(data['key'], str) or not data['key'].strip():
            print(f"❌ Validation error in {filepath}: 'key' must be a non-empty string")
            return None
        if not isinstance(data['name'], str) or not data['name'].strip():
            print(f"❌ Validation error in {filepath}: 'name' must be a non-empty string")
            return None
        if not isinstance(data['short_desc'], str) or not data['short_desc'].strip():
            print(f"❌ Validation error in {filepath}: 'short_desc' must be a non-empty string")
            return None
        
        # Ensure proper types and defaults
        short_desc = data['short_desc'][:160]  # Truncate to 160 chars
        platform = data.get('platform', [])
        platform = platform if isinstance(platform, list) else []
        tags = data.get('tags', [])
        tags = tags if isinstance(tags, list) else []
        meta = data.get('meta', {})
        meta = meta if isinstance(meta, dict) else {}
        
        tool = {
            'key': data['key'],
            'name': data['name'],
            'short_desc': short_desc,
            'platform': platform,
            'tags': tags,
            'meta': meta,
        }
        
        return tool
        
    except yaml.YAMLError as e:
        print(f"⚠️  YAML parse error in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Error loading {filepath}: {e}")
        return None


def to_vec_literal(vec: list[float]) -> str:
    """Convert a vector to PostgreSQL vector literal format with 6 decimal places."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


async def upsert_tool(
    conn: asyncpg.Connection,
    tool: dict[str, Any],
    provider: EmbeddingProvider,
    dry_run: bool = False
) -> bool:
    """
    Upsert a single tool into the database.
    
    Args:
        conn: Database connection
        tool: Tool dictionary with key, name, short_desc, platform, tags, meta
        provider: Embedding provider for generating embeddings
        dry_run: If True, only print what would be done
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract and validate fields
        key = tool['key']
        name = tool['name']
        short_desc = tool['short_desc'][:160]
        platform = tool['platform'] if isinstance(tool['platform'], list) else []
        tags = tool['tags'] if isinstance(tool['tags'], list) else []
        meta = tool['meta'] if isinstance(tool['meta'], dict) else {}
        
        # Serialize meta to JSON string
        meta_json = json.dumps(meta, separators=(",", ":"))
        
        # Generate embedding from key + " :: " + short_desc
        embed_text = f"{key} :: {short_desc}"
        embedding = await provider.embed(embed_text)
        
        # Ensure embedding is 128-dimensional
        if len(embedding) != 128:
            print(f"  ❌ Error: Expected 128-dimensional embedding, got {len(embedding)} for {key}")
            return False
        
        # Convert embedding to PostgreSQL vector literal
        vec_lit = to_vec_literal(embedding)
        
        if dry_run:
            print(f"  📝 Would upsert: {key}")
            print(f"     name: {name}")
            print(f"     short_desc: {short_desc}")
            print(f"     platform: {platform}")
            print(f"     tags: {tags}")
            print(f"     meta: {meta}")
            print(f"     embedding: [{embedding[0]:.4f}, {embedding[1]:.4f}, ... {len(embedding)} dims]")
            return True
        
        # Execute UPSERT with explicit casts
        await conn.execute(
            """
            INSERT INTO tool (key, name, short_desc, platform, tags, meta, embedding, updated_at)
            VALUES ($1, $2, $3, $4::text[], $5::text[], $6::jsonb, CAST($7 AS vector(128)), now())
            ON CONFLICT (key) DO UPDATE
            SET name = EXCLUDED.name,
                short_desc = EXCLUDED.short_desc,
                platform = EXCLUDED.platform,
                tags = EXCLUDED.tags,
                meta = EXCLUDED.meta,
                embedding = EXCLUDED.embedding,
                updated_at = now();
            """,
            key, name, short_desc, platform, tags, meta_json, vec_lit
        )
        
        print(f"  ✅ Upserted: {key}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error upserting {tool.get('key', 'unknown')}: {e}")
        return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upsert tool definitions from YAML files into database"
    )
    parser.add_argument(
        '--dsn',
        default=os.getenv('DATABASE_URL'),
        help='Database connection string (default: DATABASE_URL env var)'
    )
    parser.add_argument(
        '--glob',
        default='config/tools/**/*.yaml',
        help='Glob pattern for YAML files (default: config/tools/**/*.yaml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to database'
    )
    
    args = parser.parse_args()
    
    if not args.dsn:
        print("❌ Error: No database connection string provided")
        print("   Set DATABASE_URL env var or use --dsn flag")
        sys.exit(1)
    
    # Find all YAML files
    yaml_files = glob.glob(args.glob, recursive=True)
    if not yaml_files:
        print(f"⚠️  No YAML files found matching pattern: {args.glob}")
        sys.exit(0)
    
    print(f"📂 Found {len(yaml_files)} YAML file(s)")
    
    # Load all tools
    tools = []
    for filepath in sorted(yaml_files):
        tool = await load_yaml_tool(filepath)
        if tool:
            tools.append((filepath, tool))
    
    if not tools:
        print("⚠️  No valid tool definitions found")
        sys.exit(0)
    
    print(f"✅ Loaded {len(tools)} valid tool definition(s)")
    
    # Initialize embedding provider
    provider = EmbeddingProvider()
    
    # Connect to database (skip if dry-run)
    conn = None
    if not args.dry_run:
        try:
            conn = await asyncpg.connect(dsn=args.dsn)
            print(f"🔌 Connected to database")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
    
    # Process each tool
    print(f"\n{'🔍 DRY RUN MODE' if args.dry_run else '💾 UPSERTING TOOLS'}:")
    print("=" * 60)
    
    success_count = 0
    for filepath, tool in tools:
        print(f"\n📄 {filepath}")
        if await upsert_tool(conn, tool, provider, dry_run=args.dry_run):
            success_count += 1
    
    # Cleanup
    if conn:
        await conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"✅ Dry run complete: {success_count}/{len(tools)} tools validated")
        print("   Run without --dry-run to write to database")
    else:
        print(f"✅ Upsert complete: {success_count}/{len(tools)} tools written")
    
    sys.exit(0 if success_count == len(tools) else 1)


if __name__ == '__main__':
    asyncio.run(main())