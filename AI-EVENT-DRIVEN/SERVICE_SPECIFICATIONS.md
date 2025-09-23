# AI Event-Driven System - Service Specifications

## Service Overview

This document provides detailed specifications for the two core services that comprise the AI Event-Driven System: the Event Processing Service and the Autonomous Response Service.

## Event Processing Service (Port 3009)

### Service Description
The Event Processing Service serves as the central hub for ingesting, processing, correlating, and analyzing events from multiple monitoring sources. It acts as the intelligent gateway between external monitoring systems and the OpsConductor AI Brain.

### Technical Specifications

#### Runtime Environment
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 16 (events, rules schemas)
- **Cache**: Redis 7 (event queuing, correlation cache)
- **Message Queue**: Redis Streams for event processing pipeline
- **Container**: Docker with health checks

#### Resource Requirements
- **CPU**: 4 cores minimum, 8 cores recommended
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 100GB minimum for event data
- **Network**: 1Gbps for high-volume event ingestion

#### Dependencies
```yaml
services:
  event-processing-service:
    depends_on:
      - postgres (events schema)
      - redis (streams and caching)
      - ai-brain (event analysis)
      - asset-service (context enrichment)
      - communication-service (notifications)
```

### API Specifications

#### Event Ingestion Endpoints

##### Webhook Event Ingestion
```yaml
POST /api/v1/events/webhook
Content-Type: application/json
Authorization: Bearer <api_token>

Request Body:
{
  "source": "monitoring_system_name",
  "source_type": "nagios|zabbix|prometheus|custom",
  "event_type": "alert|metric|log|notification",
  "severity": "critical|high|medium|low|info",
  "timestamp": "2024-12-20T10:30:00Z",
  "host": "server-hostname",
  "service": "service-name",
  "title": "Event title/summary",
  "description": "Detailed event description",
  "metadata": {
    "custom_field_1": "value1",
    "custom_field_2": "value2",
    "metrics": {
      "cpu_usage": 95.5,
      "memory_usage": 87.2
    }
  },
  "tags": ["production", "web-server", "critical-service"]
}

Response:
{
  "event_id": 12345,
  "status": "accepted|rejected",
  "message": "Event processed successfully",
  "correlation_id": "uuid-string",
  "processing_time_ms": 150
}
```

##### SNMP Trap Receiver
```yaml
# SNMP trap configuration
SNMP_TRAP_PORT: 162
SUPPORTED_VERSIONS: [v1, v2c, v3]
COMMUNITY_STRINGS: ["public", "monitoring"]
TRAP_PROCESSING: async

# Trap to event conversion
trap_mapping:
  linkDown: 
    event_type: "connectivity_issue"
    severity: "high"
  linkUp:
    event_type: "connectivity_restored"
    severity: "info"
  coldStart:
    event_type: "system_restart"
    severity: "medium"
```

##### Syslog Receiver
```yaml
# Syslog configuration
SYSLOG_UDP_PORT: 514
SYSLOG_TCP_PORT: 514
SYSLOG_TLS_PORT: 6514
SUPPORTED_FORMATS: [RFC3164, RFC5424, CEF, LEEF]

# Syslog parsing rules
parsing_rules:
  - pattern: "Failed password for .* from (.*) port"
    event_type: "authentication_failure"
    severity: "medium"
    extract_fields: ["source_ip"]
  - pattern: "Out of disk space"
    event_type: "disk_space_critical"
    severity: "critical"
```

#### Event Query and Management Endpoints

##### Event Retrieval
```yaml
GET /api/v1/events
Parameters:
  - severity: critical|high|medium|low|info
  - event_type: string
  - host: string
  - service: string
  - start_time: ISO8601 timestamp
  - end_time: ISO8601 timestamp
  - limit: integer (default: 100, max: 1000)
  - offset: integer (default: 0)
  - include_correlations: boolean (default: false)

Response:
{
  "events": [
    {
      "id": 12345,
      "event_type": "threshold_breach",
      "severity": "critical",
      "host": "web-server-01",
      "service": "nginx",
      "title": "High CPU Usage",
      "description": "CPU usage exceeded 95% threshold",
      "occurred_at": "2024-12-20T10:30:00Z",
      "processed_at": "2024-12-20T10:30:05Z",
      "correlation_id": "uuid-string",
      "metadata": {...},
      "tags": [...]
    }
  ],
  "total_count": 1500,
  "has_more": true
}
```

##### Event Correlation Analysis
```yaml
GET /api/v1/events/{event_id}/correlations
Response:
{
  "primary_event": {...},
  "correlations": [
    {
      "correlation_type": "time_based|pattern_based|causal",
      "related_events": [...],
      "correlation_score": 0.85,
      "correlation_reason": "Events occurred within 5 minutes on same host",
      "created_at": "2024-12-20T10:35:00Z"
    }
  ],
  "correlation_summary": {
    "total_related_events": 5,
    "highest_correlation_score": 0.92,
    "correlation_timespan_minutes": 15
  }
}
```

#### Rule Management Endpoints

##### Trigger Rule Management
```yaml
POST /api/v1/rules/triggers
Content-Type: application/json

Request Body:
{
  "name": "High CPU Alert Rule",
  "description": "Trigger when CPU usage exceeds 90%",
  "conditions": {
    "event_type": "threshold_breach",
    "severity": ["critical", "high"],
    "metadata.cpu_usage": {"$gt": 90},
    "host": {"$regex": "web-server-.*"}
  },
  "time_window_minutes": 5,
  "max_triggers_per_hour": 3,
  "cooldown_minutes": 15,
  "active": true
}

Response:
{
  "rule_id": 456,
  "status": "created",
  "validation_result": {
    "valid": true,
    "warnings": [],
    "estimated_trigger_rate": "2-3 per day"
  }
}

GET /api/v1/rules/triggers
GET /api/v1/rules/triggers/{rule_id}
PUT /api/v1/rules/triggers/{rule_id}
DELETE /api/v1/rules/triggers/{rule_id}
```

##### Response Template Management
```yaml
POST /api/v1/rules/responses
Content-Type: application/json

Request Body:
{
  "name": "CPU Investigation Playbook",
  "description": "Automated response for high CPU events",
  "trigger_rule_id": 456,
  "response_type": "investigation|remediation|escalation",
  "actions": [
    {
      "type": "diagnostic",
      "name": "Check Process List",
      "automation_script_id": 123,
      "timeout_minutes": 5,
      "required": true
    },
    {
      "type": "remediation",
      "name": "Kill High CPU Processes",
      "automation_script_id": 124,
      "approval_required": true,
      "risk_level": "medium",
      "rollback_supported": true
    },
    {
      "type": "notification",
      "name": "Alert Operations Team",
      "channels": ["email", "slack"],
      "template": "high_cpu_alert"
    }
  ],
  "approval_required": false,
  "max_execution_time_minutes": 30
}
```

### Event Processing Pipeline

#### Processing Stages
```python
class EventProcessingPipeline:
    async def process_event(self, raw_event: dict) -> ProcessedEvent:
        # Stage 1: Validation and normalization
        validated_event = await self.validate_event(raw_event)
        normalized_event = await self.normalize_event(validated_event)
        
        # Stage 2: Enrichment
        enriched_event = await self.enrich_event(normalized_event)
        
        # Stage 3: Noise filtering
        if await self.is_noise(enriched_event):
            return await self.handle_noise(enriched_event)
        
        # Stage 4: Correlation
        correlations = await self.correlate_event(enriched_event)
        
        # Stage 5: Severity scoring
        severity_score = await self.calculate_severity(enriched_event, correlations)
        
        # Stage 6: Rule evaluation
        triggered_rules = await self.evaluate_rules(enriched_event)
        
        # Stage 7: Storage and indexing
        processed_event = await self.store_event(enriched_event, correlations, triggered_rules)
        
        # Stage 8: Downstream notifications
        await self.notify_subscribers(processed_event)
        
        return processed_event
```

#### Correlation Algorithms
```python
class EventCorrelator:
    async def correlate_event(self, event: ProcessedEvent) -> List[Correlation]:
        correlations = []
        
        # Time-based correlation (events within time window)
        time_correlations = await self.find_time_based_correlations(
            event, window_minutes=15
        )
        correlations.extend(time_correlations)
        
        # Host-based correlation (events from same system)
        host_correlations = await self.find_host_based_correlations(
            event, lookback_hours=1
        )
        correlations.extend(host_correlations)
        
        # Pattern-based correlation (similar event signatures)
        pattern_correlations = await self.find_pattern_correlations(
            event, similarity_threshold=0.8
        )
        correlations.extend(pattern_correlations)
        
        # Causal correlation (cause-effect relationships)
        causal_correlations = await self.find_causal_correlations(event)
        correlations.extend(causal_correlations)
        
        return await self.rank_correlations(correlations)
```

## Autonomous Response Service (Port 3011)

### Service Description
The Autonomous Response Service executes intelligent, automated responses to system events based on AI analysis and predefined playbooks. It provides safety controls, approval workflows, and learning capabilities.

### Technical Specifications

#### Runtime Environment
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 16 (autonomous schema)
- **Cache**: Redis 7 (execution state, locks)
- **Task Queue**: Celery with Redis broker
- **Container**: Docker with privileged capabilities for system actions

#### Resource Requirements
- **CPU**: 2 cores minimum, 4 cores recommended
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 50GB for execution logs and state
- **Network**: Access to all target systems for automation

#### Dependencies
```yaml
services:
  autonomous-response-service:
    depends_on:
      - postgres (autonomous schema)
      - redis (task queue and state)
      - event-processing-service (trigger source)
      - ai-brain (decision support)
      - automation-service (action execution)
      - asset-service (target validation)
```

### API Specifications

#### Decision and Analysis Endpoints

##### Request Autonomous Analysis
```yaml
POST /api/v1/autonomous/analyze
Content-Type: application/json
Authorization: Bearer <api_token>

Request Body:
{
  "event_id": 12345,
  "context": {
    "business_hours": true,
    "maintenance_window": false,
    "system_criticality": "high|medium|low",
    "user_preferences": {
      "auto_approve_low_risk": true,
      "notification_channels": ["email", "slack"]
    }
  },
  "analysis_options": {
    "include_recommendations": true,
    "include_risk_assessment": true,
    "include_impact_analysis": true
  }
}

Response:
{
  "decision_id": 67890,
  "analysis_result": {
    "recommended_action": "investigate|remediate|escalate|ignore",
    "confidence_score": 0.87,
    "risk_level": "low|medium|high|critical",
    "business_impact": "none|low|medium|high|critical",
    "reasoning": "Detailed explanation of decision logic",
    "estimated_resolution_time_minutes": 15
  },
  "recommended_actions": [
    {
      "action_id": 789,
      "action_type": "diagnostic|remediation|notification",
      "action_name": "Check CPU Usage",
      "description": "Execute CPU diagnostic script",
      "risk_level": "low",
      "approval_required": false,
      "estimated_duration_minutes": 5,
      "success_probability": 0.95
    }
  ],
  "approval_requirements": {
    "required": false,
    "reason": "Low risk action within approved parameters",
    "approvers": []
  }
}
```

##### Execute Autonomous Action
```yaml
POST /api/v1/autonomous/execute
Content-Type: application/json

Request Body:
{
  "decision_id": 67890,
  "action_ids": [789, 790],
  "execution_options": {
    "dry_run": false,
    "rollback_on_failure": true,
    "max_execution_time_minutes": 30,
    "notification_preferences": {
      "notify_on_start": true,
      "notify_on_completion": true,
      "notify_on_failure": true
    }
  },
  "approval_token": "human_approved_xyz" // Required if approval needed
}

Response:
{
  "execution_id": "exec_12345",
  "status": "queued|running|completed|failed|cancelled",
  "started_at": "2024-12-20T10:45:00Z",
  "estimated_completion": "2024-12-20T10:50:00Z",
  "actions": [
    {
      "action_id": 789,
      "status": "queued|running|completed|failed",
      "started_at": "2024-12-20T10:45:00Z",
      "completed_at": null,
      "result": null,
      "error_message": null
    }
  ],
  "rollback_plan": {
    "supported": true,
    "rollback_actions": [...]
  }
}
```

#### Execution Monitoring Endpoints

##### Execution Status Tracking
```yaml
GET /api/v1/autonomous/executions/{execution_id}
Response:
{
  "execution_id": "exec_12345",
  "decision_id": 67890,
  "event_id": 12345,
  "status": "running",
  "progress": {
    "current_step": 2,
    "total_steps": 3,
    "percentage_complete": 67
  },
  "actions": [
    {
      "action_id": 789,
      "name": "Check CPU Usage",
      "status": "completed",
      "started_at": "2024-12-20T10:45:00Z",
      "completed_at": "2024-12-20T10:47:00Z",
      "duration_seconds": 120,
      "result": {
        "success": true,
        "output": "CPU usage: 45%, Memory: 67%",
        "metrics": {
          "cpu_usage": 45.2,
          "memory_usage": 67.1
        }
      }
    }
  ],
  "logs": [
    {
      "timestamp": "2024-12-20T10:45:00Z",
      "level": "info",
      "message": "Starting CPU diagnostic",
      "action_id": 789
    }
  ]
}

GET /api/v1/autonomous/executions
# Query parameters: status, event_id, start_time, end_time, limit, offset
```

##### Execution Control
```yaml
POST /api/v1/autonomous/executions/{execution_id}/cancel
POST /api/v1/autonomous/executions/{execution_id}/rollback
POST /api/v1/autonomous/executions/{execution_id}/approve
POST /api/v1/autonomous/executions/{execution_id}/reject
```

#### Learning and Feedback Endpoints

##### Provide Feedback
```yaml
POST /api/v1/autonomous/feedback
Content-Type: application/json

Request Body:
{
  "execution_id": "exec_12345",
  "decision_id": 67890,
  "feedback_type": "effectiveness|accuracy|timeliness|safety",
  "rating": 1-5, // 1=poor, 5=excellent
  "feedback": "helpful|not_helpful|incorrect|dangerous",
  "comments": "The action resolved the issue quickly and effectively",
  "suggestions": "Could have provided more detailed progress updates",
  "would_approve_again": true
}

Response:
{
  "feedback_id": 999,
  "status": "recorded",
  "learning_impact": {
    "confidence_adjustment": 0.02,
    "template_updates": ["cpu_diagnostic_template"],
    "pattern_updates": ["high_cpu_resolution_pattern"]
  }
}
```

### Safety Control Framework

#### Risk Assessment Matrix
```python
class RiskAssessment:
    RISK_FACTORS = {
        'system_criticality': {
            'critical': 0.4,
            'high': 0.3,
            'medium': 0.2,
            'low': 0.1
        },
        'action_type': {
            'system_restart': 0.5,
            'service_restart': 0.3,
            'configuration_change': 0.4,
            'diagnostic': 0.1,
            'notification': 0.0
        },
        'business_hours': {
            'business_hours': 0.2,
            'after_hours': 0.0
        },
        'maintenance_window': {
            'in_maintenance': 0.0,
            'outside_maintenance': 0.1
        }
    }
    
    def calculate_risk_score(self, context: dict) -> float:
        risk_score = 0.0
        for factor, value in context.items():
            if factor in self.RISK_FACTORS:
                risk_score += self.RISK_FACTORS[factor].get(value, 0.0)
        return min(risk_score, 1.0)
    
    def requires_approval(self, risk_score: float) -> bool:
        return risk_score > 0.3  # Approval required for medium+ risk
```

#### Approval Workflow System
```python
class ApprovalWorkflow:
    async def request_approval(self, execution_request: dict) -> ApprovalRequest:
        approval_request = ApprovalRequest(
            execution_id=execution_request['execution_id'],
            risk_level=execution_request['risk_level'],
            business_impact=execution_request['business_impact'],
            requested_actions=execution_request['actions'],
            timeout_minutes=30,  # Auto-reject after 30 minutes
            approvers=await self.get_required_approvers(execution_request)
        )
        
        # Send approval notifications
        await self.send_approval_notifications(approval_request)
        
        # Set timeout for auto-rejection
        await self.schedule_timeout(approval_request)
        
        return approval_request
    
    async def process_approval_response(self, approval_id: str, response: str, approver: str):
        approval = await self.get_approval_request(approval_id)
        
        if response == 'approved':
            approval.status = 'approved'
            approval.approved_by = approver
            approval.approved_at = datetime.utcnow()
            
            # Trigger execution
            await self.trigger_execution(approval.execution_id)
            
        elif response == 'rejected':
            approval.status = 'rejected'
            approval.rejected_by = approver
            approval.rejected_at = datetime.utcnow()
            
            # Cancel execution
            await self.cancel_execution(approval.execution_id)
```

### Response Template System

#### Template Definition Structure
```yaml
response_template:
  id: "high_cpu_investigation"
  name: "High CPU Usage Investigation"
  description: "Automated investigation and remediation for high CPU usage"
  version: "1.2"
  
  triggers:
    - event_type: "threshold_breach"
      conditions:
        - "metadata.cpu_usage > 90"
        - "severity in ['critical', 'high']"
  
  variables:
    - name: "cpu_threshold"
      type: "float"
      default: 90.0
      description: "CPU usage threshold percentage"
    - name: "max_processes_to_kill"
      type: "integer"
      default: 3
      description: "Maximum number of processes to terminate"
  
  actions:
    - id: "diagnostic_cpu"
      name: "CPU Diagnostic"
      type: "diagnostic"
      automation_script: "check_cpu_usage"
      timeout_minutes: 5
      required: true
      
    - id: "diagnostic_processes"
      name: "Process Analysis"
      type: "diagnostic"
      automation_script: "list_high_cpu_processes"
      timeout_minutes: 3
      depends_on: ["diagnostic_cpu"]
      
    - id: "remediation_kill_processes"
      name: "Kill High CPU Processes"
      type: "remediation"
      automation_script: "kill_high_cpu_processes"
      parameters:
        max_processes: "{{ max_processes_to_kill }}"
      approval_required: true
      risk_level: "medium"
      rollback_supported: true
      depends_on: ["diagnostic_processes"]
      
    - id: "notification_resolved"
      name: "Resolution Notification"
      type: "notification"
      channels: ["email", "slack"]
      template: "cpu_issue_resolved"
      depends_on: ["remediation_kill_processes"]
  
  rollback_actions:
    - id: "restore_processes"
      name: "Restore Terminated Processes"
      automation_script: "restore_processes"
      condition: "remediation_kill_processes.failed"
  
  success_criteria:
    - "diagnostic_cpu.result.cpu_usage < {{ cpu_threshold }}"
    - "all_actions_completed == true"
  
  failure_criteria:
    - "any_action_failed == true"
    - "execution_time > max_execution_time"
```

### Learning and Improvement System

#### Outcome Analysis Engine
```python
class OutcomeAnalyzer:
    async def analyze_execution_outcome(self, execution: ExecutionRecord) -> LearningInsight:
        # Collect execution metrics
        metrics = await self.collect_execution_metrics(execution)
        
        # Analyze success/failure patterns
        patterns = await self.analyze_patterns(execution, metrics)
        
        # Compare with historical data
        historical_comparison = await self.compare_with_history(execution)
        
        # Generate improvement recommendations
        recommendations = await self.generate_recommendations(
            execution, metrics, patterns, historical_comparison
        )
        
        return LearningInsight(
            execution_id=execution.id,
            success_score=metrics.success_score,
            efficiency_score=metrics.efficiency_score,
            patterns_identified=patterns,
            recommendations=recommendations,
            confidence_adjustment=self.calculate_confidence_adjustment(metrics)
        )
    
    async def update_knowledge_base(self, insight: LearningInsight):
        # Update response templates
        await self.update_response_templates(insight)
        
        # Update decision models
        await self.update_decision_models(insight)
        
        # Update risk assessments
        await self.update_risk_assessments(insight)
        
        # Update correlation patterns
        await self.update_correlation_patterns(insight)
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: Q1 2025