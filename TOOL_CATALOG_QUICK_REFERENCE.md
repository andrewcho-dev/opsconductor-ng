# Tool Catalog System - Quick Reference Guide

**Version**: 1.0  
**Last Updated**: October 3, 2025

---

## 🚀 Quick Start

### Create a Tool (Template-Based - Fastest)

```bash
# Inside container
docker exec opsconductor-ai-pipeline python3 /app/scripts/tool_from_template.py \
  simple_command my_tool --author "Your Name"

# Available templates: simple_command, api_tool, database_tool, monitoring_tool, automation_tool
```

### Create a Tool (Interactive)

```bash
docker exec -it opsconductor-ai-pipeline python3 /app/scripts/tool_generator.py
# Follow the wizard prompts
```

### Create a Tool (API)

```bash
curl -X POST http://localhost:3005/api/v1/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "my_tool",
    "version": "1.0",
    "description": "My custom tool",
    "platform": "linux",
    "category": "system",
    "defaults": {
      "accuracy_level": "high",
      "freshness": "cached",
      "data_source": "direct"
    }
  }'
```

---

## 📚 API Reference

### Base URL
- **External**: `http://localhost:3005/api/v1/tools`
- **Internal (container)**: `http://localhost:8000/api/v1/tools`

### Tool Operations

#### List All Tools
```bash
GET /api/v1/tools
GET /api/v1/tools?platform=linux
GET /api/v1/tools?category=system
GET /api/v1/tools?enabled=true
```

#### Get Tool Details
```bash
GET /api/v1/tools/{tool_name}
GET /api/v1/tools/{tool_name}?version=1.0
```

#### Create Tool
```bash
POST /api/v1/tools
Content-Type: application/json

{
  "tool_name": "string",
  "version": "string",
  "description": "string",
  "platform": "linux|windows|network|scheduler|custom",
  "category": "system|network|automation|monitoring|security|database|cloud",
  "defaults": {
    "accuracy_level": "real-time|high|medium|low",
    "freshness": "live|cached|historical",
    "data_source": "direct|api|database|cache"
  },
  "dependencies": [...],
  "metadata": {...}
}
```

#### Update Tool
```bash
PUT /api/v1/tools/{tool_name}
Content-Type: application/json

{
  "description": "Updated description",
  "defaults": {...},
  ...
}
```

#### Delete Tool
```bash
DELETE /api/v1/tools/{tool_name}
DELETE /api/v1/tools/{tool_name}?version=1.0
```

#### Enable/Disable Tool
```bash
PATCH /api/v1/tools/{tool_name}/enable
Content-Type: application/json

{
  "enabled": true
}
```

### Capability Operations

#### Add Capability
```bash
POST /api/v1/tools/{tool_name}/capabilities
Content-Type: application/json

{
  "capability_name": "string",
  "description": "string"
}
```

#### List Capabilities
```bash
GET /api/v1/tools/{tool_name}/capabilities
```

#### Delete Capability
```bash
DELETE /api/v1/tools/{tool_name}/capabilities/{capability_id}
```

### Pattern Operations

#### Add Pattern
```bash
POST /api/v1/tools/{tool_name}/capabilities/{capability_id}/patterns
Content-Type: application/json

{
  "pattern_name": "string",
  "description": "string",
  "typical_use_cases": ["string"],
  "time_estimate_ms": "1000",
  "cost_estimate": "5",
  "complexity_score": 0.5,
  "scope": "single|multiple|aggregate",
  "completeness": "full|partial|summary",
  "limitations": ["string"],
  "policy": {
    "max_cost": 10,
    "requires_approval": false,
    "production_safe": true
  },
  "preference_match": {
    "speed": 0.8,
    "accuracy": 0.9,
    "cost": 0.7,
    "complexity": 0.6,
    "completeness": 0.9
  },
  "required_inputs": [...],
  "expected_outputs": [...]
}
```

#### List Patterns
```bash
GET /api/v1/tools/{tool_name}/capabilities/{capability_id}/patterns
```

#### Delete Pattern
```bash
DELETE /api/v1/tools/{tool_name}/capabilities/{capability_id}/patterns/{pattern_id}
```

### Bulk Operations

#### Bulk Import
```bash
POST /api/v1/tools/bulk-import
Content-Type: application/json

{
  "tools": [
    {
      "tool_name": "tool1",
      "version": "1.0",
      ...
    },
    {
      "tool_name": "tool2",
      "version": "1.0",
      ...
    }
  ]
}
```

#### Export All Tools
```bash
GET /api/v1/tools/export
```

### Hot Reload Operations

#### Manual Reload
```bash
POST /api/v1/tools/reload
Content-Type: application/json

{
  "tool_name": "grep",  # Optional: null for all tools
  "triggered_by": "admin"  # Optional
}
```

#### Reload History
```bash
GET /api/v1/tools/reload/history
GET /api/v1/tools/reload/history?limit=10
GET /api/v1/tools/reload/history?trigger_type=api_update
```

#### Reload Statistics
```bash
GET /api/v1/tools/reload/statistics
```

---

## 🛠️ CLI Tools

### Template-Based Generator

```bash
python tool_from_template.py <template> <tool_name> [options]

Templates:
  simple_command   - Simple command-line tool
  api_tool         - REST API integration tool
  database_tool    - Database query tool
  monitoring_tool  - System monitoring tool
  automation_tool  - Automation/orchestration tool

Options:
  --version VERSION    Tool version (default: 1.0)
  --author AUTHOR      Tool author
  --no-db              Do not save to database
  --yaml               Also save to YAML file

Examples:
  # Create simple command tool
  python tool_from_template.py simple_command ls --author "John Doe"
  
  # Create API tool and save to YAML
  python tool_from_template.py api_tool github_api --yaml
  
  # Create database tool with custom version
  python tool_from_template.py database_tool mysql_query --version 2.0
```

### Interactive Generator

```bash
python tool_generator.py

# Follow the 7-step wizard:
# 1. Basic Information
# 2. Defaults
# 3. Dependencies
# 4. Capabilities & Patterns
# 5. Metadata
# 6. Review
# 7. Save
```

---

## 🔍 Common Tasks

### Check if Tool Exists
```bash
curl -s http://localhost:3005/api/v1/tools/grep | jq '.tool_name'
```

### List All Linux Tools
```bash
curl -s http://localhost:3005/api/v1/tools?platform=linux | jq '.[].tool_name'
```

### Get Tool with All Capabilities
```bash
curl -s http://localhost:3005/api/v1/tools/grep | jq '.'
```

### Update Tool Description
```bash
curl -X PUT http://localhost:3005/api/v1/tools/grep \
  -H "Content-Type: application/json" \
  -d '{"description":"Updated description"}'
```

### Disable Tool
```bash
curl -X PATCH http://localhost:3005/api/v1/tools/grep/enable \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

### Trigger Manual Reload
```bash
curl -X POST http://localhost:3005/api/v1/tools/reload \
  -H "Content-Type: application/json" \
  -d '{"triggered_by":"admin"}'
```

### Check Reload Statistics
```bash
curl -s http://localhost:3005/api/v1/tools/reload/statistics | jq '.'
```

### Export All Tools to File
```bash
curl -s http://localhost:3005/api/v1/tools/export > tools_backup.json
```

### Import Tools from File
```bash
curl -X POST http://localhost:3005/api/v1/tools/bulk-import \
  -H "Content-Type: application/json" \
  -d @tools_backup.json
```

---

## 🐛 Troubleshooting

### Tool Not Found After Creation
```bash
# Check if tool exists
curl -s http://localhost:3005/api/v1/tools/my_tool

# Trigger manual reload
curl -X POST http://localhost:3005/api/v1/tools/reload

# Check reload history
curl -s http://localhost:3005/api/v1/tools/reload/history | jq '.'
```

### Cache Issues
```bash
# Invalidate cache by triggering reload
curl -X POST http://localhost:3005/api/v1/tools/reload \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"my_tool"}'
```

### Database Connection Issues
```bash
# Check if database is accessible
docker exec opsconductor-ai-pipeline psql -h postgres -U opsconductor -d opsconductor -c "SELECT COUNT(*) FROM tools;"
```

### API Not Responding
```bash
# Check container status
docker ps | grep opsconductor-ai-pipeline

# Check container logs
docker logs opsconductor-ai-pipeline --tail 50

# Restart container
docker restart opsconductor-ai-pipeline
```

---

## 📊 Performance Tips

### 1. Use Caching
- Tools are cached for 5 minutes by default
- Cache is automatically invalidated on updates
- Manual reload available if needed

### 2. Batch Operations
- Use bulk import for multiple tools
- Export/import for backups and migrations

### 3. Filter Queries
- Use query parameters to filter results
- Reduces response size and improves performance

### 4. Monitor Reload Statistics
- Check success rate regularly
- Monitor average reload duration
- Review failed reloads in history

---

## 🔐 Security Notes

### Authentication
- Currently no authentication required (development mode)
- Production deployment should add authentication
- Consider API keys or OAuth2

### Authorization
- All endpoints are currently public
- Add role-based access control for production
- Restrict admin endpoints (reload, bulk operations)

### Input Validation
- All inputs are validated
- SQL injection protection via parameterized queries
- JSON schema validation on API requests

---

## 📈 Monitoring

### Key Metrics to Track

1. **Tool Usage**
   - Most frequently used tools
   - Tool load times
   - Cache hit/miss ratio

2. **Reload Performance**
   - Reload frequency
   - Reload duration
   - Success/failure rate

3. **API Performance**
   - Request latency
   - Throughput (requests/second)
   - Error rate

4. **Database Performance**
   - Query execution time
   - Connection pool usage
   - Cache effectiveness

### Monitoring Endpoints

```bash
# Reload statistics
curl http://localhost:3005/api/v1/tools/reload/statistics

# Reload history
curl http://localhost:3005/api/v1/tools/reload/history?limit=100

# Tool count
curl -s http://localhost:3005/api/v1/tools | jq 'length'
```

---

## 🔗 Related Documentation

- **Phase 1 Complete**: `/TOOL_CATALOG_PHASE1_COMPLETE.md`
- **Phase 2 Complete**: `/TOOL_CATALOG_PHASE2_COMPLETE.md`
- **Hot Reload Details**: `/TOOL_CATALOG_PHASE2_TASK3_COMPLETE.md`
- **Database Schema**: `/database/init-schema.sql`
- **API Implementation**: `/api/tool_catalog_api.py`
- **ProfileLoader**: `/pipeline/stages/stage_b/profile_loader.py`

---

## 💡 Tips & Best Practices

### Tool Naming
- Use lowercase with underscores: `my_tool`
- Be descriptive but concise
- Avoid special characters

### Versioning
- Use semantic versioning: `1.0`, `1.1`, `2.0`
- Increment version on breaking changes
- Keep old versions for compatibility

### Descriptions
- Be clear and concise
- Include key features
- Mention limitations

### Dependencies
- List all required dependencies
- Mark critical dependencies as required
- Include version constraints if needed

### Patterns
- Create patterns for common use cases
- Provide realistic time/cost estimates
- Set appropriate complexity scores
- Define clear input/output schemas

### Metadata
- Add tags for searchability
- Include author information
- Link to documentation
- Note any special requirements

---

## 🎯 Quick Command Reference

```bash
# Create tool from template
docker exec opsconductor-ai-pipeline python3 /app/scripts/tool_from_template.py simple_command my_tool

# List all tools
curl http://localhost:3005/api/v1/tools

# Get tool details
curl http://localhost:3005/api/v1/tools/my_tool

# Update tool
curl -X PUT http://localhost:3005/api/v1/tools/my_tool -H "Content-Type: application/json" -d '{"description":"Updated"}'

# Delete tool
curl -X DELETE http://localhost:3005/api/v1/tools/my_tool

# Reload cache
curl -X POST http://localhost:3005/api/v1/tools/reload

# Check statistics
curl http://localhost:3005/api/v1/tools/reload/statistics

# Export all tools
curl http://localhost:3005/api/v1/tools/export > backup.json

# Import tools
curl -X POST http://localhost:3005/api/v1/tools/bulk-import -H "Content-Type: application/json" -d @backup.json
```

---

**Need Help?** Check the full documentation in `/TOOL_CATALOG_PHASE2_COMPLETE.md`