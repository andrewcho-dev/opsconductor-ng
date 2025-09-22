#!/usr/bin/env python3
"""
Continuous Training Daemon
A robust daemon for running continuous internet training
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path

# Add the ai-brain directory to Python path
sys.path.append(str(Path(__file__).parent))

from continuous_internet_learner import ContinuousInternetLearner

class TrainingDaemon:
    def __init__(self, pidfile='/tmp/continuous_training.pid'):
        self.pidfile = pidfile
        self.learner = None
        self.running = False
        
    def daemonize(self):
        """Daemonize the process"""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit parent
        except OSError as e:
            sys.stderr.write(f"Fork #1 failed: {e}\n")
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit second parent
        except OSError as e:
            sys.stderr.write(f"Fork #2 failed: {e}\n")
            sys.exit(1)
            
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Setup logging to file
        log_file = '/home/opsconductor/opsconductor-ng/ai-brain/daemon.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Write pidfile
        with open(self.pidfile, 'w') as f:
            f.write(str(os.getpid()))
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
        if self.learner:
            self.learner.stop()
            
    def start(self):
        """Start the daemon"""
        # Check if already running
        if os.path.exists(self.pidfile):
            with open(self.pidfile, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if process exists
                print(f"Daemon already running with PID {pid}")
                return
            except OSError:
                # Process doesn't exist, remove stale pidfile
                os.remove(self.pidfile)
                
        print("🚀 Starting continuous training daemon...")
        self.daemonize()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.running = True
        logging.info("🚀 CONTINUOUS TRAINING DAEMON STARTED")
        
        try:
            # Initialize the learner
            self.learner = ContinuousInternetLearner()
            logging.info("✅ Continuous learner initialized")
            
            # Start continuous learning
            self.learner.start_continuous_learning()
            logging.info("🎯 Continuous learning started")
            
            # Keep daemon running
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logging.error(f"❌ Error in daemon: {e}")
        finally:
            self.cleanup()
            
    def stop(self):
        """Stop the daemon"""
        if not os.path.exists(self.pidfile):
            print("Daemon not running")
            return
            
        with open(self.pidfile, 'r') as f:
            pid = int(f.read().strip())
            
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"🛑 Stopping daemon with PID {pid}")
            
            # Wait for process to stop
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(1)
                except OSError:
                    break
            else:
                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
                print("🔥 Force killed daemon")
                
        except OSError as e:
            print(f"Error stopping daemon: {e}")
            
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
            
    def status(self):
        """Check daemon status"""
        if not os.path.exists(self.pidfile):
            print("❌ Daemon not running")
            return False
            
        with open(self.pidfile, 'r') as f:
            pid = int(f.read().strip())
            
        try:
            os.kill(pid, 0)
            print(f"✅ Daemon running with PID {pid}")
            return True
        except OSError:
            print("❌ Daemon not running (stale pidfile)")
            os.remove(self.pidfile)
            return False
            
    def cleanup(self):
        """Cleanup resources"""
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
        logging.info("🧹 Daemon cleanup completed")

def main():
    daemon = TrainingDaemon()
    
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.stop()
            time.sleep(2)
            daemon.start()
        elif sys.argv[1] == 'status':
            daemon.status()
        else:
            print("Usage: python continuous_training_daemon.py {start|stop|restart|status}")
    else:
        print("Usage: python continuous_training_daemon.py {start|stop|restart|status}")

if __name__ == "__main__":
    main()