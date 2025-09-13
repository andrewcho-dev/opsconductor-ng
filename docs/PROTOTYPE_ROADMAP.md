# OpsConductor AI Prototype - Implementation Roadmap

## Quick Prototype Strategy

**Goal**: Get a working AI automation prototype running in 1-2 weeks that can handle the "stationcontroller.exe update" scenario end-to-end.

## Phase 1: Minimal Viable Prototype (Week 1)

### Day 1-2: AI Service Foundation
**Objective**: Basic AI service that can parse simple requests and generate workflows

#### Tasks:
1. **Create AI Service Structure**
   ```bash
   mkdir -p ai-service
   cd ai-service
   # Create basic FastAPI service
   ```

2. **Simple NLP Processing**
   - Use basic regex patterns (no complex NLP initially)
   - Focus on key patterns: "group X", "process Y", "service Z"
   - Extract: target groups, operations, file paths

3. **Asset Service Integration**
   - Create client to query existing asset service
   - Get target groups and their members
   - Retrieve target credentials and services

#### Deliverable:
```python
# ai-service/main.py - Basic working service
@app.post("/create-job")
async def create_job(request: JobRequest):
    # Parse: "update stationcontroller on CIS servers"
    # Return: Valid workflow JSON using existing format
```

### Day 3-4: Windows Management Library with OUSS Integration
**Objective**: Basic Windows operations via WinRM using OpsConductor Universal Scripting Standard

#### Tasks:
1. **Create Windows Library with OUSS Compliance**
   ```python
   # automation-service/libraries/windows_management.py
   from .scripting_engine import OUSSScriptGenerator
   
   class WindowsManagement:
       def __init__(self):
           self.script_generator = OUSSScriptGenerator()
       
       async def check_process_status(self, targets, process_name):
           # Generate OUSS-compliant PowerShell script
           script = self.script_generator.generate_windows_process_check(process_name)
           return await self.execute_script_on_targets(targets, script)
       
       async def stop_service(self, targets, service_name):
           # Generate OUSS-compliant service management script
           script = self.script_generator.generate_windows_service_script(service_name, 'stop')
           return await self.execute_script_on_targets(targets, script)
   ```

2. **OUSS Script Engine**
   ```python
   # automation-service/libraries/scripting_engine.py
   class OUSSScriptGenerator:
       """OpsConductor Universal Scripting Standard generator"""
       
       def generate_windows_service_script(self, service_name: str, operation: str):
           return {
               'type': 'powershell',
               'script': self._build_powershell_service_script(service_name, operation),
               'validation_script': f'Get-Service -Name "{service_name}" | Select-Object Name, Status',
               'rollback_script': self._build_rollback_script(service_name, operation),
               'timeout': 60,
               'requires_admin': True
           }
   ```

3. **WinRM Integration with Progress Reporting**
   - Use `pywinrm` library with OUSS script execution
   - Real-time progress reporting from PowerShell scripts
   - Structured logging and error handling
   - Automatic rollback on failures

4. **Test with Single Target**
   - Manual test with one Windows server
   - Verify OUSS script generation and execution
   - Test progress reporting and error handling

#### Deliverable:
Working Windows management functions using OUSS-compliant scripts with full observability

### Day 5-7: End-to-End Integration with Real-Time Monitoring
**Objective**: Complete workflow from chat input to execution with full visibility

#### Tasks:
1. **Frontend Chat Interface with Progress Monitoring**
   ```typescript
   // Chat component with text input and AI responses
   // Workflow preview with step breakdown
   // Real-time progress monitoring components:
   //   - Overall step progress bar
   //   - Target-level progress (completed/failed/pending)
   //   - Live log stream
   //   - Current operation indicator
   //   - ETA and elapsed time
   ```

2. **WebSocket Progress Broadcasting**
   - WebSocket endpoint for real-time job updates
   - Progress events from Celery workers
   - Live log streaming to frontend
   - Connection management for multiple users

3. **Enhanced Workflow Execution**
   - Integrate AI service with automation service
   - Submit generated workflows to existing Celery workers
   - **Real-time progress reporting from each operation**
   - **Target-by-target status updates**
   - **Step completion notifications**

4. **Comprehensive Testing**
   - Test complete scenario: "update stationcontroller on CIS servers"
   - Verify each step executes correctly
   - **Verify real-time progress updates work correctly**
   - **Test progress monitoring with multiple targets**
   - Check database logging

#### Deliverable:
Working prototype with complete visibility into AI-generated job execution

## Phase 2: Enhanced Prototype (Week 2)

### Day 8-10: Linux Support
**Objective**: Add Linux management capabilities

#### Tasks:
1. **Linux Management Library**
   ```python
   # automation-service/libraries/linux_management.py
   async def execute_command(targets, command)
   async def install_package(targets, package_name)
   async def copy_file(targets, source, destination)
   ```

2. **SSH/Telnet Connections**
   - Use `paramiko` for SSH
   - Use `telnetlib` for Telnet
   - Auto-select connection method based on target services

3. **Package Manager Detection**
   - Auto-detect apt/yum/dnf
   - Handle different Linux distributions

#### Deliverable:
Linux management functions working with SSH and Telnet targets

### Day 11-12: Enhanced AI Scenarios
**Objective**: Handle more complex requests and mixed environments

#### Tasks:
1. **Scenario Recognition**
   - Package updates: "update nginx on web servers"
   - Service management: "restart apache on all servers"
   - Mixed environments: "stop service on all servers in group X"

2. **Clarifying Questions**
   - Ask for missing information
   - Suggest best practices
   - Confirm potentially destructive operations

3. **Error Handling**
   - Graceful failure handling
   - Continue on individual target failures
   - Comprehensive error reporting

#### Deliverable:
AI that can handle multiple scenario types and ask intelligent questions

### Day 13-14: Polish and Testing
**Objective**: Production-ready prototype

#### Tasks:
1. **UI/UX Improvements**
   - Better chat interface
   - Workflow visualization
   - Progress indicators

2. **Comprehensive Testing**
   - Test with multiple target groups
   - Test Windows and Linux scenarios
   - Test error conditions

3. **Documentation**
   - User guide for AI commands
   - Technical documentation
   - Demo scenarios

#### Deliverable:
Polished prototype ready for user testing

## Technical Implementation Details

### AI Service Structure
```
ai-service/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── nlp_processor.py     # Natural language processing
├── workflow_generator.py # Workflow generation logic
├── asset_client.py      # Asset service integration
├── requirements.txt     # Dependencies
└── Dockerfile          # Container definition
```

### Key Dependencies
```python
# ai-service/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
spacy==3.7.2
pydantic==2.5.0
python-multipart==0.0.6

# automation-service additions
pywinrm==0.4.3
paramiko==3.3.1
```

### Database Schema Extensions
```sql
-- Add AI-specific tables if needed
CREATE TABLE IF NOT EXISTS automation.ai_conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    conversation_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automation.ai_job_mappings (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES automation.ai_conversations(id),
    job_id INTEGER REFERENCES automation.jobs(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Quick Start Commands

### 1. Set Up AI Service
```bash
# Create AI service
mkdir -p ai-service
cd ai-service

# Create basic FastAPI app
cat > main.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="OpsConductor AI Service")

class JobRequest(BaseModel):
    description: str

@app.post("/create-job")
async def create_job(request: JobRequest):
    return {"message": "AI service working", "input": request.description}

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF

# Create requirements
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3005"]
EOF
```

### 2. Add to Docker Compose
```yaml
# Add to docker-compose.yml
  ai-service:
    build: ./ai-service
    container_name: opsconductor-ai
    ports:
      - "3005:3005"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/opsconductor
      - ASSET_SERVICE_URL=http://asset-service:3002
      - AUTOMATION_SERVICE_URL=http://automation-service:3003
    depends_on:
      - postgres
      - redis
      - asset-service
    networks:
      - opsconductor-net
    volumes:
      - ./ai-service:/app
    restart: unless-stopped
```

### 3. Create Windows Management Library
```bash
# Create library directory
mkdir -p automation-service/libraries

# Create basic Windows management
cat > automation-service/libraries/windows_management.py << 'EOF'
import winrm
from typing import List, Dict, Any

async def check_process_status(targets: List[Dict], process_name: str) -> Dict[str, Any]:
    """Check if process is running on Windows targets"""
    results = {}
    
    for target in targets:
        try:
            # TODO: Get credentials from asset service
            # TODO: Connect via WinRM
            # TODO: Check process status
            results[target['hostname']] = {
                'running': True,  # Placeholder
                'status': 'success'
            }
        except Exception as e:
            results[target['hostname']] = {
                'running': False,
                'status': 'error',
                'error': str(e)
            }
    
    return {'results': results}

# TODO: Implement other functions
EOF
```

### 4. Add WebSocket Progress Monitoring
```python
# automation-service/websocket_progress.py
from fastapi import WebSocket
import json
import asyncio

class ProgressBroadcaster:
    def __init__(self):
        self.connections = {}
    
    async def connect(self, websocket: WebSocket, job_id: int):
        await websocket.accept()
        if job_id not in self.connections:
            self.connections[job_id] = []
        self.connections[job_id].append(websocket)
    
    async def broadcast(self, job_id: int, data: dict):
        if job_id in self.connections:
            for ws in self.connections[job_id]:
                try:
                    await ws.send_text(json.dumps(data))
                except:
                    self.connections[job_id].remove(ws)

# Add to automation-service/main.py
@app.websocket("/jobs/{job_id}/progress")
async def job_progress_websocket(websocket: WebSocket, job_id: int):
    await progress_broadcaster.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        pass
```

### 5. Frontend Progress Components
```typescript
// frontend/src/components/JobProgressMonitor.tsx
import React, { useState, useEffect } from 'react';

interface JobProgress {
  jobId: number;
  status: string;
  currentStep: number;
  totalSteps: number;
  stepName: string;
  targetProgress: {
    completed: number;
    failed: number;
    total: number;
    currentTarget?: string;
  };
  logs: Array<{
    timestamp: string;
    target: string;
    message: string;
    level: 'info' | 'success' | 'error';
  }>;
}

const JobProgressMonitor: React.FC<{jobId: number}> = ({jobId}) => {
  const [progress, setProgress] = useState<JobProgress | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:3003/jobs/${jobId}/progress`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };
    
    return () => ws.close();
  }, [jobId]);
  
  if (!progress) return <div>Connecting to job progress...</div>;
  
  return (
    <div className="job-progress-monitor">
      <div className="progress-header">
        <h3>Job #{progress.jobId}</h3>
        <span className={`status ${progress.status}`}>{progress.status}</span>
      </div>
      
      {/* Step Progress */}
      <div className="step-progress">
        <div className="progress-label">
          Step {progress.currentStep} of {progress.totalSteps}: {progress.stepName}
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{width: `${(progress.currentStep / progress.totalSteps) * 100}%`}}
          />
        </div>
      </div>
      
      {/* Target Progress */}
      <div className="target-progress">
        <div className="progress-stats">
          <span className="success">✓ {progress.targetProgress.completed}</span>
          <span className="failed">✗ {progress.targetProgress.failed}</span>
          <span className="pending">⏳ {progress.targetProgress.total - progress.targetProgress.completed - progress.targetProgress.failed}</span>
        </div>
        
        {progress.targetProgress.currentTarget && (
          <div className="current-target">
            Processing: <strong>{progress.targetProgress.currentTarget}</strong>
          </div>
        )}
      </div>
      
      {/* Live Logs */}
      <div className="live-logs">
        <h4>Live Progress</h4>
        <div className="log-container">
          {progress.logs.slice(-10).map((log, i) => (
            <div key={i} className={`log-entry ${log.level}`}>
              <span className="timestamp">{log.timestamp}</span>
              <span className="target">[{log.target}]</span>
              <span className="message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### 6. Test the Prototype
```bash
# Start the services
docker-compose up -d

# Test AI service
curl -X POST http://localhost:3005/create-job \
  -H "Content-Type: application/json" \
  -d '{"description": "update stationcontroller on CIS servers"}'

# Test WebSocket connection
# Open browser to http://localhost:3000 and check progress monitoring

# Check logs
docker-compose logs ai-service
docker-compose logs automation-service
```

## Success Criteria for Prototype

### Week 1 Goals
- [ ] AI service responds to basic requests
- [ ] Can query asset service for target groups
- [ ] Generates valid workflow JSON
- [ ] Windows management library connects via WinRM
- [ ] Can execute simple Windows operations
- [ ] **Frontend chat interface with real-time monitoring**
- [ ] **WebSocket progress broadcasting working**
- [ ] **Multi-level progress bars (step + target progress)**
- [ ] **Live log streaming from operations**
- [ ] End-to-end test of stationcontroller scenario with full visibility

### Week 2 Goals
- [ ] Linux management via SSH/Telnet
- [ ] Handles mixed Windows/Linux environments
- [ ] AI asks clarifying questions
- [ ] Error handling and recovery
- [ ] Polished user interface
- [ ] Comprehensive testing completed

## Risk Mitigation

### Technical Risks
- **WinRM Connection Issues**: Test with simple PowerShell commands first
- **Credential Access**: Ensure asset service API provides decrypted credentials
- **Network Connectivity**: Verify Docker networking between services
- **Library Dependencies**: Use well-established libraries (paramiko, pywinrm)

### Timeline Risks
- **Scope Creep**: Focus only on core scenario for Week 1
- **Integration Complexity**: Test each component independently first
- **Debugging Time**: Allocate 30% buffer for troubleshooting

## Next Actions

1. **Immediate (Today)**
   - Create AI service skeleton
   - Add to docker-compose.yml
   - Test basic service startup

2. **This Week**
   - Implement basic NLP parsing
   - Create Windows management library
   - Build simple frontend interface

3. **Next Week**
   - Add Linux support
   - Enhance AI capabilities
   - Polish and test thoroughly

The key is to start simple and build incrementally, focusing on getting one complete scenario working before adding complexity.