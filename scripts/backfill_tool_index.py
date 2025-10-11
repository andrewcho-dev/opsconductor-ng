#!/usr/bin/env python3
"""
Backfill Tool Index
Populates tool_catalog.tool_index from existing tool_catalog.tools.

Usage:
    python scripts/backfill_tool_index.py

Confidence: 0.9 | Doubt: Embedding model download may take time
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.services.embedding_service import get_embedding_service
from pipeline.services.tool_index_service import ToolIndexService
from pipeline.services.tool_catalog_service import ToolCatalogService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main backfill function."""
    logger.info("=" * 80)
    logger.info("TOOL INDEX BACKFILL")
    logger.info("=" * 80)
    
    try:
        # Initialize services
        logger.info("🔧 Initializing services...")
        embedding_service = get_embedding_service()
        tool_index_service = ToolIndexService()
        tool_catalog_service = ToolCatalogService()
        
        # Get all tools from database
        logger.info("📚 Loading tools from database...")
        tools = tool_catalog_service.get_all_tools_with_structure()
        logger.info(f"   Found {len(tools)} tools")
        
        if not tools:
            logger.warning("⚠️  No tools found in database. Nothing to backfill.")
            return
        
        # Generate tool index entries with embeddings
        logger.info("🔄 Generating embeddings and preparing entries...")
        index_entries = embedding_service.backfill_tool_index(tools, batch_size=32)
        logger.info(f"   Generated {len(index_entries)} entries")
        
        # Bulk insert into tool_index
        logger.info("💾 Inserting entries into tool_index...")
        inserted = tool_index_service.bulk_insert_tool_index(index_entries)
        logger.info(f"   Inserted {inserted} entries")
        
        # Summary
        logger.info("=" * 80)
        logger.info("✅ BACKFILL COMPLETE")
        logger.info(f"   Tools processed: {len(tools)}")
        logger.info(f"   Entries inserted: {inserted}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Backfill failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()