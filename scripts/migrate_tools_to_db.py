#!/usr/bin/env python3
"""
Tool Migration Script
Imports tool definitions from YAML files into PostgreSQL database

Usage:
    # Import single file
    python scripts/migrate_tools_to_db.py --file pipeline/config/tools/linux/grep.yaml
    
    # Import entire directory
    python scripts/migrate_tools_to_db.py --dir pipeline/config/tools/linux
    
    # Import all tools
    python scripts/migrate_tools_to_db.py --all
    
    # Dry run (validate without importing)
    python scripts/migrate_tools_to_db.py --all --dry-run
"""

import os
import sys
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.services.tool_catalog_service import ToolCatalogService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolMigrator:
    """
    Migrates tool definitions from YAML to database
    """
    
    def __init__(self, service: ToolCatalogService, dry_run: bool = False):
        self.service = service
        self.dry_run = dry_run
        self.stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def load_yaml_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse YAML file"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def validate_tool_definition(self, data: Dict[str, Any], file_path: str) -> bool:
        """Validate tool definition has required fields"""
        required_fields = ['tool_name', 'version', 'description', 'platform', 'category', 'defaults', 'capabilities']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"{file_path}: Missing required field '{field}'")
                return False
        
        # Validate platform
        valid_platforms = ['linux', 'windows', 'network', 'scheduler', 'custom', 'multi-platform', 'database', 'cloud', 'container', 'kubernetes', 'monitoring']
        if data['platform'] not in valid_platforms:
            logger.error(f"{file_path}: Invalid platform '{data['platform']}'. Must be one of: {valid_platforms}")
            return False
        
        # Validate category
        valid_categories = ['system', 'network', 'automation', 'monitoring', 'security', 'database', 'cloud', 'container', 'asset', 'communication']
        if data['category'] not in valid_categories:
            logger.error(f"{file_path}: Invalid category '{data['category']}'. Must be one of: {valid_categories}")
            return False
        
        # Validate capabilities
        if not isinstance(data['capabilities'], dict) or len(data['capabilities']) == 0:
            logger.error(f"{file_path}: 'capabilities' must be a non-empty dictionary")
            return False
        
        return True
    
    def import_tool(self, file_path: str) -> bool:
        """
        Import a single tool from YAML file
        
        Returns:
            True if successful
        """
        self.stats['processed'] += 1
        
        logger.info(f"Processing: {file_path}")
        
        # Load YAML
        data = self.load_yaml_file(file_path)
        if not data:
            self.stats['failed'] += 1
            return False
        
        # Validate
        if not self.validate_tool_definition(data, file_path):
            self.stats['failed'] += 1
            return False
        
        if self.dry_run:
            logger.info(f"  [DRY RUN] Would import: {data['tool_name']} v{data['version']}")
            self.stats['succeeded'] += 1
            return True
        
        try:
            # Check if tool already exists
            existing = self.service.get_tool_by_name(data['tool_name'], data['version'], use_cache=False)
            if existing:
                logger.warning(f"  Tool {data['tool_name']} v{data['version']} already exists (ID: {existing['id']})")
                self.stats['skipped'] += 1
                return True
            
            # Create tool
            tool_id = self.service.create_tool(
                tool_name=data['tool_name'],
                version=data['version'],
                description=data['description'],
                platform=data['platform'],
                category=data['category'],
                defaults=data['defaults'],
                dependencies=data.get('dependencies', []),
                metadata=data.get('metadata', {}),
                created_by='migration_script'
            )
            
            logger.info(f"  ✓ Created tool: {data['tool_name']} (ID: {tool_id})")
            
            # Import capabilities and patterns
            for capability_name, capability_data in data['capabilities'].items():
                capability_id = self.service.add_capability(
                    tool_id=tool_id,
                    capability_name=capability_name,
                    description=capability_data.get('description', '')
                )
                
                logger.info(f"    ✓ Added capability: {capability_name} (ID: {capability_id})")
                
                # Import patterns
                patterns = capability_data.get('patterns', {})
                for pattern_name, pattern_data in patterns.items():
                    pattern_id = self.service.add_pattern(
                        capability_id=capability_id,
                        pattern_name=pattern_name,
                        description=pattern_data.get('description', ''),
                        typical_use_cases=pattern_data.get('typical_use_cases', []),
                        time_estimate_ms=pattern_data.get('time_estimate_ms', '1000'),
                        cost_estimate=pattern_data.get('cost_estimate', '1'),
                        complexity_score=float(pattern_data.get('complexity_score', 0.5)),
                        scope=pattern_data.get('scope', 'single_item'),
                        completeness=pattern_data.get('completeness', 'complete'),
                        policy=pattern_data.get('policy', {}),
                        preference_match=pattern_data.get('preference_match', {}),
                        required_inputs=pattern_data.get('required_inputs', []),
                        expected_outputs=pattern_data.get('expected_outputs', []),
                        limitations=pattern_data.get('limitations', [])
                    )
                    
                    logger.info(f"      ✓ Added pattern: {pattern_name} (ID: {pattern_id})")
            
            self.stats['succeeded'] += 1
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Error importing tool: {e}")
            self.stats['failed'] += 1
            return False
    
    def import_directory(self, dir_path: str, recursive: bool = True) -> int:
        """
        Import all YAML files from a directory
        
        Returns:
            Number of successfully imported tools
        """
        path = Path(dir_path)
        
        if not path.exists() or not path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return 0
        
        # Find all YAML files
        if recursive:
            yaml_files = list(path.rglob('*.yaml')) + list(path.rglob('*.yml'))
        else:
            yaml_files = list(path.glob('*.yaml')) + list(path.glob('*.yml'))
        
        # Exclude template files
        yaml_files = [f for f in yaml_files if 'template' not in f.name.lower()]
        
        logger.info(f"Found {len(yaml_files)} YAML files in {dir_path}")
        
        for yaml_file in yaml_files:
            self.import_tool(str(yaml_file))
        
        return self.stats['succeeded']
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Processed:  {self.stats['processed']}")
        print(f"Succeeded:  {self.stats['succeeded']}")
        print(f"Skipped:    {self.stats['skipped']} (already exist)")
        print(f"Failed:     {self.stats['failed']}")
        print("="*60)
        
        if self.dry_run:
            print("\n[DRY RUN] No changes were made to the database")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate tool definitions from YAML to PostgreSQL database'
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='Import single YAML file')
    group.add_argument('--dir', help='Import all YAML files from directory')
    group.add_argument('--all', action='store_true', help='Import all tools from pipeline/config/tools')
    
    parser.add_argument('--dry-run', action='store_true', help='Validate without importing')
    parser.add_argument('--database-url', help='PostgreSQL connection URL (default: from env)')
    
    args = parser.parse_args()
    
    # Initialize service
    try:
        service = ToolCatalogService(database_url=args.database_url)
        
        # Test connection
        if not service.health_check():
            logger.error("Database connection failed. Is PostgreSQL running?")
            sys.exit(1)
        
        logger.info("Database connection successful")
        
    except Exception as e:
        logger.error(f"Failed to initialize ToolCatalogService: {e}")
        sys.exit(1)
    
    # Create migrator
    migrator = ToolMigrator(service, dry_run=args.dry_run)
    
    # Perform migration
    try:
        if args.file:
            migrator.import_tool(args.file)
        
        elif args.dir:
            migrator.import_directory(args.dir)
        
        elif args.all:
            # Get project root
            project_root = Path(__file__).parent.parent
            tools_dir = project_root / 'pipeline' / 'config' / 'tools'
            
            if not tools_dir.exists():
                logger.error(f"Tools directory not found: {tools_dir}")
                sys.exit(1)
            
            migrator.import_directory(str(tools_dir))
        
        # Print summary
        migrator.print_summary()
        
        # Exit code
        if migrator.stats['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
        migrator.print_summary()
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    
    finally:
        service.close()


if __name__ == '__main__':
    main()