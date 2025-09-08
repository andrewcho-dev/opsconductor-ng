"""
Workflow Export/Import Service
Handles exporting workflows to portable format and importing them with environment mapping
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ExportFormat(Enum):
    JSON = "json"
    YAML = "yaml"

class ImportStatus(Enum):
    PENDING = "pending"
    MAPPING_REQUIRED = "mapping_required" 
    VALIDATION_FAILED = "validation_failed"
    READY_TO_IMPORT = "ready_to_import"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TargetVariable:
    name: str
    type: str
    description: str
    required_capabilities: List[str]
    os_requirements: Optional[Dict[str, Any]] = None
    optional: bool = False

@dataclass
class ConfigVariable:
    name: str
    type: str
    default: Any
    description: str
    validation: Optional[Dict[str, Any]] = None

@dataclass
class ExportMetadata:
    name: str
    description: str
    version: str
    tags: List[str]
    created_at: datetime
    created_by: str
    exported_at: datetime
    exported_by: str
    source_system: str

class WorkflowExportService:
    def __init__(self, target_service, workflow_service, user_service):
        self.target_service = target_service
        self.workflow_service = workflow_service
        self.user_service = user_service
        
    def export_workflow(self, workflow_id: str, format: ExportFormat = ExportFormat.JSON) -> Dict[str, Any]:
        """Export a workflow to portable format"""
        
        # Get workflow definition
        workflow = self.workflow_service.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        # Extract target variables from workflow
        target_variables = self._extract_target_variables(workflow)
        
        # Extract configuration variables
        config_variables = self._extract_config_variables(workflow)
        
        # Create export structure
        export_data = {
            "workflow_export": {
                "format_version": "2.0",
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "exported_by": self.user_service.get_current_user().email,
                "source_system": self._get_system_identifier(),
                
                "metadata": ExportMetadata(
                    name=workflow.name,
                    description=workflow.description or "",
                    version=workflow.version or "1.0",
                    tags=workflow.tags or [],
                    created_at=workflow.created_at,
                    created_by=workflow.created_by,
                    exported_at=datetime.utcnow(),
                    exported_by=self.user_service.get_current_user().email,
                    source_system=self._get_system_identifier()
                ).__dict__,
                
                "requirements": self._generate_requirements(workflow),
                "target_variables": {tv.name: tv.__dict__ for tv in target_variables},
                "configuration_variables": {cv.name: cv.__dict__ for cv in config_variables},
                "workflow_definition": self._prepare_workflow_definition(workflow, target_variables, config_variables),
                "import_instructions": self._generate_import_instructions(workflow)
            }
        }
        
        return export_data
    
    def create_import_session(self, export_file_content: Dict[str, Any]) -> str:
        """Create an import session for mapping targets and configuration"""
        
        session_id = str(uuid.uuid4())
        export_data = export_file_content.get("workflow_export", {})
        
        # Validate export format
        if not self._validate_export_format(export_data):
            raise ValueError("Invalid export format")
            
        # Create mapping session
        session = {
            "session_id": session_id,
            "workflow_name": export_data["metadata"]["name"],
            "source_file": "imported_workflow.json",
            "import_status": ImportStatus.MAPPING_REQUIRED.value,
            "export_data": export_data,
            "target_mapping": self._create_target_mapping(export_data.get("target_variables", {})),
            "configuration_mapping": self._create_config_mapping(export_data.get("configuration_variables", {})),
            "validation_results": None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store session (in production, this would go to database)
        self._store_import_session(session_id, session)
        
        return session_id
    
    def update_import_mapping(self, session_id: str, target_mapping: Dict[str, str], config_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Update target and configuration mapping for import session"""
        
        session = self._get_import_session(session_id)
        if not session:
            raise ValueError(f"Import session {session_id} not found")
            
        # Update mappings
        session["target_mapping"] = self._update_target_mapping(session["target_mapping"], target_mapping)
        session["configuration_mapping"] = self._update_config_mapping(session["configuration_mapping"], config_mapping)
        
        # Validate mappings
        validation_results = self._validate_import_mappings(session)
        session["validation_results"] = validation_results
        
        # Update status based on validation
        if validation_results["overall_status"] == "ready_to_import":
            session["import_status"] = ImportStatus.READY_TO_IMPORT.value
        elif validation_results["issues"]:
            session["import_status"] = ImportStatus.VALIDATION_FAILED.value
        else:
            session["import_status"] = ImportStatus.MAPPING_REQUIRED.value
            
        self._store_import_session(session_id, session)
        
        return session
    
    def execute_import(self, session_id: str) -> str:
        """Execute the workflow import with mapped targets and configuration"""
        
        session = self._get_import_session(session_id)
        if not session:
            raise ValueError(f"Import session {session_id} not found")
            
        if session["import_status"] != ImportStatus.READY_TO_IMPORT.value:
            raise ValueError("Import session is not ready for import")
            
        try:
            session["import_status"] = ImportStatus.IMPORTING.value
            self._store_import_session(session_id, session)
            
            # Apply mappings to workflow definition
            workflow_def = self._apply_mappings_to_workflow(
                session["export_data"]["workflow_definition"],
                session["target_mapping"], 
                session["configuration_mapping"]
            )
            
            # Create new workflow
            new_workflow_id = self.workflow_service.create_workflow(workflow_def)
            
            session["import_status"] = ImportStatus.COMPLETED.value
            session["imported_workflow_id"] = new_workflow_id
            session["completed_at"] = datetime.utcnow().isoformat()
            
            self._store_import_session(session_id, session)
            
            return new_workflow_id
            
        except Exception as e:
            session["import_status"] = ImportStatus.FAILED.value
            session["error"] = str(e)
            session["failed_at"] = datetime.utcnow().isoformat()
            self._store_import_session(session_id, session)
            raise
    
    def _extract_target_variables(self, workflow: Dict[str, Any]) -> List[TargetVariable]:
        """Extract unique target references from workflow blocks"""
        target_vars = {}
        
        for block in workflow.get("blocks", []):
            config = block.get("config", {})
            target = config.get("target")
            
            if target and target not in target_vars:
                # Get target info from target service
                target_info = self.target_service.get_target(target)
                if target_info:
                    var_name = f"TARGET_{target.upper().replace('-', '_')}"
                    target_vars[var_name] = TargetVariable(
                        name=var_name,
                        type=target_info.type,
                        description=f"Target: {target_info.name}",
                        required_capabilities=target_info.capabilities,
                        os_requirements=target_info.os_info
                    )
        
        return list(target_vars.values())
    
    def _extract_config_variables(self, workflow: Dict[str, Any]) -> List[ConfigVariable]:
        """Extract configurable values from workflow blocks"""
        config_vars = {}
        
        # Common configurable fields to extract
        extractable_fields = {
            "service_name": {"type": "string", "description": "Service name"},
            "check_interval_sec": {"type": "integer", "description": "Check interval in seconds"},
            "timeout_seconds": {"type": "integer", "description": "Timeout in seconds"},
            "file_pattern": {"type": "string", "description": "File pattern to match"},
            "cron_expression": {"type": "string", "description": "Cron schedule expression"}
        }
        
        for block in workflow.get("blocks", []):
            config = block.get("config", {})
            for field, field_info in extractable_fields.items():
                if field in config:
                    var_name = f"{field.upper()}"
                    if var_name not in config_vars:
                        config_vars[var_name] = ConfigVariable(
                            name=var_name,
                            type=field_info["type"],
                            default=config[field],
                            description=field_info["description"]
                        )
        
        return list(config_vars.values())
    
    def _create_target_mapping(self, target_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Create target mapping structure with available targets"""
        mapping = {}
        
        for var_name, var_info in target_variables.items():
            available_targets = self.target_service.find_compatible_targets(
                required_capabilities=var_info.get("required_capabilities", []),
                os_requirements=var_info.get("os_requirements", {})
            )
            
            mapping[var_name] = {
                "variable_info": var_info,
                "available_targets": [self._target_to_dict(t) for t in available_targets],
                "selected_target": available_targets[0].id if available_targets else None,
                "mapping_status": "valid" if available_targets else "no_compatible_targets"
            }
            
        return mapping
    
    def _validate_import_mappings(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all mappings are correct and compatible"""
        issues = []
        warnings = []
        
        # Validate target mappings
        for var_name, mapping in session["target_mapping"].items():
            if not mapping["selected_target"] and not mapping["variable_info"].get("optional", False):
                issues.append({
                    "type": "missing_target",
                    "message": f"Required target variable '{var_name}' is not mapped",
                    "severity": "high"
                })
        
        # Validate configuration mappings
        for var_name, mapping in session["configuration_mapping"].items():
            if mapping["validation_status"] != "valid":
                issues.append({
                    "type": "invalid_configuration",
                    "message": f"Configuration variable '{var_name}' has invalid value",
                    "severity": "medium"
                })
        
        # Check platform requirements
        requirements_check = self._check_platform_requirements(session["export_data"].get("requirements", {}))
        
        overall_status = "ready_to_import" if not issues else "validation_failed"
        
        return {
            "overall_status": overall_status,
            "issues": issues,
            "warnings": warnings,
            "requirements_check": requirements_check
        }
    
    def _apply_mappings_to_workflow(self, workflow_def: Dict[str, Any], target_mapping: Dict[str, Any], config_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Apply target and configuration mappings to workflow definition"""
        
        # Create substitution maps
        target_substitutions = {}
        config_substitutions = {}
        
        for var_name, mapping in target_mapping.items():
            if mapping["selected_target"]:
                target_substitutions[f"{{{{TARGET_VARIABLES.{var_name}}}}}"] = mapping["selected_target"]
        
        for var_name, mapping in config_mapping.items():
            config_substitutions[f"{{{{CONFIG_VARIABLES.{var_name}}}}}"] = mapping["current_value"]
        
        # Apply substitutions to workflow definition
        workflow_json = json.dumps(workflow_def)
        
        for placeholder, value in {**target_substitutions, **config_substitutions}.items():
            workflow_json = workflow_json.replace(placeholder, str(value))
        
        return json.loads(workflow_json)
    
    # Helper methods for session management (would use database in production)
    def _store_import_session(self, session_id: str, session: Dict[str, Any]):
        """Store import session (placeholder - would use database)"""
        # In production: store in database
        pass
    
    def _get_import_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get import session (placeholder - would use database)"""
        # In production: retrieve from database
        return None
    
    def _get_system_identifier(self) -> str:
        """Get unique system identifier"""
        return "automation-system-01"  # Would be configurable
    
    def _generate_requirements(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Generate platform requirements for workflow"""
        return {
            "min_platform_version": "2.0.0",
            "required_features": ["service_monitoring", "target_management"],
            "required_permissions": ["service_control", "service_monitoring"]
        }
    
    def _generate_import_instructions(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Generate import instructions"""
        return {
            "steps": [
                "1. Verify platform version compatibility",
                "2. Map target variables to actual targets in your environment",
                "3. Configure notification settings", 
                "4. Review and adjust configuration variables",
                "5. Test workflow in safe environment before production use"
            ],
            "validation_required": [
                "target_capabilities",
                "service_permissions",
                "notification_endpoints"
            ]
        }