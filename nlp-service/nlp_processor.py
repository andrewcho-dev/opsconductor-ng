"""
Advanced NLP processor for OpsConductor AI Service
GPU-accelerated natural language processing with spaCy and transformers
"""
import re
import torch
import spacy
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ParsedRequest:
    """Parsed natural language request"""
    operation: str  # update, restart, stop, start, install, etc.
    target_process: Optional[str] = None  # stationcontroller.exe, nginx, apache
    target_service: Optional[str] = None  # IIS, Apache, MySQL
    target_group: Optional[str] = None  # CIS servers, web servers, database servers
    target_os: Optional[str] = None  # windows, linux
    package_name: Optional[str] = None  # for package operations
    confidence: float = 0.0
    raw_text: str = ""


class SimpleNLPProcessor:
    """GPU-accelerated NLP processor with spaCy and regex fallback"""
    
    def __init__(self):
        # Initialize GPU support
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"NLP Processor using device: {self.device}")
        
        # Try to load spaCy with GPU support
        self.nlp = None
        try:
            if self.device == "cuda":
                spacy.require_gpu()
                logger.info("GPU acceleration enabled for spaCy")
            
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
            
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"GPU memory available: {gpu_memory:.2f} GB")
                
        except Exception as e:
            logger.warning(f"Failed to load spaCy model, falling back to regex only: {e}")
            self.nlp = None
        # Operation patterns
        self.operation_patterns = {
            'update': [
                r'\b(update|upgrade|patch)\b',
                r'\binstall.*update\b',
                r'\bapply.*update\b'
            ],
            'restart': [
                r'\b(restart|reboot|bounce)\b',
                r'\brestart.*service\b',
                r'\breboot.*server\b'
            ],
            'stop': [
                r'\b(stop|kill|terminate|shutdown)\b',
                r'\bstop.*service\b',
                r'\bkill.*process\b'
            ],
            'start': [
                r'\b(start|launch|run|execute)\b',
                r'\bstart.*service\b',
                r'\blaunch.*application\b'
            ],
            'install': [
                r'\b(install|deploy|setup)\b',
                r'\binstall.*package\b',
                r'\bdeploy.*application\b'
            ],
            'check': [
                r'\b(check|verify|test|status)\b',
                r'\bcheck.*status\b',
                r'\bverify.*running\b'
            ]
        }
        
        # Target patterns
        self.process_patterns = [
            r'\b(stationcontroller\.exe|stationcontroller)\b',
            r'\b(nginx|apache|httpd)\b',
            r'\b(mysql|postgres|postgresql)\b',
            r'\b(iis|w3svc)\b',
            r'\b([a-zA-Z]+\.exe)\b',
            r'\b([a-zA-Z]+\.service)\b'
        ]
        
        self.service_patterns = [
            r'\b(IIS|Internet Information Services)\b',
            r'\b(Apache|Apache2|httpd)\b',
            r'\b(MySQL|MariaDB)\b',
            r'\b(PostgreSQL|Postgres)\b',
            r'\b(Redis|MongoDB)\b',
            r'\b(Nginx)\b'
        ]
        
        # Group patterns
        self.group_patterns = [
            r'\b(CIS servers?|CIS)\b',
            r'\b(web servers?|webservers?)\b',
            r'\b(database servers?|db servers?|dbservers?)\b',
            r'\b(application servers?|app servers?|appservers?)\b',
            r'\b(production servers?|prod servers?)\b',
            r'\b(staging servers?|stage servers?)\b',
            r'\b(development servers?|dev servers?)\b',
            r'\b(all servers?)\b',
            r'\b(group [A-Z]+)\b',
            r'\b(servers? in [a-zA-Z0-9_-]+)\b'
        ]
        
        # OS patterns
        self.os_patterns = {
            'windows': [r'\b(windows?|win|w2k|2019|2022)\b', r'\b(\.exe|powershell|cmd)\b'],
            'linux': [r'\b(linux|ubuntu|centos|rhel|debian)\b', r'\b(systemctl|service|apt|yum)\b']
        }

    def parse_request(self, text: str) -> ParsedRequest:
        """Parse natural language request into structured data"""
        text_lower = text.lower()
        
        # Initialize result
        result = ParsedRequest(
            operation="unknown",
            raw_text=text,
            confidence=0.0
        )
        
        # Extract operation
        operation_scores = {}
        for op, patterns in self.operation_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                operation_scores[op] = score
        
        if operation_scores:
            result.operation = max(operation_scores, key=operation_scores.get)
            result.confidence += 0.3
        
        # Extract target process
        for pattern in self.process_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.target_process = match.group(1) if match.groups() else match.group(0)
                result.confidence += 0.2
                break
        
        # Extract target service
        for pattern in self.service_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.target_service = match.group(0)
                result.confidence += 0.2
                break
        
        # Extract target group
        for pattern in self.group_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.target_group = match.group(0)
                result.confidence += 0.2
                break
        
        # Extract OS hints
        for os_name, patterns in self.os_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result.target_os = os_name
                    result.confidence += 0.1
                    break
            if result.target_os:
                break
        
        return result

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract all entities from text for debugging"""
        entities = {
            'operations': [],
            'processes': [],
            'services': [],
            'groups': [],
            'os_hints': []
        }
        
        # Extract operations
        for op, patterns in self.operation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    entities['operations'].append(op)
                    break
        
        # Extract processes
        for pattern in self.process_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['processes'].extend(matches)
        
        # Extract services
        for pattern in self.service_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['services'].extend(matches)
        
        # Extract groups
        for pattern in self.group_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['groups'].extend(matches)
        
        # Extract OS hints
        for os_name, patterns in self.os_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    entities['os_hints'].append(os_name)
                    break
        
        return entities
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status and memory usage"""
        try:
            if not torch.cuda.is_available():
                return {
                    "gpu_available": False,
                    "device": "cpu",
                    "message": "No GPU available"
                }
            
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated(current_device) / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved(current_device) / 1024**3   # GB
            memory_total = torch.cuda.get_device_properties(current_device).total_memory / 1024**3  # GB
            
            return {
                "gpu_available": True,
                "device": f"cuda:{current_device}",
                "device_name": device_name,
                "device_count": device_count,
                "memory_allocated_gb": round(memory_allocated, 2),
                "memory_reserved_gb": round(memory_reserved, 2),
                "memory_total_gb": round(memory_total, 2),
                "memory_free_gb": round(memory_total - memory_reserved, 2),
                "cuda_version": torch.version.cuda,
                "spacy_gpu_enabled": self.nlp is not None and hasattr(self.nlp, 'has_pipe')
            }
            
        except Exception as e:
            logger.error(f"Failed to get GPU status: {e}")
            return {
                "gpu_available": False,
                "device": "cpu",
                "error": str(e)
            }


# Example usage and testing
if __name__ == "__main__":
    processor = SimpleNLPProcessor()
    
    test_requests = [
        "update stationcontroller on CIS servers",
        "restart nginx on web servers",
        "stop Apache service on all servers",
        "install MySQL on database servers",
        "check status of IIS on production servers",
        "update stationcontroller.exe on Windows servers in group CIS"
    ]
    
    print("=== NLP Processor Test ===")
    for request in test_requests:
        print(f"\nInput: {request}")
        parsed = processor.parse_request(request)
        print(f"Operation: {parsed.operation}")
        print(f"Process: {parsed.target_process}")
        print(f"Service: {parsed.target_service}")
        print(f"Group: {parsed.target_group}")
        print(f"OS: {parsed.target_os}")
        print(f"Confidence: {parsed.confidence:.2f}")
        
        entities = processor.extract_entities(request)
        print(f"All entities: {entities}")