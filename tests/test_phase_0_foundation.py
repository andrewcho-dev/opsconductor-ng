"""
Phase 0 Foundation Tests
Tests for the basic foundation of NEWIDEA.MD pipeline
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestPhase0Foundation:
    """Test Phase 0 foundation components"""
    
    def test_directory_structure_exists(self):
        """Test that all required directories exist"""
        base_path = project_root
        
        required_dirs = [
            "pipeline",
            "pipeline/stages", 
            "pipeline/schemas",
            "pipeline/validation",
            "pipeline/safety",
            "llm",
            "capabilities", 
            "execution",
            "api",
            "tests"
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} does not exist"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
    
    def test_init_files_exist(self):
        """Test that all __init__.py files exist"""
        base_path = project_root
        
        required_init_files = [
            "pipeline/__init__.py",
            "pipeline/stages/__init__.py",
            "pipeline/schemas/__init__.py", 
            "pipeline/validation/__init__.py",
            "pipeline/safety/__init__.py",
            "llm/__init__.py",
            "capabilities/__init__.py",
            "execution/__init__.py",
            "api/__init__.py",
            "tests/__init__.py"
        ]
        
        for init_file in required_init_files:
            full_path = base_path / init_file
            assert full_path.exists(), f"Init file {init_file} does not exist"
            assert full_path.is_file(), f"{init_file} is not a file"
    
    def test_decision_v1_schema_exists(self):
        """Test that Decision v1 schema exists and is importable"""
        schema_file = project_root / "pipeline/schemas/decision_v1.py"
        assert schema_file.exists(), "Decision v1 schema file does not exist"
        
        # Test import
        try:
            from pipeline.schemas.decision_v1 import DecisionV1, DecisionType
            assert DecisionV1 is not None
            assert DecisionType is not None
        except ImportError as e:
            pytest.fail(f"Could not import Decision v1 schema: {e}")
    
    def test_main_entry_point_exists(self):
        """Test that main.py exists and is properly structured"""
        main_file = project_root / "main.py"
        assert main_file.exists(), "main.py does not exist"
        
        # Read and check basic structure
        content = main_file.read_text()
        assert "NEWIDEA.MD Pipeline" in content
        assert "4-Stage" in content
        assert "FastAPI" in content
        assert "/health" in content
        assert "/process" in content
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists"""
        dockerfile = project_root / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile does not exist"
        
        content = dockerfile.read_text()
        assert "python:3.11" in content
        assert "main.py" in content
    
    def test_requirements_exists(self):
        """Test that requirements.txt exists with required packages"""
        requirements_file = project_root / "requirements.txt"
        assert requirements_file.exists(), "requirements.txt does not exist"
        
        content = requirements_file.read_text()
        required_packages = ["fastapi", "uvicorn", "pydantic", "httpx", "pytest"]
        
        for package in required_packages:
            assert package in content, f"Required package {package} not in requirements.txt"
    
    def test_old_ai_brain_removed(self):
        """Test that old AI Brain directory has been removed"""
        ai_brain_path = project_root / "ai-brain"
        assert not ai_brain_path.exists(), "Old ai-brain directory still exists - should be removed"
    
    def test_docker_compose_updated(self):
        """Test that docker-compose.clean.yml has been updated for pipeline"""
        compose_file = project_root / "docker-compose.clean.yml"
        assert compose_file.exists(), "docker-compose.clean.yml does not exist"
        
        content = compose_file.read_text()
        assert "pipeline:" in content, "Pipeline service not found in docker-compose"
        assert "opsconductor-pipeline-newidea" in content, "Pipeline container name not found"
        assert "ai-brain:" not in content, "Old ai-brain service still in docker-compose"

def test_pipeline_constants():
    """Test pipeline constants and enums"""
    from pipeline import STAGE_A_CLASSIFIER, STAGE_B_SELECTOR, STAGE_C_PLANNER, STAGE_D_ANSWERER
    from pipeline import PIPELINE_STAGES, DECISION_ACTION, DECISION_INFO
    
    assert STAGE_A_CLASSIFIER == "classifier"
    assert STAGE_B_SELECTOR == "selector"
    assert STAGE_C_PLANNER == "planner"
    assert STAGE_D_ANSWERER == "answerer"
    
    assert len(PIPELINE_STAGES) == 4
    assert DECISION_ACTION == "action"
    assert DECISION_INFO == "info"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])