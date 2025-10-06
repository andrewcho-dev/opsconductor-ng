#!/usr/bin/env python3
"""
Add credential tool profiles to database
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.services.tool_catalog_service import ToolCatalogService

def main():
    print("Adding credential tool profiles to database...")
    
    # Initialize service
    service = ToolCatalogService()
    
    # Check if tool already exists
    existing = service.get_tool_by_name("asset-credentials-read", "1.0", use_cache=False)
    if existing:
        print(f"Tool asset-credentials-read already exists (ID: {existing['id']})")
        print("Skipping...")
        return
    
    # Create tool
    tool_id = service.create_tool(
        tool_name="asset-credentials-read",
        version="1.0",
        description="Retrieve asset credentials (SSH keys, passwords, API tokens) - GATED ACCESS",
        platform="multi-platform",
        category="asset",
        defaults={
            "accuracy_level": "real-time",
            "freshness": "current",
            "data_source": "credential_vault"
        },
        dependencies=["asset_service_api", "rbac_enforcement"],
        metadata={},
        created_by="admin_script"
    )
    
    print(f"✓ Created tool: asset-credentials-read (ID: {tool_id})")
    
    # Add credential_access capability
    capability_id_1 = service.add_capability(
        tool_id=tool_id,
        capability_name="credential_access",
        description="Retrieve credentials for infrastructure assets"
    )
    
    print(f"  ✓ Added capability: credential_access (ID: {capability_id_1})")
    
    # Add pattern for credential_access
    pattern_id_1 = service.add_pattern(
        capability_id=capability_id_1,
        pattern_name="retrieve_credentials",
        description="Retrieve credentials for infrastructure assets",
        typical_use_cases=[
            "get credentials",
            "what credentials",
            "show password",
            "SSH key",
            "API token"
        ],
        time_estimate_ms="500",
        cost_estimate="1",
        complexity_score=0.2,
        scope="single_asset_credentials",
        completeness="complete",
        policy={
            "max_cost": 5,
            "requires_approval": False,
            "production_safe": True
        },
        preference_match={
            "speed": 0.85,
            "accuracy": 1.0,
            "cost": 0.9,
            "complexity": 0.8,
            "completeness": 1.0
        },
        required_inputs=["asset_id", "justification"],
        expected_outputs=["credentials"],
        limitations=[
            "Requires ADMIN permissions",
            "Requires justification",
            "Audit logged"
        ]
    )
    
    print(f"    ✓ Added pattern: retrieve_credentials (ID: {pattern_id_1})")
    
    # Add secret_retrieval capability
    capability_id_2 = service.add_capability(
        tool_id=tool_id,
        capability_name="secret_retrieval",
        description="Access secrets and sensitive configuration"
    )
    
    print(f"  ✓ Added capability: secret_retrieval (ID: {capability_id_2})")
    
    # Add pattern for secret_retrieval
    pattern_id_2 = service.add_pattern(
        capability_id=capability_id_2,
        pattern_name="retrieve_secrets",
        description="Access secrets and sensitive configuration",
        typical_use_cases=[
            "get secret",
            "retrieve token",
            "access credentials",
            "communication credentials"
        ],
        time_estimate_ms="500",
        cost_estimate="1",
        complexity_score=0.2,
        scope="asset_secrets",
        completeness="complete",
        policy={
            "max_cost": 5,
            "requires_approval": False,
            "production_safe": True
        },
        preference_match={
            "speed": 0.85,
            "accuracy": 1.0,
            "cost": 0.9,
            "complexity": 0.8,
            "completeness": 1.0
        },
        required_inputs=["asset_id", "justification"],
        expected_outputs=["secrets"],
        limitations=[
            "Requires ADMIN permissions",
            "Requires justification",
            "Audit logged"
        ]
    )
    
    print(f"    ✓ Added pattern: retrieve_secrets (ID: {pattern_id_2})")
    
    print("\n✓ Successfully added credential tool profiles to database!")
    
    service.close()

if __name__ == '__main__':
    main()