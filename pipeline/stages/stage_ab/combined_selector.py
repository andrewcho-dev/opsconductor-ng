"""
Stage AB - Combined Understanding & Selection
Merges Stage A (intent classification) and Stage B (tool selection) into a single, more reliable stage.

This eliminates the fragile handoff between stages and allows the LLM to see the full context
when making tool selection decisions.
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, EntityV1, RiskLevel, ConfidenceLevel, DecisionType
from pipeline.schemas.selection_v1 import SelectionV1, SelectedTool, ExecutionPolicy
from llm.client import LLMClient, LLMRequest
from llm.response_parser import ResponseParser
from pipeline.services.tool_catalog_service import ToolCatalogService

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
        self.version = "2.0.0"
        
        # Initialize tool catalog service (database-backed)
        self.tool_catalog = tool_catalog or ToolCatalogService()
        
        # Configuration
        self.config = {
            "max_tools_per_selection": 5,
            "min_selection_confidence": 0.3,
            "temperature": 0.1,  # Low temperature for consistent decisions
            "max_tokens": 1000
        }
    
    async def process(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> SelectionV1:
        """
        Main processing method - combines understanding and selection
        
        Args:
            user_request: Original user request string
            context: Optional context information
            
        Returns:
            SelectionV1 with selected tools and execution policy
        """
        start_time = time.time()
        
        try:
            logger.info(f"🧠 Stage AB: Processing request: {user_request[:100]}...")
            
            # Step 1: Get available tools from database
            # We need to know what tools exist before we can select them
            all_tools = await self._get_available_tools()
            logger.info(f"📚 Stage AB: Loaded {len(all_tools)} tools from database")
            
            # Step 2: Create combined prompt that does EVERYTHING in one pass
            prompt = self._create_combined_prompt(user_request, all_tools, context)
            
            # Step 3: Single LLM call for understanding + selection
            llm_request = LLMRequest(
                prompt=prompt["user"],
                system_prompt=prompt["system"],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )
            
            logger.info("🤖 Stage AB: Calling LLM for combined understanding + selection...")
            response = await self.llm_client.generate(llm_request)
            
            # Step 4: Parse the combined response
            parsed = self._parse_combined_response(response.content)
            logger.info(f"✅ Stage AB: Parsed response - intent={parsed['intent']['category']}/{parsed['intent']['action']}, tools={len(parsed['selected_tools'])}")
            
            # Log detailed tool selection
            if parsed['selected_tools']:
                logger.info("🔧 TOOLS SELECTED BY LLM:")
                for i, tool in enumerate(parsed['selected_tools'], 1):
                    tool_name = tool.get('tool_name', 'unknown')
                    confidence = tool.get('confidence', 0.0)
                    logger.info(f"   {i}. {tool_name} (confidence: {confidence:.2f})")
            else:
                logger.info("ℹ️  No tools selected - information-only request")
            
            # Step 5: Validate selected tools exist in database
            validated_tools = await self._validate_and_enrich_tools(parsed['selected_tools'], all_tools)
            
            # Log validated tools
            if validated_tools:
                logger.info("✅ VALIDATED TOOLS:")
                for i, tool in enumerate(validated_tools, 1):
                    logger.info(f"   {i}. {tool.tool_name} (order: {tool.execution_order})")
            else:
                logger.info("⚠️  No tools validated")
            
            # Step 6: Build execution policy
            execution_policy = self._build_execution_policy(
                parsed['risk_level'],
                parsed['intent'],
                validated_tools,
                context
            )
            
            # Step 7: Determine additional inputs needed
            additional_inputs = self._calculate_additional_inputs(
                parsed['entities'],
                validated_tools
            )
            
            # Step 8: Determine environment requirements
            env_requirements = self._determine_environment_requirements(validated_tools)
            
            # Step 9: Determine next stage
            next_stage = self._determine_next_stage(validated_tools, execution_policy)
            
            # Step 10: Build SelectionV1 response
            processing_time = int((time.time() - start_time) * 1000)
            
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
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get all available tools from database
        
        Returns:
            List of tool dictionaries with metadata
        """
        try:
            # Get all tools with full structure (capabilities + patterns) from database
            tools = self.tool_catalog.get_all_tools_with_structure()
            
            # Format for LLM consumption (simplified view)
            formatted_tools = []
            for tool in tools:
                # Extract typical use cases from patterns (they're stored at pattern level)
                typical_use_cases = []
                capabilities = tool.get("capabilities", {})
                if isinstance(capabilities, dict):
                    for cap_name, cap_data in capabilities.items():
                        if isinstance(cap_data, dict) and 'patterns' in cap_data:
                            for pattern in cap_data['patterns']:
                                if pattern.get('typical_use_cases'):
                                    typical_use_cases.extend(pattern['typical_use_cases'])
                
                # Remove duplicates while preserving order
                seen = set()
                unique_use_cases = []
                for uc in typical_use_cases:
                    if uc not in seen:
                        seen.add(uc)
                        unique_use_cases.append(uc)
                
                formatted_tools.append({
                    "tool_name": tool["tool_name"],
                    "description": tool["description"],
                    "capabilities": tool.get("capabilities", {}),
                    "typical_use_cases": unique_use_cases,
                    "platform": tool.get("platform", "any"),
                    "category": tool.get("category", "custom"),
                    "production_safe": tool.get("production_safe", False),
                    "requires_sudo": tool.get("requires_sudo", False)
                })
            
            return formatted_tools
            
        except Exception as e:
            logger.error(f"Failed to load tools from database: {str(e)}")
            # Return empty list - LLM will handle information-only requests
            return []
    
    def _create_combined_prompt(self, user_request: str, available_tools: List[Dict[str, Any]], 
                                context: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create a combined prompt that does understanding + selection in one pass
        
        This is the key innovation: instead of two separate LLM calls (Stage A → Stage B),
        we do ONE call that sees the full context.
        """
        
        # Format tools for the prompt (compact representation)
        tools_summary = self._format_tools_for_prompt(available_tools)
        
        system_prompt = f"""You are OpsConductor's AI brain. Analyze the user's request and select the appropriate tool(s) to fulfill it.

**YOUR TASK:**
1. Understand the user's intent (what they want to do)
2. Extract any technical entities (hostnames, services, etc.)
3. Identify required capabilities
4. Select the best tool(s) from the available tools
5. Assess confidence and risk

**AVAILABLE TOOLS:**
{tools_summary}

**RESPONSE FORMAT (JSON):**
{{
  "intent": {{
    "category": "automation|monitoring|troubleshooting|configuration|information|asset_management",
    "action": "specific_action_name",
    "capabilities": ["capability1", "capability2"]
  }},
  "entities": [
    {{"type": "hostname|service|command|file_path|port|environment|application|database", "value": "actual_value", "confidence": 0.0-1.0}}
  ],
  "selected_tools": [
    {{
      "tool_name": "exact_tool_name_from_available_tools",
      "justification": "why this tool is appropriate",
      "inputs_needed": ["input1", "input2"],
      "execution_order": 1
    }}
  ],
  "confidence": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "reasoning": "brief explanation of your decision"
}}

**CRITICAL RULES:**
1. **Data Questions REQUIRE Tools**: If the user asks about real data (how many assets, what's the status, show me logs), you MUST select a tool. NEVER make up data.
2. **Asset Questions → asset-query tool**: Questions about assets, servers, hosts, inventory ALWAYS use the "asset-query" tool.
3. **Information-Only Requests**: Only return empty selected_tools[] for conceptual questions (what is X?, how does Y work?, explain Z).
4. **Tool Names Must Match**: Only use tool_name values that exist in the AVAILABLE TOOLS list above.
5. **Capabilities Must Match**: The capabilities you list must match what the selected tool provides.

**RISK LEVELS:**
- low: Read-only operations, status checks, information queries
- medium: Service restarts, configuration changes, non-destructive operations
- high: Database operations, system-wide changes, production modifications
- critical: Data deletion, irreversible operations, production-wide impact

**EXAMPLES:**

User: "How many assets do we have?"
→ Select "asset-query" tool (this is a DATA question, not conceptual)

User: "What is the status of nginx?"
→ Select appropriate monitoring tool (DATA question)

User: "What is Kubernetes?"
→ No tools needed (CONCEPTUAL question)

User: "Restart the web server"
→ Select appropriate service management tool (ACTION)"""

        user_prompt = f"""Analyze this request and select appropriate tool(s):

**USER REQUEST:** {user_request}

**CONTEXT:** {context or {}}

Return your analysis in the JSON format specified above."""

        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        Format tools into a compact, LLM-friendly representation
        
        IMPORTANT: List TOOL NAMES first (not capabilities) to avoid LLM confusion
        """
        if not tools:
            return "No tools available (information-only mode)"
        
        # Format as simple list: TOOL_NAME first, then capabilities
        lines = []
        for tool in sorted(tools, key=lambda t: t.get("tool_name", "")):
            tool_name = tool.get("tool_name", "unknown")
            description = tool.get("description", "")[:100]
            
            # Extract capability names
            capabilities = tool.get("capabilities", {})
            if isinstance(capabilities, dict):
                cap_names = list(capabilities.keys())
            elif isinstance(capabilities, list):
                cap_names = capabilities
            else:
                cap_names = []
            
            # Get use cases
            use_cases = tool.get("typical_use_cases", [])[:2]
            use_cases_str = ", ".join(use_cases) if use_cases else "general use"
            
            # Format: TOOL_NAME (capabilities) - description [use cases]
            caps_str = ", ".join(cap_names) if cap_names else "no capabilities"
            lines.append(f"- **{tool_name}** (capabilities: {caps_str})")
            lines.append(f"  Description: {description}")
            if use_cases:
                lines.append(f"  Use cases: {use_cases_str}")
            lines.append("")  # Blank line between tools
        
        return "\n".join(lines)
    
    def _parse_combined_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the combined LLM response
        
        Returns:
            Dictionary with intent, entities, selected_tools, confidence, risk_level, reasoning
        """
        import json
        import re
        
        try:
            # Try to extract JSON from response
            # LLM might wrap it in markdown code blocks
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
            required_fields = ["intent", "selected_tools", "confidence", "risk_level"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults for optional fields
            if "entities" not in parsed:
                parsed["entities"] = []
            if "reasoning" not in parsed:
                parsed["reasoning"] = "No reasoning provided"
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}\nResponse: {response_content}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    
    async def _validate_and_enrich_tools(self, selected_tools: List[Dict[str, Any]], 
                                        all_tools: List[Dict[str, Any]]) -> List[SelectedTool]:
        """
        Validate that selected tools exist and enrich with database metadata
        
        Args:
            selected_tools: Tools selected by LLM
            all_tools: All available tools from database
            
        Returns:
            List of validated SelectedTool objects
        """
        validated = []
        tool_lookup = {t["tool_name"]: t for t in all_tools}
        
        for idx, selected in enumerate(selected_tools):
            tool_name = selected.get("tool_name")
            
            # Check if tool exists
            if tool_name not in tool_lookup:
                logger.warning(f"LLM selected non-existent tool: {tool_name}, skipping")
                continue
            
            # Get full tool metadata from database
            tool_meta = tool_lookup[tool_name]
            
            # Create SelectedTool object
            validated.append(SelectedTool(
                tool_name=tool_name,
                justification=selected.get("justification", f"Selected for {tool_name}"),
                inputs_needed=selected.get("inputs_needed", []),
                execution_order=selected.get("execution_order", idx + 1),
                depends_on=selected.get("depends_on", [])
            ))
        
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