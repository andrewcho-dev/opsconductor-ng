# AI Intent-Based Strategy: Integration Specifications

## 🎯 **Integration Overview**

This document provides detailed specifications for integrating the Intent-Based AI Strategy with OpsConductor's existing infrastructure, ensuring seamless operation while maintaining backward compatibility and system reliability.

## 🏗 **System Architecture Integration**

### Current System Analysis

#### Existing Components to Integrate With

```python
# Current system components that need integration
EXISTING_COMPONENTS = {
    "job_engine": {
        "path": "ai-brain/job_engine/",
        "key_files": [
            "template_aware_job_creator.py",
            "llm_engines.py",
            "automation_job_creator.py"
        ],
        "integration_points": [
            "job_creation_interface",
            "llm_engine_abstraction",
            "template_matching_logic"
        ]
    },
    
    "automation_jobs": {
        "path": "automation-jobs/",
        "key_components": [
            "ansible_playbooks",
            "docker_containers",
            "job_definitions"
        ],
        "integration_points": [
            "job_execution_interface",
            "parameter_passing",
            "result_handling"
        ]
    },
    
    "api_layer": {
        "path": "api/",
        "endpoints": [
            "/create-job",
            "/job-status",
            "/job-results"
        ],
        "integration_points": [
            "request_routing",
            "response_formatting",
            "error_handling"
        ]
    }
}
```

### Integration Architecture Design

```python
# File: ai-brain/integration/integration_architecture.py
class IntegrationArchitecture:
    """
    Manages integration between intent-based system and existing infrastructure
    """
    
    def __init__(self, config):
        self.config = config
        self.intent_engine = IntentBasedEngine(config)
        self.legacy_job_creator = TemplateAwareJobCreator(config)
        self.integration_mode = config.get("integration_mode", "hybrid")
        
        # Integration strategies
        self.strategies = {
            "hybrid": HybridIntegrationStrategy(),
            "gradual_migration": GradualMigrationStrategy(),
            "parallel_operation": ParallelOperationStrategy(),
            "fallback_only": FallbackOnlyStrategy()
        }
    
    def process_request(self, user_request, context):
        """
        Main request processing with integration logic
        """
        strategy = self.strategies[self.integration_mode]
        return strategy.process_request(
            user_request, 
            context, 
            self.intent_engine, 
            self.legacy_job_creator
        )
```

## 🔄 **Integration Strategies**

### 1. Hybrid Integration Strategy

**Purpose**: Run both systems in parallel with intelligent routing

```python
# File: ai-brain/integration/strategies/hybrid_strategy.py
class HybridIntegrationStrategy:
    """
    Hybrid strategy that uses intent-based system for high-confidence requests
    and falls back to legacy system for low-confidence or unsupported requests
    """
    
    def __init__(self, confidence_threshold=0.75):
        self.confidence_threshold = confidence_threshold
        self.routing_rules = self._load_routing_rules()
        self.performance_tracker = PerformanceTracker()
    
    def process_request(self, user_request, context, intent_engine, legacy_engine):
        """
        Process request using hybrid approach
        """
        processing_result = {
            "request_id": self._generate_request_id(),
            "timestamp": datetime.utcnow(),
            "user_request": user_request,
            "context": context,
            "processing_path": None,
            "result": None,
            "performance_metrics": {}
        }
        
        try:
            # Step 1: Try intent-based classification
            start_time = time.time()
            intent_result = intent_engine.classify_intent(user_request, context)
            classification_time = time.time() - start_time
            
            processing_result["intent_classification"] = {
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "classification_time": classification_time
            }
            
            # Step 2: Apply routing decision logic
            routing_decision = self._make_routing_decision(
                intent_result, 
                context, 
                user_request
            )
            
            processing_result["routing_decision"] = routing_decision
            
            # Step 3: Process based on routing decision
            if routing_decision["use_intent_system"]:
                processing_result["processing_path"] = "intent_based"
                processing_result["result"] = self._process_with_intent_system(
                    intent_result, 
                    context, 
                    intent_engine
                )
            else:
                processing_result["processing_path"] = "legacy_fallback"
                processing_result["result"] = self._process_with_legacy_system(
                    user_request, 
                    context, 
                    legacy_engine
                )
            
            # Step 4: Track performance
            self.performance_tracker.record_processing(processing_result)
            
        except Exception as e:
            # Always fallback to legacy system on any error
            processing_result["processing_path"] = "error_fallback"
            processing_result["error"] = str(e)
            processing_result["result"] = self._process_with_legacy_system(
                user_request, 
                context, 
                legacy_engine
            )
        
        return processing_result
    
    def _make_routing_decision(self, intent_result, context, user_request):
        """
        Intelligent routing decision based on multiple factors
        """
        decision_factors = {
            "confidence_score": intent_result.confidence,
            "intent_supported": self._is_intent_supported(intent_result.intent),
            "context_completeness": self._assess_context_completeness(context),
            "request_complexity": self._assess_request_complexity(user_request),
            "system_load": self._get_system_load(),
            "user_preference": context.get("preferred_system", "auto")
        }
        
        # Apply routing rules
        use_intent_system = (
            decision_factors["confidence_score"] >= self.confidence_threshold and
            decision_factors["intent_supported"] and
            decision_factors["context_completeness"] >= 0.7 and
            decision_factors["system_load"] < 0.8
        )
        
        # Override based on user preference
        if decision_factors["user_preference"] == "legacy":
            use_intent_system = False
        elif decision_factors["user_preference"] == "intent":
            use_intent_system = True
        
        return {
            "use_intent_system": use_intent_system,
            "decision_factors": decision_factors,
            "routing_reason": self._generate_routing_reason(decision_factors, use_intent_system)
        }
```

### 2. Gradual Migration Strategy

**Purpose**: Gradually migrate traffic from legacy to intent-based system

```python
# File: ai-brain/integration/strategies/gradual_migration_strategy.py
class GradualMigrationStrategy:
    """
    Gradually migrate traffic from legacy system to intent-based system
    based on performance metrics and success rates
    """
    
    def __init__(self, initial_percentage=10):
        self.current_percentage = initial_percentage
        self.migration_config = self._load_migration_config()
        self.success_tracker = MigrationSuccessTracker()
        self.rollback_threshold = 0.85  # Rollback if success rate drops below 85%
    
    def process_request(self, user_request, context, intent_engine, legacy_engine):
        """
        Process request with gradual migration logic
        """
        # Determine if this request should use intent-based system
        use_intent_system = self._should_use_intent_system(user_request, context)
        
        if use_intent_system:
            try:
                result = intent_engine.process_request(user_request, context)
                self.success_tracker.record_intent_system_result(result)
                return {
                    "processing_path": "intent_based",
                    "migration_percentage": self.current_percentage,
                    "result": result
                }
            except Exception as e:
                # Fallback to legacy on error
                result = legacy_engine.create_job(user_request, context)
                self.success_tracker.record_fallback_usage("error", str(e))
                return {
                    "processing_path": "error_fallback",
                    "error": str(e),
                    "result": result
                }
        else:
            result = legacy_engine.create_job(user_request, context)
            return {
                "processing_path": "legacy_system",
                "migration_percentage": self.current_percentage,
                "result": result
            }
    
    def _should_use_intent_system(self, user_request, context):
        """
        Determine if request should use intent-based system based on migration percentage
        """
        # Use consistent hashing to ensure same requests always go to same system
        request_hash = hashlib.md5(
            f"{user_request}{context.get('user_id', '')}".encode()
        ).hexdigest()
        
        hash_value = int(request_hash[:8], 16) % 100
        return hash_value < self.current_percentage
    
    def update_migration_percentage(self):
        """
        Update migration percentage based on success metrics
        """
        current_success_rate = self.success_tracker.get_current_success_rate()
        
        if current_success_rate >= 0.95 and self.current_percentage < 100:
            # Increase migration percentage
            self.current_percentage = min(100, self.current_percentage + 10)
            self._log_migration_update("increased", current_success_rate)
        
        elif current_success_rate < self.rollback_threshold:
            # Decrease migration percentage
            self.current_percentage = max(0, self.current_percentage - 20)
            self._log_migration_update("decreased", current_success_rate)
```

### 3. Parallel Operation Strategy

**Purpose**: Run both systems in parallel for comparison and validation

```python
# File: ai-brain/integration/strategies/parallel_operation_strategy.py
class ParallelOperationStrategy:
    """
    Run both systems in parallel to compare results and validate intent-based system
    """
    
    def __init__(self, comparison_mode="shadow"):
        self.comparison_mode = comparison_mode  # "shadow" or "active"
        self.result_comparator = ResultComparator()
        self.performance_analyzer = PerformanceAnalyzer()
    
    def process_request(self, user_request, context, intent_engine, legacy_engine):
        """
        Process request with both systems and compare results
        """
        processing_start = time.time()
        
        # Process with both systems
        results = {
            "request_id": self._generate_request_id(),
            "timestamp": datetime.utcnow(),
            "user_request": user_request,
            "context": context,
            "legacy_result": None,
            "intent_result": None,
            "comparison": None,
            "primary_result": None
        }
        
        # Run both systems (potentially in parallel)
        if self.comparison_mode == "shadow":
            # Legacy system is primary, intent system runs in shadow mode
            results["legacy_result"] = self._run_legacy_system(
                user_request, context, legacy_engine
            )
            results["intent_result"] = self._run_intent_system_shadow(
                user_request, context, intent_engine
            )
            results["primary_result"] = results["legacy_result"]
        
        else:  # active comparison
            # Both systems run and results are compared
            with ThreadPoolExecutor(max_workers=2) as executor:
                legacy_future = executor.submit(
                    self._run_legacy_system, user_request, context, legacy_engine
                )
                intent_future = executor.submit(
                    self._run_intent_system, user_request, context, intent_engine
                )
                
                results["legacy_result"] = legacy_future.result(timeout=30)
                results["intent_result"] = intent_future.result(timeout=30)
            
            # Choose primary result based on comparison
            results["primary_result"] = self._choose_primary_result(
                results["legacy_result"],
                results["intent_result"]
            )
        
        # Compare results
        results["comparison"] = self.result_comparator.compare_results(
            results["legacy_result"],
            results["intent_result"]
        )
        
        # Analyze performance
        processing_time = time.time() - processing_start
        self.performance_analyzer.record_parallel_processing(
            results, processing_time
        )
        
        return results
```

## 🔌 **API Integration Specifications**

### Enhanced API Endpoints

```python
# File: api/intent_api.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v2", tags=["intent-based"])

class IntentRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = {}
    processing_mode: Optional[str] = "hybrid"  # hybrid, intent_only, legacy_only
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class IntentResponse(BaseModel):
    request_id: str
    processing_path: str
    intent_classification: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    decision: Dict[str, Any]
    response: Dict[str, Any]
    execution_plan: Optional[Dict[str, Any]] = None
    performance_metrics: Dict[str, Any]

@router.post("/process-request", response_model=IntentResponse)
async def process_intent_request(
    request: IntentRequest,
    integration_engine: IntegrationArchitecture = Depends(get_integration_engine)
):
    """
    Process user request using intent-based system with integration logic
    """
    try:
        # Set processing mode in context
        request.context["processing_mode"] = request.processing_mode
        request.context["user_id"] = request.user_id
        request.context["session_id"] = request.session_id
        
        # Process request
        result = integration_engine.process_request(request.text, request.context)
        
        # Format response
        return IntentResponse(
            request_id=result["request_id"],
            processing_path=result["processing_path"],
            intent_classification=result.get("intent_classification"),
            confidence_score=result.get("intent_classification", {}).get("confidence"),
            decision=result.get("decision", {}),
            response=result["result"],
            execution_plan=result.get("execution_plan"),
            performance_metrics=result.get("performance_metrics", {})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/system-status")
async def get_system_status():
    """
    Get status of intent-based system and integration health
    """
    return {
        "intent_system_status": "healthy",
        "legacy_system_status": "healthy",
        "integration_mode": "hybrid",
        "current_migration_percentage": 25,
        "performance_metrics": {
            "intent_system_success_rate": 0.92,
            "legacy_system_success_rate": 0.88,
            "average_response_time": 2.3,
            "error_rate": 0.02
        }
    }

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback on system performance for continuous improvement
    """
    # Process feedback for system learning
    pass
```

### Backward Compatibility Layer

```python
# File: api/compatibility_layer.py
class BackwardCompatibilityLayer:
    """
    Ensures backward compatibility with existing API clients
    """
    
    def __init__(self, integration_engine):
        self.integration_engine = integration_engine
        self.response_transformer = ResponseTransformer()
    
    async def handle_legacy_create_job(self, request_data):
        """
        Handle legacy /create-job requests and transform to intent-based processing
        """
        # Transform legacy request format to intent request format
        intent_request = self._transform_legacy_request(request_data)
        
        # Process using integration engine
        result = self.integration_engine.process_request(
            intent_request["text"],
            intent_request["context"]
        )
        
        # Transform response back to legacy format
        legacy_response = self.response_transformer.to_legacy_format(result)
        
        return legacy_response
    
    def _transform_legacy_request(self, legacy_request):
        """
        Transform legacy request format to intent-based format
        """
        return {
            "text": legacy_request.get("description", ""),
            "context": {
                "user_id": legacy_request.get("user_id"),
                "environment": legacy_request.get("environment", "production"),
                "urgency": legacy_request.get("priority", "normal"),
                "legacy_parameters": legacy_request.get("parameters", {})
            }
        }
```

## 🗄 **Database Integration**

### Schema Extensions

```sql
-- File: database/migrations/add_intent_based_tables.sql

-- Intent classification results
CREATE TABLE intent_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    user_request TEXT NOT NULL,
    classified_intent VARCHAR(100) NOT NULL,
    intent_subcategory VARCHAR(100),
    confidence_score DECIMAL(3,2) NOT NULL,
    entities JSONB,
    context JSONB,
    classification_timestamp TIMESTAMP DEFAULT NOW(),
    processing_time_ms INTEGER,
    
    INDEX idx_intent_classifications_request_id (request_id),
    INDEX idx_intent_classifications_intent (classified_intent),
    INDEX idx_intent_classifications_confidence (confidence_score),
    INDEX idx_intent_classifications_timestamp (classification_timestamp)
);

-- Decision records
CREATE TABLE decision_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    classification_id UUID REFERENCES intent_classifications(id),
    decision_action VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    risk_assessment JSONB,
    safety_overrides JSONB,
    approval_requirements JSONB,
    decision_timestamp TIMESTAMP DEFAULT NOW(),
    decision_rationale TEXT,
    
    INDEX idx_decision_records_request_id (request_id),
    INDEX idx_decision_records_action (decision_action),
    INDEX idx_decision_records_timestamp (decision_timestamp)
);

-- Template usage tracking
CREATE TABLE template_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    template_id VARCHAR(100) NOT NULL,
    template_version VARCHAR(20) NOT NULL,
    selection_score DECIMAL(3,2),
    parameters_extracted JSONB,
    analysis_results JSONB,
    usage_timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_template_usage_request_id (request_id),
    INDEX idx_template_usage_template_id (template_id),
    INDEX idx_template_usage_timestamp (usage_timestamp)
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    processing_path VARCHAR(50) NOT NULL, -- intent_based, legacy_fallback, error_fallback
    total_processing_time_ms INTEGER NOT NULL,
    intent_classification_time_ms INTEGER,
    template_selection_time_ms INTEGER,
    analysis_time_ms INTEGER,
    decision_time_ms INTEGER,
    response_construction_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_performance_metrics_request_id (request_id),
    INDEX idx_performance_metrics_path (processing_path),
    INDEX idx_performance_metrics_timestamp (timestamp)
);

-- System health monitoring
CREATE TABLE system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20),
    component VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_system_health_component (component),
    INDEX idx_system_health_timestamp (timestamp),
    INDEX idx_system_health_metric_name (metric_name)
);
```

### Data Access Layer

```python
# File: ai-brain/data/intent_data_access.py
class IntentDataAccess:
    """
    Data access layer for intent-based system
    """
    
    def __init__(self, database_connection):
        self.db = database_connection
    
    async def store_intent_classification(self, classification_result):
        """
        Store intent classification result
        """
        query = """
        INSERT INTO intent_classifications 
        (request_id, user_request, classified_intent, intent_subcategory, 
         confidence_score, entities, context, processing_time_ms)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        
        return await self.db.fetchval(
            query,
            classification_result["request_id"],
            classification_result["user_request"],
            classification_result["intent"],
            classification_result.get("subcategory"),
            classification_result["confidence"],
            json.dumps(classification_result.get("entities", {})),
            json.dumps(classification_result.get("context", {})),
            classification_result.get("processing_time_ms")
        )
    
    async def store_decision_record(self, decision_result):
        """
        Store decision record
        """
        query = """
        INSERT INTO decision_records 
        (request_id, classification_id, decision_action, confidence_score,
         risk_assessment, safety_overrides, approval_requirements, decision_rationale)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        
        return await self.db.fetchval(
            query,
            decision_result["request_id"],
            decision_result.get("classification_id"),
            decision_result["decision"]["action"],
            decision_result["confidence_score"],
            json.dumps(decision_result.get("risk_assessment", {})),
            json.dumps(decision_result.get("safety_overrides", [])),
            json.dumps(decision_result.get("approval_requirements", [])),
            decision_result.get("decision_rationale")
        )
    
    async def get_performance_trends(self, time_period="24h"):
        """
        Get performance trends for monitoring
        """
        query = """
        SELECT 
            processing_path,
            AVG(total_processing_time_ms) as avg_processing_time,
            COUNT(*) as request_count,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_processing_time_ms) as p95_processing_time
        FROM performance_metrics 
        WHERE timestamp >= NOW() - INTERVAL %s
        GROUP BY processing_path
        ORDER BY request_count DESC
        """
        
        return await self.db.fetch(query, time_period)
```

## 🔧 **Configuration Management**

### Integration Configuration

```yaml
# File: config/integration_config.yaml
integration:
  mode: "hybrid"  # hybrid, gradual_migration, parallel_operation, fallback_only
  
  hybrid_config:
    confidence_threshold: 0.75
    fallback_on_error: true
    performance_monitoring: true
    
  gradual_migration_config:
    initial_percentage: 10
    increment_percentage: 10
    success_rate_threshold: 0.90
    rollback_threshold: 0.85
    evaluation_interval: "1h"
    
  parallel_operation_config:
    comparison_mode: "shadow"  # shadow, active
    result_comparison: true
    performance_analysis: true
    
  safety_overrides:
    production_protection: true
    high_risk_prevention: true
    compliance_validation: true
    
  monitoring:
    metrics_collection: true
    performance_tracking: true
    error_tracking: true
    user_feedback_collection: true

# System thresholds
thresholds:
  confidence:
    auto_execute: 0.90
    execute_with_confirmation: 0.75
    provide_manual_instructions: 0.60
    request_clarification: 0.40
    escalate_to_human: 0.20
    
  performance:
    max_response_time_ms: 5000
    max_error_rate: 0.05
    min_availability: 0.995
    
  quality:
    min_intent_accuracy: 0.85
    min_user_satisfaction: 0.80
    min_automation_success_rate: 0.90
```

### Environment-Specific Configuration

```python
# File: config/environment_config.py
class EnvironmentConfig:
    """
    Environment-specific configuration management
    """
    
    def __init__(self, environment="production"):
        self.environment = environment
        self.config = self._load_environment_config()
    
    def _load_environment_config(self):
        """
        Load configuration based on environment
        """
        base_config = self._load_base_config()
        
        if self.environment == "development":
            return self._apply_development_overrides(base_config)
        elif self.environment == "staging":
            return self._apply_staging_overrides(base_config)
        elif self.environment == "production":
            return self._apply_production_overrides(base_config)
        else:
            return base_config
    
    def _apply_production_overrides(self, config):
        """
        Apply production-specific configuration overrides
        """
        config["integration"]["mode"] = "hybrid"
        config["thresholds"]["confidence"]["auto_execute"] = 0.95  # Higher threshold for production
        config["safety_overrides"]["production_protection"] = True
        config["monitoring"]["detailed_logging"] = True
        
        return config
    
    def _apply_development_overrides(self, config):
        """
        Apply development-specific configuration overrides
        """
        config["integration"]["mode"] = "parallel_operation"
        config["thresholds"]["confidence"]["auto_execute"] = 0.70  # Lower threshold for testing
        config["safety_overrides"]["production_protection"] = False
        config["monitoring"]["debug_logging"] = True
        
        return config
```

## 📊 **Monitoring & Observability Integration**

### Metrics Collection

```python
# File: ai-brain/monitoring/metrics_collector.py
class IntegrationMetricsCollector:
    """
    Collect metrics for intent-based system integration
    """
    
    def __init__(self, metrics_backend):
        self.metrics = metrics_backend
        self.metric_definitions = self._define_metrics()
    
    def record_request_processing(self, processing_result):
        """
        Record metrics for request processing
        """
        # Basic processing metrics
        self.metrics.increment(
            "requests_total",
            tags={
                "processing_path": processing_result["processing_path"],
                "intent": processing_result.get("intent_classification", {}).get("intent", "unknown")
            }
        )
        
        # Processing time metrics
        if "performance_metrics" in processing_result:
            self.metrics.histogram(
                "processing_time_ms",
                processing_result["performance_metrics"]["total_time_ms"],
                tags={"processing_path": processing_result["processing_path"]}
            )
        
        # Confidence score distribution
        if "intent_classification" in processing_result:
            self.metrics.histogram(
                "confidence_score",
                processing_result["intent_classification"]["confidence"],
                tags={"intent": processing_result["intent_classification"]["intent"]}
            )
        
        # Success/failure tracking
        if processing_result.get("result", {}).get("success", False):
            self.metrics.increment("requests_successful", tags={"processing_path": processing_result["processing_path"]})
        else:
            self.metrics.increment("requests_failed", tags={"processing_path": processing_result["processing_path"]})
    
    def record_system_health(self, health_metrics):
        """
        Record system health metrics
        """
        for component, metrics in health_metrics.items():
            for metric_name, value in metrics.items():
                self.metrics.gauge(
                    f"system_health_{metric_name}",
                    value,
                    tags={"component": component}
                )
```

### Alerting Configuration

```yaml
# File: monitoring/alerts/intent_system_alerts.yaml
alerts:
  - name: "intent_classification_accuracy_low"
    condition: "intent_classification_accuracy < 0.85"
    duration: "5m"
    severity: "warning"
    description: "Intent classification accuracy has dropped below 85%"
    
  - name: "response_time_high"
    condition: "avg(processing_time_ms) > 5000"
    duration: "2m"
    severity: "critical"
    description: "Average response time exceeds 5 seconds"
    
  - name: "error_rate_high"
    condition: "error_rate > 0.05"
    duration: "1m"
    severity: "critical"
    description: "Error rate exceeds 5%"
    
  - name: "confidence_score_drift"
    condition: "avg(confidence_score) < 0.70"
    duration: "10m"
    severity: "warning"
    description: "Average confidence score has drifted below 70%"
    
  - name: "fallback_usage_high"
    condition: "fallback_usage_rate > 0.30"
    duration: "5m"
    severity: "warning"
    description: "Fallback to legacy system usage exceeds 30%"
```

---

**Next**: See Testing and Validation Strategy documentation for comprehensive quality assurance approaches and testing methodologies.