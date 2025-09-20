"""
Job Validation Engine - Comprehensive validation for AI-generated jobs

This module provides multi-layer validation for jobs before creation:
1. Requirement completeness validation
2. Asset compatibility validation  
3. Command syntax validation
4. Security and safety validation
5. Permission and privilege validation
"""

import logging
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from integrations.asset_client import AssetServiceClient

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationType(Enum):
    """Types of validation checks"""
    REQUIREMENTS = "requirements"
    SYNTAX = "syntax"
    COMPATIBILITY = "compatibility"
    SECURITY = "security"
    PERMISSIONS = "permissions"

@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    type: ValidationType
    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    field: Optional[str] = None
    details: Dict[str, Any] = None

@dataclass
class ValidationResult:
    """Result of job validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    missing_requirements: List[str]
    clarification_questions: List[Dict[str, Any]]
    confidence_score: float
    field_confidence_scores: Dict[str, Dict[str, Any]] = None  # Field-level confidence details
    risk_assessment: Dict[str, Any] = None  # Risk assessment based on field confidence
    
    def has_critical_issues(self) -> bool:
        return any(issue.level == ValidationLevel.CRITICAL for issue in self.issues)
    
    def has_errors(self) -> bool:
        return any(issue.level == ValidationLevel.ERROR for issue in self.issues)
    
    def get_issues_by_type(self, validation_type: ValidationType) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.type == validation_type]

class JobValidator:
    """Comprehensive job validation engine"""
    
    def __init__(self):
        self.asset_client = AssetServiceClient()
        self.dangerous_commands = {
            'windows': [
                'format', 'del /s', 'rmdir /s', 'rd /s', 'diskpart', 'fdisk',
                'shutdown /s', 'shutdown /r', 'net user', 'net localgroup',
                'reg delete', 'bcdedit', 'sfc /scannow'
            ],
            'linux': [
                'rm -rf', 'mkfs', 'fdisk', 'parted', 'dd if=', 'shutdown',
                'reboot', 'halt', 'init 0', 'init 6', 'userdel', 'groupdel',
                'chmod 777', 'chown -R'
            ]
        }
        
    async def validate_job_request(
        self,
        intent_type: str,
        requirements: Dict[str, Any],
        target_systems: List[str],
        workflow_steps: List[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of job request
        
        Args:
            intent_type: Type of intent/operation
            requirements: Extracted requirements
            target_systems: Target systems for execution
            workflow_steps: Generated workflow steps (optional)
            
        Returns:
            ValidationResult with all validation findings
        """
        issues = []
        missing_requirements = []
        clarification_questions = []
        
        try:
            # 1. Validate requirements completeness
            req_issues, req_missing, req_questions = await self._validate_requirements(
                intent_type, requirements
            )
            issues.extend(req_issues)
            missing_requirements.extend(req_missing)
            clarification_questions.extend(req_questions)
            
            # 2. Validate target system compatibility
            if target_systems:
                compat_issues, compat_questions = await self._validate_compatibility(
                    target_systems, requirements
                )
                issues.extend(compat_issues)
                clarification_questions.extend(compat_questions)
            
            # 3. Validate command syntax and safety
            if workflow_steps:
                syntax_issues = await self._validate_command_syntax(workflow_steps, target_systems)
                issues.extend(syntax_issues)
                
                security_issues = await self._validate_security(workflow_steps, requirements)
                issues.extend(security_issues)
            
            # 4. Calculate confidence score with field-level details
            confidence_score, field_scores = self._calculate_confidence_score(
                issues, missing_requirements, intent_type, requirements
            )
            
            # 5. Generate targeted clarification questions based on field confidence
            targeted_questions = self.generate_targeted_clarification_questions(
                field_scores, intent_type, requirements
            )
            
            # Combine traditional and targeted clarification questions
            all_clarification_questions = clarification_questions + targeted_questions
            
            # 6. Generate risk assessment
            risk_assessment = self.generate_risk_assessment(field_scores, confidence_score)
            
            # 7. Determine if job is valid
            is_valid = (
                not any(issue.level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR] for issue in issues) and
                confidence_score >= 0.6
            )
            
            return ValidationResult(
                is_valid=is_valid,
                issues=issues,
                missing_requirements=missing_requirements,
                clarification_questions=all_clarification_questions,
                confidence_score=confidence_score,
                field_confidence_scores=field_scores,
                risk_assessment=risk_assessment
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    type=ValidationType.REQUIREMENTS,
                    level=ValidationLevel.CRITICAL,
                    message=f"Validation system error: {str(e)}"
                )],
                missing_requirements=[],
                clarification_questions=[],
                confidence_score=0.0,
                field_confidence_scores={},
                risk_assessment={
                    'overall_confidence': 0.0,
                    'risk_level': 'CRITICAL',
                    'recommendation': 'System error - cannot proceed',
                    'critical_issues': [{'message': 'Validation system error', 'impact': 'Cannot validate job'}],
                    'warnings': [],
                    'can_proceed': False,
                    'should_clarify': True
                }
            )
    
    async def _validate_requirements(
        self,
        intent_type: str,
        requirements: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], List[str], List[Dict[str, Any]]]:
        """Validate requirement completeness"""
        issues = []
        missing = []
        questions = []
        
        # Define required fields per intent type
        required_fields = {
            'automation_request': ['description'],
            'system_maintenance': ['target_systems', 'operation'],
            'service_management': ['target_systems', 'service_name', 'action'],
            'file_operations': ['target_systems', 'file_path', 'operation'],
            'user_management': ['target_systems', 'username', 'action'],
            'information_gathering': ['target_systems'],
            'troubleshooting': ['target_systems', 'problem_description']
        }
        
        intent_requirements = required_fields.get(intent_type, ['description'])
        
        for field in intent_requirements:
            if field not in requirements or not requirements[field]:
                missing.append(field)
                
                # Generate clarification question
                question = self._generate_clarification_question(field, intent_type)
                if question:
                    questions.append(question)
                
                issues.append(ValidationIssue(
                    type=ValidationType.REQUIREMENTS,
                    level=ValidationLevel.ERROR,
                    message=f"Missing required field: {field}",
                    suggestion=f"Please provide {field.replace('_', ' ')}",
                    field=field
                ))
        
        # Validate specific field formats
        if 'target_systems' in requirements:
            targets = requirements['target_systems']
            if isinstance(targets, list) and len(targets) == 0:
                issues.append(ValidationIssue(
                    type=ValidationType.REQUIREMENTS,
                    level=ValidationLevel.ERROR,
                    message="No target systems specified",
                    suggestion="Please specify at least one target system"
                ))
        
        return issues, missing, questions
    
    async def _validate_compatibility(
        self,
        target_systems: List[str],
        requirements: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], List[Dict[str, Any]]]:
        """Validate target system compatibility"""
        issues = []
        questions = []
        
        try:
            # Get asset information for target systems
            for target in target_systems:
                try:
                    asset_info = await self.asset_client.get_asset_by_hostname(target)
                    if not asset_info:
                        issues.append(ValidationIssue(
                            type=ValidationType.COMPATIBILITY,
                            level=ValidationLevel.WARNING,
                            message=f"Target system '{target}' not found in asset database",
                            suggestion="Verify the hostname is correct"
                        ))
                        continue
                    
                    # Validate OS compatibility
                    os_type = asset_info.get('os_type', '').lower()
                    operation = requirements.get('operation', '')
                    
                    if self._is_windows_specific_operation(operation) and 'windows' not in os_type:
                        issues.append(ValidationIssue(
                            type=ValidationType.COMPATIBILITY,
                            level=ValidationLevel.ERROR,
                            message=f"Windows-specific operation '{operation}' cannot run on {os_type}",
                            suggestion="Use a Linux/Unix equivalent command or target Windows systems"
                        ))
                    
                    if self._is_linux_specific_operation(operation) and 'linux' not in os_type and 'unix' not in os_type:
                        issues.append(ValidationIssue(
                            type=ValidationType.COMPATIBILITY,
                            level=ValidationLevel.ERROR,
                            message=f"Linux-specific operation '{operation}' cannot run on {os_type}",
                            suggestion="Use a Windows equivalent command or target Linux systems"
                        ))
                        
                except Exception as e:
                    logger.warning(f"Could not validate compatibility for {target}: {e}")
                    issues.append(ValidationIssue(
                        type=ValidationType.COMPATIBILITY,
                        level=ValidationLevel.WARNING,
                        message=f"Could not verify compatibility for '{target}'",
                        suggestion="Ensure the target system is accessible"
                    ))
        
        except Exception as e:
            logger.error(f"Compatibility validation failed: {e}")
            issues.append(ValidationIssue(
                type=ValidationType.COMPATIBILITY,
                level=ValidationLevel.WARNING,
                message="Could not perform compatibility validation",
                suggestion="Proceed with caution"
            ))
        
        return issues, questions
    
    async def _validate_command_syntax(
        self,
        workflow_steps: List[Dict[str, Any]],
        target_systems: List[str]
    ) -> List[ValidationIssue]:
        """Validate command syntax for target platforms"""
        issues = []
        
        for step in workflow_steps:
            command = step.get('command', '')
            script = step.get('script', '')
            
            if command:
                syntax_issues = await self._validate_single_command(command, target_systems)
                issues.extend(syntax_issues)
            
            if script:
                syntax_issues = await self._validate_script_syntax(script, target_systems)
                issues.extend(syntax_issues)
        
        return issues
    
    async def _validate_single_command(
        self,
        command: str,
        target_systems: List[str]
    ) -> List[ValidationIssue]:
        """Validate syntax of a single command"""
        issues = []
        
        # Detect shell type based on command patterns
        if self._is_powershell_command(command):
            issues.extend(self._validate_powershell_syntax(command))
        elif self._is_bash_command(command):
            issues.extend(self._validate_bash_syntax(command))
        else:
            # Try to infer from target systems
            for target in target_systems:
                try:
                    asset_info = await self.asset_client.get_asset_by_hostname(target)
                    if asset_info:
                        os_type = asset_info.get('os_type', '').lower()
                        if 'windows' in os_type:
                            issues.extend(self._validate_powershell_syntax(command))
                        else:
                            issues.extend(self._validate_bash_syntax(command))
                        break
                except:
                    continue
        
        return issues
    
    def _validate_powershell_syntax(self, command: str) -> List[ValidationIssue]:
        """Validate PowerShell command syntax"""
        issues = []
        
        # Check for common PowerShell syntax errors
        if '&&' in command:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Invalid PowerShell syntax: '&&' is not supported",
                suggestion="Use ';' to chain commands in PowerShell instead of '&&'"
            ))
        
        if '||' in command:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Invalid PowerShell syntax: '||' is not supported",
                suggestion="Use PowerShell conditional logic instead of '||'"
            ))
        
        # Check for unmatched quotes
        single_quotes = command.count("'")
        double_quotes = command.count('"')
        
        if single_quotes % 2 != 0:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Unmatched single quotes in PowerShell command",
                suggestion="Ensure all single quotes are properly paired"
            ))
        
        if double_quotes % 2 != 0:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Unmatched double quotes in PowerShell command",
                suggestion="Ensure all double quotes are properly paired"
            ))
        
        return issues
    
    def _validate_bash_syntax(self, command: str) -> List[ValidationIssue]:
        """Validate Bash command syntax"""
        issues = []
        
        # Check for unmatched quotes
        single_quotes = command.count("'")
        double_quotes = command.count('"')
        
        if single_quotes % 2 != 0:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Unmatched single quotes in Bash command",
                suggestion="Ensure all single quotes are properly paired"
            ))
        
        if double_quotes % 2 != 0:
            issues.append(ValidationIssue(
                type=ValidationType.SYNTAX,
                level=ValidationLevel.ERROR,
                message="Unmatched double quotes in Bash command",
                suggestion="Ensure all double quotes are properly paired"
            ))
        
        # Check for dangerous patterns
        if re.search(r'rm\s+-rf\s+/', command):
            issues.append(ValidationIssue(
                type=ValidationType.SECURITY,
                level=ValidationLevel.CRITICAL,
                message="Potentially dangerous command: 'rm -rf /' detected",
                suggestion="This command could delete system files. Please be more specific with paths."
            ))
        
        return issues
    
    async def _validate_security(
        self,
        workflow_steps: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate security aspects of commands"""
        issues = []
        
        for step in workflow_steps:
            command = step.get('command', '')
            script = step.get('script', '')
            
            # Check for dangerous commands
            for os_type, dangerous_cmds in self.dangerous_commands.items():
                for dangerous_cmd in dangerous_cmds:
                    if dangerous_cmd.lower() in command.lower() or dangerous_cmd.lower() in script.lower():
                        issues.append(ValidationIssue(
                            type=ValidationType.SECURITY,
                            level=ValidationLevel.WARNING,
                            message=f"Potentially dangerous command detected: '{dangerous_cmd}'",
                            suggestion="This command requires careful review and may need approval"
                        ))
        
        return issues
    
    def _generate_clarification_question(self, field: str, intent_type: str) -> Optional[Dict[str, Any]]:
        """Generate clarification questions for missing fields"""
        questions = {
            'target_systems': {
                'question': 'Which systems should this operation target?',
                'options': ['All servers', 'Web servers', 'Database servers', 'Specific hostname'],
                'type': 'single_choice'
            },
            'service_name': {
                'question': 'Which service do you want to manage?',
                'options': ['IIS', 'Apache', 'SQL Server', 'MySQL', 'Custom service'],
                'type': 'single_choice'
            },
            'action': {
                'question': 'What action should be performed?',
                'options': ['Start', 'Stop', 'Restart', 'Status check'],
                'type': 'single_choice'
            },
            'operation': {
                'question': 'What operation do you want to perform?',
                'options': ['Install', 'Update', 'Configure', 'Monitor'],
                'type': 'single_choice'
            }
        }
        
        return questions.get(field)
    
    def generate_targeted_clarification_questions(
        self,
        field_confidence_scores: Dict[str, Dict[str, Any]],
        intent_type: str,
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate targeted clarification questions based on field confidence scores"""
        questions = []
        
        # Sort fields by criticality (weight) and confidence (lowest first)
        sorted_fields = sorted(
            field_confidence_scores.items(),
            key=lambda x: (x[1]['weight'], -x[1]['confidence']),  # High weight, low confidence first
            reverse=True
        )
        
        for field, field_info in sorted_fields:
            confidence = field_info['confidence']
            weight = field_info['weight']
            
            # Generate questions for low-confidence critical fields
            if confidence < 0.7 and weight >= 0.2:  # Critical fields with low confidence
                question = self._generate_targeted_question(field, confidence, intent_type, requirements)
                if question:
                    questions.append(question)
        
        return questions
    
    def _generate_targeted_question(
        self,
        field: str,
        confidence: float,
        intent_type: str,
        requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a targeted question based on field confidence and current value"""
        current_value = requirements.get(field)
        
        # Determine the specific issue with this field
        if current_value is None or current_value == "":
            # Field is completely missing
            return self._generate_missing_field_question(field, intent_type)
        else:
            # Field exists but has low confidence (vague/unclear)
            return self._generate_clarification_field_question(field, current_value, confidence, intent_type)
    
    def _generate_missing_field_question(self, field: str, intent_type: str) -> Dict[str, Any]:
        """Generate questions for completely missing fields"""
        questions = {
            'target_systems': {
                'question': 'Which systems should this operation target?',
                'explanation': 'I need to know which servers or systems to run this operation on.',
                'options': ['All production servers', 'Web servers only', 'Database servers only', 'Specific hostname(s)'],
                'type': 'single_choice',
                'priority': 'critical',
                'field': field
            },
            'service_name': {
                'question': 'Which specific service do you want to manage?',
                'explanation': 'I need the exact service name to perform the requested action.',
                'options': ['Apache HTTP Server', 'IIS', 'MySQL', 'SQL Server', 'Custom service (specify name)'],
                'type': 'single_choice',
                'priority': 'critical',
                'field': field
            },
            'action': {
                'question': 'What specific action should be performed on the service?',
                'explanation': 'I need to know exactly what you want to do with the service.',
                'options': ['Start', 'Stop', 'Restart', 'Check status', 'Reload configuration'],
                'type': 'single_choice',
                'priority': 'critical',
                'field': field
            },
            'operation': {
                'question': 'What type of operation do you want to perform?',
                'explanation': 'I need to understand the specific operation you want to execute.',
                'options': ['Install software', 'Update/upgrade', 'Configure settings', 'Monitor/check status'],
                'type': 'single_choice',
                'priority': 'critical',
                'field': field
            },
            'file_path': {
                'question': 'What is the specific file or directory path?',
                'explanation': 'I need the exact path to the file or directory you want to work with.',
                'type': 'text_input',
                'placeholder': 'e.g., /etc/apache2/apache2.conf or C:\\inetpub\\wwwroot\\web.config',
                'priority': 'critical',
                'field': field
            },
            'username': {
                'question': 'What is the specific username?',
                'explanation': 'I need the exact username for the user management operation.',
                'type': 'text_input',
                'placeholder': 'e.g., john.doe or admin',
                'priority': 'critical',
                'field': field
            }
        }
        
        return questions.get(field, {
            'question': f'Please provide the {field.replace("_", " ")}',
            'explanation': f'This information is required to create the automation job.',
            'type': 'text_input',
            'priority': 'high',
            'field': field
        })
    
    def _generate_clarification_field_question(
        self,
        field: str,
        current_value: Any,
        confidence: float,
        intent_type: str
    ) -> Dict[str, Any]:
        """Generate clarification questions for vague/unclear field values"""
        
        if field == 'target_systems':
            if isinstance(current_value, list) and len(current_value) == 1:
                value = current_value[0]
            else:
                value = str(current_value)
                
            if confidence < 0.5:
                return {
                    'question': f'You mentioned "{value}" as the target. Can you be more specific?',
                    'explanation': 'Vague target specifications can lead to unintended consequences. Please provide specific hostnames or server groups.',
                    'options': [
                        'Provide specific hostname(s)',
                        'All servers in a specific environment (prod/staging/dev)',
                        'Servers with a specific role (web/db/app)',
                        'Keep current target (proceed with risk)'
                    ],
                    'type': 'single_choice',
                    'priority': 'high',
                    'field': field,
                    'risk_warning': 'Proceeding with vague targets may affect unintended systems.'
                }
            else:
                return {
                    'question': f'Please confirm the target systems: "{value}"',
                    'explanation': 'I want to make sure I understand the target correctly.',
                    'options': ['Confirmed, proceed', 'Let me be more specific'],
                    'type': 'single_choice',
                    'priority': 'medium',
                    'field': field
                }
        
        elif field == 'service_name':
            return {
                'question': f'You mentioned "{current_value}" as the service. Can you provide the exact service name?',
                'explanation': 'Service names must be exact for automation to work correctly.',
                'type': 'text_input',
                'placeholder': 'e.g., httpd, apache2, w3svc, mysql',
                'priority': 'high',
                'field': field,
                'risk_warning': 'Incorrect service names will cause the automation to fail.'
            }
        
        elif field == 'action':
            return {
                'question': f'You mentioned "{current_value}". What specific action do you want?',
                'explanation': 'I need a precise action to ensure the automation works correctly.',
                'options': ['Start', 'Stop', 'Restart', 'Reload', 'Status check', 'Enable', 'Disable'],
                'type': 'single_choice',
                'priority': 'high',
                'field': field
            }
        
        # Generic clarification for other fields
        return {
            'question': f'Can you clarify "{current_value}" for {field.replace("_", " ")}?',
            'explanation': f'The current value seems unclear and may lead to unexpected results.',
            'type': 'text_input',
            'priority': 'medium',
            'field': field,
            'risk_warning': f'Unclear {field.replace("_", " ")} may cause automation issues.'
        }
    
    def generate_risk_assessment(
        self,
        field_confidence_scores: Dict[str, Dict[str, Any]],
        overall_confidence: float
    ) -> Dict[str, Any]:
        """Generate risk assessment based on field confidence scores"""
        
        risks = []
        critical_issues = []
        warnings = []
        
        # Analyze each field for risks
        for field, field_info in field_confidence_scores.items():
            confidence = field_info['confidence']
            weight = field_info['weight']
            
            if confidence < 0.5 and weight >= 0.25:  # Critical field with very low confidence
                critical_issues.append({
                    'field': field,
                    'confidence': confidence,
                    'weight': weight,
                    'message': f'{field.replace("_", " ").title()} is unclear or missing',
                    'impact': 'Job may fail or produce unexpected results'
                })
            elif confidence < 0.7 and weight >= 0.2:  # Important field with low confidence
                warnings.append({
                    'field': field,
                    'confidence': confidence,
                    'weight': weight,
                    'message': f'{field.replace("_", " ").title()} needs clarification',
                    'impact': 'Results may not match expectations'
                })
        
        # Overall risk level
        if overall_confidence < 0.4:
            risk_level = 'HIGH'
            recommendation = 'Strongly recommend providing more information before proceeding'
        elif overall_confidence < 0.6:
            risk_level = 'MEDIUM'
            recommendation = 'Consider providing more details for better results'
        elif overall_confidence < 0.8:
            risk_level = 'LOW'
            recommendation = 'Job should work, but clarification could improve accuracy'
        else:
            risk_level = 'MINIMAL'
            recommendation = 'Job appears well-defined and ready to execute'
        
        return {
            'overall_confidence': overall_confidence,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'can_proceed': overall_confidence >= 0.3,  # Minimum threshold to attempt job creation
            'should_clarify': overall_confidence < 0.7   # Recommend clarification below this threshold
        }
    
    def _is_powershell_command(self, command: str) -> bool:
        """Detect if command is PowerShell"""
        powershell_indicators = [
            'Get-', 'Set-', 'New-', 'Remove-', 'Start-', 'Stop-',
            '$_', '$PSVersionTable', 'Write-Host', 'Write-Output'
        ]
        return any(indicator in command for indicator in powershell_indicators)
    
    def _is_bash_command(self, command: str) -> bool:
        """Detect if command is Bash"""
        bash_indicators = ['#!/bin/bash', 'echo', 'grep', 'awk', 'sed', 'ps aux']
        return any(indicator in command for indicator in bash_indicators)
    
    def _is_windows_specific_operation(self, operation: str) -> bool:
        """Check if operation is Windows-specific"""
        windows_ops = ['iis', 'registry', 'windows service', 'powershell', 'wmic']
        return any(op in operation.lower() for op in windows_ops)
    
    def _is_linux_specific_operation(self, operation: str) -> bool:
        """Check if operation is Linux-specific"""
        linux_ops = ['systemctl', 'service', 'crontab', 'iptables', 'yum', 'apt']
        return any(op in operation.lower() for op in linux_ops)
    
    def _calculate_confidence_score(
        self,
        issues: List[ValidationIssue],
        missing_requirements: List[str],
        intent_type: str,
        requirements: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Dict[str, Any]]]:
        """Calculate granular confidence score based on field completeness and validation results"""
        
        # Get required fields for this intent type
        required_fields = self._get_required_fields(intent_type)
        
        if not required_fields:
            return 0.5  # Unknown intent type gets medium confidence
        
        # Calculate field-level confidence scores
        field_scores = {}
        total_weight = 0
        
        for field in required_fields:
            field_info = self._get_field_requirements(field, intent_type)
            weight = field_info['weight']
            total_weight += weight
            
            # Calculate confidence for this specific field
            field_confidence = self._calculate_field_confidence(
                field, requirements.get(field), field_info, issues
            )
            field_scores[field] = {
                'confidence': field_confidence,
                'weight': weight,
                'weighted_score': field_confidence * weight
            }
        
        # Calculate weighted average confidence
        if total_weight == 0:
            base_confidence = 0.0
        else:
            base_confidence = sum(score['weighted_score'] for score in field_scores.values()) / total_weight
        
        # Apply global penalties for critical issues
        global_penalty = 0.0
        for issue in issues:
            if issue.level == ValidationLevel.CRITICAL:
                global_penalty += 0.3  # Critical issues significantly impact confidence
            elif issue.level == ValidationLevel.ERROR and not issue.field:
                # Global errors (not field-specific)
                global_penalty += 0.15
        
        final_confidence = max(0.0, min(1.0, base_confidence - global_penalty))
        
        return final_confidence, field_scores
    
    def _get_required_fields(self, intent_type: str) -> List[str]:
        """Get required fields for intent type with criticality levels"""
        required_fields = {
            'automation_request': ['description', 'target_systems'],
            'system_maintenance': ['target_systems', 'operation'],
            'service_management': ['target_systems', 'service_name', 'action'],
            'file_operations': ['target_systems', 'file_path', 'operation'],
            'user_management': ['target_systems', 'username', 'action'],
            'information_gathering': ['target_systems'],
            'troubleshooting': ['target_systems', 'problem_description'],
            'process_management': ['target_systems', 'process_name', 'action'],
            'network_operations': ['target_systems', 'network_config', 'operation']
        }
        
        return required_fields.get(intent_type, ['description'])
    
    def _get_field_requirements(self, field: str, intent_type: str) -> Dict[str, Any]:
        """Get detailed requirements for a specific field"""
        
        # Define field criticality and validation rules
        field_requirements = {
            'target_systems': {
                'weight': 0.3,  # 30% of total confidence
                'critical': True,
                'min_specificity': 0.7,  # How specific the target needs to be
                'validation_rules': ['not_empty', 'valid_format', 'exists_in_assets']
            },
            'service_name': {
                'weight': 0.25,
                'critical': True,
                'min_specificity': 0.8,
                'validation_rules': ['not_empty', 'known_service', 'os_compatible']
            },
            'action': {
                'weight': 0.2,
                'critical': True,
                'min_specificity': 0.9,
                'validation_rules': ['not_empty', 'valid_action', 'service_compatible']
            },
            'operation': {
                'weight': 0.25,
                'critical': True,
                'min_specificity': 0.8,
                'validation_rules': ['not_empty', 'valid_operation', 'os_compatible']
            },
            'description': {
                'weight': 0.15,
                'critical': False,
                'min_specificity': 0.6,
                'validation_rules': ['not_empty', 'sufficient_detail']
            },
            'file_path': {
                'weight': 0.25,
                'critical': True,
                'min_specificity': 0.9,
                'validation_rules': ['not_empty', 'valid_path_format', 'safe_path']
            },
            'username': {
                'weight': 0.2,
                'critical': True,
                'min_specificity': 0.9,
                'validation_rules': ['not_empty', 'valid_username_format']
            },
            'process_name': {
                'weight': 0.25,
                'critical': True,
                'min_specificity': 0.8,
                'validation_rules': ['not_empty', 'valid_process_name']
            },
            'problem_description': {
                'weight': 0.2,
                'critical': False,
                'min_specificity': 0.7,
                'validation_rules': ['not_empty', 'sufficient_detail']
            }
        }
        
        # Default requirements for unknown fields
        default_requirements = {
            'weight': 0.1,
            'critical': False,
            'min_specificity': 0.5,
            'validation_rules': ['not_empty']
        }
        
        return field_requirements.get(field, default_requirements)
    
    def _calculate_field_confidence(
        self,
        field_name: str,
        field_value: Any,
        field_info: Dict[str, Any],
        issues: List[ValidationIssue]
    ) -> float:
        """Calculate confidence score for a specific field"""
        
        if not field_value:
            return 0.0  # Missing field = 0 confidence
        
        base_confidence = 1.0
        
        # Check field-specific validation issues
        field_issues = [issue for issue in issues if issue.field == field_name]
        
        for issue in field_issues:
            if issue.level == ValidationLevel.CRITICAL:
                base_confidence -= 0.6
            elif issue.level == ValidationLevel.ERROR:
                base_confidence -= 0.4
            elif issue.level == ValidationLevel.WARNING:
                base_confidence -= 0.2
            elif issue.level == ValidationLevel.INFO:
                base_confidence -= 0.1
        
        # Apply specificity scoring
        specificity_score = self._calculate_field_specificity(field_name, field_value)
        min_specificity = field_info.get('min_specificity', 0.5)
        
        if specificity_score < min_specificity:
            # Penalize for insufficient specificity
            specificity_penalty = (min_specificity - specificity_score) * 0.5
            base_confidence -= specificity_penalty
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_field_specificity(self, field_name: str, field_value: Any) -> float:
        """Calculate how specific/detailed a field value is"""
        
        if not field_value or not isinstance(field_value, str):
            return 0.0
        
        value = field_value.lower().strip()
        
        # Field-specific specificity rules
        if field_name == 'target_systems':
            # More specific targets get higher scores
            if any(term in value for term in ['all', 'everything', 'servers']):
                return 0.3  # Very vague
            elif any(term in value for term in ['web-', 'db-', 'app-', 'prod-', 'dev-']):
                return 0.8  # Good specificity
            elif '.' in value or '-' in value:
                return 0.9  # Specific hostname/group
            else:
                return 0.5  # Medium specificity
                
        elif field_name == 'service_name':
            # Known services get higher scores
            known_services = ['apache', 'nginx', 'mysql', 'postgresql', 'iis', 'tomcat', 'redis']
            if any(service in value for service in known_services):
                return 0.9
            elif any(term in value for term in ['service', 'server', 'daemon']):
                return 0.6
            else:
                return 0.4
                
        elif field_name == 'action':
            # Specific actions get higher scores
            specific_actions = ['start', 'stop', 'restart', 'reload', 'status', 'enable', 'disable']
            if value in specific_actions:
                return 0.95
            elif any(action in value for action in specific_actions):
                return 0.8
            else:
                return 0.4
                
        elif field_name == 'operation':
            # Specific operations get higher scores
            specific_ops = ['install', 'update', 'configure', 'backup', 'restore', 'monitor']
            if any(op in value for op in specific_ops):
                return 0.8
            else:
                return 0.5
                
        elif field_name == 'file_path':
            # Absolute paths are more specific
            if value.startswith('/') or value.startswith('c:'):
                return 0.9
            elif '/' in value or '\\' in value:
                return 0.7
            else:
                return 0.4
                
        # Default specificity calculation based on length and detail
        if len(value) < 3:
            return 0.2
        elif len(value) < 10:
            return 0.5
        else:
            return 0.7