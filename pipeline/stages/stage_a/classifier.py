"""
Stage A Classifier - Main Orchestrator
Coordinates intent classification, entity extraction, confidence scoring, and risk assessment
"""

import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ...schemas.decision_v1 import DecisionV1, DecisionType
from llm.client import LLMClient
from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor
from .confidence_scorer import ConfidenceScorer
from .risk_assessor import RiskAssessor

class StageAClassifier:
    """
    Main Stage A Classifier
    
    Orchestrates the complete classification pipeline:
    1. Intent classification
    2. Entity extraction
    3. Confidence scoring
    4. Risk assessment
    5. Decision v1 output generation
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.intent_classifier = IntentClassifier(llm_client)
        self.entity_extractor = EntityExtractor(llm_client)
        self.confidence_scorer = ConfidenceScorer(llm_client)
        self.risk_assessor = RiskAssessor(llm_client)
        self.version = "1.0.0"
    
    async def classify(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> DecisionV1:
        """
        Classify user request and generate Decision v1 output
        
        Args:
            user_request: Original user request string
            context: Optional context information
            
        Returns:
            DecisionV1 object with complete classification
        """
        start_time = time.time()
        
        try:
            # Generate unique decision ID
            decision_id = self._generate_decision_id()
            
            # Step 1: Classify intent
            intent = await self.intent_classifier.classify_with_fallback(user_request)
            
            # Step 2: Extract entities
            entities = await self.entity_extractor.extract_entities(user_request)
            
            # Step 3: Calculate confidence
            confidence_data = await self.confidence_scorer.calculate_overall_confidence(
                user_request, intent, entities
            )
            
            # Step 4: Assess risk
            risk_data = await self.risk_assessor.assess_risk(user_request, intent, entities)
            
            # Step 5: Determine decision type and next stage
            decision_type = self._determine_decision_type(intent, confidence_data)
            next_stage = self._determine_next_stage(intent, confidence_data, risk_data)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create Decision v1 object
            decision = DecisionV1(
                decision_id=decision_id,
                decision_type=decision_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                intent=intent,
                entities=entities,
                overall_confidence=confidence_data["overall_confidence"],
                confidence_level=confidence_data["confidence_level"],
                risk_level=risk_data["risk_level"],
                original_request=user_request,
                context=context or {},
                stage_a_version=self.version,
                processing_time_ms=processing_time_ms,
                requires_approval=risk_data["requires_approval"],
                next_stage=next_stage
            )
            
            return decision
            
        except Exception as e:
            # FAIL FAST: OpsConductor requires AI-BRAIN to function
            raise Exception(f"AI-BRAIN (LLM) unavailable - OpsConductor cannot function without LLM: {str(e)}")
    
    def _generate_decision_id(self) -> str:
        """Generate unique decision ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"dec_{timestamp}_{unique_id}"
    

    def _determine_decision_type(self, intent, confidence_data) -> DecisionType:
        """Determine the type of decision based on intent and confidence"""
        # Information requests are always INFO type
        if intent.category == "information":
            return DecisionType.INFO
        
        # All other requests are ACTION type (let orchestrator handle low confidence)
        return DecisionType.ACTION
    
    def _determine_next_stage(self, intent, confidence_data, risk_data) -> str:
        """Determine the next pipeline stage"""
        # FAST PATH: Simple information queries that don't require tool execution
        # can skip directly to Stage D for immediate response
        if intent.category == "information" and intent.action in ["query", "list", "count", "show", "get"]:
            # Check if this is a simple query that can be answered directly
            # without needing to execute tools or create plans
            if confidence_data["overall_confidence"] >= 0.7:
                return "stage_d"
        
        # DEFAULT PATH: All other requests go to Stage B (Selector) for full pipeline processing
        return "stage_b"
    
    # 🚨 ARCHITECTURAL VIOLATION REMOVED
    # The _create_fallback_decision method has been REMOVED because it violates
    # the core architectural principle: OpsConductor is AI-BRAIN DEPENDENT and must
    # FAIL FAST when LLM is unavailable. No fallback decisions should exist.
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Stage A components
        
        Returns:
            Health status dictionary
        """
        health_status = {
            "stage_a": "healthy",
            "version": self.version,
            "components": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Check LLM connectivity
            llm_healthy = await self.llm_client.health_check()
            health_status["components"]["llm_client"] = "healthy" if llm_healthy else "unhealthy"
            
            # Check individual components
            health_status["components"]["intent_classifier"] = "healthy"
            health_status["components"]["entity_extractor"] = "healthy"
            health_status["components"]["confidence_scorer"] = "healthy"
            health_status["components"]["risk_assessor"] = "healthy"
            
            # Overall health
            if not llm_healthy:
                health_status["stage_a"] = "degraded"
            
        except Exception as e:
            health_status["stage_a"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get Stage A capabilities information
        
        Returns:
            Capabilities dictionary
        """
        return {
            "stage": "stage_a",
            "version": self.version,
            "description": "Intent classification and entity extraction",
            "capabilities": {
                "intent_classification": {
                    "supported_categories": self.intent_classifier.get_supported_categories(),
                    "description": "Classifies user intents into categories and actions"
                },
                "entity_extraction": {
                    "supported_types": self.entity_extractor.get_supported_entity_types(),
                    "description": "Extracts technical entities from user requests"
                },
                "confidence_scoring": {
                    "levels": ["high", "medium", "low"],
                    "description": "Assesses confidence in classifications"
                },
                "risk_assessment": {
                    "levels": ["low", "medium", "high", "critical"],
                    "description": "Evaluates operational risk of requests"
                }
            },
            "input_format": "Natural language text",
            "output_format": "Decision v1 JSON schema",
            "processing_time": "Typically 1-3 seconds",
            "dependencies": ["LLM backend (Ollama)"]
        }
    
    async def process_batch(self, requests: list[str], context: Optional[Dict[str, Any]] = None) -> list[DecisionV1]:
        """
        Process multiple requests in batch
        
        Args:
            requests: List of user request strings
            context: Optional shared context
            
        Returns:
            List of DecisionV1 objects
        """
        results = []
        
        for request in requests:
            try:
                decision = await self.classify(request, context)
                results.append(decision)
            except Exception as e:
                # Add fallback decision for failed requests
                fallback = self._create_fallback_decision(request, context, str(e))
                results.append(fallback)
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get Stage A metrics (placeholder for future implementation)
        
        Returns:
            Metrics dictionary
        """
        return {
            "stage": "stage_a",
            "version": self.version,
            "metrics": {
                "total_requests": 0,
                "successful_classifications": 0,
                "failed_classifications": 0,
                "average_processing_time_ms": 0,
                "confidence_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "risk_distribution": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "critical": 0
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }