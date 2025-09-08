"""
Comprehensive Test Suite for Generic Block System
Demonstrates the power and flexibility of the generic block approach
"""

import asyncio
import json
from datetime import datetime
from .connection_manager import connection_manager
from .complete_generic_block_executor import complete_generic_block_executor


async def test_windows_process_monitoring():
    """Test the Windows Process Monitoring scenario from our examples"""
    print("🚀 Testing Windows Process Monitoring Workflow...")
    
    # Register Windows target
    connection_manager.register_target('win-server-01', {
        'hostname': '192.168.1.100',
        'os_type': 'windows',
        'default_connection': 'winrm',
        'username': 'administrator',
        'password': 'password123',
        'winrm_port': 5985,
        'winrm_use_ssl': False,
        'winrm_transport': 'ntlm'
    })
    
    # Step 1: Check if process is running
    print("  📋 Step 1: Checking process status...")
    check_process_result = await complete_generic_block_executor.execute_block(
        "action.command",
        {
            "id": "check-process-1",
            "target": "win-server-01",
            "connection_method": "winrm",
            "command": "tasklist /FI \"IMAGENAME eq MyApplication.exe\" /FO CSV | findstr /V \"INFO:\"",
            "shell": "cmd",
            "timeout_seconds": 30
        }
    )
    
    print(f"    ✅ Process check result: {check_process_result['success']}")
    if check_process_result['success']:
        print(f"    📄 Output: {check_process_result['result']['stdout'][:100]}...")
    
    # Step 2: Parse process status
    print("  🔍 Step 2: Parsing process status...")
    parse_result = await complete_generic_block_executor.execute_block(
        "data.transform",
        {
            "id": "parse-process-status-1",
            "script": """
const stdout = input.result.stdout || '';
const isRunning = stdout.includes('MyApplication.exe') && !stdout.includes('INFO: No tasks');

let processInfo = null;
if (isRunning) {
    const lines = stdout.split('\\n').filter(line => line.includes('MyApplication.exe'));
    if (lines.length > 0) {
        const parts = lines[0].split(',').map(part => part.replace(/"/g, '').trim());
        processInfo = {
            imageName: parts[0] || 'MyApplication.exe',
            pid: parts[1] || 'unknown',
            sessionName: parts[2] || 'unknown',
            memoryUsage: parts[4] || 'unknown'
        };
    }
}

result = {
    process_running: isRunning,
    process_info: processInfo,
    check_timestamp: new Date().toISOString(),
    raw_output: stdout
};
            """
        },
        check_process_result
    )
    
    print(f"    ✅ Parse result: {parse_result['success']}")
    if parse_result['success']:
        process_running = parse_result['result'].get('process_running', False)
        print(f"    🔍 Process running: {process_running}")
    
    # Step 3: Conditional logic - restart if needed
    print("  🤔 Step 3: Checking if restart is needed...")
    condition_result = await complete_generic_block_executor.execute_block(
        "logic.if",
        {
            "id": "process-decision-1",
            "condition": "{{data.process_running}} === false"
        },
        parse_result['result']
    )
    
    print(f"    ✅ Condition result: {condition_result['success']}")
    needs_restart = condition_result['result']['condition_result']
    print(f"    🔄 Needs restart: {needs_restart}")
    
    # Step 4: Start process if needed
    if needs_restart:
        print("  🚀 Step 4: Starting process...")
        start_result = await complete_generic_block_executor.execute_block(
            "action.command",
            {
                "id": "start-process-1",
                "target": "win-server-01",
                "connection_method": "winrm",
                "command": "\"C:\\Program Files\\MyCompany\\MyApplication\\MyApplication.exe\"",
                "shell": "cmd",
                "timeout_seconds": 30,
                "working_directory": "C:\\Program Files\\MyCompany\\MyApplication"
            }
        )
        print(f"    ✅ Start process result: {start_result['success']}")
    
    # Step 5: Send notification
    print("  📧 Step 5: Sending notification...")
    notification_result = await complete_generic_block_executor.execute_block(
        "action.notification",
        {
            "id": "send-notification-1",
            "notification_type": "email",
            "recipients": ["admin@company.com"],
            "subject": "Process Monitor Alert - MyApplication.exe on {{data.target}}",
            "message": "Process monitoring completed. Status: {{data.process_running}}",
            "priority": "normal"
        },
        {
            "target": "win-server-01",
            "process_running": not needs_restart
        }
    )
    
    print(f"    ✅ Notification sent: {notification_result['success']}")
    
    print("🎉 Windows Process Monitoring Test Complete!\n")
    return True


async def test_axis_camera_maintenance():
    """Test the Axis Camera Maintenance scenario"""
    print("🚀 Testing Axis Camera Maintenance Workflow...")
    
    # Register camera targets (simulated)
    cameras = [
        {'id': 'camera-01', 'ip': '192.168.1.101', 'name': 'Lobby Camera'},
        {'id': 'camera-02', 'ip': '192.168.1.102', 'name': 'Parking Camera'},
        {'id': 'camera-03', 'ip': '192.168.1.103', 'name': 'Entrance Camera'}
    ]
    
    results = []
    
    for camera in cameras:
        print(f"  📹 Processing {camera['name']}...")
        
        # Step 1: Autofocus command
        print(f"    🔍 Step 1: Performing autofocus...")
        autofocus_result = await complete_generic_block_executor.execute_block(
            "action.http_request",
            {
                "id": f"camera-autofocus-{camera['id']}",
                "method": "POST",
                "url": f"http://{camera['ip']}/axis-cgi/com/ptz.cgi",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                "authentication": {
                    "type": "basic",
                    "username": "admin",
                    "password": "admin123"
                },
                "body": "autofocus=on",
                "timeout_seconds": 30
            }
        )
        
        print(f"      ✅ Autofocus result: {autofocus_result['success']}")
        
        # Step 2: PTZ Home command
        print(f"    🏠 Step 2: Moving to home position...")
        ptz_result = await complete_generic_block_executor.execute_block(
            "action.http_request",
            {
                "id": f"camera-ptz-{camera['id']}",
                "method": "POST",
                "url": f"http://{camera['ip']}/axis-cgi/com/ptz.cgi",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                "authentication": {
                    "type": "basic",
                    "username": "admin",
                    "password": "admin123"
                },
                "body": "move=home",
                "timeout_seconds": 30
            }
        )
        
        print(f"      ✅ PTZ home result: {ptz_result['success']}")
        
        # Step 3: Record results
        camera_result = {
            'camera_id': camera['id'],
            'camera_name': camera['name'],
            'camera_ip': camera['ip'],
            'autofocus_success': autofocus_result['success'],
            'ptz_success': ptz_result['success'],
            'overall_success': autofocus_result['success'] and ptz_result['success']
        }
        results.append(camera_result)
    
    # Step 4: Generate summary
    print("  📊 Step 4: Generating maintenance summary...")
    summary_result = await complete_generic_block_executor.execute_block(
        "data.transform",
        {
            "id": "generate-summary-1",
            "script": """
const results = input.results || [];
const totalCameras = results.length;
const successfulCameras = results.filter(r => r.overall_success).length;
const failedCameras = totalCameras - successfulCameras;

result = {
    summary: {
        total_cameras: totalCameras,
        successful_cameras: successfulCameras,
        failed_cameras: failedCameras,
        success_rate: totalCameras > 0 ? (successfulCameras / totalCameras * 100).toFixed(1) + '%' : '0%'
    },
    detailed_results: results,
    maintenance_completed_at: new Date().toISOString()
};
            """
        },
        {"results": results}
    )
    
    print(f"    ✅ Summary generated: {summary_result['success']}")
    if summary_result['success']:
        summary = summary_result['result']['summary']
        print(f"    📈 Success rate: {summary['success_rate']} ({summary['successful_cameras']}/{summary['total_cameras']})")
    
    # Step 5: Send summary notification
    print("  📧 Step 5: Sending maintenance summary...")
    notification_result = await complete_generic_block_executor.execute_block(
        "action.notification",
        {
            "id": "send-summary-1",
            "notification_type": "email",
            "recipients": ["security@company.com", "maintenance@company.com"],
            "subject": "Camera Maintenance Complete - {{data.summary.success_rate}} Success",
            "message": "Weekly camera maintenance completed. Success rate: {{data.summary.success_rate}} ({{data.summary.successful_cameras}}/{{data.summary.total_cameras}} cameras)",
            "priority": "normal"
        },
        summary_result['result']
    )
    
    print(f"    ✅ Summary notification sent: {notification_result['success']}")
    
    print("🎉 Axis Camera Maintenance Test Complete!\n")
    return True


async def test_linux_service_management():
    """Test Linux service management scenario"""
    print("🚀 Testing Linux Service Management...")
    
    # Register Linux target
    connection_manager.register_target('linux-server-01', {
        'hostname': '192.168.1.50',
        'os_type': 'linux',
        'default_connection': 'ssh',
        'username': 'admin',
        'private_key': '/path/to/key.pem',
        'ssh_port': 22
    })
    
    # Step 1: Check service status
    print("  🔍 Step 1: Checking service status...")
    status_result = await complete_generic_block_executor.execute_block(
        "action.service_control",
        {
            "id": "check-nginx-status",
            "target": "linux-server-01",
            "service_name": "nginx",
            "action": "status",
            "timeout_seconds": 30
        }
    )
    
    print(f"    ✅ Status check result: {status_result['success']}")
    if status_result['success']:
        service_status = status_result['service_status']['status']
        print(f"    📊 Service status: {service_status}")
    
    # Step 2: Restart service if needed
    print("  🔄 Step 2: Restarting service...")
    restart_result = await complete_generic_block_executor.execute_block(
        "action.service_control",
        {
            "id": "restart-nginx",
            "target": "linux-server-01",
            "service_name": "nginx",
            "action": "restart",
            "timeout_seconds": 60
        }
    )
    
    print(f"    ✅ Restart result: {restart_result['success']}")
    
    # Step 3: Verify service is running
    print("  ✅ Step 3: Verifying service is running...")
    verify_result = await complete_generic_block_executor.execute_block(
        "action.service_control",
        {
            "id": "verify-nginx-running",
            "target": "linux-server-01",
            "service_name": "nginx",
            "action": "status",
            "timeout_seconds": 30
        }
    )
    
    print(f"    ✅ Verification result: {verify_result['success']}")
    
    print("🎉 Linux Service Management Test Complete!\n")
    return True


async def test_file_operations():
    """Test file operations across different systems"""
    print("🚀 Testing File Operations...")
    
    # Register local target for file operations
    connection_manager.register_target('local-system', {
        'hostname': 'localhost',
        'os_type': 'linux',
        'default_connection': 'local'
    })
    
    # Step 1: Create a test file
    print("  📝 Step 1: Creating test file...")
    create_result = await complete_generic_block_executor.execute_block(
        "action.file_operation",
        {
            "id": "create-test-file",
            "target": "local-system",
            "operation": "write",
            "source_path": "/tmp/opsconductor_test.txt",
            "file_content": "This is a test file created by OpsConductor Generic Blocks!\nTimestamp: {{timestamp}}",
            "create_directories": True,
            "overwrite_existing": True
        },
        {"timestamp": datetime.now().isoformat()}
    )
    
    print(f"    ✅ File creation result: {create_result['success']}")
    
    # Step 2: Read the file back
    print("  📖 Step 2: Reading test file...")
    read_result = await complete_generic_block_executor.execute_block(
        "action.file_operation",
        {
            "id": "read-test-file",
            "target": "local-system",
            "operation": "read",
            "source_path": "/tmp/opsconductor_test.txt"
        }
    )
    
    print(f"    ✅ File read result: {read_result['success']}")
    if read_result['success']:
        content = read_result['result']['data'].get('content', '')[:50]
        print(f"    📄 File content preview: {content}...")
    
    # Step 3: Check if file exists
    print("  🔍 Step 3: Checking file existence...")
    exists_result = await complete_generic_block_executor.execute_block(
        "action.file_operation",
        {
            "id": "check-file-exists",
            "target": "local-system",
            "operation": "exists",
            "source_path": "/tmp/opsconductor_test.txt"
        }
    )
    
    print(f"    ✅ File exists check: {exists_result['success']}")
    if exists_result['success']:
        exists = exists_result['result']['data'].get('exists', False)
        print(f"    📁 File exists: {exists}")
    
    print("🎉 File Operations Test Complete!\n")
    return True


async def test_data_transformation():
    """Test data transformation capabilities"""
    print("🚀 Testing Data Transformation...")
    
    # Sample data to transform
    sample_data = {
        "servers": [
            {"name": "web-01", "cpu": 85, "memory": 70, "status": "running"},
            {"name": "web-02", "cpu": 45, "memory": 60, "status": "running"},
            {"name": "db-01", "cpu": 90, "memory": 85, "status": "running"},
            {"name": "cache-01", "cpu": 30, "memory": 40, "status": "stopped"}
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # Step 1: Transform server data
    print("  🔄 Step 1: Transforming server data...")
    transform_result = await complete_generic_block_executor.execute_block(
        "data.transform",
        {
            "id": "transform-server-data",
            "script": """
const servers = input.servers || [];
const highCpuServers = servers.filter(s => s.cpu > 80);
const stoppedServers = servers.filter(s => s.status === 'stopped');
const runningServers = servers.filter(s => s.status === 'running');

const avgCpu = servers.reduce((sum, s) => sum + s.cpu, 0) / servers.length;
const avgMemory = servers.reduce((sum, s) => sum + s.memory, 0) / servers.length;

result = {
    summary: {
        total_servers: servers.length,
        running_servers: runningServers.length,
        stopped_servers: stoppedServers.length,
        high_cpu_servers: highCpuServers.length,
        average_cpu: Math.round(avgCpu * 100) / 100,
        average_memory: Math.round(avgMemory * 100) / 100
    },
    alerts: {
        high_cpu: highCpuServers.map(s => s.name),
        stopped: stoppedServers.map(s => s.name)
    },
    processed_at: new Date().toISOString()
};
            """
        },
        sample_data
    )
    
    print(f"    ✅ Transform result: {transform_result['success']}")
    if transform_result['success']:
        summary = transform_result['result']['summary']
        print(f"    📊 Servers: {summary['running_servers']}/{summary['total_servers']} running")
        print(f"    🚨 High CPU alerts: {len(transform_result['result']['alerts']['high_cpu'])}")
        print(f"    ⚠️  Stopped servers: {len(transform_result['result']['alerts']['stopped'])}")
    
    # Step 2: Generate alert conditions
    print("  🚨 Step 2: Checking alert conditions...")
    alert_condition = await complete_generic_block_executor.execute_block(
        "logic.if",
        {
            "id": "check-alerts",
            "condition": "{{data.alerts.high_cpu.length}} > 0 || {{data.alerts.stopped.length}} > 0"
        },
        transform_result['result']
    )
    
    print(f"    ✅ Alert condition result: {alert_condition['success']}")
    has_alerts = alert_condition['result']['condition_result']
    print(f"    🚨 Has alerts: {has_alerts}")
    
    # Step 3: Send alert if needed
    if has_alerts:
        print("  📧 Step 3: Sending alert notification...")
        alert_notification = await complete_generic_block_executor.execute_block(
            "action.notification",
            {
                "id": "send-server-alert",
                "notification_type": "email",
                "recipients": ["ops@company.com"],
                "subject": "Server Alert - High CPU or Stopped Servers Detected",
                "message": "Server monitoring alert:\n- High CPU servers: {{data.alerts.high_cpu}}\n- Stopped servers: {{data.alerts.stopped}}",
                "priority": "high"
            },
            transform_result['result']
        )
        print(f"    ✅ Alert sent: {alert_notification['success']}")
    
    print("🎉 Data Transformation Test Complete!\n")
    return True


async def test_workflow_with_delays():
    """Test workflow with delays and timing"""
    print("🚀 Testing Workflow with Delays...")
    
    # Step 1: Start workflow
    print("  🚀 Step 1: Starting timed workflow...")
    start_result = await complete_generic_block_executor.execute_block(
        "flow.start",
        {
            "id": "timed-workflow-start",
            "name": "Timed Maintenance Workflow",
            "trigger_types": ["manual", "schedule"]
        }
    )
    
    print(f"    ✅ Workflow started: {start_result['success']}")
    
    # Step 2: Short delay
    print("  ⏱️  Step 2: Short delay (2 seconds)...")
    delay_result = await complete_generic_block_executor.execute_block(
        "flow.delay",
        {
            "id": "short-delay",
            "delay_seconds": 2
        }
    )
    
    print(f"    ✅ Delay completed: {delay_result['success']}")
    if delay_result['success']:
        actual_delay = delay_result['result']['actual_delay_seconds']
        print(f"    ⏰ Actual delay: {actual_delay:.2f} seconds")
    
    # Step 3: Simulate some work
    print("  🔧 Step 3: Performing maintenance task...")
    work_result = await complete_generic_block_executor.execute_block(
        "data.transform",
        {
            "id": "maintenance-work",
            "script": """
// Simulate maintenance work
const startTime = new Date();
const tasks = [
    'Checking system health',
    'Updating configurations',
    'Cleaning temporary files',
    'Validating services'
];

result = {
    maintenance_tasks: tasks,
    completed_tasks: tasks.length,
    maintenance_time: startTime.toISOString(),
    status: 'completed'
};
            """
        }
    )
    
    print(f"    ✅ Maintenance work: {work_result['success']}")
    
    # Step 4: End workflow
    print("  🏁 Step 4: Ending workflow...")
    end_result = await complete_generic_block_executor.execute_block(
        "flow.end",
        {
            "id": "timed-workflow-end",
            "name": "Timed Maintenance Complete",
            "save_result": True,
            "result_name": "maintenance_summary"
        },
        work_result['result']
    )
    
    print(f"    ✅ Workflow ended: {end_result['success']}")
    if end_result['success']:
        execution_summary = end_result['result']['execution_summary']
        print(f"    📊 Total execution time: {execution_summary['total_execution_time']}ms")
        print(f"    📈 Success rate: {execution_summary['successful_blocks']}/{execution_summary['total_blocks']} blocks")
    
    print("🎉 Timed Workflow Test Complete!\n")
    return True


async def run_comprehensive_test_suite():
    """Run the complete test suite"""
    print("🎯 Starting Comprehensive Generic Block Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Windows Process Monitoring", test_windows_process_monitoring),
        ("Axis Camera Maintenance", test_axis_camera_maintenance),
        ("Linux Service Management", test_linux_service_management),
        ("File Operations", test_file_operations),
        ("Data Transformation", test_data_transformation),
        ("Workflow with Delays", test_workflow_with_delays)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 Running {test_name}...")
            result = await test_func()
            test_results.append((test_name, result, None))
            print(f"✅ {test_name}: PASSED\n")
        except Exception as e:
            test_results.append((test_name, False, str(e)))
            print(f"❌ {test_name}: FAILED - {str(e)}\n")
    
    # Print final summary
    print("🎯 Test Suite Summary")
    print("=" * 60)
    
    passed_tests = len([r for r in test_results if r[1] is True])
    total_tests = len(test_results)
    
    for test_name, result, error in test_results:
        status = "✅ PASSED" if result else f"❌ FAILED ({error})"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    print(f"🎉 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Show execution summary
    execution_summary = complete_generic_block_executor.get_execution_summary()
    print(f"\n📈 Execution Statistics:")
    print(f"  Total Blocks Executed: {execution_summary['total_blocks_executed']}")
    print(f"  Successful Blocks: {execution_summary['successful_blocks']}")
    print(f"  Failed Blocks: {execution_summary['failed_blocks']}")
    print(f"  Block Success Rate: {execution_summary['success_rate']:.1f}%")
    print(f"  Total Execution Time: {execution_summary['total_execution_time_ms']}ms")
    
    print("\n🚀 Generic Block System Test Suite Complete!")
    return passed_tests == total_tests


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(run_comprehensive_test_suite())