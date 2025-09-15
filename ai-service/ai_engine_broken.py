"""
OpsConductor AI Engine - Core AI functionality
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import httpx
import chromadb
from chromadb.config import Settings
import ollama
import asyncpg
import redis.asyncio as redis
from vector_store import OpsConductorVectorStore
# Temporarily disabled due to dependency issues
# from protocol_manager import protocol_manager, ProtocolResult

logger = logging.getLogger(__name__)

class OpsConductorAI:
    """Main AI Engine for OpsConductor"""
    
    def __init__(self):
        self.ollama_client = None
        self.chroma_client = None
        self.vector_store = None
        self.db_pool = None
        self.redis_client = None
        self.system_knowledge = {}
        # self.protocol_manager = protocol_manager  # Temporarily disabled
        
    async def initialize(self):
        """Initialize all AI components"""
        try:
            # Initialize Ollama client
            self.ollama_client = ollama.AsyncClient(host='http://localhost:11434')
            logger.info("Ollama client initialized")
            
            # Initialize ChromaDB with enhanced vector storage
            try:
                self.chroma_client = chromadb.HttpClient(
                    host='chromadb',
                    port=8000
                )
                
                # Initialize enhanced vector store
                self.vector_store = OpsConductorVectorStore(self.chroma_client)
                vector_init_success = await self.vector_store.initialize_collections()
                
                if vector_init_success:
                    logger.info("Enhanced vector storage initialized successfully")
                    # Load initial knowledge base
                    await self.populate_initial_knowledge()
                else:
                    logger.warning("Vector storage initialization failed")
                    self.vector_store = None
                
            except Exception as e:
                logger.error(f"ChromaDB initialization failed: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                logger.warning("Continuing without vector storage")
                self.chroma_client = None
                self.vector_store = None
            
            # Initialize database connection
            self.db_pool = await asyncpg.create_pool(
                host='postgres',
                port=5432,
                database='opsconductor',
                user='postgres',
                password='postgres123',
                min_size=1,
                max_size=10
            )
            logger.info("Database pool initialized")
            
            # Initialize Redis
            self.redis_client = redis.from_url('redis://redis:6379/5')
            logger.info("Redis client initialized")
            
            # Load system knowledge
            await self.load_system_knowledge()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI engine: {e}")
            return False
    
    async def load_system_knowledge(self):
        """Load current system state into knowledge base"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load targets
                targets = await conn.fetch("SELECT * FROM assets.targets")
                self.system_knowledge['targets'] = [dict(t) for t in targets]
                
                # Load groups
                groups = await conn.fetch("SELECT * FROM assets.target_groups")
                self.system_knowledge['groups'] = [dict(g) for g in groups]
                
                # Load recent jobs
                jobs = await conn.fetch("""
                    SELECT * FROM automation.jobs 
                    ORDER BY created_at DESC 
                    LIMIT 100
                """)
                self.system_knowledge['recent_jobs'] = [dict(j) for j in jobs]
                
            logger.info(f"Loaded system knowledge: {len(self.system_knowledge['targets'])} targets, "
                       f"{len(self.system_knowledge['groups'])} groups, "
                       f"{len(self.system_knowledge['recent_jobs'])} recent jobs")
                       
        except Exception as e:
            logger.error(f"Failed to load system knowledge: {e}")
    
    async def populate_initial_knowledge(self):
        """Populate vector store with initial system knowledge"""
        try:
            if not self.vector_store:
                return
            
            # Store basic system documentation
            await self.vector_store.store_knowledge(
                content="""OpsConductor is an automation platform that manages IT infrastructure through:
                - Target management (servers, workstations, network devices)
                - Automation workflows (PowerShell, Bash scripts)
                - Asset discovery and inventory
                - Job scheduling and execution
                - RBAC (Role-Based Access Control)
                
                Common operations include:
                - Service management (start, stop, restart)
                - Software updates and patches
                - System monitoring and health checks
                - Configuration management
                - Backup and recovery operations""",
                title="OpsConductor Platform Overview",
                category="system_documentation"
            )
            
            # Store troubleshooting knowledge
            await self.vector_store.store_solution(
                problem="Service won't start after update",
                solution="Check service dependencies, verify configuration files, restart dependent services in correct order",
                success_count=5,
                metadata={"category": "service_management", "os": "windows"}
            )
            
            await self.vector_store.store_solution(
                problem="High CPU usage on server",
                solution="Identify top processes with Task Manager or top command, check for runaway processes, analyze recent changes",
                success_count=8,
                metadata={"category": "performance", "os": "both"}
            )
            
            await self.vector_store.store_solution(
                problem="Disk space running low",
                solution="Clean temporary files, check log rotation, identify large files, consider disk expansion",
                success_count=12,
                metadata={"category": "storage", "os": "both"}
            )
            
            logger.info("Initial knowledge base populated")
            
        except Exception as e:
            logger.error(f"Failed to populate initial knowledge: {e}")
    
    async def query_system(self, question: str) -> Dict[str, Any]:
        """Answer questions about the system state with enhanced AI"""
        try:
            question_lower = question.lower()
            
            # First, try to find relevant knowledge from vector store
            context = await self.get_relevant_context(question)
            
            # Handle specific system queries
            if "targets" in question_lower and "tagged" in question_lower:
                # Extract tag from question
                words = question_lower.split()
                tag_idx = -1
                for i, word in enumerate(words):
                    if word in ["with", "tagged"]:
                        tag_idx = i + 1
                        break
                
                if tag_idx < len(words):
                    tag = words[tag_idx].strip("?")
                    return await self.find_targets_by_tag(tag)
            
            elif "how many" in question_lower and "targets" in question_lower:
                return {
                    "answer": f"You have {len(self.system_knowledge['targets'])} targets total",
                    "count": len(self.system_knowledge['targets']),
                    "details": self.system_knowledge['targets']
                }
            
            elif "groups" in question_lower:
                return {
                    "answer": f"You have {len(self.system_knowledge['groups'])} target groups",
                    "groups": [g['name'] for g in self.system_knowledge['groups']],
                    "details": self.system_knowledge['groups']
                }
            
            # Check if this looks like a troubleshooting question
            elif any(word in question_lower for word in ["problem", "issue", "error", "fail", "broken", "not working"]):
                return await self.handle_troubleshooting_query(question, context)
            
            # General knowledge query
            elif context:
                return {
                    "answer": f"Based on the system knowledge: {context[0]['content'][:200]}...",
                    "context": context,
                    "suggestions": [
                        "Which targets are tagged with win10?",
                        "How many targets do I have?",
                        "What groups exist?",
                        "Help with service restart issues"
                    ]
                }
            
            else:
                return {
                    "answer": "I can help you with questions about targets, groups, system status, and troubleshooting. Try asking 'Which targets are tagged with X?' or 'How many targets do I have?'",
                    "suggestions": [
                        "Which targets are tagged with win10?",
                        "How many targets do I have?",
                        "What groups exist?",
                        "Help with service restart issues",
                        "Show me recent jobs"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to query system: {e}")
            return {"error": f"Query failed: {e}"}
    
    async def find_targets_by_tag(self, tag: str) -> Dict[str, Any]:
        """Find targets with a specific tag"""
        try:
            async with self.db_pool.acquire() as conn:
                # Query targets with the specified tag
                targets = await conn.fetch("""
                    SELECT t.*, tg.name as group_name
                    FROM assets.targets t
                    LEFT JOIN assets.target_group_members tgm ON t.id = tgm.target_id
                    LEFT JOIN assets.target_groups tg ON tgm.group_id = tg.id
                    WHERE t.tags::text ILIKE $1 OR t.hostname ILIKE $1 OR t.os_type ILIKE $1
                """, f"%{tag}%")
                
                if not targets:
                    return {
                        "answer": f"No targets found with tag '{tag}'",
                        "count": 0,
                        "targets": []
                    }
                
                target_list = []
                for target in targets:
                    target_dict = dict(target)
                    target_list.append({
                        "hostname": target_dict.get('hostname'),
                        "ip_address": target_dict.get('ip_address'),
                        "os_type": target_dict.get('os_type'),
                        "status": target_dict.get('status'),
                        "group": target_dict.get('group_name'),
                        "tags": target_dict.get('tags')
                    })
                
                return {
                    "answer": f"Found {len(target_list)} targets with tag '{tag}'",
                    "count": len(target_list),
                    "targets": target_list
                }
                
        except Exception as e:
            logger.error(f"Failed to find targets by tag: {e}")
            return {"error": f"Search failed: {e}"}
    
    async def get_relevant_context(self, query: str) -> List[Dict]:
        """Get relevant context from vector store"""
        try:
            if not self.vector_store:
                return []
            
            # Search across all collections for relevant information
            knowledge_results = await self.vector_store.search_knowledge(query, limit=3)
            solution_results = await self.vector_store.search_solutions(query, limit=2)
            
            # Combine and sort by relevance
            all_results = knowledge_results + solution_results
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            return all_results[:5]  # Return top 5 most relevant
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return []
    
    async def handle_troubleshooting_query(self, question: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle troubleshooting questions with AI assistance"""
        try:
            if not self.vector_store:
                return {"answer": "Vector storage not available for troubleshooting assistance"}
            
            # Search for similar problems and solutions
            solutions = await self.vector_store.search_solutions(question, limit=3)
            
            if solutions:
                best_solution = solutions[0]
                answer = f"I found a similar issue: {best_solution['metadata'].get('problem', 'Unknown problem')}\n\n"
                answer += f"Suggested solution: {best_solution['metadata'].get('solution', 'No solution available')}"
                
                # Add additional solutions if available
                if len(solutions) > 1:
                    answer += "\n\nOther related solutions:"
                    for sol in solutions[1:]:
                        answer += f"\n- {sol['metadata'].get('solution', 'No solution')[:100]}..."
                
                return {
                    "answer": answer,
                    "solutions": solutions,
                    "confidence": best_solution.get('similarity', 0)
                }
            else:
                return {
                    "answer": "I don't have specific solutions for this problem in my knowledge base yet. Consider checking system logs, recent changes, or consulting documentation.",
                    "suggestions": [
                        "Check system event logs",
                        "Review recent configuration changes",
                        "Verify service dependencies",
                        "Check resource utilization"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to handle troubleshooting query: {e}")
            return {"error": f"Troubleshooting assistance failed: {e}"}
    
    async def generate_script(self, request: str, language: str = "powershell") -> Dict[str, Any]:
        """Generate scripts using Ollama"""
        try:
            if not self.ollama_client:
                return {"error": "Ollama not available"}
            
            # Create a prompt for script generation
            prompt = f"""
            Generate a {language} script for the following request: {request}
            
            Requirements:
            - Include error handling
            - Add logging/output
            - Make it production-ready
            - Include comments explaining the logic
            
            Request: {request}
            """
            
            response = await self.ollama_client.generate(
                model='codellama:7b',
                prompt=prompt
            )
            
            return {
                "script": response['response'],
                "language": language,
                "request": request
            }
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            return {"error": f"Script generation failed: {e}"}
    
    async def chat(self, message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Enhanced chat interface with vector storage"""
        try:
            message_lower = message.lower()
            
            # Get relevant context from previous interactions
            context = await self.get_relevant_context(message)
            similar_interactions = []
            if self.vector_store:
                similar_interactions = await self.vector_store.find_similar_interactions(message, limit=3)
            
            response = None
            intent = "unknown"
            
            # Check for greetings first
            if (any(phrase in message_lower for phrase in ["hello", "hi", "hey", "what can you", "what do you"]) or 
                ("help me" in message_lower and not any(word in message_lower for word in ["with", "fix", "solve", "restart", "service", "server"]))):
                intent = "greeting"
            
            # System queries
            elif any(word in message_lower for word in ["which", "how many", "show me", "list"]):
                if "targets" in message_lower or "servers" in message_lower:
                    response = await self.query_system(message)
                    intent = "system_query"
            
            # Troubleshooting questions (specific problems, not general greetings)
            elif (any(word in message_lower for word in ["problem", "issue", "error", "fail", "broken", "not working"]) or 
                  ("help" in message_lower and any(word in message_lower for word in ["with", "fix", "solve", "restart", "service", "server"]))):
                response = await self.handle_troubleshooting_query(message, context)
                intent = "troubleshooting"
            
            # Script generation requests
            elif any(word in message_lower for word in ["create", "generate", "script", "automation"]):
                language = "powershell" if "powershell" in message_lower else "bash"
                response = await self.generate_script(message, language)
                intent = "script_generation"
            
            # Protocol-specific operations (temporarily disabled)
            # elif any(word in message_lower for word in ["snmp", "monitor", "network", "device", "switch", "router"]):
            #     response = await self._handle_network_monitoring_request(message)
            #     intent = "network_monitoring"
            # 
            # elif any(word in message_lower for word in ["email", "smtp", "alert", "notification", "notify"]):
            #     response = await self._handle_notification_request(message)
            #     intent = "notification"
            # 
            # elif any(word in message_lower for word in ["camera", "vapix", "axis", "motion", "detection"]):
            #     response = await self._handle_camera_request(message)
            #     intent = "camera_management"
            # 
            # elif any(word in message_lower for word in ["ssh", "remote", "execute", "command", "connect"]):
            #     response = await self._handle_ssh_request(message)
            #     intent = "remote_execution"
            
            # Knowledge queries (if we have relevant context)
            elif context and any(word in message_lower for word in ["docker", "container", "management", "best practices", "how to"]):
                response = {
                    "answer": f"Based on the system knowledge: {context[0]['content'][:500]}...",
                    "context": context,
                    "suggestions": [
                        "Create a Docker management script",
                        "Help with container issues",
                        "Show me Docker best practices"
                    ]
                }
                intent = "knowledge_query"
            
            # If no specific intent detected, treat as greeting
            if not response:
                intent = "greeting"
                base_response = "I'm your OpsConductor AI assistant! I can help you with:\n\n" \
                               "🔍 **System Queries**: 'Which targets are tagged with win10?'\n" \
                               "🛠️ **Script Generation**: 'Create a PowerShell script to restart IIS'\n" \
                               "📊 **System Status**: 'How many targets do I have?'\n" \
                               "🔧 **Troubleshooting**: 'Help with service restart issues'\n" \
                               "🌐 **Network Monitoring**: 'Monitor network devices via SNMP'\n" \
                               "📧 **Email Alerts**: 'Send notification to ops team'\n" \
                               "📹 **Camera Management**: 'Setup motion detection on cameras'\n" \
                               "🖥️ **Remote Execution**: 'Execute commands via SSH'\n\n" \
                               "What would you like to do?"
                
                # Add context from similar interactions if available
                if similar_interactions:
                    base_response += f"\n\n💡 I notice you've asked similar questions before. Here's what worked:"
                    for interaction in similar_interactions[:2]:
                        base_response += f"\n- {interaction['metadata'].get('response', 'No response')[:100]}..."
                
                response = {
                    "response": base_response,
                    "intent": intent,
                    "suggestions": [
                        "Which targets are tagged with win10?",
                        "How many targets do I have?",
                        "Create a PowerShell script to check disk space",
                        "Help with service restart issues",
                        "Monitor network devices via SNMP",
                        "Send email alert to ops team",
                        "Setup camera motion detection",
                        "Execute remote commands via SSH"
                    ]
                }
            
            # Store this interaction for future learning
            if self.vector_store and response:
                success = not response.get("error")
                await self.vector_store.store_user_interaction(
                    query=message,
                    response=str(response.get("response", response.get("answer", ""))),
                    success=success,
                    metadata={
                        "intent": intent,
                        "user_id": user_id,
                        "has_context": len(context) > 0
                    }
                )
            
            # Add intent and context to response
            if isinstance(response, dict):
                response["intent"] = intent
                if context:
                    response["context_used"] = len(context)
            
            return response or {"error": "No response generated"}
                
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"error": f"Chat failed: {e}"}
    
    # Temporarily disabled protocol methods
    async def execute_protocol_operation(self, protocol: str, target: Dict[str, Any], 
                                       command: str, credentials: Dict[str, Any] = None, 
                                       **kwargs) -> Dict[str, Any]:
        """Execute operation using specified protocol"""
        return {"success": False, "error": "Protocol operations temporarily disabled"}
    
    async def send_notification(self, message: str, alert_type: str = "info", 
                              recipients: List[str] = None, use_smtp: bool = True) -> Dict[str, Any]:
        """Send notification via available protocols"""
        return {"success": False, "error": "Notification operations temporarily disabled"}
    
    async def monitor_network_device(self, target: Dict[str, Any], 
                                   monitoring_type: str = "basic") -> Dict[str, Any]:
        """Monitor network device via SNMP"""
        return {"success": False, "error": "Network monitoring temporarily disabled"}
    
    async def setup_camera_monitoring(self, target: Dict[str, Any], 
                                    motion_sensitivity: int = 50) -> Dict[str, Any]:
        """Setup Axis camera motion detection"""
        return {"success": False, "error": "Camera monitoring temporarily disabled"}
    
    async def get_protocol_capabilities(self) -> Dict[str, Any]:
        """Get all supported protocol capabilities"""
        return {"error": "Protocol capabilities temporarily disabled"}

    async def _get_target_credentials(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Get credentials for target from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Try to get credentials from enhanced_targets first
                creds = await conn.fetchrow("""
                    SELECT credentials FROM assets.enhanced_targets 
                    WHERE hostname = $1 OR ip_address = $1
                """, target.get("hostname", target.get("ip_address")))
                
                if creds and creds["credentials"]:
                    return creds["credentials"]
                
                # Fallback to legacy target_credentials
                creds = await conn.fetchrow("""
                    SELECT tc.* FROM assets.target_credentials tc
                    JOIN assets.targets t ON tc.target_id = t.id
                    WHERE t.hostname = $1 OR t.ip_address = $1
                """, target.get("hostname", target.get("ip_address")))
                
                if creds:
                    return {
                        "username": creds.get("username"),
                        "password": creds.get("password"),
                        "private_key": creds.get("private_key"),
                        "community": creds.get("snmp_community")
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get target credentials: {e}")
            return {}

# Global AI instance
ai_engine = OpsConductorAI()
                smtp_config = await self._get_smtp_config()
                if smtp_config:
                    result = await self.protocol_manager.execute(
                        "smtp", smtp_config["target"], "send_alert",
                        credentials=smtp_config["credentials"],
                        alert_type=alert_type,
                        message=message,
                        severity=alert_type,
                        recipients=recipients
                    )
                    return result.to_dict()
            
            # Fallback to storing in database
            await self._store_notification(message, alert_type, recipients)
            return {"success": True, "method": "database_storage"}
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_smtp_config(self) -> Optional[Dict[str, Any]]:
        """Get SMTP configuration from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Look for SMTP targets
                smtp_target = await conn.fetchrow("""
                    SELECT * FROM assets.enhanced_targets 
                    WHERE service_type = 'smtp' 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                if smtp_target:
                    return {
                        "target": {
                            "hostname": smtp_target["hostname"],
                            "ip_address": smtp_target["ip_address"],
                            "port": smtp_target.get("port", 587),
                            "use_tls": True
                        },
                        "credentials": smtp_target.get("credentials", {})
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get SMTP config: {e}")
            return None
    
    async def _store_notification(self, message: str, alert_type: str, recipients: List[str]):
        """Store notification in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO communication.notifications 
                    (title, message, type, recipients, status, created_at)
                    VALUES ($1, $2, $3, $4, 'pending', NOW())
                """, f"AI Alert: {alert_type}", message, alert_type, recipients or [])
                
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
    
    async def monitor_network_device(self, target: Dict[str, Any], 
                                   monitoring_type: str = "basic") -> Dict[str, Any]:
        """Monitor network device via SNMP"""
        try:
            credentials = await self._get_target_credentials(target)
            
            if monitoring_type == "basic":
                result = await self.protocol_manager.execute(
                    "snmp", target, "get_system_info", credentials=credentials
                )
            elif monitoring_type == "interfaces":
                result = await self.protocol_manager.execute(
                    "snmp", target, "get_interface_stats", credentials=credentials
                )
            else:
                return {"success": False, "error": f"Unknown monitoring type: {monitoring_type}"}
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Network monitoring failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def setup_camera_monitoring(self, target: Dict[str, Any], 
                                    motion_sensitivity: int = 50) -> Dict[str, Any]:
        """Setup Axis camera motion detection"""
        try:
            credentials = await self._get_target_credentials(target)
            
            # Setup motion detection
            result = await self.protocol_manager.execute(
                "vapix", target, "setup_motion_detection",
                credentials=credentials,
                sensitivity=motion_sensitivity,
                enabled=True
            )
            
            if result.success:
                # Store configuration for future reference
                if self.vector_store:
                    await self.vector_store.store_knowledge(
                        content=f"Camera {target.get('hostname')} configured with motion detection at {motion_sensitivity}% sensitivity",
                        title=f"Camera Motion Detection - {target.get('hostname')}",
                        category="camera_configuration"
                    )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Camera setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_protocol_capabilities(self) -> Dict[str, Any]:
        """Get all supported protocol capabilities"""
        try:
            protocols = self.protocol_manager.get_supported_protocols()
            capabilities = {}
            
            for protocol in protocols:
                capabilities[protocol] = self.protocol_manager.get_protocol_capabilities(protocol)
            
            return {
                "supported_protocols": protocols,
                "capabilities": capabilities,
                "active_connections": len(self.protocol_manager.active_connections)
            }
            
        except Exception as e:
            logger.error(f"Failed to get protocol capabilities: {e}")
            return {"error": str(e)}
    
    async def _handle_network_monitoring_request(self, message: str) -> Dict[str, Any]:
        """Handle network monitoring requests"""
        try:
            message_lower = message.lower()
            
            # Try to find network devices in the system
            async with self.db_pool.acquire() as conn:
                network_targets = await conn.fetch("""
                    SELECT hostname, ip_address, service_type 
                    FROM assets.enhanced_targets 
                    WHERE service_type IN ('snmp', 'network', 'switch', 'router')
                    LIMIT 5
                """)
            
            if not network_targets:
                return {
                    "answer": "I can help you monitor network devices via SNMP, but I don't see any network devices configured in the system yet.",
                    "suggestions": [
                        "Add network devices to the asset inventory first",
                        "Configure SNMP credentials for your devices",
                        "Try: 'Monitor device 192.168.1.1 via SNMP'"
                    ]
                }
            
            # If specific monitoring requested
            if "monitor" in message_lower:
                device_list = "\n".join([f"• {t['hostname']} ({t['ip_address']}) - {t['service_type']}" 
                                       for t in network_targets])
                
                return {
                    "answer": f"I found {len(network_targets)} network devices that can be monitored via SNMP:\n\n{device_list}\n\nI can help you:\n• Get system information\n• Monitor interface statistics\n• Check device health\n• Set up automated monitoring",
                    "suggestions": [
                        f"Monitor {network_targets[0]['hostname']} system info",
                        f"Get interface stats for {network_targets[0]['hostname']}",
                        "Set up automated network monitoring",
                        "Show SNMP capabilities"
                    ]
                }
            
            return {
                "answer": "I can help you with network device monitoring using SNMP. What would you like to do?",
                "capabilities": ["System information", "Interface statistics", "Device health checks", "Automated monitoring"],
                "available_devices": len(network_targets)
            }
            
        except Exception as e:
            logger.error(f"Network monitoring request failed: {e}")
            return {"error": f"Failed to process network monitoring request: {e}"}
    
    async def _handle_notification_request(self, message: str) -> Dict[str, Any]:
        """Handle notification and email requests"""
        try:
            message_lower = message.lower()
            
            # Check if SMTP is configured
            smtp_config = await self._get_smtp_config()
            
            if "send" in message_lower and ("email" in message_lower or "alert" in message_lower):
                if not smtp_config:
                    return {
                        "answer": "I can send notifications, but SMTP is not configured yet. I can help you:",
                        "suggestions": [
                            "Configure SMTP server settings",
                            "Add email targets to the system",
                            "Store notifications in the database instead",
                            "Set up email alerts for monitoring"
                        ]
                    }
                
                return {
                    "answer": f"I can send email notifications via SMTP server at {smtp_config['target']['hostname']}. What would you like to send?",
                    "suggestions": [
                        "Send test email to ops team",
                        "Send alert about system status",
                        "Configure automated email alerts",
                        "Set up notification templates"
                    ]
                }
            
            return {
                "answer": "I can help you with email notifications and alerts. What would you like to do?",
                "capabilities": ["Send email alerts", "Configure SMTP", "Automated notifications", "Alert templates"],
                "smtp_configured": smtp_config is not None
            }
            
        except Exception as e:
            logger.error(f"Notification request failed: {e}")
            return {"error": f"Failed to process notification request: {e}"}
    
    async def _handle_camera_request(self, message: str) -> Dict[str, Any]:
        """Handle camera and VAPIX requests"""
        try:
            message_lower = message.lower()
            
            # Look for camera targets
            async with self.db_pool.acquire() as conn:
                camera_targets = await conn.fetch("""
                    SELECT hostname, ip_address, service_type 
                    FROM assets.enhanced_targets 
                    WHERE service_type IN ('vapix', 'camera', 'axis')
                    LIMIT 5
                """)
            
            if not camera_targets:
                return {
                    "answer": "I can help you manage Axis cameras via VAPIX API, but I don't see any cameras configured in the system yet.",
                    "suggestions": [
                        "Add Axis cameras to the asset inventory",
                        "Configure camera credentials",
                        "Try: 'Setup motion detection on camera 192.168.1.100'"
                    ]
                }
            
            if "motion" in message_lower or "detection" in message_lower:
                camera_list = "\n".join([f"• {t['hostname']} ({t['ip_address']})" for t in camera_targets])
                
                return {
                    "answer": f"I found {len(camera_targets)} cameras that support motion detection:\n\n{camera_list}\n\nI can help you:\n• Setup motion detection\n• Configure sensitivity levels\n• Capture images\n• Get camera system info",
                    "suggestions": [
                        f"Setup motion detection on {camera_targets[0]['hostname']}",
                        f"Capture image from {camera_targets[0]['hostname']}",
                        "Configure motion sensitivity to 75%",
                        "Get camera system information"
                    ]
                }
            
            return {
                "answer": "I can help you manage Axis cameras using VAPIX API. What would you like to do?",
                "capabilities": ["Motion detection setup", "Image capture", "System information", "Configuration management"],
                "available_cameras": len(camera_targets)
            }
            
        except Exception as e:
            logger.error(f"Camera request failed: {e}")
            return {"error": f"Failed to process camera request: {e}"}
    
    async def _handle_ssh_request(self, message: str) -> Dict[str, Any]:
        """Handle SSH and remote execution requests"""
        try:
            message_lower = message.lower()
            
            # Look for SSH-capable targets
            async with self.db_pool.acquire() as conn:
                ssh_targets = await conn.fetch("""
                    SELECT hostname, ip_address, os_type 
                    FROM assets.enhanced_targets 
                    WHERE service_type = 'ssh' OR os_type IN ('linux', 'unix')
                    LIMIT 5
                """)
            
            if not ssh_targets:
                return {
                    "answer": "I can help you execute remote commands via SSH, but I don't see any SSH-enabled targets configured yet.",
                    "suggestions": [
                        "Add Linux/Unix servers to the asset inventory",
                        "Configure SSH credentials for your servers",
                        "Try: 'Execute command on server1.example.com'"
                    ]
                }
            
            if "execute" in message_lower or "command" in message_lower:
                server_list = "\n".join([f"• {t['hostname']} ({t['ip_address']}) - {t['os_type']}" 
                                       for t in ssh_targets])
                
                return {
                    "answer": f"I found {len(ssh_targets)} servers available for SSH execution:\n\n{server_list}\n\nI can help you:\n• Execute single commands\n• Run scripts remotely\n• Transfer files\n• Manage remote systems",
                    "suggestions": [
                        f"Execute 'df -h' on {ssh_targets[0]['hostname']}",
                        f"Run system update script on {ssh_targets[0]['hostname']}",
                        "Check disk space on all Linux servers",
                        "Transfer configuration file to servers"
                    ]
                }
            
            return {
                "answer": "I can help you with remote command execution via SSH. What would you like to do?",
                "capabilities": ["Command execution", "Script running", "File transfer", "System management"],
                "available_servers": len(ssh_targets)
            }
            
        except Exception as e:
            logger.error(f"SSH request failed: {e}")
            return {"error": f"Failed to process SSH request: {e}"}

# Global AI instance
ai_engine = OpsConductorAI()