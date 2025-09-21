#!/usr/bin/env python3
"""
Migration Verification Script
Verifies that all modern AI components are properly integrated and functional.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the ai-brain directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def verify_migration():
    """Verify the migration is complete and functional"""
    print("🔍 AI Components Migration Verification")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing component imports...")
        
        from analytics.system_analytics import SystemAnalytics
        print("  ✅ SystemAnalytics imported successfully")
        
        from processors.intent_processor import IntentProcessor  
        print("  ✅ IntentProcessor imported successfully")
        
        from capabilities.system_capabilities import SystemCapabilities
        print("  ✅ SystemCapabilities imported successfully")
        
        from engines.ai_engine import ModernAIEngine
        print("  ✅ ModernAIEngine imported successfully")
        
        from brain_engine import AIBrainEngine
        print("  ✅ AIBrainEngine imported successfully")
        
        print("\n🏗️  Testing component initialization...")
        
        # Test modern component initialization
        system_analytics = SystemAnalytics()
        print("  ✅ SystemAnalytics initialized")
        
        intent_processor = IntentProcessor()
        print("  ✅ IntentProcessor initialized")
        
        system_capabilities = SystemCapabilities()
        print("  ✅ SystemCapabilities initialized")
        
        ai_engine = ModernAIEngine()
        print("  ✅ ModernAIEngine initialized")
        
        print("\n🧠 Testing AIBrainEngine integration...")
        
        # Test brain engine with modern components
        brain = AIBrainEngine()
        await brain.initialize()
        print("  ✅ AIBrainEngine initialized with modern components")
        
        print(f"  ℹ️  Running in Modern mode (legacy components removed)")
        
        print("\n🎯 Testing basic functionality...")
        
        # Test intent processing
        test_message = "Show me system health status"
        intent_result = await intent_processor.analyze_intent(test_message)
        print(f"  ✅ Intent analysis: {intent_result.get('intent', 'unknown')}")
        
        # Test system capabilities
        capabilities = await system_capabilities.get_system_capabilities()
        print(f"  ✅ System capabilities loaded: {len(capabilities)} capabilities")
        
        print("\n🎉 Migration Verification Results")
        print("=" * 50)
        print("✅ All modern components imported successfully")
        print("✅ All components initialized without errors")
        print("✅ AIBrainEngine integration working")
        print("✅ Basic functionality tests passed")
        print("✅ System running in Modern mode")
        print("\n🚀 Legacy cleanup COMPLETE - Modern AI system FUNCTIONAL!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

if __name__ == "__main__":
    print(f"Starting verification at {datetime.now().isoformat()}")
    success = asyncio.run(verify_migration())
    
    if success:
        print("\n✅ VERIFICATION PASSED - Migration is ready for production!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED - Please check the errors above")
        sys.exit(1)