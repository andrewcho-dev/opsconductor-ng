"""
Embedding Service for Tool Index
Generates and manages embeddings for semantic tool retrieval in Stage AB.

Uses sentence-transformers with bge-base-en-v1.5 (768d) for high-quality embeddings.
Fallback to bge-small-en-v1.5 (384d) if memory constrained.

Confidence: 0.9 | Doubt: Model download may fail; needs error handling
"""

import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings for tool semantic search.
    
    Uses sentence-transformers with BGE models (BAAI General Embedding).
    """
    
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5", dimension: int = 768):
        """
        Initialize embedding service.
        
        Args:
            model_name: HuggingFace model name
            dimension: Expected embedding dimension (768 for base, 384 for small)
        """
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self._initialized = False
        
        logger.info(f"🔧 EmbeddingService: Initializing with model={model_name}, dim={dimension}")
    
    def _lazy_init(self):
        """Lazy initialization of the model (only when first needed)"""
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"📦 Loading embedding model: {self.model_name}")
            
            # Set cache directory to avoid re-downloading
            cache_dir = os.getenv("TRANSFORMERS_CACHE", "/tmp/transformers_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            self.model = SentenceTransformer(self.model_name, cache_folder=cache_dir)
            self._initialized = True
            
            logger.info(f"✅ Embedding model loaded successfully (dim={self.dimension})")
            
        except ImportError:
            logger.error("❌ sentence-transformers not installed. Run: pip install sentence-transformers")
            raise RuntimeError("sentence-transformers package required for embeddings")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {str(e)}")
            raise RuntimeError(f"Failed to initialize embedding model: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        self._lazy_init()
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, normalize_embeddings=True)
            
            # Convert to list and validate dimension
            embedding_list = embedding.tolist()
            
            if len(embedding_list) != self.dimension:
                raise ValueError(f"Expected {self.dimension}d embedding, got {len(embedding_list)}d")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {str(e)}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}")
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        self._lazy_init()
        
        try:
            logger.info(f"🔄 Generating embeddings for {len(texts)} texts (batch_size={batch_size})")
            
            # Generate embeddings in batches
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 100
            )
            
            # Convert to list of lists
            embeddings_list = [emb.tolist() for emb in embeddings]
            
            logger.info(f"✅ Generated {len(embeddings_list)} embeddings")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"❌ Failed to generate batch embeddings: {str(e)}")
            raise RuntimeError(f"Batch embedding generation failed: {str(e)}")
    
    def format_tool_for_embedding(self, tool: Dict[str, Any]) -> str:
        """
        Format a tool dictionary into a text string optimized for embedding.
        
        Format: "{name} | {desc_short} | {tags_csv} | {platform}"
        
        Args:
            tool: Tool dictionary with name, desc_short, tags, platform
            
        Returns:
            Formatted string for embedding
        """
        name = tool.get("name", "unknown")
        desc_short = tool.get("desc_short", "")
        tags = tool.get("tags", [])
        platform = tool.get("platform", "misc")
        
        # Join tags with commas
        tags_csv = ", ".join(tags) if tags else "misc"
        
        # Format: name | description | tags | platform
        formatted = f"{name} | {desc_short} | {tags_csv} | {platform}"
        
        return formatted
    
    def prepare_tool_for_index(self, tool_from_db: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a tool from the database for insertion into tool_index.
        
        Extracts and formats:
        - id (tool_name)
        - name (truncated to 48 chars)
        - desc_short (truncated to 110 chars)
        - platform
        - tags (max 6, extracted from metadata)
        - cost_hint (derived from metadata)
        
        Args:
            tool_from_db: Tool dictionary from tool_catalog.tools
            
        Returns:
            Dictionary ready for tool_index insertion (without embedding)
        """
        tool_name = tool_from_db.get("tool_name", "unknown")
        description = tool_from_db.get("description", "")
        platform = tool_from_db.get("platform", "misc")
        metadata = tool_from_db.get("metadata", {})
        
        # Truncate name to 48 chars
        name = tool_name[:45] + "..." if len(tool_name) > 48 else tool_name
        
        # Truncate description to 110 chars (strict one-liner)
        desc_short = description[:107] + "..." if len(description) > 110 else description
        
        # Extract tags from metadata (max 6)
        tags = metadata.get("tags", [])
        if not tags:
            tags = ["misc"]
        tags = tags[:6]  # Limit to 6 tags
        
        # Derive cost_hint from metadata
        cost_hint = "med"  # Default
        if metadata.get("production_safe") is False:
            cost_hint = "high"
        elif metadata.get("requires_sudo") is True:
            cost_hint = "high"
        elif "read" in description.lower() or "query" in description.lower():
            cost_hint = "low"
        
        return {
            "id": tool_name,
            "name": name,
            "desc_short": desc_short,
            "platform": platform,
            "tags": tags,
            "cost_hint": cost_hint
        }
    
    def generate_tool_index_entry(self, tool_from_db: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete tool_index entry with embedding.
        
        Args:
            tool_from_db: Tool dictionary from tool_catalog.tools
            
        Returns:
            Complete dictionary ready for tool_index insertion (with embedding)
        """
        # Prepare base fields
        index_entry = self.prepare_tool_for_index(tool_from_db)
        
        # Format for embedding
        text_for_embedding = self.format_tool_for_embedding(index_entry)
        
        # Generate embedding
        embedding = self.embed_text(text_for_embedding)
        
        # Add embedding to entry
        index_entry["emb"] = embedding
        
        return index_entry
    
    def backfill_tool_index(self, tools_from_db: List[Dict[str, Any]], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Backfill tool_index from existing tools in database.
        
        Args:
            tools_from_db: List of tool dictionaries from tool_catalog.tools
            batch_size: Batch size for embedding generation
            
        Returns:
            List of tool_index entries ready for insertion
        """
        logger.info(f"🔄 Backfilling tool_index for {len(tools_from_db)} tools")
        
        # Prepare all entries (without embeddings)
        index_entries = []
        texts_for_embedding = []
        
        for tool in tools_from_db:
            entry = self.prepare_tool_for_index(tool)
            index_entries.append(entry)
            texts_for_embedding.append(self.format_tool_for_embedding(entry))
        
        # Generate embeddings in batch
        embeddings = self.embed_batch(texts_for_embedding, batch_size=batch_size)
        
        # Add embeddings to entries
        for entry, embedding in zip(index_entries, embeddings):
            entry["emb"] = embedding
        
        logger.info(f"✅ Backfill complete: {len(index_entries)} entries ready")
        
        return index_entries


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "BAAI/bge-base-en-v1.5", dimension: int = 768) -> EmbeddingService:
    """
    Get or create the singleton embedding service instance.
    
    Args:
        model_name: HuggingFace model name
        dimension: Expected embedding dimension
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name=model_name, dimension=dimension)
    
    return _embedding_service