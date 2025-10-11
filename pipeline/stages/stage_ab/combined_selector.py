"""
Stage AB - Combined Understanding & Selection (Semantic Retrieval)
Merges Stage A (intent classification) and Stage B (tool selection) into a single, more reliable stage.

NEW ARCHITECTURE (pgvector + minimal index):
1. Use semantic retrieval (pgvector) to build candidate shortlist
2. Send MINIMAL index (id, name, desc, tags, platform, cost) to LLM
3. LLM selects tool IDs only
4. Stage AC loads full specs for selected IDs

This eliminates token limit issues and scales to 500+ tools.

Confidence: 0.93 | Doubt: Token estimates ±10-15%; keep 10% safety margin
"""

import time
import uuid
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, RiskLevel, ConfidenceLevel, DecisionType
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy
from llm.client import LLMClient, LLMRequest
from llm.response_parser import ResponseParser
from pipeline.services.tool_catalog_service import ToolCatalogService
from pipeline.services.tool_index_service import ToolIndexService
from pipeline.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class CombinedSelector:
    """
    Combined Stage AB - Understanding & Selection
    
    This stage replaces the old Stage A + Stage B pipeline with a single, more reliable stage that:
    1. Understands user intent
    2. Extracts entities
    3. Identifies required capabilities
    4. Queries database for matching tools
    5. Selects the best tool(s)
    6. Assesses risk and confidence
    
    All in ONE pass, with full context visible to the LLM.
    """
    
    def __init__(self, llm_client: LLMClient, tool_catalog: Optional[ToolCatalogService] = None):
        self.llm_client = llm_client
        self.response_parser = ResponseParser()
        self.version = "3.0.0"  # Semantic retrieval version
        
        # Initialize services
        self.tool_catalog = tool_catalog or ToolCatalogService()
        self.tool_index = ToolIndexService()
        self.embedding_service = get_embedding_service()
        
        # Configuration
        self.config = {
            "max_tools_per_selection": 5,
            "min_selection_confidence": 0.3,
            "temperature": 0.1,  # Low temperature for consistent decisions
            "max_tokens": 1000,
            "use_semantic_retrieval": True,  # Enable semantic retrieval
            "fallback_to_keyword": True  # Fallback if embeddings fail
        }
    
    async def process(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> SelectionV1:
        """
        Main processing method - NEW SEMANTIC RETRIEVAL ARCHITECTURE
        
        Pipeline:
        1. Generate query embedding
        2. Retrieve candidates from tool_index (semantic + keyword)
        3. Apply token budget
        4. Send MINIMAL index to LLM (id, name, desc, tags, platform, cost)
        5. LLM selects tool IDs only
        6. Log telemetry
        
        Args:
            user_request: Original user request string
            context: Optional context information
            
        Returns:
            SelectionV1 with selected tools and execution policy
        """
        start_time = time.time()
        request_id = self._generate_selection_id()
        
        try:
            logger.info(f"🧠 Stage AB (v3.0): Processing request: {user_request[:100]}...")
            
            # Step 1: Generate query embedding (if semantic retrieval enabled)
            retrieval_start = time.time()
            query_embedding = None
            
            if self.config["use_semantic_retrieval"]:
                try:
                    query_embedding = self.embedding_service.embed_text(user_request)
                    logger.info(f"✅ Generated query embedding ({len(query_embedding)}d)")
                except Exception as e:
                    logger.warning(f"⚠️  Embedding generation failed: {str(e)}, falling back to keyword search")
                    if not self.config["fallback_to_keyword"]:
                        raise
            
            # Step 2: Calculate token budget
            budget_tokens, max_rows = self.tool_index.calculate_token_budget()
            logger.info(f"📊 Token budget: {budget_tokens} tokens, max_rows={max_rows}")
            
            # Step 3: Retrieve candidates from tool_index
            # Extract platform filter from context if available
            platform_filter = context.get("platform") if context else None
            
            candidates = self.tool_index.retrieve_candidates(
                query_text=user_request,
                query_embedding=query_embedding,
                platform_filter=platform_filter,
                max_rows=max_rows
            )
            
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)
            candidates_before_budget = len(candidates)  # Already budgeted in retrieve_candidates
            
            logger.info(f"🔍 Retrieved {len(candidates)} candidates in {retrieval_time_ms}ms")
            
            # Step 4: Create minimal index prompt
            prompt = self._create_minimal_index_prompt(user_request, candidates, context)
            
            # Step 5: Single LLM call for tool selection (IDs only)
            llm_start = time.time()
            llm_request = LLMRequest(
                prompt=prompt["user"],
                system_prompt=prompt["system"],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )
            
            logger.info("🤖 Stage AB: Calling LLM for tool selection...")
            response = await self.llm_client.generate(llm_request)
            llm_time_ms = int((time.time() - llm_start) * 1000)
            
            # Step 6: Parse the response (IDs + intent)
            parsed = self._parse_minimal_response(response.content)
            logger.info(f"✅ Stage AB: Parsed response - intent={parsed['intent']['category']}/{parsed['intent']['action']}, tools={len(parsed['selected_tools'])}")
            
            # Log detailed tool selection
            if parsed['selected_tools']:
                logger.info("🔧 TOOLS SELECTED BY LLM:")
                for i, tool in enumerate(parsed['selected_tools'], 1):
                    tool_id = tool.get('id', 'unknown')
                    why = tool.get('why', 'no reason')
                    logger.info(f"   {i}. {tool_id} - {why}")
            else:
                logger.info("ℹ️  No tools selected - information-only request")
            
            # Step 7: Validate selected tool IDs exist in tool_index
            validated_tools = await self._validate_tool_ids(parsed['selected_tools'])
            
            # Log validated tools
            if validated_tools:
                logger.info("✅ VALIDATED TOOLS:")
                for i, tool in enumerate(validated_tools, 1):
                    logger.info(f"   {i}. {tool.tool_name} (order: {tool.execution_order})")
            else:
                logger.info("⚠️  No tools validated")
            
            # Step 8: Build execution policy
            execution_policy = self._build_execution_policy(
                parsed['risk_level'],
                parsed['intent'],
                validated_tools,
                context
            )
            
            # Step 9: Determine additional inputs needed
            additional_inputs = self._calculate_additional_inputs(
                parsed['entities'],
                validated_tools
            )
            
            # Step 10: Determine environment requirements
            env_requirements = self._determine_environment_requirements(validated_tools)
            
            # Step 11: Determine next stage
            next_stage = self._determine_next_stage(validated_tools, execution_policy)
            
            # Step 12: Calculate telemetry
            total_time_ms = int((time.time() - start_time) * 1000)
            rows_sent = len(candidates)
            budget_used = rows_sent * self.tool_index.TOKENS_PER_ROW_EST
            headroom_left = int(((self.tool_index.CTX - budget_used - self.tool_index.BASE_TOKENS) / self.tool_index.CTX) * 100)
            
            # Step 13: Log telemetry
            selected_tool_ids = [t.tool_name for t in validated_tools]
            self.tool_index.log_telemetry(
                request_id=request_id,
                user_intent=user_request,
                catalog_size=candidates_before_budget,  # Approximate
                candidates_before_budget=candidates_before_budget,
                rows_sent=rows_sent,
                budget_used=budget_used,
                headroom_left=headroom_left,
                selected_tool_ids=selected_tool_ids,
                retrieval_time_ms=retrieval_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms
            )
            
            # Step 14: Build SelectionV1 response
            processing_time = total_time_ms
            
            selection = SelectionV1(
                selection_id=self._generate_selection_id(),
                decision_id=self._generate_decision_id(),  # Generate decision ID for compatibility
                timestamp=datetime.now(timezone.utc).isoformat(),
                selected_tools=validated_tools,
                total_tools=len(validated_tools),
                policy=execution_policy,
                additional_inputs_needed=additional_inputs,
                environment_requirements=env_requirements,
                processing_time_ms=processing_time,
                selection_confidence=parsed['confidence'],
                next_stage=next_stage,
                ready_for_execution=self._is_ready_for_execution(validated_tools, additional_inputs)
            )
            
            logger.info(f"✅ Stage AB: Complete in {processing_time}ms - {len(validated_tools)} tools selected, next_stage={next_stage}")
            return selection
            
        except Exception as e:
            logger.error(f"❌ Stage AB: Failed to process request: {str(e)}")
            raise RuntimeError(f"Combined understanding + selection failed: {str(e)}") from e
    
    def _create_minimal_index_prompt(self, user_request: str, candidates: List[Dict[str, Any]], 
                                     context: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create prompt with MINIMAL tool index (NEW ARCHITECTURE).
        
        Sends only: id, name, desc, tags, platform, cost
        LLM returns: tool IDs only
        
        Args:
            user_request: User's request
            candidates: Candidate tools from tool_index (already token-budgeted)
            context: Optional context
            
        Returns:
            Dict with 'system' and 'user' prompts
        """
        # Format minimal index for prompt
        tools_json = json.dumps(candidates, indent=2)
        
        system_prompt = """You are OpsConductor's tool selector. Your job is to select the minimal set of tools needed to fulfill the user's request.

**RULES:**
1. Choose the FEWEST tools that provide the required capabilities
2. Prefer tools with broader coverage over multiple narrow tools
3. If no tools apply, return an empty selection
4. Return tool IDs only (not full specs)

**OUTPUT FORMAT:**
Return JSON with this exact structure:
{
  "intent": {
    "category": "system|network|automation|monitoring|security|information",
    "action": "query|execute|configure|monitor|analyze"
  },
  "entities": [
    {"type": "hostname|service|path|etc", "value": "extracted_value"}
  ],
  "select": [
    {"id": "tool-id", "why": "brief reason"}
  ],
  "confidence": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "reasoning": "brief explanation"
}"""
        
        user_prompt = f"""**USER REQUEST:**
{user_request}

**AVAILABLE TOOLS:**
{tools_json}

**YOUR TASK:**
Analyze the request and select the appropriate tool IDs. Return JSON only."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def _parse_minimal_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse LLM response with minimal tool selection (IDs only).
        
        Expected format:
        {
          "intent": {...},
          "entities": [...],
          "select": [{"id": "tool-id", "why": "reason"}],
          "confidence": 0.9,
          "risk_level": "low",
          "reasoning": "..."
        }
        
        Args:
            response_content: LLM response text
            
        Returns:
            Parsed dictionary
        """
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["intent", "select", "confidence", "risk_level"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults for optional fields
            if "entities" not in parsed:
                parsed["entities"] = []
            if "reasoning" not in parsed:
                parsed["reasoning"] = "No reasoning provided"
            
            # Convert "select" to "selected_tools" for compatibility
            parsed["selected_tools"] = parsed.pop("select", [])
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}\nResponse: {response_content}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    
    async def _validate_tool_ids(self, selected_tools: List[Dict[str, Any]]) -> List[SelectedTool]:
        """
        Validate that selected tool IDs exist in tool_catalog.
        
        Args:
            selected_tools: List of {"id": "tool-id", "why": "reason"}
            
        Returns:
            List of validated SelectedTool objects
        """
        validated = []
        
        for idx, selected in enumerate(selected_tools):
            tool_id = selected.get("id")
            why = selected.get("why", "No reason provided")
            
            # Check if tool exists in catalog
            try:
                tool_meta = self.tool_catalog.get_tool_by_name(tool_id)
                if not tool_meta:
                    logger.warning(f"LLM selected non-existent tool: {tool_id}, skipping")
                    continue
                
                # Create SelectedTool object
                validated.append(SelectedTool(
                    tool_name=tool_id,
                    justification=why,
                    inputs_needed=[],  # Will be determined by Stage C
                    execution_order=idx + 1,
                    depends_on=[]  # Will be determined by Stage C
                ))
                
            except Exception as e:
                logger.warning(f"Failed to validate tool {tool_id}: {str(e)}")
                continue
        
        return validated
    

    
    def _build_execution_policy(self, risk_level: str, intent: Dict[str, Any], 
                               selected_tools: List[SelectedTool],
                               context: Optional[Dict[str, Any]]) -> ExecutionPolicy:
        """
        Build execution policy based on risk and intent
        """
        from pipeline.schemas.decision_v1 import RiskLevel
        
        # Convert string to RiskLevel enum
        try:
            risk_enum = RiskLevel(risk_level.lower())
        except ValueError:
            risk_enum = RiskLevel.LOW
        
        # Determine if approval is required
        requires_approval = risk_enum in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Determine if rollback is required
        rollback_required = risk_enum in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Determine max execution time based on tools
        max_execution_time = 300  # 5 minutes default
        if len(selected_tools) > 3:
            max_execution_time = 600  # 10 minutes for complex operations
        
        # Check if production environment
        production_environment = context.get("environment") == "production" if context else False
        
        # Determine if parallel execution is safe
        parallel_execution = len(selected_tools) > 1 and risk_enum == RiskLevel.LOW
        
        return ExecutionPolicy(
            requires_approval=requires_approval,
            production_environment=production_environment,
            risk_level=risk_enum,
            max_execution_time=max_execution_time,
            parallel_execution=parallel_execution,
            rollback_required=rollback_required
        )
    
    def _calculate_additional_inputs(self, entities: List[Dict[str, Any]], 
                                    selected_tools: List[SelectedTool]) -> List[str]:
        """
        Calculate additional inputs needed beyond what's already extracted
        """
        # Collect all inputs needed by tools
        needed_inputs = set()
        for tool in selected_tools:
            needed_inputs.update(tool.inputs_needed)
        
        # Determine what's already available from entities
        available_inputs = {"user_request", "timestamp"}
        for entity in entities:
            entity_type = entity.get("type", "")
            if entity_type == "service":
                available_inputs.update(["service_name", "service"])
            elif entity_type == "hostname":
                available_inputs.update(["hostname", "host", "target"])
            elif entity_type == "command":
                available_inputs.update(["command", "cmd"])
            elif entity_type == "file_path":
                available_inputs.update(["path", "file"])
            elif entity_type == "port":
                available_inputs.add("port")
            elif entity_type == "environment":
                available_inputs.update(["environment", "env"])
        
        # Return missing inputs
        missing = list(needed_inputs - available_inputs)
        return missing
    
    def _determine_environment_requirements(self, selected_tools: List[SelectedTool]) -> Dict[str, Any]:
        """
        Determine environment requirements based on selected tools
        """
        requirements = {
            "sudo_required": False,
            "dependencies": []
        }
        
        # Check for sudo requirements (based on common tool patterns)
        sudo_tools = ["systemctl", "iptables", "useradd", "usermod", "apt", "yum"]
        for tool in selected_tools:
            if any(sudo_tool in tool.tool_name.lower() for sudo_tool in sudo_tools):
                requirements["sudo_required"] = True
                break
        
        return requirements
    
    def _determine_next_stage(self, selected_tools: List[SelectedTool], 
                             policy: ExecutionPolicy) -> str:
        """
        Determine the next pipeline stage
        
        ROUTING LOGIC:
        - No tools selected → Stage D (information-only response)
        - Tools selected → Stage C (create execution plan)
        
        The risk level and approval requirements affect HOW execution happens,
        not WHETHER execution happens. If the user requested an action and we
        selected tools, we should execute them.
        """
        # If no tools selected, go directly to answerer (information-only)
        if not selected_tools:
            return "stage_d"
        
        # If tools were selected, they need to be executed
        # Route to Stage C (Planner) to create an execution plan
        # The planner will handle approval requirements, risk mitigation, etc.
        return "stage_c"
    
    def _is_ready_for_execution(self, selected_tools: List[SelectedTool], 
                               additional_inputs: List[str]) -> bool:
        """
        Check if selection is ready for immediate execution
        """
        # Not ready if missing inputs
        if additional_inputs:
            return False
        
        # Not ready if no tools selected (information-only is "ready" but doesn't execute)
        if not selected_tools:
            return True  # Information-only requests are ready to answer
        
        # Not ready if tools have unresolved dependencies
        tool_names = {tool.tool_name for tool in selected_tools}
        for tool in selected_tools:
            for dependency in tool.depends_on:
                if dependency not in tool_names:
                    return False
        
        return True
    
    def _generate_selection_id(self) -> str:
        """Generate unique selection ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"sel_{timestamp}_{unique_id}"
    
    def _generate_decision_id(self) -> str:
        """Generate unique decision ID (for compatibility)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"dec_{timestamp}_{unique_id}"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Stage AB components
        """
        health_status = {
            "stage_ab": "healthy",
            "version": self.version,
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Check LLM connectivity
            llm_healthy = await self.llm_client.health_check()
            health_status["components"]["llm_client"] = "healthy" if llm_healthy else "unhealthy"
            
            # Check tool catalog
            try:
                tools = await self.tool_catalog.get_all_tools()
                health_status["components"]["tool_catalog"] = f"healthy ({len(tools)} tools)"
            except Exception as e:
                health_status["components"]["tool_catalog"] = f"unhealthy: {str(e)}"
            
            # Overall health
            if not llm_healthy:
                health_status["stage_ab"] = "degraded"
            
        except Exception as e:
            health_status["stage_ab"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status