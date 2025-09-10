#!/usr/bin/env python3
"""
Simple health check for Celery Beat
"""
import os
import sys
import time

def check_celery_beat():
    """Check if Celery Beat is running by checking the schedule file"""
    schedule_file = '/app/data/celerybeat-schedule'
    
    # Check if schedule file exists
    if not os.path.exists(schedule_file):
        print("Schedule file does not exist")
        return False
    
    # Check if file was modified recently (within last 5 minutes)
    try:
        mtime = os.path.getmtime(schedule_file)
        current_time = time.time()
        age = current_time - mtime
        
        if age > 300:  # 5 minutes
            print(f"Schedule file is too old: {age} seconds")
            return False
        
        print(f"Schedule file is fresh: {age} seconds old")
        return True
    except Exception as e:
        print(f"Error checking schedule file: {e}")
        return False

if __name__ == "__main__":
    if check_celery_beat():
        sys.exit(0)
    else:
        sys.exit(1)