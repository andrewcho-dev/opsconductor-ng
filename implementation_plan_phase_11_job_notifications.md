# Phase 11: Job Notification Steps

**Status:** 📋 DEFERRED TO FUTURE PHASE  
**Note:** Phase 11 was repurposed for Target Groups & UI Improvements. Job Notifications moved to future phase.  
**Estimated Timeline:** 4 Weeks  
**Stack:** Python FastAPI, Jinja2, PostgreSQL, React TypeScript

---

## 🎯 **PHASE OVERVIEW**

Job notification steps will allow users to insert notification actions anywhere within job workflows, sending contextual notifications via multiple channels (email, Slack, Teams, webhooks) with dynamic content based on job variables and execution state. This provides real-time job monitoring and proactive error handling.

---

## 📧 **NOTIFICATION STEP TYPES**

### **Core Notification Steps**
- **notify.email**: Send email notifications with dynamic content
- **notify.slack**: Send Slack messages to channels or users
- **notify.teams**: Send Microsoft Teams notifications
- **notify.webhook**: Send HTTP webhook notifications
- **notify.conditional**: Conditional notifications based on job state

### **Advanced Notification Features**
- **Dynamic Content**: Variable substitution from job context
- **Template Engine**: Jinja2-based template system for rich content
- **Conditional Logic**: Send notifications based on job conditions
- **Escalation Rules**: Multi-level notification escalation
- **Rate Limiting**: Prevent notification spam

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 11.1: Email Notification Step Foundation** (Week 1)

#### **Email Notification Step Implementation**
```python
class EmailNotificationStep:
    def __init__(self, step_config: Dict):
        self.config = step_config
        self.template_engine = Jinja2Environment()
    
    async def execute(self, job_context: JobContext) -> StepResult:
        try:
            # Render email content with job context
            subject = self.template_engine.render(
                self.config['subject_template'], 
                job_context.variables
            )
            body = self.template_engine.render(
                self.config['body_template'], 
                job_context.variables
            )
            
            # Send email notification
            notification_service = NotificationService()
            result = await notification_service.send_email(
                recipients=self.config['recipients'],
                subject=subject,
                body=body,
                attachments=self.config.get('attachments', [])
            )
            
            return StepResult(
                status='completed',
                output=f"Email sent to {len(self.config['recipients'])} recipients",
                metadata={'notification_id': result['id']}
            )
            
        except Exception as e:
            return StepResult(
                status='failed',
                error_message=str(e)
            )
```

#### **Job Step Configuration Schema**
```json
{
  "name": "Send Status Email",
  "type": "notify.email",
  "config": {
    "recipients": [
      "admin@company.com",
      "{{job.created_by.email}}"
    ],
    "subject_template": "Job '{{job.name}}' Status: {{job.status}}",
    "body_template": "Job {{job.name}} on target {{target.hostname}} completed with status: {{job.status}}\n\nExecution time: {{job.execution_time_ms}}ms\nSteps completed: {{job.completed_steps}}/{{job.total_steps}}",
    "send_on": ["success", "failure"],
    "attachments": [
      {
        "type": "job_log",
        "filename": "job_{{job.id}}_log.txt"
      }
    ]
  }
}
```

#### **Database Schema Extensions**
```sql
-- Notification step execution tracking
CREATE TABLE notification_step_executions (
    id SERIAL PRIMARY KEY,
    job_run_step_id INTEGER REFERENCES job_run_steps(id),
    notification_type VARCHAR(50) NOT NULL,
    recipients JSONB NOT NULL,
    subject TEXT,
    content TEXT,
    delivery_status VARCHAR(50) DEFAULT 'pending',
    delivery_attempts INTEGER DEFAULT 0,
    delivered_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification templates for reuse
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    notification_type VARCHAR(50) NOT NULL,
    subject_template TEXT,
    body_template TEXT,
    default_config JSONB,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **PHASE 11.2: Template Engine & Variable Substitution** (Week 2)

#### **Job Context Variables**
```python
class JobContext:
    def __init__(self, job_run, target, user):
        self.variables = {
            'job': {
                'id': job_run.id,
                'name': job_run.job.name,
                'status': job_run.status,
                'started_at': job_run.started_at,
                'completed_at': job_run.completed_at,
                'execution_time_ms': job_run.execution_time_ms,
                'total_steps': job_run.total_steps,
                'completed_steps': job_run.completed_steps,
                'failed_steps': job_run.failed_steps,
                'parameters': job_run.parameters
            },
            'target': {
                'id': target.id,
                'name': target.name,
                'hostname': target.hostname,
                'os_type': target.os_type,
                'tags': target.tags
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'system': {
                'timestamp': datetime.now().isoformat(),
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'opsconductor_url': os.getenv('OPSCONDUCTOR_URL')
            }
        }
    
    def add_step_result(self, step_name: str, result: StepResult):
        """Add step execution result to context"""
        if 'steps' not in self.variables:
            self.variables['steps'] = {}
        
        self.variables['steps'][step_name] = {
            'status': result.status,
            'output': result.output,
            'error_message': result.error_message,
            'execution_time_ms': result.execution_time_ms
        }
```

#### **Advanced Template Features**
```python
class NotificationTemplateEngine:
    def __init__(self):
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.jinja_env.filters['duration'] = self.format_duration
        self.jinja_env.filters['status_color'] = self.get_status_color
        self.jinja_env.filters['truncate_output'] = self.truncate_output
    
    def format_duration(self, milliseconds: int) -> str:
        """Format duration in human-readable format"""
        if milliseconds < 1000:
            return f"{milliseconds}ms"
        elif milliseconds < 60000:
            return f"{milliseconds/1000:.1f}s"
        else:
            return f"{milliseconds/60000:.1f}m"
    
    def get_status_color(self, status: str) -> str:
        """Get color for status display"""
        colors = {
            'completed': '#28a745',
            'failed': '#dc3545',
            'running': '#ffc107',
            'pending': '#6c757d'
        }
        return colors.get(status, '#6c757d')
    
    def render_template(self, template: str, context: Dict) -> str:
        """Render template with context variables"""
        template_obj = self.jinja_env.from_string(template)
        return template_obj.render(**context)
```

#### **Rich Email Templates**
```html
<!-- HTML Email Template -->
<html>
<head>
    <style>
        .status-{{ job.status }} { 
            color: {{ job.status | status_color }}; 
            font-weight: bold; 
        }
        .job-details { 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
        }
    </style>
</head>
<body>
    <h2>Job Execution Report</h2>
    
    <div class="job-details">
        <h3>Job: {{ job.name }}</h3>
        <p><strong>Status:</strong> <span class="status-{{ job.status }}">{{ job.status | upper }}</span></p>
        <p><strong>Target:</strong> {{ target.name }} ({{ target.hostname }})</p>
        <p><strong>Duration:</strong> {{ job.execution_time_ms | duration }}</p>
        <p><strong>Steps:</strong> {{ job.completed_steps }}/{{ job.total_steps }} completed</p>
        
        {% if job.status == 'failed' %}
        <h4>Error Details:</h4>
        <pre style="background: #f8d7da; padding: 10px; border-radius: 3px;">
        {% for step_name, step in steps.items() %}
            {% if step.status == 'failed' %}
{{ step_name }}: {{ step.error_message }}
            {% endif %}
        {% endfor %}
        </pre>
        {% endif %}
    </div>
    
    <p><small>Generated by OpsConductor at {{ system.timestamp }}</small></p>
</body>
</html>
```

---

### **PHASE 11.3: Frontend Integration** (Week 3)

#### **Notification Step Builder**
```typescript
const NotificationStepBuilder = ({ step, onStepUpdate }) => {
  const [notificationType, setNotificationType] = useState(step.config.type || 'email');
  const [recipients, setRecipients] = useState(step.config.recipients || []);
  const [template, setTemplate] = useState(step.config.template || '');
  
  return (
    <div className="notification-step-builder">
      <FormControl>
        <InputLabel>Notification Type</InputLabel>
        <Select value={notificationType} onChange={setNotificationType}>
          <MenuItem value="email">Email</MenuItem>
          <MenuItem value="slack">Slack</MenuItem>
          <MenuItem value="teams">Microsoft Teams</MenuItem>
          <MenuItem value="webhook">Webhook</MenuItem>
        </Select>
      </FormControl>
      
      <RecipientSelector 
        type={notificationType}
        recipients={recipients}
        onChange={setRecipients}
      />
      
      <TemplateEditor 
        template={template}
        variables={availableVariables}
        onChange={setTemplate}
      />
      
      <TemplatePreview 
        template={template}
        sampleContext={sampleJobContext}
      />
    </div>
  );
};
```

#### **Template Editor with Variable Assistance**
```typescript
const TemplateEditor = ({ template, variables, onChange }) => {
  const [cursorPosition, setCursorPosition] = useState(0);
  const [showVariables, setShowVariables] = useState(false);
  
  const insertVariable = (variablePath: string) => {
    const newTemplate = 
      template.slice(0, cursorPosition) + 
      `{{${variablePath}}}` + 
      template.slice(cursorPosition);
    onChange(newTemplate);
  };
  
  return (
    <div className="template-editor">
      <div className="editor-toolbar">
        <Button onClick={() => setShowVariables(!showVariables)}>
          Insert Variable
        </Button>
      </div>
      
      <textarea
        value={template}
        onChange={(e) => onChange(e.target.value)}
        onSelect={(e) => setCursorPosition(e.target.selectionStart)}
        placeholder="Enter your notification template..."
        rows={10}
      />
      
      {showVariables && (
        <VariablePalette 
          variables={variables}
          onVariableSelect={insertVariable}
        />
      )}
    </div>
  );
};
```

---

### **PHASE 11.4: Multi-Channel Support** (Week 4)

#### **Slack Notification Step**
```python
class SlackNotificationStep:
    def __init__(self, step_config: Dict):
        self.config = step_config
    
    async def execute(self, job_context: JobContext) -> StepResult:
        webhook_url = self.config['webhook_url']
        
        # Build Slack message
        message = {
            "text": self.render_template(self.config['message_template'], job_context.variables),
            "attachments": [
                {
                    "color": self.get_status_color(job_context.variables['job']['status']),
                    "fields": [
                        {
                            "title": "Job",
                            "value": job_context.variables['job']['name'],
                            "short": True
                        },
                        {
                            "title": "Target",
                            "value": job_context.variables['target']['hostname'],
                            "short": True
                        },
                        {
                            "title": "Duration",
                            "value": f"{job_context.variables['job']['execution_time_ms']}ms",
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": job_context.variables['job']['status'].upper(),
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # Send to Slack
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status == 200:
                    return StepResult(status='completed', output='Slack notification sent')
                else:
                    return StepResult(status='failed', error_message=f'Slack API error: {response.status}')
```

#### **Teams Notification Step**
```python
class TeamsNotificationStep:
    def __init__(self, step_config: Dict):
        self.config = step_config
    
    async def execute(self, job_context: JobContext) -> StepResult:
        webhook_url = self.config['webhook_url']
        
        # Build Teams adaptive card
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self.get_status_color(job_context.variables['job']['status']),
            "summary": f"Job {job_context.variables['job']['name']} {job_context.variables['job']['status']}",
            "sections": [
                {
                    "activityTitle": f"Job: {job_context.variables['job']['name']}",
                    "activitySubtitle": f"Target: {job_context.variables['target']['hostname']}",
                    "facts": [
                        {
                            "name": "Status",
                            "value": job_context.variables['job']['status'].upper()
                        },
                        {
                            "name": "Duration",
                            "value": f"{job_context.variables['job']['execution_time_ms']}ms"
                        },
                        {
                            "name": "Steps",
                            "value": f"{job_context.variables['job']['completed_steps']}/{job_context.variables['job']['total_steps']}"
                        }
                    ]
                }
            ]
        }
        
        # Send to Teams
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=card) as response:
                if response.status == 200:
                    return StepResult(status='completed', output='Teams notification sent')
                else:
                    return StepResult(status='failed', error_message=f'Teams API error: {response.status}')
```

---

## 🔧 **API ENDPOINTS**

### **Notification Templates**
```
POST   /api/v1/notification-templates     # Create notification template
GET    /api/v1/notification-templates     # List notification templates
GET    /api/v1/notification-templates/:id # Get template details
PUT    /api/v1/notification-templates/:id # Update template
DELETE /api/v1/notification-templates/:id # Delete template
```

### **Template Testing**
```
POST   /api/v1/notification-templates/:id/test # Test template with sample data
POST   /api/v1/notification-templates/render   # Render template with custom context
```

### **Notification History**
```
GET    /api/v1/notification-executions    # List notification executions
GET    /api/v1/notification-executions/:id # Get execution details
POST   /api/v1/notification-executions/:id/retry # Retry failed notification
```

---

## 🎯 **EXPECTED BENEFITS**

### **Operational Benefits**
- **Real-time Awareness**: Immediate notification of job status changes
- **Proactive Monitoring**: Early warning of job failures and issues
- **Contextual Information**: Rich, contextual notification content
- **Multi-channel Reach**: Notifications via preferred communication channels

### **Workflow Integration**
- **Embedded Notifications**: Notifications as part of job workflow
- **Conditional Alerts**: Smart notifications based on job conditions
- **Escalation Support**: Multi-level notification escalation
- **Template Reuse**: Standardized notification templates across jobs

### **User Experience**
- **Customizable Content**: User-defined notification templates
- **Variable Substitution**: Dynamic content based on job context
- **Rich Formatting**: HTML emails and formatted chat messages
- **Delivery Tracking**: Complete notification delivery tracking

---

This phase will transform OpsConductor's notification capabilities from simple job completion alerts to comprehensive, contextual communication system that keeps teams informed and enables proactive response to automation events.