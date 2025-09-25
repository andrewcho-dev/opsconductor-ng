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
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict, field

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
class IntentOnlyResult:
    """Result for intent-only analysis mode"""
    # Request information
    request_id: str
    user_message: str
    timestamp: datetime
    
    # Intent analysis only
    intent_analysis: IntentAnalysisResult
    
    # Processing metadata
    processing_time: float
    brains_consulted: List[str]
    phase: str = "intent_only"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "request_id": self.request_id,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "intent_analysis": self.intent_analysis.to_dict(),
            "processing_time": self.processing_time,
            "brains_consulted": self.brains_consulted,
            "phase": self.phase
        }

@dataclass
class MultiBrainProcessingResult:
    """Complete result from multi-brain processing"""
    # Request information (required fields first)
    request_id: str
    user_message: str
    timestamp: datetime
    intent_analysis: IntentAnalysisResult
    overall_confidence: float
    execution_strategy: str
    recommended_actions: List[str]
    risk_assessment: Dict[str, Any]
    processing_time: float
    brains_consulted: List[str]
    
    # Optional fields with defaults last
    technical_plan: Optional[TechnicalPlan] = None
    sme_consultations: Dict[str, Any] = field(default_factory=dict)
    phase: str = "phase_1"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "request_id": self.request_id,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "intent_analysis": self.intent_analysis.to_dict(),
            "technical_plan": self.technical_plan.to_dict() if self.technical_plan else None,
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
        self.llm_engine = llm_engine
        
        # Initialize brain components - ALL brains now use LLM for intelligence
        self.intent_brain = IntentBrain(llm_engine)
        self.technical_brain = TechnicalBrain(llm_engine)
        
        # Initialize SME brains (Phase 2: All SME brains) - ALL now use LLM for intelligence
        self.sme_brains = {
            "container_orchestration": ContainerSMEBrain(llm_engine),
            "security_and_compliance": SecuritySMEBrain(llm_engine),
            "network_infrastructure": NetworkSMEBrain(llm_engine),
            "database_administration": DatabaseSMEBrain(llm_engine)
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
            # Look for IP addresses, hostnames, and asset-related keywords in the query
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ip_addresses = re.findall(ip_pattern, query)
            
            # Look for hostname patterns (common server naming conventions)
            hostname_pattern = r'\b(?:server|host|node|vm|machine|workstation|pc|desktop|laptop)[-_]?\w*\b'
            hostnames = re.findall(hostname_pattern, query.lower())
            
            # Look for asset-related keywords that indicate we should check the database
            asset_keywords = [
                'asset', 'machine', 'server', 'host', 'system', 'device', 'computer',
                'workstation', 'desktop', 'laptop', 'vm', 'virtual', 'node',
                'credential', 'password', 'username', 'login', 'access', 'connect',
                'communication', 'port', 'service', 'protocol', 'ssh', 'rdp', 'winrm',
                'windows', 'linux', 'ubuntu', 'centos', 'debian', 'os', 'operating',
                'how many', 'count', 'list', 'show', 'what', 'which', 'where'
            ]
            
            has_asset_keywords = any(keyword in query.lower() for keyword in asset_keywords)
            
            logger.info(f"🔍 Found IP addresses: {ip_addresses}")
            logger.info(f"🔍 Found hostnames: {hostnames}")  
            logger.info(f"🔍 Has asset keywords: {has_asset_keywords}")
            
            # ALWAYS check assets if we have IP addresses or asset-related content
            should_check_assets = bool(ip_addresses) or bool(hostnames) or has_asset_keywords
            
            if not should_check_assets:
                logger.info("🔍 Query doesn't appear to be asset-related")
                return None
            
            logger.info("🔍 Query appears to be asset-related - checking database")
            
            if ip_addresses:
                # Look up specific IP addresses
                asset_info = {}
                for ip in ip_addresses:
                    logger.info(f"🔍 Looking up asset information for IP: {ip}")
                    print(f"DEBUG: Looking up asset information for IP: {ip}")
                    asset = await self.asset_client.get_asset_by_ip(ip)
                    print(f"DEBUG: Asset result for {ip}: {asset}")
                    if asset:
                        asset_info[ip] = asset
                        logger.info(f"✅ Found asset information for IP {ip}: {asset.get('name', 'Unknown')} ({asset.get('os_type', 'Unknown OS')})")
                        print(f"DEBUG: ✅ Found asset information for IP {ip}: {asset.get('name', 'Unknown')} ({asset.get('os_type', 'Unknown OS')})")
                    else:
                        logger.warning(f"❌ No asset found for IP {ip}")
                        print(f"DEBUG: ❌ No asset found for IP {ip}")
                
                logger.info(f"🔍 Asset lookup result: {len(asset_info)} assets found")
                return asset_info if asset_info else None
                
            else:
                # Fetch all assets for intelligent analysis
                logger.info("🔍 Fetching all assets for intelligent LLM analysis")
                all_assets = await self.asset_client.get_all_assets()
                if all_assets:
                    asset_info = {}
                    for asset in all_assets:
                        ip = asset.get('ip_address')
                        if ip:
                            asset_info[ip] = asset
                    
                    logger.info(f"✅ Fetched {len(asset_info)} assets for intelligent analysis")
                    return asset_info if asset_info else None
                else:
                    logger.warning("❌ No assets found in system")
                    return None
            
        except Exception as e:
            logger.error(f"❌ Error looking up asset information: {str(e)}")
            return None
    
    async def _generate_intelligent_asset_answer(self, query: str, formatted_assets: List[Dict]) -> Optional[str]:
        """
        Generate an intelligent answer for asset queries using LLM analysis.
        
        This method implements human-like database analysis:
        1. Examine what data is available (schema discovery)
        2. Understand field meanings and relationships
        3. Reason about which fields are relevant to the query
        4. Formulate an intelligent analysis strategy
        5. Execute the analysis and provide precise answers
        
        Args:
            query: The user's query
            formatted_assets: List of complete asset data with all database fields
            
        Returns:
            Intelligent answer string if applicable, None otherwise
        """
        if not formatted_assets:
            logger.warning("No formatted assets provided for intelligent analysis")
            return None
            
        if not hasattr(self, 'llm_engine') or not self.llm_engine:
            logger.error("LLM engine not available for intelligent asset analysis")
            return None
            
        try:
            # STEP 1: Schema Discovery - Let the AI examine what data is available
            # Get a sample asset to understand the schema
            sample_asset = formatted_assets[0] if formatted_assets else {}
            available_fields = list(sample_asset.keys())
            
            # STEP 2: Present raw data to AI for intelligent analysis
            # No hardcoded formatting - let the AI understand the schema naturally
            import json
            raw_asset_data = json.dumps(formatted_assets, indent=2, default=str)
            
            # Create intelligent system prompt for human-like database analysis
            system_prompt = """You are an IT asset database analyst. Provide direct, accurate answers to user queries about the asset database.

INSTRUCTIONS:
- Examine the asset data provided
- Look for assets that match the user's criteria
- Count the matches carefully
- Provide a clear, direct answer

RESPONSE FORMAT:
- Give a direct answer in 1-2 sentences
- Include specific asset names and details when relevant
- Be precise with counts"""

            # Create the analysis prompt with raw data
            analysis_prompt = f"""User Question: {query}

Asset Database:
{raw_asset_data}

Analyze the asset data and answer the user's question directly."""

            logger.info(f"Sending raw asset data to LLM for intelligent schema-aware analysis")
            logger.info(f"Available fields detected: {available_fields}")
            logger.info(f"Total assets to analyze: {len(formatted_assets)}")
            
            # Get intelligent analysis from LLM
            response = await self.llm_engine.chat(
                message=analysis_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"LLM response received: {response}")
            
            if response and 'response' in response:
                # Return both the LLM response and the raw asset data for fallback processing
                return {
                    'llm_response': response['response'].strip(),
                    'assets': formatted_assets,
                    'summary': response['response'].strip()
                }
            else:
                logger.warning("LLM response was empty or malformed")
                # Still return asset data for fallback processing
                return {
                    'assets': formatted_assets,
                    'summary': f"Found {len(formatted_assets)} assets in the database."
                }
                
        except Exception as e:
            logger.error(f"Error in intelligent asset analysis: {str(e)}")
            return None

    async def _synthesize_final_response(self, query: str, multi_brain_result, asset_analysis: Optional[str] = None) -> str:
        """
        RESTORE THE ORIGINAL INTENT: Synthesize ALL brain intelligence into one authoritative answer
        
        This method combines:
        - Multi-brain strategic analysis
        - SME expert consultations  
        - Technical brain insights
        - Intelligent asset analysis
        - Intent analysis
        
        Into one comprehensive, authoritative response that uses ALL the intelligence
        instead of throwing it away like the broken implementation was doing.
        
        Args:
            query: The user's original query
            multi_brain_result: The complete multi-brain processing result
            asset_analysis: Optional intelligent asset analysis
            
        Returns:
            Synthesized final response that combines ALL intelligence
        """
        logger.info("🚀 SYNTHESIS METHOD CALLED - Starting final response synthesis")
        print("DEBUG: SYNTHESIS METHOD CALLED - Starting final response synthesis")
        
        # Initialize synthesis_components early to avoid NameError in exception handler
        synthesis_components = []
        
        if not hasattr(self, 'llm_engine') or not self.llm_engine:
            logger.warning("No LLM engine available for synthesis - falling back to asset analysis data")
            return self._create_fallback_response(asset_analysis, synthesis_components)
        
        try:
            # Extract all the intelligence that was being WASTED
            logger.info(f"🔍 DEBUG: Starting synthesis with multi_brain_result type: {type(multi_brain_result)}")
            logger.info(f"🔍 DEBUG: SME consultations type: {type(multi_brain_result.sme_consultations) if hasattr(multi_brain_result, 'sme_consultations') else 'None'}")
            if hasattr(multi_brain_result, 'sme_consultations') and multi_brain_result.sme_consultations:
                # SME consultations is a dictionary, not a list
                first_key = next(iter(multi_brain_result.sme_consultations.keys())) if multi_brain_result.sme_consultations else None
                if first_key:
                    logger.info(f"🔍 DEBUG: First SME consultation type: {type(multi_brain_result.sme_consultations[first_key])}")
                else:
                    logger.info("🔍 DEBUG: SME consultations dictionary is empty")
            
            # 1. Multi-brain strategic analysis
            if multi_brain_result.recommended_actions:
                synthesis_components.append({
                    'type': 'strategic_analysis',
                    'content': multi_brain_result.recommended_actions[0],
                    'confidence': multi_brain_result.overall_confidence,
                    'source': 'multi_brain_orchestrator'
                })
            
            # 2. SME expert consultations (STOP WASTING THESE!)
            if hasattr(multi_brain_result, 'sme_consultations') and multi_brain_result.sme_consultations:
                try:
                    logger.info(f"🔍 DEBUG: Processing {len(multi_brain_result.sme_consultations)} SME consultations")
                    for domain, sme in multi_brain_result.sme_consultations.items():
                        logger.info(f"🔍 DEBUG: SME domain {domain} type: {type(sme)}")
                        # Handle both dict and string formats
                        if isinstance(sme, dict):
                            # Extract recommendations from the SME consultation
                            recommendations = sme.get('recommendations', [])
                            if recommendations:
                                # If recommendations is a list, process each one
                                if isinstance(recommendations, list):
                                    for rec in recommendations:
                                        if isinstance(rec, dict):
                                            synthesis_components.append({
                                                'type': 'expert_consultation',
                                                'content': rec.get('description', rec.get('title', str(rec))),
                                                'expertise': domain,
                                                'reasoning': rec.get('rationale', ''),
                                                'confidence': rec.get('confidence', 0.5),
                                                'source': 'sme_brain'
                                            })
                                        else:
                                            synthesis_components.append({
                                                'type': 'expert_consultation',
                                                'content': str(rec),
                                                'expertise': domain,
                                                'reasoning': '',
                                                'confidence': 0.5,
                                                'source': 'sme_brain'
                                            })
                                else:
                                    # If recommendations is not a list, treat as single recommendation
                                    synthesis_components.append({
                                        'type': 'expert_consultation',
                                        'content': str(recommendations),
                                        'expertise': domain,
                                        'reasoning': '',
                                        'confidence': 0.5,
                                        'source': 'sme_brain'
                                    })
                            else:
                                # No specific recommendations, use general content
                                synthesis_components.append({
                                    'type': 'expert_consultation',
                                    'content': str(sme),
                                    'expertise': domain,
                                    'reasoning': '',
                                    'confidence': 0.5,
                                    'source': 'sme_brain'
                                })
                        elif isinstance(sme, str):
                            synthesis_components.append({
                                'type': 'expert_consultation',
                                'content': sme,
                                'expertise': domain,
                                'reasoning': '',
                                'confidence': 0.5,
                                'source': 'sme_brain'
                            })
                        else:
                            # Handle other formats by converting to string
                            synthesis_components.append({
                                'type': 'expert_consultation',
                                'content': str(sme),
                                'expertise': domain,
                                'reasoning': '',
                                'confidence': 0.5,
                                'source': 'sme_brain'
                            })
                except Exception as sme_error:
                    logger.error(f"Error processing SME consultations: {sme_error}")
                    # Continue without SME data
            
            # 3. Technical analysis insights
            if hasattr(multi_brain_result, 'technical_plan') and multi_brain_result.technical_plan:
                tech_plan = multi_brain_result.technical_plan
                if hasattr(tech_plan, 'to_dict'):
                    tech_dict = tech_plan.to_dict()
                else:
                    tech_dict = {'analysis': str(tech_plan)}
                
                synthesis_components.append({
                    'type': 'technical_analysis',
                    'content': tech_dict.get('analysis', str(tech_plan)),
                    'recommendations': tech_dict.get('recommendations', []),
                    'source': 'technical_brain'
                })
            
            # 4. Intent analysis
            if hasattr(multi_brain_result, 'intent_analysis') and multi_brain_result.intent_analysis:
                intent = multi_brain_result.intent_analysis
                if hasattr(intent, 'to_dict'):
                    intent_dict = intent.to_dict()
                else:
                    intent_dict = {'intent_type': str(intent)}
                
                synthesis_components.append({
                    'type': 'intent_analysis',
                    'content': intent_dict.get('analysis', ''),
                    'intent_type': intent_dict.get('intent_type', 'unknown'),
                    'source': 'intent_brain'
                })
            
            # 5. Intelligent asset analysis (if available)
            if asset_analysis:
                # Handle both old string format and new dict format
                if isinstance(asset_analysis, dict):
                    content = asset_analysis.get('llm_response', asset_analysis.get('summary', str(asset_analysis)))
                else:
                    content = str(asset_analysis)
                
                synthesis_components.append({
                    'type': 'asset_analysis',
                    'content': content,
                    'confidence': 0.9,
                    'source': 'asset_intelligence'
                })
            
            # Create intelligent synthesis system prompt
            system_prompt = """You are the Final Synthesis AI for OpsConductor's multi-brain system.

Your job is to provide clean, direct answers to user queries by synthesizing intelligence from multiple AI brains.

CRITICAL REQUIREMENTS:
- Provide ONLY the final answer - do not show your analysis process
- Do not use section headers like "Analyze User's Intent", "Identify Relevant Information", etc.
- Do not explain your synthesis methodology 
- Do not show step-by-step reasoning
- Give a direct, professional response that answers the user's question

SYNTHESIS APPROACH:
- For factual queries (counts, lists, status): Use asset analysis as the primary source of truth
- For operational tasks: Combine technical analysis with expert recommendations  
- For strategic decisions: Leverage strategic analysis with expert consultations
- Asset analysis is typically most accurate for infrastructure and inventory questions
- When sources conflict, use the most reliable and relevant source

RESPONSE STYLE:
- Direct and concise
- Professional tone
- Include specific details when relevant (names, counts, IPs, etc.)
- No meta-commentary about your analysis process
- No section headers or structured breakdowns

Your goal is to provide the MOST ACCURATE ANSWER in a clean, readable format."""

            # Format the synthesis data
            synthesis_prompt = f"""User Query: {query}

INTELLIGENCE TO SYNTHESIZE:
"""
            
            for i, component in enumerate(synthesis_components, 1):
                synthesis_prompt += f"""
{i}. {component['type'].upper()} (Source: {component['source']})
   Content: {component['content']}
"""
                if 'expertise' in component:
                    synthesis_prompt += f"   Expertise Area: {component['expertise']}\n"
                if 'reasoning' in component:
                    synthesis_prompt += f"   Reasoning: {component['reasoning']}\n"
                if 'confidence' in component:
                    synthesis_prompt += f"   Confidence: {component['confidence']}\n"

            # Add intelligent synthesis task instructions
            synthesis_prompt += """
CRITICAL: You MUST respond in a simple, direct format. Do NOT use any analysis headers or structured breakdowns.

FORBIDDEN FORMATS (DO NOT USE):
- "**ANALYZE THE USER'S INTENT:**"
- "**IDENTIFY RELEVANT INFORMATION:**"
- "**CROSS-REFERENCE DATA:**"
- "**RESOLVE CONFLICTS:**"
- "**SYNTHESIZE INTELLIGENTLY:**"
- "**SANITY CHECK:**"
- "Based on the provided intelligence sources"
- "Final Synthesis Response"

REQUIRED FORMAT:
Answer the user's question directly in 1-2 sentences maximum.

For the query "how many Windows 11 machines do we have?", respond like this:
"We have 1 Windows 11 machine: win11-test01 (IP: 192.168.50.214)."

NOT like this:
"**ANALYZE THE USER'S INTENT:** The user is asking for..."

Use asset analysis data as your primary source for factual queries. Give a direct answer only."""

            # Get the synthesis from LLM
            logger.info("🎯 Performing final LLM synthesis of ALL brain intelligence")
            logger.info(f"🔍 DEBUG: Synthesis prompt length: {len(synthesis_prompt)}")
            logger.info(f"🔍 DEBUG: System prompt length: {len(system_prompt)}")
            
            response = await self.llm_engine.chat(
                message=synthesis_prompt,
                system_prompt=system_prompt
            )
            
            logger.info(f"🔍 DEBUG: LLM response type: {type(response)}")
            logger.info(f"🔍 DEBUG: LLM response content: {response}")
            
            if response and 'response' in response:
                synthesized_answer = response['response'].strip()
                logger.info(f"✅ Final synthesis completed - combined {len(synthesis_components)} intelligence sources")
                logger.info(f"🔍 DEBUG: Raw LLM response: '{response['response']}'")
                logger.info(f"🔍 DEBUG: After strip(): '{synthesized_answer}'")
                logger.info(f"🔍 DEBUG: Ends with period: {synthesized_answer.endswith('.')}")
                logger.info(f"🔍 DEBUG: Last 5 chars: '{synthesized_answer[-5:]}'")
                return synthesized_answer
            else:
                logger.warning(f"LLM synthesis failed - response format invalid: {response}")
                logger.warning("Falling back to asset analysis data")
                return self._create_fallback_response(asset_analysis, synthesis_components)
                
        except Exception as e:
            logger.error(f"Error in final synthesis: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {repr(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to asset analysis data
            logger.warning("Exception occurred - falling back to asset analysis data")
            return self._create_fallback_response(asset_analysis, synthesis_components)

    
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
                        'has_credentials': asset.get('has_credentials', False),
                        'description': asset.get('description', 'No description available'),
                        'tags': asset.get('tags', []),
                        'status': asset.get('connection_status', 'Unknown'),
                        'is_active': asset.get('is_active', False)
                    }
                    formatted_assets.append(asset_summary)
                
                context['asset_information'] = formatted_assets
                context['asset_query_context'] = f"The user is asking about assets. Available asset information has been provided for the following IP addresses: {', '.join(asset_info.keys())}. Use this information to answer their question directly."
                
                # Use LLM to intelligently determine query type
                if self.llm_engine:
                    try:
                        query_type_prompt = f"""Analyze this query and determine if it's asking for information (vs. asking to perform an action):

Query: "{query}"

Is this query asking for INFORMATION (like "how many", "what is", "show me", "list") or asking to PERFORM AN ACTION (like "deploy", "configure", "install", "restart")?

Answer with just "INFORMATION" or "ACTION"."""

                        type_response = await self.llm_engine.chat(
                            message=query_type_prompt,
                            system_prompt="You are a query type classifier. Classify queries as INFORMATION or ACTION requests."
                        )
                        
                        if type_response and 'response' in type_response:
                            response_content = type_response['response'].upper()
                            if 'INFORMATION' in response_content:
                                context['query_type'] = 'informational'
                                context['instruction'] = 'This is an informational query. Provide a direct answer using the available asset information. Do not require human oversight for simple information requests.'
                                logger.info("🧠 LLM classified query as informational")
                            else:
                                logger.info("🧠 LLM classified query as action-based")
                    except Exception as e:
                        logger.error(f"Error in LLM query type analysis: {str(e)}")
                        # Default to informational for asset queries
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
            confidence = result.overall_confidence
            intent = result.intent_analysis.intent_type if hasattr(result.intent_analysis, 'intent_type') else "multi_brain_analysis"
            
            # RESTORE ORIGINAL INTENT: SYNTHESIZE ALL INTELLIGENCE
            # Instead of throwing away multi-brain analysis, COMBINE it with asset intelligence
            
            # Generate intelligent asset analysis if we have asset data
            asset_analysis = None
            if asset_info and context.get('query_type') == 'informational':
                asset_analysis = await self._generate_intelligent_asset_answer(query, formatted_assets)
                if asset_analysis:
                    logger.info("🎯 Generated intelligent asset analysis for synthesis")
                    print(f"DEBUG: Generated asset analysis: {asset_analysis}")
            
            # FINAL LLM SYNTHESIS: Combine ALL brain intelligence
            logger.info("🧠 Performing final synthesis of ALL brain intelligence")
            print("DEBUG: Synthesizing multi-brain analysis + asset intelligence + SME consultations")
            
            try:
                response_text = await self._synthesize_final_response(
                    query=query,
                    multi_brain_result=result,
                    asset_analysis=asset_analysis
                )
                logger.info("✅ Synthesis completed successfully")
            except Exception as synthesis_error:
                logger.error(f"Error in final synthesis: {synthesis_error}")
                print(f"DEBUG: Synthesis failed with error: {synthesis_error}")
                # Use proper fallback with asset analysis data
                response_text = self._create_fallback_response(asset_analysis, [])
            
            # Update confidence based on synthesis quality
            has_sme_consultations = hasattr(result, 'sme_consultations') and result.sme_consultations
            if asset_analysis and has_sme_consultations:
                confidence = min(0.95, confidence + 0.1)  # Boost confidence when we have multiple intelligence sources
            elif asset_analysis or has_sme_consultations:
                confidence = min(0.90, confidence + 0.05)  # Slight boost for additional intelligence
            
            logger.info(f"✅ Final synthesis completed with confidence: {confidence}")
            print(f"DEBUG: Final synthesized response: {response_text[:200]}...")
            
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

    async def process_request(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Union[IntentOnlyResult, MultiBrainProcessingResult]:
        """
        Process user request through INTENT ANALYSIS ONLY
        
        DISABLED: All other brains (technical, SME) for focused intent analysis testing
        
        Args:
            user_message: User's request message
            context: Optional additional context
            
        Returns:
            MultiBrainProcessingResult: Intent analysis result only
        """
        start_time = datetime.now()
        request_id = f"mbr_{start_time.strftime('%Y%m%d_%H%M%S')}_{len(self.request_history)}"
        
        try:
            logger.info(f"🎯 INTENT-ONLY Processing: {request_id}")
            
            # Ensure async components are initialized
            if not (self._communication_initialized and self._learning_initialized):
                logger.warning("Multi-brain components not fully initialized, initializing now...")
                await self.initialize()
            
            # ONLY Step 1: Intent Brain Analysis
            logger.info("🎯 INTENT ANALYSIS ONLY - All other brains DISABLED")
            intent_analysis = await self.intent_brain.analyze_intent(user_message, context or {})
            logger.info(f"🎯 Intent analysis completed with confidence: {intent_analysis.overall_confidence}")
            
            # DISABLED: All other processing steps
            logger.info("🚫 DISABLED: Technical Brain, SME Brains, Confidence Aggregation, Strategy, Recommendations")
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create intent-only result (no technical plan, no SME consultations)
            result = IntentOnlyResult(
                request_id=request_id,
                user_message=user_message,
                timestamp=start_time,
                intent_analysis=intent_analysis,
                processing_time=processing_time,
                brains_consulted=["intent_brain_only"]
            )
            
            # Update metrics
            await self._update_metrics(result)
            
            # Store in history
            self.request_history.append(result)
            
            logger.info(f"🎯 Intent-only processing completed: {request_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi-brain processing: {str(e)}")
            
            # Create error result
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create minimal result for error case
            from brains.intent_brain.four_w_analyzer import FourWAnalysis, WhatAnalysis, WhereWhatAnalysis, WhenAnalysis, HowAnalysis, ActionType, ScopeLevel, UrgencyLevel, TimelineType, MethodType
            # Create minimal 4W analysis for error case
            error_four_w = FourWAnalysis(
                what_analysis=WhatAnalysis(
                    action_type=ActionType.INFORMATION,
                    specific_outcome="Error processing request",
                    root_need="System error resolution",
                    surface_request=user_message,
                    confidence=0.0,
                    reasoning="Error in processing"
                ),
                where_what_analysis=WhereWhatAnalysis(
                    target_systems=[],
                    scope_level=ScopeLevel.SINGLE_SYSTEM,
                    affected_components=[],
                    dependencies=[],
                    confidence=0.0,
                    reasoning="Error in processing"
                ),
                when_analysis=WhenAnalysis(
                    urgency=UrgencyLevel.MEDIUM,
                    timeline_type=TimelineType.FLEXIBLE,
                    specific_timeline=None,
                    scheduling_constraints=[],
                    business_hours_required=False,
                    confidence=0.0,
                    reasoning="Error in processing"
                ),
                how_analysis=HowAnalysis(
                    method_preference=MethodType.MANUAL,
                    execution_constraints=[],
                    approval_required=True,
                    rollback_needed=False,
                    testing_required=False,
                    confidence=0.0,
                    reasoning="Error in processing"
                ),
                overall_confidence=0.0,
                missing_information=["Error occurred during analysis"],
                clarifying_questions=["Please try your request again"],
                resource_complexity="LOW",
                estimated_effort="Unknown",
                required_capabilities=[],
                risk_level="HIGH",
                risk_factors=["Processing error"],
                analysis_timestamp=start_time,
                processing_time=processing_time
            )
            
            error_result = MultiBrainProcessingResult(
                request_id=request_id,
                user_message=user_message,
                timestamp=start_time,
                intent_analysis=IntentAnalysisResult(
                    intent_id=request_id,
                    user_message=user_message,
                    timestamp=start_time,
                    four_w_analysis=error_four_w,
                    overall_confidence=0.0,
                    intent_summary="Error in processing",
                    recommended_approach="Manual review required",
                    technical_requirements=[],
                    resource_requirements=[],
                    risk_level="HIGH",
                    risk_factors=["Processing error"],
                    processing_time=processing_time,
                    brain_version="2.0.0"
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
                # Handle different consultation formats safely
                if isinstance(consultation, dict):
                    if "error" not in consultation:
                        # Extract confidence from SME recommendations
                        recommendations = consultation.get("recommendations", [])
                        if recommendations:
                            for rec in recommendations:
                                if isinstance(rec, dict):
                                    avg_sme_confidence = rec.get("confidence", 0.5)
                                    sme_confidences.append(avg_sme_confidence)
                                else:
                                    # If recommendation is not a dict, use default confidence
                                    sme_confidences.append(0.5)
                elif isinstance(consultation, str):
                    # If consultation is a string, use default confidence
                    sme_confidences.append(0.5)
                else:
                    # For any other format, use default confidence
                    sme_confidences.append(0.5)
            
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
    
    def _create_fallback_response(self, asset_analysis: Optional[Dict[str, Any]], synthesis_components: List[Dict[str, Any]]) -> str:
        """Create a fallback response using asset analysis data instead of generic recommendations"""
        try:
            logger.info("🔄 Creating fallback response from asset analysis data")
            
            # First, try to use asset analysis data if available
            if asset_analysis:
                logger.info("📊 Using asset analysis data for fallback response")
                
                # If we have an LLM response from asset analysis, use it directly
                if isinstance(asset_analysis, dict) and 'llm_response' in asset_analysis:
                    llm_response = asset_analysis['llm_response'].strip()
                    if llm_response and len(llm_response) > 10:
                        logger.info("🎯 Using LLM asset analysis response directly")
                        return llm_response
                
                # For asset queries, provide direct information
                if 'assets' in asset_analysis:
                    assets = asset_analysis['assets']
                    if isinstance(assets, list) and assets:
                        # Count-based queries
                        asset_count = len(assets)
                        if asset_count == 1:
                            asset = assets[0]
                            asset_name = asset.get('name', 'Unknown')
                            asset_ip = asset.get('ip_address', 'Unknown IP')
                            fallback_response = f"We have 1 asset: {asset_name} (IP: {asset_ip})."
                            logger.info(f"🔍 DEBUG: Fallback response created: '{fallback_response}'")
                            logger.info(f"🔍 DEBUG: Fallback ends with period: {fallback_response.endswith('.')}")
                            logger.info(f"🔍 DEBUG: Fallback last 5 chars: '{fallback_response[-5:]}'")
                            return fallback_response
                        else:
                            return f"We have {asset_count} assets matching your query."
                    elif isinstance(assets, dict):
                        # Single asset response
                        asset_name = assets.get('name', 'Unknown')
                        asset_ip = assets.get('ip_address', 'Unknown IP')
                        return f"Found asset: {asset_name} (IP: {asset_ip})."
                
                # For summary data
                if 'summary' in asset_analysis:
                    summary = asset_analysis['summary']
                    if isinstance(summary, str):
                        return summary
                    elif isinstance(summary, dict):
                        # Extract meaningful information from summary
                        if 'total_count' in summary:
                            return f"Found {summary['total_count']} items matching your query."
            
            # Second, try to use synthesis components with actual data
            for component in synthesis_components:
                if component.get('type') == 'asset_analysis' and component.get('content'):
                    content = component['content']
                    if isinstance(content, str) and len(content.strip()) > 10:
                        logger.info("📊 Using asset analysis component for fallback")
                        return content.strip()
                elif component.get('type') == 'expert_consultation' and component.get('content'):
                    content = component['content']
                    if isinstance(content, str) and len(content.strip()) > 10:
                        logger.info("👨‍💼 Using expert consultation for fallback")
                        return content.strip()
            
            # Last resort: generic message
            logger.warning("⚠️ No suitable data found for fallback response")
            return "Analysis completed. Please check the logs for detailed information."
            
        except Exception as e:
            logger.error(f"Error creating fallback response: {str(e)}")
            return "Analysis completed with errors. Please check the logs for details."
    
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
            "response": "Legacy method - use process_query for proper responses",
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
                "error_message": "Multi-brain job creation requires LLM intelligence - NO FALLBACKS AVAILABLE"
            }