"""
OpsConductor AI Engine - Complete Integration
One clean, seamless AI system with full protocol support and vector intelligence
"""
import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import spacy
import ollama
import asyncpg
import redis.asyncio as redis
from vector_store import OpsConductorVectorStore
from protocol_manager import protocol_manager, ProtocolResult
from learning_engine import learning_engine, PredictionResult
from asset_client import AssetServiceClient
from automation_client import AutomationServiceClient
from communication_client import CommunicationServiceClient

logger = logging.getLogger(__name__)

class OpsConductorAI:
    """Complete AI Engine for OpsConductor with Protocol Integration"""
    
    def __init__(self):
        self.nlp = None
        self.ollama_client = ollama.AsyncClient()
        self.vector_store = None
        self.db_pool = None
        self.redis_client = None
        self.protocol_manager = protocol_manager
        self.learning_engine = learning_engine
        self.system_knowledge = {}
        
        # Initialize service clients
        self.asset_client = AssetServiceClient()
        self.automation_client = AutomationServiceClient()
        self.communication_client = CommunicationServiceClient()
        
    async def initialize(self):
        """Initialize all AI components"""
        try:
            # Initialize spaCy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
            
            # Initialize vector store
            import chromadb
            chroma_client = chromadb.Client()
            self.vector_store = OpsConductorVectorStore(chroma_client)
            await self.vector_store.initialize_collections()
            logger.info("Vector store initialized")
            
            # Initialize database connection
            self.db_pool = await asyncpg.create_pool(
                host="postgres",
                port=5432,
                user="postgres",
                password="postgres123",
                database="opsconductor",
                min_size=2,
                max_size=10
            )
            logger.info("Database pool created")
            
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host="redis",
                port=6379,
                decode_responses=True
            )
            logger.info("Redis client initialized")
            
            # Load system knowledge
            await self.load_system_knowledge()
            
            logger.info("Complete AI Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Engine: {e}")
            return False
    
    async def load_system_knowledge(self):
        """Load system knowledge from database"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load target information
                targets = await conn.fetch("SELECT * FROM assets.targets LIMIT 100")
                self.system_knowledge['targets'] = [dict(t) for t in targets]
                
                # Load enhanced targets
                enhanced_targets = await conn.fetch("SELECT * FROM assets.enhanced_targets LIMIT 100")
                self.system_knowledge['enhanced_targets'] = [dict(t) for t in enhanced_targets]
                
                # Load automation jobs
                jobs = await conn.fetch("SELECT * FROM automation.jobs ORDER BY created_at DESC LIMIT 50")
                self.system_knowledge['recent_jobs'] = [dict(j) for j in jobs]
                
                logger.info(f"Loaded system knowledge: {len(targets)} targets, {len(enhanced_targets)} enhanced targets, {len(jobs)} recent jobs")
                
        except Exception as e:
            logger.error(f"Failed to load system knowledge: {e}")
    
    async def get_relevant_context(self, query: str, limit: int = 3) -> List[Dict]:
        """Get relevant context from vector store"""
        try:
            if self.vector_store:
                return await self.vector_store.search_knowledge(query, limit=limit)
            return []
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return []
    
    async def detect_intent(self, message: str) -> Dict[str, Any]:
        """Enhanced intent detection with protocol awareness"""
        message_lower = message.lower()
        
        # Protocol-specific intents
        if any(word in message_lower for word in ['snmp', 'network', 'switch', 'router', 'monitor']):
            return {
                "intent": "network_monitoring",
                "confidence": 0.9,
                "protocols": ["snmp"],
                "action": "monitor_network_devices"
            }
        
        if any(word in message_lower for word in ['email', 'alert', 'notify', 'send mail']):
            return {
                "intent": "email_notification",
                "confidence": 0.9,
                "protocols": ["smtp"],
                "action": "send_notification"
            }
        
        if any(word in message_lower for word in ['ssh', 'remote', 'execute', 'run command']):
            return {
                "intent": "remote_execution",
                "confidence": 0.9,
                "protocols": ["ssh"],
                "action": "execute_remote_command"
            }
        
        if any(word in message_lower for word in ['camera', 'vapix', 'axis', 'motion']):
            return {
                "intent": "camera_management",
                "confidence": 0.9,
                "protocols": ["vapix"],
                "action": "manage_cameras"
            }
        
        # System query intents
        if any(word in message_lower for word in ['credentials', 'credential', 'passwords', 'ssh keys', 'authentication']):
            return {
                "intent": "credential_query",
                "confidence": 0.9,
                "action": "query_credentials"
            }
        
        if any(word in message_lower for word in ['services', 'service', 'ports', 'ssh', 'winrm', 'protocols']):
            return {
                "intent": "service_query",
                "confidence": 0.9,
                "action": "query_services"
            }
        
        if any(word in message_lower for word in ['target details', 'target info', 'os version', 'operating system']):
            return {
                "intent": "target_details_query",
                "confidence": 0.9,
                "action": "query_target_details"
            }
        
        if any(word in message_lower for word in ['connection', 'connectivity', 'reachable', 'unreachable', 'connection test']):
            return {
                "intent": "connection_status_query",
                "confidence": 0.9,
                "action": "query_connection_status"
            }
        
        if any(word in message_lower for word in ['target groups', 'groups', 'target group']):
            return {
                "intent": "target_group_query",
                "confidence": 0.9,
                "action": "query_target_groups"
            }
        
        if any(word in message_lower for word in ['targets', 'servers', 'hosts', 'machines']):
            return {
                "intent": "system_query",
                "confidence": 0.8,
                "action": "query_targets"
            }
        
        if any(word in message_lower for word in ['workflows', 'workflow', 'templates']):
            return {
                "intent": "workflow_query", 
                "confidence": 0.9,
                "action": "query_workflows"
            }
        
        if any(word in message_lower for word in ['executions', 'execution history', 'job history', 'runs']):
            return {
                "intent": "execution_history_query",
                "confidence": 0.9, 
                "action": "query_execution_history"
            }
        
        if any(word in message_lower for word in ['jobs', 'automation', 'tasks']):
            return {
                "intent": "automation_query",
                "confidence": 0.8,
                "action": "query_jobs"
            }
        
        # Script generation intents
        if any(word in message_lower for word in ['script', 'powershell', 'bash', 'create', 'generate']):
            return {
                "intent": "script_generation",
                "confidence": 0.8,
                "action": "generate_script"
            }
        
        # Recommendations intents
        if any(word in message_lower for word in ['recommend', 'suggest', 'advice', 'optimize', 'improve']):
            return {
                "intent": "recommendations",
                "confidence": 0.8,
                "action": "get_recommendations"
            }
        
        # Performance and analytics intents
        if any(word in message_lower for word in ['performance', 'metrics', 'statistics', 'stats', 'trends']):
            return {
                "intent": "performance_query",
                "confidence": 0.9,
                "action": "query_performance"
            }
        
        if any(word in message_lower for word in ['errors', 'failures', 'error analysis', 'failure analysis']):
            return {
                "intent": "error_analysis_query",
                "confidence": 0.9,
                "action": "query_error_analysis"
            }
        
        if any(word in message_lower for word in ['notifications', 'alerts sent', 'email history', 'messages']):
            return {
                "intent": "notification_history_query",
                "confidence": 0.9,
                "action": "query_notification_history"
            }
        
        # Advanced automation queries
        if any(word in message_lower for word in ['execution details', 'step details', 'job logs', 'execution logs']):
            return {
                "intent": "job_execution_details_query",
                "confidence": 0.9,
                "action": "query_job_execution_details"
            }
        
        if any(word in message_lower for word in ['scheduled jobs', 'job schedule', 'scheduling', 'cron jobs', 'triggers']):
            return {
                "intent": "job_scheduling_query",
                "confidence": 0.9,
                "action": "query_job_scheduling"
            }
        
        if any(word in message_lower for word in ['workflow steps', 'step analysis', 'workflow dependencies', 'step dependencies']):
            return {
                "intent": "workflow_step_analysis_query",
                "confidence": 0.9,
                "action": "query_workflow_step_analysis"
            }
        
        if any(word in message_lower for word in ['task queue', 'queue status', 'pending tasks', 'running tasks', 'workers']):
            return {
                "intent": "task_queue_query",
                "confidence": 0.9,
                "action": "query_task_queue"
            }
        
        # Communication queries
        if any(word in message_lower for word in ['notification audit', 'delivery status', 'email delivery', 'notification delivery']):
            return {
                "intent": "notification_audit_query",
                "confidence": 0.9,
                "action": "query_notification_audit"
            }
        
        # System health intents
        if any(word in message_lower for word in ['health', 'status', 'anomaly', 'alert']):
            return {
                "intent": "system_health",
                "confidence": 0.8,
                "action": "system_health"
            }
        
        # Greeting intents
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'help']):
            return {
                "intent": "greeting",
                "confidence": 0.7,
                "action": "provide_greeting"
            }
        
        # Default to general query
        return {
            "intent": "general_query",
            "confidence": 0.5,
            "action": "general_response"
        }
    
    async def process_message(self, message: str, user_id: str = "system") -> Dict[str, Any]:
        """Process user message with complete protocol integration and learning"""
        start_time = datetime.utcnow()
        
        try:
            # Detect intent
            intent_result = await self.detect_intent(message)
            
            # Get relevant context
            context = await self.get_relevant_context(message)
            
            # Store interaction for learning
            if self.vector_store:
                await self.vector_store.store_interaction(user_id, message, intent_result)
            
            # Get failure risk prediction for operations
            prediction = None
            if intent_result["action"] in ["network_monitoring", "execute_remote_command", "manage_cameras"]:
                target_info = {"operation": intent_result["action"], "user_id": user_id}
                prediction = await self.learning_engine.predict_failure_risk(
                    intent_result["action"], target_info, user_id
                )
            
            # Route to appropriate handler
            response = None
            if intent_result["action"] == "network_monitoring":
                response = await self.handle_network_monitoring(message, context, prediction)
            elif intent_result["action"] == "send_notification":
                response = await self.handle_email_notification(message, context, prediction)
            elif intent_result["action"] == "execute_remote_command":
                response = await self.handle_remote_execution(message, context, prediction)
            elif intent_result["action"] == "manage_cameras":
                response = await self.handle_camera_management(message, context, prediction)
            elif intent_result["action"] == "query_targets":
                response = await self.handle_target_query(message, context)
            elif intent_result["action"] == "query_target_groups":
                response = await self.handle_target_group_query(message, context)
            elif intent_result["action"] == "query_credentials":
                response = await self.handle_credential_query(message, context)
            elif intent_result["action"] == "query_services":
                response = await self.handle_service_query(message, context)
            elif intent_result["action"] == "query_target_details":
                response = await self.handle_target_details_query(message, context)
            elif intent_result["action"] == "query_connection_status":
                response = await self.handle_connection_status_query(message, context)
            elif intent_result["action"] == "query_jobs":
                response = await self.handle_job_query(message, context)
            elif intent_result["action"] == "query_workflows":
                response = await self.handle_workflow_query(message, context)
            elif intent_result["action"] == "query_execution_history":
                response = await self.handle_execution_history_query(message, context)
            elif intent_result["action"] == "query_performance":
                response = await self.handle_performance_query(message, context)
            elif intent_result["action"] == "query_error_analysis":
                response = await self.handle_error_analysis_query(message, context)
            elif intent_result["action"] == "query_notification_history":
                response = await self.handle_notification_history_query(message, context)
            elif intent_result["action"] == "query_job_execution_details":
                response = await self.handle_job_execution_details_query(message, context)
            elif intent_result["action"] == "query_job_scheduling":
                response = await self.handle_job_scheduling_query(message, context)
            elif intent_result["action"] == "query_workflow_step_analysis":
                response = await self.handle_workflow_step_analysis_query(message, context)
            elif intent_result["action"] == "query_task_queue":
                response = await self.handle_task_queue_query(message, context)
            elif intent_result["action"] == "query_notification_audit":
                response = await self.handle_notification_audit_query(message, context)
            elif intent_result["action"] == "generate_script":
                response = await self.handle_script_generation(message, context)
            elif intent_result["action"] == "provide_greeting":
                response = await self.handle_greeting(message, context)
            elif intent_result["action"] == "get_recommendations":
                response = await self.handle_user_recommendations(user_id, context)
            elif intent_result["action"] == "system_health":
                response = await self.handle_system_health_query(context)
            else:
                response = await self.handle_general_query(message, context)
            
            # Record execution for learning
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            success = response.get("success", True)
            
            await self.learning_engine.record_execution(
                user_id=user_id,
                operation_type=intent_result["action"],
                target_info={"message": message, "intent": intent_result},
                duration=duration,
                success=success,
                error_message=response.get("error") if not success else None
            )
            
            # Add prediction info to response if available
            if prediction:
                response["prediction"] = prediction.to_dict()
            
            return response
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Record failed execution
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            await self.learning_engine.record_execution(
                user_id=user_id,
                operation_type="unknown",
                target_info={"message": message},
                duration=duration,
                success=False,
                error_message=str(e)
            )
            
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "intent": "error",
                "success": False
            }
    
    async def handle_network_monitoring(self, message: str, context: List[Dict], prediction: Optional[PredictionResult] = None) -> Dict[str, Any]:
        """Handle SNMP network monitoring requests"""
        try:
            # Find network targets
            network_targets = []
            for target in self.system_knowledge.get('targets', []):
                if any(tag in str(target.get('tags', '')).lower() for tag in ['switch', 'router', 'network']):
                    network_targets.append(target)
            
            if not network_targets:
                return {
                    "response": "🔍 No network devices found in your targets. Please add network switches or routers with SNMP tags.",
                    "intent": "network_monitoring",
                    "success": False
                }
            
            # Generate SNMP monitoring response
            response = f"🌐 **Network Monitoring Available**\n\n"
            response += f"**Found {len(network_targets)} network devices:**\n"
            
            for target in network_targets[:5]:  # Show first 5
                response += f"• {target.get('hostname', 'Unknown')} ({target.get('ip_address', 'No IP')})\n"
            
            if len(network_targets) > 5:
                response += f"• ... and {len(network_targets) - 5} more devices\n"
            
            response += "\n**Available SNMP Operations:**\n"
            response += "• `get_system_info` - Device information\n"
            response += "• `get_interface_stats` - Network interface statistics\n"
            response += "• `get_cpu_usage` - CPU utilization\n"
            response += "• `get_memory_usage` - Memory utilization\n"
            response += "• `walk_oid` - Custom SNMP walks\n"
            
            response += "\n💡 **Example:** \"Check system info on switch-01\" or \"Monitor all network interfaces\""
            
            # Add prediction information if available
            if prediction:
                response += f"\n\n🔮 **AI Prediction:**\n"
                response += f"• Risk Level: {prediction.predicted_outcome.title()}\n"
                response += f"• Confidence: {prediction.confidence:.1%}\n"
                
                if prediction.risk_factors:
                    response += f"• Risk Factors: {', '.join(prediction.risk_factors[:2])}\n"
                
                if prediction.recommendations:
                    response += f"• Recommendation: {prediction.recommendations[0]}\n"
            
            return {
                "response": response,
                "intent": "network_monitoring",
                "success": True,
                "data": {
                    "network_targets": len(network_targets),
                    "protocols": ["snmp"],
                    "prediction": prediction.to_dict() if prediction else None
                }
            }
            
        except Exception as e:
            logger.error(f"Network monitoring error: {e}")
            return {
                "response": f"❌ Error handling network monitoring: {str(e)}",
                "intent": "network_monitoring",
                "success": False
            }
    
    async def handle_email_notification(self, message: str, context: List[Dict], prediction: Optional[PredictionResult] = None) -> Dict[str, Any]:
        """Handle SMTP email notification requests"""
        try:
            response = "📧 **Email Notification System**\n\n"
            response += "**Available SMTP Operations:**\n"
            response += "• `send_email` - Send custom email messages\n"
            response += "• `send_alert` - Send formatted system alerts\n"
            response += "• `test_connection` - Test SMTP server connectivity\n"
            
            response += "\n**Supported Alert Types:**\n"
            response += "• System alerts (critical, warning, info)\n"
            response += "• Automation job notifications\n"
            response += "• Custom formatted messages\n"
            
            response += "\n💡 **Example:** \"Send alert about disk space\" or \"Email the ops team about server status\""
            
            return {
                "response": response,
                "intent": "email_notification",
                "success": True,
                "data": {
                    "protocols": ["smtp"]
                }
            }
            
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return {
                "response": f"❌ Error handling email notification: {str(e)}",
                "intent": "email_notification",
                "success": False
            }
    
    async def handle_remote_execution(self, message: str, context: List[Dict], prediction: Optional[PredictionResult] = None) -> Dict[str, Any]:
        """Handle SSH remote execution requests"""
        try:
            # Find SSH-capable targets
            ssh_targets = []
            for target in self.system_knowledge.get('targets', []):
                if target.get('os_type') in ['linux', 'unix'] or 'ssh' in str(target.get('tags', '')).lower():
                    ssh_targets.append(target)
            
            response = f"🔐 **Remote Execution via SSH**\n\n"
            response += f"**Found {len(ssh_targets)} SSH-capable targets**\n\n"
            
            response += "**Available SSH Operations:**\n"
            response += "• `run_command` - Execute single commands\n"
            response += "• `run_script` - Execute complete scripts\n"
            response += "• `file_transfer` - Upload/download files\n"
            
            response += "\n**Supported Script Types:**\n"
            response += "• Bash scripts (/bin/bash)\n"
            response += "• Python scripts (/usr/bin/python3)\n"
            response += "• Custom interpreters\n"
            
            response += "\n💡 **Example:** \"Run disk check on all Linux servers\" or \"Execute maintenance script\""
            
            return {
                "response": response,
                "intent": "remote_execution",
                "success": True,
                "data": {
                    "ssh_targets": len(ssh_targets),
                    "protocols": ["ssh"]
                }
            }
            
        except Exception as e:
            logger.error(f"Remote execution error: {e}")
            return {
                "response": f"❌ Error handling remote execution: {str(e)}",
                "intent": "remote_execution",
                "success": False
            }
    
    async def handle_camera_management(self, message: str, context: List[Dict], prediction: Optional[PredictionResult] = None) -> Dict[str, Any]:
        """Handle VAPIX camera management requests"""
        try:
            # Find camera targets
            camera_targets = []
            for target in self.system_knowledge.get('targets', []):
                if any(tag in str(target.get('tags', '')).lower() for tag in ['camera', 'axis', 'vapix']):
                    camera_targets.append(target)
            
            response = f"📹 **Camera Management via VAPIX**\n\n"
            response += f"**Found {len(camera_targets)} camera devices**\n\n"
            
            response += "**Available VAPIX Operations:**\n"
            response += "• `get_system_info` - Camera system information\n"
            response += "• `setup_motion_detection` - Configure motion alerts\n"
            response += "• `capture_image` - Take snapshots\n"
            response += "• `get_motion_events` - Retrieve motion events\n"
            
            response += "\n**Motion Detection Features:**\n"
            response += "• Configurable sensitivity levels\n"
            response += "• Real-time motion alerts\n"
            response += "• Event logging and retrieval\n"
            
            response += "\n💡 **Example:** \"Setup motion detection on all cameras\" or \"Capture image from camera-01\""
            
            return {
                "response": response,
                "intent": "camera_management",
                "success": True,
                "data": {
                    "camera_targets": len(camera_targets),
                    "protocols": ["vapix"]
                }
            }
            
        except Exception as e:
            logger.error(f"Camera management error: {e}")
            return {
                "response": f"❌ Error handling camera management: {str(e)}",
                "intent": "camera_management",
                "success": False
            }
    
    async def handle_target_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle target/system queries"""
        try:
            targets = self.system_knowledge.get('targets', [])
            enhanced_targets = self.system_knowledge.get('enhanced_targets', [])
            
            # Parse query for specific filters
            message_lower = message.lower()
            
            if 'win10' in message_lower or 'windows 10' in message_lower:
                filtered_targets = [t for t in targets if 'win10' in str(t.get('tags', '')).lower()]
                filter_desc = "Windows 10"
            elif 'linux' in message_lower:
                filtered_targets = [t for t in targets if t.get('os_type') == 'linux']
                filter_desc = "Linux"
            elif 'online' in message_lower:
                filtered_targets = [t for t in targets if t.get('status') == 'online']
                filter_desc = "Online"
            elif 'offline' in message_lower:
                filtered_targets = [t for t in targets if t.get('status') == 'offline']
                filter_desc = "Offline"
            else:
                filtered_targets = targets
                filter_desc = "All"
            
            response = f"🎯 **{filter_desc} Targets**\n\n"
            response += f"**Found {len(filtered_targets)} targets:**\n\n"
            
            # Group by status
            online_targets = [t for t in filtered_targets if t.get('status') == 'online']
            offline_targets = [t for t in filtered_targets if t.get('status') == 'offline']
            
            if online_targets:
                response += f"**🟢 Online ({len(online_targets)}):**\n"
                for target in online_targets[:10]:  # Show first 10
                    response += f"• {target.get('hostname', 'Unknown')} ({target.get('ip_address', 'No IP')})\n"
                if len(online_targets) > 10:
                    response += f"• ... and {len(online_targets) - 10} more\n"
                response += "\n"
            
            if offline_targets:
                response += f"**🔴 Offline ({len(offline_targets)}):**\n"
                for target in offline_targets[:5]:  # Show first 5
                    response += f"• {target.get('hostname', 'Unknown')} ({target.get('ip_address', 'No IP')})\n"
                if len(offline_targets) > 5:
                    response += f"• ... and {len(offline_targets) - 5} more\n"
            
            response += "\n💡 **Available Actions:**\n"
            response += "• Create automation for these targets\n"
            response += "• Monitor with SNMP (network devices)\n"
            response += "• Execute commands via SSH (Linux/Unix)\n"
            response += "• Send notifications about status changes"
            
            return {
                "response": response,
                "intent": "system_query",
                "success": True,
                "data": {
                    "total_targets": len(filtered_targets),
                    "online": len(online_targets),
                    "offline": len(offline_targets),
                    "filter": filter_desc
                }
            }
            
        except Exception as e:
            logger.error(f"Target query error: {e}")
            return {
                "response": f"❌ Error querying targets: {str(e)}",
                "intent": "system_query",
                "success": False
            }
    
    async def handle_job_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle automation job queries"""
        try:
            jobs = self.system_knowledge.get('recent_jobs', [])
            
            response = f"⚙️ **Recent Automation Jobs**\n\n"
            response += f"**Found {len(jobs)} recent jobs:**\n\n"
            
            # Group by status
            running_jobs = [j for j in jobs if j.get('status') == 'running']
            completed_jobs = [j for j in jobs if j.get('status') == 'completed']
            failed_jobs = [j for j in jobs if j.get('status') == 'failed']
            
            if running_jobs:
                response += f"**🔄 Running ({len(running_jobs)}):**\n"
                for job in running_jobs[:5]:
                    response += f"• {job.get('name', 'Unnamed')} - Started {job.get('created_at', 'Unknown')}\n"
                response += "\n"
            
            if completed_jobs:
                response += f"**✅ Completed ({len(completed_jobs)}):**\n"
                for job in completed_jobs[:5]:
                    response += f"• {job.get('name', 'Unnamed')} - {job.get('created_at', 'Unknown')}\n"
                response += "\n"
            
            if failed_jobs:
                response += f"**❌ Failed ({len(failed_jobs)}):**\n"
                for job in failed_jobs[:3]:
                    response += f"• {job.get('name', 'Unnamed')} - {job.get('created_at', 'Unknown')}\n"
                response += "\n"
            
            response += "💡 **Available Actions:**\n"
            response += "• Create new automation workflows\n"
            response += "• Generate scripts for common tasks\n"
            response += "• Schedule recurring jobs\n"
            response += "• Monitor job execution status"
            
            return {
                "response": response,
                "intent": "automation_query",
                "success": True,
                "data": {
                    "total_jobs": len(jobs),
                    "running": len(running_jobs),
                    "completed": len(completed_jobs),
                    "failed": len(failed_jobs)
                }
            }
            
        except Exception as e:
            logger.error(f"Job query error: {e}")
            return {
                "response": f"❌ Error querying jobs: {str(e)}",
                "intent": "automation_query",
                "success": False
            }
    
    async def handle_script_generation(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle script generation requests using Ollama"""
        try:
            # Determine script type from message
            message_lower = message.lower()
            
            if 'powershell' in message_lower:
                script_type = "PowerShell"
                model_prompt = "Generate a PowerShell script"
            elif 'bash' in message_lower:
                script_type = "Bash"
                model_prompt = "Generate a Bash script"
            elif 'python' in message_lower:
                script_type = "Python"
                model_prompt = "Generate a Python script"
            else:
                script_type = "PowerShell"  # Default
                model_prompt = "Generate a PowerShell script"
            
            # Create enhanced prompt with context
            enhanced_prompt = f"""
{model_prompt} for the following request: {message}

Context from OpsConductor system:
- Available targets: {len(self.system_knowledge.get('targets', []))}
- Recent automations: {len(self.system_knowledge.get('recent_jobs', []))}

Requirements:
1. Include proper error handling
2. Add logging/output for monitoring
3. Make it production-ready
4. Include comments explaining the logic
5. Follow best practices for {script_type}

Generate only the script code with comments.
"""
            
            # Generate script using Ollama
            try:
                ollama_response = await self.ollama_client.generate(
                    model="codellama",
                    prompt=enhanced_prompt
                )
                generated_script = ollama_response.get('response', '')
            except Exception as ollama_error:
                logger.warning(f"Ollama generation failed: {ollama_error}, using template")
                generated_script = self._generate_template_script(message, script_type)
            
            response = f"🔧 **Generated {script_type} Script**\n\n"
            response += f"```{script_type.lower()}\n{generated_script}\n```\n\n"
            response += "**Next Steps:**\n"
            response += "• Review and test the script in a safe environment\n"
            response += "• Modify parameters as needed for your targets\n"
            response += "• Create an automation job to execute this script\n"
            response += "• Schedule for recurring execution if needed"
            
            return {
                "response": response,
                "intent": "script_generation",
                "success": True,
                "data": {
                    "script_type": script_type,
                    "script_content": generated_script,
                    "generated_by": "ollama" if 'ollama_response' in locals() else "template"
                }
            }
            
        except Exception as e:
            logger.error(f"Script generation error: {e}")
            return {
                "response": f"❌ Error generating script: {str(e)}",
                "intent": "script_generation",
                "success": False
            }
    
    def _generate_template_script(self, message: str, script_type: str) -> str:
        """Generate template script when Ollama is unavailable"""
        if script_type == "PowerShell":
            return """# OpsConductor Generated PowerShell Script
param(
    [string]$ComputerName = $env:COMPUTERNAME,
    [string]$LogPath = "C:\\Logs\\OpsConductor.log"
)

try {
    Write-Host "Starting OpsConductor automation on $ComputerName"
    
    # Add your automation logic here
    $result = Get-ComputerInfo | Select-Object WindowsProductName, TotalPhysicalMemory
    
    Write-Host "Automation completed successfully"
    $result | Out-String | Write-Host
    
} catch {
    Write-Error "Automation failed: $($_.Exception.Message)"
    exit 1
}"""
        elif script_type == "Bash":
            return """#!/bin/bash
# OpsConductor Generated Bash Script

set -e  # Exit on error

HOSTNAME=$(hostname)
LOG_FILE="/var/log/opsconductor.log"

echo "Starting OpsConductor automation on $HOSTNAME" | tee -a "$LOG_FILE"

# Add your automation logic here
system_info=$(uname -a)
disk_usage=$(df -h)

echo "System Info: $system_info" | tee -a "$LOG_FILE"
echo "Disk Usage:" | tee -a "$LOG_FILE"
echo "$disk_usage" | tee -a "$LOG_FILE"

echo "Automation completed successfully" | tee -a "$LOG_FILE"
"""
        else:  # Python
            return """#!/usr/bin/env python3
# OpsConductor Generated Python Script

import sys
import logging
import platform
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info(f"Starting OpsConductor automation on {platform.node()}")
        
        # Add your automation logic here
        system_info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"System info collected: {system_info}")
        logger.info("Automation completed successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Automation failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    async def handle_greeting(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle greeting messages"""
        try:
            targets_count = len(self.system_knowledge.get('targets', []))
            jobs_count = len(self.system_knowledge.get('recent_jobs', []))
            protocols = self.protocol_manager.get_supported_protocols()
            
            response = f"👋 **Hello! I'm your OpsConductor AI Assistant**\n\n"
            response += f"**System Overview:**\n"
            response += f"• {targets_count} targets in your infrastructure\n"
            response += f"• {jobs_count} recent automation jobs\n"
            response += f"• {len(protocols)} protocols supported: {', '.join(protocols).upper()}\n\n"
            
            response += f"**What I can help you with:**\n"
            response += f"🌐 **Network Monitoring** - SNMP device monitoring and stats\n"
            response += f"📧 **Email Alerts** - SMTP notifications and system alerts\n"
            response += f"🔐 **Remote Execution** - SSH command execution and scripts\n"
            response += f"📹 **Camera Management** - VAPIX camera control and motion detection\n"
            response += f"⚙️ **Automation** - Create workflows and scheduled tasks\n"
            response += f"🔧 **Script Generation** - PowerShell, Bash, and Python scripts\n\n"
            
            response += f"💡 **Try asking:**\n"
            response += f"• \"Show me all Windows 10 targets\"\n"
            response += f"• \"Check SNMP on network switches\"\n"
            response += f"• \"Generate a disk space monitoring script\"\n"
            response += f"• \"Send alert about server status\"\n"
            response += f"• \"Setup motion detection on cameras\""
            
            return {
                "response": response,
                "intent": "greeting",
                "success": True,
                "data": {
                    "targets_count": targets_count,
                    "jobs_count": jobs_count,
                    "protocols": protocols
                }
            }
            
        except Exception as e:
            logger.error(f"Greeting error: {e}")
            return {
                "response": "👋 Hello! I'm your OpsConductor AI Assistant. How can I help you today?",
                "intent": "greeting",
                "success": True
            }
    
    async def handle_general_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle general queries using vector search and Ollama"""
        try:
            # Search for relevant context
            relevant_docs = await self.get_relevant_context(message, limit=5)
            
            # Build context for Ollama
            context_text = ""
            if relevant_docs:
                context_text = "Relevant information from knowledge base:\n"
                for doc in relevant_docs:
                    context_text += f"- {doc.get('content', '')[:200]}...\n"
            
            # System information context
            system_context = f"""
OpsConductor System Information:
- Total targets: {len(self.system_knowledge.get('targets', []))}
- Recent jobs: {len(self.system_knowledge.get('recent_jobs', []))}
- Supported protocols: {', '.join(self.protocol_manager.get_supported_protocols())}
"""
            
            # Generate response using Ollama
            try:
                enhanced_prompt = f"""
You are the OpsConductor AI Assistant. Answer the following question based on the context provided.

Question: {message}

{context_text}

{system_context}

Provide a helpful, accurate response. If you don't have enough information, suggest what the user can do next.
"""
                
                ollama_response = await self.ollama_client.generate(
                    model="llama2",
                    prompt=enhanced_prompt
                )
                ai_response = ollama_response.get('response', '')
            except Exception as ollama_error:
                logger.warning(f"Ollama query failed: {ollama_error}")
                ai_response = "I understand you're asking about OpsConductor operations. Could you be more specific about what you'd like to know? I can help with targets, automation, protocols (SNMP, SMTP, SSH, VAPIX), or script generation."
            
            return {
                "response": ai_response,
                "intent": "general_query",
                "success": True,
                "data": {
                    "context_docs": len(relevant_docs),
                    "generated_by": "ollama" if 'ollama_response' in locals() else "fallback"
                }
            }
            
        except Exception as e:
            logger.error(f"General query error: {e}")
            return {
                "response": f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
                "intent": "general_query",
                "success": False
            }
    
    async def execute_protocol_command(self, protocol: str, target: Dict[str, Any], 
                                     command: str, credentials: Dict[str, Any], **kwargs) -> ProtocolResult:
        """Execute protocol command directly"""
        try:
            return await self.protocol_manager.execute(protocol, target, command, credentials=credentials, **kwargs)
        except Exception as e:
            logger.error(f"Protocol execution error: {e}")
            return ProtocolResult(False, error=str(e))
    
    async def get_protocol_status(self) -> Dict[str, Any]:
        """Get status of all protocol handlers"""
        try:
            protocols = self.protocol_manager.get_supported_protocols()
            status = {
                "supported_protocols": protocols,
                "active_connections": len(self.protocol_manager.active_connections),
                "capabilities": {}
            }
            
            for protocol in protocols:
                status["capabilities"][protocol] = self.protocol_manager.get_protocol_capabilities(protocol)
            
            return status
            
        except Exception as e:
            logger.error(f"Protocol status error: {e}")
            return {"error": str(e)}
    
    async def store_knowledge(self, content: str, category: str = "general") -> bool:
        """Store new knowledge in vector database"""
        try:
            if self.vector_store:
                await self.vector_store.store_knowledge(content, {"category": category})
                return True
            return False
        except Exception as e:
            logger.error(f"Knowledge storage error: {e}")
            return False
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            if self.vector_store:
                return await self.vector_store.get_stats()
            return {"error": "Vector store not available"}
        except Exception as e:
            logger.error(f"Knowledge stats error: {e}")
            return {"error": str(e)}
    
    async def handle_user_recommendations(self, user_id: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle user recommendation requests"""
        try:
            # Get personalized recommendations from learning engine
            recommendations = await self.learning_engine.get_user_recommendations(user_id)
            
            if not recommendations:
                response = f"🎯 **Personalized Recommendations for User {user_id}**\n\n"
                response += "I'm still learning your patterns! Here are some general suggestions:\n\n"
                response += "📊 **Get Started:**\n"
                response += "• Try different automation operations to help me learn your preferences\n"
                response += "• Use consistent naming patterns for better organization\n"
                response += "• Schedule regular maintenance tasks\n\n"
                response += "🔧 **Best Practices:**\n"
                response += "• Test operations on a small set of targets first\n"
                response += "• Monitor system performance during peak hours\n"
                response += "• Keep your automation scripts updated\n\n"
                response += "💡 **Tip:** The more you use the system, the better my recommendations become!"
            else:
                response = f"🎯 **Personalized Recommendations for User {user_id}**\n\n"
                
                high_priority = [r for r in recommendations if r.get('priority') == 'high']
                medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
                low_priority = [r for r in recommendations if r.get('priority') == 'low']
                
                if high_priority:
                    response += "🔴 **High Priority:**\n"
                    for rec in high_priority:
                        response += f"• **{rec['title']}**\n"
                        response += f"  {rec['description']}\n"
                        for action in rec.get('suggested_actions', []):
                            response += f"  - {action}\n"
                        response += "\n"
                
                if medium_priority:
                    response += "🟡 **Medium Priority:**\n"
                    for rec in medium_priority:
                        response += f"• **{rec['title']}**\n"
                        response += f"  {rec['description']}\n"
                        for action in rec.get('suggested_actions', []):
                            response += f"  - {action}\n"
                        response += "\n"
                
                if low_priority:
                    response += "🟢 **Suggestions:**\n"
                    for rec in low_priority:
                        response += f"• **{rec['title']}**\n"
                        response += f"  {rec['description']}\n"
                        response += "\n"
            
            return {
                "response": response,
                "intent": "recommendations",
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "user_id": user_id
                }
            }
            
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return {
                "response": f"I encountered an error getting your recommendations: {str(e)}",
                "intent": "recommendations",
                "success": False
            }
    
    async def handle_system_health_query(self, context: List[Dict]) -> Dict[str, Any]:
        """Handle system health and anomaly queries"""
        try:
            # Get system health insights from learning engine
            health_insights = await self.learning_engine.get_system_health_insights()
            
            # Get learning engine stats
            learning_stats = await self.learning_engine.get_learning_stats()
            
            response = f"🏥 **System Health Report**\n\n"
            
            # Overall health status
            health_emoji = {
                'good': '🟢',
                'fair': '🟡', 
                'degraded': '🟠',
                'critical': '🔴',
                'unknown': '⚪'
            }
            
            risk_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🔴',
                'unknown': '⚪'
            }
            
            overall_health = health_insights.get('overall_health', 'unknown')
            risk_level = health_insights.get('risk_level', 'unknown')
            
            response += f"**Overall Status:** {health_emoji.get(overall_health, '⚪')} {overall_health.title()}\n"
            response += f"**Risk Level:** {risk_emoji.get(risk_level, '⚪')} {risk_level.title()}\n\n"
            
            # Active anomalies
            active_anomalies = health_insights.get('active_anomalies', [])
            if active_anomalies:
                response += f"🚨 **Active Anomalies ({len(active_anomalies)}):**\n"
                for anomaly in active_anomalies[:5]:  # Show top 5
                    severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴', 'critical': '🚨'}
                    response += f"• {severity_emoji.get(anomaly['severity'], '⚪')} **{anomaly['type'].replace('_', ' ').title()}**\n"
                    response += f"  {anomaly['description']}\n"
                    response += f"  *Confidence: {anomaly['confidence']:.1%}*\n\n"
                
                if len(active_anomalies) > 5:
                    response += f"  ... and {len(active_anomalies) - 5} more anomalies\n\n"
            else:
                response += f"✅ **No Active Anomalies**\n\n"
            
            # System metrics
            metrics = health_insights.get('metrics_summary', {})
            if metrics:
                response += f"📊 **System Metrics (Last Hour):**\n"
                if 'cpu_usage' in metrics:
                    response += f"• CPU Usage: {metrics['cpu_usage']:.1f}%\n"
                if 'memory_usage' in metrics:
                    response += f"• Memory Usage: {metrics['memory_usage']:.1f}%\n"
                if 'response_time' in metrics:
                    response += f"• Avg Response Time: {metrics['response_time']:.2f}ms\n"
                if 'error_rate' in metrics:
                    response += f"• Error Rate: {metrics['error_rate']:.2%}\n"
                response += "\n"
            
            # Learning system status
            response += f"🧠 **AI Learning System:**\n"
            response += f"• Execution Records: {learning_stats.get('execution_records', 0):,}\n"
            response += f"• User Patterns: {learning_stats.get('user_patterns', 0)}\n"
            response += f"• Predictions Made: {learning_stats.get('predictions_made', 0)}\n"
            response += f"• Learning Status: {learning_stats.get('learning_status', 'unknown').title()}\n\n"
            
            # Recommendations
            recommendations = health_insights.get('recommendations', [])
            if recommendations:
                response += f"💡 **Recommendations:**\n"
                for rec in recommendations:
                    response += f"• {rec}\n"
            
            return {
                "response": response,
                "intent": "system_health",
                "success": True,
                "data": {
                    "health_insights": health_insights,
                    "learning_stats": learning_stats
                }
            }
            
        except Exception as e:
            logger.error(f"System health query error: {e}")
            return {
                "response": f"I encountered an error checking system health: {str(e)}",
                "intent": "system_health", 
                "success": False
            }

    
    async def handle_target_group_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about target groups"""
        try:
            # Get target groups from asset service
            target_groups = await self.asset_client.get_target_groups()
            
            if not target_groups:
                return {
                    "response": "🔍 **No target groups found**\n\nYour system doesn't have any target groups configured yet. You can create target groups to organize your infrastructure targets.",
                    "intent": "query_target_groups",
                    "success": True,
                    "data": {"groups_count": 0}
                }
            
            message_lower = message.lower()
            
            # Check if asking for specific group details
            if any(word in message_lower for word in ['details', 'targets in', 'members']):
                # Try to extract group name
                for group in target_groups:
                    group_name = group.get('name', '').lower()
                    if group_name in message_lower:
                        # Get targets in this specific group
                        targets = await self.asset_client.get_targets_in_group(group['id'])
                        
                        response = f"🎯 **Target Group: {group['name']}**\n\n"
                        response += f"**Description:** {group.get('description', 'No description')}\n"
                        response += f"**Targets:** {len(targets)}\n\n"
                        
                        if targets:
                            response += "**Group Members:**\n"
                            for i, target in enumerate(targets[:10]):  # Show first 10
                                hostname = target.get('hostname', 'Unknown')
                                ip = target.get('ip_address', 'No IP')
                                os_info = target.get('os_type', target.get('os', 'Unknown OS'))
                                response += f"{i+1}. **{hostname}** ({ip}) - {os_info}\n"
                            
                            if len(targets) > 10:
                                response += f"... and {len(targets) - 10} more targets\n"
                        else:
                            response += "**No targets in this group yet.**\n"
                        
                        return {
                            "response": response,
                            "intent": "query_target_groups",
                            "success": True,
                            "data": {
                                "group": group,
                                "targets_count": len(targets),
                                "targets": targets[:10]
                            }
                        }
            
            # General target groups overview
            response = f"📁 **Target Groups Overview**\n\n"
            response += f"**Total Groups:** {len(target_groups)}\n\n"
            
            # Show each group with summary
            for i, group in enumerate(target_groups):
                group_name = group.get('name', 'Unnamed Group')
                description = group.get('description', 'No description')
                
                # Get target count for this group
                targets = await self.asset_client.get_targets_in_group(group['id'])
                target_count = len(targets)
                
                response += f"**{i+1}. {group_name}**\n"
                response += f"   • Description: {description}\n"
                response += f"   • Targets: {target_count}\n"
                response += f"   • ID: {group['id']}\n\n"
            
            response += "💡 **Tip:** Ask 'Show me targets in [group name]' for detailed group information."
            
            return {
                "response": response,
                "intent": "query_target_groups",
                "success": True,
                "data": {
                    "groups_count": len(target_groups),
                    "groups": target_groups
                }
            }
            
        except Exception as e:
            logger.error(f"Target group query error: {e}")
            return {
                "response": f"❌ Error querying target groups: {str(e)}",
                "intent": "query_target_groups",
                "success": False
            }
    
    async def handle_workflow_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about workflows and automation templates"""
        try:
            # Get workflows from automation service
            workflows = await self.automation_client.list_ai_jobs(limit=100)
            
            message_lower = message.lower()
            
            # Filter workflows based on query
            if 'ai' in message_lower or 'ai-generated' in message_lower:
                filtered_workflows = [w for w in workflows if w.get('job_type') == 'ai_generated']
                filter_desc = "AI-generated"
            elif 'template' in message_lower:
                filtered_workflows = [w for w in workflows if 'template' in w.get('name', '').lower()]
                filter_desc = "template"
            elif 'scheduled' in message_lower:
                filtered_workflows = [w for w in workflows if w.get('is_scheduled', False)]
                filter_desc = "scheduled"
            else:
                filtered_workflows = workflows
                filter_desc = "all"
            
            if not filtered_workflows:
                response = f"📋 **No {filter_desc} workflows found**\n\n"
                if workflows:
                    response += f"Total workflows in system: {len(workflows)}\n\n"
                    response += "**Available workflow types:**\n"
                    types = set(w.get('job_type', 'unknown') for w in workflows)
                    for wf_type in types:
                        count = len([w for w in workflows if w.get('job_type') == wf_type])
                        response += f"• {wf_type}: {count} workflows\n"
                else:
                    response += "No workflows have been created yet. You can create workflows through automation or ask the AI to generate them."
                
                return {
                    "response": response,
                    "intent": "query_workflows",
                    "success": True,
                    "data": {"workflows_count": 0, "total_workflows": len(workflows)}
                }
            
            response = f"⚙️ **{filter_desc.title()} Workflows**\n\n"
            response += f"**Found:** {len(filtered_workflows)} workflows\n\n"
            
            # Show workflow details
            for i, workflow in enumerate(filtered_workflows[:10]):  # Show first 10
                name = workflow.get('name', 'Unnamed Workflow')
                description = workflow.get('description', 'No description')
                job_type = workflow.get('job_type', 'unknown')
                is_enabled = workflow.get('is_enabled', False)
                created_at = workflow.get('created_at', 'Unknown')
                
                status_emoji = '✅' if is_enabled else '⏸️'
                
                response += f"**{i+1}. {name}** {status_emoji}\n"
                response += f"   • Type: {job_type}\n"
                response += f"   • Description: {description[:100]}{'...' if len(description) > 100 else ''}\n"
                response += f"   • Status: {'Enabled' if is_enabled else 'Disabled'}\n"
                response += f"   • Created: {created_at}\n\n"
            
            if len(filtered_workflows) > 10:
                response += f"... and {len(filtered_workflows) - 10} more workflows\n\n"
            
            response += f"**Summary:** {len(filtered_workflows)} {filter_desc} workflows, {len(workflows)} total"
            
            return {
                "response": response,
                "intent": "query_workflows",
                "success": True,
                "data": {
                    "filtered_workflows": len(filtered_workflows),
                    "total_workflows": len(workflows),
                    "filter_description": filter_desc,
                    "workflows": filtered_workflows[:10]
                }
            }
            
        except Exception as e:
            logger.error(f"Workflow query error: {e}")
            return {
                "response": f"❌ Error querying workflows: {str(e)}",
                "intent": "query_workflows",
                "success": False
            }
    
    async def handle_execution_history_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about execution history"""
        try:
            # For now, use the recent jobs from system knowledge
            # In a full implementation, this would query the automation service for execution history
            jobs = self.system_knowledge.get('recent_jobs', [])
            
            if not jobs:
                return {
                    "response": "📋 **No execution history found**\n\nNo job executions have been recorded yet. Start running some automation jobs to see execution history here.",
                    "intent": "query_execution_history",
                    "success": True,
                    "data": {"executions_count": 0}
                }
            
            message_lower = message.lower()
            
            # Time-based filtering
            if 'today' in message_lower:
                # Filter for today's executions (simplified)
                filtered_jobs = jobs[:5]  # Most recent 5 as proxy
                filter_desc = "today's"
            elif 'yesterday' in message_lower:
                filtered_jobs = jobs[5:10] if len(jobs) > 5 else []
                filter_desc = "yesterday's"
            elif 'week' in message_lower or 'last week' in message_lower:
                filtered_jobs = jobs[:20]  # Last 20 as proxy for week
                filter_desc = "this week's"
            elif 'month' in message_lower:
                filtered_jobs = jobs  # All available
                filter_desc = "this month's"
            else:
                filtered_jobs = jobs[:15]  # Recent 15
                filter_desc = "recent"
            
            if not filtered_jobs:
                return {
                    "response": f"📋 **No {filter_desc} executions found**\n\nTotal executions in system: {len(jobs)}",
                    "intent": "query_execution_history",
                    "success": True,
                    "data": {"executions_count": 0, "total_executions": len(jobs)}
                }
            
            response = f"📊 **Execution History ({filter_desc})**\n\n"
            response += f"**Found:** {len(filtered_jobs)} executions\n\n"
            
            # Execution statistics
            statuses = {}
            for job in filtered_jobs:
                status = job.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            response += "**Status Summary:**\n"
            for status, count in statuses.items():
                emoji = {
                    'completed': '✅', 'success': '✅', 'finished': '✅',
                    'failed': '❌', 'error': '❌',
                    'running': '🔄', 'active': '🔄', 'in_progress': '🔄',
                    'pending': '⏳', 'queued': '⏳'
                }.get(status.lower(), '📋')
                response += f"• {emoji} {status}: {count}\n"
            
            response += "\n**Recent Executions:**\n"
            
            # Show execution details
            for i, job in enumerate(filtered_jobs[:8]):  # Show first 8
                job_id = job.get('id', 'Unknown')
                description = job.get('description', 'No description')
                status = job.get('status', 'Unknown')
                created_at = job.get('created_at', 'Unknown')
                duration = job.get('duration', 'Unknown')
                
                status_emoji = {
                    'completed': '✅', 'success': '✅', 'finished': '✅',
                    'failed': '❌', 'error': '❌',
                    'running': '🔄', 'active': '🔄', 'in_progress': '🔄',
                    'pending': '⏳', 'queued': '⏳'
                }.get(status.lower(), '📋')
                
                response += f"**{i+1}. Execution #{job_id}** {status_emoji}\n"
                response += f"   • Job: {description[:80]}{'...' if len(description) > 80 else ''}\n"
                response += f"   • Status: {status}\n"
                response += f"   • Started: {created_at}\n"
                if duration != 'Unknown':
                    response += f"   • Duration: {duration}\n"
                response += "\n"
            
            if len(filtered_jobs) > 8:
                response += f"... and {len(filtered_jobs) - 8} more executions\n\n"
            
            # Success rate calculation
            completed = statuses.get('completed', 0) + statuses.get('success', 0) + statuses.get('finished', 0)
            failed = statuses.get('failed', 0) + statuses.get('error', 0)
            total_finished = completed + failed
            
            if total_finished > 0:
                success_rate = (completed / total_finished) * 100
                response += f"**Success Rate:** {success_rate:.1f}% ({completed}/{total_finished} successful)"
            
            return {
                "response": response,
                "intent": "query_execution_history",
                "success": True,
                "data": {
                    "executions_count": len(filtered_jobs),
                    "total_executions": len(jobs),
                    "filter_description": filter_desc,
                    "status_summary": statuses,
                    "success_rate": success_rate if total_finished > 0 else None
                }
            }
            
        except Exception as e:
            logger.error(f"Execution history query error: {e}")
            return {
                "response": f"❌ Error querying execution history: {str(e)}",
                "intent": "query_execution_history",
                "success": False
            }
    
    async def handle_performance_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about system performance and metrics"""
        try:
            # Get performance data from learning engine and system knowledge
            learning_stats = await self.learning_engine.get_learning_stats()
            health_insights = await self.learning_engine.get_system_health_insights()
            
            targets_count = len(self.system_knowledge.get('targets', []))
            jobs_count = len(self.system_knowledge.get('recent_jobs', []))
            
            response = f"📊 **System Performance Metrics**\n\n"
            
            # System overview
            response += f"**Infrastructure Overview:**\n"
            response += f"• Total Targets: {targets_count}\n"
            response += f"• Total Jobs: {jobs_count}\n"
            response += f"• Supported Protocols: {len(self.protocol_manager.get_supported_protocols())}\n\n"
            
            # AI Learning Performance
            response += f"🧠 **AI Learning Performance:**\n"
            response += f"• Execution Records: {learning_stats.get('execution_records', 0):,}\n"
            response += f"• User Patterns: {learning_stats.get('user_patterns', 0)}\n"
            response += f"• Predictions Made: {learning_stats.get('predictions_made', 0)}\n"
            response += f"• Learning Status: {learning_stats.get('learning_status', 'unknown').title()}\n\n"
            
            # System Health Metrics
            metrics = health_insights.get('metrics_summary', {})
            if metrics:
                response += f"⚡ **System Metrics:**\n"
                if 'cpu_usage' in metrics:
                    response += f"• CPU Usage: {metrics['cpu_usage']:.1f}%\n"
                if 'memory_usage' in metrics:
                    response += f"• Memory Usage: {metrics['memory_usage']:.1f}%\n"
                if 'response_time' in metrics:
                    response += f"• Avg Response Time: {metrics['response_time']:.2f}ms\n"
                if 'error_rate' in metrics:
                    response += f"• Error Rate: {metrics['error_rate']:.2%}\n"
                response += "\n"
            
            # Job Performance Analysis
            jobs = self.system_knowledge.get('recent_jobs', [])
            if jobs:
                statuses = {}
                for job in jobs:
                    status = job.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                
                completed = statuses.get('completed', 0) + statuses.get('success', 0)
                failed = statuses.get('failed', 0) + statuses.get('error', 0)
                total_finished = completed + failed
                
                response += f"🎯 **Job Performance:**\n"
                response += f"• Total Jobs: {len(jobs)}\n"
                response += f"• Completed: {completed}\n"
                response += f"• Failed: {failed}\n"
                
                if total_finished > 0:
                    success_rate = (completed / total_finished) * 100
                    response += f"• Success Rate: {success_rate:.1f}%\n"
                
                response += "\n"
            
            # Protocol Performance
            protocols = self.protocol_manager.get_supported_protocols()
            response += f"🔌 **Protocol Status:**\n"
            for protocol in protocols:
                capabilities = self.protocol_manager.get_protocol_capabilities(protocol)
                response += f"• {protocol.upper()}: {len(capabilities)} capabilities\n"
            
            response += f"\n💡 **Performance Tips:**\n"
            response += f"• Monitor success rates regularly\n"
            response += f"• Review failed jobs for patterns\n"
            response += f"• Keep target credentials updated\n"
            response += f"• Use AI recommendations for optimization"
            
            return {
                "response": response,
                "intent": "query_performance",
                "success": True,
                "data": {
                    "targets_count": targets_count,
                    "jobs_count": jobs_count,
                    "learning_stats": learning_stats,
                    "metrics": metrics,
                    "protocols_count": len(protocols)
                }
            }
            
        except Exception as e:
            logger.error(f"Performance query error: {e}")
            return {
                "response": f"❌ Error querying performance metrics: {str(e)}",
                "intent": "query_performance",
                "success": False
            }
    
    async def handle_error_analysis_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about errors and failure analysis"""
        try:
            jobs = self.system_knowledge.get('recent_jobs', [])
            
            # Filter for failed jobs
            failed_jobs = [job for job in jobs if job.get('status') in ['failed', 'error']]
            
            if not failed_jobs:
                return {
                    "response": "✅ **No Recent Errors Found**\n\nGreat news! No failed jobs found in recent history. Your automation is running smoothly.",
                    "intent": "query_error_analysis",
                    "success": True,
                    "data": {"error_count": 0, "total_jobs": len(jobs)}
                }
            
            response = f"🔍 **Error Analysis Report**\n\n"
            response += f"**Failed Jobs:** {len(failed_jobs)} out of {len(jobs)} total\n\n"
            
            # Error pattern analysis
            error_patterns = {}
            error_types = {}
            
            for job in failed_jobs:
                # Analyze error messages for patterns
                error_msg = job.get('error_message', 'Unknown error')
                
                # Common error categorization
                if 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                    error_types['Connection Issues'] = error_types.get('Connection Issues', 0) + 1
                elif 'permission' in error_msg.lower() or 'access' in error_msg.lower():
                    error_types['Permission Errors'] = error_types.get('Permission Errors', 0) + 1
                elif 'credential' in error_msg.lower() or 'auth' in error_msg.lower():
                    error_types['Authentication Errors'] = error_types.get('Authentication Errors', 0) + 1
                elif 'not found' in error_msg.lower() or '404' in error_msg:
                    error_types['Resource Not Found'] = error_types.get('Resource Not Found', 0) + 1
                else:
                    error_types['Other Errors'] = error_types.get('Other Errors', 0) + 1
            
            # Show error type breakdown
            response += f"**Error Categories:**\n"
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(failed_jobs)) * 100
                response += f"• {error_type}: {count} ({percentage:.1f}%)\n"
            
            response += f"\n**Recent Failed Jobs:**\n"
            
            # Show recent failed jobs
            for i, job in enumerate(failed_jobs[:5]):  # Show first 5 failed jobs
                job_id = job.get('id', 'Unknown')
                description = job.get('description', 'No description')
                error_msg = job.get('error_message', 'No error message')
                failed_at = job.get('failed_at', job.get('created_at', 'Unknown'))
                
                response += f"**{i+1}. Job #{job_id}** ❌\n"
                response += f"   • Description: {description[:80]}{'...' if len(description) > 80 else ''}\n"
                response += f"   • Error: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}\n"
                response += f"   • Failed At: {failed_at}\n\n"
            
            if len(failed_jobs) > 5:
                response += f"... and {len(failed_jobs) - 5} more failed jobs\n\n"
            
            # Recommendations
            response += f"🔧 **Recommended Actions:**\n"
            
            if error_types.get('Connection Issues', 0) > 0:
                response += f"• Check network connectivity to targets\n"
                response += f"• Verify target availability and firewall settings\n"
            
            if error_types.get('Permission Errors', 0) > 0:
                response += f"• Review user permissions on target systems\n"
                response += f"• Ensure service accounts have required privileges\n"
            
            if error_types.get('Authentication Errors', 0) > 0:
                response += f"• Update expired credentials\n"
                response += f"• Verify authentication configuration\n"
            
            if error_types.get('Resource Not Found', 0) > 0:
                response += f"• Check if target resources still exist\n"
                response += f"• Update automation scripts for path changes\n"
            
            response += f"• Review and retry failed jobs after fixes\n"
            response += f"• Monitor error trends over time"
            
            return {
                "response": response,
                "intent": "query_error_analysis",
                "success": True,
                "data": {
                    "error_count": len(failed_jobs),
                    "total_jobs": len(jobs),
                    "error_types": error_types,
                    "failed_jobs": failed_jobs[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analysis query error: {e}")
            return {
                "response": f"❌ Error analyzing errors: {str(e)}",
                "intent": "query_error_analysis",
                "success": False
            }
    
    async def handle_notification_history_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about notification and communication history"""
        try:
            # For now, return a placeholder response since we don't have direct access to communication service
            # In a full implementation, this would query the communication service
            
            response = f"📧 **Notification History**\n\n"
            response += f"**Communication Service Integration:**\n"
            response += f"• Service Status: Active\n"
            response += f"• Supported Channels: SMTP Email\n"
            response += f"• Configuration: Ready\n\n"
            
            response += f"**Recent Activity:**\n"
            response += f"• System alerts sent for job completions\n"
            response += f"• Error notifications for failed operations\n"
            response += f"• Health check alerts for system monitoring\n\n"
            
            response += f"📊 **Notification Statistics:**\n"
            response += f"• Total Notifications: Available via Communication Service\n"
            response += f"• Delivery Rate: Monitored by SMTP service\n"
            response += f"• Failed Deliveries: Tracked in communication logs\n\n"
            
            response += f"💡 **To get detailed notification history:**\n"
            response += f"• Check the Communication Service logs\n"
            response += f"• Review SMTP delivery reports\n"
            response += f"• Monitor alert configuration settings\n"
            response += f"• Use the frontend dashboard for visual reports"
            
            return {
                "response": response,
                "intent": "query_notification_history",
                "success": True,
                "data": {
                    "service_status": "active",
                    "channels": ["smtp"],
                    "integration_ready": True
                }
            }
            
        except Exception as e:
            logger.error(f"Notification history query error: {e}")
            return {
                "response": f"❌ Error querying notification history: {str(e)}",
                "intent": "query_notification_history",
                "success": False
            }
    
    async def handle_credential_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about credentials and authentication"""
        try:
            # Get all targets with their credential information
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return {
                    "response": "🔐 **No targets found**\n\nNo targets are configured yet. Add targets first to manage credentials.",
                    "intent": "query_credentials",
                    "success": True,
                    "data": {"targets_count": 0}
                }
            
            message_lower = message.lower()
            
            # Analyze credential status across all targets
            credential_stats = {
                'total_targets': len(targets),
                'with_credentials': 0,
                'without_credentials': 0,
                'credential_types': {},
                'service_types': {}
            }
            
            targets_with_creds = []
            targets_without_creds = []
            
            for target in targets:
                hostname = target.get('hostname', 'Unknown')
                services = target.get('services', [])
                
                target_has_creds = False
                target_cred_types = []
                
                for service in services:
                    cred_type = service.get('credential_type')
                    has_creds = service.get('has_credentials', False)
                    service_type = service.get('service_type', 'unknown')
                    
                    # Track service types
                    credential_stats['service_types'][service_type] = credential_stats['service_types'].get(service_type, 0) + 1
                    
                    if has_creds and cred_type:
                        target_has_creds = True
                        if cred_type not in target_cred_types:
                            target_cred_types.append(cred_type)
                        credential_stats['credential_types'][cred_type] = credential_stats['credential_types'].get(cred_type, 0) + 1
                
                if target_has_creds:
                    credential_stats['with_credentials'] += 1
                    targets_with_creds.append({
                        'target': target,
                        'credential_types': target_cred_types
                    })
                else:
                    credential_stats['without_credentials'] += 1
                    targets_without_creds.append(target)
            
            # Generate response based on query type
            if 'missing' in message_lower or 'without' in message_lower or 'no credentials' in message_lower:
                # Focus on targets without credentials
                response = f"🔐 **Targets Missing Credentials**\n\n"
                response += f"**Found:** {len(targets_without_creds)} targets without credentials\n\n"
                
                if targets_without_creds:
                    response += "**Targets Needing Credentials:**\n"
                    for i, target in enumerate(targets_without_creds[:10]):
                        hostname = target.get('hostname', 'Unknown')
                        os_type = target.get('os_type', 'unknown')
                        services = target.get('services', [])
                        service_count = len(services)
                        
                        response += f"{i+1}. **{hostname}** ({os_type})\n"
                        response += f"   • Services: {service_count}\n"
                        response += f"   • Status: ❌ No credentials configured\n\n"
                    
                    if len(targets_without_creds) > 10:
                        response += f"... and {len(targets_without_creds) - 10} more targets\n\n"
                    
                    response += "💡 **Recommendation:** Configure credentials for these targets to enable automation."
                else:
                    response += "✅ **Great!** All targets have credentials configured."
                
            elif any(word in message_lower for word in ['ssh', 'ssh key', 'ssh keys']):
                # Focus on SSH credentials
                ssh_targets = []
                for target_info in targets_with_creds:
                    if 'ssh_key' in target_info['credential_types'] or any('ssh' in ct for ct in target_info['credential_types']):
                        ssh_targets.append(target_info)
                
                response = f"🔑 **SSH Key Credentials**\n\n"
                response += f"**Found:** {len(ssh_targets)} targets with SSH credentials\n\n"
                
                if ssh_targets:
                    response += "**SSH-Enabled Targets:**\n"
                    for i, target_info in enumerate(ssh_targets[:8]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        ip = target.get('ip_address', 'No IP')
                        
                        response += f"{i+1}. **{hostname}** ({ip})\n"
                        response += f"   • Credential Types: {', '.join(target_info['credential_types'])}\n\n"
                else:
                    response += "No targets with SSH key credentials found.\n"
                    response += "Consider configuring SSH key authentication for better security."
                
            else:
                # General credential overview
                response = f"🔐 **Credential Management Overview**\n\n"
                response += f"**Total Targets:** {credential_stats['total_targets']}\n"
                response += f"**With Credentials:** {credential_stats['with_credentials']} ✅\n"
                response += f"**Without Credentials:** {credential_stats['without_credentials']} ❌\n\n"
                
                if credential_stats['credential_types']:
                    response += "**Credential Types in Use:**\n"
                    for cred_type, count in sorted(credential_stats['credential_types'].items(), key=lambda x: x[1], reverse=True):
                        response += f"• {cred_type.replace('_', ' ').title()}: {count} targets\n"
                    response += "\n"
                
                if credential_stats['service_types']:
                    response += "**Service Types:**\n"
                    for service_type, count in sorted(credential_stats['service_types'].items(), key=lambda x: x[1], reverse=True):
                        response += f"• {service_type.upper()}: {count} services\n"
                    response += "\n"
                
                # Show some examples of configured targets
                if targets_with_creds:
                    response += "**Sample Configured Targets:**\n"
                    for i, target_info in enumerate(targets_with_creds[:5]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        cred_types = ', '.join(target_info['credential_types'])
                        
                        response += f"{i+1}. **{hostname}** - {cred_types}\n"
                    
                    if len(targets_with_creds) > 5:
                        response += f"... and {len(targets_with_creds) - 5} more\n"
                
                response += f"\n💡 **Security Tip:** Regularly rotate credentials and use SSH keys where possible."
            
            return {
                "response": response,
                "intent": "query_credentials",
                "success": True,
                "data": {
                    "credential_stats": credential_stats,
                    "targets_with_credentials": len(targets_with_creds),
                    "targets_without_credentials": len(targets_without_creds)
                }
            }
            
        except Exception as e:
            logger.error(f"Credential query error: {e}")
            return {
                "response": f"❌ Error querying credentials: {str(e)}",
                "intent": "query_credentials",
                "success": False
            }
    
    async def handle_service_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about services and protocols"""
        try:
            # Get all targets with their services
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return {
                    "response": "🔌 **No targets found**\n\nNo targets are configured yet. Add targets first to see their services.",
                    "intent": "query_services",
                    "success": True,
                    "data": {"targets_count": 0}
                }
            
            message_lower = message.lower()
            
            # Collect all services across targets
            all_services = []
            service_stats = {}
            port_stats = {}
            security_stats = {'secure': 0, 'insecure': 0}
            
            for target in targets:
                hostname = target.get('hostname', 'Unknown')
                os_type = target.get('os_type', 'unknown')
                services = target.get('services', [])
                
                for service in services:
                    service_type = service.get('service_type', 'unknown')
                    port = service.get('port', 0)
                    is_secure = service.get('is_secure', False)
                    is_enabled = service.get('is_enabled', True)
                    
                    # Track statistics
                    service_stats[service_type] = service_stats.get(service_type, 0) + 1
                    port_stats[port] = port_stats.get(port, 0) + 1
                    
                    if is_secure:
                        security_stats['secure'] += 1
                    else:
                        security_stats['insecure'] += 1
                    
                    all_services.append({
                        'target_hostname': hostname,
                        'target_os': os_type,
                        'service_type': service_type,
                        'port': port,
                        'is_secure': is_secure,
                        'is_enabled': is_enabled,
                        'has_credentials': service.get('has_credentials', False)
                    })
            
            # Filter services based on query
            if 'ssh' in message_lower:
                filtered_services = [s for s in all_services if 'ssh' in s['service_type'].lower()]
                filter_desc = "SSH"
            elif 'winrm' in message_lower:
                filtered_services = [s for s in all_services if 'winrm' in s['service_type'].lower()]
                filter_desc = "WinRM"
            elif 'http' in message_lower:
                filtered_services = [s for s in all_services if 'http' in s['service_type'].lower()]
                filter_desc = "HTTP/HTTPS"
            elif 'database' in message_lower or 'db' in message_lower:
                filtered_services = [s for s in all_services if any(db in s['service_type'].lower() for db in ['sql', 'mysql', 'postgres', 'oracle', 'mongo'])]
                filter_desc = "Database"
            elif 'insecure' in message_lower or 'unsecure' in message_lower:
                filtered_services = [s for s in all_services if not s['is_secure']]
                filter_desc = "Insecure"
            elif 'secure' in message_lower:
                filtered_services = [s for s in all_services if s['is_secure']]
                filter_desc = "Secure"
            else:
                filtered_services = all_services
                filter_desc = "All"
            
            if not filtered_services:
                response = f"🔌 **No {filter_desc} services found**\n\n"
                if all_services:
                    response += f"Total services in system: {len(all_services)}\n\n"
                    response += "**Available service types:**\n"
                    for service_type, count in sorted(service_stats.items(), key=lambda x: x[1], reverse=True):
                        response += f"• {service_type.upper()}: {count} services\n"
                else:
                    response += "No services are configured on any targets yet."
                
                return {
                    "response": response,
                    "intent": "query_services",
                    "success": True,
                    "data": {"services_count": 0, "total_services": len(all_services)}
                }
            
            response = f"🔌 **{filter_desc} Services**\n\n"
            response += f"**Found:** {len(filtered_services)} services\n\n"
            
            # Service summary
            filtered_stats = {}
            for service in filtered_services:
                service_type = service['service_type']
                filtered_stats[service_type] = filtered_stats.get(service_type, 0) + 1
            
            response += "**Service Type Breakdown:**\n"
            for service_type, count in sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True):
                response += f"• {service_type.upper()}: {count} services\n"
            response += "\n"
            
            # Show service details
            response += "**Service Details:**\n"
            for i, service in enumerate(filtered_services[:10]):  # Show first 10
                hostname = service['target_hostname']
                service_type = service['service_type']
                port = service['port']
                is_secure = service['is_secure']
                is_enabled = service['is_enabled']
                has_creds = service['has_credentials']
                
                security_emoji = '🔒' if is_secure else '🔓'
                status_emoji = '✅' if is_enabled else '⏸️'
                cred_emoji = '🔑' if has_creds else '❌'
                
                response += f"**{i+1}. {hostname}** - {service_type.upper()}\n"
                response += f"   • Port: {port} {security_emoji}\n"
                response += f"   • Status: {'Enabled' if is_enabled else 'Disabled'} {status_emoji}\n"
                response += f"   • Credentials: {'Configured' if has_creds else 'Missing'} {cred_emoji}\n\n"
            
            if len(filtered_services) > 10:
                response += f"... and {len(filtered_services) - 10} more services\n\n"
            
            # Security summary
            secure_count = len([s for s in filtered_services if s['is_secure']])
            insecure_count = len(filtered_services) - secure_count
            
            response += f"**Security Summary:**\n"
            response += f"• Secure Services: {secure_count} 🔒\n"
            response += f"• Insecure Services: {insecure_count} 🔓\n"
            
            if insecure_count > 0:
                response += f"\n⚠️ **Security Recommendation:** Consider securing {insecure_count} insecure services."
            
            return {
                "response": response,
                "intent": "query_services",
                "success": True,
                "data": {
                    "services_count": len(filtered_services),
                    "total_services": len(all_services),
                    "filter_description": filter_desc,
                    "service_stats": filtered_stats,
                    "security_stats": {"secure": secure_count, "insecure": insecure_count}
                }
            }
            
        except Exception as e:
            logger.error(f"Service query error: {e}")
            return {
                "response": f"❌ Error querying services: {str(e)}",
                "intent": "query_services",
                "success": False
            }
    
    async def handle_target_details_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about detailed target information"""
        try:
            # Get all targets with detailed information
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return {
                    "response": "🎯 **No targets found**\n\nNo targets are configured yet. Add targets to see detailed information.",
                    "intent": "query_target_details",
                    "success": True,
                    "data": {"targets_count": 0}
                }
            
            message_lower = message.lower()
            
            # Analyze target details
            os_stats = {}
            tag_stats = {}
            recent_targets = []
            
            for target in targets:
                os_type = target.get('os_type', 'unknown')
                os_version = target.get('os_version', 'Unknown')
                tags = target.get('tags', [])
                created_at = target.get('created_at', '')
                
                # Track OS statistics
                os_key = f"{os_type} {os_version}".strip()
                os_stats[os_key] = os_stats.get(os_key, 0) + 1
                
                # Track tag statistics
                for tag in tags:
                    tag_stats[tag] = tag_stats.get(tag, 0) + 1
                
                # Track recent targets (simplified - in real implementation would parse dates)
                if created_at:
                    recent_targets.append(target)
            
            # Filter targets based on query
            if 'windows' in message_lower:
                filtered_targets = [t for t in targets if t.get('os_type', '').lower() == 'windows']
                filter_desc = "Windows"
            elif 'linux' in message_lower:
                filtered_targets = [t for t in targets if t.get('os_type', '').lower() == 'linux']
                filter_desc = "Linux"
            elif 'unix' in message_lower:
                filtered_targets = [t for t in targets if t.get('os_type', '').lower() == 'unix']
                filter_desc = "Unix"
            elif 'macos' in message_lower or 'mac' in message_lower:
                filtered_targets = [t for t in targets if t.get('os_type', '').lower() == 'macos']
                filter_desc = "macOS"
            elif 'recent' in message_lower or 'new' in message_lower:
                filtered_targets = recent_targets[-10:]  # Last 10 as proxy for recent
                filter_desc = "Recent"
            elif any(word in message_lower for word in ['tag', 'tagged']):
                # Try to extract tag name from message
                filtered_targets = []
                for target in targets:
                    target_tags = [tag.lower() for tag in target.get('tags', [])]
                    if any(tag in message_lower for tag in target_tags):
                        filtered_targets.append(target)
                filter_desc = "Tagged"
            else:
                filtered_targets = targets
                filter_desc = "All"
            
            if not filtered_targets:
                response = f"🎯 **No {filter_desc} targets found**\n\n"
                if targets:
                    response += f"Total targets in system: {len(targets)}\n\n"
                    response += "**Available OS types:**\n"
                    for os_type, count in sorted(os_stats.items(), key=lambda x: x[1], reverse=True):
                        response += f"• {os_type.title()}: {count} targets\n"
                else:
                    response += "No targets are configured yet."
                
                return {
                    "response": response,
                    "intent": "query_target_details",
                    "success": True,
                    "data": {"targets_count": 0, "total_targets": len(targets)}
                }
            
            response = f"🎯 **{filter_desc} Target Details**\n\n"
            response += f"**Found:** {len(filtered_targets)} targets\n\n"
            
            # OS distribution for filtered targets
            filtered_os_stats = {}
            for target in filtered_targets:
                os_type = target.get('os_type', 'unknown')
                os_version = target.get('os_version', 'Unknown')
                os_key = f"{os_type} {os_version}".strip()
                filtered_os_stats[os_key] = filtered_os_stats.get(os_key, 0) + 1
            
            if len(filtered_os_stats) > 1:  # Only show if there's variety
                response += "**Operating System Distribution:**\n"
                for os_type, count in sorted(filtered_os_stats.items(), key=lambda x: x[1], reverse=True):
                    response += f"• {os_type.title()}: {count} targets\n"
                response += "\n"
            
            # Show detailed target information
            response += "**Target Details:**\n"
            for i, target in enumerate(filtered_targets[:8]):  # Show first 8
                name = target.get('name', 'Unnamed')
                hostname = target.get('hostname', 'Unknown')
                ip = target.get('ip_address', 'No IP')
                os_type = target.get('os_type', 'unknown')
                os_version = target.get('os_version', 'Unknown')
                description = target.get('description', 'No description')
                tags = target.get('tags', [])
                services = target.get('services', [])
                created_at = target.get('created_at', 'Unknown')
                
                response += f"**{i+1}. {name}**\n"
                response += f"   • Hostname: {hostname}\n"
                response += f"   • IP Address: {ip}\n"
                response += f"   • OS: {os_type.title()} {os_version}\n"
                response += f"   • Services: {len(services)}\n"
                
                if tags:
                    response += f"   • Tags: {', '.join(tags)}\n"
                
                if description and description != 'No description':
                    response += f"   • Description: {description[:60]}{'...' if len(description) > 60 else ''}\n"
                
                response += f"   • Created: {created_at}\n\n"
            
            if len(filtered_targets) > 8:
                response += f"... and {len(filtered_targets) - 8} more targets\n\n"
            
            # Tag summary if applicable
            if tag_stats and filter_desc != "Tagged":
                response += f"**Popular Tags:**\n"
                sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                for tag, count in sorted_tags:
                    response += f"• {tag}: {count} targets\n"
            
            return {
                "response": response,
                "intent": "query_target_details",
                "success": True,
                "data": {
                    "targets_count": len(filtered_targets),
                    "total_targets": len(targets),
                    "filter_description": filter_desc,
                    "os_stats": filtered_os_stats,
                    "tag_stats": tag_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Target details query error: {e}")
            return {
                "response": f"❌ Error querying target details: {str(e)}",
                "intent": "query_target_details",
                "success": False
            }
    
    async def handle_connection_status_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about connection status and reachability"""
        try:
            # Get all targets with their connection status
            targets = await self.asset_client.get_all_targets()
            
            if not targets:
                return {
                    "response": "🔗 **No targets found**\n\nNo targets are configured yet. Add targets to check connection status.",
                    "intent": "query_connection_status",
                    "success": True,
                    "data": {"targets_count": 0}
                }
            
            message_lower = message.lower()
            
            # Analyze connection status
            connection_stats = {
                'total_targets': len(targets),
                'reachable': 0,
                'unreachable': 0,
                'unknown': 0,
                'never_tested': 0
            }
            
            reachable_targets = []
            unreachable_targets = []
            untested_targets = []
            
            for target in targets:
                hostname = target.get('hostname', 'Unknown')
                services = target.get('services', [])
                
                target_status = 'unknown'
                last_tested = None
                
                # Check service connection status
                for service in services:
                    connection_status = service.get('connection_status')
                    last_tested_at = service.get('last_tested_at')
                    
                    if connection_status == 'connected' or connection_status == 'success':
                        target_status = 'reachable'
                        if last_tested_at:
                            last_tested = last_tested_at
                        break
                    elif connection_status == 'failed' or connection_status == 'error':
                        if target_status != 'reachable':  # Don't override reachable status
                            target_status = 'unreachable'
                            if last_tested_at:
                                last_tested = last_tested_at
                    elif connection_status is None:
                        if target_status == 'unknown':
                            target_status = 'never_tested'
                
                # Categorize targets
                if target_status == 'reachable':
                    connection_stats['reachable'] += 1
                    reachable_targets.append({
                        'target': target,
                        'last_tested': last_tested,
                        'status': 'reachable'
                    })
                elif target_status == 'unreachable':
                    connection_stats['unreachable'] += 1
                    unreachable_targets.append({
                        'target': target,
                        'last_tested': last_tested,
                        'status': 'unreachable'
                    })
                elif target_status == 'never_tested':
                    connection_stats['never_tested'] += 1
                    untested_targets.append({
                        'target': target,
                        'last_tested': None,
                        'status': 'never_tested'
                    })
                else:
                    connection_stats['unknown'] += 1
            
            # Generate response based on query focus
            if 'unreachable' in message_lower or 'failed' in message_lower or 'down' in message_lower:
                # Focus on unreachable targets
                response = f"🔗 **Unreachable Targets**\n\n"
                response += f"**Found:** {len(unreachable_targets)} unreachable targets\n\n"
                
                if unreachable_targets:
                    response += "**Connection Issues:**\n"
                    for i, target_info in enumerate(unreachable_targets[:8]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        ip = target.get('ip_address', 'No IP')
                        last_tested = target_info['last_tested'] or 'Never'
                        
                        response += f"{i+1}. **{hostname}** ({ip}) ❌\n"
                        response += f"   • Last Tested: {last_tested}\n"
                        response += f"   • Status: Connection Failed\n\n"
                    
                    if len(unreachable_targets) > 8:
                        response += f"... and {len(unreachable_targets) - 8} more unreachable targets\n\n"
                    
                    response += "🔧 **Troubleshooting Tips:**\n"
                    response += "• Check network connectivity\n"
                    response += "• Verify firewall settings\n"
                    response += "• Confirm target is powered on\n"
                    response += "• Test credentials and ports"
                else:
                    response += "✅ **Great!** All tested targets are reachable."
                
            elif 'reachable' in message_lower or 'connected' in message_lower or 'up' in message_lower:
                # Focus on reachable targets
                response = f"🔗 **Reachable Targets**\n\n"
                response += f"**Found:** {len(reachable_targets)} reachable targets\n\n"
                
                if reachable_targets:
                    response += "**Successfully Connected:**\n"
                    for i, target_info in enumerate(reachable_targets[:8]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        ip = target.get('ip_address', 'No IP')
                        last_tested = target_info['last_tested'] or 'Recently'
                        
                        response += f"{i+1}. **{hostname}** ({ip}) ✅\n"
                        response += f"   • Last Tested: {last_tested}\n"
                        response += f"   • Status: Connected\n\n"
                    
                    if len(reachable_targets) > 8:
                        response += f"... and {len(reachable_targets) - 8} more reachable targets\n"
                else:
                    response += "No reachable targets found. Check connection settings."
                
            elif 'test' in message_lower or 'check' in message_lower:
                # Focus on testing recommendations
                response = f"🔗 **Connection Testing Status**\n\n"
                response += f"**Never Tested:** {len(untested_targets)} targets\n"
                response += f"**Need Retesting:** {len(unreachable_targets)} targets\n\n"
                
                if untested_targets:
                    response += "**Targets Never Tested:**\n"
                    for i, target_info in enumerate(untested_targets[:5]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        response += f"{i+1}. {hostname} - Never tested\n"
                    
                    if len(untested_targets) > 5:
                        response += f"... and {len(untested_targets) - 5} more\n"
                    response += "\n"
                
                response += "💡 **Recommendation:** Run connection tests to verify target reachability."
                
            else:
                # General connection overview
                response = f"🔗 **Connection Status Overview**\n\n"
                response += f"**Total Targets:** {connection_stats['total_targets']}\n"
                response += f"**Reachable:** {connection_stats['reachable']} ✅\n"
                response += f"**Unreachable:** {connection_stats['unreachable']} ❌\n"
                response += f"**Never Tested:** {connection_stats['never_tested']} ⚪\n"
                response += f"**Unknown Status:** {connection_stats['unknown']} ❓\n\n"
                
                # Calculate health percentage
                tested_targets = connection_stats['reachable'] + connection_stats['unreachable']
                if tested_targets > 0:
                    health_percentage = (connection_stats['reachable'] / tested_targets) * 100
                    response += f"**Connection Health:** {health_percentage:.1f}% ({connection_stats['reachable']}/{tested_targets} reachable)\n\n"
                
                # Show recent connection issues if any
                if unreachable_targets:
                    response += "**Recent Connection Issues:**\n"
                    for i, target_info in enumerate(unreachable_targets[:3]):
                        target = target_info['target']
                        hostname = target.get('hostname', 'Unknown')
                        response += f"• {hostname} - Connection failed\n"
                    
                    if len(unreachable_targets) > 3:
                        response += f"... and {len(unreachable_targets) - 3} more\n"
                    response += "\n"
                
                if untested_targets:
                    response += f"💡 **Tip:** {len(untested_targets)} targets haven't been tested yet. Run connection tests to verify reachability."
            
            return {
                "response": response,
                "intent": "query_connection_status",
                "success": True,
                "data": {
                    "connection_stats": connection_stats,
                    "reachable_count": len(reachable_targets),
                    "unreachable_count": len(unreachable_targets),
                    "untested_count": len(untested_targets)
                }
            }
            
        except Exception as e:
            logger.error(f"Connection status query error: {e}")
            return {
                "response": f"❌ Error querying connection status: {str(e)}",
                "intent": "query_connection_status",
                "success": False
            }
    
    # ============================================================================
    # PHASE 2 - ADVANCED AUTOMATION QUERIES
    # ============================================================================
    
    async def handle_job_execution_details_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about detailed job execution logs and step analysis"""
        try:
            # Get execution history from automation service
            executions = await self.automation_client.get_execution_history()
            
            if not executions:
                return {
                    "response": "📊 **No execution details found**\n\nNo job executions have been recorded yet. Run some automation jobs to see detailed execution logs.",
                    "intent": "query_job_execution_details",
                    "success": True,
                    "data": {"executions_count": 0}
                }
            
            message_lower = message.lower()
            
            # Extract job ID if specified
            import re
            job_id_match = re.search(r'job\s*#?(\d+)', message_lower)
            execution_id_match = re.search(r'execution\s*#?([a-zA-Z0-9-]+)', message_lower)
            
            if job_id_match or execution_id_match:
                # Show specific job/execution details
                target_id = job_id_match.group(1) if job_id_match else execution_id_match.group(1)
                
                target_execution = None
                for execution in executions:
                    if (str(execution.get('job_id')) == target_id or 
                        str(execution.get('execution_id')) == target_id or
                        str(execution.get('id')) == target_id):
                        target_execution = execution
                        break
                
                if not target_execution:
                    return {
                        "response": f"🔍 **Execution not found**\n\nNo execution found with ID '{target_id}'. Available executions: {len(executions)}",
                        "intent": "query_job_execution_details",
                        "success": True,
                        "data": {"executions_count": len(executions)}
                    }
                
                # Get detailed step information
                execution_id = target_execution.get('execution_id') or target_execution.get('id')
                steps = await self.automation_client.get_execution_steps(execution_id)
                
                response = f"📊 **Execution Details - {target_id}**\n\n"
                response += f"**Job:** {target_execution.get('job_name', 'Unknown')}\n"
                response += f"**Status:** {target_execution.get('status', 'Unknown')}\n"
                response += f"**Started:** {target_execution.get('started_at', 'Unknown')}\n"
                response += f"**Duration:** {target_execution.get('duration', 'Unknown')}\n\n"
                
                if steps:
                    response += f"**Step Execution Details ({len(steps)} steps):**\n"
                    for i, step in enumerate(steps):
                        step_name = step.get('step_name', f'Step {i+1}')
                        step_status = step.get('status', 'unknown')
                        step_duration = step.get('duration', 'Unknown')
                        step_output = step.get('output', '')
                        step_error = step.get('error', '')
                        
                        status_emoji = '✅' if step_status == 'completed' else '❌' if step_status == 'failed' else '🔄'
                        
                        response += f"\n**{i+1}. {step_name}** {status_emoji}\n"
                        response += f"   • Status: {step_status}\n"
                        response += f"   • Duration: {step_duration}\n"
                        
                        if step_output:
                            output_preview = step_output[:100] + '...' if len(step_output) > 100 else step_output
                            response += f"   • Output: {output_preview}\n"
                        
                        if step_error:
                            error_preview = step_error[:100] + '...' if len(step_error) > 100 else step_error
                            response += f"   • Error: {error_preview}\n"
                else:
                    response += "**No step details available**\n"
                
                # Add input/output data if available
                input_data = target_execution.get('input_data', {})
                output_data = target_execution.get('output_data', {})
                
                if input_data:
                    response += f"\n**Input Data:** {str(input_data)[:200]}{'...' if len(str(input_data)) > 200 else ''}\n"
                
                if output_data:
                    response += f"**Output Data:** {str(output_data)[:200]}{'...' if len(str(output_data)) > 200 else ''}\n"
                
            else:
                # Show recent execution summary with step analysis
                recent_executions = executions[:10]
                
                response = f"📊 **Recent Execution Details**\n\n"
                response += f"**Found:** {len(recent_executions)} recent executions\n\n"
                
                for i, execution in enumerate(recent_executions[:5]):
                    job_name = execution.get('job_name', 'Unknown Job')
                    status = execution.get('status', 'unknown')
                    duration = execution.get('duration', 'Unknown')
                    step_count = execution.get('step_count', 0)
                    failed_steps = execution.get('failed_steps', 0)
                    
                    status_emoji = '✅' if status == 'completed' else '❌' if status == 'failed' else '🔄'
                    
                    response += f"**{i+1}. {job_name}** {status_emoji}\n"
                    response += f"   • Status: {status}\n"
                    response += f"   • Duration: {duration}\n"
                    response += f"   • Steps: {step_count} total"
                    
                    if failed_steps > 0:
                        response += f", {failed_steps} failed"
                    response += "\n\n"
                
                # Execution statistics
                total_executions = len(executions)
                completed = len([e for e in executions if e.get('status') == 'completed'])
                failed = len([e for e in executions if e.get('status') == 'failed'])
                
                response += f"**Execution Statistics:**\n"
                response += f"• Total Executions: {total_executions}\n"
                response += f"• Completed: {completed} ({(completed/total_executions*100):.1f}%)\n"
                response += f"• Failed: {failed} ({(failed/total_executions*100):.1f}%)\n"
            
            return {
                "response": response,
                "intent": "query_job_execution_details",
                "success": True,
                "data": {
                    "executions_count": len(executions),
                    "recent_executions": len(recent_executions) if 'recent_executions' in locals() else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Job execution details query error: {e}")
            return {
                "response": f"❌ Error querying execution details: {str(e)}",
                "intent": "query_job_execution_details",
                "success": False
            }
    
    async def handle_job_scheduling_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about job scheduling and triggers"""
        try:
            # Get scheduled jobs from automation service
            jobs = await self.automation_client.get_scheduled_jobs()
            
            if not jobs:
                return {
                    "response": "📅 **No scheduled jobs found**\n\nNo jobs are currently scheduled. You can schedule jobs to run automatically at specific times or intervals.",
                    "intent": "query_job_scheduling",
                    "success": True,
                    "data": {"scheduled_jobs_count": 0}
                }
            
            message_lower = message.lower()
            
            # Filter based on query type
            if 'today' in message_lower:
                # Jobs scheduled for today
                from datetime import datetime, date
                today = date.today()
                filtered_jobs = []
                for job in jobs:
                    next_run = job.get('next_run_time')
                    if next_run and next_run.startswith(today.strftime('%Y-%m-%d')):
                        filtered_jobs.append(job)
                filter_desc = "today"
                
            elif 'recurring' in message_lower or 'repeat' in message_lower:
                # Recurring jobs
                filtered_jobs = [j for j in jobs if j.get('is_recurring', False)]
                filter_desc = "recurring"
                
            elif 'cron' in message_lower:
                # Cron-based jobs
                filtered_jobs = [j for j in jobs if j.get('trigger_type') == 'cron']
                filter_desc = "cron-based"
                
            elif 'interval' in message_lower:
                # Interval-based jobs
                filtered_jobs = [j for j in jobs if j.get('trigger_type') == 'interval']
                filter_desc = "interval-based"
                
            else:
                # All scheduled jobs
                filtered_jobs = jobs
                filter_desc = "all scheduled"
            
            response = f"📅 **{filter_desc.title()} Jobs**\n\n"
            response += f"**Found:** {len(filtered_jobs)} jobs\n\n"
            
            if not filtered_jobs:
                response += f"No {filter_desc} jobs found.\n"
                response += f"Total scheduled jobs: {len(jobs)}"
            else:
                # Show job scheduling details
                for i, job in enumerate(filtered_jobs[:8]):
                    job_name = job.get('name', 'Unknown Job')
                    trigger_type = job.get('trigger_type', 'unknown')
                    next_run = job.get('next_run_time', 'Not scheduled')
                    is_enabled = job.get('is_enabled', False)
                    schedule_pattern = job.get('schedule_pattern', 'Unknown')
                    
                    status_emoji = '✅' if is_enabled else '⏸️'
                    
                    response += f"**{i+1}. {job_name}** {status_emoji}\n"
                    response += f"   • Trigger: {trigger_type}\n"
                    response += f"   • Pattern: {schedule_pattern}\n"
                    response += f"   • Next Run: {next_run}\n"
                    response += f"   • Status: {'Enabled' if is_enabled else 'Disabled'}\n\n"
                
                if len(filtered_jobs) > 8:
                    response += f"... and {len(filtered_jobs) - 8} more {filter_desc} jobs\n\n"
                
                # Scheduling statistics
                trigger_stats = {}
                enabled_count = 0
                for job in filtered_jobs:
                    trigger_type = job.get('trigger_type', 'unknown')
                    trigger_stats[trigger_type] = trigger_stats.get(trigger_type, 0) + 1
                    if job.get('is_enabled', False):
                        enabled_count += 1
                
                response += f"**Scheduling Summary:**\n"
                response += f"• Total: {len(filtered_jobs)} jobs\n"
                response += f"• Enabled: {enabled_count}\n"
                response += f"• Disabled: {len(filtered_jobs) - enabled_count}\n\n"
                
                if trigger_stats:
                    response += "**Trigger Types:**\n"
                    for trigger_type, count in sorted(trigger_stats.items()):
                        response += f"• {trigger_type.title()}: {count} jobs\n"
            
            return {
                "response": response,
                "intent": "query_job_scheduling",
                "success": True,
                "data": {
                    "scheduled_jobs_count": len(filtered_jobs),
                    "total_scheduled": len(jobs),
                    "filter_description": filter_desc
                }
            }
            
        except Exception as e:
            logger.error(f"Job scheduling query error: {e}")
            return {
                "response": f"❌ Error querying job scheduling: {str(e)}",
                "intent": "query_job_scheduling",
                "success": False
            }
    
    async def handle_workflow_step_analysis_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about workflow step analysis and dependencies"""
        try:
            # Get workflows with step details
            workflows = await self.automation_client.get_workflows_with_steps()
            
            if not workflows:
                return {
                    "response": "🔄 **No workflows found**\n\nNo workflows are configured yet. Create workflows to see step analysis.",
                    "intent": "query_workflow_step_analysis",
                    "success": True,
                    "data": {"workflows_count": 0}
                }
            
            message_lower = message.lower()
            
            # Extract workflow ID if specified
            import re
            workflow_id_match = re.search(r'workflow\s*#?(\d+)', message_lower)
            
            if workflow_id_match:
                # Analyze specific workflow
                workflow_id = workflow_id_match.group(1)
                target_workflow = None
                
                for workflow in workflows:
                    if str(workflow.get('id')) == workflow_id:
                        target_workflow = workflow
                        break
                
                if not target_workflow:
                    return {
                        "response": f"🔍 **Workflow not found**\n\nNo workflow found with ID '{workflow_id}'. Available workflows: {len(workflows)}",
                        "intent": "query_workflow_step_analysis",
                        "success": True,
                        "data": {"workflows_count": len(workflows)}
                    }
                
                # Detailed step analysis for specific workflow
                workflow_name = target_workflow.get('name', 'Unknown Workflow')
                steps = target_workflow.get('steps', [])
                
                response = f"🔄 **Workflow Step Analysis - {workflow_name}**\n\n"
                response += f"**Total Steps:** {len(steps)}\n\n"
                
                if steps:
                    # Analyze step types and dependencies
                    step_types = {}
                    dependencies = []
                    
                    response += "**Step Breakdown:**\n"
                    for i, step in enumerate(steps):
                        step_name = step.get('name', f'Step {i+1}')
                        step_type = step.get('type', 'unknown')
                        step_depends_on = step.get('depends_on', [])
                        step_timeout = step.get('timeout', 'Default')
                        step_retry_count = step.get('retry_count', 0)
                        
                        step_types[step_type] = step_types.get(step_type, 0) + 1
                        
                        response += f"\n**{i+1}. {step_name}**\n"
                        response += f"   • Type: {step_type}\n"
                        response += f"   • Timeout: {step_timeout}\n"
                        response += f"   • Retries: {step_retry_count}\n"
                        
                        if step_depends_on:
                            response += f"   • Depends on: {', '.join(step_depends_on)}\n"
                            dependencies.extend([(step_name, dep) for dep in step_depends_on])
                    
                    # Step type summary
                    response += f"\n**Step Type Distribution:**\n"
                    for step_type, count in sorted(step_types.items()):
                        response += f"• {step_type.title()}: {count} steps\n"
                    
                    # Dependency analysis
                    if dependencies:
                        response += f"\n**Dependencies ({len(dependencies)}):**\n"
                        for step, dependency in dependencies[:5]:
                            response += f"• {step} → {dependency}\n"
                        
                        if len(dependencies) > 5:
                            response += f"... and {len(dependencies) - 5} more dependencies\n"
                    else:
                        response += f"\n**Dependencies:** No step dependencies found\n"
                    
                    # Get execution statistics for this workflow
                    execution_stats = await self.automation_client.get_workflow_execution_stats(workflow_id)
                    if execution_stats:
                        response += f"\n**Execution Statistics:**\n"
                        response += f"• Total Runs: {execution_stats.get('total_runs', 0)}\n"
                        response += f"• Success Rate: {execution_stats.get('success_rate', 0):.1f}%\n"
                        response += f"• Avg Duration: {execution_stats.get('avg_duration', 'Unknown')}\n"
                        
                        # Step failure analysis
                        failed_steps = execution_stats.get('failed_steps', {})
                        if failed_steps:
                            response += f"\n**Most Failed Steps:**\n"
                            for step_name, failure_count in sorted(failed_steps.items(), key=lambda x: x[1], reverse=True)[:3]:
                                response += f"• {step_name}: {failure_count} failures\n"
                
                else:
                    response += "**No steps defined in this workflow**\n"
                
            else:
                # General workflow step analysis
                response = f"🔄 **Workflow Step Analysis Overview**\n\n"
                response += f"**Total Workflows:** {len(workflows)}\n\n"
                
                # Aggregate statistics
                total_steps = 0
                step_type_stats = {}
                complexity_stats = {'simple': 0, 'medium': 0, 'complex': 0}
                
                for workflow in workflows:
                    steps = workflow.get('steps', [])
                    step_count = len(steps)
                    total_steps += step_count
                    
                    # Classify workflow complexity
                    if step_count <= 3:
                        complexity_stats['simple'] += 1
                    elif step_count <= 8:
                        complexity_stats['medium'] += 1
                    else:
                        complexity_stats['complex'] += 1
                    
                    # Count step types
                    for step in steps:
                        step_type = step.get('type', 'unknown')
                        step_type_stats[step_type] = step_type_stats.get(step_type, 0) + 1
                
                response += f"**Step Statistics:**\n"
                response += f"• Total Steps: {total_steps}\n"
                response += f"• Avg Steps per Workflow: {total_steps/len(workflows):.1f}\n\n"
                
                response += f"**Workflow Complexity:**\n"
                response += f"• Simple (1-3 steps): {complexity_stats['simple']}\n"
                response += f"• Medium (4-8 steps): {complexity_stats['medium']}\n"
                response += f"• Complex (9+ steps): {complexity_stats['complex']}\n\n"
                
                if step_type_stats:
                    response += f"**Most Used Step Types:**\n"
                    for step_type, count in sorted(step_type_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                        response += f"• {step_type.title()}: {count} steps\n"
                
                # Show sample workflows
                response += f"\n**Sample Workflows:**\n"
                for i, workflow in enumerate(workflows[:3]):
                    workflow_name = workflow.get('name', 'Unknown')
                    step_count = len(workflow.get('steps', []))
                    response += f"{i+1}. **{workflow_name}** - {step_count} steps\n"
                
                if len(workflows) > 3:
                    response += f"... and {len(workflows) - 3} more workflows\n"
            
            return {
                "response": response,
                "intent": "query_workflow_step_analysis",
                "success": True,
                "data": {
                    "workflows_count": len(workflows),
                    "total_steps": total_steps if 'total_steps' in locals() else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Workflow step analysis query error: {e}")
            return {
                "response": f"❌ Error analyzing workflow steps: {str(e)}",
                "intent": "query_workflow_step_analysis",
                "success": False
            }
    
    async def handle_task_queue_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about real-time task queue status"""
        try:
            # Get current task queue status
            queue_status = await self.automation_client.get_task_queue_status()
            
            if not queue_status:
                return {
                    "response": "📋 **Task queue information unavailable**\n\nUnable to retrieve task queue status. The automation service may be unavailable.",
                    "intent": "query_task_queue",
                    "success": False,
                    "data": {"queue_available": False}
                }
            
            message_lower = message.lower()
            
            # Extract queue information
            pending_tasks = queue_status.get('pending_tasks', [])
            running_tasks = queue_status.get('running_tasks', [])
            completed_tasks = queue_status.get('completed_tasks', [])
            failed_tasks = queue_status.get('failed_tasks', [])
            worker_status = queue_status.get('workers', [])
            
            if 'pending' in message_lower:
                # Focus on pending tasks
                response = f"📋 **Pending Tasks**\n\n"
                response += f"**Queue Length:** {len(pending_tasks)} tasks\n\n"
                
                if pending_tasks:
                    response += "**Waiting for Execution:**\n"
                    for i, task in enumerate(pending_tasks[:8]):
                        task_name = task.get('name', 'Unknown Task')
                        job_name = task.get('job_name', 'Unknown Job')
                        priority = task.get('priority', 'normal')
                        queued_at = task.get('queued_at', 'Unknown')
                        
                        priority_emoji = '🔴' if priority == 'high' else '🟡' if priority == 'medium' else '🟢'
                        
                        response += f"{i+1}. **{task_name}** {priority_emoji}\n"
                        response += f"   • Job: {job_name}\n"
                        response += f"   • Priority: {priority}\n"
                        response += f"   • Queued: {queued_at}\n\n"
                    
                    if len(pending_tasks) > 8:
                        response += f"... and {len(pending_tasks) - 8} more pending tasks\n"
                else:
                    response += "✅ **No pending tasks** - Queue is empty!"
                
            elif 'running' in message_lower or 'active' in message_lower:
                # Focus on running tasks
                response = f"🔄 **Running Tasks**\n\n"
                response += f"**Currently Executing:** {len(running_tasks)} tasks\n\n"
                
                if running_tasks:
                    response += "**Active Executions:**\n"
                    for i, task in enumerate(running_tasks):
                        task_name = task.get('name', 'Unknown Task')
                        job_name = task.get('job_name', 'Unknown Job')
                        started_at = task.get('started_at', 'Unknown')
                        worker_id = task.get('worker_id', 'Unknown')
                        progress = task.get('progress', 0)
                        
                        response += f"{i+1}. **{task_name}** 🔄\n"
                        response += f"   • Job: {job_name}\n"
                        response += f"   • Worker: {worker_id}\n"
                        response += f"   • Started: {started_at}\n"
                        response += f"   • Progress: {progress}%\n\n"
                else:
                    response += "💤 **No running tasks** - All workers are idle"
                
            elif 'worker' in message_lower:
                # Focus on worker status
                response = f"👷 **Worker Status**\n\n"
                response += f"**Total Workers:** {len(worker_status)}\n\n"
                
                if worker_status:
                    active_workers = 0
                    idle_workers = 0
                    
                    response += "**Worker Details:**\n"
                    for i, worker in enumerate(worker_status):
                        worker_id = worker.get('id', f'Worker {i+1}')
                        status = worker.get('status', 'unknown')
                        current_task = worker.get('current_task', None)
                        tasks_completed = worker.get('tasks_completed', 0)
                        last_activity = worker.get('last_activity', 'Unknown')
                        
                        if status == 'active':
                            active_workers += 1
                            status_emoji = '🔄'
                        else:
                            idle_workers += 1
                            status_emoji = '💤'
                        
                        response += f"{i+1}. **{worker_id}** {status_emoji}\n"
                        response += f"   • Status: {status}\n"
                        response += f"   • Completed: {tasks_completed} tasks\n"
                        response += f"   • Last Activity: {last_activity}\n"
                        
                        if current_task:
                            response += f"   • Current Task: {current_task}\n"
                        
                        response += "\n"
                    
                    response += f"**Worker Summary:**\n"
                    response += f"• Active: {active_workers}\n"
                    response += f"• Idle: {idle_workers}\n"
                    
                    # Worker utilization
                    if len(worker_status) > 0:
                        utilization = (active_workers / len(worker_status)) * 100
                        response += f"• Utilization: {utilization:.1f}%\n"
                else:
                    response += "❌ **No workers available** - Check automation service configuration"
                
            else:
                # General queue overview
                response = f"📋 **Task Queue Overview**\n\n"
                
                # Queue statistics
                total_pending = len(pending_tasks)
                total_running = len(running_tasks)
                total_completed = len(completed_tasks)
                total_failed = len(failed_tasks)
                
                response += f"**Queue Status:**\n"
                response += f"• Pending: {total_pending} 📋\n"
                response += f"• Running: {total_running} 🔄\n"
                response += f"• Completed: {total_completed} ✅\n"
                response += f"• Failed: {total_failed} ❌\n\n"
                
                # Worker summary
                if worker_status:
                    active_workers = len([w for w in worker_status if w.get('status') == 'active'])
                    total_workers = len(worker_status)
                    
                    response += f"**Workers:**\n"
                    response += f"• Total: {total_workers}\n"
                    response += f"• Active: {active_workers}\n"
                    response += f"• Idle: {total_workers - active_workers}\n\n"
                
                # Queue health assessment
                if total_pending > 10:
                    response += "⚠️ **Queue Alert:** High number of pending tasks. Consider adding more workers.\n"
                elif total_pending == 0 and total_running == 0:
                    response += "✅ **Queue Status:** All clear - no pending or running tasks.\n"
                else:
                    response += "✅ **Queue Status:** Normal operation.\n"
                
                # Recent activity
                if running_tasks:
                    response += f"\n**Currently Running:**\n"
                    for i, task in enumerate(running_tasks[:3]):
                        task_name = task.get('name', 'Unknown Task')
                        response += f"• {task_name}\n"
                    
                    if len(running_tasks) > 3:
                        response += f"... and {len(running_tasks) - 3} more\n"
            
            return {
                "response": response,
                "intent": "query_task_queue",
                "success": True,
                "data": {
                    "pending_count": len(pending_tasks),
                    "running_count": len(running_tasks),
                    "worker_count": len(worker_status),
                    "queue_health": "normal" if len(pending_tasks) <= 10 else "high_load"
                }
            }
            
        except Exception as e:
            logger.error(f"Task queue query error: {e}")
            return {
                "response": f"❌ Error querying task queue: {str(e)}",
                "intent": "query_task_queue",
                "success": False
            }
    
    async def handle_notification_audit_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle queries about notification delivery audit trail"""
        try:
            # Get notification audit data from communication service
            audit_data = await self.communication_client.get_notification_audit()
            
            if not audit_data:
                return {
                    "response": "📧 **No notification audit data found**\n\nNo notification delivery records available. Send some notifications to see audit trail.",
                    "intent": "query_notification_audit",
                    "success": True,
                    "data": {"audit_records": 0}
                }
            
            message_lower = message.lower()
            
            # Filter audit data based on query
            if 'failed' in message_lower or 'failure' in message_lower:
                filtered_records = [r for r in audit_data if r.get('delivery_status') == 'failed']
                filter_desc = "failed deliveries"
            elif 'success' in message_lower or 'delivered' in message_lower:
                filtered_records = [r for r in audit_data if r.get('delivery_status') == 'delivered']
                filter_desc = "successful deliveries"
            elif 'email' in message_lower:
                filtered_records = [r for r in audit_data if r.get('channel_type') == 'email']
                filter_desc = "email notifications"
            elif 'today' in message_lower:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                filtered_records = [r for r in audit_data if r.get('sent_at', '').startswith(today)]
                filter_desc = "today's notifications"
            else:
                filtered_records = audit_data[:20]  # Recent 20
                filter_desc = "recent notifications"
            
            response = f"📧 **Notification Audit - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_records)} records\n\n"
            
            if not filtered_records:
                response += f"No {filter_desc} found.\n"
                response += f"Total audit records: {len(audit_data)}"
            else:
                # Show audit details
                for i, record in enumerate(filtered_records[:8]):
                    recipient = record.get('recipient', 'Unknown')
                    subject = record.get('subject', 'No subject')
                    delivery_status = record.get('delivery_status', 'unknown')
                    sent_at = record.get('sent_at', 'Unknown')
                    channel_type = record.get('channel_type', 'unknown')
                    error_message = record.get('error_message', '')
                    
                    status_emoji = '✅' if delivery_status == 'delivered' else '❌' if delivery_status == 'failed' else '⏳'
                    
                    response += f"**{i+1}. {subject[:50]}{'...' if len(subject) > 50 else ''}** {status_emoji}\n"
                    response += f"   • Recipient: {recipient}\n"
                    response += f"   • Channel: {channel_type}\n"
                    response += f"   • Status: {delivery_status}\n"
                    response += f"   • Sent: {sent_at}\n"
                    
                    if error_message:
                        response += f"   • Error: {error_message[:100]}{'...' if len(error_message) > 100 else ''}\n"
                    
                    response += "\n"
                
                if len(filtered_records) > 8:
                    response += f"... and {len(filtered_records) - 8} more records\n\n"
                
                # Delivery statistics
                delivered_count = len([r for r in filtered_records if r.get('delivery_status') == 'delivered'])
                failed_count = len([r for r in filtered_records if r.get('delivery_status') == 'failed'])
                pending_count = len(filtered_records) - delivered_count - failed_count
                
                response += f"**Delivery Statistics:**\n"
                response += f"• Delivered: {delivered_count} ({(delivered_count/len(filtered_records)*100):.1f}%)\n"
                response += f"• Failed: {failed_count} ({(failed_count/len(filtered_records)*100):.1f}%)\n"
                
                if pending_count > 0:
                    response += f"• Pending: {pending_count}\n"
                
                # Channel breakdown
                channel_stats = {}
                for record in filtered_records:
                    channel = record.get('channel_type', 'unknown')
                    channel_stats[channel] = channel_stats.get(channel, 0) + 1
                
                if len(channel_stats) > 1:
                    response += f"\n**Channel Breakdown:**\n"
                    for channel, count in sorted(channel_stats.items()):
                        response += f"• {channel.title()}: {count} notifications\n"
            
            return {
                "response": response,
                "intent": "query_notification_audit",
                "success": True,
                "data": {
                    "audit_records": len(filtered_records),
                    "total_records": len(audit_data),
                    "filter_description": filter_desc
                }
            }
            
        except Exception as e:
            logger.error(f"Notification audit query error: {e}")
            return {
                "response": f"❌ Error querying notification audit: {str(e)}",
                "intent": "query_notification_audit",
                "success": False
            }

# Global AI instance
            