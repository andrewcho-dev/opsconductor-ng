#!/usr/bin/env python3
"""
Step Libraries Service - OpsConductor Microservice System
Manages modular, installable step libraries for the visual job builder

Features:
- Dynamic library installation/removal
- Version management and dependency resolution
- Performance-optimized lazy loading
- Security validation and sandboxing
- Premium addon support with licensing
- Hot-swappable libraries without restart
"""

import os
import json
import hashlib
import zipfile
import tempfile
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from pathlib import Path
import asyncio
import aiofiles
import sys
import traceback
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod

# Import shared modules
from .database import get_db_cursor, check_database_health, cleanup_database_pool, get_database_metrics
from .logging_config import setup_service_logging, get_logger, log_startup, log_shutdown
from .middleware import add_standard_middleware
from .models import HealthResponse, HealthCheck, create_success_response
from .errors import DatabaseError, ValidationError, NotFoundError, PermissionError, handle_database_error
from .auth import require_admin_role
from .utils import get_service_client

# Setup structured logging
setup_service_logging("step-libraries-service", level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("step-libraries-service")

# Database connection handled by shared module

# Library storage configuration
LIBRARIES_DIR = Path("/app/libraries")
CACHE_DIR = Path("/app/cache")
TEMP_DIR = Path("/app/temp")

# Ensure directories exist
for dir_path in [LIBRARIES_DIR, CACHE_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# MODELS & SCHEMAS
# =============================================================================

class StepParameter(BaseModel):
    """Step parameter definition"""
    type: str = Field(..., description="Parameter type (string, number, boolean, array, object)")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value")
    description: str = Field(default="", description="Parameter description")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    options: Optional[List[Any]] = Field(default=None, description="Allowed values for enum types")

class StepDefinition(BaseModel):
    """Individual step definition within a library"""
    name: str = Field(..., description="Step identifier (e.g., 'file.create')")
    display_name: str = Field(..., description="Human-readable step name")
    category: str = Field(..., description="Step category")
    description: str = Field(..., description="Step description")
    icon: str = Field(default="📄", description="Step icon")
    color: str = Field(default="#007bff", description="Step color")
    inputs: int = Field(default=1, description="Number of input ports")
    outputs: int = Field(default=1, description="Number of output ports")
    parameters: Dict[str, StepParameter] = Field(default_factory=dict, description="Step parameters")
    platform_support: List[str] = Field(default_factory=lambda: ["windows", "linux", "macos"], description="Supported platforms")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")
    tags: List[str] = Field(default_factory=list, description="Search tags")

class LibraryMetadata(BaseModel):
    """Library metadata and information"""
    name: str = Field(..., description="Library name")
    version: str = Field(..., description="Library version (semver)")
    display_name: str = Field(..., description="Human-readable library name")
    description: str = Field(..., description="Library description")
    author: str = Field(..., description="Library author")
    author_email: Optional[str] = Field(default=None, description="Author email")
    homepage: Optional[str] = Field(default=None, description="Library homepage")
    repository: Optional[str] = Field(default=None, description="Source repository")
    license: str = Field(default="MIT", description="Library license")
    categories: List[str] = Field(default_factory=list, description="Library categories")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    min_opsconductor_version: str = Field(default="1.0.0", description="Minimum OpsConductor version")
    is_premium: bool = Field(default=False, description="Whether library requires premium license")
    price: Optional[float] = Field(default=None, description="Library price (if premium)")
    trial_days: Optional[int] = Field(default=None, description="Trial period in days")

class LibraryInstallRequest(BaseModel):
    """Request to install a library"""
    source_type: str = Field(..., description="Installation source (upload, url, marketplace)")
    source_data: Dict[str, Any] = Field(..., description="Source-specific data")
    license_key: Optional[str] = Field(default=None, description="Premium license key")
    auto_enable: bool = Field(default=True, description="Enable library after installation")

class LibraryUpdateRequest(BaseModel):
    """Request to update a library"""
    library_id: int = Field(..., description="Library ID to update")
    version: Optional[str] = Field(default=None, description="Target version (latest if not specified)")
    force: bool = Field(default=False, description="Force update even if breaking changes")

class LibraryResponse(BaseModel):
    """Library information response"""
    id: int
    name: str
    version: str
    display_name: str
    description: str
    author: str
    is_enabled: bool
    is_premium: bool
    installation_date: datetime
    last_used: Optional[datetime]
    step_count: int
    status: str  # installed, enabled, disabled, error, updating

class StepLibraryBase(ABC):
    """Abstract base class for step libraries"""
    
    @abstractmethod
    def get_metadata(self) -> LibraryMetadata:
        """Return library metadata"""
        pass
    
    @abstractmethod
    def get_step_definitions(self) -> List[StepDefinition]:
        """Return all step definitions in this library"""
        pass
    
    @abstractmethod
    async def execute_step(self, step_name: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step from this library"""
        pass
    
    @abstractmethod
    async def validate_step(self, step_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step parameters"""
        pass

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

class DatabaseManager:
    """Handles all database operations for step libraries"""
    
    def __init__(self):
        self.connection_pool = None
    
    async def get_connection(self) -> Dict[str, Any]:
        """Get database connection"""
        # This method is deprecated - use get_db_cursor() directly
        pass
    
    async def create_library_record(self, metadata: LibraryMetadata, file_path: str, file_hash: str) -> int:
        """Create a new library record in database"""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO step_libraries (
                    name, version, display_name, description, author, author_email,
                    homepage, repository, license, categories, tags, dependencies,
                    min_opsconductor_version, is_premium, price, trial_days,
                    file_path, file_hash, is_enabled, installation_date, status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                metadata.name, metadata.version, metadata.display_name, metadata.description,
                metadata.author, metadata.author_email, metadata.homepage, metadata.repository,
                metadata.license, metadata.categories, metadata.tags, metadata.dependencies,
                metadata.min_opsconductor_version, metadata.is_premium, metadata.price,
                metadata.trial_days, file_path, file_hash, True, datetime.now(timezone.utc), 'installed'
            ))
            library_id = cur.fetchone()['id']
            return library_id
    
    async def create_step_records(self, library_id: int, steps: List[StepDefinition]) -> Dict[str, Any]:
        """Create step definition records"""
        with get_db_cursor() as cur:
            for step in steps:
                try:
                    # Convert StepParameter objects to dictionaries for JSON serialization
                    parameters_dict = {}
                    for param_name, param_obj in step.parameters.items():
                        logger.info(f"Processing parameter {param_name}, type: {type(param_obj)}")
                        if hasattr(param_obj, 'model_dump'):
                            parameters_dict[param_name] = param_obj.model_dump()
                            logger.info(f"Used model_dump for {param_name}")
                        elif hasattr(param_obj, 'dict'):
                            parameters_dict[param_name] = param_obj.dict()
                            logger.info(f"Used dict for {param_name}")
                        else:
                            parameters_dict[param_name] = param_obj
                            logger.info(f"Used raw object for {param_name}")
                    
                    logger.info(f"About to serialize parameters: {parameters_dict}")
                    json_test = json.dumps(parameters_dict)
                    logger.info(f"JSON serialization test successful")
                    
                    logger.info(f"Creating step record for {step.name}")
                    cur.execute("""
                        INSERT INTO library_steps (
                            library_id, name, display_name, category, description, icon, color,
                            inputs, outputs, parameters, platform_support, required_permissions,
                            examples, tags
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        library_id, step.name, step.display_name, step.category, step.description,
                        step.icon, step.color, step.inputs, step.outputs, 
                        json.dumps(parameters_dict), step.platform_support, step.required_permissions,
                        json.dumps(step.examples), step.tags
                    ))
                    logger.info(f"Successfully created step record for {step.name}")
                except Exception as e:
                    logger.error(f"Failed to create step record for {step.name}: {str(e)}")
                    raise
    
    async def get_libraries(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get all installed libraries"""
        with get_db_cursor(commit=False) as cur:
            query = "SELECT * FROM step_libraries"
            if enabled_only:
                query += " WHERE is_enabled = true"
            query += " ORDER BY display_name"
            
            cur.execute(query)
            return cur.fetchall()
    
    async def get_library_steps(self, library_id: int) -> List[Dict[str, Any]]:
        """Get all steps for a library"""
        with get_db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT s.*, l.is_enabled as library_enabled
                FROM library_steps s
                JOIN step_libraries l ON s.library_id = l.id
                WHERE s.library_id = %s
                ORDER BY s.category, s.display_name
            """, (library_id,))
            return cur.fetchall()
    
    async def toggle_library(self, library_id: int, enabled: bool) -> bool:
        """Enable or disable a library"""
        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE step_libraries 
                SET is_enabled = %s, last_updated = %s
                WHERE id = %s
            """, (enabled, datetime.now(timezone.utc), library_id))
            return cur.rowcount > 0
    
    async def delete_library(self, library_id: int) -> bool:
        """Delete a library and its steps"""
        with get_db_cursor() as cur:
            # Delete steps first (foreign key constraint)
            cur.execute("DELETE FROM library_steps WHERE library_id = %s", (library_id,))
            # Delete library
            cur.execute("DELETE FROM step_libraries WHERE id = %s", (library_id,))
            return cur.rowcount > 0

# =============================================================================
# LIBRARY MANAGER
# =============================================================================

class LibraryManager:
    """Manages step library lifecycle and execution"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.loaded_libraries: Dict[int, StepLibraryBase] = {}
        self.library_cache: Dict[str, Any] = {}
        self.performance_stats = {
            'libraries_loaded': 0,
            'steps_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def install_library_from_upload(self, file: UploadFile, license_key: Optional[str] = None) -> Dict[str, Any]:
        """Install library from uploaded file"""
        try:
            # Create temporary file
            temp_file = TEMP_DIR / f"upload_{datetime.now().timestamp()}.zip"
            
            # Save uploaded file
            async with aiofiles.open(temp_file, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Extract and validate library
            logger.info("Starting library extraction...")
            library_dir = await self._extract_library(temp_file)
            logger.info(f"Extracted library to {library_dir}")
            
            logger.info("Starting library validation...")
            metadata, steps = await self._validate_library(library_dir)
            logger.info(f"Validated library: {metadata.name} with {len(steps)} steps")
            
            # Debug: Check step parameters
            for i, step in enumerate(steps):
                logger.info(f"Step {i}: {step.name}, parameters: {len(step.parameters)}")
                for param_name, param_obj in step.parameters.items():
                    logger.info(f"  Parameter {param_name}: type={type(param_obj)}")
            
            # Check if library already exists
            existing = await self._check_existing_library(metadata.name, metadata.version)
            if existing:
                raise ValidationError(f"Library {metadata.name} v{metadata.version} already installed")
            
            # Validate premium license if required
            if metadata.is_premium and not license_key:
                raise ValidationError("Premium license key required")
            
            # Install library files
            final_path = LIBRARIES_DIR / f"{metadata.name}_{metadata.version}"
            final_path.mkdir(parents=True, exist_ok=True)
            
            # Copy library files
            await self._copy_library_files(library_dir, final_path)
            
            # Create database records
            logger.info(f"Creating library record for {metadata.name}")
            library_id = await self.db.create_library_record(metadata, str(final_path), file_hash)
            logger.info(f"Created library record with ID {library_id}")
            logger.info(f"Creating step records for {len(steps)} steps")
            await self.db.create_step_records(library_id, steps)
            logger.info(f"Created step records successfully")
            
            # Load library into memory
            await self._load_library(library_id, final_path)
            
            # Cleanup
            temp_file.unlink(missing_ok=True)
            
            logger.info(f"Successfully installed library {metadata.name} v{metadata.version}")
            
            return {
                'library_id': library_id,
                'name': metadata.name,
                'version': metadata.version,
                'step_count': len(steps),
                'status': 'installed'
            }
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            error_msg = f"Failed to install library: {str(e)}"
            logger.error(f"{error_msg}\nTraceback:\n{tb}")
            # Cleanup on failure
            if 'temp_file' in locals():
                temp_file.unlink(missing_ok=True)
            raise DatabaseError(f"Installation failed: {str(e)}")
    
    async def uninstall_library(self, library_id: int) -> Dict[str, Any]:
        """Uninstall a library"""
        try:
            # Get library info
            libraries = await self.db.get_libraries()
            library = next((l for l in libraries if l['id'] == library_id), None)
            if not library:
                raise NotFoundError("Library", library_id)
            
            # Remove from memory
            if library_id in self.loaded_libraries:
                del self.loaded_libraries[library_id]
            
            # Remove files
            library_path = Path(library['file_path'])
            if library_path.exists():
                import shutil
                shutil.rmtree(library_path, ignore_errors=True)
            
            # Remove from database
            await self.db.delete_library(library_id)
            
            logger.info(f"Successfully uninstalled library {library['name']} v{library['version']}")
            
            return {
                'library_id': library_id,
                'name': library['name'],
                'version': library['version'],
                'status': 'uninstalled'
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall library {library_id}: {str(e)}")
            raise DatabaseError(f"Uninstallation failed: {str(e)}")
    
    def _get_core_workflow_steps(self) -> List[Dict[str, Any]]:
        """Get core workflow steps that are always available"""
        return [
            {
                'id': 'core.flow.start',
                'name': 'Start',
                'type': 'flow.start',
                'category': 'Workflow',
                'library': 'core',
                'library_id': 0,
                'icon': '▶️',
                'description': 'Job start point - every job must begin with this step',
                'color': '#28a745',
                'inputs': 0,
                'outputs': 1,
                'parameters': {},
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['flow', 'start', 'workflow']
            },
            {
                'id': 'core.flow.end',
                'name': 'End',
                'type': 'flow.end',
                'category': 'Workflow',
                'library': 'core',
                'library_id': 0,
                'icon': '⏹️',
                'description': 'Job end point - marks successful completion of the job',
                'color': '#dc3545',
                'inputs': 1,
                'outputs': 0,
                'parameters': {},
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['flow', 'end', 'workflow']
            },
            {
                'id': 'core.flow.failure',
                'name': 'Failure',
                'type': 'flow.failure',
                'category': 'Workflow',
                'library': 'core',
                'library_id': 0,
                'icon': '❌',
                'description': 'Job failure termination - marks job as failed',
                'color': '#dc3545',
                'inputs': 1,
                'outputs': 0,
                'parameters': {
                    'error_message': {
                        'type': 'string',
                        'required': False,
                        'description': 'Optional error message to log',
                        'default': ''
                    }
                },
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['flow', 'failure', 'workflow', 'error']
            },
            {
                'id': 'core.target.assign',
                'name': 'Target Assignment',
                'type': 'target.assign',
                'category': 'Targets',
                'library': 'core',
                'library_id': 0,
                'icon': '🎯',
                'description': 'Assign job execution to specific targets',
                'color': '#007bff',
                'inputs': 1,
                'outputs': 1,
                'parameters': {
                    'target_names': {
                        'type': 'string',
                        'required': True,
                        'description': 'Target names (comma-separated) or target selection criteria',
                        'default': ''
                    },
                    'selection_mode': {
                        'type': 'string',
                        'required': False,
                        'description': 'How to select targets: specific, tag-based, or all',
                        'default': 'specific',
                        'options': ['specific', 'tag-based', 'all']
                    }
                },
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['target', 'assignment', 'selection']
            },
            {
                'id': 'core.logic.if',
                'name': 'If Condition',
                'type': 'logic.if',
                'category': 'Logic',
                'library': 'core',
                'library_id': 0,
                'icon': '🔀',
                'description': 'Conditional branching - execute different paths based on conditions',
                'color': '#ffc107',
                'inputs': 1,
                'outputs': 2,
                'parameters': {
                    'condition': {
                        'type': 'string',
                        'required': True,
                        'description': 'Condition to evaluate (e.g., $variable == "value")',
                        'default': ''
                    },
                    'condition_type': {
                        'type': 'string',
                        'required': False,
                        'description': 'Type of condition evaluation',
                        'default': 'expression',
                        'options': ['expression', 'variable_exists', 'file_exists', 'service_running']
                    }
                },
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['logic', 'condition', 'branching', 'if']
            },
            {
                'id': 'core.logic.switch',
                'name': 'Switch/Case',
                'type': 'logic.switch',
                'category': 'Logic',
                'library': 'core',
                'library_id': 0,
                'icon': '🔄',
                'description': 'Multi-way branching - route execution based on variable value',
                'color': '#ffc107',
                'inputs': 1,
                'outputs': 5,
                'parameters': {
                    'variable': {
                        'type': 'string',
                        'required': True,
                        'description': 'Variable to evaluate for switching',
                        'default': ''
                    },
                    'cases': {
                        'type': 'string',
                        'required': True,
                        'description': 'Comma-separated case values (e.g., "success,warning,error")',
                        'default': ''
                    }
                },
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['logic', 'switch', 'case', 'branching']
            },
            {
                'id': 'core.flow.parallel',
                'name': 'Parallel Execution',
                'type': 'flow.parallel',
                'category': 'Workflow',
                'library': 'core',
                'library_id': 0,
                'icon': '⚡',
                'description': 'Execute multiple branches in parallel',
                'color': '#17a2b8',
                'inputs': 1,
                'outputs': 3,
                'parameters': {
                    'wait_for_all': {
                        'type': 'boolean',
                        'required': False,
                        'description': 'Wait for all parallel branches to complete',
                        'default': True
                    },
                    'fail_on_any_error': {
                        'type': 'boolean',
                        'required': False,
                        'description': 'Fail the entire job if any parallel branch fails',
                        'default': True
                    }
                },
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['flow', 'parallel', 'concurrent', 'workflow']
            },
            {
                'id': 'core.flow.join',
                'name': 'Join/Merge',
                'type': 'flow.join',
                'category': 'Workflow',
                'library': 'core',
                'library_id': 0,
                'icon': '🔗',
                'description': 'Merge multiple execution paths back together',
                'color': '#17a2b8',
                'inputs': 3,
                'outputs': 1,
                'parameters': {},
                'platform_support': ['windows', 'linux', 'macos'],
                'required_permissions': [],
                'examples': [],
                'tags': ['flow', 'join', 'merge', 'workflow']
            }
        ]

    async def get_available_steps(self, category: Optional[str] = None, library_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all available steps with optional filtering"""
        logger.info(f"=== GET_AVAILABLE_STEPS CALLED: category={category}, library_name={library_name} ===")
        cache_key = f"steps_{category}_{library_name}"
        
        # Check cache first
        if cache_key in self.library_cache:
            self.performance_stats['cache_hits'] += 1
            return self.library_cache[cache_key]
        
        self.performance_stats['cache_misses'] += 1
        
        # Only use library steps (no more core steps)
        all_steps = []
        
        # Get enabled libraries
        libraries = await self.db.get_libraries(enabled_only=True)
        logger.info(f"Found {len(libraries)} enabled libraries")
        
        for library in libraries:
            logger.info(f"Processing library: {library['name']} (ID: {library['id']})")
            if library_name and library['name'] != library_name:
                continue
                
            steps = await self.db.get_library_steps(library['id'])
            logger.info(f"Found {len(steps)} steps for library {library['name']}")
            for step in steps:
                logger.info(f"Processing step: {step['name']}")
                if category and step['category'] != category:
                    continue
                
                # Convert to frontend format
                step_data = {
                    'id': f"{library['name']}.{step['name']}",
                    'name': step['display_name'],
                    'type': step['name'],
                    'category': step['category'],
                    'library': library['name'],
                    'library_id': library['id'],
                    'icon': step['icon'],
                    'description': step['description'],
                    'color': step['color'],
                    'inputs': step['inputs'],
                    'outputs': step['outputs'],
                    'parameters': step['parameters'] if step['parameters'] else {},
                    'platform_support': step['platform_support'],
                    'required_permissions': step['required_permissions'],
                    'examples': step['examples'] if step['examples'] else [],
                    'tags': step['tags']
                }
                all_steps.append(step_data)
        
        # Cache results
        self.library_cache[cache_key] = all_steps
        
        return all_steps
    
    async def _extract_library(self, zip_path: Path) -> Path:
        """Extract library zip file"""
        extract_dir = TEMP_DIR / f"extract_{datetime.now().timestamp()}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        return extract_dir
    
    async def _validate_library(self, library_dir: Path) -> tuple[LibraryMetadata, List[StepDefinition]]:
        """Validate library structure and load metadata"""
        # Check for required files
        manifest_file = library_dir / "manifest.json"
        if not manifest_file.exists():
            raise ValueError("Library manifest.json not found")
        
        # Load manifest
        async with aiofiles.open(manifest_file, 'r') as f:
            manifest_data = json.loads(await f.read())
        
        metadata = LibraryMetadata(**manifest_data['metadata'])
        
        # Load step definitions
        steps = []
        for step_data in manifest_data.get('steps', []):
            # Convert parameter dictionaries to StepParameter objects
            if 'parameters' in step_data:
                parameters = {}
                for param_name, param_dict in step_data['parameters'].items():
                    parameters[param_name] = StepParameter(**param_dict)
                step_data['parameters'] = parameters
            
            steps.append(StepDefinition(**step_data))
        
        return metadata, steps
    
    async def _check_existing_library(self, name: str, version: str) -> bool:
        """Check if library version already exists"""
        libraries = await self.db.get_libraries()
        return any(l['name'] == name and l['version'] == version for l in libraries)
    
    async def _copy_library_files(self, source: Path, destination: Path):
        """Copy library files to installation directory"""
        import shutil
        shutil.copytree(source, destination, dirs_exist_ok=True)
    
    async def _load_library(self, library_id: int, library_path: Path):
        """Load library into memory for execution"""
        try:
            # This would load the actual library implementation
            # For now, we'll create a placeholder
            self.loaded_libraries[library_id] = None
            self.performance_stats['libraries_loaded'] += 1
            
        except Exception as e:
            logger.error(f"Failed to load library {library_id}: {str(e)}")

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Global library manager
library_manager = LibraryManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    log_startup("step-libraries-service", "1.0.0", 3011)
    
    # Initialize any startup tasks here
    yield
    
    log_shutdown("step-libraries-service")
    cleanup_database_pool()

app = FastAPI(
    title="Step Libraries Service",
    description="Modular step library management for OpsConductor",
    version="1.0.0",
    lifespan=lifespan
)

# Add standard middleware
add_standard_middleware(app, "step-libraries-service", version="1.0.0")

# Helper functions for header-based authentication
def get_user_from_headers(request: Request):
    """Extract user info from nginx headers (set by gateway authentication)"""
    return {
        "id": request.headers.get("X-User-ID"),
        "username": request.headers.get("X-Username"),
        "email": request.headers.get("X-User-Email"),
        "role": request.headers.get("X-User-Role")
    }

# Auth is now handled at nginx gateway level - no internal auth checks needed

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    db_health = check_database_health()
    
    checks = [
        HealthCheck(
            name="database",
            status=db_health["status"],
            message=db_health.get("message", "Database connection check"),
            duration_ms=db_health.get("response_time_ms")
        ),
        HealthCheck(
            name="library_manager",
            status="healthy",
            message="Library manager operational"
        )
    ]
    
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        service="step-libraries-service",
        status=overall_status,
        version="1.0.0",
        checks=checks
    )

@app.get("/metrics/database")
async def database_metrics() -> Dict[str, Any]:
    """Database connection pool metrics endpoint"""
    metrics = get_database_metrics()
    return {
        "service": "step-libraries-service",
        "timestamp": datetime.utcnow().isoformat(),
        "database": metrics
    }

@app.get("/api/v1/libraries", response_model=List[LibraryResponse])
async def get_libraries(enabled_only: bool = False):
    """Get all installed libraries"""
    try:
        libraries = await library_manager.db.get_libraries(enabled_only=enabled_only)
        
        result = []
        for lib in libraries:
            steps = await library_manager.db.get_library_steps(lib['id'])
            
            result.append(LibraryResponse(
                id=lib['id'],
                name=lib['name'],
                version=lib['version'],
                display_name=lib['display_name'],
                description=lib['description'],
                author=lib['author'],
                is_enabled=lib['is_enabled'],
                is_premium=lib['is_premium'],
                installation_date=lib['installation_date'],
                last_used=lib.get('last_used'),
                step_count=len(steps),
                status=lib['status']
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get libraries: {str(e)}")
        raise DatabaseError(str(e))

@app.get("/api/v1/libraries/{library_id}")
async def get_library(library_id: int):
    """Get specific library details"""
    try:
        libraries = await library_manager.db.get_libraries()
        library = next((l for l in libraries if l['id'] == library_id), None)
        
        if not library:
            raise NotFoundError("Library not found")
        
        steps = await library_manager.db.get_library_steps(library_id)
        
        return {
            **dict(library),
            'steps': steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get library {library_id}: {str(e)}")
        raise DatabaseError(str(e))

@app.post("/api/v1/libraries/install")
async def install_library(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    license_key: Optional[str] = None
):
    """Install a new step library"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        result = await library_manager.install_library_from_upload(file, license_key)
        
        # Clear cache after installation
        library_manager.library_cache.clear()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Failed to install library: {str(e)}\nTraceback:\n{tb}")
        raise DatabaseError(str(e))

@app.delete("/api/v1/libraries/{library_id}")
async def uninstall_library(library_id: int, request: Request):
    """Uninstall a step library"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        result = await library_manager.uninstall_library(library_id)
        
        # Clear cache after uninstallation
        library_manager.library_cache.clear()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to uninstall library: {str(e)}")
        raise DatabaseError(str(e))

@app.put("/api/v1/libraries/{library_id}/toggle")
async def toggle_library(library_id: int, enabled: bool, request: Request):
    """Enable or disable a library"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        success = await library_manager.db.toggle_library(library_id, enabled)
        
        if not success:
            raise NotFoundError("Library", library_id)
        
        # Clear cache after toggle
        library_manager.library_cache.clear()
        
        return {
            'library_id': library_id,
            'enabled': enabled,
            'status': 'success'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle library {library_id}: {str(e)}")
        raise DatabaseError(str(e))

@app.get("/api/v1/steps")
async def get_available_steps(
    category: Optional[str] = None,
    library: Optional[str] = None,
    platform: Optional[str] = None
):
    """Get all available steps with optional filtering"""
    try:
        steps = await library_manager.get_available_steps(category, library)
        
        # Filter by platform if specified
        if platform:
            steps = [s for s in steps if platform in s.get('platform_support', [])]
        
        return {
            'steps': steps,
            'total_count': len(steps),
            'categories': list(set(s['category'] for s in steps)),
            'libraries': list(set(s['library'] for s in steps))
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Failed to get steps: {str(e)}\nTraceback:\n{tb}")
        raise DatabaseError(str(e))

@app.get("/api/v1/debug/steps")
async def debug_steps() -> Dict[str, Any]:
    """Debug endpoint to check raw step data"""
    try:
        libraries = await library_manager.db.get_libraries(enabled_only=True)
        result = []
        for library in libraries:
            steps = await library_manager.db.get_library_steps(library['id'])
            result.append({
                'library': library['name'],
                'step_count': len(steps),
                'steps': [{'name': s['name'], 'parameters_type': type(s['parameters']).__name__} for s in steps]
            })
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Debug steps failed: {str(e)}\nTraceback:\n{tb}")
        return {"error": str(e), "traceback": tb}

@app.get("/api/v1/performance")
async def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    return {
        'stats': library_manager.performance_stats,
        'cache_size': len(library_manager.library_cache),
        'loaded_libraries': len(library_manager.loaded_libraries),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/v1/install-generic-blocks")
async def install_generic_blocks(request: Request) -> Dict[str, Any]:
    """Install the built-in generic blocks library"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    try:
        from generic_blocks_library import create_generic_blocks_library
        
        # Create the generic blocks library
        generic_library = create_generic_blocks_library()
        
        # Get metadata and steps
        metadata = generic_library.get_metadata()
        step_definitions = generic_library.get_step_definitions()
        
        # Check if already installed
        libraries = await library_manager.db.get_libraries()
        existing = next((lib for lib in libraries if lib['name'] == metadata.name), None)
        
        if existing:
            return {
                "success": True,
                "message": "Generic blocks library already installed",
                "library_id": existing['id'],
                "step_count": len(step_definitions)
            }
        
        # Create library record
        library_id = await library_manager.db.create_library_record(
            metadata=metadata,
            file_path="built-in://generic-blocks",
            file_hash="generic-blocks-v1.0.0"
        )
        
        # Create step records
        await library_manager.db.create_step_records(library_id, step_definitions)
        
        # Clear cache to force reload
        library_manager.library_cache.clear()
        
        logger.info(f"Generic blocks library installed with ID {library_id}, {len(step_definitions)} steps")
        
        return {
            "success": True,
            "message": "Generic blocks library installed successfully",
            "library_id": library_id,
            "step_count": len(step_definitions),
            "steps": [step.name for step in step_definitions]
        }
        
    except Exception as e:
        logger.error(f"Failed to install generic blocks library: {str(e)}")
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Traceback:\n{tb}")
        raise DatabaseError(f"Failed to install generic blocks: {str(e)}")

@app.post("/api/v1/cache/clear")
async def clear_cache(request: Request) -> Dict[str, Any]:
    """Clear the step library cache"""
    # Check admin/operator role
    # Auth handled at nginx gateway level
    library_manager.library_cache.clear()
    return {
        'status': 'success',
        'message': 'Cache cleared',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/analytics/usage")
async def get_usage_analytics() -> Dict[str, Any]:
    """Get usage analytics and database integration status"""
    try:
        libraries = await library_manager.db.get_libraries()
        total_steps = 0
        
        for lib in libraries:
            steps = await library_manager.db.get_library_steps(lib['id'])
            total_steps += len(steps)
        
        return {
            'status': 'connected',
            'total_libraries': len(libraries),
            'total_steps': total_steps,
            'performance_stats': library_manager.performance_stats,
            'cache_stats': {
                'cache_size': len(library_manager.library_cache),
                'loaded_libraries': len(library_manager.loaded_libraries)
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}")
        raise DatabaseError(str(e))

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3011,
        reload=True,
        log_level="info"
    )