"""
Multi-Brain AI Engine - Phase 1 Implementation

This is the main orchestrator for the Multi-Brain AI Architecture.
It coordinates Intent Brain, Technical Brain, and SME Brains to process user requests.

Phase 1 Implementation following exact roadmap specification:
- Week 1: Intent Brain Core Implementation ✓
- Week 2: Technical Brain Implementation ✓  
- Week 3: Initial SME Brain Implementation ✓

This replaces the legacy keyword-based system with intelligent multi-brain reasoning.
"""

import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Multi-Brain Components
from brains.intent_brain.intent_brain import IntentBrain, IntentAnalysisResult
from brains.technical_brain import TechnicalBrain, TechnicalPlan
from brains.sme.container_sme_brain import ContainerSMEBrain
from brains.sme.security_sme_brain import SecuritySMEBrain
from brains.sme.network_sme_brain import NetworkSMEBrain
from brains.sme.database_sme_brain import DatabaseSMEBrain
from communication.brain_protocol import BrainCommunicationProtocol, MultibrainAnalysis
from learning.continuous_learning_system import ContinuousLearningSystem, ExecutionFeedback
from learning.quality_assurance import LearningQualityAssurance
from confidence.multibrain_confidence import MultibrainConfidenceEngine, AggregatedConfidence

logger = logging.getLogger(__name__)

@dataclass
class MultiBrainProcessingResult:
    """Complete result from multi-brain processing"""
    # Request information
    request_id: str
    user_message: str
    timestamp: datetime
    
    # Brain analysis results
    intent_analysis: IntentAnalysisResult
    technical_plan: TechnicalPlan
    sme_consultations: Dict[str, Any]
    
    # Aggregated results
    overall_confidence: float
    execution_strategy: str
    recommended_actions: List[str]
    risk_assessment: Dict[str, Any]
    
    # Processing metadata
    processing_time: float
    brains_consulted: List[str]
    phase: str = "phase_1"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "request_id": self.request_id,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "intent_analysis": self.intent_analysis.to_dict(),
            "technical_plan": self.technical_plan.to_dict(),
            "sme_consultations": self.sme_consultations,
            "overall_confidence": self.overall_confidence,
            "execution_strategy": self.execution_strategy,
            "recommended_actions": self.recommended_actions,
            "risk_assessment": self.risk_assessment,
            "processing_time": self.processing_time,
            "brains_consulted": self.brains_consulted,
            "phase": self.phase
        }

class MultiBrainAIEngine:
    """
    Multi-Brain AI Engine - Phase 2 Implementation
    
    This engine orchestrates the multi-brain architecture to process user requests
    with intelligent reasoning, advanced communication, continuous learning, and
    sophisticated confidence aggregation.
    
    Phase 2 Architecture Flow:
    1. Intent Brain: Understands WHAT the user wants
    2. Technical Brain: Determines HOW to achieve it
    3. SME Brains: Provide domain-specific expertise (Container, Security, Network, Database)
    4. Brain Communication Protocol: Coordinates multi-brain analysis
    5. Continuous Learning System: Learns from execution feedback
    6. Multi-Brain Confidence Engine: Risk-adjusted confidence aggregation
    7. Quality Assurance: Validates learning updates
    """
    
    def __init__(self, llm_engine=None, asset_client=None):
        """
        Initialize Multi-Brain AI Engine
        
        Args:
            llm_engine: Optional LLM engine for enhanced analysis
            asset_client: Optional asset service client for asset database access
        """
        self.engine_id = "multi_brain_ai_engine"
        self.engine_version = "2.0.0"
        self.phase = "phase_2"
        
        # Store service clients
        self.asset_client = asset_client
        
        # Initialize brain components
        self.intent_brain = IntentBrain(llm_engine)
        self.technical_brain = TechnicalBrain()
        
        # Initialize SME brains (Phase 2: All SME brains)
        self.sme_brains = {
            "container_orchestration": ContainerSMEBrain(),
            "security_and_compliance": SecuritySMEBrain(),
            "network_infrastructure": NetworkSMEBrain(),
            "database_administration": DatabaseSMEBrain()
        }
        
        # Initialize Brain Communication Protocol
        self.communication_protocol = BrainCommunicationProtocol()
        
        # Initialize Phase 2 Systems
        self.continuous_learning_system = ContinuousLearningSystem()
        self.learning_quality_assurance = LearningQualityAssurance()
        self.multibrain_confidence_engine = MultibrainConfidenceEngine()
        
        # Configuration
        self.confidence_threshold = 0.7
        self.max_processing_time = 30.0  # seconds
        
        # Tracking
        self.request_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0
        }
        
        # Mark initialization flags (async initialization will happen in initialize() method)
        self._communication_initialized = False
        self._learning_initialized = False
        
        logger.info(f"Multi-Brain AI Engine initialized - Phase 2 with {len(self.sme_brains)} SME brains")
    
    async def initialize(self) -> bool:
        """
        Initialize async components of the Multi-Brain AI Engine
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize communication protocol with brains
            if not self._communication_initialized:
                await self._initialize_communication_protocol()
                self._communication_initialized = True
                logger.info("Communication protocol initialized")
            
            # Initialize learning systems
            if not self._learning_initialized:
                await self._initialize_learning_systems()
                self._learning_initialized = True
                logger.info("Learning systems initialized")
            
            logger.info("Multi-Brain AI Engine async initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Brain AI Engine: {str(e)}")
            return False
    
    async def _lookup_asset_information(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Look up asset information from the asset database if IP addresses are mentioned
        
        Args:
            query: The user's query to analyze for IP addresses
            
        Returns:
            Dict containing asset information if found, None otherwise
        """
        logger.info(f"🔍 Asset lookup called for query: '{query}'")
        print(f"DEBUG: Asset lookup called for query: '{query}'")
        
        if not self.asset_client:
            logger.warning("🔍 No asset client available for asset lookup")
            return None
            
        try:
            # Look for IP addresses in the query
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ip_addresses = re.findall(ip_pattern, query)
            logger.info(f"🔍 Found IP addresses in query: {ip_addresses}")
            
            # Check if this is a counting or general asset query
            query_lower = query.lower()
            is_counting_query = any(phrase in query_lower for phrase in ['how many', 'count of', 'number of', 'total', 'list all', 'show all'])
            is_general_query = any(phrase in query_lower for phrase in ['assets', 'systems', 'machines', 'devices', 'windows', 'linux', 'ubuntu'])
            
            if ip_addresses:
                # Look up specific IP addresses
                asset_info = {}
                for ip in ip_addresses:
                    logger.info(f"🔍 Looking up asset information for IP: {ip}")
                    asset = await self.asset_client.get_asset_by_ip(ip)
                    if asset:
                        asset_info[ip] = asset
                        logger.info(f"✅ Found asset information for IP {ip}: {asset.get('name', 'Unknown')} ({asset.get('os_type', 'Unknown OS')})")
                    else:
                        logger.warning(f"❌ No asset found for IP {ip}")
                
                logger.info(f"🔍 Asset lookup result: {len(asset_info)} assets found")
                return asset_info if asset_info else None
                
            elif is_counting_query or is_general_query:
                # Fetch all assets for counting/general queries
                logger.info("🔍 Fetching all assets for counting/general query")
                all_assets = await self.asset_client.get_all_assets()
                if all_assets:
                    asset_info = {}
                    for asset in all_assets:
                        ip = asset.get('ip_address')
                        if ip:
                            asset_info[ip] = asset
                    
                    logger.info(f"✅ Fetched {len(asset_info)} assets for counting/general query")
                    return asset_info if asset_info else None
                else:
                    logger.warning("❌ No assets found in system")
                    return None
            else:
                logger.info("🔍 No IP addresses found and not a counting/general query")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error looking up asset information: {str(e)}")
            return None
    
    def _generate_direct_asset_answer(self, query: str, formatted_assets: List[Dict]) -> Optional[str]:
        """
        Generate a direct answer for simple informational queries about assets.
        
        This method provides direct answers for basic asset information queries
        when we have the exact data available, avoiding unnecessary "Execute with human oversight"
        responses for simple informational requests.
        
        Args:
            query: The user's query
            formatted_assets: List of formatted asset information
            
        Returns:
            Direct answer string if applicable, None otherwise
        """
        if not formatted_assets:
            return None
            
        query_lower = query.lower()
        
        # Handle counting queries (how many, count, etc.)
        if any(phrase in query_lower for phrase in ['how many', 'count of', 'number of', 'total']):
            # Count assets by OS type
            if any(phrase in query_lower for phrase in ['windows', 'win', 'microsoft']):
                windows_assets = [asset for asset in formatted_assets if 'windows' in asset.get('os_type', '').lower()]
                count = len(windows_assets)
                if count == 0:
                    return "There are no Windows assets in the system."
                elif count == 1:
                    return f"There is 1 Windows asset in the system: {windows_assets[0].get('name', windows_assets[0].get('ip_address'))}."
                else:
                    asset_names = [asset.get('name', asset.get('ip_address')) for asset in windows_assets]
                    return f"There are {count} Windows assets in the system: {', '.join(asset_names)}."
            
            elif any(phrase in query_lower for phrase in ['linux', 'ubuntu', 'centos', 'redhat', 'debian']):
                linux_assets = [asset for asset in formatted_assets if any(linux_term in asset.get('os_type', '').lower() for linux_term in ['linux', 'ubuntu', 'centos', 'redhat', 'debian'])]
                count = len(linux_assets)
                if count == 0:
                    return "There are no Linux assets in the system."
                elif count == 1:
                    return f"There is 1 Linux asset in the system: {linux_assets[0].get('name', linux_assets[0].get('ip_address'))}."
                else:
                    asset_names = [asset.get('name', asset.get('ip_address')) for asset in linux_assets]
                    return f"There are {count} Linux assets in the system: {', '.join(asset_names)}."
            
            elif any(phrase in query_lower for phrase in ['assets', 'systems', 'machines', 'devices']):
                count = len(formatted_assets)
                if count == 0:
                    return "There are no assets in the system."
                elif count == 1:
                    return f"There is 1 asset in the system: {formatted_assets[0].get('name', formatted_assets[0].get('ip_address'))}."
                else:
                    return f"There are {count} assets in the system."
        
        # For single asset queries, use the first asset
        asset = formatted_assets[0]
        
        # Communication method queries
        if any(phrase in query_lower for phrase in ['communication method', 'default communication', 'how to connect', 'connection method']):
            method = asset.get('communication_method', 'Unknown')
            port = asset.get('communication_port', 'Unknown')
            secure = asset.get('is_secure_connection', False)
            name = asset.get('name', asset.get('ip_address', 'Unknown'))
            
            if method == 'winrm':
                security_note = " (HTTP - not secure)" if not secure else " (HTTPS - secure)"
                return f"The default communication method for {name} ({asset.get('ip_address')}) is WinRM (Windows Remote Management) on port {port}{security_note}."
            elif method == 'ssh':
                return f"The default communication method for {name} ({asset.get('ip_address')}) is SSH on port {port}."
            elif method != 'Unknown':
                return f"The default communication method for {name} ({asset.get('ip_address')}) is {method} on port {port}."
        
        # OS type queries
        if any(phrase in query_lower for phrase in ['operating system', 'os type', 'what os', 'system type', 'os is', 'running on']):
            os_type = asset.get('os_type', 'Unknown')
            os_version = asset.get('os_version', '')
            name = asset.get('name', asset.get('ip_address', 'Unknown'))
            
            if os_type != 'Unknown':
                version_text = f" {os_version}" if os_version else ""
                return f"{name} ({asset.get('ip_address')}) is running {os_type.title()}{version_text}."
        
        # Device type queries
        if any(phrase in query_lower for phrase in ['device type', 'what type', 'kind of device']):
            device_type = asset.get('device_type', 'Unknown')
            name = asset.get('name', asset.get('ip_address', 'Unknown'))
            
            if device_type != 'Unknown':
                return f"{name} ({asset.get('ip_address')}) is a {device_type}."
        
        # General asset info queries
        if any(phrase in query_lower for phrase in ['tell me about', 'information about', 'details about', 'what is']):
            name = asset.get('name', 'Unknown')
            ip = asset.get('ip_address', 'Unknown')
            os_type = asset.get('os_type', 'Unknown')
            device_type = asset.get('device_type', 'Unknown')
            method = asset.get('communication_method', 'Unknown')
            port = asset.get('communication_port', 'Unknown')
            description = asset.get('description', '')
            
            info_parts = [f"{name} ({ip})"]
            if os_type != 'Unknown':
                info_parts.append(f"OS: {os_type.title()}")
            if device_type != 'Unknown':
                info_parts.append(f"Type: {device_type}")
            if method != 'Unknown':
                info_parts.append(f"Communication: {method} on port {port}")
            if description:
                info_parts.append(f"Description: {description}")
            
            return " | ".join(info_parts)
        
        return None
    

    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user query using multi-brain architecture (compatibility method)
        
        This method provides compatibility with the existing interface while using
        the advanced multi-brain processing capabilities.
        
        Args:
            query: The user's natural language query
            user_context: Optional user context information
            
        Returns:
            Dict containing the AI response and metadata
        """
        try:
            logger.info(f"🧠 Processing query: '{query}'")
            
            # First, check if this query involves asset information
            asset_info = await self._lookup_asset_information(query)
            logger.info(f"🧠 Asset lookup completed, found: {asset_info is not None}")
            
            # Convert user_context to the format expected by process_request
            context = {}
            if user_context:
                if isinstance(user_context, str):
                    context['user_id'] = user_context
                elif isinstance(user_context, dict):
                    context.update(user_context)
            
            # Add asset information to context if found
            if asset_info:
                # Format asset information in a way that's clear for the AI
                formatted_assets = []
                for ip, asset in asset_info.items():
                    asset_summary = {
                        'ip_address': ip,
                        'name': asset.get('name', 'Unknown'),
                        'hostname': asset.get('hostname', ip),
                        'os_type': asset.get('os_type', 'Unknown'),
                        'os_version': asset.get('os_version', 'Unknown'),
                        'device_type': asset.get('device_type', 'Unknown'),
                        'communication_method': asset.get('service_type', 'Unknown'),
                        'communication_port': asset.get('port', 'Unknown'),
                        'is_secure_connection': asset.get('is_secure', False),
                        'description': asset.get('description', 'No description available')
                    }
                    formatted_assets.append(asset_summary)
                
                context['asset_information'] = formatted_assets
                context['asset_query_context'] = f"The user is asking about assets. Available asset information has been provided for the following IP addresses: {', '.join(asset_info.keys())}. Use this information to answer their question directly."
                
                # Add explicit instruction for informational queries
                if any(word in query.lower() for word in ['what is', 'what are', 'show me', 'tell me', 'how do', 'how many', 'how much', 'which', 'list', 'count']):
                    context['query_type'] = 'informational'
                    context['instruction'] = 'This is an informational query. Provide a direct answer using the available asset information. Do not require human oversight for simple information requests.'
                
                logger.info(f"✅ Added asset information to context for {len(asset_info)} assets")
                print(f"DEBUG: Asset information being passed to AI: {asset_info}")
                print(f"DEBUG: Formatted asset context: {formatted_assets}")
            
            # ALWAYS use Multi-Brain AI processing - no bypassing allowed!
            logger.info("🧠 Using multi-brain analysis path (ALWAYS - no keyword matching)")
            print("DEBUG: Using multi-brain analysis path (ALWAYS - no keyword matching)")
            
            # Process through multi-brain architecture
            result = await self.process_request(query, context)
            response_text = result.recommended_actions[0] if result.recommended_actions else "Analysis completed successfully"
            confidence = result.overall_confidence
            intent = result.intent_analysis.intent_type if hasattr(result.intent_analysis, 'intent_type') else "multi_brain_analysis"
            
            # Post-process: If this is a simple informational query about assets and we have the data,
            # provide a direct answer with the specific asset information
            if (asset_info and 
                context.get('query_type') == 'informational' and
                result.execution_strategy == "informational_response"):
                
                # Generate a direct answer based on the asset information
                direct_answer = self._generate_direct_asset_answer(query, formatted_assets)
                if direct_answer:
                    response_text = direct_answer
                    confidence = 0.85  # High confidence since we have the exact data
                    logger.info(f"🎯 Provided direct answer for informational asset query: {direct_answer}")
                    print(f"DEBUG: Provided direct answer: {direct_answer}")
            
            # Use full multi-brain metadata
            metadata = {
                "engine": "multi_brain_ai_engine",
                "version": "2.0.0",
                "processing_time": result.processing_time,
                "brains_consulted": result.brains_consulted,
                "intent_analysis": result.intent_analysis.to_dict() if hasattr(result.intent_analysis, 'to_dict') else str(result.intent_analysis),
                "technical_plan": result.technical_plan.to_dict() if hasattr(result.technical_plan, 'to_dict') else str(result.technical_plan),
                "sme_consultations": result.sme_consultations,
                "execution_strategy": result.execution_strategy,
                "risk_assessment": result.risk_assessment,
                "success": True
            }
            
            return {
                "response": response_text,
                "confidence": confidence,
                "intent": intent,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Multi-brain query processing failed: {str(e)}")
            return {
                "response": f"I encountered an issue processing your request: {str(e)}. Please try again.",
                "confidence": 0.3,
                "intent": "error",
                "metadata": {
                    "engine": "multi_brain_ai_engine",
                    "version": "2.0.0",
                    "error": str(e),
                    "success": False
                }
            }

    async def process_request(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> MultiBrainProcessingResult:
        """
        Process user request through multi-brain architecture
        
        This is the main entry point that replaces legacy keyword-based processing.
        
        Args:
            user_message: User's request message
            context: Optional additional context
            
        Returns:
            MultiBrainProcessingResult: Complete processing result
        """
        start_time = datetime.now()
        request_id = f"mbr_{start_time.strftime('%Y%m%d_%H%M%S')}_{len(self.request_history)}"
        
        try:
            logger.info(f"Processing multi-brain request: {request_id}")
            
            # Ensure async components are initialized
            if not (self._communication_initialized and self._learning_initialized):
                logger.warning("Multi-brain components not fully initialized, initializing now...")
                await self.initialize()
            
            # Step 1: Intent Brain Analysis
            logger.info("Step 1: Intent Brain analysis")
            intent_analysis = await self.intent_brain.analyze_intent(user_message, context or {})
            logger.info(f"Intent analysis completed with confidence: {intent_analysis.overall_confidence}")
            
            # Step 2: Technical Brain Planning
            logger.info("Step 2: Technical Brain planning")
            technical_plan = await self.technical_brain.create_execution_plan(intent_analysis.to_dict())
            logger.info(f"Technical plan created with {len(technical_plan.steps)} steps")
            
            # Step 3: SME Brain Consultations
            logger.info("Step 3: SME Brain consultations")
            sme_consultations = await self._consult_sme_brains(technical_plan, intent_analysis)
            logger.info(f"SME consultations completed for {len(sme_consultations)} domains")
            
            # Step 4: Aggregate Confidence and Determine Strategy
            logger.info("Step 4: Confidence aggregation and strategy determination")
            overall_confidence = await self._aggregate_confidence(intent_analysis, technical_plan, sme_consultations)
            execution_strategy = await self._determine_execution_strategy(overall_confidence, technical_plan, intent_analysis)
            
            # Step 5: Generate Recommendations
            logger.info("Step 5: Generating recommendations")
            recommended_actions = await self._generate_recommendations(technical_plan, sme_consultations, execution_strategy)
            
            # Step 6: Risk Assessment
            risk_assessment = await self._aggregate_risk_assessment(technical_plan, sme_consultations, intent_analysis)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create result
            result = MultiBrainProcessingResult(
                request_id=request_id,
                user_message=user_message,
                timestamp=start_time,
                intent_analysis=intent_analysis,
                technical_plan=technical_plan,
                sme_consultations=sme_consultations,
                overall_confidence=overall_confidence,
                execution_strategy=execution_strategy,
                recommended_actions=recommended_actions,
                risk_assessment=risk_assessment,
                processing_time=processing_time,
                brains_consulted=["intent_brain", "technical_brain"] + list(sme_consultations.keys())
            )
            
            # Update metrics
            await self._update_metrics(result)
            
            # Store in history
            self.request_history.append(result)
            
            logger.info(f"Multi-brain processing completed: {request_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-brain processing: {str(e)}")
            
            # Create error result
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create minimal result for error case
            error_result = MultiBrainProcessingResult(
                request_id=request_id,
                user_message=user_message,
                timestamp=start_time,
                intent_analysis=IntentAnalysisResult(
                    intent_id=request_id,
                    user_message=user_message,
                    timestamp=start_time,
                    itil_classification=None,
                    business_intent=None,
                    overall_confidence=0.0,
                    intent_summary="Error in processing",
                    recommended_approach="Manual review required",
                    technical_requirements=[],
                    resource_requirements=[],
                    risk_level="high",
                    risk_factors=["Processing error"],
                    processing_time=processing_time,
                    brain_version="1.0.0"
                ),
                technical_plan=None,
                sme_consultations={},
                overall_confidence=0.0,
                execution_strategy="manual_review",
                recommended_actions=["Review error and retry"],
                risk_assessment={"error": str(e)},
                processing_time=processing_time,
                brains_consulted=[]
            )
            
            return error_result
    
    async def _consult_sme_brains(self, technical_plan: TechnicalPlan, intent_analysis: IntentAnalysisResult) -> Dict[str, Any]:
        """Consult relevant SME brains based on technical plan"""
        consultations = {}
        
        try:
            # Determine which SME brains to consult
            relevant_domains = set(technical_plan.sme_consultations_needed)
            
            # Always consult security for high-risk operations
            if intent_analysis.risk_level == "high" or technical_plan.risk_assessment.get("overall_risk") == "high":
                relevant_domains.add("security_and_compliance")
            
            # Consult available SME brains
            for domain in relevant_domains:
                if domain in self.sme_brains:
                    try:
                        sme_brain = self.sme_brains[domain]
                        
                        # Analyze technical plan from SME perspective
                        sme_analysis = await sme_brain.analyze_technical_plan(
                            technical_plan.to_dict(),
                            intent_analysis.to_dict()
                        )
                        
                        consultations[domain] = sme_analysis
                        logger.info(f"SME consultation completed for domain: {domain}")
                        
                    except Exception as e:
                        logger.error(f"Error consulting SME brain {domain}: {str(e)}")
                        consultations[domain] = {"error": str(e)}
            
            return consultations
            
        except Exception as e:
            logger.error(f"Error in SME consultations: {str(e)}")
            return {}
    
    async def _aggregate_confidence(self, intent_analysis: IntentAnalysisResult, technical_plan: TechnicalPlan, sme_consultations: Dict[str, Any]) -> float:
        """Aggregate confidence from all brain components"""
        try:
            # Base confidence from intent and technical analysis
            intent_confidence = intent_analysis.overall_confidence
            technical_confidence = technical_plan.confidence_score
            
            # SME confidence (average of all consultations)
            sme_confidences = []
            for domain, consultation in sme_consultations.items():
                if "error" not in consultation:
                    # Extract confidence from SME recommendations
                    recommendations = consultation.get("recommendations", [])
                    if recommendations:
                        avg_sme_confidence = sum(rec.get("confidence", 0.5) for rec in recommendations) / len(recommendations)
                        sme_confidences.append(avg_sme_confidence)
            
            sme_confidence = sum(sme_confidences) / len(sme_confidences) if sme_confidences else 0.5
            
            # Weighted aggregation
            weights = {
                "intent": 0.4,
                "technical": 0.4,
                "sme": 0.2
            }
            
            overall_confidence = (
                intent_confidence * weights["intent"] +
                technical_confidence * weights["technical"] +
                sme_confidence * weights["sme"]
            )
            
            return max(0.0, min(1.0, overall_confidence))
            
        except Exception as e:
            logger.error(f"Error aggregating confidence: {str(e)}")
            return 0.5  # Default confidence
    
    async def _determine_execution_strategy(self, overall_confidence: float, technical_plan: TechnicalPlan, intent_analysis: IntentAnalysisResult) -> str:
        """Determine execution strategy based on confidence and risk"""
        try:
            # Check if this is an informational query
            if (hasattr(intent_analysis, 'four_w_analysis') and 
                hasattr(intent_analysis.four_w_analysis, 'what_analysis') and
                hasattr(intent_analysis.four_w_analysis.what_analysis, 'action_type') and
                intent_analysis.four_w_analysis.what_analysis.action_type.value == 'information'):
                return "informational_response"
            
            # High confidence and low risk: Automated execution
            if overall_confidence >= 0.8 and intent_analysis.risk_level == "low":
                return "automated_execution"
            
            # Medium confidence: Guided execution with validation
            elif overall_confidence >= 0.6:
                return "guided_execution"
            
            # Low confidence or high risk: Manual review required
            elif overall_confidence < 0.4 or intent_analysis.risk_level == "high":
                return "manual_review"
            
            # Default: Assisted execution
            else:
                return "assisted_execution"
                
        except Exception as e:
            logger.error(f"Error determining execution strategy: {str(e)}")
            return "manual_review"  # Safe default
    
    async def _generate_recommendations(self, technical_plan: TechnicalPlan, sme_consultations: Dict[str, Any], execution_strategy: str) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            # Check if this is an informational query that should provide direct answers
            if execution_strategy == "informational_response":
                recommendations.append("Information provided based on available data")
                recommendations.append("No further action required")
                return recommendations
            
            # Add strategy-specific recommendations
            if execution_strategy == "automated_execution":
                recommendations.append("Execute plan automatically with monitoring")
                recommendations.append("Set up automated rollback on failure")
            elif execution_strategy == "guided_execution":
                recommendations.append("Execute plan with step-by-step validation")
                recommendations.append("Require approval for high-risk steps")
            elif execution_strategy == "manual_review":
                recommendations.append("Manual review required before execution")
                recommendations.append("Consider breaking down into smaller steps")
            else:  # assisted_execution
                recommendations.append("Review the analysis and proceed with appropriate action")
                recommendations.append("Validate each step before proceeding")
            
            # Add technical recommendations
            if technical_plan.steps:
                recommendations.append(f"Execute {len(technical_plan.steps)} planned steps")
                if technical_plan.estimated_duration > 300:  # 5 minutes
                    recommendations.append("Consider scheduling during maintenance window")
            
            # Add SME recommendations
            for domain, consultation in sme_consultations.items():
                if "recommendations" in consultation:
                    domain_recs = consultation["recommendations"]
                    if domain_recs:
                        recommendations.append(f"Follow {domain} expert recommendations")
            
            # Add risk-based recommendations
            if technical_plan.risk_assessment.get("overall_risk") == "high":
                recommendations.append("Implement additional safety measures")
                recommendations.append("Prepare rollback procedures")
            
            return recommendations[:10]  # Limit to top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Manual review recommended due to processing error"]
    
    async def _aggregate_risk_assessment(self, technical_plan: TechnicalPlan, sme_consultations: Dict[str, Any], intent_analysis: IntentAnalysisResult) -> Dict[str, Any]:
        """Aggregate risk assessment from all sources"""
        try:
            risk_assessment = {
                "overall_risk_level": intent_analysis.risk_level,
                "risk_factors": intent_analysis.risk_factors.copy(),
                "technical_risks": technical_plan.risk_assessment,
                "sme_risks": {},
                "mitigation_strategies": []
            }
            
            # Aggregate SME risk assessments
            for domain, consultation in sme_consultations.items():
                if "risk_assessment" in consultation:
                    risk_assessment["sme_risks"][domain] = consultation["risk_assessment"]
                
                if "risk_mitigation_strategies" in consultation:
                    risk_assessment["mitigation_strategies"].extend(consultation["risk_mitigation_strategies"])
            
            # Determine overall risk level
            risk_levels = [intent_analysis.risk_level]
            if technical_plan.risk_assessment.get("overall_risk"):
                risk_levels.append(technical_plan.risk_assessment["overall_risk"])
            
            for consultation in sme_consultations.values():
                if "risk_assessment" in consultation and "overall_risk_level" in consultation["risk_assessment"]:
                    risk_levels.append(consultation["risk_assessment"]["overall_risk_level"])
            
            # Use highest risk level
            if "high" in risk_levels:
                risk_assessment["overall_risk_level"] = "high"
            elif "medium" in risk_levels:
                risk_assessment["overall_risk_level"] = "medium"
            else:
                risk_assessment["overall_risk_level"] = "low"
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error aggregating risk assessment: {str(e)}")
            return {"overall_risk_level": "high", "error": str(e)}
    
    async def _update_metrics(self, result: MultiBrainProcessingResult):
        """Update performance metrics"""
        try:
            self.performance_metrics["total_requests"] += 1
            
            if result.overall_confidence > 0.5:  # Consider successful if confidence > 0.5
                self.performance_metrics["successful_requests"] += 1
            
            # Update average processing time
            total_requests = self.performance_metrics["total_requests"]
            current_avg_time = self.performance_metrics["average_processing_time"]
            new_avg_time = ((current_avg_time * (total_requests - 1)) + result.processing_time) / total_requests
            self.performance_metrics["average_processing_time"] = new_avg_time
            
            # Update average confidence
            current_avg_confidence = self.performance_metrics["average_confidence"]
            new_avg_confidence = ((current_avg_confidence * (total_requests - 1)) + result.overall_confidence) / total_requests
            self.performance_metrics["average_confidence"] = new_avg_confidence
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get current status of the multi-brain engine"""
        try:
            # Get brain statuses
            brain_statuses = {}
            
            brain_statuses["intent_brain"] = await self.intent_brain.get_brain_status()
            brain_statuses["technical_brain"] = await self.technical_brain.get_brain_status()
            
            for domain, sme_brain in self.sme_brains.items():
                brain_statuses[f"sme_{domain}"] = await sme_brain.get_brain_status()
            
            return {
                "engine_id": self.engine_id,
                "engine_version": self.engine_version,
                "phase": self.phase,
                "status": "active",
                "confidence_threshold": self.confidence_threshold,
                "brain_count": 2 + len(self.sme_brains),  # Intent + Technical + SME brains
                "sme_domains": list(self.sme_brains.keys()),
                "performance_metrics": self.performance_metrics,
                "request_history_size": len(self.request_history),
                "brain_statuses": brain_statuses
            }
            
        except Exception as e:
            logger.error(f"Error getting engine status: {str(e)}")
            return {"error": str(e)}
    
    async def get_recent_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent request history"""
        try:
            recent_requests = self.request_history[-limit:]
            return [request.to_dict() for request in recent_requests]
        except Exception as e:
            logger.error(f"Error getting recent requests: {str(e)}")
            return []
    
    async def _initialize_communication_protocol(self):
        """Initialize the brain communication protocol"""
        try:
            await self.communication_protocol.initialize_brains(
                self.intent_brain,
                self.technical_brain,
                self.sme_brains
            )
            logger.info("Brain communication protocol initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing communication protocol: {str(e)}")
    
    async def _initialize_learning_systems(self):
        """Initialize the learning systems"""
        try:
            # Initialize continuous learning system with quality assurance
            await self.continuous_learning_system.initialize(self.learning_quality_assurance)
            
            # Add trusted sources to quality assurance
            await self.learning_quality_assurance.add_trusted_source("execution_feedback_analyzer")
            await self.learning_quality_assurance.add_trusted_source("cross_brain_learner")
            
            # Initialize brain reliability in confidence engine
            for brain_name in self.sme_brains.keys():
                # SME brains start with high reliability
                self.multibrain_confidence_engine.brain_reliability_scores[brain_name] = 1.1
            
            logger.info("Learning systems initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing learning systems: {str(e)}")
    
    async def process_request_with_protocol(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> MultibrainAnalysis:
        """
        Process request using the new Brain Communication Protocol
        
        This method uses the advanced communication protocol for coordinated multi-brain analysis.
        """
        try:
            logger.info("Processing request with Brain Communication Protocol")
            
            # Use the communication protocol for coordinated analysis
            analysis = await self.communication_protocol.coordinate_multi_brain_analysis(user_message)
            
            # Update performance metrics
            self.performance_metrics["total_requests"] += 1
            if analysis.aggregated_confidence > 0.5:
                self.performance_metrics["successful_requests"] += 1
            
            # Update average metrics
            total_requests = self.performance_metrics["total_requests"]
            if total_requests > 0:
                current_avg_time = self.performance_metrics["average_processing_time"]
                analysis_time = analysis.analysis_metadata.get("total_duration", 0)
                self.performance_metrics["average_processing_time"] = (
                    (current_avg_time * (total_requests - 1) + analysis_time) / total_requests
                )
                
                current_avg_confidence = self.performance_metrics["average_confidence"]
                self.performance_metrics["average_confidence"] = (
                    (current_avg_confidence * (total_requests - 1) + analysis.aggregated_confidence) / total_requests
                )
            
            logger.info(f"Protocol-based analysis completed with confidence: {analysis.aggregated_confidence}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in protocol-based processing: {str(e)}")
            raise
    
    async def process_execution_feedback(self, request_id: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process execution feedback for continuous learning
        
        Args:
            request_id: ID of the original request
            execution_result: Results from executing the recommended actions
            
        Returns:
            Dict containing learning insights and updates
        """
        try:
            logger.info(f"Processing execution feedback for request: {request_id}")
            
            # Find the original request in history
            original_request = None
            for request in self.request_history:
                if request.get("request_id") == request_id:
                    original_request = request
                    break
            
            if not original_request:
                logger.warning(f"Original request {request_id} not found in history")
                return {"success": False, "error": "Original request not found"}
            
            # Process feedback through continuous learning system
            learning_result = await self.continuous_learning_system.process_execution_feedback(
                original_request,
                execution_result
            )
            
            # Update confidence engine with execution outcomes
            if execution_result.get("success", False):
                # Successful execution - increase brain reliability
                for brain_name in original_request.get("consulted_brains", []):
                    await self.multibrain_confidence_engine.update_brain_reliability(
                        brain_name, 
                        True,
                        execution_result.get("confidence_accuracy", 0.8)
                    )
            else:
                # Failed execution - decrease brain reliability
                for brain_name in original_request.get("consulted_brains", []):
                    await self.multibrain_confidence_engine.update_brain_reliability(
                        brain_name, 
                        False,
                        execution_result.get("confidence_accuracy", 0.2)
                    )
            
            # Update performance metrics
            self.performance_metrics["total_requests"] += 1
            if execution_result.get("success", False):
                self.performance_metrics["successful_requests"] += 1
            
            logger.info(f"Execution feedback processed successfully for {request_id}")
            return {
                "success": True,
                "learning_insights": learning_result,
                "updated_brain_reliability": self.multibrain_confidence_engine.brain_reliability_scores
            }
            
        except Exception as e:
            logger.error(f"Error processing execution feedback: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive learning insights from all systems
        
        Returns:
            Dict containing learning metrics, brain reliability, and system status
        """
        try:
            # Get learning system metrics
            learning_metrics = await self.continuous_learning_system.get_learning_metrics()
            
            # Get confidence engine status
            confidence_status = {
                "brain_reliability_scores": self.multibrain_confidence_engine.brain_reliability_scores,
                "confidence_history": getattr(self.multibrain_confidence_engine, 'confidence_history', [])[-10:],  # Last 10 entries
                "calibration_accuracy": getattr(self.multibrain_confidence_engine, 'calibration_accuracy', 0.0)
            }
            
            # Get quality assurance metrics
            qa_metrics = await self.learning_quality_assurance.get_quality_metrics()
            
            # Get communication protocol metrics
            protocol_metrics = await self.communication_protocol.get_communication_metrics()
            
            return {
                "learning_system": learning_metrics,
                "confidence_engine": confidence_status,
                "quality_assurance": qa_metrics,
                "communication_protocol": protocol_metrics,
                "performance_metrics": self.performance_metrics,
                "system_status": {
                    "phase": "phase_2",
                    "active_sme_brains": list(self.sme_brains.keys()),
                    "total_requests_processed": len(self.request_history),
                    "engine_version": self.engine_version
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting learning insights: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the Multi-Brain AI Engine.
        
        Returns:
            Dict containing health status information
        """
        return {
            "status": "healthy",
            "service": "ai-brain",
            "engine_type": "multi_brain_ai_engine",
            "engine_version": self.engine_version,
            "phase": self.phase,
            "components": {
                "intent_brain": hasattr(self, 'intent_brain') and self.intent_brain is not None,
                "technical_brain": hasattr(self, 'technical_brain') and self.technical_brain is not None,
                "sme_brains": {
                    "count": len(self.sme_brains),
                    "active_domains": list(self.sme_brains.keys())
                },
                "communication_protocol": self._communication_initialized,
                "learning_systems": self._learning_initialized,
                "continuous_learning": hasattr(self, 'continuous_learning_system'),
                "quality_assurance": hasattr(self, 'learning_quality_assurance'),
                "confidence_engine": hasattr(self, 'multibrain_confidence_engine')
            },
            "performance_metrics": self.performance_metrics,
            "configuration": {
                "confidence_threshold": self.confidence_threshold,
                "max_processing_time": self.max_processing_time
            },
            "architecture": "multi_brain_phase_2",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Legacy compatibility methods for gradual migration
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy compatibility method"""
        result = await self.process_request(message, context)
        
        # Convert to legacy format for backward compatibility
        return {
            "success": True,
            "confidence": result.overall_confidence,
            "intent": result.intent_analysis.intent_summary,
            "response": result.recommended_actions[0] if result.recommended_actions else "No action recommended",
            "execution_plan": result.technical_plan.to_dict() if result.technical_plan else None,
            "risk_level": result.risk_assessment.get("overall_risk_level", "medium"),
            "processing_time": result.processing_time,
            "multi_brain_result": result.to_dict()  # Full result for modern clients
        }
    
    async def create_job_from_natural_language(self, description: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create an executable job from natural language description using Multi-Brain Architecture.
        
        This method leverages the multi-brain system to:
        1. INTENT BRAIN: Understand what the user wants to accomplish
        2. TECHNICAL BRAIN: Plan the technical execution steps
        3. SME BRAINS: Provide domain-specific expertise and validation
        4. CONFIDENCE ENGINE: Assess overall feasibility and risk
        5. JOB CREATION: Generate executable workflow
        
        Args:
            description: Natural language description of the desired job
            user_context: Optional user context information
            
        Returns:
            Dict containing the created job or error information
        """
        try:
            logger.info(f"🧠 Multi-Brain job creation requested: {description[:50]}...")
            
            # Process through multi-brain architecture
            result = await self.process_request(description, user_context or {})
            
            # Check if we have sufficient confidence to create a job
            if result.overall_confidence < self.confidence_threshold:
                return {
                    "success": False,
                    "error": f"Insufficient confidence ({result.overall_confidence:.2%}) to create job safely",
                    "confidence": result.overall_confidence,
                    "threshold": self.confidence_threshold,
                    "clarification_needed": True,
                    "intent_analysis": result.intent_analysis.to_dict() if result.intent_analysis else None,
                    "risk_assessment": result.risk_assessment,
                    "recommended_actions": result.recommended_actions
                }
            
            # Generate job workflow from technical plan
            if not result.technical_plan or not result.technical_plan.steps:
                return {
                    "success": False,
                    "error": "Unable to generate technical execution plan",
                    "confidence": result.overall_confidence,
                    "intent_analysis": result.intent_analysis.to_dict() if result.intent_analysis else None
                }
            
            # Create job structure
            job_id = f"mb_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.request_history)}"
            
            # Convert technical plan to executable workflow
            workflow = {
                "job_id": job_id,
                "name": result.intent_analysis.intent_summary if result.intent_analysis else "Multi-Brain Generated Job",
                "description": description,
                "steps": [],
                "metadata": {
                    "created_by": "multi_brain_ai_engine",
                    "engine_version": self.engine_version,
                    "confidence": result.overall_confidence,
                    "intent_analysis": result.intent_analysis.to_dict() if result.intent_analysis else None,
                    "technical_plan": result.technical_plan.to_dict() if result.technical_plan else None,
                    "sme_consultations": result.sme_consultations,
                    "risk_assessment": result.risk_assessment,
                    "processing_time": result.processing_time
                }
            }
            
            # Convert technical plan steps to workflow steps
            for i, step in enumerate(result.technical_plan.steps):
                workflow_step = {
                    "step_id": f"step_{i+1}",
                    "name": step.get("name", f"Step {i+1}"),
                    "description": step.get("description", ""),
                    "action": step.get("action", "manual"),
                    "parameters": step.get("parameters", {}),
                    "dependencies": step.get("dependencies", []),
                    "estimated_duration": step.get("estimated_duration", 300),  # 5 minutes default
                    "risk_level": step.get("risk_level", "medium"),
                    "validation_criteria": step.get("validation_criteria", []),
                    "rollback_steps": step.get("rollback_steps", [])
                }
                workflow["steps"].append(workflow_step)
            
            # Add SME recommendations as validation steps
            for domain, consultation in result.sme_consultations.items():
                if isinstance(consultation, dict) and consultation.get("recommendations"):
                    for rec in consultation["recommendations"][:2]:  # Limit to top 2 recommendations
                        validation_step = {
                            "step_id": f"validation_{domain}_{len(workflow['steps'])+1}",
                            "name": f"{domain.replace('_', ' ').title()} Validation",
                            "description": rec.get("description", "SME validation step"),
                            "action": "validation",
                            "parameters": {
                                "domain": domain,
                                "validation_type": rec.get("recommendation_type", "best_practice"),
                                "criteria": rec.get("validation_criteria", [])
                            },
                            "estimated_duration": 60,  # 1 minute for validation
                            "risk_level": "low"
                        }
                        workflow["steps"].append(validation_step)
            
            logger.info(f"✅ Multi-Brain job created successfully: {job_id} with {len(workflow['steps'])} steps")
            
            return {
                "success": True,
                "job_id": job_id,
                "workflow": workflow,
                "confidence": result.overall_confidence,
                "execution_strategy": result.execution_strategy,
                "estimated_duration": sum(step.get("estimated_duration", 300) for step in workflow["steps"]),
                "risk_assessment": result.risk_assessment,
                "multi_brain_analysis": result.to_dict(),
                "message": f"Job '{workflow['name']}' created successfully using Multi-Brain Architecture with {result.overall_confidence:.1%} confidence"
            }
            
        except Exception as e:
            logger.error(f"Multi-brain job creation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Multi-brain job creation failed: {str(e)}",
                "confidence": 0.0,
                "fallback_message": "Please try rephrasing your request or use the manual job creation interface"
            }