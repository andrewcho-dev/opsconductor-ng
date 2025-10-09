#!/usr/bin/env python3
"""
Script to add /execute-plan endpoints to asset-service and network-service
"""

# Asset service execution code
ASSET_SERVICE_EXECUTION_ROUTES = '''
    def _setup_execution_routes(self):
        """Setup execution routes for AI-pipeline integration"""
        
        @self.app.post("/execute-plan")
        async def execute_plan_from_pipeline(request: Dict[str, Any]):
            """
            Execute an asset management plan from AI-pipeline
            
            Handles asset-specific tools:
            - asset_query: Query asset inventory
            - asset_create: Create new assets
            - asset_update: Update existing assets
            - asset_delete: Delete assets
            - asset_list: List assets
            
            Args:
                request: {
                    "execution_id": str,
                    "plan": dict,
                    "tenant_id": str,
                    "actor_id": int
                }
            
            Returns:
                Execution result with status, output, and timing
            """
            try:
                self.logger.info(f"Received asset execution request from ai-pipeline: {request.get('execution_id')}")
                
                execution_id = request.get("execution_id")
                plan = request.get("plan", {})
                steps = plan.get("steps", [])
                
                if not steps:
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "result": {},
                        "step_results": [],
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": "No steps in plan"
                    }
                
                # Execute each asset step
                step_results = []
                overall_success = True
                
                for idx, step in enumerate(steps):
                    tool = step.get("tool", "unknown")
                    inputs = step.get("inputs", {})
                    
                    self.logger.info(f"Executing asset step {idx + 1}/{len(steps)}: {tool}")
                    
                    try:
                        # Route to appropriate asset handler
                        if tool == "asset-query" or tool == "asset_query":
                            result = await self._execute_asset_query(inputs)
                        elif tool == "asset-create" or tool == "asset_create":
                            result = await self._execute_asset_create(inputs)
                        elif tool == "asset-update" or tool == "asset_update":
                            result = await self._execute_asset_update(inputs)
                        elif tool == "asset-delete" or tool == "asset_delete":
                            result = await self._execute_asset_delete(inputs)
                        elif tool == "asset-list" or tool == "asset_list":
                            result = await self._execute_asset_list(inputs)
                        else:
                            result = {
                                "success": False,
                                "message": f"Unknown asset tool: {tool}"
                            }
                        
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "completed" if result.get("success") else "failed",
                            "output": result,
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        
                        if not result.get("success"):
                            overall_success = False
                    
                    except Exception as e:
                        self.logger.error(f"Asset step {idx + 1} failed: {e}", exc_info=True)
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "failed",
                            "error": str(e),
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        overall_success = False
                
                # Return result to ai-pipeline
                return {
                    "execution_id": execution_id,
                    "status": "completed" if overall_success else "failed",
                    "result": {
                        "total_steps": len(steps),
                        "successful_steps": sum(1 for r in step_results if r.get("status") == "completed"),
                        "failed_steps": sum(1 for r in step_results if r.get("status") == "failed")
                    },
                    "step_results": step_results,
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": None if overall_success else "One or more asset steps failed"
                }
            
            except Exception as e:
                self.logger.error(f"Asset plan execution failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_asset_query(self, inputs: dict) -> dict:
        """Execute asset query"""
        # TODO: Implement actual asset query logic
        self.logger.info(f"Querying assets: {inputs}")
        return {
            "success": True,
            "message": "Asset query executed successfully (stub implementation)",
            "details": inputs,
            "assets": []
        }
    
    async def _execute_asset_create(self, inputs: dict) -> dict:
        """Execute asset creation"""
        # TODO: Implement actual asset creation logic
        self.logger.info(f"Creating asset: {inputs}")
        return {
            "success": True,
            "message": "Asset created successfully (stub implementation)",
            "details": inputs
        }
    
    async def _execute_asset_update(self, inputs: dict) -> dict:
        """Execute asset update"""
        # TODO: Implement actual asset update logic
        self.logger.info(f"Updating asset: {inputs}")
        return {
            "success": True,
            "message": "Asset updated successfully (stub implementation)",
            "details": inputs
        }
    
    async def _execute_asset_delete(self, inputs: dict) -> dict:
        """Execute asset deletion"""
        # TODO: Implement actual asset deletion logic
        self.logger.info(f"Deleting asset: {inputs}")
        return {
            "success": True,
            "message": "Asset deleted successfully (stub implementation)",
            "details": inputs
        }
    
    async def _execute_asset_list(self, inputs: dict) -> dict:
        """Execute asset listing"""
        # TODO: Implement actual asset listing logic
        self.logger.info(f"Listing assets: {inputs}")
        return {
            "success": True,
            "message": "Assets listed successfully (stub implementation)",
            "details": inputs,
            "assets": []
        }
'''

# Network service execution code
NETWORK_SERVICE_EXECUTION_ROUTES = '''
    def _setup_execution_routes(self):
        """Setup execution routes for AI-pipeline integration"""
        
        @self.app.post("/execute-plan")
        async def execute_plan_from_pipeline(request: Dict[str, Any]):
            """
            Execute a network analysis plan from AI-pipeline
            
            Handles network-specific tools:
            - tcpdump: Packet capture
            - tshark: Wireshark CLI
            - nmap: Network scanning
            - scapy: Packet manipulation
            - pyshark: Python packet analysis
            - And many more network analysis tools
            
            Args:
                request: {
                    "execution_id": str,
                    "plan": dict,
                    "tenant_id": str,
                    "actor_id": int
                }
            
            Returns:
                Execution result with status, output, and timing
            """
            try:
                self.logger.info(f"Received network execution request from ai-pipeline: {request.get('execution_id')}")
                
                execution_id = request.get("execution_id")
                plan = request.get("plan", {})
                steps = plan.get("steps", [])
                
                if not steps:
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "result": {},
                        "step_results": [],
                        "completed_at": datetime.utcnow().isoformat(),
                        "error_message": "No steps in plan"
                    }
                
                # Execute each network step
                step_results = []
                overall_success = True
                
                for idx, step in enumerate(steps):
                    tool = step.get("tool", "unknown")
                    inputs = step.get("inputs", {})
                    
                    self.logger.info(f"Executing network step {idx + 1}/{len(steps)}: {tool}")
                    
                    try:
                        # Execute network tool
                        result = await self._execute_network_tool(tool, inputs)
                        
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "completed" if result.get("success") else "failed",
                            "output": result,
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        
                        if not result.get("success"):
                            overall_success = False
                    
                    except Exception as e:
                        self.logger.error(f"Network step {idx + 1} failed: {e}", exc_info=True)
                        step_results.append({
                            "step_index": idx,
                            "tool": tool,
                            "status": "failed",
                            "error": str(e),
                            "completed_at": datetime.utcnow().isoformat()
                        })
                        overall_success = False
                
                # Return result to ai-pipeline
                return {
                    "execution_id": execution_id,
                    "status": "completed" if overall_success else "failed",
                    "result": {
                        "total_steps": len(steps),
                        "successful_steps": sum(1 for r in step_results if r.get("status") == "completed"),
                        "failed_steps": sum(1 for r in step_results if r.get("status") == "failed")
                    },
                    "step_results": step_results,
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": None if overall_success else "One or more network steps failed"
                }
            
            except Exception as e:
                self.logger.error(f"Network plan execution failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _execute_network_tool(self, tool: str, inputs: dict) -> dict:
        """Execute network analysis tool"""
        # TODO: Implement actual network tool execution logic
        self.logger.info(f"Executing network tool '{tool}': {inputs}")
        return {
            "success": True,
            "message": f"Network tool '{tool}' executed successfully (stub implementation)",
            "tool": tool,
            "details": inputs,
            "output": "Network analysis output would appear here"
        }
'''

print("=" * 80)
print("EXECUTION ENDPOINT CODE GENERATED")
print("=" * 80)
print("\nAsset Service Code:")
print(ASSET_SERVICE_EXECUTION_ROUTES)
print("\n" + "=" * 80)
print("\nNetwork Service Code:")
print(NETWORK_SERVICE_EXECUTION_ROUTES)
print("\n" + "=" * 80)
print("\nManual steps required:")
print("1. Add the code above to asset-service/main.py before 'if __name__ == \"__main__\"'")
print("2. Add the code above to network-service/main.py before 'if __name__ == \"__main__\"'")
print("3. Call self._setup_execution_routes() in each service's on_startup() method")