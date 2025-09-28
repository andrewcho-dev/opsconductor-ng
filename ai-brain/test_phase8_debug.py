#!/usr/bin/env python3
"""
🧪 PHASE 8: DEBUG TEST
Debug test to identify specific import issues.
"""

import sys
import traceback

def test_imports():
    """Test imports one by one to identify issues"""
    
    print("🔍 Testing imports one by one...")
    
    # Test 1: Basic imports
    try:
        import asyncio
        import structlog
        from datetime import datetime
        from typing import Dict, List, Optional, Any, Union
        from dataclasses import dataclass, field
        from enum import Enum
        import json
        import uuid
        print("✅ Basic imports: OK")
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False
    
    # Test 2: Core system imports
    try:
        from integrations.thinking_llm_client import ThinkingLLMClient
        print("✅ ThinkingLLMClient import: OK")
    except Exception as e:
        print(f"❌ ThinkingLLMClient import failed: {e}")
        traceback.print_exc()
    
    try:
        from integrations.llm_client import LLMEngine
        print("✅ LLMEngine import: OK")
    except Exception as e:
        print(f"❌ LLMEngine import failed: {e}")
        traceback.print_exc()
    
    # Test 3: Phase imports
    try:
        from streaming.stream_manager import CentralStreamManager
        print("✅ CentralStreamManager import: OK")
    except Exception as e:
        print(f"❌ CentralStreamManager import failed: {e}")
        traceback.print_exc()
    
    try:
        from decision.decision_engine import DecisionEngine
        print("✅ DecisionEngine import: OK")
    except Exception as e:
        print(f"❌ DecisionEngine import failed: {e}")
        traceback.print_exc()
    
    try:
        from workflows.intelligent_workflow_generator import IntelligentWorkflowGenerator
        print("✅ IntelligentWorkflowGenerator import: OK")
    except Exception as e:
        print(f"❌ IntelligentWorkflowGenerator import failed: {e}")
        traceback.print_exc()
    
    try:
        from workflows.adaptive_execution_engine import AdaptiveExecutionEngine
        print("✅ AdaptiveExecutionEngine import: OK")
    except Exception as e:
        print(f"❌ AdaptiveExecutionEngine import failed: {e}")
        traceback.print_exc()
    
    try:
        from workflows.workflow_orchestrator import WorkflowOrchestrator
        print("✅ WorkflowOrchestrator import: OK")
    except Exception as e:
        print(f"❌ WorkflowOrchestrator import failed: {e}")
        traceback.print_exc()
    
    try:
        from analysis.deductive_analysis_engine import DeductiveAnalysisEngine
        print("✅ DeductiveAnalysisEngine import: OK")
    except Exception as e:
        print(f"❌ DeductiveAnalysisEngine import failed: {e}")
        traceback.print_exc()
    
    try:
        from conversation.conversation_memory_engine import ConversationMemoryEngine
        print("✅ ConversationMemoryEngine import: OK")
    except Exception as e:
        print(f"❌ ConversationMemoryEngine import failed: {e}")
        traceback.print_exc()
    
    try:
        from conversation.clarification_intelligence import ClarificationIntelligence
        print("✅ ClarificationIntelligence import: OK")
    except Exception as e:
        print(f"❌ ClarificationIntelligence import failed: {e}")
        traceback.print_exc()
    
    # Test 4: Service integrations
    try:
        from integrations.asset_client import AssetServiceClient
        print("✅ AssetServiceClient import: OK")
    except Exception as e:
        print(f"❌ AssetServiceClient import failed: {e}")
        traceback.print_exc()
    
    try:
        from integrations.automation_client import AutomationServiceClient
        print("✅ AutomationServiceClient import: OK")
    except Exception as e:
        print(f"❌ AutomationServiceClient import failed: {e}")
        traceback.print_exc()
    
    try:
        from integrations.network_client import NetworkAnalyzerClient
        print("✅ NetworkAnalyzerClient import: OK")
    except Exception as e:
        print(f"❌ NetworkAnalyzerClient import failed: {e}")
        traceback.print_exc()
    
    try:
        from integrations.communication_client import CommunicationServiceClient
        print("✅ CommunicationServiceClient import: OK")
    except Exception as e:
        print(f"❌ CommunicationServiceClient import failed: {e}")
        traceback.print_exc()
    
    try:
        from integrations.prefect_client import PrefectClient
        print("✅ PrefectClient import: OK")
    except Exception as e:
        print(f"❌ PrefectClient import failed: {e}")
        traceback.print_exc()
    
    print("\n🔍 Import testing complete")
    return True

if __name__ == "__main__":
    print("🧪 PHASE 8: DEBUG TEST - IMPORT ANALYSIS")
    print("=" * 60)
    test_imports()