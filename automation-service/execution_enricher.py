#!/usr/bin/env python3
"""
Execution Enricher - Automatic asset lookup and credential resolution
Enriches tool execution requests with connection profiles and credentials
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ExecutionEnricher:
    """
    Enriches tool execution requests with asset profiles and credentials
    
    Workflow:
    1. Check if tool has auth metadata
    2. Extract host parameter from request
    3. Lookup connection profile from asset facade
    4. Resolve credentials from secrets broker
    5. Inject enriched parameters into execution request
    """
    
    def __init__(self, asset_facade, secrets_manager, internal_key: str):
        """
        Initialize execution enricher
        
        Args:
            asset_facade: AssetFacade instance
            secrets_manager: SecretsManager instance
            internal_key: Internal key for service-to-service auth
        """
        self.asset_facade = asset_facade
        self.secrets_manager = secrets_manager
        self.internal_key = internal_key
        self.enabled = os.getenv("EXEC_ENRICH_ENABLE", "true").lower() == "true"
        
        logger.info(f"ExecutionEnricher initialized (enabled={self.enabled})")
    
    async def enrich_execution(
        self,
        tool_name: str,
        tool_def: Dict[str, Any],
        parameters: Dict[str, Any],
        trace_id: str
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Enrich execution request with asset profile and credentials
        
        Args:
            tool_name: Tool name
            tool_def: Tool definition from registry
            parameters: Original parameters from request
            trace_id: Trace ID for logging
            
        Returns:
            Tuple of (enriched_parameters, error_dict)
            If error_dict is not None, enrichment failed and error should be returned
        """
        start_time = time.perf_counter()
        
        if not self.enabled:
            logger.debug(f"[{trace_id}] Enrichment disabled, skipping")
            return parameters, None
        
        # Check if tool has auth metadata
        auth_metadata = tool_def.get('auth')
        if not auth_metadata:
            logger.debug(f"[{trace_id}] Tool {tool_name} has no auth metadata, skipping enrichment")
            return parameters, None
        
        protocol = auth_metadata.get('protocol')
        needs = auth_metadata.get('needs', [])
        
        if not protocol or not needs:
            logger.debug(f"[{trace_id}] Tool {tool_name} auth metadata incomplete, skipping enrichment")
            return parameters, None
        
        # Check if required parameters are present
        for param in needs:
            if param not in parameters or not parameters[param]:
                logger.debug(f"[{trace_id}] Required parameter '{param}' not provided, skipping enrichment")
                return parameters, None
        
        # Extract host parameter
        host = parameters.get('host')
        if not host:
            logger.warning(f"[{trace_id}] Host parameter missing for tool {tool_name}")
            return parameters, None
        
        logger.info(f"[{trace_id}] Enriching execution for tool={tool_name}, host={host}, protocol={protocol}")
        
        try:
            # Step 1: Lookup connection profile
            profile_start = time.perf_counter()
            profile = await self.asset_facade.get_connection_profile(host)
            profile_duration = (time.perf_counter() - profile_start) * 1000
            
            logger.info(f"[{trace_id}] Profile lookup completed in {profile_duration:.2f}ms")
            
            # Check for errors
            if not profile.get('found'):
                error_type = profile.get('error', 'asset_not_found')
                
                if error_type == 'ambiguous_asset':
                    return parameters, {
                        "error": "ambiguous_asset",
                        "host": host,
                        "candidates": profile.get('candidates', []),
                        "how_to_fix": "Specify the IP or choose one candidate"
                    }
                else:
                    return parameters, {
                        "error": "asset_not_found",
                        "host": host,
                        "how_to_fix": "Add this host to the asset inventory"
                    }
            
            # Step 2: Select protocol branch
            protocol_config = profile.get(protocol)
            if not protocol_config:
                logger.warning(f"[{trace_id}] Protocol {protocol} not available for host {host}")
                return parameters, {
                    "error": "protocol_not_available",
                    "host": host,
                    "protocol": protocol,
                    "available_protocols": [k for k in profile.keys() if k in ['winrm', 'ssh', 'rdp']],
                    "how_to_fix": f"Host does not support {protocol} protocol"
                }
            
            # Step 3: Resolve credentials
            credential_ref = protocol_config.get('credential_ref')
            if not credential_ref:
                logger.warning(f"[{trace_id}] No credential_ref for host {host}, protocol {protocol}")
                return parameters, {
                    "error": "missing_credentials",
                    "protocol": protocol,
                    "host": host,
                    "required": ["username", "password"],
                    "how_to_fix": f"Store {protocol.upper()} credentials on the asset or import them into the secrets broker"
                }
            
            # Resolve credential reference
            secret_start = time.perf_counter()
            credentials = self.secrets_manager.resolve_credential_ref(
                credential_ref=credential_ref,
                accessed_by=f"enricher-{trace_id}"
            )
            secret_duration = (time.perf_counter() - secret_start) * 1000
            
            logger.info(f"[{trace_id}] Secret resolved in {secret_duration:.2f}ms (password masked)")
            
            if not credentials:
                return parameters, {
                    "error": "secret_unavailable",
                    "ref": credential_ref,
                    "host": host,
                    "protocol": protocol,
                    "how_to_fix": "Recreate or reimport the secret for this asset"
                }
            
            # Step 4: Build enriched parameters
            enriched = parameters.copy()
            
            # Inject connection parameters
            enriched['username'] = credentials.get('username')
            enriched['password'] = credentials.get('password')
            
            if protocol == 'winrm':
                enriched['port'] = protocol_config.get('port', 5985)
                enriched['use_ssl'] = protocol_config.get('use_ssl', False)
                if protocol_config.get('domain'):
                    enriched['domain'] = protocol_config['domain']
            elif protocol == 'ssh':
                enriched['port'] = protocol_config.get('port', 22)
                if credentials.get('private_key'):
                    enriched['private_key'] = credentials['private_key']
            
            total_duration = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                f"[{trace_id}] Enrichment completed in {total_duration:.2f}ms "
                f"(profile={profile_duration:.2f}ms, secret={secret_duration:.2f}ms)"
            )
            
            # Log enriched parameter keys (not values)
            enriched_keys = [k for k in enriched.keys() if k not in parameters]
            logger.info(f"[{trace_id}] Injected parameters: {enriched_keys}")
            
            return enriched, None
            
        except Exception as e:
            logger.error(f"[{trace_id}] Enrichment failed: {e}")
            return parameters, {
                "error": "enrichment_failed",
                "host": host,
                "protocol": protocol,
                "message": str(e),
                "how_to_fix": "Check logs for details or contact support"
            }