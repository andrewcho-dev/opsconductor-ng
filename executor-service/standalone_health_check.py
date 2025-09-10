#!/usr/bin/env python3
"""
Standalone health check for Celery Beat
No shared module dependencies
"""
import os
import sys
import time

def check_beat_health():
    """Check if Celery Beat is healthy"""
    schedule_file = '/app/data/celerybeat-schedule'
    
    try:
        # Check if schedule file exists
        if not os.path.exists(schedule_file):
            print("UNHEALTHY: Schedule file does not exist")
            return False
        
        # Check if file was modified recently (within last 10 minutes)
        mtime = os.path.getmtime(schedule_file)
        current_time = time.time()
        age = current_time - mtime
        
        if age > 600:  # 10 minutes
            print(f"UNHEALTHY: Schedule file is too old: {age:.1f} seconds")
            return False
        
        print(f"HEALTHY: Schedule file is fresh: {age:.1f} seconds old")
        return True
        
    except Exception as e:
        print(f"UNHEALTHY: Error checking schedule file: {e}")
        return False

if __name__ == "__main__":
    if check_beat_health():
        sys.exit(0)
    else:
        sys.exit(1)