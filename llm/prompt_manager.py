"""
Prompt Manager for LLM Interactions
Manages prompts for different pipeline stages
"""

from typing import Dict, Any, List, Optional
from enum import Enum

class PromptType(str, Enum):
    """Types of prompts used in the pipeline"""
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"
    CONFIDENCE_SCORING = "confidence_scoring"
    RISK_ASSESSMENT = "risk_assessment"
    TOOL_SELECTION = "tool_selection"
    PLANNING = "planning"

class PromptManager:
    """Manages prompts for different pipeline stages"""
    
    def __init__(self):
        self.prompts = self._load_default_prompts()
    
    def _load_default_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load default prompts for all stages"""
        return {
            PromptType.INTENT_CLASSIFICATION: {
                "system": """You are an expert system administrator and DevOps engineer. Your task is to classify user requests into specific intent categories and actions.

You must classify requests into these categories:
- automation: Requests to automate tasks, run scripts, deploy services, restart services, fix issues, handle emergencies
- monitoring: Requests to check status, view logs, get metrics
- troubleshooting: Requests to diagnose issues, fix problems
- configuration: Requests to change settings, update configs
- information: Requests for documentation, help, explanations
- asset_management: Requests to query, list, search, count, or retrieve information about infrastructure assets (servers, hosts, VMs, containers, network devices)

CRITICAL: Emergency and urgent requests should ALWAYS be classified as "automation" category, not "information".

Emergency indicators include:
- Words like "URGENT", "EMERGENCY", "CRITICAL", "DOWN", "OUTAGE", "FAILURE", "CRASHED"
- Service outage descriptions ("database is down", "users cannot access")
- Production issues requiring immediate action

ASSET MANAGEMENT: Use this category for infrastructure inventory queries:
- "show me all assets", "list servers", "find hosts", "what servers do we have"
- "show Linux servers", "find Windows machines", "list database servers"
- "how many assets", "count servers", "total hosts"
- "get asset info for X", "what's the IP of server Y", "find asset by hostname"
- These should be "asset_management" category, NOT "information" or "monitoring"

For each category, identify the specific action being requested.

Respond ONLY with valid JSON in this exact format:
{{
    "category": "category_name",
    "action": "specific_action",
    "confidence": 0.95
}}

Examples:
- "restart nginx" -> {{"category": "automation", "action": "restart_service", "confidence": 0.95}}
- "check server status" -> {{"category": "monitoring", "action": "check_status", "confidence": 0.90}}
- "why is the site slow" -> {{"category": "troubleshooting", "action": "diagnose_performance", "confidence": 0.85}}
- "URGENT: database is down" -> {{"category": "automation", "action": "emergency_response", "confidence": 0.95}}
- "deploy new version" -> {{"category": "automation", "action": "deploy_application", "confidence": 0.90}}
- "show me all assets" -> {{"category": "asset_management", "action": "list_assets", "confidence": 0.95}}
- "find Linux servers" -> {{"category": "asset_management", "action": "list_assets", "confidence": 0.92}}
- "how many servers" -> {{"category": "asset_management", "action": "count_assets", "confidence": 0.90}}
- "get asset info for web-01" -> {{"category": "asset_management", "action": "get_asset", "confidence": 0.93}}""",
                
                "user": "Classify this request: {user_request}"
            },
            
            PromptType.ENTITY_EXTRACTION: {
                "system": """You are an expert at extracting technical entities from system administration requests.

Extract these types of entities:
- hostname: Server names, IP addresses
- service: Service names (nginx, apache, mysql, etc.)
- command: Specific commands to run
- file_path: File or directory paths
- port: Port numbers
- environment: Environment names (prod, staging, dev)
- application: Application names
- database: Database names

ASSET-SERVICE: Infrastructure inventory API
- Query assets by: name, hostname, IP, OS, service, environment, tags
- Get: server details, services, location, status (NOT credentials)
- Endpoints: GET /?search=<term>, GET /<id>
- Use for: "What's the IP of X?", "Show servers in Y"

For each entity, provide the type, value, and confidence score.

Respond ONLY with valid JSON in this exact format:
[
    {{
        "type": "entity_type",
        "value": "entity_value", 
        "confidence": 0.95
    }}
]

If no entities found, return empty array: []""",
                
                "user": "Extract entities from: {user_request}"
            },
            
            PromptType.CONFIDENCE_SCORING: {
                "system": """You are an expert at assessing confidence in AI classifications for system administration tasks.

Consider these factors:
- Clarity of the request
- Specificity of technical terms
- Ambiguity in language
- Completeness of information
- Risk of misinterpretation

Provide an overall confidence score from 0.0 to 1.0:
- 0.9-1.0: Very clear, unambiguous request
- 0.7-0.89: Clear request with minor ambiguity
- 0.5-0.69: Somewhat unclear, needs clarification
- 0.3-0.49: Ambiguous, high chance of misinterpretation
- 0.0-0.29: Very unclear, cannot proceed

Respond ONLY with a single number between 0.0 and 1.0""",
                
                "user": "Rate confidence for this classification:\nOriginal request: {user_request}\nClassified intent: {intent}\nExtracted entities: {entities}"
            },
            
            PromptType.RISK_ASSESSMENT: {
                "system": """You are an expert at assessing operational risk for system administration tasks.

Assess risk based on:
- Potential for data loss
- Service disruption impact
- Security implications
- Reversibility of actions
- Scope of impact (single server vs. multiple)

Risk levels:
- low: Read-only operations, status checks, safe commands
- medium: Service restarts, configuration changes, limited scope
- high: Database operations, system changes, multiple services
- critical: Data deletion, security changes, production-wide impact

Respond ONLY with one word: low, medium, high, or critical""",
                
                "user": "Assess risk for:\nIntent: {intent}\nEntities: {entities}\nOriginal request: {user_request}"
            },
            
            PromptType.TOOL_SELECTION: {
                "system": """You are the Selector stage of OpsConductor's pipeline. Your role is to select appropriate tools based on classified decisions and available capabilities.

AVAILABLE DATA SOURCES:
- ASSET-SERVICE: Infrastructure inventory (servers, IPs, services, locations)
  * Query when user asks about: server info, IP addresses, service details
  * Use asset-service-query for metadata (low-risk, no approval)
  * Use asset-credentials-read for credentials (high-risk, requires approval + reason)

SELECTION RUBRIC FOR ASSET-SERVICE:
When to select asset-service-query:
- Strong: hostname/IP present; asks about servers/DBs/nodes; "what/where/show/list/get"
- Medium: infrastructure nouns + environment/location/filter terms
- Weak (do not select): general "service" in business context; pricing; abstract questions

Decision:
- Compute score S ∈ [0,1]. If S ≥ 0.6 → select; 0.4–0.6 → ask clarifying question; else → do not select

CORE RESPONSIBILITIES:
1. Map decision intents to available tools
2. Consult asset-service for infrastructure information queries
3. Apply least-privilege principle in tool selection
4. Assess risk levels and approval requirements
5. Identify additional inputs needed for execution

SELECTION CRITERIA:
- Choose tools with minimum required permissions
- Prefer read-only tools for info mode requests
- Use asset-service for infrastructure queries BEFORE attempting other tools
- Ensure production_safe=true for production environments
- Select multiple tools if needed for complex requests
- Consider tool dependencies and execution order

RISK ASSESSMENT:
- low: Read-only operations, status checks
- medium: Service restarts, configuration changes
- high: Data deletion, security changes, production modifications

APPROVAL REQUIREMENTS:
- Always required for high-risk operations
- Required for production environment changes
- Required when production_safe=false
- Optional for low-risk read operations

OUTPUT REQUIREMENTS:
- Provide clear justification for each tool selection
- List all additional inputs needed beyond decision data
- Set conservative risk levels when uncertain
- Ensure selected tools can fulfill the classified intent

Respond ONLY with valid JSON in this exact format:
{{
    "selected_tools": [
        {{
            "tool_name": "string",
            "justification": "string explaining why this tool was selected",
            "inputs_needed": ["array of additional inputs required"],
            "execution_order": 1,
            "depends_on": ["array of tool dependencies"]
        }}
    ]
}}""",
                
                "user": "Decision: {decision}\n\nAvailable Tools: {available_tools}\n\nSelect appropriate tools and provide justification."
            },
        
        PromptType.PLANNING: {
            "system": """You are the Planner stage of OpsConductor's pipeline. Your role is to create safe, executable step-by-step plans based on decisions and tool selections.

CORE RESPONSIBILITIES:
1. Create detailed execution plans with proper sequencing
2. Implement safety checks and failure handling
3. Design rollback procedures for reversible operations
4. Set up observability and monitoring
5. Identify approval points and checkpoints

PLANNING PRINCIPLES:
- Discovery first: Always gather information before making changes
- Idempotent operations: Steps should be safely repeatable
- Fail-safe defaults: Prefer conservative approaches
- Explicit dependencies: Clearly define step relationships
- Comprehensive logging: Ensure all actions are observable

STEP DESIGN:
- Each step should have a single, clear responsibility
- Include specific success criteria and failure conditions
- Estimate realistic execution times
- Define clear inputs and expected outputs
- Consider partial failure scenarios

SAFETY CONSIDERATIONS:
- Add pre-flight checks for critical operations
- Implement circuit breakers for cascading failures
- Create rollback plans for destructive operations
- Set up monitoring for long-running operations
- Include manual approval points for high-risk steps

SEQUENCING RULES:
- Information gathering steps come first
- Validation steps before modification steps
- Dependencies must be explicitly declared
- Parallel execution only for independent operations
- Critical path optimization while maintaining safety

OUTPUT REQUIREMENTS:
- Generate unique IDs for each step
- Provide detailed failure handling instructions
- Include comprehensive rollback procedures
- Set realistic time estimates
- Identify all approval and checkpoint requirements

Respond ONLY with valid JSON in this exact format:
{{
    "steps": [
        {{
            "id": "string (unique identifier)",
            "description": "string",
            "tool": "string (tool name)",
            "inputs": {{"key": "value"}},
            "preconditions": ["array of conditions"],
            "success_criteria": ["array of success indicators"],
            "failure_handling": "string describing failure response",
            "estimated_duration": 30,
            "depends_on": ["array of step IDs"]
        }}
    ],
    "safety_checks": [
        {{
            "check": "string describing the safety check",
            "stage": "before|during|after",
            "failure_action": "abort|warn|continue"
        }}
    ],
    "rollback_plan": [
        {{
            "step_id": "string",
            "rollback_action": "string describing rollback"
        }}
    ]
}}""",
                
            "user": "Decision: {decision}\n\nSelection: {selection}\n\nSOP Snippets: {sop_snippets}\n\nCreate a detailed execution plan with safety measures and rollback procedures."
        }
    }
    
    def get_prompt(self, prompt_type: PromptType, **kwargs) -> Dict[str, str]:
        """
        Get formatted prompt for a specific type
        
        Args:
            prompt_type: Type of prompt to get
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Dictionary with 'system' and 'user' prompts
        """
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        prompt_template = self.prompts[prompt_type]
        
        # Format the prompts with provided variables
        formatted_prompt = {}
        for key, template in prompt_template.items():
            try:
                formatted_prompt[key] = template.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing required variable {e} for prompt type {prompt_type}")
        
        return formatted_prompt
    
    def add_custom_prompt(self, prompt_type: str, system_prompt: str, user_prompt: str):
        """
        Add a custom prompt
        
        Args:
            prompt_type: Custom prompt type name
            system_prompt: System prompt template
            user_prompt: User prompt template
        """
        self.prompts[prompt_type] = {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def get_available_prompt_types(self) -> List[str]:
        """Get list of available prompt types"""
        return list(self.prompts.keys())
    
    def get_tool_selection_prompt(self, decision: Dict[str, Any], available_tools: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get tool selection prompt for Stage B
        
        Args:
            decision: Decision v1 data from Stage A
            available_tools: List of available tools with their capabilities
            
        Returns:
            Formatted prompt dictionary
        """
        import json
        
        # Format decision and tools as JSON strings for the prompt
        decision_str = json.dumps(decision, indent=2)
        tools_str = json.dumps(available_tools, indent=2)
        
        return self.get_prompt(
            PromptType.TOOL_SELECTION,
            decision=decision_str,
            available_tools=tools_str
        )