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
            "query_task_queue"
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
    
    # Additional methods for job execution details, scheduling, and workflow step analysis
    # would be implemented here following the same pattern...