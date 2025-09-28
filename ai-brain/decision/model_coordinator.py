"""
OUIOE Phase 4: Model Coordinator

Advanced multi-model coordination system that manages AI model selection,
load balancing, and performance optimization for collaborative decision making.

Key Features:
- Dynamic model selection based on task complexity and requirements
- Intelligent load balancing across available models
- Real-time model performance monitoring and optimization
- Fallback and redundancy management for reliability
- Model capability matching and routing
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Set
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of AI models available"""
    GENERAL = "general"           # General purpose models
    ANALYTICAL = "analytical"     # Data analysis specialists
    CREATIVE = "creative"         # Creative and ideation models
    TECHNICAL = "technical"       # Technical implementation models
    ETHICAL = "ethical"          # Ethical reasoning models
    STRATEGIC = "strategic"       # Strategic planning models
    COLLABORATIVE = "collaborative"  # Multi-agent coordination
    SPECIALIZED = "specialized"   # Domain-specific models


class ModelCapability(Enum):
    """Model capabilities"""
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    CREATIVITY = "creativity"
    PLANNING = "planning"
    PROBLEM_SOLVING = "problem_solving"
    DECISION_MAKING = "decision_making"
    COLLABORATION = "collaboration"
    TECHNICAL_EXPERTISE = "technical_expertise"
    ETHICAL_REASONING = "ethical_reasoning"
    PATTERN_RECOGNITION = "pattern_recognition"


class ModelStatus(Enum):
    """Model availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_id: str
    response_time: float = 0.0
    accuracy: float = 0.0
    reliability: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    confidence_score: float = 0.0
    user_satisfaction: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_metrics(self, response_time: float, success: bool, confidence: float = 0.0):
        """Update performance metrics with new data"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        
        # Update averages
        self.response_time = (self.response_time + response_time) / 2
        self.reliability = self.successful_requests / self.total_requests
        self.error_rate = 1.0 - self.reliability
        
        if confidence > 0:
            self.confidence_score = (self.confidence_score + confidence) / 2
        
        self.last_updated = datetime.now()


@dataclass
class ModelInfo:
    """Information about an available model"""
    id: str
    name: str
    model_type: ModelType
    capabilities: Set[ModelCapability]
    max_concurrent: int = 5
    current_load: int = 0
    status: ModelStatus = ModelStatus.AVAILABLE
    endpoint: str = ""
    api_key: Optional[str] = None
    performance: ModelPerformance = field(default_factory=lambda: ModelPerformance(""))
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.performance.model_id:
            self.performance.model_id = self.id
    
    def is_available(self) -> bool:
        """Check if model is available for new requests"""
        return (self.status == ModelStatus.AVAILABLE and 
                self.current_load < self.max_concurrent)
    
    def get_load_percentage(self) -> float:
        """Get current load as percentage"""
        return (self.current_load / self.max_concurrent) * 100 if self.max_concurrent > 0 else 100


@dataclass
class ModelSelection:
    """Result of model selection process"""
    selected_models: List[str]
    selection_reasoning: str
    confidence: float
    fallback_models: List[str] = field(default_factory=list)
    estimated_response_time: float = 0.0
    load_distribution: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelRequest:
    """Request for model coordination"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    required_capabilities: Set[ModelCapability] = field(default_factory=set)
    preferred_model_types: List[ModelType] = field(default_factory=list)
    max_models: int = 3
    min_models: int = 1
    priority: str = "normal"
    timeout: float = 30.0
    quality_threshold: float = 0.8
    require_consensus: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ModelCoordinator:
    """
    Advanced Model Coordinator - Intelligent multi-model management system
    
    Provides:
    - Dynamic model selection based on capabilities and performance
    - Intelligent load balancing and resource optimization
    - Real-time performance monitoring and adaptation
    - Fallback and redundancy management
    - Model capability matching and routing
    """
    
    def __init__(self, performance_callback: Optional[Callable] = None):
        """Initialize the model coordinator"""
        self.performance_callback = performance_callback
        
        # Model registry
        self.models: Dict[str, ModelInfo] = {}
        self.model_groups: Dict[ModelType, List[str]] = defaultdict(list)
        self.capability_index: Dict[ModelCapability, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.global_metrics: Dict[str, Any] = {
            'total_requests': 0,
            'successful_selections': 0,
            'average_response_time': 0.0,
            'model_utilization': {},
            'capability_coverage': {}
        }
        
        # Load balancing
        self.load_balancer_strategy = "round_robin"  # round_robin, least_loaded, performance_based
        self.round_robin_counters: Dict[ModelType, int] = defaultdict(int)
        
        # Initialize with default models
        self._initialize_default_models()
        
        logger.info("🤖 Model Coordinator initialized - Ready for intelligent model management!")
    
    def _initialize_default_models(self):
        """Initialize default model configurations"""
        default_models = [
            {
                'id': 'general-llm-1',
                'name': 'General Purpose LLM',
                'model_type': ModelType.GENERAL,
                'capabilities': {ModelCapability.REASONING, ModelCapability.ANALYSIS, 
                               ModelCapability.PROBLEM_SOLVING, ModelCapability.DECISION_MAKING},
                'max_concurrent': 10,
                'endpoint': 'http://ollama:11434/api/generate'
            },
            {
                'id': 'analytical-model-1',
                'name': 'Analytical Specialist',
                'model_type': ModelType.ANALYTICAL,
                'capabilities': {ModelCapability.ANALYSIS, ModelCapability.PATTERN_RECOGNITION,
                               ModelCapability.TECHNICAL_EXPERTISE},
                'max_concurrent': 5,
                'endpoint': 'http://ollama:11434/api/generate'
            },
            {
                'id': 'creative-model-1',
                'name': 'Creative Ideation Model',
                'model_type': ModelType.CREATIVE,
                'capabilities': {ModelCapability.CREATIVITY, ModelCapability.PROBLEM_SOLVING,
                               ModelCapability.COLLABORATION},
                'max_concurrent': 3,
                'endpoint': 'http://ollama:11434/api/generate'
            },
            {
                'id': 'strategic-model-1',
                'name': 'Strategic Planning Model',
                'model_type': ModelType.STRATEGIC,
                'capabilities': {ModelCapability.PLANNING, ModelCapability.DECISION_MAKING,
                               ModelCapability.REASONING},
                'max_concurrent': 3,
                'endpoint': 'http://ollama:11434/api/generate'
            },
            {
                'id': 'ethical-model-1',
                'name': 'Ethical Reasoning Model',
                'model_type': ModelType.ETHICAL,
                'capabilities': {ModelCapability.ETHICAL_REASONING, ModelCapability.REASONING,
                               ModelCapability.DECISION_MAKING},
                'max_concurrent': 2,
                'endpoint': 'http://ollama:11434/api/generate'
            }
        ]
        
        for model_config in default_models:
            model_info = ModelInfo(**model_config)
            self.register_model(model_info)
    
    def register_model(self, model_info: ModelInfo):
        """Register a new model with the coordinator"""
        self.models[model_info.id] = model_info
        
        # Update indexes
        self.model_groups[model_info.model_type].append(model_info.id)
        
        for capability in model_info.capabilities:
            self.capability_index[capability].append(model_info.id)
        
        # Initialize performance tracking
        self.performance_history[model_info.id] = deque(maxlen=100)
        
        logger.info(f"📝 Registered model: {model_info.name} ({model_info.id})")
    
    def unregister_model(self, model_id: str):
        """Unregister a model from the coordinator"""
        if model_id not in self.models:
            return
        
        model_info = self.models[model_id]
        
        # Remove from indexes
        self.model_groups[model_info.model_type].remove(model_id)
        
        for capability in model_info.capabilities:
            if model_id in self.capability_index[capability]:
                self.capability_index[capability].remove(model_id)
        
        # Clean up
        del self.models[model_id]
        if model_id in self.performance_history:
            del self.performance_history[model_id]
        
        logger.info(f"🗑️ Unregistered model: {model_id}")
    
    async def select_models(self, request: ModelRequest) -> ModelSelection:
        """
        Select optimal models for a given request
        
        Args:
            request: Model selection request with requirements
            
        Returns:
            ModelSelection with selected models and reasoning
        """
        start_time = time.time()
        
        try:
            # Find candidate models
            candidates = self._find_candidate_models(request)
            
            if not candidates:
                return ModelSelection(
                    selected_models=[],
                    selection_reasoning="No suitable models found for requirements",
                    confidence=0.0
                )
            
            # Score and rank candidates
            scored_candidates = self._score_models(candidates, request)
            
            # Select optimal models
            selected_models = self._select_optimal_models(scored_candidates, request)
            
            # Generate fallback options
            fallback_models = self._generate_fallback_models(scored_candidates, selected_models, request)
            
            # Calculate confidence and metrics
            confidence = self._calculate_selection_confidence(selected_models, request)
            estimated_time = self._estimate_response_time(selected_models)
            load_distribution = self._calculate_load_distribution(selected_models)
            
            # Build selection result
            selection = ModelSelection(
                selected_models=selected_models,
                selection_reasoning=self._generate_selection_reasoning(selected_models, request),
                confidence=confidence,
                fallback_models=fallback_models,
                estimated_response_time=estimated_time,
                load_distribution=load_distribution,
                metadata={
                    'candidates_evaluated': len(candidates),
                    'selection_time': time.time() - start_time,
                    'strategy': self.load_balancer_strategy
                }
            )
            
            # Update metrics
            self._update_selection_metrics(selection, request)
            
            logger.info(f"🎯 Selected models: {selected_models} (confidence: {confidence:.2f})")
            return selection
            
        except Exception as e:
            logger.error(f"❌ Model selection failed: {str(e)}")
            return ModelSelection(
                selected_models=[],
                selection_reasoning=f"Selection failed: {str(e)}",
                confidence=0.0
            )
    
    def _find_candidate_models(self, request: ModelRequest) -> List[str]:
        """Find models that match the request requirements"""
        candidates = set()
        
        # Find by required capabilities
        if request.required_capabilities:
            capability_matches = set()
            for capability in request.required_capabilities:
                capability_matches.update(self.capability_index.get(capability, []))
            candidates.update(capability_matches)
        
        # Find by preferred model types
        if request.preferred_model_types:
            for model_type in request.preferred_model_types:
                candidates.update(self.model_groups.get(model_type, []))
        
        # If no specific requirements, consider all available models
        if not candidates:
            candidates = set(self.models.keys())
        
        # Filter by availability
        available_candidates = []
        for model_id in candidates:
            model = self.models.get(model_id)
            if model and model.is_available():
                available_candidates.append(model_id)
        
        return available_candidates
    
    def _score_models(self, candidates: List[str], request: ModelRequest) -> List[tuple]:
        """Score candidate models based on suitability"""
        scored_models = []
        
        for model_id in candidates:
            model = self.models[model_id]
            score = 0.0
            
            # Capability match score (40%)
            capability_score = self._calculate_capability_score(model, request)
            score += capability_score * 0.4
            
            # Performance score (30%)
            performance_score = self._calculate_performance_score(model)
            score += performance_score * 0.3
            
            # Load score (20%)
            load_score = self._calculate_load_score(model)
            score += load_score * 0.2
            
            # Availability score (10%)
            availability_score = 1.0 if model.is_available() else 0.0
            score += availability_score * 0.1
            
            scored_models.append((model_id, score))
        
        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return scored_models
    
    def _calculate_capability_score(self, model: ModelInfo, request: ModelRequest) -> float:
        """Calculate how well model capabilities match request"""
        if not request.required_capabilities:
            return 1.0
        
        matched_capabilities = model.capabilities.intersection(request.required_capabilities)
        return len(matched_capabilities) / len(request.required_capabilities)
    
    def _calculate_performance_score(self, model: ModelInfo) -> float:
        """Calculate model performance score"""
        perf = model.performance
        
        # Combine multiple performance metrics
        reliability_score = perf.reliability
        confidence_score = perf.confidence_score
        response_time_score = max(0, 1.0 - (perf.response_time / 10.0))  # Normalize to 10s max
        
        # Weighted average
        return (reliability_score * 0.4 + confidence_score * 0.3 + response_time_score * 0.3)
    
    def _calculate_load_score(self, model: ModelInfo) -> float:
        """Calculate load-based score (lower load = higher score)"""
        load_percentage = model.get_load_percentage()
        return max(0, 1.0 - (load_percentage / 100.0))
    
    def _select_optimal_models(self, scored_candidates: List[tuple], request: ModelRequest) -> List[str]:
        """Select optimal models from scored candidates"""
        selected = []
        
        # Apply load balancing strategy
        if self.load_balancer_strategy == "performance_based":
            # Select top performers
            for model_id, score in scored_candidates:
                if len(selected) >= request.max_models:
                    break
                if score >= request.quality_threshold:
                    selected.append(model_id)
        
        elif self.load_balancer_strategy == "least_loaded":
            # Sort by load and select least loaded
            load_sorted = sorted(scored_candidates, 
                               key=lambda x: self.models[x[0]].get_load_percentage())
            for model_id, score in load_sorted:
                if len(selected) >= request.max_models:
                    break
                if score >= request.quality_threshold:
                    selected.append(model_id)
        
        else:  # round_robin
            # Round robin selection among top candidates
            top_candidates = [model_id for model_id, score in scored_candidates 
                            if score >= request.quality_threshold]
            
            for i in range(min(request.max_models, len(top_candidates))):
                if top_candidates:
                    selected.append(top_candidates[i % len(top_candidates)])
        
        # Ensure minimum models
        if len(selected) < request.min_models and scored_candidates:
            # Add more models even if below threshold
            for model_id, score in scored_candidates:
                if model_id not in selected:
                    selected.append(model_id)
                    if len(selected) >= request.min_models:
                        break
        
        return selected
    
    def _generate_fallback_models(self, scored_candidates: List[tuple], 
                                selected_models: List[str], request: ModelRequest) -> List[str]:
        """Generate fallback model options"""
        fallbacks = []
        
        for model_id, score in scored_candidates:
            if model_id not in selected_models and len(fallbacks) < 3:
                fallbacks.append(model_id)
        
        return fallbacks
    
    def _calculate_selection_confidence(self, selected_models: List[str], request: ModelRequest) -> float:
        """Calculate confidence in model selection"""
        if not selected_models:
            return 0.0
        
        # Base confidence on model performance and capability match
        total_confidence = 0.0
        
        for model_id in selected_models:
            model = self.models[model_id]
            
            # Performance confidence
            perf_confidence = model.performance.confidence_score
            
            # Capability match confidence
            if request.required_capabilities:
                matched = model.capabilities.intersection(request.required_capabilities)
                capability_confidence = len(matched) / len(request.required_capabilities)
            else:
                capability_confidence = 1.0
            
            # Combined confidence
            model_confidence = (perf_confidence * 0.6 + capability_confidence * 0.4)
            total_confidence += model_confidence
        
        return min(total_confidence / len(selected_models), 1.0)
    
    def _estimate_response_time(self, selected_models: List[str]) -> float:
        """Estimate response time for selected models"""
        if not selected_models:
            return 0.0
        
        # Use average response time of selected models
        total_time = sum(self.models[model_id].performance.response_time 
                        for model_id in selected_models)
        
        return total_time / len(selected_models)
    
    def _calculate_load_distribution(self, selected_models: List[str]) -> Dict[str, float]:
        """Calculate load distribution across selected models"""
        distribution = {}
        
        if not selected_models:
            return distribution
        
        # Equal distribution for now (can be made more sophisticated)
        load_per_model = 1.0 / len(selected_models)
        
        for model_id in selected_models:
            distribution[model_id] = load_per_model
        
        return distribution
    
    def _generate_selection_reasoning(self, selected_models: List[str], request: ModelRequest) -> str:
        """Generate human-readable reasoning for model selection"""
        if not selected_models:
            return "No suitable models available for the request requirements"
        
        reasoning_parts = []
        
        # Selection criteria
        reasoning_parts.append(f"Selected {len(selected_models)} models based on:")
        
        if request.required_capabilities:
            capabilities_str = ", ".join([cap.value for cap in request.required_capabilities])
            reasoning_parts.append(f"- Required capabilities: {capabilities_str}")
        
        if request.preferred_model_types:
            types_str = ", ".join([mt.value for mt in request.preferred_model_types])
            reasoning_parts.append(f"- Preferred model types: {types_str}")
        
        # Model details
        for model_id in selected_models:
            model = self.models[model_id]
            load_pct = model.get_load_percentage()
            reasoning_parts.append(
                f"- {model.name}: {model.performance.reliability:.1%} reliability, "
                f"{load_pct:.0f}% load"
            )
        
        return " ".join(reasoning_parts)
    
    def _update_selection_metrics(self, selection: ModelSelection, request: ModelRequest):
        """Update global selection metrics"""
        self.global_metrics['total_requests'] += 1
        
        if selection.selected_models:
            self.global_metrics['successful_selections'] += 1
        
        # Update model utilization
        for model_id in selection.selected_models:
            if model_id not in self.global_metrics['model_utilization']:
                self.global_metrics['model_utilization'][model_id] = 0
            self.global_metrics['model_utilization'][model_id] += 1
    
    async def update_model_performance(self, model_id: str, response_time: float, 
                                     success: bool, confidence: float = 0.0):
        """Update model performance metrics"""
        if model_id not in self.models:
            return
        
        model = self.models[model_id]
        model.performance.update_metrics(response_time, success, confidence)
        
        # Add to performance history
        self.performance_history[model_id].append({
            'timestamp': datetime.now(),
            'response_time': response_time,
            'success': success,
            'confidence': confidence
        })
        
        # Performance callback
        if self.performance_callback:
            await self.performance_callback({
                'type': 'performance_update',
                'model_id': model_id,
                'performance': model.performance.__dict__
            })
    
    def set_model_status(self, model_id: str, status: ModelStatus):
        """Set model status"""
        if model_id in self.models:
            self.models[model_id].status = status
            logger.info(f"🔄 Model {model_id} status changed to {status.value}")
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a specific model"""
        return self.models.get(model_id)
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models"""
        return [model for model in self.models.values() if model.is_available()]
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """Get models that have a specific capability"""
        model_ids = self.capability_index.get(capability, [])
        return [self.models[model_id] for model_id in model_ids if model_id in self.models]
    
    def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """Get models of a specific type"""
        model_ids = self.model_groups.get(model_type, [])
        return [self.models[model_id] for model_id in model_ids if model_id in self.models]
    
    def get_coordinator_metrics(self) -> Dict[str, Any]:
        """Get coordinator performance metrics"""
        metrics = self.global_metrics.copy()
        
        # Add current model status
        metrics['model_status'] = {}
        for model_id, model in self.models.items():
            metrics['model_status'][model_id] = {
                'status': model.status.value,
                'load_percentage': model.get_load_percentage(),
                'performance': model.performance.__dict__
            }
        
        return metrics