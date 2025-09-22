#!/usr/bin/env python3
"""
Start Continuous Training - Simple launcher for continuous internet learning
"""

import sys
import signal
import time
from continuous_internet_learner import ContinuousInternetLearner

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n🛑 Stopping continuous training...')
    if 'learner' in globals():
        learner.stop_continuous_learning()
    sys.exit(0)

def main():
    """Start continuous learning with proper error handling"""
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 STARTING CONTINUOUS INTERNET TRAINING SYSTEM")
    print("=" * 50)
    
    try:
        # Create learner instance
        global learner
        learner = ContinuousInternetLearner()
        
        print("✅ Continuous learner initialized")
        print("🎯 Starting continuous learning...")
        print("📝 Logs will be written to the console")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 50)
        
        # Start continuous learning
        learner.start_continuous_learning()
        
    except KeyboardInterrupt:
        print("\n🛑 Continuous learning stopped by user")
        if 'learner' in globals():
            learner.stop_continuous_learning()
    except Exception as e:
        print(f"❌ Error in continuous learning: {e}")
        import traceback
        traceback.print_exc()
        if 'learner' in globals():
            learner.stop_continuous_learning()
    
    print("✅ Continuous training system stopped")

if __name__ == "__main__":
    main()