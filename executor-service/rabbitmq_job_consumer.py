"""
RabbitMQ Job Consumer for Executor Service

This module handles consuming job execution messages from RabbitMQ queues
and integrating with the existing JobExecutor class.
"""

import asyncio
import logging
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Add shared directory to path
sys.path.append('/home/opsconductor')

from shared.utility_event_consumer import get_event_consumer, message_handler
from shared.utility_event_publisher import publish_audit
from shared.message_schemas import JobScheduleMessage, QueueNames
from shared.database import get_db_cursor

logger = logging.getLogger(__name__)


class RabbitMQJobConsumer:
    """Handles RabbitMQ job consumption for the executor service"""
    
    def __init__(self, job_executor):
        """
        Initialize RabbitMQ job consumer
        
        Args:
            job_executor: Instance of JobExecutor class from main.py
        """
        self.job_executor = job_executor
        self.consumer = None
        self.running = False
    
    async def start_consuming(self):
        """Start consuming job messages from RabbitMQ"""
        try:
            logger.info("Starting RabbitMQ job consumer...")
            
            # Get event consumer and register our handler
            self.consumer = await get_event_consumer()
            self.consumer.register_handler("job_schedule", self.handle_job_message)
            
            # Start consuming from job scheduler queue
            await self.consumer.start_consuming(QueueNames.JOB_SCHEDULER, prefetch_count=3)
            
            self.running = True
            logger.info("RabbitMQ job consumer started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start RabbitMQ job consumer: {e}")
            raise
    
    async def stop_consuming(self):
        """Stop consuming job messages"""
        try:
            if self.consumer and self.running:
                await self.consumer.stop_consuming(QueueNames.JOB_SCHEDULER)
                self.running = False
                logger.info("RabbitMQ job consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping RabbitMQ job consumer: {e}")
    
    async def handle_job_message(self, message: JobScheduleMessage, context: Dict[str, Any]) -> bool:
        """
        Handle incoming job schedule message from RabbitMQ
        
        Args:
            message: JobScheduleMessage from RabbitMQ
            context: Message context (queue, headers, etc.)
            
        Returns:
            bool: True if message processed successfully, False otherwise
        """
        try:
            logger.info(f"Processing job message {message.message_id}: {message.job_type}")
            
            # Log audit event for job processing start
            await publish_audit(
                event_type="job_processing_started",
                resource_type="job",
                resource_id=message.job_id,
                action="process_job",
                source_service="executor-service",
                user_id=message.user_id,
                details={
                    "job_type": message.job_type,
                    "target_id": message.target_id,
                    "priority": message.priority,
                    "message_id": message.message_id
                },
                correlation_id=message.correlation_id
            )
            
            # Process the job based on job type
            success = await self._process_job_by_type(message)
            
            if success:
                # Log successful processing
                await publish_audit(
                    event_type="job_processing_completed",
                    resource_type="job",
                    resource_id=message.job_id,
                    action="complete_job",
                    source_service="executor-service",
                    user_id=message.user_id,
                    details={
                        "job_type": message.job_type,
                        "status": "success",
                        "message_id": message.message_id
                    },
                    correlation_id=message.correlation_id
                )
                
                logger.info(f"Successfully processed job {message.job_id}")
                return True
            else:
                # Log failed processing
                await publish_audit(
                    event_type="job_processing_failed",
                    resource_type="job",
                    resource_id=message.job_id,
                    action="fail_job",
                    source_service="executor-service",
                    user_id=message.user_id,
                    details={
                        "job_type": message.job_type,
                        "status": "failed",
                        "message_id": message.message_id
                    },
                    correlation_id=message.correlation_id
                )
                
                logger.error(f"Failed to process job {message.job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling job message {message.message_id}: {e}")
            
            # Log error audit event
            try:
                await publish_audit(
                    event_type="job_processing_error",
                    resource_type="job",
                    resource_id=message.job_id,
                    action="error_job",
                    source_service="executor-service",
                    user_id=message.user_id,
                    details={
                        "job_type": message.job_type,
                        "error": str(e),
                        "message_id": message.message_id
                    },
                    correlation_id=message.correlation_id
                )
            except Exception as audit_error:
                logger.error(f"Failed to log audit event: {audit_error}")
            
            return False
    
    async def _process_job_by_type(self, message: JobScheduleMessage) -> bool:
        """
        Process job based on its type
        
        Args:
            message: JobScheduleMessage to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            job_type = message.job_type
            
            if job_type == "execute_job_run":
                # This is a job run execution request
                return await self._execute_job_run(message)
            elif job_type == "execute_step":
                # This is a single step execution request
                return await self._execute_single_step(message)
            elif job_type == "scheduled_job":
                # This is a scheduled job execution
                return await self._execute_scheduled_job(message)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing job type {message.job_type}: {e}")
            return False
    
    async def _execute_job_run(self, message: JobScheduleMessage) -> bool:
        """
        Execute a complete job run
        
        Args:
            message: JobScheduleMessage containing job run details
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            job_run_id = message.parameters.get("job_run_id")
            if not job_run_id:
                logger.error("No job_run_id in message parameters")
                return False
            
            # Get job run details from database
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT jr.*, j.definition as job_definition
                    FROM job_runs jr
                    JOIN jobs j ON jr.job_id = j.id
                    WHERE jr.id = %s
                """, (job_run_id,))
                
                job_run = cursor.fetchone()
                if not job_run:
                    logger.error(f"Job run {job_run_id} not found")
                    return False
                
                # Mark job run as running
                cursor.execute("""
                    UPDATE job_runs 
                    SET status = 'running', started_at = %s 
                    WHERE id = %s
                """, (datetime.utcnow(), job_run_id))
                
                # Get all steps for this job run
                cursor.execute("""
                    SELECT * FROM job_run_steps 
                    WHERE job_run_id = %s 
                    ORDER BY step_order
                """, (job_run_id,))
                
                steps = cursor.fetchall()
                
                # Execute each step in order
                all_successful = True
                for step in steps:
                    try:
                        # Execute step using existing JobExecutor logic
                        self.job_executor._execute_step(step, cursor)
                        
                        # Check if step succeeded
                        cursor.execute(
                            "SELECT status FROM job_run_steps WHERE id = %s",
                            (step['id'],)
                        )
                        step_status = cursor.fetchone()['status']
                        
                        if step_status == 'failed':
                            all_successful = False
                            break
                            
                    except Exception as e:
                        logger.error(f"Error executing step {step['id']}: {e}")
                        all_successful = False
                        break
                
                # Update final job run status
                final_status = 'completed' if all_successful else 'failed'
                cursor.execute("""
                    UPDATE job_runs 
                    SET status = %s, finished_at = %s 
                    WHERE id = %s
                """, (final_status, datetime.utcnow(), job_run_id))
                
                logger.info(f"Job run {job_run_id} completed with status: {final_status}")
                return all_successful
                
        except Exception as e:
            logger.error(f"Error executing job run: {e}")
            return False
    
    async def _execute_single_step(self, message: JobScheduleMessage) -> bool:
        """
        Execute a single job step
        
        Args:
            message: JobScheduleMessage containing step details
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            step_id = message.parameters.get("step_id")
            if not step_id:
                logger.error("No step_id in message parameters")
                return False
            
            # Get step details from database
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT jrs.*, jr.parameters as run_parameters, j.definition as job_definition
                    FROM job_run_steps jrs
                    JOIN job_runs jr ON jrs.job_run_id = jr.id
                    JOIN jobs j ON jr.job_id = j.id
                    WHERE jrs.id = %s
                """, (step_id,))
                
                step = cursor.fetchone()
                if not step:
                    logger.error(f"Step {step_id} not found")
                    return False
                
                # Execute the step using existing JobExecutor logic
                self.job_executor._execute_step(step, cursor)
                
                # Check execution result
                cursor.execute(
                    "SELECT status FROM job_run_steps WHERE id = %s",
                    (step_id,)
                )
                step_status = cursor.fetchone()['status']
                
                success = step_status in ['completed', 'succeeded']
                logger.info(f"Step {step_id} executed with status: {step_status}")
                return success
                
        except Exception as e:
            logger.error(f"Error executing single step: {e}")
            return False
    
    async def _execute_scheduled_job(self, message: JobScheduleMessage) -> bool:
        """
        Execute a scheduled job (create job run and execute)
        
        Args:
            message: JobScheduleMessage containing scheduled job details
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            job_id = message.parameters.get("job_id")
            if not job_id:
                logger.error("No job_id in message parameters")
                return False
            
            # Create a new job run for this scheduled execution
            with get_db_cursor() as cursor:
                # Create job run
                cursor.execute("""
                    INSERT INTO job_runs (job_id, user_id, status, parameters, created_at)
                    VALUES (%s, %s, 'queued', %s, %s)
                    RETURNING id
                """, (
                    job_id,
                    message.user_id,
                    json.dumps(message.parameters),
                    datetime.utcnow()
                ))
                
                job_run_id = cursor.fetchone()['id']
                
                # Create a new message for job run execution
                job_run_message = JobScheduleMessage(
                    message_id=f"{message.message_id}_run",
                    source_service="executor-service",
                    correlation_id=message.correlation_id,
                    job_id=message.job_id,
                    job_type="execute_job_run",
                    user_id=message.user_id,
                    target_id=message.target_id,
                    parameters={"job_run_id": job_run_id},
                    scheduled_time=message.scheduled_time,
                    priority=message.priority
                )
                
                # Execute the job run
                return await self._execute_job_run(job_run_message)
                
        except Exception as e:
            logger.error(f"Error executing scheduled job: {e}")
            return False


# Global consumer instance
_rabbitmq_job_consumer: Optional[RabbitMQJobConsumer] = None


async def get_rabbitmq_job_consumer(job_executor) -> RabbitMQJobConsumer:
    """Get global RabbitMQ job consumer instance"""
    global _rabbitmq_job_consumer
    
    if _rabbitmq_job_consumer is None:
        _rabbitmq_job_consumer = RabbitMQJobConsumer(job_executor)
    
    return _rabbitmq_job_consumer


async def start_rabbitmq_job_consumer(job_executor):
    """Start the RabbitMQ job consumer"""
    consumer = await get_rabbitmq_job_consumer(job_executor)
    await consumer.start_consuming()
    return consumer


async def stop_rabbitmq_job_consumer():
    """Stop the RabbitMQ job consumer"""
    global _rabbitmq_job_consumer
    
    if _rabbitmq_job_consumer:
        await _rabbitmq_job_consumer.stop_consuming()
        _rabbitmq_job_consumer = None