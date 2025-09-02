# OpsConductor Starter Libraries

This directory contains the starter pack of step libraries for OpsConductor, providing essential automation capabilities out of the box.

## 📦 Included Libraries

### 1. Windows Core Operations (`windows-core-v1.0.0.zip`)
Essential Windows system operations including:
- **Run PowerShell Command**: Execute PowerShell scripts and commands
- **Copy File/Folder**: File system operations with recursive support
- **Control Windows Service**: Start, stop, restart, and monitor services
- **Read Registry Value**: Access Windows Registry data
- **Control Process**: Manage Windows processes and applications

### 2. Network Tools (`network-tools-v1.0.0.zip`)
Network connectivity and monitoring tools:
- **Ping Host**: Test network connectivity with detailed statistics
- **Port Check**: Verify if network ports are open and accessible
- **DNS Lookup**: Resolve domain names and IP addresses
- **Network Scan**: Discover devices and services on network ranges
- **Bandwidth Test**: Measure network performance and throughput

### 3. Automation Basics (`automation-basics-v1.0.0.zip`)
Essential automation building blocks:
- **Delay**: Pause execution with configurable timing
- **Condition Check**: Evaluate conditions for branching logic
- **Set Variable**: Store and manipulate data between steps
- **Loop Control**: Create repeating operations (for, while, foreach)
- **Text Manipulation**: String processing and transformation
- **Log Message**: Structured logging with different severity levels

### 4. Web & HTTP Tools (`web-http-v1.0.0.zip`)
Web services and HTTP operations:
- **HTTP Request**: Make REST API calls and web requests
- **Download File**: Fetch files from web URLs with validation
- **JSON Parse**: Extract data from JSON responses using JSONPath
- **XML Parse**: Process XML documents with XPath queries
- **Web Scrape**: Extract data from web pages using CSS selectors
- **API Test**: Comprehensive API testing with assertions

## 🚀 Installation

### Automatic Installation
Run the installer script to install all starter libraries:

```bash
cd /home/opsconductor/microservice-system
python3 install-starter-libraries.py
```

### Manual Installation
1. Open OpsConductor web interface: http://localhost
2. Navigate to **Step Libraries** section
3. Click **Install Library**
4. Upload the desired `.zip` file from this directory
5. Follow the installation prompts

## 📋 Available Steps Summary

After installation, you'll have access to **22 automation steps** across 4 categories:

| Category | Steps | Description |
|----------|-------|-------------|
| **System** | 6 steps | Windows operations, services, processes |
| **Network** | 5 steps | Connectivity testing, monitoring |
| **Automation** | 6 steps | Control flow, variables, conditions |
| **Web/HTTP** | 6 steps | API calls, web scraping, data parsing |

## 🔧 Usage Examples

### Basic Windows Automation
```
1. Run PowerShell Command → Get system information
2. Condition Check → Verify system meets requirements
3. Control Windows Service → Restart required services
4. Log Message → Record completion status
```

### Network Monitoring Workflow
```
1. Ping Host → Test connectivity to critical servers
2. Port Check → Verify service availability
3. Set Variable → Store results for reporting
4. HTTP Request → Send status to monitoring API
```

### Web Data Processing
```
1. HTTP Request → Fetch data from API
2. JSON Parse → Extract required fields
3. Text Manipulation → Format data
4. Log Message → Record processing results
```

## 🛠️ Development

### Library Structure
Each library contains:
- `manifest.json`: Library metadata and step definitions
- `steps.py`: Python implementation of step functions

### Adding Custom Steps
1. Modify the appropriate `steps.py` file
2. Update `manifest.json` with new step definitions
3. Recreate the ZIP package
4. Reinstall the library

### Creating New Libraries
Use the existing libraries as templates:
1. Create new directory with `manifest.json` and `steps.py`
2. Follow the established patterns for step implementations
3. Package as ZIP file for distribution

## 📊 Installation Status

To check installed libraries:
```bash
curl http://localhost:3011/api/v1/libraries
```

To view available steps:
```bash
curl http://localhost:3011/api/v1/steps
```

## 🔍 Troubleshooting

### Common Issues

**Libraries not appearing in UI:**
- Verify step-libraries service is running: `docker ps | grep step`
- Check service logs: `docker logs opsconductor-step-libraries`
- Restart services: `./restart-services.sh`

**Installation failures:**
- Ensure ZIP files are properly formatted
- Check manifest.json syntax
- Verify Python step implementations

**Step execution errors:**
- Review step parameters and requirements
- Check target system compatibility
- Examine job execution logs

### Service Health Check
```bash
curl http://localhost:3011/health
```

## 📝 Version History

- **v1.0.0**: Initial release with 4 core libraries and 22 automation steps
- Comprehensive Windows, Network, Automation, and Web capabilities
- Production-ready implementations with error handling
- Full parameter validation and documentation

## 🤝 Contributing

To contribute new steps or libraries:
1. Follow the established code patterns
2. Include comprehensive error handling
3. Add parameter validation
4. Provide usage examples
5. Update documentation

---

**Next Steps:**
1. Install the starter libraries using the provided installer
2. Explore the Visual Job Builder to create your first automation workflows
3. Review the step documentation and examples
4. Start building powerful automation solutions with OpsConductor!