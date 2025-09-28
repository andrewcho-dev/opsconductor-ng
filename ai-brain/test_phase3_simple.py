#!/usr/bin/env python3
"""
Simple Phase 3 Intelligence Test
Tests core functionality without external dependencies.
"""

import asyncio
import sys
import os

# Add the ai-brain directory to Python path
sys.path.insert(0, '/home/opsconductor/opsconductor-ng/ai-brain')

async def test_progress_intelligence():
    """Test Progress Intelligence Engine"""
    print("🧠 Testing Progress Intelligence Engine...")
    
    try:
        from intelligence import create_progress_intelligence_engine, OperationType, ComplexityLevel
        
        engine = create_progress_intelligence_engine()
        
        # Test operation analysis
        message = "Analyze this complex Python code for performance issues and suggest optimizations"
        context = await engine.analyze_operation(message)
        
        print(f"✅ Operation Type: {context.operation_type.value}")
        print(f"✅ Complexity Level: {context.complexity_level.value}")
        print(f"✅ Estimated Duration: {context.estimated_duration:.1f}s")
        print(f"✅ Key Concepts: {context.key_concepts[:3]}...")
        print(f"✅ User Intent: {context.user_intent}")
        print(f"✅ Requires Code Analysis: {context.requires_code}")
        
        # Test dynamic milestones
        milestones = await engine.generate_dynamic_milestones(context)
        print(f"✅ Generated {len(milestones)} dynamic milestones")
        
        for i, milestone in enumerate(milestones[:2]):
            print(f"   Milestone {i+1}: {milestone.name} ({milestone.estimated_completion*100:.0f}%)")
        
        # Test progress intelligence calculation
        progress_intel = await engine.calculate_progress_intelligence(
            operation_context=context,
            milestones=milestones,
            current_step=3,
            total_steps=5,
            elapsed_time=2.5
        )
        
        print(f"✅ Progress: {progress_intel.completion_percentage*100:.1f}%")
        print(f"✅ ETA: {progress_intel.eta_seconds:.1f}s")
        print(f"✅ Confidence: {progress_intel.confidence_score:.2f}")
        print(f"✅ Current Phase: {progress_intel.current_phase.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Progress Intelligence test failed: {e}")
        return False

async def test_operation_analyzer():
    """Test Operation Analyzer"""
    print("\n📊 Testing Operation Analyzer...")
    
    try:
        from intelligence import create_operation_analyzer, OperationType, ComplexityLevel
        from intelligence.progress_intelligence import OperationContext
        
        analyzer = create_operation_analyzer()
        
        # Create test context
        context = OperationContext(
            operation_type=OperationType.CODE_ANALYSIS,
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=8.0,
            key_concepts=["code", "analysis", "performance"],
            user_intent="analyze",
            technical_domain="web_development",
            requires_code=True,
            requires_analysis=True
        )
        
        thinking_steps = [
            "Understanding code structure",
            "Analyzing performance patterns",
            "Identifying optimization opportunities"
        ]
        
        # Test operation depth analysis
        metrics = await analyzer.analyze_operation_depth(
            message="Analyze this complex web application code",
            operation_context=context,
            thinking_steps=thinking_steps
        )
        
        print(f"✅ Thinking Steps: {metrics.thinking_steps_count}")
        print(f"✅ Complexity Indicators: {len(metrics.complexity_indicators)}")
        print(f"✅ Performance Score: {metrics.performance_score:.2f}")
        print(f"✅ Context Switches: {metrics.context_switches}")
        
        if metrics.complexity_indicators:
            print(f"✅ Top Indicators: {metrics.complexity_indicators[:2]}")
        
        # Test trajectory prediction
        trajectory = await analyzer.predict_operation_trajectory(context, metrics, 3.0)
        print(f"✅ Predicted Total Steps: {trajectory['predicted_total_steps']}")
        print(f"✅ Trajectory Type: {trajectory['trajectory_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Operation Analyzer test failed: {e}")
        return False

async def test_smart_messaging():
    """Test Smart Progress Messaging"""
    print("\n💬 Testing Smart Progress Messaging...")
    
    try:
        from intelligence import (
            create_smart_progress_messaging, 
            MessageContext, MessageTone, OperationType, ComplexityLevel, ProgressPhase
        )
        from intelligence.progress_intelligence import OperationContext, ProgressIntelligence, ProgressMilestone
        from intelligence.operation_analyzer import OperationMetrics
        
        messaging = create_smart_progress_messaging()
        
        # Create test data
        context = OperationContext(
            operation_type=OperationType.CODE_ANALYSIS,
            complexity_level=ComplexityLevel.COMPLEX,
            estimated_duration=8.0,
            key_concepts=["code", "analysis"],
            user_intent="analyze"
        )
        
        milestone = ProgressMilestone(
            phase=ProgressPhase.SOLUTION_GENERATION,
            name="Code Analysis",
            description="Analyzing code patterns",
            estimated_completion=0.6,
            context_message="Analyzing code structure...",
            user_benefit="Identifying improvements"
        )
        
        progress_intel = ProgressIntelligence(
            operation_context=context,
            milestones=[milestone],
            current_phase=ProgressPhase.SOLUTION_GENERATION,
            completion_percentage=0.6,
            eta_seconds=3.2,
            confidence_score=0.85,
            contextual_message="Analyzing code patterns...",
            next_milestone=None
        )
        
        metrics = OperationMetrics(
            thinking_steps_count=4,
            complexity_indicators=["high_technical_vocabulary"],
            performance_score=0.8
        )
        
        # Test message generation for different contexts
        contexts_to_test = [MessageContext.STARTUP, MessageContext.PROGRESS, MessageContext.COMPLETION]
        
        for context_type in contexts_to_test:
            message = await messaging.generate_adaptive_message(
                progress_intelligence=progress_intel,
                operation_metrics=metrics,
                message_context=context_type,
                user_id="test_user"
            )
            
            print(f"✅ {context_type.value.title()} Message: {message.content[:50]}...")
            print(f"   Tone: {message.tone.value}, Confidence: {message.confidence:.2f}")
        
        # Test insights
        insights = messaging.get_messaging_insights()
        print(f"✅ Total Templates: {insights['total_templates']}")
        print(f"✅ Supported Tones: {len(insights['supported_tones'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Smart Messaging test failed: {e}")
        return False

async def test_thinking_client_intelligence():
    """Test Thinking Client Intelligence Integration"""
    print("\n🤖 Testing Thinking Client Intelligence...")
    
    try:
        from integrations.thinking_llm_client import ThinkingConfig
        from intelligence import MessageTone
        
        # Test intelligent configuration
        config = ThinkingConfig(
            enable_intelligence=True,
            enable_contextual_messaging=True,
            enable_dynamic_milestones=True,
            enable_complexity_analysis=True,
            enable_adaptive_communication=True,
            message_tone=MessageTone.FRIENDLY
        )
        
        print(f"✅ Intelligence Enabled: {config.enable_intelligence}")
        print(f"✅ Contextual Messaging: {config.enable_contextual_messaging}")
        print(f"✅ Dynamic Milestones: {config.enable_dynamic_milestones}")
        print(f"✅ Complexity Analysis: {config.enable_complexity_analysis}")
        print(f"✅ Adaptive Communication: {config.enable_adaptive_communication}")
        print(f"✅ Message Tone: {config.message_tone.value}")
        
        # Note: We can't fully test the client without mocking dependencies,
        # but we can verify the configuration works
        
        return True
        
    except Exception as e:
        print(f"❌ Thinking Client Intelligence test failed: {e}")
        return False

async def test_end_to_end_intelligence():
    """Test end-to-end intelligence workflow"""
    print("\n🔄 Testing End-to-End Intelligence Workflow...")
    
    try:
        from intelligence import (
            create_progress_intelligence_engine,
            create_operation_analyzer,
            create_smart_progress_messaging,
            MessageContext
        )
        
        # Create all systems
        progress_engine = create_progress_intelligence_engine()
        operation_analyzer = create_operation_analyzer()
        smart_messaging = create_smart_progress_messaging()
        
        # Test message
        message = "Help me design a scalable microservices architecture with monitoring"
        
        # Step 1: Analyze operation
        context = await progress_engine.analyze_operation(message)
        print(f"✅ Step 1 - Operation Analysis: {context.operation_type.value} ({context.complexity_level.value})")
        
        # Step 2: Generate milestones
        milestones = await progress_engine.generate_dynamic_milestones(context)
        print(f"✅ Step 2 - Dynamic Milestones: {len(milestones)} milestones generated")
        
        # Step 3: Simulate progress
        for step in range(1, 4):
            elapsed_time = step * 2.0
            
            # Calculate progress intelligence
            progress_intel = await progress_engine.calculate_progress_intelligence(
                operation_context=context,
                milestones=milestones,
                current_step=step,
                total_steps=3,
                elapsed_time=elapsed_time
            )
            
            # Analyze metrics
            thinking_steps = [f"Step {i}: Processing..." for i in range(1, step + 1)]
            metrics = await operation_analyzer.analyze_operation_depth(
                message, context, thinking_steps
            )
            
            # Generate message
            adaptive_msg = await smart_messaging.generate_adaptive_message(
                progress_intelligence=progress_intel,
                operation_metrics=metrics,
                message_context=MessageContext.PROGRESS,
                user_id="test_user",
                elapsed_time=elapsed_time
            )
            
            print(f"✅ Step 3.{step} - Progress {progress_intel.completion_percentage*100:.0f}%: {adaptive_msg.content[:40]}...")
        
        print("✅ End-to-end workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

async def main():
    """Run all Phase 3 tests"""
    print("🚀 OUIOE Phase 3: Intelligent Progress Communication Tests")
    print("=" * 60)
    
    tests = [
        test_progress_intelligence,
        test_operation_analyzer,
        test_smart_messaging,
        test_thinking_client_intelligence,
        test_end_to_end_intelligence
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PHASE 3 TESTS PASSED! Intelligence systems working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)