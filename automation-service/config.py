"""
Configuration for Automation Service
Environment-driven configuration with sensible defaults
"""
import os
from typing import Optional


class Config:
    """Automation Service Configuration"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://opsconductor:opsconductor_secure_2024@postgres:5432/opsconductor"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # AI Pipeline Integration
    AI_PIPELINE_BASE_URL: str = os.getenv(
        "AI_PIPELINE_BASE_URL",
        "http://ai-pipeline:8000"
    )
    
    # Execution Timeouts
    EXEC_TIMEOUT_MS: int = int(os.getenv("EXEC_TIMEOUT_MS", "5000"))
    
    # Service Configuration
    SERVICE_NAME: str = "automation-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 3003
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_exec_timeout_seconds(cls) -> float:
        """Get execution timeout in seconds"""
        return cls.EXEC_TIMEOUT_MS / 1000.0


# Global config instance
config = Config()