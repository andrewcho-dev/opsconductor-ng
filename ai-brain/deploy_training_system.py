#!/usr/bin/env python3
"""
🚀 PROGRESSIVE AI TRAINING SYSTEM DEPLOYMENT
Deploy and massively expand training data for continuous AI improvement
"""

import asyncio
import json
import os
from adaptive_training_system import AdaptiveTrainingSystem
from training_data_manager import TrainingDataManager
from internet_training_harvester import InternetTrainingHarvester

async def deploy_and_expand_training():
    """Deploy the system and massively expand training data"""
    
    print("🚀 DEPLOYING PROGRESSIVE AI TRAINING SYSTEM")
    print("=" * 60)
    
    # Initialize the system
    training_system = AdaptiveTrainingSystem()
    manager = TrainingDataManager(training_system)
    harvester = InternetTrainingHarvester(training_system)
    
    # Import existing training data
    try:
        if os.path.exists('/tmp/training_export.json'):
            await manager.import_training_data('/tmp/training_export.json')
            print(f'✅ Successfully imported existing training examples')
        else:
            print(f'⚠️  No existing training data found - starting fresh')
    except Exception as e:
        print(f'⚠️  Error importing existing data: {e}')
    
    # Get current stats
    current_examples = len(training_system.training_examples)
    current_patterns = len(training_system.learned_patterns)
    
    print(f'📊 Current Training Stats:')
    print(f'   Total Examples: {current_examples}')
    print(f'   Learned Patterns: {current_patterns}')
    
    print("\n🎯 MASSIVELY EXPANDING TRAINING DATA...")
    print("=" * 60)
    
    # Generate massive training expansion
    expansion_data = await harvester.generate_massive_training_expansion()
    
    print(f"\n📈 TRAINING EXPANSION RESULTS:")
    print(f"   New Examples Generated: {len(expansion_data)}")
    
    # Add all new examples to the system
    for example in expansion_data:
        training_system.add_training_example(
            example['user_input'],
            example['intent'],
            example['confidence']
        )
    
    # Retrain the system
    training_system.retrain()
    
    # Get final stats
    final_examples = len(training_system.training_examples)
    final_patterns = len(training_system.learned_patterns)
    
    print(f"\n🎉 DEPLOYMENT COMPLETE!")
    print(f"=" * 60)
    print(f"📊 Final Training Stats:")
    print(f"   Total Examples: {final_examples} (+{final_examples - current_examples})")
    print(f"   Learned Patterns: {final_patterns} (+{final_patterns - current_patterns})")
    
    # Export the expanded training data
    export_path = '/tmp/massive_training_export.json'
    await manager.export_training_data(export_path)
    
    # Create backup
    backup_path = await manager.create_backup()
    
    print(f"\n💾 Data Management:")
    print(f"   Export File: {export_path}")
    print(f"   Backup File: {backup_path}")
    
    # Test the system with some queries
    print(f"\n🧪 TESTING EXPANDED SYSTEM:")
    print(f"=" * 60)
    
    test_queries = [
        "show me all our servers",
        "what infrastructure do we have",
        "list all production systems",
        "tell me about our network devices",
        "what assets are in our datacenter",
        "show server performance metrics",
        "create automation for backups",
        "troubleshoot network connectivity",
        "setup monitoring alerts",
        "apply security patches"
    ]
    
    for query in test_queries:
        intent, confidence = training_system.predict_intent(query)
        print(f"   Query: '{query}'")
        print(f"   Intent: {intent} (confidence: {confidence:.3f})")
        print()
    
    print("🎯 SYSTEM IS FULLY DEPLOYED AND READY FOR CONTINUOUS LEARNING!")
    print("The AI will now learn and improve from every user interaction.")
    
    return {
        'total_examples': final_examples,
        'learned_patterns': final_patterns,
        'export_path': export_path,
        'backup_path': backup_path
    }

if __name__ == "__main__":
    asyncio.run(deploy_and_expand_training())