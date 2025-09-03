# OpsConductor Comprehensive E2E Test Suite

This directory contains a complete end-to-end test suite for the OpsConductor application using **Playwright** with **TypeScript**.

## 🎯 Framework & Tools
- **Testing Framework**: Playwright (v1.44+)
- **Language**: TypeScript
- **Browser**: Chromium (headless by default)
- **Target Application**: http://localhost (OpsConductor microservices)

## 📁 Test Structure

### Core Test Files
1. **01-authentication.spec.ts** - Login/logout functionality, user role validation
2. **02-dashboard.spec.ts** - Dashboard components, service health monitoring, navigation
3. **03-users.spec.ts** - User management CRUD operations, role changes
4. **04-credentials.spec.ts** - Credential management interface
5. **05-targets.spec.ts** - Target management, filtering, service operations
6. **06-discovery.spec.ts** - Network discovery jobs and results
7. **07-jobs.spec.ts** - Job creation, management, execution
8. **08-schedules.spec.ts** - Job scheduling, cron expressions, scheduler control
9. **09-job-runs.spec.ts** - Job execution history and monitoring
10. **10-notifications.spec.ts** - Notification preferences and configuration
11. **11-settings.spec.ts** - System settings, SMTP configuration
12. **12-integration-workflows.spec.ts** - Cross-screen workflows and user journeys

## 🚀 Quick Start

### Prerequisites
- Node.js (v18+)
- OpsConductor system running on http://localhost

### Installation
```bash
cd /home/opsconductor/tests
npm install
npx playwright install chromium
```

### Running Tests

#### All Tests
```bash
npm test
```

#### Individual Test Suites
```bash
npm run test:auth          # Authentication tests
npm run test:dashboard     # Dashboard functionality
npm run test:users         # User management
npm run test:credentials   # Credential management
npm run test:targets       # Target management
npm run test:discovery     # Discovery functionality
npm run test:jobs          # Job management
npm run test:schedules     # Schedule management
npm run test:job-runs      # Job execution monitoring
npm run test:notifications # Notification settings
npm run test:settings      # System settings
npm run test:integration   # Cross-screen workflows
```

#### Smoke Tests
```bash
npm run test:smoke         # Quick validation of all main pages
```

#### Debug & Development
```bash
npm run test:debug         # Run with Playwright debugger
npm run test:headed        # Run with visible browser
npm run test:ui            # Run with Playwright UI mode
npm run test:report        # Generate HTML report
```

## 🧪 Test Coverage

### Authentication System
- ✅ Login page display and credentials
- ✅ Admin, Operator, Viewer role authentication
- ✅ Invalid credential rejection
- ✅ Logout functionality
- ✅ Session management

### Dashboard Functionality
- ✅ Service health monitoring and refresh
- ✅ System metrics display
- ✅ Statistics cards navigation
- ✅ Quick actions functionality
- ✅ Recent activity display
- ✅ System information validation

### User Management
- ✅ User listing and data display
- ✅ Role management dropdown
- ✅ User actions (edit, delete)
- ✅ Add user functionality
- ✅ Data validation

### Target Management
- ✅ Enhanced target interface
- ✅ Target filtering (OS type, service type)
- ✅ Target information display
- ✅ Service management per target
- ✅ Credential assignment
- ✅ CRUD operations

### Discovery Management
- ✅ Discovery job creation and management
- ✅ Tab navigation (Jobs, Targets, Create)
- ✅ Job status and results display
- ✅ Discovery history

### Job Management
- ✅ Job listing and details
- ✅ Job actions (run, edit, delete)
- ✅ Job creation workflow
- ✅ Version and status tracking

### Schedule Management
- ✅ Schedule listing and cron expressions
- ✅ Scheduler control (start/stop)
- ✅ Next execution and timing
- ✅ Schedule CRUD operations
- ✅ Status monitoring

### Job Runs Monitoring
- ✅ Execution history display
- ✅ Job filtering capabilities
- ✅ Status tracking and timing
- ✅ Run details and actions

### Notification System
- ✅ Preference configuration (email, Slack, Teams, webhook)
- ✅ Event notification settings
- ✅ Quiet hours configuration
- ✅ Tab navigation (preferences, history)
- ✅ Settings persistence

### System Settings
- ✅ SMTP configuration management
- ✅ Email server settings
- ✅ Test email functionality
- ✅ Authentication configuration
- ✅ Configuration validation

### Integration Workflows
- ✅ Complete navigation flow
- ✅ Cross-screen data consistency
- ✅ User session management
- ✅ Browser navigation (back/forward)
- ✅ End-to-end user journeys

## 📊 Test Results

### Test Execution Stats
- **Total Test Files**: 12
- **Estimated Test Cases**: 150+
- **Coverage Areas**: 11 major application modules
- **Browser Support**: Chromium (expandable to Firefox, WebKit)

### Key Test Scenarios
- **Authentication Flow**: 6 test cases
- **Dashboard Validation**: 8 test cases
- **CRUD Operations**: 40+ test cases across modules
- **Navigation Testing**: 25+ test cases
- **Form Interactions**: 50+ test cases
- **Integration Workflows**: 15+ test cases

## 🔧 Configuration

### Playwright Config (`playwright.config.ts`)
- Base URL: http://localhost
- Browser: Chromium (Desktop Chrome)
- Screenshots: On failure
- Traces: On retry
- Timeouts: Standard Playwright defaults

### Test Helpers
- Automatic login handling
- Page object patterns for complex interactions
- Consistent error handling and reporting
- Screenshot capture on failures

## 🐛 Debugging

### Common Issues
1. **Strict Mode Violations**: Multiple elements match selector
   - Solution: Use exact matches or more specific selectors
   
2. **Timing Issues**: Elements not ready
   - Solution: Proper waits and assertions
   
3. **Authentication State**: Session not maintained
   - Solution: Consistent beforeEach blocks

### Debug Commands
```bash
# Run specific test with debug
npx playwright test e2e/01-authentication.spec.ts --debug

# Generate trace
npx playwright test --trace on

# Take screenshots
npx playwright test --screenshot only-on-failure
```

## 📈 Reporting

### HTML Reports
```bash
npm run test:report
npx playwright show-report
```

### CI/CD Integration
The test suite is configured for CI/CD environments:
- Headless execution by default
- Retry configuration for flaky tests
- Parallel execution support
- Artifact collection (screenshots, videos, traces)

## 🔄 Maintenance

### Regular Updates Needed
- Update selectors when UI changes
- Add new test cases for new features
- Maintain test data consistency
- Update browser versions

### Best Practices Implemented
- Page Object Model patterns
- Consistent wait strategies
- Proper error handling
- Comprehensive assertions
- Cross-browser compatibility preparation
- Maintainable and readable test code

---

**Total Test Suite Implementation**: ✅ **COMPLETE**
**Framework**: Playwright TypeScript
**Coverage**: All major OpsConductor functionality
**Status**: Production-ready comprehensive test suite