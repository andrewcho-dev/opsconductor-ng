#!/usr/bin/env python3
"""
Small test of the fixed training system
"""

import sys
import os
import logging
import asyncio
import requests
import time
from datetime import datetime
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealTrainingScenario:
    def __init__(self, id, name, description, difficulty, category, job_type, target_assets, workflow_steps, expected_outcomes, learning_objectives, estimated_duration):
        self.id = id
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.category = category
        self.job_type = job_type
        self.target_assets = target_assets
        self.workflow_steps = workflow_steps
        self.expected_outcomes = expected_outcomes
        self.learning_objectives = learning_objectives
        self.estimated_duration = estimated_duration

class EnhancedNetworkTrainingSystem:
    def __init__(self):
        self.automation_service_url = "http://localhost:3003"
        
    def create_training_job(self, scenario: RealTrainingScenario) -> Optional[int]:
        """Create a real job in the automation service"""
        try:
            job_data = {
                "name": scenario.name,
                "description": scenario.description,
                "job_type": scenario.job_type,
                "workflow_definition": {
                    "steps": scenario.workflow_steps,
                    "target_assets": scenario.target_assets
                },
                "metadata": {
                    "training_scenario_id": scenario.id,
                    "difficulty": scenario.difficulty,
                    "category": scenario.category,
                    "expected_outcomes": scenario.expected_outcomes,
                    "learning_objectives": scenario.learning_objectives,
                    "estimated_duration": scenario.estimated_duration
                },
                "tags": ["training", "network_analysis", scenario.difficulty, scenario.category]
            }
            
            # Try to create job via API
            response = requests.post(
                f"{self.automation_service_url}/jobs",
                json=job_data,
                timeout=10
            )
            
            if response.status_code == 200:
                job_info = response.json()
                job_id = job_info.get("data", {}).get("id")
                logger.info(f"✅ Created real job: {job_id} for scenario {scenario.id}")
                return job_id
            else:
                logger.warning(f"⚠️  Failed to create job via API: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Could not create real job for {scenario.id}: {e}")
            return None
    
    async def execute_training_job(self, job_id: int, scenario: RealTrainingScenario) -> Optional[str]:
        """Execute the training job and create a run"""
        try:
            # Try to start job execution via API
            response = requests.post(
                f"{self.automation_service_url}/jobs/{job_id}/run",
                json={"triggered_by": "ai_training_system"},
                timeout=10
            )
            
            if response.status_code == 200:
                run_info = response.json()
                run_id = run_info.get("data", {}).get("execution_id")
                logger.info(f"🏃 Started real job execution: {run_id}")
                return run_id
            else:
                logger.warning(f"⚠️  Failed to execute job: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Could not execute job {job_id}: {e}")
            return None

async def test_small_training():
    """Test with just one scenario"""
    
    # Create a simple test scenario
    scenario = RealTrainingScenario(
        id="TEST-001",
        name="Basic Network Connectivity Test",
        description="Test basic network connectivity and response times",
        difficulty="basic",
        category="connectivity",
        job_type="network-analysis",
        target_assets=["network-analyzer-service"],
        workflow_steps=[
            {
                "type": "ping_test",
                "action": "ping_hosts",
                "parameters": {"targets": ["8.8.8.8", "1.1.1.1"], "count": 4}
            }
        ],
        expected_outcomes=["Connectivity verified", "Response times measured"],
        learning_objectives=["Learn basic connectivity testing"],
        estimated_duration=5
    )
    
    trainer = EnhancedNetworkTrainingSystem()
    
    logger.info("🧪 Testing job creation and execution...")
    
    # Create job
    job_id = trainer.create_training_job(scenario)
    if job_id:
        logger.info(f"✅ Job created with ID: {job_id}")
        
        # Execute job
        run_id = await trainer.execute_training_job(job_id, scenario)
        if run_id:
            logger.info(f"✅ Job execution started with run ID: {run_id}")
            return True
        else:
            logger.error("❌ Job execution failed")
            return False
    else:
        logger.error("❌ Job creation failed")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Small Training System Test")
    logger.info("=" * 50)
    
    success = await test_small_training()
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ Small test passed! Training system is working.")
    else:
        logger.error("❌ Small test failed.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)