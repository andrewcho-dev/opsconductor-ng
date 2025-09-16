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
                "users": "System users with different roles and permissions"
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
    
    async def handle_system_query(self, query: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system-specific queries with real-time data"""
        try:
            query_lower = query.lower()
            
            # Handle target-related queries
            if any(term in query_lower for term in ["target", "server", "machine", "system"]):
                return await self._handle_target_query(query, parsed_data)
            
            # Handle job-related queries
            elif any(term in query_lower for term in ["job", "task", "automation"]):
                return await self._handle_job_query(query, parsed_data)
            
            # Handle run-related queries
            elif any(term in query_lower for term in ["run", "execution", "result"]):
                return await self._handle_run_query(query, parsed_data)
            
            # Handle general system queries
            elif any(term in query_lower for term in ["status", "health", "overview", "summary"]):
                return await self._handle_system_overview_query(query, parsed_data)
            
            else:
                return {
                    "success": False,
                    "message": "Query type not recognized",
                    "suggestion": "Try asking about targets, jobs, runs, or system status"
                }
                
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
                # Count query
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
                
                response = f"OpsConductor Targets ({len(target_details)} total):\n\n"
                for target in target_details:
                    services = target.get('services', [])
                    status = "Connected" if any(s.get('connection_status') == 'connected' for s in services) else "Disconnected"
                    response += f"• {target['name']} ({target['ip_address']})\n"
                    response += f"  OS: {target['os_type']}\n"
                    response += f"  Status: {status}\n"
                    response += f"  Services: {len(services)}\n\n"
                
                return {
                    "success": True,
                    "message": response.strip(),
                    "data": {"targets": target_details}
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