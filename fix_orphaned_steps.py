#!/usr/bin/env python3
"""
Fix Orphaned Steps Script
Fixes steps that are stuck in 'queued' status when their job runs are in final status
"""

import sys
import os
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append('/home/opsconductor')

from shared.database import get_db_cursor
from shared.logging import setup_service_logging, get_logger

# Setup logging
setup_service_logging("fix-orphaned-steps", level="INFO")
logger = get_logger("fix-orphaned-steps")

def fix_orphaned_steps():
    """Fix steps that are stuck in queued status when job is in final status"""
    
    try:
        with get_db_cursor() as cursor:
            # Find orphaned steps - steps in 'queued' status where job run is in final status
            cursor.execute("""
                SELECT jrs.id, jrs.job_run_id, jrs.idx, jr.status as job_status
                FROM job_run_steps jrs
                JOIN job_runs jr ON jrs.job_run_id = jr.id
                WHERE jrs.status = 'queued' 
                AND jr.status IN ('succeeded', 'failed', 'cancelled')
                ORDER BY jrs.job_run_id, jrs.idx
            """)
            
            orphaned_steps = cursor.fetchall()
            
            if not orphaned_steps:
                logger.info("No orphaned steps found")
                return
            
            logger.info(f"Found {len(orphaned_steps)} orphaned steps to fix")
            
            # Fix each orphaned step
            for step in orphaned_steps:
                step_id = step['id']
                job_run_id = step['job_run_id']
                step_idx = step['idx']
                job_status = step['job_status']
                
                logger.info(f"Fixing orphaned step {step_id} (job_run_id: {job_run_id}, idx: {step_idx}, job_status: {job_status})")
                
                # Mark the step as failed with appropriate error message
                cursor.execute("""
                    UPDATE job_run_steps 
                    SET status = 'failed',
                        stderr = 'Step was orphaned - job completed but step remained in queued status. Fixed by cleanup script.',
                        finished_at = %s
                    WHERE id = %s
                """, (datetime.now(timezone.utc), step_id))
                
                logger.info(f"Fixed step {step_id}")
            
            logger.info(f"Successfully fixed {len(orphaned_steps)} orphaned steps")
            
            # Also check for steps with invalid target_ids
            cursor.execute("""
                SELECT jrs.id, jrs.job_run_id, jrs.idx, jrs.target_id
                FROM job_run_steps jrs
                LEFT JOIN targets t ON jrs.target_id = t.id AND t.deleted_at IS NULL
                WHERE jrs.target_id IS NOT NULL 
                AND t.id IS NULL
                AND jrs.status = 'queued'
                ORDER BY jrs.job_run_id, jrs.idx
            """)
            
            invalid_target_steps = cursor.fetchall()
            
            if invalid_target_steps:
                logger.info(f"Found {len(invalid_target_steps)} steps with invalid target_ids")
                
                for step in invalid_target_steps:
                    step_id = step['id']
                    job_run_id = step['job_run_id']
                    step_idx = step['idx']
                    target_id = step['target_id']
                    
                    logger.info(f"Fixing step {step_id} with invalid target_id {target_id}")
                    
                    cursor.execute("""
                        UPDATE job_run_steps 
                        SET status = 'failed',
                            stderr = %s,
                            finished_at = %s
                        WHERE id = %s
                    """, (
                        f'Target ID {target_id} not found or was deleted. Fixed by cleanup script.',
                        datetime.now(timezone.utc), 
                        step_id
                    ))
                    
                    logger.info(f"Fixed step {step_id} with invalid target_id {target_id}")
                
                logger.info(f"Successfully fixed {len(invalid_target_steps)} steps with invalid target_ids")
            else:
                logger.info("No steps with invalid target_ids found")
                
    except Exception as e:
        logger.error(f"Error fixing orphaned steps: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting orphaned steps cleanup")
    fix_orphaned_steps()
    logger.info("Orphaned steps cleanup completed")