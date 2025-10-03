# Phase 2: API & Service Layer - Kickoff Document

**Date**: 2025-10-03  
**Status**: 🚧 **STARTING PHASE 2**

---

## 📋 Phase 1 Recap

✅ **Phase 1 COMPLETE** - All deliverables met:
- Database schema created and applied
- ToolCatalogService implemented with CRUD operations
- Migration script tested (2 tools imported successfully)
- Validation script working
- Integration tests passing (8/8)
- Consistency audit completed and all fixes applied
- Documentation complete

**Key Achievement**: We have a solid, tested foundation for managing 200+ tools in PostgreSQL.

---

## 🎯 Phase 2 Goals

**Primary Goal**: Integrate ToolCatalogService with HybridOrchestrator and build REST API for tool management.

**Why This Matters**:
- Currently, HybridOrchestrator loads tools from YAML files via ProfileLoader
- We need to switch to database-backed tool loading for dynamic updates
- REST API enables external tool management without code changes
- Hot reload enables zero-downtime tool updates

---

## 📊 Phase 2 Task Breakdown

### **Task 2.1: Update HybridOrchestrator Integration** ⭐ **HIGH PRIORITY**

**Goal**: Replace YAML-based ProfileLoader with database-backed ToolCatalogService

**Current State**:
```python
# ProfileLoader currently loads from YAML
class ProfileLoader:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "tool_optimization_profiles.yaml"
        self.config_path = Path(config_path)
        self._profiles: Optional[OptimizationProfilesConfig] = None
```

**Target State**:
```python
# ProfileLoader should load from database
class ProfileLoader:
    def __init__(self, use_database: bool = True, config_path: Optional[Path] = None):
        self.use_database = use_database
        if use_database:
            self.catalog_service = ToolCatalogService()
        else:
            self.config_path = Path(config_path) if config_path else self._default_yaml_path()
        self._profiles: Optional[OptimizationProfilesConfig] = None
```

**Files to Modify**:
1. `/pipeline/stages/stage_b/profile_loader.py` (211 lines)
   - Add `use_database` flag
   - Add ToolCatalogService integration
   - Keep YAML fallback
   - Add caching layer

2. `/pipeline/stages/stage_b/candidate_enumerator.py` (341 lines)
   - No changes needed (uses ProfileLoader interface)
   - Verify it works with database-backed ProfileLoader

3. `/pipeline/stages/stage_b/hybrid_orchestrator.py` (408 lines)
   - Update initialization to use database mode by default
   - Add configuration option

**Data Mapping Challenge**:
- **Database Schema**: Stores tools with capabilities and patterns (nested structure)
- **ProfileLoader Schema**: Expects `OptimizationProfilesConfig` (Pydantic model)
- **Solution**: Transform database results into `OptimizationProfilesConfig` format

**Acceptance Criteria**:
- [ ] ProfileLoader can load from database
- [ ] ProfileLoader maintains YAML fallback
- [ ] CandidateEnumerator works with both modes
- [ ] HybridOrchestrator selects tools from database
- [ ] Performance: < 5ms for tool enumeration
- [ ] All existing tests pass
- [ ] New integration test for database mode

**Estimated Time**: 4-6 hours

---

### **Task 2.2: Create REST API** ⭐ **MEDIUM PRIORITY**

**Goal**: Build REST API for tool management

**Files to Create**:
1. `/api/tool_catalog_api.py` - Main API implementation
2. `/api/schemas/tool_schemas.py` - Pydantic schemas
3. `/tests/test_tool_catalog_api.py` - API tests

**Technology Stack**:
- FastAPI (async, OpenAPI docs, Pydantic validation)
- Uvicorn (ASGI server)
- Pytest (testing)

**Endpoints** (Priority Order):
1. `GET /api/v1/tools` - List all tools
2. `GET /api/v1/tools/{name}` - Get tool by name
3. `POST /api/v1/tools` - Create new tool
4. `PUT /api/v1/tools/{name}` - Update tool
5. `DELETE /api/v1/tools/{name}` - Delete tool
6. `GET /api/v1/capabilities` - List capabilities
7. `GET /api/v1/capabilities/{name}/tools` - Get tools by capability

**Acceptance Criteria**:
- [ ] All endpoints implemented
- [ ] OpenAPI/Swagger documentation auto-generated
- [ ] Request validation with Pydantic
- [ ] Error handling and proper status codes
- [ ] API tests with 90%+ coverage
- [ ] Performance: < 100ms p95 response time

**Estimated Time**: 6-8 hours

---

### **Task 2.3: Implement Hot Reload** ⭐ **LOW PRIORITY**

**Goal**: Enable zero-downtime tool updates

**Implementation**:
1. Add cache invalidation to ToolCatalogService
2. Add event notification on tool updates
3. Update ProfileLoader to listen for cache invalidation events

**Acceptance Criteria**:
- [ ] Tool updates propagate within 1 second
- [ ] No service restart required
- [ ] Cache invalidation works correctly
- [ ] Integration test for hot reload

**Estimated Time**: 3-4 hours

---

### **Task 2.4: Tool Generator CLI** ⭐ **MEDIUM PRIORITY**

**Goal**: Interactive CLI wizard for creating new tools

**Files to Create**:
1. `/scripts/generate_tool_definition.py` - Interactive wizard
2. `/scripts/templates/tool_template.yaml` - Tool template

**Features**:
- Interactive prompts for all required fields
- Template selection (Linux, Windows, Network, etc.)
- Expression validation (time_estimate_ms, cost_estimate)
- Direct database import option
- YAML export option

**Example Flow**:
```bash
$ python scripts/generate_tool_definition.py

🛠️  Tool Catalog Generator
==========================

1. Tool Name: systemctl
2. Version: 1.0
3. Platform: 
   [1] Linux
   [2] Windows
   [3] Network
   [4] Scheduler
   [5] Custom
   Select: 1

4. Category:
   [1] System
   [2] Network
   [3] Automation
   [4] Monitoring
   [5] Security
   Select: 1

5. Description: Manage systemd services
...

✅ Tool definition created!
   
What would you like to do?
[1] Import to database
[2] Export to YAML
[3] Both
Select: 3

✅ Imported to database: systemctl v1.0
✅ Exported to: pipeline/config/tools/linux/systemctl.yaml
```

**Acceptance Criteria**:
- [ ] Wizard guides user through tool creation
- [ ] Validates all inputs
- [ ] Generates valid tool definition
- [ ] Can import directly to database
- [ ] Can export to YAML file
- [ ] User-friendly error messages

**Estimated Time**: 4-5 hours

---

## 📅 Phase 2 Timeline

**Total Estimated Time**: 17-23 hours (2-3 days)

**Recommended Order**:
1. **Day 1**: Task 2.1 (HybridOrchestrator Integration) - 4-6 hours
2. **Day 2**: Task 2.2 (REST API) - 6-8 hours
3. **Day 3**: Task 2.4 (Tool Generator CLI) - 4-5 hours
4. **Day 3**: Task 2.3 (Hot Reload) - 3-4 hours

---

## 🎯 Phase 2 Success Criteria

At the end of Phase 2, we should have:

✅ **HybridOrchestrator Integration**:
- HybridOrchestrator loads tools from database
- YAML fallback still works
- Performance: < 5ms tool enumeration
- All existing tests pass

✅ **REST API**:
- All core endpoints working
- OpenAPI documentation available
- API tests passing
- Performance: < 100ms p95

✅ **Hot Reload**:
- Tool updates propagate without restart
- Cache invalidation working
- Integration test passing

✅ **Tool Generator**:
- Interactive CLI working
- Can create and import tools
- Validation working

✅ **Documentation**:
- API documentation complete
- Integration guide updated
- Phase 2 status document created

---

## 🚀 Getting Started

### **Step 1: Review Current Code**

Understand how ProfileLoader and CandidateEnumerator currently work:

```bash
# View ProfileLoader
cat pipeline/stages/stage_b/profile_loader.py

# View CandidateEnumerator
cat pipeline/stages/stage_b/candidate_enumerator.py

# View HybridOrchestrator
cat pipeline/stages/stage_b/hybrid_orchestrator.py
```

### **Step 2: Review ToolCatalogService**

Understand the database service interface:

```bash
# View ToolCatalogService
cat pipeline/services/tool_catalog_service.py

# Key methods:
# - get_all_tools()
# - get_tool_by_name(name)
# - get_tools_by_capability(capability, platform)
```

### **Step 3: Plan Data Transformation**

The key challenge is transforming database results into `OptimizationProfilesConfig` format:

**Database Format** (from ToolCatalogService):
```python
{
    "tool_name": "grep",
    "version": "1.0",
    "platform": "linux",
    "capabilities": [
        {
            "capability_name": "text_search",
            "patterns": [
                {
                    "pattern_name": "search_files",
                    "time_estimate_ms": "100 + 10 * N",
                    "cost_estimate": "0",
                    "complexity_score": 0.3,
                    "preference_match": {"speed": 0.9, "accuracy": 1.0, ...},
                    ...
                }
            ]
        }
    ]
}
```

**ProfileLoader Format** (OptimizationProfilesConfig):
```python
{
    "tools": {
        "grep": {
            "defaults": {...},
            "capabilities": {
                "text_search": {
                    "patterns": {
                        "search_files": {
                            "time_estimate_ms": "100 + 10 * N",
                            "cost_estimate": "0",
                            ...
                        }
                    }
                }
            }
        }
    }
}
```

### **Step 4: Start with Task 2.1**

Begin implementing database integration in ProfileLoader.

---

## 📝 Notes

- **Backward Compatibility**: YAML mode must continue to work
- **Performance**: Database queries should be cached
- **Testing**: All existing tests must pass
- **Documentation**: Update as we go

---

## ❓ Questions Before Starting

1. **Should we make database mode the default?**
   - Yes: `use_database=True` by default
   - No: Keep YAML as default, opt-in to database

2. **How should we handle missing tools in database?**
   - Fallback to YAML automatically
   - Raise error and require explicit fallback
   - Log warning and continue

3. **Should ProfileLoader cache database results?**
   - Yes: Cache for 5 minutes (same as ToolCatalogService)
   - No: Always query fresh data
   - Configurable cache TTL

**Recommended Answers**:
1. Yes - database mode by default (that's the goal)
2. Log warning and fallback to YAML if available
3. Yes - cache for 5 minutes (performance)

---

## 🎊 Let's Begin Phase 2!

Ready to start with **Task 2.1: Update HybridOrchestrator Integration**?

This is the most critical task - once this is done, the system will be fully database-backed!