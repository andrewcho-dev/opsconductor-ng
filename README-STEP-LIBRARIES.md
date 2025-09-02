# OpsConductor Step Libraries System

A comprehensive, modular step library system that enables dynamic loading, installation, and management of workflow steps in OpsConductor.

## 🌟 Features

### Core Capabilities
- **Dynamic Step Loading**: Steps are loaded dynamically from installed libraries
- **Modular Architecture**: Each library is a self-contained package
- **Hot-Swappable**: Install/uninstall libraries without system restart
- **Premium Support**: Built-in licensing system for commercial libraries
- **Performance Optimized**: Efficient caching and lazy loading
- **Multi-Platform**: Support for Windows, Linux, and macOS steps

### Library Management
- **Web-Based Interface**: Manage libraries through the frontend UI
- **RESTful API**: Programmatic library management
- **Dependency Resolution**: Automatic handling of library dependencies
- **Version Control**: Support for multiple library versions
- **Health Monitoring**: Automatic library health checks
- **Usage Analytics**: Track step usage and performance

### Security & Licensing
- **License Validation**: Support for premium library licensing
- **Permission System**: Fine-grained permission controls
- **Secure Installation**: Validation and sandboxing of library code
- **Audit Trail**: Complete audit log of library operations

## 🏗️ Architecture

### Components

1. **Step Libraries Service** (`step-libraries-service/`)
   - Port: 3011
   - Manages library installation, validation, and metadata
   - Provides REST API for library operations
   - Handles licensing and premium features

2. **Frontend Integration** (`frontend/src/services/stepLibraryService.ts`)
   - Dynamic step loading in Visual Job Builder
   - Library management interface
   - Real-time step availability updates

3. **Database Schema** (`database/step-libraries-schema.sql`)
   - Library metadata and step definitions
   - Usage analytics and performance metrics
   - License management and validation

### Data Flow

```
Library Package (ZIP) → Upload → Validation → Installation → Database → Frontend
                                     ↓
                              Health Checks ← Usage Analytics ← Step Execution
```

## 🚀 Quick Start

### 1. Start the System

```bash
# Start OpsConductor with step libraries support
./start-with-step-libraries.sh
```

### 2. Access the Frontend

Open http://localhost in your browser and navigate to the Visual Job Builder.

### 3. Manage Libraries

1. Click the "Manage" button in the Step Library panel
2. Upload a library ZIP file
3. Configure licensing if needed (for premium libraries)
4. The new steps will be immediately available

### 4. Use Dynamic Steps

- Steps are automatically loaded from installed libraries
- Filter by category, library, or search terms
- Drag and drop steps into your workflow
- Configure step parameters dynamically

## 📦 Library Development

### Creating a Library

1. **Create the structure**:
```
my-library/
├── manifest.json
├── steps/
│   └── my_step.json
├── executors/
│   └── my_step.py
└── docs/
    └── README.md
```

2. **Define the manifest**:
```json
{
  "name": "my-library",
  "version": "1.0.0",
  "display_name": "My Custom Library",
  "description": "Custom steps for my organization",
  "author": "Your Name",
  "is_premium": false,
  "steps": [
    {
      "file": "steps/my_step.json",
      "executor": "executors/my_step.py"
    }
  ]
}
```

3. **Define steps**:
```json
{
  "name": "my.custom.step",
  "display_name": "My Custom Step",
  "category": "custom",
  "description": "Does something custom",
  "icon": "⚡",
  "color": "#ff6b35",
  "inputs": 1,
  "outputs": 1,
  "parameters": {
    "param1": {
      "type": "string",
      "required": true,
      "description": "First parameter"
    }
  }
}
```

4. **Package and install**:
```bash
zip -r my-library-1.0.0.zip manifest.json steps/ executors/ docs/
```

### Example Libraries

See `examples/step-libraries/` for complete examples:

- **file-operations-basic**: Essential file operations
- **network-tools-premium**: Premium network utilities (example)
- **custom-integrations**: Custom API integrations (example)

## 🔧 API Reference

### Library Management API

#### Install Library
```http
POST /api/v1/libraries/install
Content-Type: multipart/form-data

file: library.zip
license_key: optional-license-key
```

#### List Libraries
```http
GET /api/v1/libraries?enabled_only=true
```

#### Get Library Details
```http
GET /api/v1/libraries/{library_id}
```

#### Toggle Library
```http
PUT /api/v1/libraries/{library_id}/toggle?enabled=true
```

#### Uninstall Library
```http
DELETE /api/v1/libraries/{library_id}
```

### Step Definitions API

#### Get Available Steps
```http
GET /api/v1/steps?category=file&library=core&platform=linux
```

#### Get Step Details
```http
GET /api/v1/steps/{step_id}
```

## 📊 Monitoring & Analytics

### Usage Tracking
- Step execution counts and timing
- Library usage statistics
- Performance metrics
- Error rates and patterns

### Health Monitoring
- Library status monitoring
- Dependency validation
- License expiration alerts
- Performance degradation detection

### Dashboard Metrics
- Most used libraries and steps
- Performance trends
- License utilization
- System resource usage

## 🔒 Security Considerations

### Library Validation
- Manifest schema validation
- Step definition validation
- Dependency security scanning
- Code signature verification (future)

### Permission System
- File system access controls
- Network access restrictions
- System command limitations
- Resource usage limits

### Licensing Security
- Encrypted license keys
- Server-side validation
- Usage tracking and limits
- Anti-tampering measures

## 🎯 Premium Features

### Commercial Libraries
- License key validation
- Usage-based billing
- Trial periods
- Support channels

### Enterprise Features
- Private library repositories
- Custom licensing models
- Advanced analytics
- Priority support

## 🛠️ Development

### Running in Development

```bash
# Start the step-libraries-service
cd step-libraries-service
python main.py

# Start the frontend with step library support
cd frontend
npm start
```

### Testing

```bash
# Test library installation
curl -X POST http://localhost:3011/api/v1/libraries/install \
  -F "file=@examples/step-libraries/file-operations-basic/file-operations-basic-1.0.0.zip"

# Test step retrieval
curl http://localhost:3011/api/v1/steps
```

### Database Migration

The step libraries schema is automatically applied when starting the system. For manual migration:

```sql
-- Apply step libraries schema
\i database/step-libraries-schema.sql
```

## 📈 Performance Optimization

### Caching Strategy
- In-memory step definition cache
- Redis cache for frequently accessed data
- CDN for library assets (future)

### Lazy Loading
- Steps loaded on-demand
- Library metadata cached
- Executor code loaded when needed

### Resource Management
- Memory usage monitoring
- CPU usage limits
- Disk space management
- Network bandwidth optimization

## 🔮 Future Enhancements

### Planned Features
- **Library Marketplace**: Central repository for sharing libraries
- **Visual Step Editor**: GUI for creating step definitions
- **Library Templates**: Scaffolding for new libraries
- **Advanced Analytics**: ML-powered usage insights
- **Cloud Integration**: Cloud-native library storage
- **Version Management**: Advanced versioning and rollback

### Community Features
- **Library Ratings**: User ratings and reviews
- **Community Contributions**: Open-source library contributions
- **Documentation Portal**: Centralized documentation
- **Developer Tools**: CLI tools and IDE extensions

## 📚 Documentation

- [Step Library Development Guide](docs/step-library-development.md)
- [API Documentation](docs/api-reference.md)
- [Security Guide](docs/security.md)
- [Performance Tuning](docs/performance.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Develop your library or enhancement
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: https://docs.opsconductor.com/step-libraries
- **Community Forum**: https://community.opsconductor.com
- **GitHub Issues**: https://github.com/opsconductor/opsconductor/issues
- **Email Support**: support@opsconductor.com

---

**OpsConductor Step Libraries System** - Extending automation capabilities through modular, dynamic step libraries.