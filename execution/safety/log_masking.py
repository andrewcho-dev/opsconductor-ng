"""
Log Masker - Safety Feature #7

Sink-level log masking for sensitive data:
- Automatic masking of secrets in logs
- Masking of PII (personally identifiable information)
- Masking of credentials, tokens, API keys
- Custom masking patterns

Implementation:
- Regex-based pattern matching
- Sink-level masking (applied before writing to log)
- Integration with logging framework
- Configurable masking patterns

Usage:
    masker = LogMasker()
    masker.add_pattern(r'password=\w+', 'password=***')
    
    # In logging handler:
    masked_message = masker.mask(log_record.getMessage())
"""

import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MaskingPattern:
    """Masking pattern configuration"""
    name: str
    pattern: str
    replacement: str
    enabled: bool = True


class LogMasker:
    """
    Log masker for sink-level log masking.
    
    This is Safety Feature #7 and is critical for production deployment.
    """
    
    # Default masking patterns
    DEFAULT_PATTERNS = [
        # Passwords
        MaskingPattern(
            name="password",
            pattern=r'(?i)(password|passwd|pwd)["\s:=]+([^\s"\']+)',
            replacement=r'\1=***MASKED***',
        ),
        # API keys
        MaskingPattern(
            name="api_key",
            pattern=r'(?i)(api[_-]?key|apikey)["\s:=]+([a-zA-Z0-9_\-]{15,})',
            replacement=r'\1=***MASKED***',
        ),
        # Tokens
        MaskingPattern(
            name="token",
            pattern=r'(?i)(token|auth|bearer)["\s:=]+([a-zA-Z0-9_\-\.]{20,})',
            replacement=r'\1=***MASKED***',
        ),
        # AWS access keys
        MaskingPattern(
            name="aws_access_key",
            pattern=r'(AKIA[0-9A-Z]{16})',
            replacement=r'***MASKED_AWS_KEY***',
        ),
        # AWS secret keys
        MaskingPattern(
            name="aws_secret_key",
            pattern=r'(?i)(aws[_-]?secret[_-]?access[_-]?key)["\s:=]+([a-zA-Z0-9/+=]{40})',
            replacement=r'\1=***MASKED***',
        ),
        # Private keys
        MaskingPattern(
            name="private_key",
            pattern=r'-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----',
            replacement=r'***MASKED_PRIVATE_KEY***',
        ),
        # SSH keys
        MaskingPattern(
            name="ssh_key",
            pattern=r'ssh-rsa [A-Za-z0-9+/=]+',
            replacement=r'***MASKED_SSH_KEY***',
        ),
        # Database connection strings
        MaskingPattern(
            name="db_connection",
            pattern=r'(?i)(postgres|mysql|mongodb)://([^:]+):([^@]+)@',
            replacement=r'\1://\2:***MASKED***@',
        ),
        # Email addresses (PII)
        MaskingPattern(
            name="email",
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            replacement=r'***MASKED_EMAIL***',
        ),
        # Credit card numbers (PII)
        MaskingPattern(
            name="credit_card",
            pattern=r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            replacement=r'***MASKED_CC***',
        ),
        # Social security numbers (PII)
        MaskingPattern(
            name="ssn",
            pattern=r'\b\d{3}-\d{2}-\d{4}\b',
            replacement=r'***MASKED_SSN***',
        ),
        # IP addresses (optional, can be disabled)
        MaskingPattern(
            name="ip_address",
            pattern=r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            replacement=r'***MASKED_IP***',
            enabled=False,  # Disabled by default
        ),
        # Generic secrets (base64-like strings)
        MaskingPattern(
            name="generic_secret",
            pattern=r'(?i)(secret|credential)["\s:=]+([a-zA-Z0-9+/]{32,}={0,2})',
            replacement=r'\1=***MASKED***',
        ),
    ]
    
    def __init__(
        self,
        enable_default_patterns: bool = True,
        custom_patterns: Optional[List[MaskingPattern]] = None,
    ):
        """
        Initialize log masker.
        
        Args:
            enable_default_patterns: Enable default masking patterns (default: True)
            custom_patterns: Custom masking patterns
        """
        self.patterns: List[MaskingPattern] = []
        self._compiled_patterns: List[Tuple[str, re.Pattern, str]] = []
        
        # Add default patterns
        if enable_default_patterns:
            for pattern in self.DEFAULT_PATTERNS:
                if pattern.enabled:
                    self.add_pattern(pattern)
        
        # Add custom patterns
        if custom_patterns:
            for pattern in custom_patterns:
                self.add_pattern(pattern)
    
    def add_pattern(self, pattern: MaskingPattern) -> None:
        """
        Add masking pattern.
        
        Args:
            pattern: Masking pattern
        """
        self.patterns.append(pattern)
        
        # Compile regex
        try:
            compiled = re.compile(pattern.pattern)
            self._compiled_patterns.append(
                (pattern.name, compiled, pattern.replacement)
            )
            logger.debug(f"Added masking pattern: {pattern.name}")
        except re.error as e:
            logger.error(
                f"Failed to compile masking pattern {pattern.name}: {e}"
            )
    
    def remove_pattern(self, name: str) -> None:
        """
        Remove masking pattern by name.
        
        Args:
            name: Pattern name
        """
        self.patterns = [p for p in self.patterns if p.name != name]
        self._compiled_patterns = [
            (n, c, r) for n, c, r in self._compiled_patterns if n != name
        ]
        logger.debug(f"Removed masking pattern: {name}")
    
    def enable_pattern(self, name: str) -> None:
        """
        Enable masking pattern by name.
        
        Args:
            name: Pattern name
        """
        for pattern in self.patterns:
            if pattern.name == name:
                pattern.enabled = True
                logger.debug(f"Enabled masking pattern: {name}")
                break
    
    def disable_pattern(self, name: str) -> None:
        """
        Disable masking pattern by name.
        
        Args:
            name: Pattern name
        """
        for pattern in self.patterns:
            if pattern.name == name:
                pattern.enabled = False
                logger.debug(f"Disabled masking pattern: {name}")
                break
    
    def mask(self, text: str) -> str:
        """
        Mask sensitive data in text.
        
        This is the main entry point for log masking.
        
        Args:
            text: Text to mask
        
        Returns:
            Masked text
        """
        if not text:
            return text
        
        masked_text = text
        
        # Apply all patterns
        for name, pattern, replacement in self._compiled_patterns:
            try:
                masked_text = pattern.sub(replacement, masked_text)
            except Exception as e:
                logger.error(
                    f"Failed to apply masking pattern {name}: {e}"
                )
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive data in dictionary.
        
        Args:
            data: Dictionary to mask
        
        Returns:
            Masked dictionary
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            # Mask key
            masked_key = self.mask(str(key))
            
            # Mask value
            if isinstance(value, str):
                masked_value = self.mask(value)
            elif isinstance(value, dict):
                masked_value = self.mask_dict(value)
            elif isinstance(value, list):
                masked_value = self.mask_list(value)
            else:
                masked_value = value
            
            masked_data[masked_key] = masked_value
        
        return masked_data
    
    def mask_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively mask sensitive data in list.
        
        Args:
            data: List to mask
        
        Returns:
            Masked list
        """
        if not isinstance(data, list):
            return data
        
        masked_data = []
        for item in data:
            if isinstance(item, str):
                masked_item = self.mask(item)
            elif isinstance(item, dict):
                masked_item = self.mask_dict(item)
            elif isinstance(item, list):
                masked_item = self.mask_list(item)
            else:
                masked_item = item
            
            masked_data.append(masked_item)
        
        return masked_data
    
    def get_patterns(self) -> List[MaskingPattern]:
        """
        Get all masking patterns.
        
        Returns:
            List of masking patterns
        """
        return self.patterns.copy()


class MaskingLogHandler(logging.Handler):
    """
    Logging handler that masks sensitive data.
    
    This should be added to the logging configuration to mask all logs.
    """
    
    def __init__(
        self,
        masker: Optional[LogMasker] = None,
        target_handler: Optional[logging.Handler] = None,
    ):
        """
        Initialize masking log handler.
        
        Args:
            masker: Log masker (if None, creates default masker)
            target_handler: Target handler to forward masked logs to
        """
        super().__init__()
        self.masker = masker or LogMasker()
        self.target_handler = target_handler
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit log record with masking.
        
        Args:
            record: Log record
        """
        try:
            # Mask message
            if record.msg:
                record.msg = self.masker.mask(str(record.msg))
            
            # Mask args
            if record.args:
                if isinstance(record.args, dict):
                    record.args = self.masker.mask_dict(record.args)
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        self.masker.mask(str(arg)) if isinstance(arg, str) else arg
                        for arg in record.args
                    )
            
            # Forward to target handler
            if self.target_handler:
                self.target_handler.emit(record)
        except Exception as e:
            self.handleError(record)


def setup_log_masking(
    masker: Optional[LogMasker] = None,
    logger_name: Optional[str] = None,
) -> None:
    """
    Setup log masking for logger.
    
    Args:
        masker: Log masker (if None, creates default masker)
        logger_name: Logger name (if None, applies to root logger)
    """
    target_logger = logging.getLogger(logger_name)
    
    # Create masking handler
    masking_handler = MaskingLogHandler(masker=masker)
    
    # Add handler to logger
    target_logger.addHandler(masking_handler)
    
    logger.info(
        f"Log masking enabled for logger: {logger_name or 'root'}"
    )