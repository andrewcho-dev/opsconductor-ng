"""
Automation Query Handler
Handles job, workflow, and automation-related queries
"""

import logging
from typing import Dict, List, Any
from .base_handler import BaseQueryHandler

logger = logging.getLogger(__name__)

class AutomationQueryHandler(BaseQueryHandler):
    """Handles automation-related queries"""
    
    async def get_supported_intents(self) -> List[str]:
        """Return supported automation intents"""
        return [
            "query_jobs",
            "query_workflows", 
            "query_error_analysis",
            "query_job_execution_details",
            "query_job_scheduling",
            "query_workflow_step_analysis",
            "query_task_queue",
            "execute_command",
            "execute_powershell",
            "execute_bash",
            "remote_execution",
            "create_job",
            "execute_job",
            "stop_job"
        ]
    
    async def handle_query(self, intent: str, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Route automation queries to appropriate handlers"""
        try:
            if intent == "query_jobs":
                return await self.handle_job_query(message, context)
            elif intent == "query_workflows":
                return await self.handle_workflow_query(message, context)
            elif intent == "query_error_analysis":
                return await self.handle_error_analysis_query(message, context)
            elif intent == "query_job_execution_details":
                return await self.handle_job_execution_details_query(message, context)
            elif intent == "query_job_scheduling":
                return await self.handle_job_scheduling_query(message, context)
            elif intent == "query_workflow_step_analysis":
                return await self.handle_workflow_step_analysis_query(message, context)
            elif intent == "query_task_queue":
                return await self.handle_task_queue_query(message, context)
            elif intent in ["execute_command", "execute_powershell", "execute_bash", "remote_execution"]:
                return await self.handle_command_execution(message, context, intent)
            elif intent == "create_job":
                return await self.handle_job_creation(message, context)
            elif intent == "execute_job":
                return await self.handle_job_execution(message, context)
            elif intent == "stop_job":
                return await self.handle_job_stop(message, context)
            else:
                return self.create_error_response(intent, Exception(f"Unsupported intent: {intent}"))
                
        except Exception as e:
            return self.create_error_response(intent, e)
    
    async def handle_job_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle job-related queries"""
        try:
            # Get jobs from automation service
            jobs = await self.automation_client.list_ai_jobs(limit=100)
            
            if not jobs:
                return self.create_success_response(
                    "query_jobs",
                    "⚙️ **No jobs found**\n\nNo automation jobs are currently available. Create some jobs to get started!",
                    {"jobs_count": 0}
                )
            
            message_lower = message.lower()
            
            # Filter jobs based on query
            if 'failed' in message_lower:
                filtered_jobs = [j for j in jobs if j.get('status') == 'failed']
                filter_desc = "failed jobs"
            elif 'running' in message_lower:
                filtered_jobs = [j for j in jobs if j.get('status') == 'running']
                filter_desc = "running jobs"
            elif 'completed' in message_lower or 'success' in message_lower:
                filtered_jobs = [j for j in jobs if j.get('status') == 'completed']
                filter_desc = "completed jobs"
            elif 'pending' in message_lower or 'queued' in message_lower:
                filtered_jobs = [j for j in jobs if j.get('status') == 'pending']
                filter_desc = "pending jobs"
            elif 'recent' in message_lower or 'latest' in message_lower:
                filtered_jobs = jobs[:10]  # Most recent 10
                filter_desc = "recent jobs"
            elif 'today' in message_lower:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                filtered_jobs = [j for j in jobs if j.get('created_at', '').startswith(today)]
                filter_desc = "today's jobs"
            else:
                filtered_jobs = jobs[:15]  # Default recent 15
                filter_desc = "jobs"
            
            response = f"⚙️ **Job Query - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_jobs)} {filter_desc}\n\n"
            
            if not filtered_jobs:
                response += f"No {filter_desc} found.\n"
                response += f"Total jobs in system: {len(jobs)}\n\n"
                
                # Suggest alternatives
                if 'failed' in message_lower:
                    completed_count = len([j for j in jobs if j.get('status') == 'completed'])
                    if completed_count > 0:
                        response += f"💡 **Good news:** {completed_count} jobs completed successfully!"
                elif 'running' in message_lower:
                    response += "💡 **Info:** No jobs are currently running. All workers are idle."
            else:
                # Show job details
                for i, job in enumerate(filtered_jobs[:8]):
                    job_name = job.get('name', 'Unknown Job')
                    job_id = job.get('id', 'Unknown')
                    job_status = job.get('status', 'unknown')
                    created_at = job.get('created_at', 'Unknown')
                    duration = job.get('duration', 'Unknown')
                    target_count = len(job.get('targets', []))
                    
                    status_emoji = '✅' if job_status == 'completed' else '❌' if job_status == 'failed' else '🔄' if job_status == 'running' else '⏳'
                    
                    response += f"**{i+1}. {job_name}** {status_emoji}\n"
                    response += f"   • ID: {job_id}\n"
                    response += f"   • Status: {job_status}\n"
                    response += f"   • Created: {created_at}\n"
                    response += f"   • Duration: {duration}\n"
                    response += f"   • Targets: {target_count}\n\n"
                
                if len(filtered_jobs) > 8:
                    response += f"... and {len(filtered_jobs) - 8} more {filter_desc}\n\n"
                
                # Job statistics
                completed_count = len([j for j in filtered_jobs if j.get('status') == 'completed'])
                failed_count = len([j for j in filtered_jobs if j.get('status') == 'failed'])
                running_count = len([j for j in filtered_jobs if j.get('status') == 'running'])
                pending_count = len([j for j in filtered_jobs if j.get('status') == 'pending'])
                
                response += f"**Status Summary:**\n"
                response += f"• Completed: {completed_count} ({(completed_count/len(filtered_jobs)*100):.1f}%)\n"
                response += f"• Failed: {failed_count} ({(failed_count/len(filtered_jobs)*100):.1f}%)\n"
                response += f"• Running: {running_count}\n"
                response += f"• Pending: {pending_count}\n"
                
                # Success rate
                if completed_count + failed_count > 0:
                    success_rate = (completed_count / (completed_count + failed_count)) * 100
                    response += f"\n**Success Rate:** {success_rate:.1f}%\n"
                
                # Most common job types
                job_types = {}
                for job in filtered_jobs:
                    job_type = job.get('type', 'unknown')
                    job_types[job_type] = job_types.get(job_type, 0) + 1
                
                if len(job_types) > 1:
                    response += f"\n**Job Types:**\n"
                    for job_type, count in sorted(job_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                        response += f"• {job_type.title()}: {count} jobs\n"
            
            return self.create_success_response(
                "query_jobs",
                response,
                {
                    "jobs_found": len(filtered_jobs),
                    "total_jobs": len(jobs),
                    "filter_description": filter_desc,
                    "completed_count": len([j for j in filtered_jobs if j.get('status') == 'completed']),
                    "failed_count": len([j for j in filtered_jobs if j.get('status') == 'failed']),
                    "running_count": len([j for j in filtered_jobs if j.get('status') == 'running'])
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_jobs", e)
    
    async def handle_workflow_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle workflow-related queries"""
        try:
            # Get workflows from automation service
            workflows = await self.automation_client.list_workflows()
            
            if not workflows:
                return self.create_success_response(
                    "query_workflows",
                    "🔄 **No workflows found**\n\nNo workflows are currently configured. Create some workflows to automate complex processes!",
                    {"workflows_count": 0}
                )
            
            message_lower = message.lower()
            
            # Check if asking for specific workflow
            workflow_name = None
            for workflow in workflows:
                if workflow.get('name', '').lower() in message_lower:
                    workflow_name = workflow.get('name')
                    break
            
            if workflow_name:
                # Show specific workflow details
                target_workflow = next((w for w in workflows if w.get('name') == workflow_name), None)
                if target_workflow:
                    response = f"🔄 **Workflow - {workflow_name}**\n\n"
                    response += f"**ID:** {target_workflow.get('id')}\n"
                    response += f"**Description:** {target_workflow.get('description', 'No description')}\n"
                    response += f"**Status:** {target_workflow.get('status', 'unknown')}\n"
                    response += f"**Created:** {target_workflow.get('created_at', 'Unknown')}\n"
                    
                    # Get workflow steps
                    steps = target_workflow.get('steps', [])
                    response += f"**Steps:** {len(steps)}\n\n"
                    
                    if steps:
                        response += "**Workflow Steps:**\n"
                        for i, step in enumerate(steps):
                            step_name = step.get('name', f'Step {i+1}')
                            step_type = step.get('type', 'unknown')
                            response += f"{i+1}. **{step_name}** ({step_type})\n"
                        response += "\n"
                    
                    # Get recent executions
                    executions = await self.automation_client.get_workflow_executions(target_workflow['id'])
                    if executions:
                        response += f"**Recent Executions ({len(executions)}):**\n"
                        for i, execution in enumerate(executions[:3]):
                            exec_status = execution.get('status', 'unknown')
                            exec_date = execution.get('started_at', 'Unknown')
                            status_emoji = '✅' if exec_status == 'completed' else '❌' if exec_status == 'failed' else '🔄'
                            
                            response += f"• {exec_date} {status_emoji} ({exec_status})\n"
                        
                        if len(executions) > 3:
                            response += f"... and {len(executions) - 3} more executions\n"
                    else:
                        response += "**No recent executions**\n"
                else:
                    response = f"🔄 **Workflow '{workflow_name}' not found**\n\n"
                    response += f"Available workflows: {len(workflows)}\n\n"
                    response += "**Available Workflows:**\n"
                    for i, workflow in enumerate(workflows[:5]):
                        response += f"{i+1}. {workflow.get('name', 'Unknown')}\n"
            else:
                # Show workflows overview
                response = f"🔄 **Workflows Overview**\n\n"
                response += f"**Total Workflows:** {len(workflows)}\n\n"
                
                # Filter workflows based on query
                if 'active' in message_lower:
                    filtered_workflows = [w for w in workflows if w.get('status') == 'active']
                    filter_desc = "active workflows"
                elif 'disabled' in message_lower or 'inactive' in message_lower:
                    filtered_workflows = [w for w in workflows if w.get('status') == 'disabled']
                    filter_desc = "disabled workflows"
                else:
                    filtered_workflows = workflows
                    filter_desc = "workflows"
                
                response += f"**{filter_desc.title()} ({len(filtered_workflows)}):**\n\n"
                
                for i, workflow in enumerate(filtered_workflows[:8]):
                    workflow_name = workflow.get('name', 'Unknown')
                    workflow_desc = workflow.get('description', 'No description')
                    workflow_status = workflow.get('status', 'unknown')
                    step_count = len(workflow.get('steps', []))
                    
                    status_emoji = '✅' if workflow_status == 'active' else '❌' if workflow_status == 'disabled' else '⏳'
                    
                    response += f"**{i+1}. {workflow_name}** {status_emoji}\n"
                    response += f"   • Description: {workflow_desc[:50]}{'...' if len(workflow_desc) > 50 else ''}\n"
                    response += f"   • Status: {workflow_status}\n"
                    response += f"   • Steps: {step_count}\n\n"
                
                if len(filtered_workflows) > 8:
                    response += f"... and {len(filtered_workflows) - 8} more {filter_desc}\n\n"
                
                # Workflow statistics
                active_count = len([w for w in workflows if w.get('status') == 'active'])
                disabled_count = len([w for w in workflows if w.get('status') == 'disabled'])
                
                response += f"**Status Summary:**\n"
                response += f"• Active: {active_count}\n"
                response += f"• Disabled: {disabled_count}\n"
                
                # Complexity analysis
                simple_workflows = len([w for w in workflows if len(w.get('steps', [])) <= 3])
                complex_workflows = len([w for w in workflows if len(w.get('steps', [])) > 8])
                
                response += f"\n**Complexity:**\n"
                response += f"• Simple (≤3 steps): {simple_workflows}\n"
                response += f"• Complex (>8 steps): {complex_workflows}\n"
            
            return self.create_success_response(
                "query_workflows",
                response,
                {
                    "workflows_count": len(workflows),
                    "specific_workflow": workflow_name,
                    "active_count": len([w for w in workflows if w.get('status') == 'active']),
                    "disabled_count": len([w for w in workflows if w.get('status') == 'disabled'])
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_workflows", e)
    
    async def handle_error_analysis_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle error analysis queries"""
        try:
            # Get error data from automation service
            error_data = await self.automation_client.get_error_analysis()
            
            if not error_data:
                return self.create_success_response(
                    "query_error_analysis",
                    "📊 **No error data found**\n\nNo errors have been recorded recently. Your system is running smoothly! 🎉",
                    {"error_count": 0}
                )
            
            message_lower = message.lower()
            
            # Filter errors based on query
            if 'today' in message_lower:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                filtered_errors = [e for e in error_data if e.get('timestamp', '').startswith(today)]
                filter_desc = "today's errors"
            elif 'critical' in message_lower or 'severe' in message_lower:
                filtered_errors = [e for e in error_data if e.get('severity', '').lower() in ['critical', 'severe']]
                filter_desc = "critical errors"
            elif 'job' in message_lower:
                filtered_errors = [e for e in error_data if e.get('source', '').lower() == 'job']
                filter_desc = "job errors"
            elif 'workflow' in message_lower:
                filtered_errors = [e for e in error_data if e.get('source', '').lower() == 'workflow']
                filter_desc = "workflow errors"
            else:
                filtered_errors = error_data[:20]  # Recent 20
                filter_desc = "recent errors"
            
            response = f"📊 **Error Analysis - {filter_desc.title()}**\n\n"
            response += f"**Found:** {len(filtered_errors)} {filter_desc}\n\n"
            
            if not filtered_errors:
                response += f"No {filter_desc} found! ✅\n"
                response += f"Total errors in system: {len(error_data)}\n\n"
                response += "🎉 **Great news!** Your system is running without the specified errors."
            else:
                # Error categorization
                error_categories = {}
                severity_stats = {}
                source_stats = {}
                
                for error in filtered_errors:
                    category = error.get('category', 'unknown')
                    severity = error.get('severity', 'unknown')
                    source = error.get('source', 'unknown')
                    
                    error_categories[category] = error_categories.get(category, 0) + 1
                    severity_stats[severity] = severity_stats.get(severity, 0) + 1
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                # Show error breakdown
                response += "**Error Categories:**\n"
                for category, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / len(filtered_errors)) * 100
                    response += f"• {category.title()}: {count} ({percentage:.1f}%)\n"
                
                response += f"\n**Severity Distribution:**\n"
                for severity, count in sorted(severity_stats.items(), key=lambda x: x[1], reverse=True):
                    severity_emoji = '🔴' if severity == 'critical' else '🟡' if severity == 'warning' else '🔵'
                    response += f"• {severity.title()}: {count} {severity_emoji}\n"
                
                response += f"\n**Error Sources:**\n"
                for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
                    response += f"• {source.title()}: {count} errors\n"
                
                # Show recent errors
                response += f"\n**Recent {filter_desc.title()}:**\n"
                for i, error in enumerate(filtered_errors[:5]):
                    error_message = error.get('message', 'Unknown error')
                    timestamp = error.get('timestamp', 'Unknown')
                    severity = error.get('severity', 'unknown')
                    source = error.get('source', 'unknown')
                    
                    severity_emoji = '🔴' if severity == 'critical' else '🟡' if severity == 'warning' else '🔵'
                    
                    response += f"\n**{i+1}.** {severity_emoji} **{severity.title()}** - {source.title()}\n"
                    response += f"   • Time: {timestamp}\n"
                    response += f"   • Message: {error_message[:100]}{'...' if len(error_message) > 100 else ''}\n"
                
                if len(filtered_errors) > 5:
                    response += f"\n... and {len(filtered_errors) - 5} more {filter_desc}\n"
                
                # Recommendations
                response += f"\n**🔧 Recommendations:**\n"
                if severity_stats.get('critical', 0) > 0:
                    response += "• Address critical errors immediately\n"
                if error_categories.get('connection', 0) > 0:
                    response += "• Check network connectivity and target availability\n"
                if error_categories.get('authentication', 0) > 0:
                    response += "• Verify credentials and permissions\n"
                if error_categories.get('timeout', 0) > 0:
                    response += "• Consider increasing timeout values\n"
            
            return self.create_success_response(
                "query_error_analysis",
                response,
                {
                    "error_count": len(filtered_errors),
                    "total_errors": len(error_data),
                    "filter_description": filter_desc,
                    "critical_errors": len([e for e in filtered_errors if e.get('severity') == 'critical']),
                    "categories": list(error_categories.keys()) if 'error_categories' in locals() else []
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_error_analysis", e)
    
    async def handle_task_queue_query(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle task queue status queries"""
        try:
            # Get current task queue status
            queue_status = await self.automation_client.get_task_queue_status()
            
            if not queue_status:
                return self.create_success_response(
                    "query_task_queue",
                    "📋 **Task queue information unavailable**\n\nUnable to retrieve task queue status. The automation service may be unavailable.",
                    {"queue_available": False}
                )
            
            message_lower = message.lower()
            
            # Extract queue information
            pending_tasks = queue_status.get('pending_tasks', [])
            running_tasks = queue_status.get('running_tasks', [])
            completed_tasks = queue_status.get('completed_tasks', [])
            failed_tasks = queue_status.get('failed_tasks', [])
            worker_status = queue_status.get('workers', [])
            
            if 'pending' in message_lower:
                # Focus on pending tasks
                response = f"📋 **Pending Tasks**\n\n"
                response += f"**Queue Length:** {len(pending_tasks)} tasks\n\n"
                
                if pending_tasks:
                    response += "**Waiting for Execution:**\n"
                    for i, task in enumerate(pending_tasks[:8]):
                        task_name = task.get('name', 'Unknown Task')
                        job_name = task.get('job_name', 'Unknown Job')
                        priority = task.get('priority', 'normal')
                        queued_at = task.get('queued_at', 'Unknown')
                        estimated_duration = task.get('estimated_duration', 'Unknown')
                        
                        priority_emoji = '🔴' if priority == 'high' else '🟡' if priority == 'medium' else '🟢'
                        
                        response += f"{i+1}. **{task_name}** {priority_emoji}\n"
                        response += f"   • Job: {job_name}\n"
                        response += f"   • Priority: {priority}\n"
                        response += f"   • Queued: {queued_at}\n"
                        response += f"   • Est. Duration: {estimated_duration}\n\n"
                    
                    if len(pending_tasks) > 8:
                        response += f"... and {len(pending_tasks) - 8} more pending tasks\n\n"
                    
                    # Queue analysis
                    high_priority = len([t for t in pending_tasks if t.get('priority') == 'high'])
                    if high_priority > 0:
                        response += f"⚠️ **{high_priority} high-priority tasks** in queue\n"
                else:
                    response += "✅ **No pending tasks** - Queue is empty!"
                
            elif 'running' in message_lower or 'active' in message_lower:
                # Focus on running tasks
                response = f"🔄 **Running Tasks**\n\n"
                response += f"**Currently Executing:** {len(running_tasks)} tasks\n\n"
                
                if running_tasks:
                    response += "**Active Executions:**\n"
                    for i, task in enumerate(running_tasks):
                        task_name = task.get('name', 'Unknown Task')
                        job_name = task.get('job_name', 'Unknown Job')
                        started_at = task.get('started_at', 'Unknown')
                        worker_id = task.get('worker_id', 'Unknown')
                        progress = task.get('progress', 0)
                        estimated_completion = task.get('estimated_completion', 'Unknown')
                        
                        response += f"{i+1}. **{task_name}** 🔄\n"
                        response += f"   • Job: {job_name}\n"
                        response += f"   • Worker: {worker_id}\n"
                        response += f"   • Started: {started_at}\n"
                        response += f"   • Progress: {progress}%\n"
                        response += f"   • Est. Completion: {estimated_completion}\n\n"
                else:
                    response += "💤 **No running tasks** - All workers are idle"
                
            elif 'worker' in message_lower:
                # Focus on worker status
                response = f"👷 **Worker Status**\n\n"
                response += f"**Total Workers:** {len(worker_status)}\n\n"
                
                if worker_status:
                    active_workers = 0
                    idle_workers = 0
                    
                    response += "**Worker Details:**\n"
                    for i, worker in enumerate(worker_status):
                        worker_id = worker.get('id', f'Worker {i+1}')
                        status = worker.get('status', 'unknown')
                        current_task = worker.get('current_task', None)
                        tasks_completed = worker.get('tasks_completed', 0)
                        last_activity = worker.get('last_activity', 'Unknown')
                        worker_load = worker.get('load_percentage', 0)
                        
                        if status == 'active':
                            active_workers += 1
                            status_emoji = '🔄'
                        else:
                            idle_workers += 1
                            status_emoji = '💤'
                        
                        response += f"{i+1}. **{worker_id}** {status_emoji}\n"
                        response += f"   • Status: {status}\n"
                        response += f"   • Load: {worker_load}%\n"
                        response += f"   • Completed: {tasks_completed} tasks\n"
                        response += f"   • Last Activity: {last_activity}\n"
                        
                        if current_task:
                            response += f"   • Current Task: {current_task}\n"
                        
                        response += "\n"
                    
                    response += f"**Worker Summary:**\n"
                    response += f"• Active: {active_workers}\n"
                    response += f"• Idle: {idle_workers}\n"
                    
                    # Worker utilization
                    if len(worker_status) > 0:
                        utilization = (active_workers / len(worker_status)) * 100
                        response += f"• Utilization: {utilization:.1f}%\n"
                        
                        # Performance insights
                        avg_load = sum(w.get('load_percentage', 0) for w in worker_status) / len(worker_status)
                        response += f"• Average Load: {avg_load:.1f}%\n"
                        
                        if utilization > 80:
                            response += "\n⚠️ **High utilization** - Consider adding more workers\n"
                        elif utilization < 20:
                            response += "\n💡 **Low utilization** - Workers are underused\n"
                else:
                    response += "❌ **No workers available** - Check automation service configuration"
                
            else:
                # General queue overview
                response = f"📋 **Task Queue Overview**\n\n"
                
                # Queue statistics
                total_pending = len(pending_tasks)
                total_running = len(running_tasks)
                total_completed = len(completed_tasks)
                total_failed = len(failed_tasks)
                
                response += f"**Queue Status:**\n"
                response += f"• Pending: {total_pending} 📋\n"
                response += f"• Running: {total_running} 🔄\n"
                response += f"• Completed: {total_completed} ✅\n"
                response += f"• Failed: {total_failed} ❌\n\n"
                
                # Worker summary
                if worker_status:
                    active_workers = len([w for w in worker_status if w.get('status') == 'active'])
                    total_workers = len(worker_status)
                    
                    response += f"**Workers:**\n"
                    response += f"• Total: {total_workers}\n"
                    response += f"• Active: {active_workers}\n"
                    response += f"• Idle: {total_workers - active_workers}\n\n"
                
                # Queue health assessment
                if total_pending > 10:
                    response += "⚠️ **Queue Alert:** High number of pending tasks. Consider adding more workers.\n"
                elif total_pending == 0 and total_running == 0:
                    response += "✅ **Queue Status:** All clear - no pending or running tasks.\n"
                else:
                    response += "✅ **Queue Status:** Normal operation.\n"
                
                # Throughput analysis
                if total_completed > 0:
                    if total_failed > 0:
                        success_rate = (total_completed / (total_completed + total_failed)) * 100
                        response += f"\n**Success Rate:** {success_rate:.1f}%\n"
                    
                    response += f"**Throughput:** {total_completed} tasks completed\n"
                
                # Recent activity
                if running_tasks:
                    response += f"\n**Currently Running:**\n"
                    for i, task in enumerate(running_tasks[:3]):
                        task_name = task.get('name', 'Unknown Task')
                        progress = task.get('progress', 0)
                        response += f"• {task_name} ({progress}%)\n"
                    
                    if len(running_tasks) > 3:
                        response += f"... and {len(running_tasks) - 3} more\n"
            
            return self.create_success_response(
                "query_task_queue",
                response,
                {
                    "pending_count": len(pending_tasks),
                    "running_count": len(running_tasks),
                    "completed_count": len(completed_tasks),
                    "failed_count": len(failed_tasks),
                    "worker_count": len(worker_status),
                    "queue_health": "normal" if len(pending_tasks) <= 10 else "high_load"
                }
            )
            
        except Exception as e:
            return self.create_error_response("query_task_queue", e)
    
    async def handle_command_execution(self, message: str, context: List[Dict], intent: str) -> Dict[str, Any]:
        """Handle command execution requests"""
        try:
            logger.info(f"Processing command execution: {intent}")
            
            # Check if this is actually a request for help/script writing
            message_lower = message.lower()
            help_indicators = [
                "write", "create", "script", "show me", "give me", "need", "example", 
                "sample", "how to", "help", "code"
            ]
            
            if any(indicator in message_lower for indicator in help_indicators):
                # This is a help request, not a command execution request
                return await self._provide_script_help(message, intent)
            
            # Extract target information from message
            target_info = self._extract_target_info(message)
            command_info = self._extract_command_info(message, intent)
            
            if not target_info:
                # Instead of just erroring, provide helpful guidance
                return await self._provide_execution_guidance(message, intent, command_info)
            
            if not command_info:
                return self.create_error_response(
                    intent,
                    Exception("Command Required: Please specify what command to execute.\n\nExamples:\n• \"Get directory of C: drive\"\n• \"List files in /home\"\n• \"Check disk space\"")
                )
            
            # Try to execute the command
            try:
                # Create a job for execution
                job_data = {
                    "name": f"AI Command: {command_info['description']}",
                    "description": f"Automated command execution from AI: {message}",
                    "workflow_definition": {
                        "steps": [
                            {
                                "id": "execute_command",
                                "name": "Execute Command",
                                "type": "command_execution",
                                "target": target_info,
                                "command": command_info,
                                "timeout": 300
                            }
                        ]
                    },
                    "job_type": "ai_automation",
                    "tags": ["ai-generated", "command-execution"]
                }
                
                # Create and execute job via automation service
                if self.automation_client:
                    job_result = await self.automation_client.create_and_execute_job(job_data)
                    
                    if job_result.get("success"):
                        response = f"✅ **Command Execution Started**\n\n"
                        response += f"**Target**: {target_info.get('ip_address', target_info.get('hostname'))}\n"
                        response += f"**Command**: {command_info['description']}\n"
                        response += f"**Job ID**: {job_result.get('job_id')}\n"
                        response += f"**Execution ID**: {job_result.get('execution_id')}\n\n"
                        response += "🔄 The command is being executed. You can check the status in the Jobs section."
                        
                        return self.create_success_response(
                            intent,
                            response,
                            {
                                "target": target_info,
                                "command": command_info,
                                "job_id": job_result.get("job_id"),
                                "execution_id": job_result.get("execution_id")
                            }
                        )
                    else:
                        return self.create_error_response(
                            intent,
                            Exception(f"Execution Failed: {job_result.get('error', 'Unknown error occurred')}")
                        )
                else:
                    return self.create_error_response(
                        intent,
                        Exception("Service Unavailable: Automation service is not available for command execution.")
                    )
                    
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                return self.create_error_response(intent, e)
                
        except Exception as e:
            logger.error(f"Command execution handler error: {e}")
            return self.create_error_response(intent, e)
    
    def _extract_target_info(self, message: str) -> Dict[str, Any]:
        """Extract target information from message"""
        import re
        
        # Look for IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ip_matches = re.findall(ip_pattern, message)
        
        if ip_matches:
            return {
                "ip_address": ip_matches[0],
                "hostname": ip_matches[0],  # Use IP as hostname for now
                "connection_type": "auto"  # Will be determined by target OS
            }
        
        # Look for hostnames
        hostname_patterns = [
            r'\bon\s+([a-zA-Z0-9\-\.]+)',
            r'\bfor\s+([a-zA-Z0-9\-\.]+)',
            r'\btarget\s+([a-zA-Z0-9\-\.]+)',
            r'\bserver\s+([a-zA-Z0-9\-\.]+)'
        ]
        
        for pattern in hostname_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                hostname = matches[0]
                # Skip common words that aren't hostnames
                if hostname.lower() not in ['the', 'a', 'an', 'this', 'that']:
                    return {
                        "hostname": hostname,
                        "connection_type": "auto"
                    }
        
        return None
    
    async def _provide_script_help(self, message: str, intent: str) -> Dict[str, Any]:
        """Provide script examples and help instead of demanding execution parameters"""
        message_lower = message.lower()
        
        if "powershell" in message_lower and ("winrm" in message_lower or "connect" in message_lower):
            # PowerShell WinRM script request
            script_content = '''# PowerShell script to connect via WinRM and list C:\\ directory
param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName,
    
    [Parameter(Mandatory=$false)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [switch]$UseSSL
)

# Function to create credentials
function Get-RemoteCredentials {
    param($Username, $Password)
    
    if ($Username -and $Password) {
        $SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
        return New-Object System.Management.Automation.PSCredential($Username, $SecurePassword)
    } elseif ($Username) {
        return Get-Credential -UserName $Username -Message "Enter password for $Username"
    } else {
        return Get-Credential -Message "Enter credentials for remote connection"
    }
}

# Main script
try {
    Write-Host "Connecting to $ComputerName via WinRM..." -ForegroundColor Yellow
    
    # Get credentials
    $Credential = Get-RemoteCredentials -Username $Username -Password $Password
    
    # Set up session options
    $SessionOptions = New-PSSessionOption -SkipCACheck -SkipCNCheck
    
    # Create connection parameters
    $ConnectionParams = @{
        ComputerName = $ComputerName
        Credential = $Credential
        SessionOption = $SessionOptions
    }
    
    # Add SSL if specified
    if ($UseSSL) {
        $ConnectionParams.UseSSL = $true
        $ConnectionParams.Port = 5986
    } else {
        $ConnectionParams.Port = 5985
    }
    
    # Test WinRM connectivity first
    Write-Host "Testing WinRM connectivity..." -ForegroundColor Yellow
    if (-not (Test-WSMan -ComputerName $ComputerName -Port $ConnectionParams.Port -UseSSL:$UseSSL -ErrorAction SilentlyContinue)) {
        throw "WinRM is not accessible on $ComputerName. Please ensure WinRM is enabled and configured."
    }
    
    # Create PS Session
    $Session = New-PSSession @ConnectionParams -ErrorAction Stop
    
    Write-Host "Successfully connected to $ComputerName" -ForegroundColor Green
    Write-Host "Listing contents of C:\\ drive..." -ForegroundColor Yellow
    Write-Host "=" * 60
    
    # Execute directory listing on remote machine
    $Result = Invoke-Command -Session $Session -ScriptBlock {
        Get-ChildItem -Path "C:\\" | Select-Object Mode, LastWriteTime, Length, Name | Format-Table -AutoSize
    }
    
    # Display results
    $Result
    
} catch {
    Write-Error "Failed to connect or execute command: $($_.Exception.Message)"
    
    # Provide troubleshooting tips
    Write-Host "\\nTroubleshooting Tips:" -ForegroundColor Yellow
    Write-Host "1. Ensure WinRM is enabled on the target machine:"
    Write-Host "   winrm quickconfig"
    Write-Host "2. Check if the WinRM service is running:"
    Write-Host "   Get-Service WinRM"
    Write-Host "3. Verify firewall rules allow WinRM traffic (ports 5985/5986)"
    
} finally {
    # Clean up session
    if ($Session) {
        Remove-PSSession $Session
        Write-Host "\\nSession closed." -ForegroundColor Green
    }
}'''
            
            response = "📝 **PowerShell WinRM Script**\\n\\n"
            response += "Here's a complete PowerShell script to connect to a Windows machine via WinRM and list the C:\\ directory:\\n\\n"
            response += "```powershell\\n{script_content}\\n```\\n\\n"
            response += "**Usage Examples:**\\n"
            response += "```powershell\\n"
            response += "# Basic usage (will prompt for credentials):\\n"
            response += f".\WinRM-DirectoryList.ps1 -ComputerName \"192.168.1.100\"\n\n"
            response += "# With username (will prompt for password):\\n"
            response += f".\WinRM-DirectoryList.ps1 -ComputerName \"server01\" -Username \"domain\\administrator\"\n\n"
            response += "# Using SSL:\\n"
            response += f".\WinRM-DirectoryList.ps1 -ComputerName \"server01\" -Username \"admin\" -UseSSL\n"
            response += "```\\n\\n"
            response += "**Prerequisites on Target Machine:**\\n"
            response += "```powershell\\n"
            response += "# Enable WinRM\\n"
            response += "winrm quickconfig -y\\n\\n"
            response += "# Configure WinRM for remote access\\n"
            response += "winrm set winrm/config/service '@{AllowUnencrypted=\"true\"}'\n"
            response += "winrm set winrm/config/service/auth '@{Basic=\"true\"}'\n"
            response += f"```"
            
            return self.create_success_response(intent, response, {"script_type": "powershell_winrm"})
        
        elif "directory" in message_lower or "dir" in message_lower:
            # General directory listing help
            response = "📝 **Directory Listing Scripts**\\n\\n"
            response += "Here are scripts to list directory contents on different systems:\\n\\n"
            response += "**PowerShell (Windows):**\\n"
            response += "```powershell\\n"
            response += "# List C: drive contents\\n"
            response += "Get-ChildItem -Path C:\\ | Select-Object Name, Mode, Length, LastWriteTime | Format-Table -AutoSize\\n\\n"
            response += "# List with detailed info\\n"
            response += "Get-ChildItem -Path C:\\ -Force | Format-List Name, FullName, Length, CreationTime, LastWriteTime\\n"
            response += "```\\n\\n"
            response += "**Bash (Linux/macOS):**\\n"
            response += "```bash\\n"
            response += "# List directory contents\\n"
            response += "ls -la /\\n\\n"
            response += "# List with human-readable sizes\\n"
            response += "ls -lah /\\n\\n"
            response += "# List recursively\\n"
            response += "find / -maxdepth 1 -type f -ls\\n"
            response += "```\\n\\n"
            response += "**Command Prompt (Windows):**\\n"
            response += "```cmd\\n"
            response += "dir C:\\ /a\\n"
            response += f"```"
            
            return self.create_success_response(intent, response, {"script_type": "directory_listing"})
        
        else:
            # General script help
            response = "📝 **Script Help**\\n\\n"
            response += "I can help you create scripts for various tasks. Here are some examples:\\n\\n"
            response += "**Available Script Types:**\\n"
            response += "• PowerShell scripts for Windows automation\\n"
            response += "• Bash scripts for Linux/Unix systems\\n"
            response += "• Python scripts for cross-platform tasks\\n"
            response += "• Batch files for Windows command line\\n\\n"
            response += "**Common Tasks:**\\n"
            response += "• Remote connections (WinRM, SSH)\\n"
            response += "• File and directory operations\\n"
            response += "• System monitoring and health checks\\n"
            response += "• Network connectivity testing\\n"
            response += "• Service management\\n\\n"
            response += "**To get specific help, try asking:**\\n"
            response += '• "Write me a PowerShell script to connect via WinRM"\\n'
            response += '• "Create a bash script to check disk space"\\n'
            response += '• "Show me a Python script to ping multiple hosts"\\n'
            response += '• "Give me a script to list files in a directory"'
            
            return self.create_success_response(intent, response, {"script_type": "general_help"})
    
    async def _provide_execution_guidance(self, message: str, intent: str, command_info: Dict[str, Any]) -> Dict[str, Any]:
        """Provide helpful guidance when target is missing instead of just erroring"""
        response = "🎯 **Execution Guidance**\\n\\n"
        
        if command_info:
            response += "I understand you want to: **{command_info.get('description', 'execute a command')}**\\n\\n"
            response += "To execute this command, I need to know the target system. You can specify:\\n\\n"
            response += "**Target Options:**\\n"
            response += '• IP address: "Get directory of C: drive for 192.168.1.100"\\n'
            response += '• Hostname: "List files on server01"\\n'
            response += '• Server name: "Check disk space on web-server"\\n\\n'
            response += "**Or, if you want help creating a script instead:**\\n"
            response += '• "Write me a script to ' + command_info.get('description', 'do this task') + '"\\n'
            response += '• "Show me how to ' + command_info.get('description', 'accomplish this') + '"\\n\\n'
        else:
            response += "I can help you with command execution or script creation.\\n\\n"
            response += "**For immediate execution, specify a target:**\\n"
            response += '• \"Get directory of C: drive for 192.168.1.100\"\n'
            response += '• "List processes on server01"\\n\\n'
            response += "**For script help:**\\n"
            response += '• \"Write me a PowerShell script to list directories\"\n'
            response += '• "Create a bash script to check system status"\\n\\n'
        
        response += "**Available Command Types:**\\n"
        response += "• Directory listings (dir, ls)\\n"
        response += "• System information (processes, services)\\n"
        response += "• Network diagnostics (ping, connectivity)\\n"
        response += "• File operations (copy, move, delete)\\n"
        response += f"• Custom PowerShell/Bash commands"
        
        return self.create_success_response(intent, response, {"guidance_type": "execution_help"})
    
    def _extract_command_info(self, message: str, intent_action: str) -> Dict[str, Any]:
        """Extract command information from message"""
        message_lower = message.lower()
        
        # Directory/file listing commands
        if "directory" in message_lower or "dir" in message_lower or "folder" in message_lower:
            if "c:" in message_lower or "c drive" in message_lower:
                return {
                    "type": "powershell",
                    "command": "Get-ChildItem -Path C:\\ | Select-Object Name, Mode, Length, LastWriteTime",
                    "description": "List C: drive directory contents"
                }
            elif "d:" in message_lower or "d drive" in message_lower:
                return {
                    "type": "powershell", 
                    "command": "Get-ChildItem -Path D:\\ | Select-Object Name, Mode, Length, LastWriteTime",
                    "description": "List D: drive directory contents"
                }
            else:
                return {
                    "type": "auto",
                    "command": "ls -la" if "linux" in message_lower or "unix" in message_lower else "dir",
                    "description": "List directory contents"
                }
        
        # File listing
        if "list files" in message_lower or "show files" in message_lower:
            return {
                "type": "auto",
                "command": "ls -la" if "linux" in message_lower else "dir /a",
                "description": "List all files"
            }
        
        # System information
        if "system info" in message_lower or "system information" in message_lower:
            return {
                "type": "auto",
                "command": "systeminfo" if "windows" in message_lower else "uname -a && df -h",
                "description": "Get system information"
            }
        
        # Disk space
        if "disk space" in message_lower or "disk usage" in message_lower:
            return {
                "type": "auto",
                "command": "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace" if "windows" in message_lower else "df -h",
                "description": "Check disk space"
            }
        
        # Process list
        if "process" in message_lower and ("list" in message_lower or "show" in message_lower):
            return {
                "type": "auto",
                "command": "Get-Process" if "windows" in message_lower else "ps aux",
                "description": "List running processes"
            }
        
        # Service status
        if "service" in message_lower and ("status" in message_lower or "list" in message_lower):
            return {
                "type": "auto",
                "command": "Get-Service" if "windows" in message_lower else "systemctl list-units --type=service",
                "description": "List services"
            }
        
        # Generic command execution
        if "run" in message_lower or "execute" in message_lower:
            # Try to extract the actual command
            import re
            command_patterns = [
                r'run\s+"([^"]+)"',
                r'execute\s+"([^"]+)"',
                r'run\s+([^\s]+)',
                r'execute\s+([^\s]+)'
            ]
            
            for pattern in command_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    return {
                        "type": "auto",
                        "command": matches[0],
                        "description": f"Execute command: {matches[0]}"
                    }
        
        return None
    
    async def handle_job_creation(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle job creation requests"""
        # Implementation for job creation
        return self.create_error_response("create_job", Exception("Job creation not yet implemented"))
    
    async def handle_job_execution(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle job execution requests"""
        # Implementation for job execution
        return self.create_error_response("execute_job", Exception("Job execution not yet implemented"))
    
    async def handle_job_stop(self, message: str, context: List[Dict]) -> Dict[str, Any]:
        """Handle job stop requests"""
        # Implementation for job stopping
        return self.create_error_response("stop_job", Exception("Job stopping not yet implemented"))
    
    # Additional methods for job execution details, scheduling, and workflow step analysis
    # would be implemented here following the same pattern...