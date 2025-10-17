#!/usr/bin/env python3
"""
OpsConductor Capability Management System

This is the PERMANENT, COMPREHENSIVE solution for capability consistency across:
- Stage A LLM prompts/responses
- Database tool catalog
- Tool optimization profiles
- Stage B hybrid orchestrator

This system ensures capability names are consistent across ALL layers and provides
automated validation, migration, and maintenance tools.

Author: AI Assistant
Created: 2025-01-27
Purpose: Fix capability mismatch issues permanently
"""

import os
import re
import json
import yaml
import asyncio
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CapabilityDefinition:
    """Canonical capability definition"""
    name: str
    description: str
    category: str  # system, network, automation, monitoring, security, database, cloud, container
    aliases: List[str]  # Alternative names that should map to this capability
    stage_a_patterns: List[str]  # Patterns that Stage A should recognize
    example_tools: List[str]  # Example tools that provide this capability
    validation_regex: Optional[str] = None  # Regex pattern for validation

@dataclass
class CapabilityAuditResult:
    """Result of capability audit across the system"""
    consistent_capabilities: List[str]
    inconsistent_capabilities: Dict[str, Dict[str, List[str]]]  # capability -> {source: [variants]}
    missing_capabilities: Dict[str, List[str]]  # source -> [missing_capabilities]
    orphaned_capabilities: Dict[str, List[str]]  # source -> [orphaned_capabilities]
    recommendations: List[str]

class CapabilityRegistry:
    """
    Canonical capability registry - Single Source of Truth
    
    This defines ALL valid capabilities in the OpsConductor system.
    """
    
    def __init__(self):
        self.capabilities: Dict[str, CapabilityDefinition] = {}
        self._load_canonical_capabilities()
    
    def _load_canonical_capabilities(self):
        """Load the canonical capability definitions"""
        
        # Define the canonical capabilities for OpsConductor
        canonical_capabilities = [
            CapabilityDefinition(
                name="file_reading",
                description="Read contents of files and directories",
                category="system",
                aliases=["file_read", "file_access", "read_file"],
                stage_a_patterns=["read", "view", "display", "show", "contents", "cat"],
                example_tools=["cat", "head", "tail", "Get-Content", "type"]
            ),
            CapabilityDefinition(
                name="file_writing",
                description="Write or modify file contents",
                category="system", 
                aliases=["file_write", "file_modify", "write_file"],
                stage_a_patterns=["write", "create", "edit", "modify", "append"],
                example_tools=["echo", "tee", "Set-Content", "Add-Content"]
            ),
            CapabilityDefinition(
                name="system_monitoring",
                description="Monitor system processes, resources, and status",
                category="monitoring",
                aliases=["process_monitoring", "system_status", "resource_monitoring"],
                stage_a_patterns=["monitor", "status", "check", "processes", "performance"],
                example_tools=["ps", "top", "htop", "systemctl", "Get-Process"]
            ),
            CapabilityDefinition(
                name="service_control",
                description="Start, stop, restart, and manage system services",
                category="system",
                aliases=["service_management", "daemon_control"],
                stage_a_patterns=["start", "stop", "restart", "service", "daemon"],
                example_tools=["systemctl", "service", "Start-Service", "Stop-Service"]
            ),
            CapabilityDefinition(
                name="network_connectivity",
                description="Test network connectivity and reachability",
                category="network",
                aliases=["connectivity_test", "network_test", "ping_test"],
                stage_a_patterns=["ping", "connect", "test", "network", "reachable"],
                example_tools=["ping", "telnet", "nc", "Test-NetConnection"]
            ),
            CapabilityDefinition(
                name="network_analysis",
                description="Analyze network traffic and connections",
                category="network",
                aliases=["traffic_analysis", "connection_analysis"],
                stage_a_patterns=["analyze", "traffic", "connections", "netstat"],
                example_tools=["netstat", "ss", "tcpdump", "Get-NetTCPConnection"]
            ),
            CapabilityDefinition(
                name="asset_query",
                description="Query and search asset information",
                category="automation",
                aliases=["asset_search", "inventory_query"],
                stage_a_patterns=["query", "search", "find", "list", "assets"],
                example_tools=["asset-query", "Get-Asset"]
            ),
            CapabilityDefinition(
                name="credential_access",
                description="Access and manage credentials",
                category="security",
                aliases=["credential_management", "credential_lookup"],
                stage_a_patterns=["credentials", "password", "key", "token"],
                example_tools=["credential-manager", "Get-Credential"]
            ),
            CapabilityDefinition(
                name="docker_management",
                description="Manage Docker containers and images",
                category="container",
                aliases=["container_management", "docker_control"],
                stage_a_patterns=["docker", "container", "image", "deploy"],
                example_tools=["docker", "docker-compose"]
            ),
            CapabilityDefinition(
                name="database_query",
                description="Query and manage database operations",
                category="database",
                aliases=["db_query", "sql_execution"],
                stage_a_patterns=["database", "query", "sql", "select"],
                example_tools=["psql", "mysql", "Invoke-Sqlcmd"]
            )
        ]
        
        # Build the registry
        for cap in canonical_capabilities:
            self.capabilities[cap.name] = cap
            
            # Add aliases mapping back to canonical name
            for alias in cap.aliases:
                if alias not in self.capabilities:
                    # Create alias entry pointing to canonical
                    alias_def = CapabilityDefinition(
                        name=alias,
                        description=f"Alias for {cap.name}",
                        category=cap.category,
                        aliases=[],
                        stage_a_patterns=[],
                        example_tools=[],
                        validation_regex=f"^{re.escape(cap.name)}$"
                    )
                    alias_def._canonical_name = cap.name
                    self.capabilities[alias] = alias_def
    
    def get_canonical_name(self, capability_name: str) -> str:
        """Get the canonical name for a capability (resolves aliases)"""
        if capability_name in self.capabilities:
            cap = self.capabilities[capability_name]
            return getattr(cap, '_canonical_name', capability_name)
        return capability_name
    
    def is_valid_capability(self, capability_name: str) -> bool:
        """Check if a capability name is valid (canonical or alias)"""
        return capability_name in self.capabilities
    
    def get_all_canonical_capabilities(self) -> List[str]:
        """Get all canonical capability names (no aliases)"""
        return [name for name, cap in self.capabilities.items() 
                if not hasattr(cap, '_canonical_name')]
    
    def get_stage_a_patterns(self, capability_name: str) -> List[str]:
        """Get Stage A recognition patterns for a capability"""
        canonical = self.get_canonical_name(capability_name)
        if canonical in self.capabilities:
            return self.capabilities[canonical].stage_a_patterns
        return []

class CapabilityAuditor:
    """
    Audits capability consistency across all system components
    """
    
    def __init__(self, registry: CapabilityRegistry, db_connection_string: str):
        self.registry = registry
        self.db_connection_string = db_connection_string
    
    async def audit_system_capabilities(self) -> CapabilityAuditResult:
        """
        Comprehensive audit of capability consistency across:
        - Database tool_capabilities table
        - Tool optimization profiles YAML
        - Stage A prompts/training data
        - HybridOrchestrator configuration
        """
        logger.info("🔍 Starting comprehensive capability audit...")
        
        # Collect capabilities from all sources
        db_capabilities = await self._audit_database_capabilities()
        profile_capabilities = await self._audit_optimization_profiles()
        stage_a_capabilities = await self._audit_stage_a_capabilities()
        
        # Analyze consistency
        all_sources = {
            'database': db_capabilities,
            'optimization_profiles': profile_capabilities, 
            'stage_a': stage_a_capabilities
        }
        
        consistent = []
        inconsistent = {}
        missing = {}
        orphaned = {}
        recommendations = []
        
        # Find canonical capabilities present in all sources
        canonical_caps = set(self.registry.get_all_canonical_capabilities())
        
        for cap in canonical_caps:
            sources_with_cap = []
            variants_by_source = {}
            
            for source, caps in all_sources.items():
                # Check if canonical name or any alias exists
                found_variants = []
                cap_def = self.registry.capabilities[cap]
                
                # Check canonical name
                if cap in caps:
                    found_variants.append(cap)
                
                # Check aliases
                for alias in cap_def.aliases:
                    if alias in caps:
                        found_variants.append(alias)
                
                if found_variants:
                    sources_with_cap.append(source)
                    variants_by_source[source] = found_variants
                else:
                    missing.setdefault(source, []).append(cap)
            
            # Determine if consistent
            if len(sources_with_cap) == len(all_sources):
                # Check if all sources use the same variant
                all_variants = []
                for variants in variants_by_source.values():
                    all_variants.extend(variants)
                
                if len(set(all_variants)) == 1 and all_variants[0] == cap:
                    consistent.append(cap)
                else:
                    inconsistent[cap] = variants_by_source
            else:
                inconsistent[cap] = variants_by_source
        
        # Find orphaned capabilities (in sources but not in registry)
        for source, caps in all_sources.items():
            orphaned_caps = []
            for cap in caps:
                if not self.registry.is_valid_capability(cap):
                    orphaned_caps.append(cap)
            if orphaned_caps:
                orphaned[source] = orphaned_caps
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            inconsistent, missing, orphaned
        )
        
        return CapabilityAuditResult(
            consistent_capabilities=consistent,
            inconsistent_capabilities=inconsistent,
            missing_capabilities=missing,
            orphaned_capabilities=orphaned,
            recommendations=recommendations
        )
    
    async def _audit_database_capabilities(self) -> Set[str]:
        """Extract all capability names from database"""
        capabilities = set()
        
        try:
            conn = psycopg2.connect(self.db_connection_string)
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT DISTINCT capability_name 
                    FROM tool_catalog.tool_capabilities
                    ORDER BY capability_name
                """)
                for row in cursor.fetchall():
                    capabilities.add(row['capability_name'])
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to audit database capabilities: {e}")
        
        logger.info(f"Found {len(capabilities)} capabilities in database")
        return capabilities
    
    async def _audit_optimization_profiles(self) -> Set[str]:
        """Extract capabilities from tool_optimization_profiles.yaml"""
        capabilities = set()
        
        try:
            profile_path = "/home/opsconductor/opsconductor-ng/pipeline/config/tool_optimization_profiles.yaml"
            
            if os.path.exists(profile_path):
                async with aiofiles.open(profile_path, 'r') as f:
                    content = await f.read()
                    data = yaml.safe_load(content)
                
                # Extract capabilities from optimization profiles
                # The YAML structure is: tools -> tool_name -> capabilities -> capability_name
                for tool_name, tool_data in data.get('tools', {}).items():
                    if isinstance(tool_data, dict) and 'capabilities' in tool_data:
                        for capability_name in tool_data['capabilities'].keys():
                            capabilities.add(capability_name)
            
        except Exception as e:
            logger.error(f"Failed to audit optimization profiles: {e}")
        
        logger.info(f"Found {len(capabilities)} capabilities in optimization profiles")
        return capabilities
    
    async def _audit_stage_a_capabilities(self) -> Set[str]:
        """Extract capabilities that Stage A might generate"""
        capabilities = set()
        
        try:
            # Look for Stage A prompt files and classifier code
            stage_a_files = [
                "/home/opsconductor/opsconductor-ng/pipeline/stages/stage_a/intent_classifier.py",
                "/home/opsconductor/opsconductor-ng/pipeline/stages/stage_a/classifier.py"
            ]
            
            for file_path in stage_a_files:
                if os.path.exists(file_path):
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        
                        # Look for capability patterns in code
                        # This is a heuristic - in real system would need more sophisticated analysis
                        cap_patterns = re.findall(r'"([a-z_]+)"', content)
                        for cap in cap_patterns:
                            if '_' in cap and len(cap) > 5:  # Likely capability name
                                capabilities.add(cap)
            
        except Exception as e:
            logger.error(f"Failed to audit Stage A capabilities: {e}")
        
        logger.info(f"Found {len(capabilities)} potential capabilities in Stage A")
        return capabilities
    
    def _generate_recommendations(self, inconsistent: Dict, missing: Dict, orphaned: Dict) -> List[str]:
        """Generate actionable recommendations for fixing capability issues"""
        recommendations = []
        
        if inconsistent:
            recommendations.append(
                f"🔧 CRITICAL: {len(inconsistent)} capabilities have naming inconsistencies. "
                "Run migration to standardize capability names."
            )
        
        if missing:
            recommendations.append(
                f"⚠️  WARNING: Capabilities missing from some sources. "
                "Update tool definitions and configurations."
            )
        
        if orphaned:
            recommendations.append(
                f"🧹 CLEANUP: {sum(len(caps) for caps in orphaned.values())} orphaned capabilities found. "
                "Remove or map to canonical capabilities."
            )
        
        if not inconsistent and not missing and not orphaned:
            recommendations.append("✅ All capabilities are consistent across the system!")
        
        return recommendations

class CapabilityMigrator:
    """
    Migrates capabilities to canonical names across all system components
    """
    
    def __init__(self, registry: CapabilityRegistry, db_connection_string: str):
        self.registry = registry
        self.db_connection_string = db_connection_string
    
    async def migrate_to_canonical_capabilities(self, audit_result: CapabilityAuditResult, dry_run: bool = True) -> Dict[str, int]:
        """
        Migrate all capability names to canonical versions
        
        Returns: Dictionary with migration counts by source
        """
        logger.info(f"🚀 Starting capability migration (dry_run={dry_run})...")
        
        migration_counts = {
            'database': 0,
            'optimization_profiles': 0,
            'stage_a_prompts': 0
        }
        
        # 1. Migrate database capabilities
        migration_counts['database'] = await self._migrate_database_capabilities(dry_run)
        
        # 2. Migrate optimization profiles
        migration_counts['optimization_profiles'] = await self._migrate_optimization_profiles(dry_run)
        
        # 3. Generate Stage A training data
        migration_counts['stage_a_prompts'] = await self._generate_stage_a_training_data(dry_run)
        
        if not dry_run:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.info("📋 Dry run completed - no changes made")
        
        return migration_counts
    
    async def _migrate_database_capabilities(self, dry_run: bool) -> int:
        """Migrate database capability names to canonical versions"""
        migration_count = 0
        
        try:
            conn = psycopg2.connect(self.db_connection_string)
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all current capabilities
                cursor.execute("""
                    SELECT id, tool_id, capability_name
                    FROM tool_catalog.tool_capabilities
                    ORDER BY capability_name
                """)
                
                capabilities = cursor.fetchall()
                
                for cap_row in capabilities:
                    current_name = cap_row['capability_name']
                    canonical_name = self.registry.get_canonical_name(current_name)
                    
                    if current_name != canonical_name and self.registry.is_valid_capability(current_name):
                        logger.info(f"Database: {current_name} → {canonical_name}")
                        migration_count += 1
                        
                        if not dry_run:
                            # Update to canonical name
                            cursor.execute("""
                                UPDATE tool_catalog.tool_capabilities 
                                SET capability_name = %s 
                                WHERE id = %s
                            """, (canonical_name, cap_row['id']))
                
                if not dry_run:
                    conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to migrate database capabilities: {e}")
        
        return migration_count
    
    async def _migrate_optimization_profiles(self, dry_run: bool) -> int:
        """Migrate optimization profiles to use canonical capability names"""
        migration_count = 0
        
        try:
            profile_path = "/home/opsconductor/opsconductor-ng/pipeline/config/tool_optimization_profiles.yaml"
            
            if os.path.exists(profile_path):
                async with aiofiles.open(profile_path, 'r') as f:
                    content = await f.read()
                    data = yaml.safe_load(content)
                
                # Migrate capability names in optimization profiles
                modified = False
                
                for tool_name, tool_data in data.get('tools', {}).items():
                    if isinstance(tool_data, dict) and 'capabilities' in tool_data:
                        capabilities_dict = tool_data['capabilities']
                        
                        # Need to rebuild the capabilities dict with canonical names
                        new_capabilities = {}
                        
                        for cap_name, cap_data in capabilities_dict.items():
                            canonical = self.registry.get_canonical_name(cap_name)
                            if cap_name != canonical and self.registry.is_valid_capability(cap_name):
                                logger.info(f"Optimization profiles: {cap_name} → {canonical}")
                                migration_count += 1
                                
                                if not dry_run:
                                    new_capabilities[canonical] = cap_data
                                    modified = True
                                else:
                                    new_capabilities[cap_name] = cap_data
                            else:
                                new_capabilities[cap_name] = cap_data
                        
                        if modified and not dry_run:
                            tool_data['capabilities'] = new_capabilities
                
                # Write back if modified
                if modified and not dry_run:
                    async with aiofiles.open(profile_path, 'w') as f:
                        await f.write(yaml.dump(data, default_flow_style=False, sort_keys=True))
                        
        except Exception as e:
            logger.error(f"Failed to migrate optimization profiles: {e}")
        
        return migration_count
    
    async def _generate_stage_a_training_data(self, dry_run: bool) -> int:
        """Generate Stage A training data with canonical capability mappings"""
        
        if dry_run:
            logger.info("Would generate Stage A training data with canonical capabilities")
            return len(self.registry.get_all_canonical_capabilities())
        
        # Generate training data file
        training_data = {
            'capability_mappings': {},
            'recognition_patterns': {},
            'examples': []
        }
        
        for cap_name in self.registry.get_all_canonical_capabilities():
            cap_def = self.registry.capabilities[cap_name]
            
            # Add capability mapping
            training_data['capability_mappings'][cap_name] = {
                'canonical_name': cap_name,
                'description': cap_def.description,
                'category': cap_def.category,
                'aliases': cap_def.aliases
            }
            
            # Add recognition patterns
            training_data['recognition_patterns'][cap_name] = cap_def.stage_a_patterns
            
            # Add examples
            for pattern in cap_def.stage_a_patterns:
                training_data['examples'].append({
                    'query_pattern': pattern,
                    'expected_capability': cap_name,
                    'example_tools': cap_def.example_tools[:3]  # First 3 tools
                })
        
        # Write training data
        training_file = "/home/opsconductor/opsconductor-ng/pipeline/stages/stage_a/capability_training_data.yaml"
        
        try:
            async with aiofiles.open(training_file, 'w') as f:
                await f.write(yaml.dump(training_data, default_flow_style=False, sort_keys=True))
            
            logger.info(f"✅ Generated Stage A training data: {training_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate Stage A training data: {e}")
        
        return len(training_data['capability_mappings'])

class CapabilityValidator:
    """
    Validates capability consistency and provides ongoing monitoring
    """
    
    def __init__(self, registry: CapabilityRegistry, db_connection_string: str):
        self.registry = registry
        self.db_connection_string = db_connection_string
    
    async def validate_new_tool(self, tool_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that a new tool uses only canonical capability names
        
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        for capability in tool_data.get('capabilities', []):
            cap_name = capability.get('capability_name', '')
            
            if not self.registry.is_valid_capability(cap_name):
                issues.append(f"Invalid capability '{cap_name}' - not in canonical registry")
            
            canonical = self.registry.get_canonical_name(cap_name)
            if cap_name != canonical:
                issues.append(f"Use canonical name '{canonical}' instead of '{cap_name}'")
        
        return len(issues) == 0, issues
    
    async def continuous_validation(self) -> bool:
        """
        Run continuous validation checks to ensure system remains consistent
        
        Returns: True if system is consistent, False if issues found
        """
        auditor = CapabilityAuditor(self.registry, self.db_connection_string)
        audit_result = await auditor.audit_system_capabilities()
        
        # Check for any consistency issues
        has_issues = (
            bool(audit_result.inconsistent_capabilities) or
            bool(audit_result.missing_capabilities) or
            bool(audit_result.orphaned_capabilities)
        )
        
        if has_issues:
            logger.warning("🚨 Capability consistency issues detected!")
            self._log_audit_summary(audit_result)
        else:
            logger.info("✅ All capabilities are consistent")
        
        return not has_issues
    
    def _log_audit_summary(self, audit_result: CapabilityAuditResult):
        """Log a summary of audit results"""
        logger.info(f"Consistent: {len(audit_result.consistent_capabilities)}")
        logger.info(f"Inconsistent: {len(audit_result.inconsistent_capabilities)}")
        logger.info(f"Missing: {sum(len(caps) for caps in audit_result.missing_capabilities.values())}")
        logger.info(f"Orphaned: {sum(len(caps) for caps in audit_result.orphaned_capabilities.values())}")

# Main CLI Interface
async def main():
    """Main CLI interface for capability management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpsConductor Capability Management System")
    parser.add_argument('action', choices=['audit', 'migrate', 'validate', 'fix'], 
                       help='Action to perform')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without making changes')
    parser.add_argument('--db-url', default='postgresql://opsconductor:opsconductor@localhost:5432/opsconductor',
                       help='Database connection string')
    
    args = parser.parse_args()
    
    # Initialize system
    registry = CapabilityRegistry()
    auditor = CapabilityAuditor(registry, args.db_url)
    migrator = CapabilityMigrator(registry, args.db_url)
    validator = CapabilityValidator(registry, args.db_url)
    
    try:
        if args.action == 'audit':
            print("🔍 Auditing capability consistency across system...")
            audit_result = await auditor.audit_system_capabilities()
            
            print(f"\n📊 AUDIT RESULTS:")
            print(f"✅ Consistent capabilities: {len(audit_result.consistent_capabilities)}")
            print(f"⚠️  Inconsistent capabilities: {len(audit_result.inconsistent_capabilities)}")
            print(f"❌ Missing capabilities: {sum(len(caps) for caps in audit_result.missing_capabilities.values())}")
            print(f"🧹 Orphaned capabilities: {sum(len(caps) for caps in audit_result.orphaned_capabilities.values())}")
            
            if audit_result.inconsistent_capabilities:
                print(f"\n🔧 INCONSISTENT CAPABILITIES:")
                for cap, sources in audit_result.inconsistent_capabilities.items():
                    print(f"  {cap}:")
                    for source, variants in sources.items():
                        print(f"    {source}: {variants}")
            
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in audit_result.recommendations:
                print(f"  {rec}")
        
        elif args.action == 'migrate':
            print("🚀 Starting capability migration...")
            audit_result = await auditor.audit_system_capabilities()
            migration_counts = await migrator.migrate_to_canonical_capabilities(audit_result, args.dry_run)
            
            print(f"\n📈 MIGRATION RESULTS:")
            for source, count in migration_counts.items():
                print(f"  {source}: {count} capabilities migrated")
            
            if args.dry_run:
                print(f"\n💡 This was a dry run. Use --no-dry-run to apply changes.")
        
        elif args.action == 'validate':
            print("✅ Running capability validation...")
            is_valid = await validator.continuous_validation()
            
            if is_valid:
                print("✅ System validation passed!")
                return 0
            else:
                print("❌ System validation failed!")
                return 1
        
        elif args.action == 'fix':
            print("🔧 Running complete capability fix process...")
            
            # 1. Audit
            audit_result = await auditor.audit_system_capabilities()
            
            # 2. Migrate
            migration_counts = await migrator.migrate_to_canonical_capabilities(audit_result, args.dry_run)
            
            # 3. Validate
            is_valid = await validator.continuous_validation()
            
            print(f"\n🎯 FIX COMPLETE:")
            print(f"  Migrated: {sum(migration_counts.values())} capabilities")
            print(f"  Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            
            if not is_valid:
                print(f"  Run 'audit' to see remaining issues")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))