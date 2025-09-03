# 🚀 OpsConductor Enhanced Features - Quick Start Guide

## Welcome to the Enhanced OpsConductor!

This guide will get you up and running with the new visual job builder, step libraries, and enhanced features in just a few minutes.

---

## 🏁 Quick Setup

### 1. Start the System
```bash
# Start all services
./start-python-system.sh

# Wait for services to be ready (about 30 seconds)
# Check status
./system-status.sh
```

### 2. Access the Enhanced Interface
Open your browser and navigate to:
- **Main Dashboard**: http://localhost:8080
- **Enhanced Jobs**: http://localhost:8080/enhanced-jobs
- **Step Library**: http://localhost:8080/step-library

### 3. Login
- **Username**: `admin`
- **Password**: `admin123`

---

## 🎨 Create Your First Visual Job

### Step 1: Navigate to Enhanced Jobs
1. Click on "Enhanced Jobs" in the navigation menu
2. Click "Create New Job" button

### Step 2: Build Your Workflow
1. **Drag nodes** from the left palette to the canvas
2. **Connect nodes** by dragging from output ports to input ports
3. **Configure nodes** by clicking on them and filling in the configuration panel

### Example Workflow:
```
[Start] → [Read File] → [Get System Info] → [Send Email] → [End]
```

### Step 3: Configure Each Node

#### Start Node
- Automatically added
- No configuration needed

#### Read File Node
```json
{
  "file_path": "/etc/hostname",
  "encoding": "utf-8"
}
```

#### Get System Info Node
```json
{
  "include_hardware": true,
  "include_network": true,
  "include_processes": false
}
```

#### Send Email Node
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "from_email": "admin@company.com",
  "to_emails": ["ops@company.com"],
  "subject": "System Report",
  "body": "System information collected successfully",
  "use_tls": true
}
```

### Step 4: Select Targets
1. In the target selector, choose which machines to run the job on
2. Use filters to find specific targets:
   - **Platform**: Windows, Linux, macOS
   - **Environment**: Production, Staging, Development
   - **Status**: Online, Offline

### Step 5: Save and Execute
1. Give your job a name and description
2. Click "Create Job"
3. Click "Execute" to run it immediately

---

## 📚 Explore Step Libraries

### Navigate to Step Library Registry
Go to http://localhost:8080/step-library

### Available Libraries:

#### 📁 File Operations
- Read/write files
- Copy/move files
- Directory management
- File permissions
- Compression

#### 🪟 Windows Operations
- Registry management
- Service control
- Process management
- Event log reading
- PowerShell execution

#### 💻 System Operations
- System information
- Performance monitoring
- Process management
- User/group management
- Environment variables

#### 🌐 Network Operations
- HTTP requests
- File downloads/uploads
- Email sending
- Network connectivity tests

#### 🔀 Logic & Control
- Conditional branching
- Loops and iterations
- Parallel execution
- Wait/delay operations

#### 🗄️ Database Operations
- Database connections
- SQL queries
- Data manipulation
- Backup operations

#### 🔒 Security Operations
- Data encryption/decryption
- Hash generation
- Vulnerability scanning
- Compliance checking

---

## 🎯 Common Use Cases

### 1. System Health Check
```
[Start] → [Get CPU Usage] → [Get Memory Usage] → [Get Disk Usage] → [Send Report] → [End]
```

### 2. File Backup and Sync
```
[Start] → [List Files] → [Compress Files] → [Upload to Cloud] → [Verify Upload] → [End]
```

### 3. Security Audit
```
[Start] → [Scan Vulnerabilities] → [Check Compliance] → [Generate Report] → [Email Results] → [End]
```

### 4. Database Maintenance
```
[Start] → [Connect to DB] → [Run Cleanup Query] → [Backup Database] → [Verify Backup] → [End]
```

### 5. Windows Service Management
```
[Start] → [Check Service Status] → [If Service Down] → [Start Service] → [Verify Started] → [End]
```

---

## 🔧 Advanced Features

### Conditional Logic
Use the "If Condition" node to create branching workflows:
```
[Start] → [Check Disk Space] → [If > 90%] → [Send Alert] → [End]
                              ↓
                           [If < 90%] → [Continue Normal] → [End]
```

### Loops and Iterations
Use loop nodes to repeat operations:
```
[Start] → [For Each File] → [Process File] → [Next File] → [End]
```

### Variable Passing
Nodes automatically pass data to subsequent nodes:
- File content from "Read File" → available in next nodes
- System info from "Get System Info" → available for email templates
- Query results from "Database Query" → available for processing

### Error Handling
Configure error handling for each node:
- **Continue on Error**: Keep going if this step fails
- **Retry Count**: Number of retry attempts
- **Timeout**: Maximum execution time

---

## 🎨 Tips and Best Practices

### 1. Start Simple
- Begin with basic workflows
- Add complexity gradually
- Test each step individually

### 2. Use Descriptive Names
- Name your jobs clearly
- Use descriptive node names
- Add comments in descriptions

### 3. Organize with Groups
- Group related targets together
- Use tags for organization
- Create environment-specific groups

### 4. Test Before Production
- Test jobs on development targets first
- Use the validation feature
- Check logs for any issues

### 5. Monitor Execution
- Watch job execution in real-time
- Check the execution history
- Review logs for troubleshooting

---

## 🆘 Troubleshooting

### Common Issues

#### Job Won't Execute
1. Check target connectivity
2. Verify credentials are correct
3. Ensure target is online
4. Check job validation errors

#### Node Configuration Errors
1. Review required parameters
2. Check data types (string, number, boolean)
3. Verify file paths exist
4. Test connections (database, email, etc.)

#### Performance Issues
1. Reduce parallel execution
2. Add delays between operations
3. Optimize database queries
4. Check network connectivity

### Getting Help
1. **Check Logs**: View detailed execution logs
2. **Validation**: Use the job validation feature
3. **Step Library Docs**: Reference step documentation
4. **Test Individual Steps**: Test steps in isolation

---

## 🎉 What's Next?

### Explore More Features
1. **Custom Step Libraries**: Create your own step libraries
2. **Advanced Scheduling**: Set up complex schedules
3. **Notifications**: Configure alerts and notifications
4. **API Integration**: Use the REST API for automation

### Join the Community
- Share your workflows
- Contribute to step libraries
- Report bugs and suggest features
- Help other users

---

## 📞 Support

### Documentation
- **Full Documentation**: [ENHANCED_FEATURES.md](./ENHANCED_FEATURES.md)
- **API Reference**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Step Library Guide**: [STEP_LIBRARY_GUIDE.md](./STEP_LIBRARY_GUIDE.md)

### Testing
```bash
# Run comprehensive tests
./test-enhanced-system.sh

# Check system status
./system-status.sh
```

### Need Help?
- Check the documentation
- Review example workflows
- Test with simple jobs first
- Use the validation features

---

## 🚀 Ready to Go!

You're now ready to use the enhanced OpsConductor system! Start by creating simple visual jobs and gradually explore the advanced features. The system is designed to be intuitive and powerful, making complex automation tasks simple and visual.

**Happy Automating!** 🎉