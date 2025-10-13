# PR #1: Hygiene - Package Init + Import Fixes

**Branch**: `zenc/hygiene-imports-init`  
**Base**: `stabilize/automation-service-v3`  
**Type**: Hygiene / Technical Debt  
**Risk**: LOW

## Summary

This PR fixes Python package structure and import issues in the automation-service to enable proper test collection and eliminate `ModuleNotFoundError` issues.

### Changes Made

1. **Added missing `__init__.py` files**:
   - `automation-service/__init__.py` - Package root with version
   - `automation-service/shared/__init__.py` - Shared utilities package
   - `automation-service/tests/__init__.py` - Test suite package
   - `automation-service/shared/tests/__init__.py` - Shared tests package

2. **Fixed imports in `main_clean.py`**:
   - Replaced `sys.path.append('/app/shared')` with `from shared.base_service import BaseService`
   - Replaced `sys.path.append('/app/libraries')` with direct package imports
   - Removed hardcoded path manipulation

3. **Fixed imports in `shared/tests/test_credential_utils.py`**:
   - Replaced `sys.path.append(...)` with `from shared.credential_utils import CredentialManager`

4. **Updated `pytest.ini`**:
   - Added `pythonpath = .` to ensure package root is in path
   - Added `addopts = --import-mode=importlib` for proper import handling

## Evidence

### Before
```bash
$ pytest --collect-only automation-service/tests/selector -k "not e2e"
collected 0 items
```

### After
```bash
$ export PYTHONPATH=$PWD/automation-service
$ pytest -q automation-service/tests/ -k "not e2e"
..                                                                       [100%]
2 passed in 0.07s
```

### Test Collection Output
```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/opsconductor/opsconductor-ng/automation-service
configfile: pytest.ini
plugins: anyio-4.11.0, asyncio-1.2.0
asyncio: mode=auto
collected 2 items

<Package automation-service>
  <Package tests>
    <Module test_selector_bridge.py>
      <Coroutine test_dedupe_and_cap>
      <Coroutine test_json_log_line>

========================== 2 tests collected in 0.03s ==========================
```

## How I Verified

```bash
# 1. Test collection works
cd /home/opsconductor/opsconductor-ng/automation-service
python3 -m pytest --collect-only tests/

# 2. Tests pass
python3 -m pytest tests/ -v

# 3. No import errors
python3 -c "from shared.base_service import BaseService; print('OK')"
```

## Risk Assessment

**Risk Level**: LOW

- Changes are purely structural (package initialization)
- No logic changes
- All existing tests pass
- Import paths are more explicit and maintainable

## Rollback Plan

If issues arise:
```bash
git revert <commit-hash>
```

The changes are isolated to import structure and can be safely reverted.

## Environment Variables

No environment variables added or changed.

## Dependencies

No new dependencies added.

## Next Steps

After this PR is merged:
1. PR #2: Metrics consolidation & port exposure
2. PR #3: E2E Walking Skeleton (Echo tool)
3. PR #4: Tracing & metrics for execution path
4. PR #5: Runbooks, tests, CI guards

## Checklist

- [x] All tests pass
- [x] No new dependencies
- [x] No environment variable changes
- [x] Import structure improved
- [x] pytest collection works correctly
- [x] Documentation updated (this PR doc)