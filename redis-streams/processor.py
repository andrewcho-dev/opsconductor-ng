"""
Redis Streams Message Processor
Handles message processing, retries, and dead letter queue management
"""

import asyncio
import os
import signal
import sys
import time
from typing import Dict, List, Any, Optional
import structlog
import uvloop

# Add shared directory to path
sys.path.append('/app/shared')

from redis_streams import (
    RedisStreamsClient, 
    StreamMessage, 
    MessagePriority, 
    MessageStatus,
    create_streams_client
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class StreamsMessageProcessor:
    """Main message processor for Redis Streams"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_STREAMS_URL", "redis://redis-streams:6379/0")
        self.password = os.getenv("REDIS_PASSWORD", "opsconductor-streams-2024")
        self.workers = int(os.getenv("PROCESSOR_WORKERS", "4"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.dead_letter_ttl = int(os.getenv("DEAD_LETTER_TTL", "86400"))
        
        self.client: Optional[RedisStreamsClient] = None
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Message handlers by event type
        self.message_handlers = {
            "user_created": self._handle_user_event,
            "user_updated": self._handle_user_event,
            "user_deleted": self._handle_user_event,
            "asset_created": self._handle_asset_event,
            "asset_updated": self._handle_asset_event,
            "asset_deleted": self._handle_asset_event,
            "automation_started": self._handle_automation_event,
            "automation_completed": self._handle_automation_event,
            "automation_failed": self._handle_automation_event,
            "notification_sent": self._handle_communication_event,
            "email_sent": self._handle_communication_event,
            "ai_analysis_completed": self._handle_ai_event,
            "ai_prediction_generated": self._handle_ai_event,
            "network_scan_completed": self._handle_network_event,
            "vulnerability_detected": self._handle_network_event,
            "system_alert": self._handle_system_event,
            "health_check": self._handle_system_event
        }
        
        # Performance metrics
        self.metrics = {
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "messages_dead_lettered": 0,
            "processing_time_total": 0.0,
            "start_time": time.time()
        }
    
    async def start(self):
        """Start the message processor"""
        try:
            logger.info("Starting Redis Streams Message Processor",
                       workers=self.workers,
                       redis_url=self.redis_url)
            
            # Initialize Redis Streams client
            self.client = await create_streams_client(self.redis_url, self.password)
            
            # Start worker tasks
            self.running = True
            for i in range(self.workers):
                task = asyncio.create_task(self._worker(f"worker-{i}"))
                self.worker_tasks.append(task)
            
            # Start metrics reporter
            metrics_task = asyncio.create_task(self._metrics_reporter())
            self.worker_tasks.append(metrics_task)
            
            # Start cleanup task
            cleanup_task = asyncio.create_task(self._cleanup_task())
            self.worker_tasks.append(cleanup_task)
            
            logger.info("Message processor started successfully",
                       active_workers=len(self.worker_tasks))
            
            # Wait for all tasks
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error("Failed to start message processor", error=str(e))
            raise
    
    async def stop(self):
        """Stop the message processor"""
        logger.info("Stopping message processor...")
        
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Close Redis client
        if self.client:
            await self.client.close()
        
        logger.info("Message processor stopped")
    
    async def _worker(self, worker_name: str):
        """Worker task to process messages"""
        logger.info("Worker started", worker=worker_name)
        
        streams_to_consume = ["identity", "assets", "automation", "communication", "ai_brain", "network_analyzer", "system"]
        
        while self.running:
            try:
                # Consume messages from all streams
                messages = await self.client.consume_messages(
                    streams=streams_to_consume,
                    consumer_name=worker_name,
                    batch_size=5,
                    block_time=1000
                )
                
                # Process each message
                for message in messages:
                    await self._process_message(message, worker_name)
                
                # Small delay to prevent tight loop
                if not messages:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                logger.info("Worker cancelled", worker=worker_name)
                break
            except Exception as e:
                logger.error("Worker error", worker=worker_name, error=str(e))
                await asyncio.sleep(1)  # Back off on error
        
        logger.info("Worker stopped", worker=worker_name)
    
    async def _process_message(self, message: StreamMessage, worker_name: str):
        """Process a single message"""
        start_time = time.time()
        
        try:
            logger.info("Processing message",
                       worker=worker_name,
                       message_id=message.id,
                       event_type=message.event_type,
                       service=message.service,
                       priority=message.priority.value)
            
            # Get handler for event type
            handler = self.message_handlers.get(message.event_type, self._handle_unknown_event)
            
            # Process the message
            success = await handler(message)
            
            if success:
                # Acknowledge successful processing
                group_name = self.client.consumer_groups.get(message.stream, f"{message.stream}_processors")
                await self.client.acknowledge_message(message.stream, group_name, message.id)
                
                self.metrics["messages_processed"] += 1
                processing_time = time.time() - start_time
                self.metrics["processing_time_total"] += processing_time
                
                logger.info("Message processed successfully",
                           message_id=message.id,
                           event_type=message.event_type,
                           processing_time=f"{processing_time:.3f}s")
            else:
                # Handle failure
                await self._handle_message_failure(message)
                
        except Exception as e:
            logger.error("Error processing message",
                        message_id=message.id,
                        event_type=message.event_type,
                        error=str(e))
            await self._handle_message_failure(message)
    
    async def _handle_message_failure(self, message: StreamMessage):
        """Handle message processing failure"""
        try:
            self.metrics["messages_failed"] += 1
            
            # Attempt retry or send to dead letter queue
            retry_success = await self.client.retry_message(message)
            
            if retry_success:
                self.metrics["messages_retried"] += 1
                logger.info("Message queued for retry",
                           message_id=message.id,
                           retry_count=message.retry_count)
            else:
                self.metrics["messages_dead_lettered"] += 1
                logger.warning("Message sent to dead letter queue",
                              message_id=message.id,
                              max_retries=message.max_retries)
            
        except Exception as e:
            logger.error("Failed to handle message failure",
                        message_id=message.id,
                        error=str(e))
    
    # Message Handlers
    async def _handle_user_event(self, message: StreamMessage) -> bool:
        """Handle identity service events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing user event",
                       event_type=event_type,
                       user_id=data.get("user_id"),
                       correlation_id=message.correlation_id)
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            # Example: Update user cache, send notifications, etc.
            if event_type == "user_created":
                await self._notify_services_of_new_user(data)
            elif event_type == "user_updated":
                await self._update_user_cache(data)
            elif event_type == "user_deleted":
                await self._cleanup_user_data(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process user event", error=str(e))
            return False
    
    async def _handle_asset_event(self, message: StreamMessage) -> bool:
        """Handle asset service events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing asset event",
                       event_type=event_type,
                       asset_id=data.get("asset_id"),
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.05)
            
            # Example: Update asset indexes, trigger scans, etc.
            if event_type == "asset_created":
                await self._index_new_asset(data)
            elif event_type == "asset_updated":
                await self._update_asset_index(data)
            elif event_type == "asset_deleted":
                await self._remove_asset_from_index(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process asset event", error=str(e))
            return False
    
    async def _handle_automation_event(self, message: StreamMessage) -> bool:
        """Handle automation service events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing automation event",
                       event_type=event_type,
                       job_id=data.get("job_id"),
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.1)
            
            # Example: Update job status, send notifications, etc.
            if event_type == "automation_started":
                await self._notify_automation_start(data)
            elif event_type == "automation_completed":
                await self._process_automation_results(data)
            elif event_type == "automation_failed":
                await self._handle_automation_failure(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process automation event", error=str(e))
            return False
    
    async def _handle_communication_event(self, message: StreamMessage) -> bool:
        """Handle communication service events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing communication event",
                       event_type=event_type,
                       recipient=data.get("recipient"),
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.05)
            
            # Example: Log delivery status, update metrics, etc.
            if event_type == "notification_sent":
                await self._log_notification_delivery(data)
            elif event_type == "email_sent":
                await self._log_email_delivery(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process communication event", error=str(e))
            return False
    
    async def _handle_ai_event(self, message: StreamMessage) -> bool:
        """Handle AI brain events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing AI event",
                       event_type=event_type,
                       analysis_id=data.get("analysis_id"),
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.2)  # AI events might take longer
            
            # Example: Store results, trigger actions, etc.
            if event_type == "ai_analysis_completed":
                await self._store_ai_analysis(data)
            elif event_type == "ai_prediction_generated":
                await self._process_ai_prediction(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process AI event", error=str(e))
            return False
    
    async def _handle_network_event(self, message: StreamMessage) -> bool:
        """Handle network analyzer events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing network event",
                       event_type=event_type,
                       scan_id=data.get("scan_id"),
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.1)
            
            # Example: Update security status, trigger alerts, etc.
            if event_type == "network_scan_completed":
                await self._process_scan_results(data)
            elif event_type == "vulnerability_detected":
                await self._handle_vulnerability_alert(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process network event", error=str(e))
            return False
    
    async def _handle_system_event(self, message: StreamMessage) -> bool:
        """Handle system events"""
        try:
            event_type = message.event_type
            data = message.data
            
            logger.info("Processing system event",
                       event_type=event_type,
                       correlation_id=message.correlation_id)
            
            await asyncio.sleep(0.05)
            
            # Example: Update system status, log metrics, etc.
            if event_type == "system_alert":
                await self._process_system_alert(data)
            elif event_type == "health_check":
                await self._update_health_status(data)
            
            return True
            
        except Exception as e:
            logger.error("Failed to process system event", error=str(e))
            return False
    
    async def _handle_unknown_event(self, message: StreamMessage) -> bool:
        """Handle unknown event types"""
        logger.warning("Unknown event type",
                      event_type=message.event_type,
                      service=message.service,
                      message_id=message.id)
        
        # Still acknowledge to prevent reprocessing
        return True
    
    # Helper methods (simplified implementations)
    async def _notify_services_of_new_user(self, data: Dict[str, Any]):
        logger.debug("Notifying services of new user", user_id=data.get("user_id"))
    
    async def _update_user_cache(self, data: Dict[str, Any]):
        logger.debug("Updating user cache", user_id=data.get("user_id"))
    
    async def _cleanup_user_data(self, data: Dict[str, Any]):
        logger.debug("Cleaning up user data", user_id=data.get("user_id"))
    
    async def _index_new_asset(self, data: Dict[str, Any]):
        logger.debug("Indexing new asset", asset_id=data.get("asset_id"))
    
    async def _update_asset_index(self, data: Dict[str, Any]):
        logger.debug("Updating asset index", asset_id=data.get("asset_id"))
    
    async def _remove_asset_from_index(self, data: Dict[str, Any]):
        logger.debug("Removing asset from index", asset_id=data.get("asset_id"))
    
    async def _notify_automation_start(self, data: Dict[str, Any]):
        logger.debug("Notifying automation start", job_id=data.get("job_id"))
    
    async def _process_automation_results(self, data: Dict[str, Any]):
        logger.debug("Processing automation results", job_id=data.get("job_id"))
    
    async def _handle_automation_failure(self, data: Dict[str, Any]):
        logger.debug("Handling automation failure", job_id=data.get("job_id"))
    
    async def _log_notification_delivery(self, data: Dict[str, Any]):
        logger.debug("Logging notification delivery", recipient=data.get("recipient"))
    
    async def _log_email_delivery(self, data: Dict[str, Any]):
        logger.debug("Logging email delivery", recipient=data.get("recipient"))
    
    async def _store_ai_analysis(self, data: Dict[str, Any]):
        logger.debug("Storing AI analysis", analysis_id=data.get("analysis_id"))
    
    async def _process_ai_prediction(self, data: Dict[str, Any]):
        logger.debug("Processing AI prediction", prediction_id=data.get("prediction_id"))
    
    async def _process_scan_results(self, data: Dict[str, Any]):
        logger.debug("Processing scan results", scan_id=data.get("scan_id"))
    
    async def _handle_vulnerability_alert(self, data: Dict[str, Any]):
        logger.debug("Handling vulnerability alert", vulnerability_id=data.get("vulnerability_id"))
    
    async def _process_system_alert(self, data: Dict[str, Any]):
        logger.debug("Processing system alert", alert_type=data.get("alert_type"))
    
    async def _update_health_status(self, data: Dict[str, Any]):
        logger.debug("Updating health status", service=data.get("service"))
    
    async def _metrics_reporter(self):
        """Report metrics periodically"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                uptime = time.time() - self.metrics["start_time"]
                avg_processing_time = (
                    self.metrics["processing_time_total"] / max(self.metrics["messages_processed"], 1)
                )
                
                logger.info("Processor metrics",
                           uptime_seconds=int(uptime),
                           messages_processed=self.metrics["messages_processed"],
                           messages_failed=self.metrics["messages_failed"],
                           messages_retried=self.metrics["messages_retried"],
                           messages_dead_lettered=self.metrics["messages_dead_lettered"],
                           avg_processing_time=f"{avg_processing_time:.3f}s",
                           messages_per_minute=int(self.metrics["messages_processed"] / (uptime / 60)))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error reporting metrics", error=str(e))
    
    async def _cleanup_task(self):
        """Periodic cleanup of old messages"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                logger.info("Starting periodic cleanup")
                await self.client.cleanup_old_messages(max_age_hours=24)
                logger.info("Periodic cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error during cleanup", error=str(e))

async def main():
    """Main entry point"""
    # Set up uvloop for better performance
    uvloop.install()
    
    processor = StreamsMessageProcessor()
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(processor.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Processor failed", error=str(e))
        sys.exit(1)
    finally:
        await processor.stop()

if __name__ == "__main__":
    asyncio.run(main())