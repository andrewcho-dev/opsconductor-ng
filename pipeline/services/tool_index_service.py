"""
Tool Index Service
Handles database operations for tool_index table (semantic retrieval).

Provides:
- Semantic search (vector similarity)
- Keyword/tag search (fallback)
- Token-budgeted retrieval
- Telemetry logging

Confidence: 0.93 | Doubt: Token estimates ±10-15%; keep 10% safety margin
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import os

logger = logging.getLogger(__name__)


class ToolIndexService:
    """
    Service for tool_index operations (semantic retrieval for Stage AB).
    """
    
    # Token budgeting constants (adjust as needed)
    CTX = 8192  # vLLM context window
    HEADROOM = 0.30  # Reserve 30% for model output
    BASE_TOKENS = 900  # System + instructions + user text (measure actual)
    TOKENS_PER_ROW_EST = 95  # Increased from 45 to account for JSON formatting and all fields
    
    # Recall constants - KEEP THESE LOW for precision!
    VECTOR_TOP_K = 10  # Vector similarity top-K (reduced from 15)
    KEYWORD_TOP_K = 10  # Keyword/tag fallback top-K (reduced from 60)
    SIMILARITY_THRESHOLD = 0.50  # Minimum similarity score to include (balanced precision/recall)
    ALWAYS_INCLUDE = ["asset-query"]  # Always include these tools
    
    def __init__(self):
        """Initialize tool index service."""
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "opsconductor"),
            "user": os.getenv("POSTGRES_USER", "opsconductor"),
            "password": os.getenv("POSTGRES_PASSWORD", "opsconductor_secure_2024")
        }
        logger.info("🔧 ToolIndexService: Initialized")
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)
    
    def calculate_token_budget(self, base_tokens: Optional[int] = None) -> Tuple[int, int]:
        """
        Calculate token budget for tool index rows.
        
        Args:
            base_tokens: Override BASE_TOKENS if provided
            
        Returns:
            Tuple of (budget_tokens, max_rows)
        """
        base = base_tokens or self.BASE_TOKENS
        budget = self.CTX - int(self.CTX * self.HEADROOM) - base
        max_rows = max(10, int(budget / self.TOKENS_PER_ROW_EST))
        
        logger.debug(f"📊 Token budget: {budget} tokens, max_rows={max_rows}")
        
        return budget, max_rows
    
    def vector_search(
        self,
        query_embedding: List[float],
        platform_filter: Optional[str] = None,
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on tool_index.
        
        Args:
            query_embedding: Query embedding vector
            platform_filter: Optional platform filter (windows, linux, etc.)
            top_k: Number of results to return
            
        Returns:
            List of tool index entries with similarity scores (filtered by threshold)
        """
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query with optional platform filter and similarity threshold
            if platform_filter:
                query = """
                    SELECT id, name, desc_short, platform, tags, cost_hint,
                           1 - (emb <=> %s::vector) AS similarity
                    FROM tool_catalog.tool_index
                    WHERE (platform = %s OR platform = 'multi-platform')
                      AND (1 - (emb <=> %s::vector)) >= %s
                    ORDER BY emb <=> %s::vector
                    LIMIT %s
                """
                cursor.execute(query, (query_embedding, platform_filter, query_embedding, 
                                     self.SIMILARITY_THRESHOLD, query_embedding, top_k))
            else:
                query = """
                    SELECT id, name, desc_short, platform, tags, cost_hint,
                           1 - (emb <=> %s::vector) AS similarity
                    FROM tool_catalog.tool_index
                    WHERE (1 - (emb <=> %s::vector)) >= %s
                    ORDER BY emb <=> %s::vector
                    LIMIT %s
                """
                cursor.execute(query, (query_embedding, query_embedding, 
                                     self.SIMILARITY_THRESHOLD, query_embedding, top_k))
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"🔍 Vector search: {len(results)} results (similarity >= {self.SIMILARITY_THRESHOLD}) in {elapsed_ms}ms")
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {str(e)}")
            return []
    
    def keyword_search(
        self,
        query_text: str,
        platform_filter: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword/tag search on tool_index (fallback).
        
        Args:
            query_text: Query text for keyword matching
            platform_filter: Optional platform filter
            top_k: Number of results to return
            
        Returns:
            List of tool index entries
        """
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Extract keywords (simple split)
            keywords = [kw.lower() for kw in query_text.split() if len(kw) > 2]
            
            # Build ILIKE conditions
            ilike_conditions = []
            params = []
            
            for kw in keywords[:5]:  # Limit to 5 keywords
                ilike_conditions.append("(name ILIKE %s OR desc_short ILIKE %s OR %s = ANY(tags))")
                params.extend([f"%{kw}%", f"%{kw}%", kw])
            
            if not ilike_conditions:
                return []
            
            where_clause = " OR ".join(ilike_conditions)
            
            if platform_filter:
                where_clause = f"({where_clause}) AND (platform = %s OR platform = 'multi-platform')"
                params.append(platform_filter)
            
            query = f"""
                SELECT id, name, desc_short, platform, tags, cost_hint
                FROM tool_catalog.tool_index
                WHERE {where_clause}
                LIMIT %s
            """
            params.append(top_k)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"🔍 Keyword search: {len(results)} results in {elapsed_ms}ms")
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {str(e)}")
            return []
    
    def get_always_include_tools(self) -> List[Dict[str, Any]]:
        """
        Get tools that should always be included (e.g., asset-query).
        
        Returns:
            List of tool index entries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT id, name, desc_short, platform, tags, cost_hint
                FROM tool_catalog.tool_index
                WHERE id = ANY(%s)
            """
            cursor.execute(query, (self.ALWAYS_INCLUDE,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"❌ Failed to get always-include tools: {str(e)}")
            return []
    
    def retrieve_candidates(
        self,
        query_text: str,
        query_embedding: Optional[List[float]] = None,
        platform_filter: Optional[str] = None,
        max_rows: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve candidate tools using union of multiple strategies.
        
        Pipeline:
        1. Vector Top-K (if embedding provided)
        2. Keyword/Tag Top-K (fallback)
        3. Always-include IDs
        4. Union → de-dup → slice to max_rows
        
        Args:
            query_text: User query text
            query_embedding: Optional query embedding for vector search
            platform_filter: Optional platform filter
            max_rows: Maximum rows to return (token budget)
            
        Returns:
            List of tool index entries (de-duplicated, token-budgeted)
        """
        start_time = time.time()
        
        # Calculate token budget if not provided
        if max_rows is None:
            _, max_rows = self.calculate_token_budget()
        
        logger.info(f"🔍 Retrieving candidates: max_rows={max_rows}, platform={platform_filter}")
        
        # Collect candidates from multiple sources
        candidates_dict = {}  # Use dict for de-duplication by id
        
        # 1. Vector search (if embedding provided)
        if query_embedding:
            vector_results = self.vector_search(
                query_embedding,
                platform_filter=platform_filter,
                top_k=self.VECTOR_TOP_K
            )
            for result in vector_results:
                candidates_dict[result["id"]] = result
            logger.info(f"   Vector: {len(vector_results)} candidates")
        
        # 2. Keyword/tag search (fallback ONLY if no vector search)
        # NOTE: Keyword search disabled when embeddings available to avoid noise
        if not query_embedding:
            keyword_results = self.keyword_search(
                query_text,
                platform_filter=platform_filter,
                top_k=self.KEYWORD_TOP_K
            )
            for result in keyword_results:
                if result["id"] not in candidates_dict:
                    candidates_dict[result["id"]] = result
            logger.info(f"   Keyword: {len(keyword_results)} candidates")
        else:
            logger.info(f"   Keyword: skipped (vector search available)")
        
        # 3. Always-include tools
        always_include = self.get_always_include_tools()
        for result in always_include:
            if result["id"] not in candidates_dict:
                candidates_dict[result["id"]] = result
        logger.info(f"   Always-include: {len(always_include)} candidates")
        
        # 4. De-dup and slice to max_rows
        candidates = list(candidates_dict.values())
        
        # Sort by similarity if available, otherwise by name
        if query_embedding and candidates and "similarity" in candidates[0]:
            candidates.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        else:
            candidates.sort(key=lambda x: x["name"])
        
        # Slice to token budget
        candidates_before_budget = len(candidates)
        candidates = candidates[:max_rows]
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Retrieved {len(candidates)} candidates (from {candidates_before_budget}) in {elapsed_ms}ms")
        
        return candidates
    
    def insert_tool_index_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Insert a single tool index entry.
        
        Args:
            entry: Tool index entry with id, name, desc_short, platform, tags, cost_hint, emb
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO tool_catalog.tool_index (id, name, desc_short, platform, tags, cost_hint, emb)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    desc_short = EXCLUDED.desc_short,
                    platform = EXCLUDED.platform,
                    tags = EXCLUDED.tags,
                    cost_hint = EXCLUDED.cost_hint,
                    emb = EXCLUDED.emb,
                    updated_at = now()
            """
            
            cursor.execute(query, (
                entry["id"],
                entry["name"],
                entry["desc_short"],
                entry["platform"],
                entry["tags"],
                entry["cost_hint"],
                entry["emb"]
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert tool index entry: {str(e)}")
            return False
    
    def bulk_insert_tool_index(self, entries: List[Dict[str, Any]]) -> int:
        """
        Bulk insert tool index entries.
        
        Args:
            entries: List of tool index entries
            
        Returns:
            Number of entries inserted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO tool_catalog.tool_index (id, name, desc_short, platform, tags, cost_hint, emb)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    desc_short = EXCLUDED.desc_short,
                    platform = EXCLUDED.platform,
                    tags = EXCLUDED.tags,
                    cost_hint = EXCLUDED.cost_hint,
                    emb = EXCLUDED.emb,
                    updated_at = now()
            """
            
            values = [
                (
                    entry["id"],
                    entry["name"],
                    entry["desc_short"],
                    entry["platform"],
                    entry["tags"],
                    entry["cost_hint"],
                    entry["emb"]
                )
                for entry in entries
            ]
            
            execute_values(cursor, query, values)
            
            conn.commit()
            inserted = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Bulk inserted {inserted} tool index entries")
            
            return inserted
            
        except Exception as e:
            logger.error(f"❌ Bulk insert failed: {str(e)}")
            return 0
    
    def log_telemetry(
        self,
        request_id: str,
        user_intent: str,
        catalog_size: int,
        candidates_before_budget: int,
        rows_sent: int,
        budget_used: int,
        headroom_left: int,
        selected_tool_ids: List[str],
        retrieval_time_ms: int,
        llm_time_ms: int,
        total_time_ms: int,
        executed_tool_ids: Optional[List[str]] = None,
        recall_at_k: Optional[float] = None,
        truncation_events: int = 0
    ) -> bool:
        """
        Log telemetry for Stage AB monitoring.
        
        Args:
            request_id: Unique request ID
            user_intent: User query text
            catalog_size: Total tools in catalog
            candidates_before_budget: Candidates before token budget
            rows_sent: Rows sent to LLM
            budget_used: Tokens used
            headroom_left: Tokens remaining (%)
            selected_tool_ids: Tool IDs selected by LLM
            retrieval_time_ms: Retrieval time
            llm_time_ms: LLM time
            total_time_ms: Total time
            executed_tool_ids: Tool IDs actually executed (optional)
            recall_at_k: Recall metric (optional)
            truncation_events: Number of truncation events
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO tool_catalog.stage_ab_telemetry (
                    request_id, user_intent, catalog_size, candidates_before_budget,
                    rows_sent, budget_used, headroom_left, selected_tool_ids,
                    executed_tool_ids, recall_at_k, truncation_events,
                    retrieval_time_ms, llm_time_ms, total_time_ms
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                request_id, user_intent, catalog_size, candidates_before_budget,
                rows_sent, budget_used, headroom_left, selected_tool_ids,
                executed_tool_ids, recall_at_k, truncation_events,
                retrieval_time_ms, llm_time_ms, total_time_ms
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Check for alerts
            if headroom_left < 15:
                logger.warning(f"⚠️  Low headroom: {headroom_left}% remaining")
            if recall_at_k is not None and recall_at_k < 0.98:
                logger.warning(f"⚠️  Low recall: {recall_at_k:.2f}")
            if truncation_events > 0:
                logger.error(f"❌ Truncation events: {truncation_events}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log telemetry: {str(e)}")
            return False