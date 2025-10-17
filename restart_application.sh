#!/bin/bash
# Restart the OpsConductor application

echo "Restarting OpsConductor application..."

# Check if we're running in a Docker container
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    
    # Find the main process
    PID=$(ps -ef | grep "python3 /home/opsconductor/opsconductor-ng/main.py" | grep -v grep | awk '{print $2}')
    
    if [ -n "$PID" ]; then
        echo "Stopping process with PID $PID"
        kill -15 $PID
        sleep 2
        
        # Check if process is still running
        if ps -p $PID > /dev/null; then
            echo "Process still running, force killing"
            kill -9 $PID
        fi
    else
        echo "Main process not found"
    fi
    
    # Start the application in the background
    echo "Starting application"
    nohup python3 /home/opsconductor/opsconductor-ng/main.py > /tmp/opsconductor.log 2>&1 &
    
    echo "Application restarted with PID $!"
    echo "Log file: /tmp/opsconductor.log"
else
    echo "Not running in Docker container, using systemctl"
    sudo systemctl restart opsconductor
fi

echo "Restart complete"