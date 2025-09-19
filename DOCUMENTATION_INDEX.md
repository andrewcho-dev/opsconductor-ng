# OpsConductor NG - Documentation Index

## 📚 Complete Documentation Guide

This index provides quick access to all OpsConductor NG documentation, organized by user type and use case.

## 🚀 Quick Start (New Users)

1. **[README.md](README.md)** - Start here! Project overview, features, and one-command deployment
2. **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment instructions with troubleshooting
3. **Web Interface** - http://localhost:3100 (admin/admin123)

## 🏗️ Architecture & Development

### System Architecture
- **[REPO.md](REPO.md)** - Repository structure, service architecture, and development guidelines
- **[AI_DOCUMENTATION.md](AI_DOCUMENTATION.md)** - AI system architecture, services, and capabilities

### Development Resources
- **[VOLUME_MOUNT_SYSTEM.md](VOLUME_MOUNT_SYSTEM.md)** - Docker volume configuration and development setup
- **[docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - Coding standards and best practices

## 📖 Detailed Guides

### Installation & Setup
- **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - Detailed installation instructions for all scenarios
- **[docs/GPU_VFIO_PCI_VM_FIX.md](docs/GPU_VFIO_PCI_VM_FIX.md)** - GPU virtualization troubleshooting

### Planning & Roadmap
- **[docs/PROTOTYPE_ROADMAP.md](docs/PROTOTYPE_ROADMAP.md)** - Development roadmap and future plans

## 🎯 Documentation by User Type

### For System Administrators
1. **[README.md](README.md)** - Quick overview and deployment
2. **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Production deployment guide
3. **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - Detailed installation options

### For Developers
1. **[REPO.md](REPO.md)** - Architecture and service structure
2. **[VOLUME_MOUNT_SYSTEM.md](VOLUME_MOUNT_SYSTEM.md)** - Development environment setup
3. **[docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md](docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md)** - Coding standards
4. **[AI_DOCUMENTATION.md](AI_DOCUMENTATION.md)** - AI system internals

### For End Users
1. **[README.md](README.md)** - Feature overview and capabilities
2. **[AI_DOCUMENTATION.md](AI_DOCUMENTATION.md)** - AI features and natural language commands
3. **Web Interface Documentation** - Available at http://localhost:3100/help

### For DevOps Engineers
1. **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment and scaling
2. **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - Advanced installation options
3. **[REPO.md](REPO.md)** - Service architecture and dependencies

## 🔧 Technical Documentation

### API Documentation
- **Interactive API Docs**: http://localhost:3000/docs (API Gateway)
- **AI Service API**: http://localhost:3005/docs (AI Command Service)
- **All Service APIs**: Available at `<service-url>/docs`

### Database Documentation
- **Schema**: Defined in `database/complete-schema.sql`
- **4 Schemas**: identity, assets, automation, communication
- **23 Tables**: Complete relational structure

### Service Documentation
Each service includes:
- **README files** in service directories
- **API documentation** at `/docs` endpoints
- **Health checks** at `/health` endpoints

## 📊 Documentation Statistics

### Current Structure
- **Core Documentation**: 5 files (README, REPO, AI_DOCUMENTATION, DEPLOYMENT-GUIDE, VOLUME_MOUNT_SYSTEM)
- **Specialized Documentation**: 4 files in docs/ directory
- **Total Active Documentation**: 9 comprehensive files
- **Archived Documentation**: Historical files preserved in docs/archive/

### Quality Metrics
- ✅ **Up-to-date**: All documentation reflects current system state
- ✅ **Comprehensive**: All major components documented
- ✅ **Tested**: All examples and instructions verified
- ✅ **Accessible**: Clear navigation and organization
- ✅ **Maintainable**: Regular updates and validation

## 🔍 Finding Information

### By Topic
- **Getting Started**: README.md → DEPLOYMENT-GUIDE.md
- **Architecture**: REPO.md → AI_DOCUMENTATION.md
- **Development**: VOLUME_MOUNT_SYSTEM.md → docs/OPSCONDUCTOR_SCRIPTING_STANDARD.md
- **Installation**: docs/INSTALLATION_GUIDE.md
- **Troubleshooting**: DEPLOYMENT-GUIDE.md (Troubleshooting section)

### By File Type
- **Markdown Files**: All documentation in .md format
- **Code Examples**: Embedded in documentation with syntax highlighting
- **Configuration Files**: Referenced with full paths
- **Scripts**: Located in `/scripts/` directory with documentation

## 🔄 Documentation Maintenance

### Update Schedule
- **Weekly**: Review for accuracy
- **Monthly**: Update examples and screenshots
- **Per Release**: Version-specific updates
- **As Needed**: New features and changes

### Validation Process
1. **Link Checking**: All internal and external links verified
2. **Code Testing**: All examples tested in clean environment
3. **Accuracy Review**: Technical details verified against implementation
4. **User Testing**: Instructions tested by new users

## 📝 Contributing to Documentation

### How to Contribute
1. **Identify Gaps**: Note missing or outdated information
2. **Create Issues**: Report documentation bugs or requests
3. **Submit PRs**: Contribute improvements and additions
4. **Review Process**: All changes reviewed for accuracy and clarity

### Documentation Standards
- **Clarity**: Write for both beginners and experts
- **Completeness**: Include all necessary information
- **Examples**: Provide working, tested examples
- **Structure**: Use consistent formatting and organization
- **Testing**: Verify all instructions work

## 🆘 Getting Help

### Documentation Issues
- **GitHub Issues**: Report documentation bugs or gaps
- **GitHub Discussions**: Ask questions about documentation
- **Direct Updates**: Submit PRs for improvements

### System Support
- **Health Checks**: All services provide `/health` endpoints
- **Logs**: `docker-compose logs <service-name>`
- **Troubleshooting**: DEPLOYMENT-GUIDE.md troubleshooting section

---

## 📋 Quick Reference

### Essential Commands
```bash
# Deploy system
./deploy.sh

# Check health
./verify-setup.sh

# View logs
docker-compose logs -f

# Access web interface
open http://localhost:3100
```

### Essential URLs
- **Web Interface**: http://localhost:3100
- **API Gateway**: http://localhost:3000/docs
- **AI Service**: http://localhost:3005/docs
- **Celery Monitor**: http://localhost:5555

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **Change immediately** after first login

---

**This documentation index provides comprehensive access to all OpsConductor NG information. Start with README.md for overview, then follow the appropriate path based on your role and needs.**