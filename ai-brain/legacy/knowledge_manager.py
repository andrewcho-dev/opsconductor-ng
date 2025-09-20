"""
Knowledge Manager for AI Orchestrator
Manages OpsConductor-specific knowledge and real-time system data
"""
import structlog
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = structlog.get_logger()

class KnowledgeManager:
    """Manages OpsConductor knowledge base and real-time system data"""
    
    def __init__(self, api_gateway_url: str, vector_service_url: str):
        self.api_gateway_url = api_gateway_url
        self.vector_service_url = vector_service_url
        
        # OpsConductor system knowledge
        self.system_knowledge = {
            "architecture": {
                "description": "OpsConductor is an IT operations automation platform",
                "components": [
                    "API Gateway - Central routing and authentication",
                    "Asset Service - Manages targets, credentials, and infrastructure",
                    "Automation Service - Executes jobs and workflows",
                    "Communication Service - Handles notifications and alerts",
                    "Identity Service - User management and authentication",
                    "AI Services - NLP, Vector DB, LLM for intelligent automation"
                ]
            },
            "terminology": {
                "targets": "Managed systems/servers in the infrastructure (Windows/Linux machines)",
                "jobs": "Automation tasks that can be executed on targets",
                "runs": "Execution instances of jobs with results and logs",
                "workflows": "Multi-step automation processes",
                "credentials": "Authentication information for accessing targets",
                "services": "Connection methods (WinRM, SSH, SNMP, etc.) for targets",
                "users": "System users with different roles and permissions",
                "tags": "Labels used to categorize and organize targets (e.g., 'production', 'development', 'web-server')"
            },
            "capabilities": [
                "Remote command execution via WinRM/SSH",
                "System monitoring and health checks",
                "Automated task scheduling and execution",
                "Multi-target parallel operations",
                "Real-time status monitoring",
                "Credential management and security",
                "Workflow orchestration",
                "AI-powered natural language automation"
            ]
        }
    
    async def initialize_knowledge_base(self):
        """Initialize the knowledge base with OpsConductor system knowledge"""
        try:
            logger.info("Initializing OpsConductor knowledge base...")
            
            # Store system architecture knowledge
            await self._store_knowledge("system_architecture", 
                f"OpsConductor Architecture: {json.dumps(self.system_knowledge['architecture'], indent=2)}")
            
            # Store terminology
            for term, definition in self.system_knowledge["terminology"].items():
                await self._store_knowledge("terminology", 
                    f"OpsConductor Term - {term}: {definition}")
            
            # Store capabilities
            capabilities_text = "OpsConductor Capabilities:\n" + "\n".join([f"- {cap}" for cap in self.system_knowledge["capabilities"]])
            await self._store_knowledge("capabilities", capabilities_text)
            
            # Get and store current system state
            await self._update_system_state()
            
            logger.info("Knowledge base initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize knowledge base", error=str(e))
            return False
    
    async def get_system_context(self, query: str) -> str:
        """Get relevant system context for a query"""
        try:
            # Get real-time system data
            system_data = await self._get_current_system_data()
            
            # Search for relevant knowledge
            relevant_knowledge = await self._search_knowledge(query)
            
            # Build context
            context_parts = []
            
            # Add current system state
            if system_data:
                context_parts.append("Current OpsConductor System State:")
                context_parts.append(f"- Targets: {system_data.get('targets', 0)} managed systems")
                context_parts.append(f"- Jobs: {system_data.get('jobs', 0)} automation jobs")
                context_parts.append(f"- Runs: {system_data.get('runs', 0)} execution runs")
                context_parts.append(f"- Users: {system_data.get('users', 0)} system users")
                
                if system_data.get('target_details'):
                    context_parts.append("\nTarget Details:")
                    for target in system_data['target_details'][:3]:  # Show first 3 targets
                        context_parts.append(f"- {target['name']} ({target['os_type']}) - {target.get('connection_status', 'unknown')} status")
            
            # Add relevant knowledge
            if relevant_knowledge:
                context_parts.append("\nRelevant OpsConductor Knowledge:")
                context_parts.extend(relevant_knowledge[:3])  # Top 3 relevant pieces
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error("Failed to get system context", error=str(e))
            return "OpsConductor system context unavailable"
    
    async def _get_current_system_data(self) -> Dict[str, Any]:
        """Get current system data from API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get counts
                targets_response = await client.get(f"{self.api_gateway_url}/api/v1/targets?limit=1")
                jobs_response = await client.get(f"{self.api_gateway_url}/api/v1/jobs?limit=1")
                runs_response = await client.get(f"{self.api_gateway_url}/api/v1/runs?limit=1")
                users_response = await client.get(f"{self.api_gateway_url}/api/v1/users?limit=1")
                
                # Get detailed target info
                targets_detail_response = await client.get(f"{self.api_gateway_url}/api/v1/targets?limit=10")
                
                targets_data = targets_response.json()
                jobs_data = jobs_response.json()
                runs_data = runs_response.json()
                users_data = users_response.json()
                targets_detail_data = targets_detail_response.json()
                
                return {
                    "targets": targets_data.get("total", 0),
                    "jobs": jobs_data.get("total", 0),
                    "runs": runs_data.get("total", 0),
                    "users": users_data.get("total", 0),
                    "target_details": targets_detail_data.get("targets", []),
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to get current system data", error=str(e))
            return {}
    
    async def _update_system_state(self):
        """Update the knowledge base with current system state"""
        try:
            system_data = await self._get_current_system_data()
            if system_data:
                # Store current system state
                state_text = f"""OpsConductor Current System State (as of {system_data.get('last_updated', 'unknown')}):
- Total Targets: {system_data.get('targets', 0)}
- Total Jobs: {system_data.get('jobs', 0)}
- Total Runs: {system_data.get('runs', 0)}
- Total Users: {system_data.get('users', 0)}

Target Details:
"""
                for target in system_data.get('target_details', []):
                    services = target.get('services', [])
                    service_info = f"{len(services)} services" if services else "no services"
                    connection_status = "connected" if services and any(s.get('connection_status') == 'connected' for s in services) else "disconnected"
                    
                    state_text += f"- {target['name']} ({target['ip_address']}) - {target['os_type']} - {connection_status} - {service_info}\n"
                
                await self._store_knowledge("system_state", state_text)
                
        except Exception as e:
            logger.error("Failed to update system state", error=str(e))
    
    async def _store_knowledge(self, category: str, content: str):
        """Store knowledge in vector database"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{self.vector_service_url}/vector/store",
                    json={
                        "content": content,
                        "category": f"opsconductor_{category}",
                        "metadata": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "knowledge_manager"
                        }
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to store knowledge for {category}", error=str(e))
    
    async def _search_knowledge(self, query: str, limit: int = 5) -> List[str]:
        """Search for relevant knowledge"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vector_service_url}/vector/search",
                    json={
                        "query": query,
                        "limit": limit,
                        "filter": {"category": {"$regex": "opsconductor_.*"}}
                    }
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    return [result.get("content", "") for result in results if result.get("content")]
                
        except Exception as e:
            logger.warning("Failed to search knowledge", error=str(e))
        
        return []
    
    async def _handle_automated_introspection_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries using automated introspection - discovers what data to return based on query"""
        try:
            query_lower = query.lower()
            
            # Get all system data
            system_data = await self._get_current_system_data()
            target_details = system_data.get('target_details', [])
            
            # Analyze query for what the user is asking about using flexible pattern matching
            if any(term in query_lower for term in ["tag", "tags", "label", "labels", "category", "categories", "tagged", "labelled", "classification", "organize", "group"]):
                # User is asking about tags - automatically discover and return tag information
                all_tags = {}
                tagged_targets = []
                
                for target in target_details:
                    target_tags = target.get("tags", [])
                    if target_tags:
                        tagged_targets.append(target)
                        for tag in target_tags:
                            if tag not in all_tags:
                                all_tags[tag] = []
                            all_tags[tag].append(target["name"])
                
                if not all_tags:
                    return {
                        "success": True,
                        "message": "🏷️ **No tags found** - None of the targets have tags assigned yet."
                    }
                
                response = f"🏷️ **Available Tags ({len(all_tags)} total):**\n\n"
                sorted_tags = sorted(all_tags.items(), key=lambda x: len(x[1]), reverse=True)
                
                for tag, target_names in sorted_tags:
                    response += f"• **{tag}** - used by {len(target_names)} target(s)\n"
                    if len(target_names) <= 3:
                        response += f"  └─ {', '.join(target_names)}\n"
                    else:
                        response += f"  └─ {', '.join(target_names[:3])} and {len(target_names) - 3} more\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {
                        "tags": all_tags,
                        "total_tags": len(all_tags),
                        "tagged_targets": len(tagged_targets)
                    }
                }
            
            # Try to understand other types of queries with enhanced pattern matching
            elif (any(term in query_lower for term in ["target", "targets", "server", "servers", "machine", "machines", "host", "hosts", "system", "systems", "computer", "computers", "node", "nodes", "device", "devices"]) or
                  # Also catch queries that mention connection status + environment/OS
                  (any(conn in query_lower for conn in ["connected", "disconnected", "online", "offline"]) and 
                   any(env in query_lower for env in ["windows", "linux", "production", "development", "staging"])) or
                  # Catch queries about specific services/roles
                  any(role in query_lower for role in ["database", "web", "api", "frontend", "backend"])):
                # User is asking about targets/servers with potential filtering
                if not target_details:
                    return {
                        "success": True,
                        "message": "No targets are currently configured in OpsConductor."
                    }
                
                # Check for filtering criteria
                filtered_targets = target_details
                filter_applied = ""
                
                # Filter by connection status
                if any(term in query_lower for term in ["connected", "online", "up", "active"]):
                    filtered_targets = [t for t in target_details 
                                     if any(s.get('connection_status') == 'connected' 
                                           for s in t.get('services', []))]
                    filter_applied = " (connected only)"
                elif any(term in query_lower for term in ["disconnected", "offline", "down", "inactive"]):
                    filtered_targets = [t for t in target_details 
                                     if not any(s.get('connection_status') == 'connected' 
                                               for s in t.get('services', []))]
                    filter_applied = " (disconnected only)"
                
                # Filter by OS type
                elif any(term in query_lower for term in ["windows", "win"]):
                    filtered_targets = [t for t in target_details if "windows" in t.get('os_type', '').lower()]
                    filter_applied = " (Windows only)"
                elif any(term in query_lower for term in ["linux", "unix"]):
                    filtered_targets = [t for t in target_details if "linux" in t.get('os_type', '').lower()]
                    filter_applied = " (Linux only)"
                
                # Filter by environment tags
                elif any(term in query_lower for term in ["production", "prod"]):
                    filtered_targets = [t for t in target_details if "production" in t.get('tags', [])]
                    filter_applied = " (production only)"
                elif any(term in query_lower for term in ["development", "dev"]):
                    filtered_targets = [t for t in target_details if "development" in t.get('tags', [])]
                    filter_applied = " (development only)"
                elif any(term in query_lower for term in ["staging", "stage"]):
                    filtered_targets = [t for t in target_details if "staging" in t.get('tags', [])]
                    filter_applied = " (staging only)"
                
                if not filtered_targets:
                    return {
                        "success": True,
                        "message": f"No targets found matching your criteria{filter_applied}."
                    }
                
                response = f"OpsConductor Targets ({len(filtered_targets)} total{filter_applied}):\n\n"
                for target in filtered_targets:
                    services = target.get('services', [])
                    status = "Connected" if any(s.get('connection_status') == 'connected' for s in services) else "Disconnected"
                    tags = target.get('tags', [])
                    
                    response += f"• **{target['name']}** ({target['ip_address']})\n"
                    response += f"  └─ OS: {target['os_type']}\n"
                    response += f"  └─ Status: {status}\n"
                    response += f"  └─ Services: {len(services)}\n"
                    if tags:
                        response += f"  └─ Tags: {', '.join(tags)}\n"
                    response += "\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {
                        "targets": filtered_targets,
                        "total_targets": len(filtered_targets),
                        "filter_applied": filter_applied
                    }
                }
            
            elif any(term in query_lower for term in ["count", "how many", "number", "total"]):
                # User is asking for counts
                connected_count = sum(1 for t in target_details 
                                    if any(s.get('connection_status') == 'connected' 
                                          for s in t.get('services', [])))
                
                response = f"📊 **OpsConductor System Summary:**\n\n"
                response += f"• **{len(target_details)}** total targets\n"
                response += f"• **{connected_count}** connected targets\n"
                response += f"• **{len(target_details) - connected_count}** disconnected targets\n"
                
                # Add tag summary
                all_tags = set()
                for target in target_details:
                    all_tags.update(target.get('tags', []))
                
                if all_tags:
                    response += f"• **{len(all_tags)}** unique tags in use\n"
                
                return {
                    "success": True,
                    "message": response,
                    "data": {
                        "total_targets": len(target_details),
                        "connected_targets": connected_count,
                        "total_tags": len(all_tags)
                    }
                }
            
            # Try to understand more conversational patterns
            elif any(phrase in query_lower for phrase in [
                "what do we have", "what are our", "what's in our", "tell me about our",
                "show me our", "give me info", "i want to see", "can you show",
                "help me understand", "what's available", "what exists"
            ]):
                # General inquiry - provide overview
                connected_count = sum(1 for t in target_details 
                                    if any(s.get('connection_status') == 'connected' 
                                          for s in t.get('services', [])))
                
                all_tags = set()
                for target in target_details:
                    all_tags.update(target.get('tags', []))
                
                response = f"📋 **OpsConductor Overview:**\n\n"
                response += f"🖥️ **Infrastructure:**\n"
                response += f"• {len(target_details)} total targets/servers\n"
                response += f"• {connected_count} currently connected\n"
                response += f"• {len(target_details) - connected_count} disconnected\n\n"
                
                if all_tags:
                    response += f"🏷️ **Organization:**\n"
                    response += f"• {len(all_tags)} different tags in use\n"
                    response += f"• Tags include: {', '.join(sorted(list(all_tags))[:5])}"
                    if len(all_tags) > 5:
                        response += f" and {len(all_tags) - 5} more"
                    response += "\n\n"
                
                response += f"💡 **Ask me about:**\n"
                response += f"• 'show targets' - detailed target list\n"
                response += f"• 'what tags do we have' - tag breakdown\n"
                response += f"• 'how many connected' - connection status\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {
                        "total_targets": len(target_details),
                        "connected_targets": connected_count,
                        "total_tags": len(all_tags)
                    }
                }
            
            # If we can't automatically determine what they want, provide helpful guidance with examples
            return {
                "success": True,
                "message": "🤖 **I can help you with OpsConductor information!**\n\n" +
                          "📊 **System Information:**\n" +
                          "• 'show machines' - list all targets\n" +
                          "• 'connected servers' - filter by status\n" +
                          "• 'production systems' - filter by environment\n" +
                          "• 'Windows connected servers' - multi-criteria\n\n" +
                          "🏷️ **Organization:**\n" +
                          "• 'what tags do we have' - show all labels\n" +
                          "• 'database servers' - targets by role\n\n" +
                          "📈 **Status & Metrics:**\n" +
                          "• 'how many targets' - counts and stats\n" +
                          "• 'system overview' - infrastructure summary\n\n" +
                          "💡 **Try asking naturally:** 'Which production systems are offline?' or 'Show me all our web servers'"
            }
            
        except Exception as e:
            logger.error("Failed to handle automated introspection query", error=str(e))
            return {
                "success": False,
                "message": f"Error processing query: {str(e)}"
            }
    
    async def _analyze_query_intent(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently analyze query to determine user intent"""
        try:
            query_lower = query.lower()
            entities = parsed_data.get("entities", [])
            
            # Extract key terms and patterns
            intent_analysis = {
                "primary_intent": "unknown",
                "entities": [],
                "confidence": 0.0,
                "query_type": "information"
            }
            
            # Tag-related queries (highest priority for tag questions)
            tag_indicators = [
                "tag", "tags", "label", "labels", "category", "categories",
                "what tags", "show tags", "list tags", "available tags", "all tags",
                "tagged", "labelled", "categorized"
            ]
            
            if any(indicator in query_lower for indicator in tag_indicators):
                intent_analysis["primary_intent"] = "tag_info"
                intent_analysis["confidence"] = 0.9
                return intent_analysis
            
            # Target/Server queries with enhanced synonyms and contextual terms
            target_indicators = [
                "target", "targets", "server", "servers", "machine", "machines",
                "host", "hosts", "system", "systems", "computer", "computers",
                "windows", "linux", "production", "development", "staging",
                "node", "nodes", "device", "devices", "endpoint", "endpoints",
                "vm", "vms", "virtual", "instance", "instances", "box", "boxes",
                "workstation", "workstations", "pc", "pcs", "desktop", "desktops",
                "infrastructure", "environment", "platform", "deployment",
                # Connection status terms that imply targets
                "connected", "disconnected", "online", "offline", "up", "down",
                # Service/role terms that imply targets
                "database", "web", "api", "frontend", "backend", "service"
            ]
            
            if any(indicator in query_lower for indicator in target_indicators):
                intent_analysis["primary_intent"] = "target_info"
                intent_analysis["confidence"] = 0.8
                
                # Check if it's specifically about tags on targets
                if any(tag_ind in query_lower for tag_ind in tag_indicators):
                    intent_analysis["primary_intent"] = "tag_info"
                    intent_analysis["confidence"] = 0.9
                
                return intent_analysis
            
            # Job/Automation queries
            job_indicators = [
                "job", "jobs", "task", "tasks", "automation", "workflow", "workflows",
                "script", "scripts", "playbook", "playbooks"
            ]
            
            if any(indicator in query_lower for indicator in job_indicators):
                intent_analysis["primary_intent"] = "job_info"
                intent_analysis["confidence"] = 0.8
                return intent_analysis
            
            # Run/Execution queries
            run_indicators = [
                "run", "runs", "execution", "executions", "result", "results",
                "log", "logs", "history", "recent", "last", "latest"
            ]
            
            if any(indicator in query_lower for indicator in run_indicators):
                intent_analysis["primary_intent"] = "run_info"
                intent_analysis["confidence"] = 0.8
                return intent_analysis
            
            # System status queries
            status_indicators = [
                "status", "health", "overview", "summary", "dashboard",
                "how many", "count", "total", "statistics", "stats"
            ]
            
            if any(indicator in query_lower for indicator in status_indicators):
                intent_analysis["primary_intent"] = "system_status"
                intent_analysis["confidence"] = 0.7
                return intent_analysis
            
            # Use NLP entities to help determine intent
            entity_texts = [e.get("text", "").lower() for e in entities]
            if any("target" in text or "server" in text for text in entity_texts):
                intent_analysis["primary_intent"] = "target_info"
                intent_analysis["confidence"] = 0.6
            
            return intent_analysis
            
        except Exception as e:
            logger.error("Failed to analyze query intent", error=str(e))
            return {
                "primary_intent": "unknown",
                "entities": [],
                "confidence": 0.0,
                "query_type": "information"
            }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better understanding"""
        # Convert to lowercase for processing
        normalized = query.lower().strip()
        
        # Handle common variations and synonyms
        replacements = {
            # Question words and conversational patterns
            "which": "show",
            "what": "show", 
            "where": "show",
            "find": "show",
            "get": "show",
            "list": "show",
            "display": "show",
            "how do i see": "show",
            "how can i see": "show",
            "how to see": "show",
            "how do i find": "show",
            "how can i find": "show",
            "how to find": "show",
            "tell me about": "show",
            "i need to see": "show",
            "i want to see": "show",
            "i need to check": "show",
            "can you show me": "show",
            
            # Plural/singular normalization
            "machines": "servers",
            "computers": "servers", 
            "hosts": "servers",
            "systems": "servers",
            "nodes": "servers",
            "devices": "servers",
            
            # Status synonyms
            "online": "connected",
            "up": "connected",
            "active": "connected",
            "offline": "disconnected", 
            "down": "disconnected",
            "inactive": "disconnected",
            
            # Environment synonyms
            "prod": "production",
            "dev": "development",
            "stage": "staging",
            
            # Common phrases
            "are currently": "that are",
            "that are currently": "that are",
            "right now": "",
            "at the moment": "",
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized.strip()
    
    async def _handle_contextual_fallback(self, query: str, parsed_data: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """Enhanced fallback handler with contextual understanding"""
        query_lower = query.lower()
        
        # Try to extract meaningful keywords and suggest relevant actions
        keywords = {
            "status": ["connected", "disconnected", "online", "offline", "up", "down"],
            "environment": ["production", "development", "staging"],
            "os": ["windows", "linux"],
            "role": ["database", "web", "api", "frontend", "backend"],
            "metrics": ["count", "how many", "total", "number"]
        }
        
        detected_categories = []
        for category, terms in keywords.items():
            if any(term in query_lower for term in terms):
                detected_categories.append(category)
        
        if detected_categories:
            # Provide contextual suggestions based on detected keywords
            suggestions = []
            if "status" in detected_categories:
                suggestions.append("'show connected servers' or 'show disconnected servers'")
            if "environment" in detected_categories:
                suggestions.append("'show production servers' or 'show development servers'")
            if "role" in detected_categories:
                suggestions.append("'show database servers' or 'show web servers'")
            if "metrics" in detected_categories:
                suggestions.append("'how many targets' or 'system overview'")
            
            message = f"🤔 **I understand you're asking about {', '.join(detected_categories)}.**\n\n"
            message += f"💡 **Try these specific queries:**\n"
            for suggestion in suggestions[:3]:  # Limit to 3 suggestions
                message += f"• {suggestion}\n"
            message += f"\n📋 **Or ask:** 'what can you help me with' for more options"
            
            return {
                "success": True,
                "message": message
            }
        
        # Default to automated introspection for general queries
        return await self._handle_automated_introspection_query(query, parsed_data)
    
    async def handle_system_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system-specific queries with enhanced natural language understanding"""
        try:
            # Normalize and preprocess the query for better understanding
            normalized_query = self._normalize_query(query)
            
            # Use intelligent query analysis to determine what the user wants
            query_intent = await self._analyze_query_intent(normalized_query, parsed_data)
            
            logger.info("Query intent analysis", 
                       original_query=query,
                       normalized_query=normalized_query,
                       intent=query_intent.get("primary_intent"),
                       entities=query_intent.get("entities"),
                       confidence=query_intent.get("confidence"))
            
            # Route based on intelligent analysis
            primary_intent = query_intent.get("primary_intent")
            
            if primary_intent == "target_info":
                return await self._handle_target_query(normalized_query, parsed_data)
            elif primary_intent == "tag_info":
                return await self._handle_target_query("list target tags", parsed_data)
            elif primary_intent == "job_info":
                return await self._handle_job_query(normalized_query, parsed_data)
            elif primary_intent == "run_info":
                return await self._handle_run_query(normalized_query, parsed_data)
            elif primary_intent == "system_status":
                return await self._handle_system_overview_query(normalized_query, parsed_data)
            else:
                # Enhanced fallback with contextual suggestions
                return await self._handle_contextual_fallback(normalized_query, parsed_data, query)
                
        except Exception as e:
            logger.error("Failed to handle system query", error=str(e))
            return {
                "success": False,
                "message": f"Error processing query: {str(e)}"
            }
    
    async def _handle_target_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle target-related queries"""
        try:
            system_data = await self._get_current_system_data()
            targets = system_data.get('targets', 0)
            target_details = system_data.get('target_details', [])
            
            if "how many" in query.lower() or "count" in query.lower():
                # Count query - check if it's asking about specific tags or OS versions
                query_lower = query.lower()
                
                # Check for specific OS version queries
                os_version_queries = {
                    "windows 10": "win10",
                    "win10": "win10", 
                    "windows 11": "win11",
                    "win11": "win11",
                    "production": "production",
                    "development": "development",
                    "staging": "staging"
                }
                
                # Look for specific tag/OS version in query
                matching_tag = None
                for query_term, tag in os_version_queries.items():
                    if query_term in query_lower:
                        matching_tag = tag
                        break
                
                if matching_tag:
                    # Count targets with specific tag
                    matching_targets = [t for t in target_details if matching_tag in t.get('tags', [])]
                    connected_matching = sum(1 for t in matching_targets 
                                           if any(s.get('connection_status') == 'connected' 
                                                 for s in t.get('services', [])))
                    
                    if matching_targets:
                        response = f"🏷️ **{matching_tag.upper()} Targets ({len(matching_targets)} found):**\n\n"
                        response += f"• **{len(matching_targets)}** total {matching_tag} targets\n"
                        response += f"• **{connected_matching}** are connected\n"
                        response += f"• **{len(matching_targets) - connected_matching}** are disconnected\n\n"
                        
                        response += "**Target Details:**\n"
                        for target in matching_targets:
                            services = target.get('services', [])
                            status = "Connected" if any(s.get('connection_status') == 'connected' for s in services) else "Disconnected"
                            other_tags = [t for t in target.get('tags', []) if t != matching_tag]
                            
                            response += f"• **{target['name']}** ({target['ip_address']}) - {status}\n"
                            if other_tags:
                                response += f"  └─ Also tagged: {', '.join(other_tags)}\n"
                        
                        return {
                            "success": True,
                            "message": response.strip(),
                            "data": {
                                "tag": matching_tag,
                                "total_targets": len(matching_targets),
                                "connected_targets": connected_matching,
                                "targets": matching_targets
                            }
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"❌ **No {matching_tag} targets found**\n\nNo targets are currently tagged with '{matching_tag}'.",
                            "data": {
                                "tag": matching_tag,
                                "total_targets": 0,
                                "connected_targets": 0,
                                "targets": []
                            }
                        }
                
                # General count query
                connected_count = sum(1 for t in target_details 
                                    if any(s.get('connection_status') == 'connected' 
                                          for s in t.get('services', [])))
                
                response = f"OpsConductor currently manages {targets} targets:\n"
                response += f"- {connected_count} targets are connected\n"
                response += f"- {targets - connected_count} targets are disconnected\n\n"
                
                if target_details:
                    response += "Target breakdown:\n"
                    os_counts = {}
                    for target in target_details:
                        os_type = target.get('os_type', 'unknown')
                        os_counts[os_type] = os_counts.get(os_type, 0) + 1
                    
                    for os_type, count in os_counts.items():
                        response += f"- {count} {os_type} systems\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {
                        "total_targets": targets,
                        "connected_targets": connected_count,
                        "target_details": target_details
                    }
                }
            
            elif "list" in query.lower() or "show" in query.lower():
                # List query
                if not target_details:
                    return {
                        "success": True,
                        "message": "No targets are currently configured in OpsConductor."
                    }
                
                # Check if this is specifically about tags or specific OS/environment
                query_lower = query.lower()
                
                # Check for specific tag/environment queries first
                os_version_queries = {
                    "windows 10": "win10",
                    "win10": "win10", 
                    "windows 11": "win11",
                    "win11": "win11",
                    "production": "production",
                    "development": "development",
                    "staging": "staging",
                    "database": "database",
                    "web-server": "web-server",
                    "api-server": "api-server"
                }
                
                # Look for specific tag/OS version in query
                matching_tag = None
                for query_term, tag in os_version_queries.items():
                    if query_term in query_lower:
                        matching_tag = tag
                        break
                
                if matching_tag:
                    # Show targets with specific tag
                    matching_targets = [t for t in target_details if matching_tag in t.get('tags', [])]
                    
                    if matching_targets:
                        response = f"🏷️ **{matching_tag.upper()} Targets ({len(matching_targets)} found):**\n\n"
                        
                        for target in matching_targets:
                            services = target.get('services', [])
                            status = "Connected" if any(s.get('connection_status') == 'connected' for s in services) else "Disconnected"
                            other_tags = [t for t in target.get('tags', []) if t != matching_tag]
                            
                            response += f"• **{target['name']}** ({target['ip_address']})\n"
                            response += f"  └─ OS: {target['os_type']}\n"
                            response += f"  └─ Status: {status}\n"
                            response += f"  └─ Services: {len(services)}\n"
                            
                            if other_tags:
                                response += f"  └─ Also tagged: {', '.join(other_tags)}\n"
                            
                            response += "\n"
                        
                        return {
                            "success": True,
                            "message": response.strip(),
                            "data": {
                                "tag": matching_tag,
                                "targets": matching_targets,
                                "total_found": len(matching_targets)
                            }
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"❌ **No {matching_tag} targets found**\n\nNo targets are currently tagged with '{matching_tag}'."
                        }
                
                elif any(term in query_lower for term in ["tag", "tagged", "label"]):
                    # Tag-specific listing
                    all_tags = {}
                    tagged_targets = []
                    
                    for target in target_details:
                        target_tags = target.get("tags", [])
                        if target_tags:
                            tagged_targets.append(target)
                            for tag in target_tags:
                                if tag not in all_tags:
                                    all_tags[tag] = []
                                all_tags[tag].append(target["name"])
                    
                    if not all_tags:
                        return {
                            "success": True,
                            "message": "🏷️ **No tags found** - None of the targets have tags assigned yet."
                        }
                    
                    response = f"🏷️ **Available Tags ({len(all_tags)} total):**\n\n"
                    sorted_tags = sorted(all_tags.items(), key=lambda x: len(x[1]), reverse=True)
                    
                    for tag, target_names in sorted_tags:
                        response += f"• **{tag}** - used by {len(target_names)} target(s)\n"
                        if len(target_names) <= 3:
                            response += f"  └─ {', '.join(target_names)}\n"
                        else:
                            response += f"  └─ {', '.join(target_names[:3])} and {len(target_names) - 3} more\n"
                    
                    return {
                        "success": True,
                        "message": response.strip(),
                        "data": {
                            "tags": all_tags,
                            "total_tags": len(all_tags),
                            "tagged_targets": len(tagged_targets)
                        }
                    }
                
                # Regular target listing with filtering
                query_lower = query.lower()
                filtered_targets = target_details
                filter_applied = ""
                
                # Multi-criteria filtering with natural language understanding
                filters_applied = []
                
                # Connection status filters
                connection_filter = None
                if any(term in query_lower for term in ["disconnected", "offline", "down", "inactive"]):
                    connection_filter = "disconnected"
                    filters_applied.append("disconnected")
                elif any(term in query_lower for term in ["connected", "online", "up", "active"]):
                    connection_filter = "connected"
                    filters_applied.append("connected")
                
                # OS type filters
                os_filter = None
                if any(term in query_lower for term in ["windows", "win"]):
                    os_filter = "windows"
                    filters_applied.append("Windows")
                elif any(term in query_lower for term in ["linux", "unix"]):
                    os_filter = "linux"
                    filters_applied.append("Linux")
                
                # Environment/tag filters
                tag_filters = []
                if any(term in query_lower for term in ["production", "prod"]):
                    tag_filters.append("production")
                    filters_applied.append("production")
                if any(term in query_lower for term in ["development", "dev"]):
                    tag_filters.append("development")
                    filters_applied.append("development")
                if any(term in query_lower for term in ["staging", "stage"]):
                    tag_filters.append("staging")
                    filters_applied.append("staging")
                
                # Additional semantic filters
                if any(term in query_lower for term in ["database", "db", "mysql", "postgres", "sql"]):
                    tag_filters.append("database")
                    filters_applied.append("database")
                if any(term in query_lower for term in ["web", "frontend", "ui"]):
                    tag_filters.append("web-server")
                    tag_filters.append("frontend")
                    filters_applied.append("web/frontend")
                if any(term in query_lower for term in ["api", "backend", "service"]):
                    tag_filters.append("api-server")
                    tag_filters.append("backend")
                    filters_applied.append("API/backend")
                
                # Apply all filters (only if any filters were detected)
                if filters_applied:
                    filtered_targets = []
                    for target in target_details:
                        include_target = True
                        
                        # Apply connection filter
                        if connection_filter:
                            services = target.get('services', [])
                            is_connected = any(s.get('connection_status') == 'connected' for s in services)
                            if connection_filter == "connected" and not is_connected:
                                include_target = False
                            elif connection_filter == "disconnected" and is_connected:
                                include_target = False
                        
                        # Apply OS filter
                        if os_filter and include_target:
                            target_os = target.get('os_type', '').lower()
                            if os_filter not in target_os:
                                include_target = False
                        
                        # Apply tag filters (target must have at least one matching tag)
                        if tag_filters and include_target:
                            target_tags = target.get('tags', [])
                            if not any(tag in target_tags for tag in tag_filters):
                                include_target = False
                        
                        if include_target:
                            filtered_targets.append(target)
                
                # Create filter description
                if filters_applied:
                    filter_applied = f" ({', '.join(filters_applied)} only)"
                else:
                    filter_applied = ""
                
                if not filtered_targets:
                    # Provide helpful suggestions when no results found
                    suggestion_msg = f"❌ **No targets found matching your criteria{filter_applied}.**\n\n"
                    
                    # Suggest alternatives based on what we do have
                    if connection_filter == "connected":
                        disconnected_count = sum(1 for t in target_details 
                                               if not any(s.get('connection_status') == 'connected' 
                                                         for s in t.get('services', [])))
                        if disconnected_count > 0:
                            suggestion_msg += f"💡 **Try instead:** 'show disconnected servers' ({disconnected_count} available)\n"
                    elif connection_filter == "disconnected":
                        connected_count = sum(1 for t in target_details 
                                            if any(s.get('connection_status') == 'connected' 
                                                  for s in t.get('services', [])))
                        if connected_count > 0:
                            suggestion_msg += f"💡 **Try instead:** 'show connected servers' ({connected_count} available)\n"
                    
                    # Suggest available tags
                    if tag_filters:
                        all_tags = set()
                        for target in target_details:
                            all_tags.update(target.get('tags', []))
                        available_tags = [tag for tag in all_tags if tag not in tag_filters]
                        if available_tags:
                            suggestion_msg += f"💡 **Available environments:** {', '.join(sorted(available_tags)[:3])}\n"
                    
                    suggestion_msg += f"\n📋 **Or try:** 'show all targets' to see everything"
                    
                    return {
                        "success": True,
                        "message": suggestion_msg.strip()
                    }
                
                response = f"OpsConductor Targets ({len(filtered_targets)} total{filter_applied}):\n\n"
                for target in filtered_targets:
                    services = target.get('services', [])
                    status = "Connected" if any(s.get('connection_status') == 'connected' for s in services) else "Disconnected"
                    tags = target.get('tags', [])
                    
                    response += f"• **{target['name']}** ({target['ip_address']})\n"
                    response += f"  └─ OS: {target['os_type']}\n"
                    response += f"  └─ Status: {status}\n"
                    response += f"  └─ Services: {len(services)}\n"
                    
                    if tags:
                        response += f"  └─ Tags: {', '.join(tags)}\n"
                    
                    response += "\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {
                        "targets": filtered_targets,
                        "total_targets": len(filtered_targets),
                        "filter_applied": filter_applied
                    }
                }
            
            else:
                return {
                    "success": True,
                    "message": f"OpsConductor manages {targets} targets. You can ask me to 'list targets' for details or 'how many targets are connected' for status information."
                }
                
        except Exception as e:
            logger.error("Failed to handle target query", error=str(e))
            return {
                "success": False,
                "message": f"Error retrieving target information: {str(e)}"
            }
    
    async def _handle_job_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle job-related queries"""
        try:
            system_data = await self._get_current_system_data()
            jobs = system_data.get('jobs', 0)
            
            return {
                "success": True,
                "message": f"OpsConductor currently has {jobs} automation jobs configured. Jobs are automation tasks that can be executed on your targets to perform various IT operations.",
                "data": {"total_jobs": jobs}
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error retrieving job information: {str(e)}"
            }
    
    async def _handle_run_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run-related queries"""
        try:
            system_data = await self._get_current_system_data()
            runs = system_data.get('runs', 0)
            
            return {
                "success": True,
                "message": f"OpsConductor has executed {runs} job runs. Runs are individual executions of automation jobs with their results and logs.",
                "data": {"total_runs": runs}
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error retrieving run information: {str(e)}"
            }
    
    async def _handle_system_overview_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system overview queries"""
        try:
            system_data = await self._get_current_system_data()
            target_details = system_data.get('target_details', [])
            
            connected_targets = sum(1 for t in target_details 
                                  if any(s.get('connection_status') == 'connected' 
                                        for s in t.get('services', [])))
            
            response = f"""OpsConductor System Overview:

📊 Infrastructure:
• {system_data.get('targets', 0)} managed targets
• {connected_targets} targets connected
• {system_data.get('targets', 0) - connected_targets} targets disconnected

⚙️ Automation:
• {system_data.get('jobs', 0)} automation jobs
• {system_data.get('runs', 0)} job executions

👥 Users:
• {system_data.get('users', 0)} system users

🔧 System Status: Operational
"""
            
            return {
                "success": True,
                "message": response.strip(),
                "data": system_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error retrieving system overview: {str(e)}"
            }