#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    
    print("🧪 Testing Modern AI Brain imports...")
    
    try:
        # Test orchestration imports
        print("  📦 Testing orchestration imports...")
        from orchestration.prefect_flow_engine import PrefectFlowEngine, FlowDefinition, FlowType, TaskType
        from orchestration.ai_brain_service import AIBrainService, IntentType, ChatResponse
        print("  ✅ Orchestration imports successful")
        
        # Test basic functionality
        print("  🔧 Testing basic functionality...")
        
        # Test PrefectFlowEngine initialization
        engine = PrefectFlowEngine()
        print(f"  ✅ PrefectFlowEngine created: {type(engine).__name__}")
        
        # Test AIBrainService initialization
        service = AIBrainService()
        print(f"  ✅ AIBrainService created: {type(service).__name__}")
        
        # Test enum values
        print(f"  ✅ FlowType enum: {[ft.value for ft in FlowType]}")
        print(f"  ✅ TaskType enum: {[tt.value for tt in TaskType]}")
        print(f"  ✅ IntentType enum: {[it.value for it in IntentType]}")
        
        print("\n🎉 All imports and basic functionality tests passed!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)