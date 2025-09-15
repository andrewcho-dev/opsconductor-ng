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
        if any(word in message_lower for word in ['targets', 'servers', 'hosts', 'machines']):
            return {
                "intent": "system_query",
                "confidence": 0.8,
                "action": "query_targets"
            }
        
        if any(word in message_lower for word in ['jobs', 'automation', 'tasks', 'workflows']):
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
        
        # System health intents
        if any(word in message_lower for word in ['health', 'status', 'anomaly', 'alert', 'performance']):
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
            elif intent_result["action"] == "query_jobs":
                response = await self.handle_job_query(message, context)
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

# Global AI instance
ai_engine = OpsConductorAI()