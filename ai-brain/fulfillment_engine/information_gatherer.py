"""
Information Gatherer - Gathers missing information for fulfillment

Handles cases where the original AI understanding lacks specific details:
- Queries asset service for server details
- Retrieves network topology information
- Gathers credential information
- Validates target systems exist and are accessible
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .intent_processor import ProcessedIntent
from .resource_mapper import ResourceMapping, ServiceType

logger = logging.getLogger(__name__)


@dataclass
class AssetInfo:
    """Asset information gathered from asset service"""
    asset_id: str
    hostname: str
    ip_address: str
    os_type: str
    status: str
    services: List[str] = None
    credentials_available: bool = False
    
    def __post_init__(self):
        if self.services is None:
            self.services = []


@dataclass
class NetworkInfo:
    """Network information gathered from network analyzer"""
    network_id: str
    network_range: str
    gateway: str
    accessible_hosts: List[str] = None
    network_topology: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.accessible_hosts is None:
            self.accessible_hosts = []
        if self.network_topology is None:
            self.network_topology = {}


@dataclass
class CredentialInfo:
    """Credential information (without actual credentials)"""
    asset_id: str
    credential_types: List[str]
    authentication_methods: List[str]
    access_validated: bool = False


@dataclass
class EnrichedIntent:
    """Intent enriched with gathered information"""
    original_intent: ProcessedIntent
    assets: List[AssetInfo] = None
    network_info: List[NetworkInfo] = None
    credentials: List[CredentialInfo] = None
    validation_results: Dict[str, Any] = None
    information_complete: bool = False
    missing_information: List[str] = None
    
    def __post_init__(self):
        if self.assets is None:
            self.assets = []
        if self.network_info is None:
            self.network_info = []
        if self.credentials is None:
            self.credentials = []
        if self.validation_results is None:
            self.validation_results = {}
        if self.missing_information is None:
            self.missing_information = []


class InformationGatherer:
    """
    Gathers additional information needed for fulfillment
    """
    
    def __init__(self, asset_client=None, network_client=None, llm_engine=None):
        """Initialize the Information Gatherer"""
        self.asset_client = asset_client
        self.network_client = network_client
        self.llm_engine = llm_engine
        logger.info("Information Gatherer initialized")
    
    async def gather_missing_information(self, processed_intent: ProcessedIntent, resource_mapping: ResourceMapping) -> EnrichedIntent:
        """
        Gather additional information needed for fulfillment
        
        Args:
            processed_intent: Processed intent from IntentProcessor
            resource_mapping: Resource mapping from ResourceMapper
            
        Returns:
            EnrichedIntent with all gathered information
        """
        try:
            logger.info(f"Gathering missing information for intent {processed_intent.intent_id}")
            
            enriched_intent = EnrichedIntent(original_intent=processed_intent)
            
            # Gather asset information if needed
            if processed_intent.requires_asset_info:
                enriched_intent.assets = await self._gather_asset_information(processed_intent)
            
            # Gather network information if needed
            if processed_intent.requires_network_info:
                enriched_intent.network_info = await self._gather_network_information(processed_intent, enriched_intent.assets)
            
            # Gather credential information if needed
            if processed_intent.requires_credentials:
                enriched_intent.credentials = await self._gather_credential_information(processed_intent, enriched_intent.assets)
            
            # Validate gathered information
            enriched_intent.validation_results = await self._validate_gathered_information(enriched_intent)
            
            # Check if information is complete
            enriched_intent.missing_information = await self._identify_missing_information(enriched_intent)
            enriched_intent.information_complete = len(enriched_intent.missing_information) == 0
            
            logger.info(f"Information gathering completed. Complete: {enriched_intent.information_complete}")
            return enriched_intent
            
        except Exception as e:
            logger.error(f"Failed to gather missing information: {str(e)}")
            raise
    
    async def _gather_asset_information(self, processed_intent: ProcessedIntent) -> List[AssetInfo]:
        """Gather asset information from asset service"""
        assets = []
        
        try:
            if not self.asset_client:
                logger.warning("Asset client not available - cannot gather asset information")
                return assets
            
            # If specific targets are mentioned, query for them
            if processed_intent.target_systems:
                for target in processed_intent.target_systems:
                    try:
                        # Query asset service for this target
                        asset_data = await self._query_asset_by_name(target)
                        if asset_data:
                            asset_info = AssetInfo(
                                asset_id=asset_data.get("id", target),
                                hostname=asset_data.get("hostname", target),
                                ip_address=asset_data.get("ip_address", ""),
                                os_type=asset_data.get("os_type", "unknown"),
                                status=asset_data.get("status", "unknown"),
                                services=asset_data.get("services", []),
                                credentials_available=asset_data.get("has_credentials", False)
                            )
                            assets.append(asset_info)
                        else:
                            logger.warning(f"Asset not found: {target}")
                    except Exception as e:
                        logger.error(f"Failed to query asset {target}: {str(e)}")
            else:
                # No specific targets - use LLM to determine what assets might be needed
                if self.llm_engine:
                    suggested_targets = await self._suggest_targets_with_llm(processed_intent)
                    for target in suggested_targets:
                        asset_data = await self._query_asset_by_name(target)
                        if asset_data:
                            asset_info = AssetInfo(
                                asset_id=asset_data.get("id", target),
                                hostname=asset_data.get("hostname", target),
                                ip_address=asset_data.get("ip_address", ""),
                                os_type=asset_data.get("os_type", "unknown"),
                                status=asset_data.get("status", "unknown"),
                                services=asset_data.get("services", []),
                                credentials_available=asset_data.get("has_credentials", False)
                            )
                            assets.append(asset_info)
            
            logger.info(f"Gathered information for {len(assets)} assets")
            return assets
            
        except Exception as e:
            logger.error(f"Failed to gather asset information: {str(e)}")
            return assets
    
    async def _gather_network_information(self, processed_intent: ProcessedIntent, assets: List[AssetInfo]) -> List[NetworkInfo]:
        """Gather network information from network analyzer"""
        network_info = []
        
        try:
            if not self.network_client:
                logger.warning("Network client not available - cannot gather network information")
                return network_info
            
            # Gather network information for each asset
            for asset in assets:
                try:
                    # Query network analyzer for this asset's network
                    network_data = await self._query_network_for_asset(asset)
                    if network_data:
                        net_info = NetworkInfo(
                            network_id=network_data.get("network_id", f"net_{asset.asset_id}"),
                            network_range=network_data.get("network_range", ""),
                            gateway=network_data.get("gateway", ""),
                            accessible_hosts=network_data.get("accessible_hosts", []),
                            network_topology=network_data.get("topology", {})
                        )
                        network_info.append(net_info)
                except Exception as e:
                    logger.error(f"Failed to gather network info for asset {asset.asset_id}: {str(e)}")
            
            logger.info(f"Gathered network information for {len(network_info)} networks")
            return network_info
            
        except Exception as e:
            logger.error(f"Failed to gather network information: {str(e)}")
            return network_info
    
    async def _gather_credential_information(self, processed_intent: ProcessedIntent, assets: List[AssetInfo]) -> List[CredentialInfo]:
        """Gather credential information (without actual credentials)"""
        credentials = []
        
        try:
            if not self.asset_client:
                logger.warning("Asset client not available - cannot gather credential information")
                return credentials
            
            # Check credential availability for each asset
            for asset in assets:
                try:
                    # Query asset service for credential information
                    cred_data = await self._query_credentials_for_asset(asset.asset_id)
                    if cred_data:
                        cred_info = CredentialInfo(
                            asset_id=asset.asset_id,
                            credential_types=cred_data.get("types", []),
                            authentication_methods=cred_data.get("auth_methods", []),
                            access_validated=cred_data.get("validated", False)
                        )
                        credentials.append(cred_info)
                except Exception as e:
                    logger.error(f"Failed to gather credential info for asset {asset.asset_id}: {str(e)}")
            
            logger.info(f"Gathered credential information for {len(credentials)} assets")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to gather credential information: {str(e)}")
            return credentials
    
    async def _validate_gathered_information(self, enriched_intent: EnrichedIntent) -> Dict[str, Any]:
        """Validate the gathered information"""
        validation_results = {
            "assets_valid": True,
            "network_accessible": True,
            "credentials_available": True,
            "validation_errors": []
        }
        
        try:
            # 🚨 HARDCODED LOGIC VIOLATION DETECTED 🚨
            # This validation was using hardcoded status checks instead of LLM analysis
            
            # Use LLM to validate the gathered information intelligently
            validation_prompt = f"""
            Analyze the following gathered information and determine if it's sufficient and valid for the intended operation:
            
            Original Intent: {enriched_intent.original_intent.description}
            Risk Level: {enriched_intent.original_intent.risk_level.value}
            
            Assets: {[{'hostname': a.hostname, 'status': a.status, 'credentials_available': a.credentials_available} for a in enriched_intent.assets]}
            Network Info: {[{'network_id': n.network_id, 'accessible_hosts': len(n.accessible_hosts)} for n in enriched_intent.network_info]}
            
            Respond with JSON:
            {{
                "assets_valid": true/false,
                "network_accessible": true/false, 
                "credentials_available": true/false,
                "validation_errors": ["list of specific issues if any"],
                "reasoning": "explanation of validation decision"
            }}
            """
            
            from ..llm_service import LLMService
            llm_service = LLMService()
            
            response = await llm_service.generate_response(validation_prompt)
            
            if response and isinstance(response, dict) and "generated_text" in response:
                import json
                try:
                    llm_validation = json.loads(response["generated_text"])
                    
                    # Use LLM's validation results
                    validation_results.update({
                        "assets_valid": llm_validation.get("assets_valid", True),
                        "network_accessible": llm_validation.get("network_accessible", True),
                        "credentials_available": llm_validation.get("credentials_available", True),
                        "validation_errors": llm_validation.get("validation_errors", [])
                    })
                    
                    logger.info(f"LLM validation completed: {llm_validation.get('reasoning', 'No reasoning provided')}")
                    return validation_results
                    
                except json.JSONDecodeError as e:
                    logger.error(f"LLM validation response not valid JSON: {e}")
                    raise RuntimeError(f"LLM validation failed to produce valid JSON: {e}")
            else:
                raise RuntimeError("LLM validation service failed to respond")
                
            logger.info(f"LLM validation completed with {len(validation_results['validation_errors'])} errors")
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate gathered information: {str(e)}")
            validation_results["validation_errors"].append(f"Validation failed: {str(e)}")
            return validation_results
    
    async def _identify_missing_information(self, enriched_intent: EnrichedIntent) -> List[str]:
        """Identify what information is still missing"""
        missing = []
        
        try:
            original_intent = enriched_intent.original_intent
            
            # Check if required asset information is missing
            if original_intent.requires_asset_info and not enriched_intent.assets:
                missing.append("Asset information required but not available")
            
            # Check if required network information is missing
            if original_intent.requires_network_info and not enriched_intent.network_info:
                missing.append("Network information required but not available")
            
            # Check if required credentials are missing
            if original_intent.requires_credentials and not enriched_intent.credentials:
                missing.append("Credential information required but not available")
            
            # Check for specific target systems if mentioned
            if original_intent.target_systems:
                found_targets = [asset.hostname for asset in enriched_intent.assets]
                for target in original_intent.target_systems:
                    if target not in found_targets:
                        missing.append(f"Target system '{target}' not found")
            
            # Use LLM to identify additional missing information
            if self.llm_engine and missing:
                additional_missing = await self._identify_missing_with_llm(enriched_intent)
                missing.extend(additional_missing)
            
            return missing
            
        except Exception as e:
            logger.error(f"Failed to identify missing information: {str(e)}")
            return [f"Error identifying missing information: {str(e)}"]
    
    async def _query_asset_by_name(self, asset_name: str) -> Optional[Dict[str, Any]]:
        """Query asset service for asset by name"""
        try:
            if not self.asset_client:
                return None
            
            # This would be the actual API call to asset service
            # For now, return mock data structure
            return {
                "id": f"asset_{asset_name}",
                "hostname": asset_name,
                "ip_address": "192.168.1.100",
                "os_type": "linux",
                "status": "online",
                "services": ["ssh", "http"],
                "has_credentials": True
            }
            
        except Exception as e:
            logger.error(f"Failed to query asset {asset_name}: {str(e)}")
            return None
    
    async def _query_network_for_asset(self, asset: AssetInfo) -> Optional[Dict[str, Any]]:
        """Query network analyzer for asset's network information"""
        try:
            if not self.network_client:
                return None
            
            # This would be the actual API call to network analyzer
            # For now, return mock data structure
            return {
                "network_id": f"net_{asset.asset_id}",
                "network_range": "192.168.1.0/24",
                "gateway": "192.168.1.1",
                "accessible_hosts": [asset.ip_address],
                "topology": {"type": "ethernet", "speed": "1Gbps"}
            }
            
        except Exception as e:
            logger.error(f"Failed to query network for asset {asset.asset_id}: {str(e)}")
            return None
    
    async def _query_credentials_for_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Query asset service for credential information"""
        try:
            if not self.asset_client:
                return None
            
            # This would be the actual API call to asset service
            # For now, return mock data structure
            return {
                "types": ["ssh_key", "password"],
                "auth_methods": ["public_key", "password"],
                "validated": True
            }
            
        except Exception as e:
            logger.error(f"Failed to query credentials for asset {asset_id}: {str(e)}")
            return None
    
    async def _suggest_targets_with_llm(self, processed_intent: ProcessedIntent) -> List[str]:
        """Use LLM to suggest target systems based on intent"""
        try:
            if not self.llm_engine:
                return []
            
            suggestion_prompt = f"""
            Based on this user intent, suggest what target systems might be involved:
            
            Intent: {processed_intent.description}
            Original Message: {processed_intent.original_message}
            Operations: {processed_intent.operations}
            
            Suggest specific server names, hostnames, or system identifiers that might be relevant.
            Respond with a JSON array of strings:
            ["server1", "web-server", "database-host"]
            """
            
            llm_response = await self.llm_engine.generate(suggestion_prompt)
            
            # Extract the generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            # Parse the response
            import json
            try:
                suggested_targets = json.loads(generated_text)
                if isinstance(suggested_targets, list):
                    return suggested_targets
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM target suggestions as JSON")
            
            return []
            
        except Exception as e:
            logger.warning(f"LLM target suggestion failed: {str(e)}")
            return []
    
    async def _identify_missing_with_llm(self, enriched_intent: EnrichedIntent) -> List[str]:
        """Use LLM to identify additional missing information"""
        try:
            if not self.llm_engine:
                return []
            
            analysis_prompt = f"""
            Analyze this intent and gathered information to identify what might still be missing:
            
            Original Intent: {enriched_intent.original_intent.description}
            Target Systems: {enriched_intent.original_intent.target_systems}
            Operations: {enriched_intent.original_intent.operations}
            
            Gathered Assets: {len(enriched_intent.assets)} assets
            Gathered Networks: {len(enriched_intent.network_info)} networks
            Gathered Credentials: {len(enriched_intent.credentials)} credential sets
            
            What additional information might be needed to successfully fulfill this intent?
            Consider: specific configuration details, dependencies, prerequisites, etc.
            
            Respond with a JSON array of strings describing missing information:
            ["Missing database connection details", "Need application version info"]
            """
            
            llm_response = await self.llm_engine.generate(analysis_prompt)
            
            # Extract the generated text
            if isinstance(llm_response, dict) and "generated_text" in llm_response:
                generated_text = llm_response["generated_text"]
            else:
                generated_text = str(llm_response)
            
            # Parse the response
            import json
            try:
                missing_info = json.loads(generated_text)
                if isinstance(missing_info, list):
                    return missing_info
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM missing information analysis as JSON")
            
            return []
            
        except Exception as e:
            logger.warning(f"LLM missing information analysis failed: {str(e)}")
            return []