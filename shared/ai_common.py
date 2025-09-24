"""
OpsConductor Common AI Utilities
Shared utilities for all AI services
"""
import re
import json
import hashlib
import structlog
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = structlog.get_logger()

class Intent(Enum):
    """Standardized intents across AI system"""
    # Infrastructure
    LIST_TARGETS = "list_targets"
    GET_TARGET = "get_target"
    CREATE_TARGET = "create_target"
    UPDATE_TARGET = "update_target"
    DELETE_TARGET = "delete_target"
    CHECK_SERVICE = "check_service"
    
    # Automation
    LIST_JOBS = "list_jobs"
    RUN_JOB = "run_job"
    CREATE_WORKFLOW = "create_workflow"
    SCHEDULE_JOB = "schedule_job"
    CHECK_EXECUTION = "check_execution"
    
    # Communication
    SEND_NOTIFICATION = "send_notification"
    CREATE_TEMPLATE = "create_template"
    CHECK_ALERTS = "check_alerts"
    
    # System
    CHECK_HEALTH = "check_health"
    GET_METRICS = "get_metrics"
    TROUBLESHOOT = "troubleshoot"
    
    # General
    GENERAL_QUERY = "general_query"
    HELP = "help"
    UNKNOWN = "unknown"

class AIContext:
    """Manages context across AI interactions"""
    
    def __init__(self):
        self.conversation_history = []
        self.user_context = {}
        self.system_context = {}
        self.max_history = 10
    
    def add_interaction(self, query: str, response: str, metadata: Optional[Dict] = None):
        """Add interaction to history"""
        interaction = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversation_history.append(interaction)
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_context_summary(self) -> str:
        """Get summary of current context"""
        if not self.conversation_history:
            return "No previous context"
        
        summary_parts = []
        for interaction in self.conversation_history[-3:]:  # Last 3 interactions
            summary_parts.append(f"Q: {interaction['query'][:100]}...")
            summary_parts.append(f"A: {interaction['response'][:100]}...")
        
        return "\n".join(summary_parts)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "conversation_history": self.conversation_history,
            "user_context": self.user_context,
            "system_context": self.system_context
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load context from dictionary"""
        self.conversation_history = data.get("conversation_history", [])
        self.user_context = data.get("user_context", {})
        self.system_context = data.get("system_context", {})



def extract_entities(query: str) -> Dict[str, Any]:
    """
    Extract entities from query (targets, jobs, dates, etc.)
    """
    entities = {
        "targets": [],
        "jobs": [],
        "dates": [],
        "numbers": [],
        "emails": [],
        "ips": [],
        "urls": []
    }
    
    # Extract IP addresses
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    entities["ips"] = re.findall(ip_pattern, query)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities["emails"] = re.findall(email_pattern, query)
    
    # Extract URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities["urls"] = re.findall(url_pattern, query)
    
    # Extract numbers
    number_pattern = r'\b\d+\b'
    entities["numbers"] = [int(n) for n in re.findall(number_pattern, query)]
    
    # Extract quoted strings (potential target/job names)
    quoted_pattern = r'"([^"]*)"'
    quoted_strings = re.findall(quoted_pattern, query)
    
    # Classify quoted strings
    for quoted in quoted_strings:
        if any(word in query.lower() for word in ["target", "server", "host"]):
            entities["targets"].append(quoted)
        elif any(word in query.lower() for word in ["job", "task", "workflow"]):
            entities["jobs"].append(quoted)
    
    return entities

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    """
    # Remove potential SQL injection patterns
    sql_patterns = [
        r';\s*DROP\s+TABLE',
        r';\s*DELETE\s+FROM',
        r';\s*UPDATE\s+',
        r';\s*INSERT\s+INTO',
        r'--\s*$',
        r'\/\*.*\*\/',
        r'UNION\s+SELECT',
        r'OR\s+1\s*=\s*1',
        r'AND\s+1\s*=\s*1'
    ]
    
    sanitized = text
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Limit length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def format_response(
    success: bool,
    data: Any = None,
    message: str = None,
    error: str = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Format standardized API response
    """
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    if error:
        response["error"] = error
    
    if metadata:
        response["metadata"] = metadata
    
    return response

def generate_interaction_id(user_id: str, timestamp: Optional[float] = None) -> str:
    """
    Generate unique interaction ID
    """
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    
    # Create hash from user_id and timestamp
    hash_input = f"{user_id}:{timestamp}"
    hash_obj = hashlib.md5(hash_input.encode())
    hash_str = hash_obj.hexdigest()[:8]
    
    return f"int_{int(timestamp)}_{hash_str}"

def parse_natural_language_time(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse natural language time expressions
    Returns dict with parsed time information
    """
    time_info = {
        "original": text,
        "parsed": None,
        "type": None  # "absolute", "relative", "recurring"
    }
    
    text_lower = text.lower()
    
    # Relative time patterns
    relative_patterns = {
        r"in (\d+) minute[s]?": lambda m: {"minutes": int(m.group(1))},
        r"in (\d+) hour[s]?": lambda m: {"hours": int(m.group(1))},
        r"in (\d+) day[s]?": lambda m: {"days": int(m.group(1))},
        r"tomorrow": lambda m: {"days": 1},
        r"next week": lambda m: {"weeks": 1},
        r"next month": lambda m: {"months": 1}
    }
    
    for pattern, parser in relative_patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            time_info["parsed"] = parser(match)
            time_info["type"] = "relative"
            return time_info
    
    # Recurring patterns
    recurring_patterns = {
        r"every (\d+) minute[s]?": lambda m: {"interval": "minutes", "value": int(m.group(1))},
        r"every (\d+) hour[s]?": lambda m: {"interval": "hours", "value": int(m.group(1))},
        r"daily": lambda m: {"interval": "daily", "value": 1},
        r"weekly": lambda m: {"interval": "weekly", "value": 1},
        r"monthly": lambda m: {"interval": "monthly", "value": 1}
    }
    
    for pattern, parser in recurring_patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            time_info["parsed"] = parser(match)
            time_info["type"] = "recurring"
            return time_info
    
    return None

def calculate_confidence_score(
    factors: Dict[str, float],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate weighted confidence score from multiple factors
    """
    if not factors:
        return 0.0
    
    if weights is None:
        # Equal weights
        weights = {k: 1.0 for k in factors.keys()}
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for factor, value in factors.items():
        weight = weights.get(factor, 1.0)
        weighted_sum += value * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return weighted_sum / total_weight

def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks for processing
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start:
                end = sentence_end + 1
        
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start with overlap
        start = end - overlap if end < len(text) else end
    
    return chunks

class ResponseBuilder:
    """Build natural language responses"""
    
    @staticmethod
    def success_message(action: str, entity: str, details: Optional[Dict] = None) -> str:
        """Generate success message"""
        base_message = f"Successfully {action} {entity}"
        
        if details:
            detail_parts = []
            for key, value in details.items():
                detail_parts.append(f"{key}: {value}")
            
            if detail_parts:
                base_message += f" ({', '.join(detail_parts)})"
        
        return base_message
    
    @staticmethod
    def error_message(action: str, entity: str, error: str) -> str:
        """Generate error message"""
        return f"Failed to {action} {entity}: {error}"
    
    @staticmethod
    def list_message(entity_type: str, items: List[Any], format_func=None) -> str:
        """Generate list message"""
        if not items:
            return f"No {entity_type} found"
        
        message = f"Found {len(items)} {entity_type}:\n"
        
        for i, item in enumerate(items, 1):
            if format_func:
                item_str = format_func(item)
            else:
                item_str = str(item)
            
            message += f"{i}. {item_str}\n"
        
        return message
    
    @staticmethod
    def help_message(topic: str) -> str:
        """Generate help message"""
        help_topics = {
            "targets": "You can manage targets using commands like:\n"
                      "- 'List all targets'\n"
                      "- 'Create a new target named \"server1\"'\n"
                      "- 'Update target \"server1\"'\n"
                      "- 'Delete target \"server1\"'\n"
                      "- 'Check service status on \"server1\"'",
            
            "jobs": "You can manage jobs and automation using:\n"
                   "- 'List all jobs'\n"
                   "- 'Run job \"backup\"'\n"
                   "- 'Schedule job \"maintenance\" daily'\n"
                   "- 'Check execution status'\n"
                   "- 'Create a new workflow'",
            
            "notifications": "You can manage notifications using:\n"
                           "- 'Send notification to admin@example.com'\n"
                           "- 'Create notification template'\n"
                           "- 'Check recent alerts'\n"
                           "- 'Configure alert channels'",
            
            "general": "I can help you with:\n"
                      "- Infrastructure management (targets, services)\n"
                      "- Automation (jobs, workflows, scheduling)\n"
                      "- Communications (notifications, alerts)\n"
                      "- System monitoring and troubleshooting\n"
                      "Ask me anything about these topics!"
        }
        
        return help_topics.get(topic, help_topics["general"])