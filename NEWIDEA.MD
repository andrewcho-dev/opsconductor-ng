# OpsConductor Multi-Stage Pipeline Architecture Complete Documentation

## Overview

OpsConductor implements a sophisticated multi-stage pipeline architecture for automated operations tasks. The system processes user requests through multiple specialized stages, each with distinct responsibilities and well-defined input/output schemas.

## Pipeline Stages

### Stage A - Classifier

**Purpose**: Initial processing stage that converts user requests into structured decisions.

**Input Schema**:
```json
{
  "user_request": "string (natural language)",
  "context": {
    "logs": "optional string",
    "configs": "optional string", 
    "alerts": "optional string",
    "other": "optional string"
  }
}
```

**Output Schema - Decision v1**:
```json
{
  "mode": "info|act|clarify",
  "intent": "string (classified intent)",
  "confidence": "float 0-1",
  "entities": {
    "hosts": ["array of strings"],
    "services": ["array of strings"],
    "actions": ["array of strings"],
    "other": "object with extracted entities"
  },
  "missing_fields": ["array of required fields not provided"],
  "clarification_needed": "optional string explaining what needs clarification"
}
```

**System Prompt**:
```
You are the Classifier stage of OpsConductor's pipeline. Your role is to analyze user requests and convert them into structured decisions.

CORE RESPONSIBILITIES:
1. Parse natural language requests into structured format
2. Classify intent from predefined categories
3. Extract relevant entities (hosts, services, actions)
4. Determine if request is informational, actionable, or needs clarification
5. Assess confidence in classification

CLASSIFICATION RULES:
- Use "info" mode for read-only requests (status checks, logs, monitoring)
- Use "act" mode for operations that modify system state
- Use "clarify" mode when request is ambiguous or missing critical information
- Confidence must be >= 0.7 for "act" mode, >= 0.5 for "info" mode
- If confidence is below threshold, use "clarify" mode

INTENT CATEGORIES:
- system_status: Check system health, resource usage, service status
- log_analysis: Retrieve and analyze logs
- service_management: Start, stop, restart services
- configuration_management: Update configs, deploy changes
- troubleshooting: Diagnose and fix issues
- monitoring: Set up alerts, check metrics
- security: Security scans, access management
- unknown: When intent cannot be classified

ENTITY EXTRACTION:
- Extract hostnames, IP addresses, service names
- Identify specific actions requested
- Capture time ranges, file paths, configuration keys
- Note any constraints or conditions

OUTPUT REQUIREMENTS:
- Always return valid JSON matching Decision v1 schema
- Include confidence score with 2 decimal precision
- List missing critical information in missing_fields
- Provide clear clarification requests when needed
```

**User Content Template**:
```
Request: {user_request}

Context:
{context}

Classify this request and extract relevant information.
```

### Stage B - Selector

**Purpose**: Tool selection stage that maps classified decisions to available capabilities.

**Input Schema**:
```json
{
  "decision": "Decision v1 object from Stage A",
  "capabilities": {
    "tools": [
      {
        "name": "string",
        "description": "string",
        "capabilities": ["array of strings"],
        "required_inputs": ["array of strings"],
        "permissions": "string (read|write|admin)",
        "production_safe": "boolean"
      }
    ]
  }
}
```

**Output Schema**:
```json
{
  "selected_tools": [
    {
      "tool_name": "string",
      "justification": "string explaining why this tool was selected",
      "inputs_needed": ["array of additional inputs required"]
    }
  ],
  "policy": {
    "requires_approval": "boolean",
    "production_environment": "boolean",
    "risk_level": "low|medium|high",
    "max_execution_time": "integer seconds"
  },
  "additional_inputs_needed": ["array of inputs not available from decision"]
}
```

**System Prompt**:
```
You are the Selector stage of OpsConductor's pipeline. Your role is to select appropriate tools based on classified decisions and available capabilities.

CORE RESPONSIBILITIES:
1. Map decision intents to available tools
2. Apply least-privilege principle in tool selection
3. Assess risk levels and approval requirements
4. Identify additional inputs needed for execution

SELECTION CRITERIA:
- Choose tools with minimum required permissions
- Prefer read-only tools for info mode requests
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

POLICY SETTINGS:
- Set production_environment=true if targeting production systems
- Set appropriate max_execution_time based on operation complexity
- Consider cascading effects and dependencies

OUTPUT REQUIREMENTS:
- Provide clear justification for each tool selection
- List all additional inputs needed beyond decision data
- Set conservative risk levels when uncertain
- Ensure selected tools can fulfill the classified intent
```

**User Content Template**:
```
Decision: {decision}

Available Capabilities: {capabilities}

Select appropriate tools and set execution policy.
```

### Stage C - Planner

**Purpose**: Planning stage that creates safe, executable step-by-step plans.

**Input Schema**:
```json
{
  "decision": "Decision v1 object",
  "selection": "Selection object from Stage B",
  "sop_snippets": "optional array of relevant SOP procedures"
}
```

**Output Schema**:
```json
{
  "plan": {
    "steps": [
      {
        "id": "string (unique identifier)",
        "description": "string",
        "tool": "string (tool name)",
        "inputs": "object with tool-specific inputs",
        "preconditions": ["array of conditions that must be met"],
        "success_criteria": ["array of success indicators"],
        "failure_handling": "string describing what to do on failure",
        "estimated_duration": "integer seconds",
        "depends_on": ["array of step IDs this step depends on"]
      }
    ],
    "safety_checks": [
      {
        "check": "string describing the safety check",
        "stage": "before|during|after",
        "failure_action": "abort|warn|continue"
      }
    ],
    "rollback_plan": [
      {
        "step_id": "string",
        "rollback_action": "string describing how to undo this step"
      }
    ],
    "observability": {
      "metrics_to_collect": ["array of metrics"],
      "logs_to_monitor": ["array of log sources"],
      "alerts_to_set": ["array of alert conditions"]
    }
  },
  "execution_metadata": {
    "total_estimated_time": "integer seconds",
    "risk_factors": ["array of identified risks"],
    "approval_points": ["array of step IDs requiring approval"],
    "checkpoint_steps": ["array of step IDs for progress checkpoints"]
  }
}
```

**System Prompt**:
```
You are the Planner stage of OpsConductor's pipeline. Your role is to create safe, executable step-by-step plans based on decisions and tool selections.

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
```

**User Content Template**:
```
Decision: {decision}
Selection: {selection}
SOP Snippets: {sop_snippets}

Create a detailed execution plan with safety measures and rollback procedures.
```

### Stage D - Answerer (Optional)

**Purpose**: Information-only response generation using RAG (Retrieval-Augmented Generation).

**Input Schema**:
```json
{
  "decision": "Decision v1 object with mode='info'",
  "retrieved_snippets": [
    {
      "source": "string (document/log source)",
      "content": "string (relevant content)",
      "relevance_score": "float 0-1"
    }
  ]
}
```

**Output Schema**:
```json
{
  "response": "string (human-readable answer)",
  "sources": ["array of sources used"],
  "confidence": "float 0-1",
  "additional_actions_suggested": ["array of follow-up suggestions"]
}
```

**System Prompt**:
```
You are the Answerer stage of OpsConductor's pipeline. Your role is to provide comprehensive, accurate responses to informational requests using retrieved context.

CORE RESPONSIBILITIES:
1. Synthesize information from multiple sources
2. Provide clear, actionable answers
3. Cite sources appropriately
4. Suggest relevant follow-up actions
5. Maintain accuracy and relevance

RESPONSE GUIDELINES:
- Use clear, professional language
- Structure information logically
- Highlight key findings and insights
- Include relevant metrics and data points
- Provide context for technical information

SOURCE HANDLING:
- Prioritize high-relevance sources
- Cross-reference information when possible
- Note any conflicting information
- Cite specific sources for claims
- Indicate confidence levels for uncertain information

FOLLOW-UP SUGGESTIONS:
- Recommend related monitoring actions
- Suggest preventive measures
- Identify areas needing attention
- Propose optimization opportunities
- Highlight potential issues

OUTPUT REQUIREMENTS:
- Provide comprehensive yet concise responses
- Include confidence assessment
- List all sources consulted
- Offer actionable next steps
- Maintain professional tone throughout
```

**User Content Template**:
```
Original Question: {decision.user_request}

Retrieved Information:
{retrieved_snippets}

Provide a comprehensive answer using the available information.
```

## JSON Repair Prompt

**Purpose**: Specialized repair mechanism for invalid JSON outputs.

**System Prompt**:
```
You are a JSON repair specialist. Your ONLY job is to fix invalid JSON to match the required schema.

RULES:
1. Output ONLY valid JSON - no explanations, no prose, no markdown
2. Fix syntax errors (missing quotes, brackets, commas)
3. Ensure all required fields are present
4. Use appropriate data types for each field
5. Maintain original intent while ensuring validity
6. Add missing required fields with reasonable defaults
7. Remove invalid fields not in schema

REPAIR STRATEGIES:
- Add missing quotes around strings
- Fix bracket/brace mismatches
- Remove trailing commas
- Escape special characters in strings
- Convert invalid types to correct types
- Add required fields with null/empty defaults
- Remove extra fields not in schema

OUTPUT: Return only the repaired JSON object.
```

## Router Implementation Notes

**For AI Coder Implementation**:

### Pipeline Orchestration
1. **Stage Validation**: Use Pydantic models or JSON-Schema validation for all inputs/outputs
2. **Error Handling**: Implement retry logic with exponential backoff for transient failures
3. **State Management**: Persist pipeline state between stages for debugging and recovery
4. **Logging**: Comprehensive logging at each stage with correlation IDs

### Execution Flow
1. **Classifier Stage**: Always first, validates and structures user input
2. **Selector Stage**: Maps decisions to available tools and capabilities
3. **Planner Stage**: Creates detailed execution plans with safety measures
4. **Answerer Stage**: Only for info mode requests, provides direct responses
5. **Execution Engine**: Executes plans from Planner stage with proper monitoring

### Special Handling
1. **Clarification Requests**: Return to user with specific questions when mode="clarify"
2. **Approval Workflows**: Pause execution at approval points, wait for human confirmation
3. **Failure Recovery**: Implement rollback procedures and partial failure handling
4. **Production Safety**: Extra validation and approval for production environments

### Integration Points
1. **RBAC Integration**: Validate user permissions before tool selection
2. **Audit Logging**: Record all decisions, selections, and executions
3. **Monitoring Integration**: Real-time status updates and progress tracking
4. **Notification System**: Alerts for failures, approvals needed, and completions

### Configuration Management
1. **Capability Manifests**: Dynamic loading of available tools and their capabilities
2. **SOP Integration**: Retrieve relevant procedures based on intent classification
3. **Policy Engine**: Configurable rules for risk assessment and approval requirements
4. **Environment Detection**: Automatic detection of production vs. non-production environments

## Example Usage

### Request: "Connect to 192.168.50.211 and get the complete system status"

**Stage A Output**:
```json
{
  "mode": "info",
  "intent": "system_status",
  "confidence": 0.95,
  "entities": {
    "hosts": ["192.168.50.211"],
    "services": [],
    "actions": ["connect", "get_status"]
  },
  "missing_fields": [],
  "clarification_needed": null
}
```

**Stage B Input (Capabilities)**:
```json
{
  "tools": [
    {
      "name": "ssh_connector",
      "description": "Secure shell connection to remote hosts",
      "capabilities": ["remote_connection", "command_execution"],
      "required_inputs": ["host", "credentials"],
      "permissions": "read",
      "production_safe": true
    },
    {
      "name": "system_monitor",
      "description": "System status and resource monitoring",
      "capabilities": ["cpu_usage", "memory_usage", "disk_usage", "service_status"],
      "required_inputs": ["connection"],
      "permissions": "read",
      "production_safe": true
    }
  ]
}
```

**Stage B Output**:
```json
{
  "selected_tools": [
    {
      "tool_name": "ssh_connector",
      "justification": "Required to establish connection to target host",
      "inputs_needed": ["credentials"]
    },
    {
      "tool_name": "system_monitor",
      "justification": "Provides comprehensive system status information",
      "inputs_needed": []
    }
  ],
  "policy": {
    "requires_approval": false,
    "production_environment": false,
    "risk_level": "low",
    "max_execution_time": 300
  },
  "additional_inputs_needed": ["ssh_credentials"]
}
```

**Stage C Input (SOP Snippets)**:
```json
[
  {
    "title": "System Status Check Procedure",
    "content": "1. Verify host connectivity\n2. Check CPU, memory, disk usage\n3. Verify critical services status\n4. Check system logs for errors\n5. Report findings in structured format"
  }
]
```

**Stage C Output**:
```json
{
  "plan": {
    "steps": [
      {
        "id": "step_001",
        "description": "Establish SSH connection to target host",
        "tool": "ssh_connector",
        "inputs": {
          "host": "192.168.50.211",
          "port": 22,
          "timeout": 30
        },
        "preconditions": ["Host is reachable", "Valid credentials provided"],
        "success_criteria": ["SSH connection established", "Authentication successful"],
        "failure_handling": "Retry with different credentials or report connection failure",
        "estimated_duration": 10,
        "depends_on": []
      },
      {
        "id": "step_002",
        "description": "Gather comprehensive system status",
        "tool": "system_monitor",
        "inputs": {
          "connection": "step_001_output",
          "checks": ["cpu", "memory", "disk", "services", "logs"]
        },
        "preconditions": ["SSH connection active"],
        "success_criteria": ["All system metrics collected", "Service status retrieved"],
        "failure_handling": "Continue with partial data collection if some checks fail",
        "estimated_duration": 60,
        "depends_on": ["step_001"]
      }
    ],
    "safety_checks": [
      {
        "check": "Verify host is not in maintenance mode",
        "stage": "before",
        "failure_action": "warn"
      },
      {
        "check": "Monitor connection stability during execution",
        "stage": "during",
        "failure_action": "abort"
      }
    ],
    "rollback_plan": [
      {
        "step_id": "step_001",
        "rollback_action": "Close SSH connection cleanly"
      }
    ],
    "observability": {
      "metrics_to_collect": ["connection_time", "data_collection_time", "success_rate"],
      "logs_to_monitor": ["ssh_logs", "system_monitor_logs"],
      "alerts_to_set": ["connection_timeout", "authentication_failure"]
    }
  },
  "execution_metadata": {
    "total_estimated_time": 70,
    "risk_factors": ["Network connectivity issues", "Authentication failures"],
    "approval_points": [],
    "checkpoint_steps": ["step_001"]
  }
}
```

This comprehensive architecture provides a robust foundation for automated operations with proper safety measures, approval workflows, and comprehensive observability throughout the execution pipeline.

## Scaling to Complex Multi-Step Operations

Yes—this exact pattern scales to multi-step, complex jobs. The trick is to keep the LLM's "thinking" modular, while your executor handles graph semantics (fan-out, retries, rollbacks, approvals). Here's how it works at scale:

### Why it scales

**Hierarchical planning**: Run A→B→C (Classifier→Selector→Planner) repeatedly: the Planner can emit subplans (HTN style). Your executor resolves each subplan into a DAG.

**Graph, not script**: Plans are DAGs with typed nodes, dependencies, branches, and loops. The LLM outputs structured JSON; your engine enforces order, parallelism, retries, and rollbacks.

**Iterative refinement**: After any step finishes, you can feed step results back into the Planner for re-planning (e.g., if a canary fails, generate a rollback path).

**Safety stays outside**: RBAC, approvals, environment fences, and schema validation still gate every complex plan.

### Minimal extensions for complex jobs

**1) Add DAG fields to the Plan schema**

```json
{
  "depends_on": ["stepA","stepB"],
  "strategy": { 
    "retries": 3, 
    "backoff_s": 5, 
    "timeout_s": 300, 
    "continue_on_fail": false 
  },
  "branch": { 
    "when": "<expr>", 
    "then": ["id1"], 
    "else": ["id2"] 
  },
  "foreach": { 
    "items": ["web-01","web-02"], 
    "param": "target" 
  },
  "gather": { 
    "from": ["idA[*]"], 
    "reduce": "all_success|any_success|concat" 
  },
  "checkpoint": true
}
```

**2) Planner prompt tweak**

Tell the Planner: "Prefer canary → batch → full rollout, include verify after each batch, and provide a rollback path."

**3) Executor responsibilities**

- Build the DAG, run nodes with parallelism, retries, and timeouts.
- Evaluate branch/loop expressions against real outputs.
- Stop or rollback on policy triggers.
- Persist artifacts and expose them to the Planner for possible re-planning.

### Example: "Patch 50 web servers with canary, drain from LB, verify, then roll out; rollback on error"

Planner can emit:

```json
{
  "plan": {
    "summary": "Canary → Batch → Global rollout with LB drain and health checks.",
    "steps": [
      {"id":"discover","tool":"inventory.query","args":{"group":"web"}},
      {"id":"select_canary","tool":"list.pick","args":{"from":"discover.hosts","count":1}},
      {"id":"drain_canary","tool":"lb.drain","args":{"pool":"web","target":"${select_canary[0]}"}},
      {"id":"patch_canary","tool":"ssh.exec","args":{"target":"${select_canary[0]}","command":"apt-get update && apt-get -y upgrade nginx"}},
      {"id":"health_canary","tool":"http.get","args":{"url":"https://${select_canary[0]}/health","allow_insecure":true}},
      {
        "id":"canary_ok",
        "tool":"branch.if",
        "args":{"condition":"health_canary.status == 200"}
      },
      {"id":"undrain_canary","tool":"lb.undrain","args":{"pool":"web","target":"${select_canary[0]}"},
       "preconditions":["canary_ok:true"]},

      {"id":"batches","tool":"batch.split","args":{"items":"discover.hosts","exclude":"${select_canary}","size":10}},
      {
        "id":"foreach_batch",
        "tool":"foreach",
        "foreach":{"items":"batches.groups","param":"group"},
        "steps":[
          {"id":"drain_batch","tool":"lb.drain_many","args":{"pool":"web","targets":"${group}"}},
          {"id":"patch_batch","tool":"ssh.exec_many","args":{"targets":"${group}","command":"apt-get -y upgrade nginx"},
           "strategy":{"retries":1,"timeout_s":900}},
          {"id":"verify_batch","tool":"http.multi_check","args":{"targets":"${group}","path":"/health"}},
          {
            "id":"batch_ok","tool":"branch.if",
            "args":{"condition":"reduce(verify_batch.statuses,'all_success')"}
          },
          {"id":"undrain_batch","tool":"lb.undrain_many","args":{"pool":"web","targets":"${group}"},
           "preconditions":["batch_ok:true"]},
          {"id":"rollback_batch","tool":"ssh.exec_many",
           "args":{"targets":"${group}","command":"apt-get -y install nginx=PREV_VERSION"},
           "preconditions":["batch_ok:false"], "on_fail":"abort"}
        ]
      },

      {"id":"post_verify","tool":"http.multi_check","args":{"targets":"discover.hosts","path":"/health"}},
      {"id":"report","tool":"report.aggregate","args":{"sections":["health_canary","verify_batch[*]","post_verify"]}}
    ]
  },
  "safety": {"destructive": true, "required_approvals": ["web_maintainers"]},
  "observability": {"log_level":"info","emit_events":true}
}
```

**What's happening:**

- **Fan-out/fan-in**: foreach and batch.split handle 50 hosts in groups of 10.
- **Branching**: branch.if moves forward only on good health.
- **Rollback**: per-batch rollback on failures.
- **LB integration**: drain/undrain around patching.
- **Resilience**: retries and timeouts per step.

### How the LLM fits in (multi-step flow)

1. **Classifier** sees "patch 50 servers" → mode:"action", intent:"apply_config", entities include the service and group.

2. **Selector** maps to inventory.query, lb.*, ssh.exec_many, http.*.

3. **Planner** emits the DAG JSON like above (with foreach, branch, strategy).

4. **Executor** runs it; if a batch fails, you can:
   - **Auto-replan**: feed the failure summary back to the Planner to propose a mitigation plan.
   - **Or halt & require approval** (policy).

### Practical tips

- Keep Planner outputs JSON-only (use format:"json" or a JSON grammar).
- Validate the DAG JSON (Pydantic/JSON Schema) before running.
- Teach only a small vocabulary of flow controls: depends_on, branch.if, foreach, gather, strategy.
- Let the engine own parallelism, retries, timeouts, not the model.
- For very long jobs, run stage-by-stage (plan→execute block→replan) to keep context tight.

**Bottom line**: With a DAG-capable schema and an executor that understands loops/branches, the same A→B→C pipeline cleanly handles complex, multi-step operations—while the LLM continues to make logical decisions inside your safety and policy sandbox. If you want, I can hand you the exact JSON Schema for that plan format so your coder can implement validation and execution.