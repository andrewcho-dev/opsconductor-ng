"""
Pipeline Orchestrator V2 - Simplified Architecture

Uses the new Stage AB (Combined Understanding & Selection) instead of separate Stage A + Stage B.
This eliminates the fragile handoff and makes the system more reliable.

Pipeline Flow:
User Request → Stage AB (Understanding + Selection) → Stage C (Planner) → Stage D (Answerer) → Stage E (Executor) → Response
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from pipeline.stages.stage_ab.combined_selector import CombinedSelector
from pipeline.stages.stage_c.planner import StageCPlanner
from pipeline.stages.stage_d.answerer import StageDAnswerer
from pipeline.stages.stage_e.executor import StageEExecutor
from pipeline.schemas.response_v1 import ResponseV1, ResponseType, ConfidenceLevel as ResponseConfidenceLevel
from pipeline.conversation_history import get_conversation_manager

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stage enumeration for tracking and monitoring."""
    STAGE_AB = "stage_ab"  # Combined understanding + selection
    STAGE_C = "stage_c"
    STAGE_D = "stage_d"
    STAGE_E = "stage_e"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineMetrics:
    """Performance metrics for pipeline execution."""
    total_duration_ms: float
    stage_durations: Dict[str, float]
    memory_usage_mb: float
    request_id: str
    timestamp: float
    status: PipelineStatus
    error_details: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    response: ResponseV1
    metrics: PipelineMetrics
    intermediate_results: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class PipelineOrchestratorV2:
    """
    Simplified pipeline orchestrator using Stage AB (combined understanding + selection).
    
    This eliminates the Stage A → Stage B handoff that was causing capability extraction issues.
    """
    
    def __init__(self, llm_client=None):
        """Initialize the pipeline orchestrator with all stage components."""
        # Initialize LLM client if not provided
        if llm_client is None:
            from llm.factory import get_default_llm_client
            llm_client = get_default_llm_client()
        
        self.llm_client = llm_client
        
        # Initialize stages
        self.stage_ab = CombinedSelector(llm_client)  # NEW: Combined stage
        self.stage_c = StageCPlanner(llm_client)
        self.stage_d = StageDAnswerer(llm_client)
        self.stage_e = StageEExecutor()
        
        # Performance tracking
        self._active_requests: Dict[str, float] = {}
        self._completed_requests: List[PipelineMetrics] = []
        self._max_history = 1000
        
        # Health status
        self._last_health_check = time.time()
        self._health_status = "healthy"
        self._error_count = 0
        self._success_count = 0
    
    async def initialize(self):
        """Initialize the orchestrator and connect to LLM."""
        try:
            # Connect to LLM
            await self.llm_client.connect()
            if not self.llm_client.is_connected:
                raise Exception("Failed to connect to LLM")
            logger.info("✅ Pipeline Orchestrator V2 initialized successfully")
        except Exception as e:
            raise Exception(f"Orchestrator initialization failed: {str(e)}")
    
    async def process_request(
        self, 
        user_request: str, 
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> PipelineResult:
        """
        Process a user request through the simplified 3-stage pipeline.
        
        Args:
            user_request: The user's natural language request
            request_id: Optional request identifier for tracking
            context: Optional context information
            session_id: Optional session identifier for conversation history
            progress_callback: Optional callback for real-time progress updates
            
        Returns:
            PipelineResult containing the response and execution metrics
        """
        if request_id is None:
            request_id = str(uuid4())
        
        start_time = time.time()
        self._active_requests[request_id] = start_time
        
        stage_durations = {}
        intermediate_results = {}
        
        # Initialize context
        if context is None:
            context = {}
        
        # Add conversation history to context if session_id is provided
        if session_id:
            conversation_manager = get_conversation_manager()
            conversation_manager.add_message(session_id, "user", user_request)
            conversation_history = conversation_manager.get_formatted_history(session_id, max_messages=10)
            context["conversation_history"] = conversation_history
            context["session_id"] = session_id
            logger.info(f"Session {session_id}: {conversation_manager.get_message_count(session_id)} messages in history")
        
        try:
            logger.info(f"🚀 [REQUEST {request_id}] Starting pipeline V2 processing")
            logger.info(f"📝 User request: {user_request[:100]}...")
            
            # ============================================================
            # Stage AB: Combined Understanding + Selection
            # ============================================================
            logger.info(f"⏱️  [STAGE AB] Starting combined understanding + selection...")
            if progress_callback:
                await progress_callback("stage_ab", "start", {
                    "stage": "AB", 
                    "name": "Understanding & Selection", 
                    "message": "🧠 Analyzing request and selecting tools..."
                })
            
            stage_start = time.time()
            selection_result = await self.stage_ab.process(user_request, context)
            stage_durations["stage_ab"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_ab"] = selection_result
            
            logger.info(f"✅ [STAGE AB] Complete in {stage_durations['stage_ab']:.2f}ms")
            logger.info(f"   Selected {len(selection_result.selected_tools)} tools, next_stage={selection_result.next_stage}")
            
            if progress_callback:
                await progress_callback("stage_ab", "complete", {
                    "stage": "AB", 
                    "name": "Understanding & Selection", 
                    "duration_ms": stage_durations["stage_ab"], 
                    "message": f"✅ Analysis complete ({stage_durations['stage_ab']:.0f}ms)"
                })
            
            # ============================================================
            # ASSET VALIDATION: Verify all target hosts exist in asset database
            # ============================================================
            validation_error = await self._validate_target_assets(context)
            if validation_error:
                logger.warning(f"❌ Asset validation failed: {validation_error}")
                # Return error response immediately
                total_duration = (time.time() - start_time) * 1000
                error_response = ResponseV1(
                    response_type=ResponseType.ERROR,
                    message=validation_error,
                    confidence=ResponseConfidenceLevel.HIGH,
                    approval_required=False,
                    response_id=f"resp_error_{request_id}",
                    processing_time_ms=int(total_duration)
                )
                
                metrics = PipelineMetrics(
                    total_duration_ms=total_duration,
                    stage_durations=stage_durations,
                    memory_usage_mb=0,
                    request_id=request_id,
                    timestamp=start_time,
                    status=PipelineStatus.FAILED,
                    error_details=validation_error
                )
                
                return PipelineResult(
                    response=error_response,
                    metrics=metrics,
                    intermediate_results=intermediate_results,
                    success=False,
                    error_message=validation_error
                )
            
            # ============================================================
            # Stage C: Planning (if tools were selected)
            # ============================================================
            planning_result = None
            has_tools = len(selection_result.selected_tools) > 0
            
            if has_tools and selection_result.next_stage == "stage_c":
                logger.info(f"⏱️  [STAGE C] Starting plan creation...")
                if progress_callback:
                    await progress_callback("stage_c", "start", {
                        "stage": "C", 
                        "name": "Planning", 
                        "message": "📋 Creating execution plan..."
                    })
                
                stage_start = time.time()
                # Stage C expects a DecisionV1, so we need to create a minimal one from SelectionV1
                mock_decision = self._create_mock_decision_from_selection(selection_result, user_request)
                planning_result = await self.stage_c.create_plan(mock_decision, selection_result, context=context)
                stage_durations["stage_c"] = (time.time() - stage_start) * 1000
                intermediate_results["stage_c"] = planning_result
                
                logger.info(f"✅ [STAGE C] Complete in {stage_durations['stage_c']:.2f}ms")
                if planning_result and hasattr(planning_result, 'plan'):
                    # Convert ExecutionPlan to dict if needed
                    if isinstance(planning_result.plan, dict):
                        plan_dict = planning_result.plan
                    elif hasattr(planning_result.plan, 'dict'):
                        plan_dict = planning_result.plan.dict()
                    elif hasattr(planning_result.plan, 'model_dump'):
                        plan_dict = planning_result.plan.model_dump()
                    else:
                        plan_dict = {}
                    steps = plan_dict.get('steps', [])
                    logger.info(f"   Created plan with {len(steps)} steps")
                
                if progress_callback:
                    await progress_callback("stage_c", "complete", {
                        "stage": "C", 
                        "name": "Planning", 
                        "duration_ms": stage_durations["stage_c"], 
                        "message": f"✅ Planning complete ({stage_durations['stage_c']:.0f}ms)"
                    })
            else:
                logger.info("⏭️  Skipping Stage C: No tools selected or direct to answerer")
                stage_durations["stage_c"] = 0
            
            # ============================================================
            # Stage D: Response Generation
            # ============================================================
            logger.info(f"⏱️  [STAGE D] Starting response generation...")
            if progress_callback:
                await progress_callback("stage_d", "start", {
                    "stage": "D", 
                    "name": "Response Generation", 
                    "message": "💬 Generating response..."
                })
            
            stage_start = time.time()
            # Stage D also expects DecisionV1, so we use the mock decision
            mock_decision = self._create_mock_decision_from_selection(selection_result, user_request)
            response_result = await self.stage_d.generate_response(mock_decision, selection_result, planning_result, context)
            stage_durations["stage_d"] = (time.time() - stage_start) * 1000
            intermediate_results["stage_d"] = response_result
            
            logger.info(f"✅ [STAGE D] Complete in {stage_durations['stage_d']:.2f}ms")
            logger.info(f"   Response type: {response_result.response_type}, Approval required: {response_result.approval_required}")
            
            if progress_callback:
                await progress_callback("stage_d", "complete", {
                    "stage": "D", 
                    "name": "Response Generation", 
                    "duration_ms": stage_durations["stage_d"], 
                    "message": f"✅ Response complete ({stage_durations['stage_d']:.0f}ms)"
                })
            
            # ============================================================
            # Stage E: Execution (if plan exists and should be executed)
            # ============================================================
            should_execute = False
            
            if planning_result is None:
                logger.info("⏭️  Skipping Stage E: No execution plan (information-only request)")
            elif planning_result and hasattr(planning_result, 'plan') and planning_result.plan:
                plan_steps = planning_result.plan.get('steps', []) if isinstance(planning_result.plan, dict) else getattr(planning_result.plan, 'steps', [])
                if plan_steps and len(plan_steps) > 0:
                    # Check if approval is required
                    if response_result.approval_required:
                        logger.info("⏸️  Stage E: Execution requires approval - waiting for user confirmation")
                    else:
                        should_execute = True
            
            if should_execute:
                logger.info(f"⏱️  [STAGE E] Starting execution...")
                if progress_callback:
                    await progress_callback("stage_e", "start", {
                        "stage": "E", 
                        "name": "Execution", 
                        "message": "⚙️ Executing plan..."
                    })
                
                stage_start = time.time()
                execution_result = await self._execute_stage_e(planning_result, context, progress_callback)
                stage_durations["stage_e"] = (time.time() - stage_start) * 1000
                intermediate_results["stage_e"] = execution_result
                
                logger.info(f"✅ [STAGE E] Complete in {stage_durations['stage_e']:.2f}ms")
                
                if progress_callback:
                    await progress_callback("stage_e", "complete", {
                        "stage": "E", 
                        "name": "Execution", 
                        "duration_ms": stage_durations["stage_e"], 
                        "message": f"✅ Execution complete ({stage_durations['stage_e']:.0f}ms)"
                    })
                
                # Update response with execution results
                response_result = await self._update_response_with_execution(response_result, execution_result, context)
            else:
                stage_durations["stage_e"] = 0
            
            # ============================================================
            # Calculate final metrics and return result
            # ============================================================
            total_duration = (time.time() - start_time) * 1000
            
            metrics = PipelineMetrics(
                total_duration_ms=total_duration,
                stage_durations=stage_durations,
                memory_usage_mb=self._get_memory_usage(),
                request_id=request_id,
                timestamp=start_time,
                status=PipelineStatus.COMPLETED
            )
            
            # Store metrics
            self._completed_requests.append(metrics)
            if len(self._completed_requests) > self._max_history:
                self._completed_requests.pop(0)
            
            # Clean up active request
            if request_id in self._active_requests:
                del self._active_requests[request_id]
            
            self._success_count += 1
            
            # Add assistant response to conversation history
            if session_id:
                conversation_manager = get_conversation_manager()
                conversation_manager.add_message(session_id, "assistant", response_result.message)
            
            logger.info(f"✅ [REQUEST {request_id}] Pipeline complete in {total_duration:.2f}ms")
            
            return PipelineResult(
                response=response_result,
                metrics=metrics,
                intermediate_results=intermediate_results,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ [REQUEST {request_id}] Pipeline failed: {str(e)}", exc_info=True)
            
            # Calculate metrics for failed request
            total_duration = (time.time() - start_time) * 1000
            metrics = PipelineMetrics(
                total_duration_ms=total_duration,
                stage_durations=stage_durations,
                memory_usage_mb=self._get_memory_usage(),
                request_id=request_id,
                timestamp=start_time,
                status=PipelineStatus.FAILED,
                error_details=str(e)
            )
            
            # Clean up
            if request_id in self._active_requests:
                del self._active_requests[request_id]
            
            self._error_count += 1
            
            # Create error response
            error_response = ResponseV1(
                response_id=f"resp_{request_id}",
                response_type=ResponseType.ERROR,
                message=f"I encountered an error processing your request: {str(e)}",
                confidence=ResponseConfidenceLevel.LOW,
                approval_required=False,
                processing_time_ms=int(total_duration)
            )
            
            return PipelineResult(
                response=error_response,
                metrics=metrics,
                intermediate_results=intermediate_results,
                success=False,
                error_message=str(e)
            )
    
    def _create_mock_decision_from_selection(self, selection, user_request: str):
        """
        Create a minimal DecisionV1 object from SelectionV1 for compatibility with Stage C/D.
        
        This is a temporary bridge until we refactor Stage C/D to work directly with SelectionV1.
        """
        from pipeline.schemas.decision_v1 import DecisionV1, IntentV1, DecisionType, ConfidenceLevel, RiskLevel
        
        # Extract intent information from selection metadata (if available)
        # For now, we'll create a minimal intent
        intent = IntentV1(
            category="automation",  # Default category
            action="execute_request",  # Generic action
            confidence=selection.selection_confidence,
            capabilities=[]  # Capabilities already used for tool selection
        )
        
        return DecisionV1(
            decision_id=selection.decision_id,
            decision_type=DecisionType.ACTION if selection.selected_tools else DecisionType.INFO,
            timestamp=selection.timestamp,
            intent=intent,
            entities=[],  # Entities already extracted during selection
            overall_confidence=selection.selection_confidence,
            confidence_level=ConfidenceLevel.HIGH if selection.selection_confidence >= 0.8 else 
                           (ConfidenceLevel.MEDIUM if selection.selection_confidence >= 0.5 else ConfidenceLevel.LOW),
            risk_level=selection.policy.risk_level,
            original_request=user_request,
            context={},
            requires_approval=selection.policy.requires_approval,
            next_stage="stage_c" if selection.selected_tools else "stage_d"
        )
    
    async def _validate_target_assets(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Validate that all target hosts (hostnames/IPs) exist in the asset database.
        
        Args:
            context: Pipeline context containing entities from Stage AB
        
        Returns:
            Error message if validation fails, None if validation passes
        """
        import aiohttp
        
        # Extract target hosts from entities in context
        entities = context.get("entities", [])
        target_hosts = []
        for entity in entities:
            entity_type = entity.get("type", "")
            entity_value = entity.get("value", "")
            if entity_type in ['hostname', 'ip_address', 'target_host']:
                target_hosts.append(entity_value)
        
        # If no target hosts found, validation passes (might be an info query)
        if not target_hosts:
            logger.debug("No target hosts found in entities, skipping asset validation")
            return None
        
        # Check each target host against asset database
        asset_service_url = os.getenv("ASSET_SERVICE_URL", "http://asset-service:3002")
        invalid_hosts = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for host in target_hosts:
                    # Query asset service to see if this host exists
                    try:
                        async with session.get(
                            f"{asset_service_url}/",
                            params={"search": host, "limit": 10},
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                assets = data.get("data", {}).get("assets", [])
                                
                                # Check if any asset matches this host (by IP or hostname)
                                found = False
                                for asset in assets:
                                    if (asset.get("ip_address") == host or 
                                        asset.get("hostname") == host):
                                        found = True
                                        break
                                
                                if not found:
                                    invalid_hosts.append(host)
                                    logger.warning(f"Host '{host}' not found in asset database")
                            else:
                                logger.error(f"Asset service returned status {response.status} for host '{host}'")
                                # Don't block on asset service errors, just log
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout querying asset service for host '{host}'")
                        # Don't block on timeouts
                    except Exception as e:
                        logger.error(f"Error querying asset service for host '{host}': {e}")
                        # Don't block on errors
        except Exception as e:
            logger.error(f"Failed to validate assets: {e}")
            # Don't block the entire request if asset service is down
            return None
        
        # If any hosts are invalid, return error message
        if invalid_hosts:
            if len(invalid_hosts) == 1:
                return f"❌ **Asset Not Found**: The hostname/IP address `{invalid_hosts[0]}` is not defined in the asset database. Please verify the hostname/IP address or add it to the asset database first."
            else:
                hosts_list = "`, `".join(invalid_hosts)
                return f"❌ **Assets Not Found**: The following hostname/IP addresses are not defined in the asset database: `{hosts_list}`. Please verify these addresses or add them to the asset database first."
        
        logger.info(f"✅ Asset validation passed for hosts: {target_hosts}")
        return None
    
    async def _execute_stage_e(self, planning_result, context, progress_callback):
        """Execute Stage E (Executor)"""
        from execution.dtos import ExecutionRequest
        
        # Convert planning result to execution request
        # ExecutionRequest expects plan as a dict, so convert ExecutionPlan to dict
        plan_dict = planning_result.plan.model_dump() if hasattr(planning_result.plan, 'model_dump') else planning_result.plan
        
        execution_request = ExecutionRequest(
            plan=plan_dict,
            context=context or {}
        )
        
        # Get tenant_id and actor_id from context, or use defaults
        tenant_id = context.get("tenant_id", "default") if context else "default"
        actor_id = context.get("actor_id", 1) if context else 1
        
        # Execute with progress tracking
        return await self.stage_e.execute(execution_request, tenant_id, actor_id)
    
    async def _update_response_with_execution(self, response, execution_result, context):
        """Update response with execution results"""
        from execution.models import ExecutionStatus
        
        if not execution_result:
            return response
        
        # Extract execution status and results
        status = execution_result.status if hasattr(execution_result, 'status') else None
        
        # Build execution summary - CONCISE VERSION
        if status == ExecutionStatus.COMPLETED:
            execution_summary = ""
            
            # Add step results if available - check both .step_results attribute and .result['step_results']
            step_results = None
            if hasattr(execution_result, 'step_results') and execution_result.step_results:
                step_results = execution_result.step_results
            elif hasattr(execution_result, 'result') and isinstance(execution_result.result, dict):
                step_results = execution_result.result.get('step_results')
            
            if step_results:
                for i, step_result in enumerate(step_results, 1):
                    step_status = step_result.get('status', 'unknown')
                    
                    # Show output for successful commands (stdout for commands, output for API tools)
                    if step_status == 'completed' or step_status == 'success':
                        # Check for stdout (command-based tools)
                        if step_result.get('stdout'):
                            stdout = step_result['stdout'].strip()
                            # Limit output to first 100000 chars to avoid overwhelming the user
                            if len(stdout) > 100000:
                                stdout = stdout[:100000] + "...(truncated)"
                            
                            # Just display the output as-is (hostname is now included in the PowerShell output itself)
                            execution_summary += f"```text\n{stdout}\n```\n"
                        
                        # Check for output (API-based tools like asset-query)
                        elif step_result.get('output'):
                            import json
                            output_data = step_result['output']
                            
                            # Handle asset-query results
                            if isinstance(output_data, dict):
                                if 'assets' in output_data and 'count' in output_data:
                                    # Asset query result - provide count and CSV format
                                    count = output_data.get('count', 0)
                                    assets = output_data.get('assets', [])
                                    execution_summary += f"**Found {count} asset(s)**\n\n"
                                    
                                    # Provide results in downloadable CSV format
                                    if assets:
                                        csv_lines = ["Hostname,IP Address,OS Type,OS Version,Status,Tags"]
                                        for asset in assets:
                                            hostname = asset.get('hostname', 'Unknown')
                                            ip = asset.get('ip_address', 'N/A')
                                            os_type = asset.get('os_type', '')
                                            os_version = asset.get('os_version', '')
                                            status = asset.get('status', '')
                                            tags = '|'.join(asset.get('tags', []))
                                            csv_lines.append(f'"{hostname}","{ip}","{os_type}","{os_version}","{status}","{tags}"')
                                        csv_output = '\n'.join(csv_lines)
                                        execution_summary += f"```csv\n{csv_output}\n```\n"
                                else:
                                    # Generic JSON output
                                    output_json = json.dumps(output_data, indent=2)
                                    if len(output_json) > 10000:
                                        output_json = output_json[:10000] + "...(truncated)"
                                    execution_summary += f"```json\n{output_json}\n```\n"
                    
                    # Show errors if any (but filter out PowerShell CLIXML progress messages)
                    if step_result.get('stderr'):
                        stderr = step_result['stderr'].strip()
                        # Filter out PowerShell progress CLIXML (not real errors)
                        if stderr and not (stderr.startswith('#< CLIXML') and 'progress' in stderr.lower()):
                            execution_summary += f"⚠️ Warnings/Errors:\n```text\n{stderr}\n```\n"
            
            # Replace the verbose message with just the output
            response.message = execution_summary.strip() if execution_summary.strip() else "Execution completed."
            
        elif status == ExecutionStatus.FAILED:
            error_msg = execution_result.error_message if hasattr(execution_result, 'error_message') else "Unknown error"
            response.message = f"{response.message}\n\n❌ **Execution failed:** {error_msg}"
        
        # Update response type to indicate execution happened
        if response.response_type == ResponseType.EXECUTION_READY:
            response.response_type = ResponseType.INFORMATION  # Change to information since execution is done
        
        return response
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on all pipeline components.
        """
        health_status = {
            "orchestrator": "healthy",
            "version": "2.0.0",
            "stages": {},
            "metrics": {
                "active_requests": len(self._active_requests),
                "completed_requests": len(self._completed_requests),
                "success_count": self._success_count,
                "error_count": self._error_count,
                "success_rate": self._success_count / max(1, self._success_count + self._error_count)
            },
            "timestamp": time.time()
        }
        
        try:
            # Check Stage AB
            stage_ab_health = await self.stage_ab.health_check()
            health_status["stages"]["stage_ab"] = stage_ab_health
            
            # Check LLM
            llm_healthy = await self.llm_client.health_check()
            health_status["llm"] = "healthy" if llm_healthy else "unhealthy"
            
            # Overall health
            if not llm_healthy or stage_ab_health.get("stage_ab") != "healthy":
                health_status["orchestrator"] = "degraded"
            
        except Exception as e:
            health_status["orchestrator"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        if not self._completed_requests:
            return {
                "total_requests": 0,
                "average_duration_ms": 0,
                "stage_averages": {}
            }
        
        total_duration = sum(m.total_duration_ms for m in self._completed_requests)
        avg_duration = total_duration / len(self._completed_requests)
        
        # Calculate stage averages
        stage_averages = {}
        for stage in ["stage_ab", "stage_c", "stage_d", "stage_e"]:
            stage_durations = [m.stage_durations.get(stage, 0) for m in self._completed_requests]
            stage_averages[stage] = sum(stage_durations) / len(stage_durations)
        
        return {
            "total_requests": len(self._completed_requests),
            "average_duration_ms": avg_duration,
            "stage_averages": stage_averages,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": self._success_count / max(1, self._success_count + self._error_count)
        }


# ============================================================================
# GLOBAL ORCHESTRATOR INSTANCE (for backward compatibility)
# ============================================================================

_pipeline_orchestrator: Optional[PipelineOrchestratorV2] = None


async def get_pipeline_orchestrator(llm_client=None) -> PipelineOrchestratorV2:
    """
    Get the global pipeline orchestrator V2 instance.
    
    This function provides backward compatibility with V1 API.
    
    Args:
        llm_client: Optional LLM client instance
        
    Returns:
        PipelineOrchestratorV2 instance
    """
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestratorV2(llm_client)
        await _pipeline_orchestrator.initialize()
    return _pipeline_orchestrator


async def process_user_request(user_request: str, request_id: Optional[str] = None) -> PipelineResult:
    """
    Convenience function to process a user request through Pipeline V2.
    
    This function provides backward compatibility with V1 API.
    
    Args:
        user_request: The user's natural language request
        request_id: Optional request identifier for tracking
        
    Returns:
        PipelineResult containing the response and execution metrics
    """
    orchestrator = await get_pipeline_orchestrator()
    return await orchestrator.process_request(user_request, request_id)