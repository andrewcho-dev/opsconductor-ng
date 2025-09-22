#!/usr/bin/env python3
"""
Test script to verify the training system fixes
"""

import sys
import os
import logging
import requests
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_job_creation():
    """Test basic job creation"""
    automation_service_url = "http://localhost:3003"
    
    job_data = {
        "name": "Test Network Analysis Training",
        "description": "Testing the fixed API endpoints",
        "job_type": "network-analysis",
        "workflow_definition": {
            "steps": [
                {
                    "type": "network_scan",
                    "action": "scan_network",
                    "parameters": {"target": "192.168.1.0/24"}
                }
            ]
        },
        "metadata": {
            "training_scenario": "test",
            "ai_generated": True
        }
    }
    
    try:
        logger.info("🧪 Testing job creation...")
        response = requests.post(
            f"{automation_service_url}/jobs",
            json=job_data,
            timeout=10
        )
        
        if response.status_code == 200:
            job_info = response.json()
            job_id = job_info['data']['id']
            logger.info(f"✅ Job created successfully with ID: {job_id}")
            
            # Test job execution
            logger.info("🧪 Testing job execution...")
            exec_response = requests.post(
                f"{automation_service_url}/jobs/{job_id}/run",
                json={"triggered_by": "test_system"},
                timeout=10
            )
            
            if exec_response.status_code == 200:
                run_info = exec_response.json()
                logger.info(f"✅ Job execution started successfully: {run_info}")
                return True
            else:
                logger.error(f"❌ Job execution failed: {exec_response.status_code} - {exec_response.text}")
                return False
        else:
            logger.error(f"❌ Job creation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Starting Training System Fix Test")
    logger.info("=" * 60)
    
    success = test_job_creation()
    
    logger.info("=" * 60)
    if success:
        logger.info("✅ All tests passed! Training system is ready.")
    else:
        logger.error("❌ Tests failed. Check the logs above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)