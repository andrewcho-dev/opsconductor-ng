import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Job, JobStep } from '../types';


interface VisualJobBuilderProps {
  onJobCreate: (jobData: any) => void;
  onCancel: () => void;
  editingJob?: Job | null;
}

interface FlowNode {
  id: string;
  type: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  config: any;
  inputs: number;
  outputs: number;
  category: string;
  library: string;
}

interface Connection {
  id: string;
  sourceNodeId: string;
  sourcePort: number;
  targetNodeId: string;
  targetPort: number;
}

interface NodeTemplate {
  id: string;
  name: string;
  type: string;
  category: string;
  library: string;
  icon: string;
  description: string;
  inputs: number;
  outputs: number;
  defaultConfig: any;
  color: string;
  parameters?: any[];
}

// Comprehensive node templates with all libraries
const nodeTemplates: NodeTemplate[] = [
  // Flow Control Nodes
  {
    id: 'start',
    name: 'Start',
    type: 'flow.start',
    category: 'flow',
    library: 'core',
    icon: '▶️',
    description: 'Job start point',
    inputs: 0,
    outputs: 1,
    defaultConfig: { name: 'Start' },
    color: '#28a745'
  },
  {
    id: 'end',
    name: 'End',
    type: 'flow.end',
    category: 'flow',
    library: 'core',
    icon: '⏹️',
    description: 'Job end point',
    inputs: 1,
    outputs: 0,
    defaultConfig: { name: 'End' },
    color: '#dc3545'
  },
  {
    id: 'target-assign',
    name: 'Target Assignment',
    type: 'target.assign',
    category: 'targets',
    library: 'core',
    icon: '🎯',
    description: 'Assign job execution to specific target',
    inputs: 1,
    outputs: 1,
    defaultConfig: { 
      target_id: null,
      target_name: '',
      hostname: '',
      ip_address: ''
    },
    color: '#28a745'
  },
  
  // Logic Control Library
  {
    id: 'if-condition',
    name: 'If Condition',
    type: 'logic.if',
    category: 'logic',
    library: 'logic_control',
    icon: '❓',
    description: 'Conditional branching based on expression',
    inputs: 1,
    outputs: 2,
    defaultConfig: { 
      condition: 'variable == "value"',
      variables: {},
      true_steps: [],
      false_steps: []
    },
    color: '#ffc107'
  },
  {
    id: 'switch-case',
    name: 'Switch Case',
    type: 'logic.switch',
    category: 'logic',
    library: 'logic_control',
    icon: '🔀',
    description: 'Multi-way conditional execution',
    inputs: 1,
    outputs: 3,
    defaultConfig: {
      expression: 'environment',
      cases: {
        'dev': [],
        'prod': []
      },
      default_steps: [],
      variables: {}
    },
    color: '#17a2b8'
  },
  {
    id: 'for-loop',
    name: 'For Loop',
    type: 'logic.for_loop',
    category: 'logic',
    library: 'logic_control',
    icon: '🔄',
    description: 'For loop iteration',
    inputs: 1,
    outputs: 2,
    defaultConfig: {
      start: 1,
      end: 10,
      step: 1,
      variable_name: 'i',
      steps: []
    },
    color: '#6f42c1'
  },
  {
    id: 'while-loop',
    name: 'While Loop',
    type: 'logic.while_loop',
    category: 'logic',
    library: 'logic_control',
    icon: '🔁',
    description: 'While loop with condition',
    inputs: 1,
    outputs: 2,
    defaultConfig: {
      condition: 'counter < 10',
      steps: [],
      max_iterations: 100,
      variables: {}
    },
    color: '#6f42c1'
  },
  {
    id: 'foreach',
    name: 'For Each',
    type: 'logic.foreach',
    category: 'logic',
    library: 'logic_control',
    icon: '📋',
    description: 'Iterate over array items',
    inputs: 1,
    outputs: 2,
    defaultConfig: {
      items: [],
      variable_name: 'item',
      index_name: 'index',
      steps: []
    },
    color: '#6f42c1'
  },
  {
    id: 'set-variable',
    name: 'Set Variable',
    type: 'logic.set_variable',
    category: 'variables',
    library: 'logic_control',
    icon: '📝',
    description: 'Set variable value',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      name: 'my_variable',
      value: 'default_value',
      type: 'string',
      scope: 'job'
    },
    color: '#20c997'
  },
  {
    id: 'wait',
    name: 'Wait',
    type: 'logic.wait',
    category: 'flow',
    library: 'logic_control',
    icon: '⏰',
    description: 'Wait for specified duration',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      seconds: 30,
      message: 'Waiting...'
    },
    color: '#fd7e14'
  },
  {
    id: 'retry',
    name: 'Retry',
    type: 'logic.retry',
    category: 'flow',
    library: 'logic_control',
    icon: '🔄',
    description: 'Retry operation with backoff',
    inputs: 1,
    outputs: 2,
    defaultConfig: {
      steps: [],
      max_attempts: 3,
      delay_seconds: 1,
      backoff_multiplier: 2.0
    },
    color: '#e83e8c'
  },
  {
    id: 'parallel',
    name: 'Parallel',
    type: 'logic.parallel',
    category: 'flow',
    library: 'logic_control',
    icon: '⚡',
    description: 'Execute steps in parallel',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      step_groups: [],
      max_concurrent: 5,
      fail_fast: false
    },
    color: '#6610f2'
  },
  {
    id: 'try-catch',
    name: 'Try-Catch',
    type: 'logic.try_catch',
    category: 'error_handling',
    library: 'logic_control',
    icon: '🛡️',
    description: 'Error handling with try-catch',
    inputs: 1,
    outputs: 2,
    defaultConfig: {
      try_steps: [],
      catch_steps: [],
      finally_steps: []
    },
    color: '#dc3545'
  },

  // Windows Operations Library
  {
    id: 'powershell',
    name: 'PowerShell',
    type: 'windows.powershell.execute',
    category: 'windows',
    library: 'windows_operations',
    icon: '💻',
    description: 'Execute PowerShell command',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      command: 'Get-Date',
      execution_policy: 'Bypass',
      timeout_seconds: 300,
      run_as_admin: false
    },
    color: '#007bff'
  },
  {
    id: 'cmd',
    name: 'Command',
    type: 'windows.cmd.execute',
    category: 'windows',
    library: 'windows_operations',
    icon: '⚫',
    description: 'Execute CMD command',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      command: 'echo Hello World',
      timeout_seconds: 300
    },
    color: '#6c757d'
  },
  {
    id: 'registry-read',
    name: 'Registry Read',
    type: 'windows.registry.read_value',
    category: 'registry',
    library: 'windows_operations',
    icon: '📋',
    description: 'Read Windows Registry value',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      hive: 'HKLM',
      key_path: 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion',
      value_name: 'ProductName'
    },
    color: '#fd7e14'
  },
  {
    id: 'registry-write',
    name: 'Registry Write',
    type: 'windows.registry.write_value',
    category: 'registry',
    library: 'windows_operations',
    icon: '✏️',
    description: 'Write Windows Registry value',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      hive: 'HKLM',
      key_path: 'SOFTWARE\\MyApp',
      value_name: 'Setting',
      value_data: 'Value',
      value_type: 'REG_SZ'
    },
    color: '#fd7e14'
  },
  {
    id: 'service-start',
    name: 'Start Service',
    type: 'windows.service.start',
    category: 'services',
    library: 'windows_operations',
    icon: '▶️',
    description: 'Start Windows service',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      service_name: 'W3SVC',
      timeout_seconds: 60
    },
    color: '#28a745'
  },
  {
    id: 'service-stop',
    name: 'Stop Service',
    type: 'windows.service.stop',
    category: 'services',
    library: 'windows_operations',
    icon: '⏹️',
    description: 'Stop Windows service',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      service_name: 'Spooler',
      timeout_seconds: 60,
      force: false
    },
    color: '#dc3545'
  },
  {
    id: 'eventlog-write',
    name: 'Write Event Log',
    type: 'windows.eventlog.write',
    category: 'eventlog',
    library: 'windows_operations',
    icon: '📝',
    description: 'Write to Windows Event Log',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      log_name: 'Application',
      source: 'MyApplication',
      event_id: 1001,
      message: 'Application event',
      entry_type: 'Information'
    },
    color: '#17a2b8'
  },

  // File Operations Library
  {
    id: 'file-create',
    name: 'Create File',
    type: 'file.create',
    category: 'file',
    library: 'file_operations',
    icon: '📄',
    description: 'Create a new file',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      path: '/tmp/newfile.txt',
      content: 'Hello World',
      encoding: 'utf-8',
      overwrite: false
    },
    color: '#28a745'
  },
  {
    id: 'file-read',
    name: 'Read File',
    type: 'file.read',
    category: 'file',
    library: 'file_operations',
    icon: '📖',
    description: 'Read file contents',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      path: '/tmp/file.txt',
      encoding: 'utf-8',
      max_size: 10485760
    },
    color: '#17a2b8'
  },
  {
    id: 'file-copy',
    name: 'Copy File',
    type: 'file.copy',
    category: 'file',
    library: 'file_operations',
    icon: '📁',
    description: 'Copy file from source to destination',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      source: '/tmp/source.txt',
      destination: '/tmp/dest.txt',
      overwrite: false
    },
    color: '#fd7e14'
  },
  {
    id: 'file-delete',
    name: 'Delete File',
    type: 'file.delete',
    category: 'file',
    library: 'file_operations',
    icon: '🗑️',
    description: 'Delete file',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      path: '/tmp/file.txt',
      confirm: true
    },
    color: '#dc3545'
  },
  {
    id: 'file-compress',
    name: 'Compress Files',
    type: 'file.compress',
    category: 'archive',
    library: 'file_operations',
    icon: '🗜️',
    description: 'Compress files into archive',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      files: ['/tmp/file1.txt', '/tmp/file2.txt'],
      archive_path: '/tmp/archive.zip',
      format: 'zip'
    },
    color: '#6f42c1'
  },
  {
    id: 'file-extract',
    name: 'Extract Archive',
    type: 'file.extract',
    category: 'archive',
    library: 'file_operations',
    icon: '📦',
    description: 'Extract archive contents',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      archive_path: '/tmp/archive.zip',
      destination: '/tmp/extracted',
      overwrite: false
    },
    color: '#6f42c1'
  },
  {
    id: 'file-download',
    name: 'Download File',
    type: 'file.download',
    category: 'network',
    library: 'file_operations',
    icon: '⬇️',
    description: 'Download file from URL',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      url: 'https://example.com/file.zip',
      destination: '/tmp/downloaded.zip',
      timeout: 300
    },
    color: '#20c997'
  },

  // System Operations Library
  {
    id: 'system-info',
    name: 'System Info',
    type: 'system.info.get',
    category: 'system',
    library: 'system_operations',
    icon: '💻',
    description: 'Get system information',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      include_hardware: true,
      include_network: true,
      include_processes: false
    },
    color: '#6c757d'
  },
  {
    id: 'cpu-performance',
    name: 'CPU Performance',
    type: 'system.performance.cpu',
    category: 'monitoring',
    library: 'system_operations',
    icon: '📊',
    description: 'Get CPU performance metrics',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      interval_seconds: 1,
      per_cpu: false,
      sample_count: 3
    },
    color: '#e83e8c'
  },
  {
    id: 'memory-performance',
    name: 'Memory Performance',
    type: 'system.performance.memory',
    category: 'monitoring',
    library: 'system_operations',
    icon: '🧠',
    description: 'Get memory performance metrics',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      include_swap: true,
      format_bytes: true
    },
    color: '#e83e8c'
  },
  {
    id: 'process-list',
    name: 'List Processes',
    type: 'system.process.list',
    category: 'process',
    library: 'system_operations',
    icon: '📋',
    description: 'List running processes',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      sort_by: 'cpu_percent',
      limit: 50
    },
    color: '#fd7e14'
  },
  {
    id: 'process-kill',
    name: 'Kill Process',
    type: 'system.process.kill',
    category: 'process',
    library: 'system_operations',
    icon: '💀',
    description: 'Kill process by PID or name',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      name: 'notepad.exe',
      signal: 'TERM',
      kill_children: false
    },
    color: '#dc3545'
  },

  // Network Operations Library
  {
    id: 'http-get',
    name: 'HTTP GET',
    type: 'network.http.get',
    category: 'http',
    library: 'network_operations',
    icon: '🌐',
    description: 'Perform HTTP GET request',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      url: 'https://api.example.com/status',
      headers: {},
      timeout_seconds: 30,
      verify_ssl: true
    },
    color: '#20c997'
  },
  {
    id: 'http-post',
    name: 'HTTP POST',
    type: 'network.http.post',
    category: 'http',
    library: 'network_operations',
    icon: '📤',
    description: 'Perform HTTP POST request',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      url: 'https://api.example.com/data',
      json_data: {},
      headers: {'Content-Type': 'application/json'},
      timeout_seconds: 30
    },
    color: '#20c997'
  },
  {
    id: 'dns-lookup',
    name: 'DNS Lookup',
    type: 'network.dns.lookup',
    category: 'dns',
    library: 'network_operations',
    icon: '🔍',
    description: 'Perform DNS lookup',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      hostname: 'example.com',
      record_type: 'A',
      timeout_seconds: 10
    },
    color: '#6610f2'
  },
  {
    id: 'port-test',
    name: 'Test Port',
    type: 'network.port.test',
    category: 'connectivity',
    library: 'network_operations',
    icon: '🔌',
    description: 'Test network port connectivity',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      host: 'example.com',
      port: 80,
      timeout_seconds: 5,
      protocol: 'tcp'
    },
    color: '#17a2b8'
  },
  {
    id: 'port-scan',
    name: 'Port Scan',
    type: 'network.port.scan',
    category: 'connectivity',
    library: 'network_operations',
    icon: '🔍',
    description: 'Scan multiple ports',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      host: '192.168.1.1',
      ports: [22, 80, 443, 3389],
      timeout_seconds: 2
    },
    color: '#17a2b8'
  },
  {
    id: 'ssl-certificate',
    name: 'SSL Certificate',
    type: 'network.ssl.certificate_info',
    category: 'ssl',
    library: 'network_operations',
    icon: '🔒',
    description: 'Get SSL certificate information',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      hostname: 'example.com',
      port: 443,
      timeout_seconds: 10
    },
    color: '#28a745'
  },
  {
    id: 'send-email',
    name: 'Send Email',
    type: 'network.email.send',
    category: 'email',
    library: 'network_operations',
    icon: '📧',
    description: 'Send email via SMTP',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      smtp_server: 'smtp.gmail.com',
      smtp_port: 587,
      from_email: 'sender@example.com',
      to_emails: ['recipient@example.com'],
      subject: 'Test Email',
      body: 'This is a test email',
      use_tls: true
    },
    color: '#fd7e14'
  },
  {
    id: 'ping',
    name: 'Ping',
    type: 'system.network.ping',
    category: 'network',
    library: 'system_operations',
    icon: '📡',
    description: 'Ping network host',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      host: '8.8.8.8',
      count: 4,
      timeout_seconds: 5
    },
    color: '#20c997'
  },

  // Database Operations Library
  {
    id: 'db-connect',
    name: 'DB Connect',
    type: 'database.connect',
    category: 'database',
    library: 'database_operations',
    icon: '🔌',
    description: 'Connect to database',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      connection_string: 'postgresql://user:pass@localhost:5432/mydb',
      database_type: 'postgresql',
      timeout_seconds: 30
    },
    color: '#6f42c1'
  },
  {
    id: 'db-query',
    name: 'DB Query',
    type: 'database.query',
    category: 'database',
    library: 'database_operations',
    icon: '🔍',
    description: 'Execute SQL query',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      connection_id: 'main_db',
      sql: 'SELECT * FROM users WHERE active = %(active)s',
      parameters: { active: true },
      fetch_mode: 'all'
    },
    color: '#6f42c1'
  },
  {
    id: 'db-execute',
    name: 'DB Execute',
    type: 'database.execute',
    category: 'database',
    library: 'database_operations',
    icon: '⚡',
    description: 'Execute SQL statement',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      connection_id: 'main_db',
      sql: 'UPDATE users SET active = %(active)s WHERE id = %(user_id)s',
      parameters: { active: false, user_id: 123 }
    },
    color: '#6f42c1'
  },
  {
    id: 'db-backup',
    name: 'DB Backup',
    type: 'database.backup',
    category: 'database',
    library: 'database_operations',
    icon: '💾',
    description: 'Create database backup',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      connection_id: 'main_db',
      backup_path: '/backups/db_backup.sql.gz',
      compression: true
    },
    color: '#6f42c1'
  },

  // Security Operations Library
  {
    id: 'encrypt-data',
    name: 'Encrypt Data',
    type: 'security.encrypt_data',
    category: 'security',
    library: 'security_operations',
    icon: '🔒',
    description: 'Encrypt sensitive data',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      data: 'sensitive information',
      algorithm: 'AES-256',
      key: 'my-secret-key-32-chars-long!!!',
      output_format: 'base64'
    },
    color: '#dc3545'
  },
  {
    id: 'decrypt-data',
    name: 'Decrypt Data',
    type: 'security.decrypt_data',
    category: 'security',
    library: 'security_operations',
    icon: '🔓',
    description: 'Decrypt encrypted data',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      encrypted_data: 'U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y=',
      algorithm: 'AES-256',
      key: 'my-secret-key-32-chars-long!!!'
    },
    color: '#dc3545'
  },
  {
    id: 'generate-hash',
    name: 'Generate Hash',
    type: 'security.generate_hash',
    category: 'security',
    library: 'security_operations',
    icon: '#️⃣',
    description: 'Generate hash of data',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      data: 'mypassword123',
      algorithm: 'SHA-256',
      salt: 'randomsalt',
      output_format: 'hex'
    },
    color: '#dc3545'
  },
  {
    id: 'vulnerability-scan',
    name: 'Vulnerability Scan',
    type: 'security.vulnerability_scan',
    category: 'security',
    library: 'security_operations',
    icon: '🛡️',
    description: 'Scan for vulnerabilities',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      target: 'https://example.com',
      scan_type: 'comprehensive',
      include_cve_check: true
    },
    color: '#dc3545'
  },
  {
    id: 'check-certificate',
    name: 'Check Certificate',
    type: 'security.check_certificate',
    category: 'security',
    library: 'security_operations',
    icon: '📜',
    description: 'Check SSL certificate',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      hostname: 'example.com',
      port: 443,
      warn_days_before_expiry: 30
    },
    color: '#dc3545'
  },
  {
    id: 'compliance-check',
    name: 'Compliance Check',
    type: 'security.compliance_check',
    category: 'security',
    library: 'security_operations',
    icon: '✅',
    description: 'Perform compliance assessment',
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      framework: 'CIS',
      target_system: 'linux',
      check_categories: ['access_control', 'logging', 'network']
    },
    color: '#dc3545'
  }
];

const VisualJobBuilder: React.FC<VisualJobBuilderProps> = ({ onJobCreate, onCancel, editingJob }) => {
  const [jobName, setJobName] = useState('');
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLibrary, setSelectedLibrary] = useState<string>('all');
  const [draggedTemplate, setDraggedTemplate] = useState<NodeTemplate | null>(null);
  const [selectedNode, setSelectedNode] = useState<FlowNode | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<{ nodeId: string, port: number } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [showConfigPanel, setShowConfigPanel] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    // Add default start node
    if (nodes.length === 0) {
      const startNode: FlowNode = {
        id: 'start-' + Date.now(),
        type: 'flow.start',
        name: 'Start',
        x: 100,
        y: 100,
        width: 120,
        height: 60,
        config: { name: 'Start' },
        inputs: 0,
        outputs: 1,
        category: 'flow',
        library: 'core'
      };
      setNodes([startNode]);
    }
  }, []);

  useEffect(() => {
    if (editingJob) {
      setJobName(editingJob.name || '');
      // TODO: Convert job steps to visual nodes
    }
  }, [editingJob]);



  const handleCanvasMouseMove = useCallback((e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setMousePos({ x, y });

    if (isDragging && selectedNode) {
      setNodes(prev => prev.map(node => 
        node.id === selectedNode.id 
          ? { ...node, x: x - dragOffset.x, y: y - dragOffset.y }
          : node
      ));
    }
  }, [isDragging, selectedNode, dragOffset]);

  const handleCanvasMouseUp = useCallback(() => {
    setIsDragging(false);
    setSelectedNode(null);
    setDragOffset({ x: 0, y: 0 });
  }, []);

  const handleNodeMouseDown = (node: FlowNode, e: React.MouseEvent) => {
    e.stopPropagation();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setSelectedNode(node);
    setIsDragging(true);
    setDragOffset({
      x: x - node.x,
      y: y - node.y
    });
  };

  const handleNodeDoubleClick = (node: FlowNode) => {
    setSelectedNode(node);
    setShowConfigPanel(true);
  };

  const handleOutputPortClick = (nodeId: string, port: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (isConnecting) {
      // Complete connection
      if (connectionStart && connectionStart.nodeId !== nodeId) {
        const newConnection: Connection = {
          id: `conn-${Date.now()}`,
          sourceNodeId: connectionStart.nodeId,
          sourcePort: connectionStart.port,
          targetNodeId: nodeId,
          targetPort: port
        };
        setConnections(prev => [...prev, newConnection]);
      }
      setIsConnecting(false);
      setConnectionStart(null);
    } else {
      // Start connection
      setIsConnecting(true);
      setConnectionStart({ nodeId, port });
    }
  };

  const handleInputPortClick = (nodeId: string, port: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (isConnecting && connectionStart) {
      const newConnection: Connection = {
        id: `conn-${Date.now()}`,
        sourceNodeId: connectionStart.nodeId,
        sourcePort: connectionStart.port,
        targetNodeId: nodeId,
        targetPort: port
      };
      setConnections(prev => [...prev, newConnection]);
      setIsConnecting(false);
      setConnectionStart(null);
    }
  };

  const addNodeFromTemplate = (template: NodeTemplate, x: number, y: number) => {
    const newNode: FlowNode = {
      id: `${template.type}-${Date.now()}`,
      type: template.type,
      name: template.name,
      x,
      y,
      width: 140,
      height: 80,
      config: { ...template.defaultConfig },
      inputs: template.inputs,
      outputs: template.outputs,
      category: template.category,
      library: template.library
    };
    setNodes(prev => [...prev, newNode]);
  };

  const handleTemplateDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedTemplate) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    addNodeFromTemplate(draggedTemplate, x, y);
    setDraggedTemplate(null);
  };

  const deleteNode = (nodeId: string) => {
    setNodes(prev => prev.filter(node => node.id !== nodeId));
    setConnections(prev => prev.filter(conn => 
      conn.sourceNodeId !== nodeId && conn.targetNodeId !== nodeId
    ));
  };

  const deleteConnection = (connectionId: string) => {
    setConnections(prev => prev.filter(conn => conn.id !== connectionId));
  };

  const updateNodeConfig = (nodeId: string, newConfig: any) => {
    setNodes(prev => prev.map(node => 
      node.id === nodeId ? { ...node, config: { ...node.config, ...newConfig } } : node
    ));
  };

  const getNodePosition = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    return node ? { x: node.x, y: node.y, width: node.width, height: node.height } : null;
  };

  const renderConnection = (conn: Connection) => {
    const sourcePos = getNodePosition(conn.sourceNodeId);
    const targetPos = getNodePosition(conn.targetNodeId);
    
    if (!sourcePos || !targetPos) return null;
    
    const x1 = sourcePos.x + sourcePos.width;
    const y1 = sourcePos.y + sourcePos.height / 2;
    const x2 = targetPos.x;
    const y2 = targetPos.y + targetPos.height / 2;
    
    const midX = (x1 + x2) / 2;
    
    return (
      <g key={conn.id}>
        <path
          d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
          stroke="#007bff"
          strokeWidth="2"
          fill="none"
          markerEnd="url(#arrowhead)"
          style={{ cursor: 'pointer' }}
          onClick={() => deleteConnection(conn.id)}
        />
        {/* Connection delete button */}
        <circle
          cx={(x1 + x2) / 2}
          cy={(y1 + y2) / 2}
          r="8"
          fill="#dc3545"
          style={{ cursor: 'pointer' }}
          onClick={() => deleteConnection(conn.id)}
        />
        <text
          x={(x1 + x2) / 2}
          y={(y1 + y2) / 2 + 3}
          textAnchor="middle"
          fill="white"
          fontSize="10"
          style={{ cursor: 'pointer', userSelect: 'none' }}
          onClick={() => deleteConnection(conn.id)}
        >
          ×
        </text>
      </g>
    );
  };

  const renderTempConnection = () => {
    if (!isConnecting || !connectionStart) return null;
    
    const sourcePos = getNodePosition(connectionStart.nodeId);
    if (!sourcePos) return null;
    
    const x1 = sourcePos.x + sourcePos.width;
    const y1 = sourcePos.y + sourcePos.height / 2;
    const x2 = mousePos.x;
    const y2 = mousePos.y;
    
    return (
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke="#007bff"
        strokeWidth="2"
        strokeDasharray="5,5"
      />
    );
  };

  const handleSubmit = () => {
    if (!jobName.trim()) {
      alert('Please enter a job name');
      return;
    }



    if (nodes.length === 0) {
      alert('Please add at least one step');
      return;
    }

    // Convert visual flow to job steps
    const steps = nodes
      .filter(node => node.type !== 'flow.start' && node.type !== 'flow.end')
      .map(node => ({
        type: node.type,
        name: node.config.name || node.name,
        ...node.config
      }));

    const jobData = {
      name: jobName,
      version: 1,
      definition: {
        name: jobName,
        version: 1,
        parameters: {},
        steps: steps,
        flow: {
          nodes: nodes,
          connections: connections
        }
      },
      is_active: true
    };

    onJobCreate(jobData);
  };

  // Get unique categories and libraries
  const categories = ['all', ...Array.from(new Set(nodeTemplates.map(t => t.category)))];
  const libraries = ['all', ...Array.from(new Set(nodeTemplates.map(t => t.library)))];

  // Filter templates
  const filteredTemplates = nodeTemplates.filter(template => {
    const categoryMatch = selectedCategory === 'all' || template.category === selectedCategory;
    const libraryMatch = selectedLibrary === 'all' || template.library === selectedLibrary;
    const searchMatch = searchTerm === '' || 
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.type.toLowerCase().includes(searchTerm.toLowerCase());
    
    return categoryMatch && libraryMatch && searchMatch;
  });

  return (
    <div style={{ display: 'flex', height: '90vh', backgroundColor: '#f8f9fa' }}>
      {/* Left Panel - Node Palette */}
      <div style={{ 
        width: '320px', 
        backgroundColor: 'white', 
        borderRight: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0
      }}>
        {/* Job Configuration */}
        <div style={{ padding: '15px', borderBottom: '1px solid #ddd' }}>
          <h4 style={{ margin: '0 0 15px 0', fontSize: '16px' }}>Job Configuration</h4>
          <div style={{ marginBottom: '10px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
              Job Name *
            </label>
            <input
              type="text"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              placeholder="Enter job name"
              style={{ 
                width: '100%', 
                padding: '6px', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                fontSize: '12px'
              }}
            />
          </div>
          

        </div>

        {/* Node Palette */}
        <div style={{ flex: 1, padding: '15px', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <h4 style={{ margin: '0 0 15px 0', fontSize: '16px' }}>Step Library</h4>
          
          {/* Search */}
          <input
            type="text"
            placeholder="Search steps..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '6px', 
              marginBottom: '10px', 
              border: '1px solid #ddd', 
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          
          {/* Filters */}
          <div style={{ display: 'flex', gap: '5px', marginBottom: '15px' }}>
            <select 
              value={selectedLibrary} 
              onChange={(e) => setSelectedLibrary(e.target.value)}
              style={{ flex: 1, padding: '4px', fontSize: '11px', border: '1px solid #ddd', borderRadius: '3px' }}
            >
              {libraries.map(lib => (
                <option key={lib} value={lib}>
                  {lib === 'all' ? 'All Libraries' : lib.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
            
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ flex: 1, padding: '4px', fontSize: '11px', border: '1px solid #ddd', borderRadius: '3px' }}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Node Templates */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '6px',
            paddingRight: '5px',
            minHeight: 0
          }}>
            {/* Generic Target Block */}
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '12px', margin: '0 0 8px 0', color: '#333', fontWeight: 'bold' }}>🎯 Target Block</h4>
              <div
                draggable
                onDragStart={() => setDraggedTemplate({
                  id: 'generic-target',
                  name: 'Target',
                  type: 'target.selector',
                  category: 'targets',
                  library: 'core',
                  icon: '🎯',
                  description: 'Configurable target selector - choose specific targets or groups',
                  inputs: 0,
                  outputs: 1,
                  defaultConfig: { 
                    target_type: 'single', // 'single', 'multiple', 'group'
                    selected_targets: [],
                    selected_groups: [],
                    target_name: 'Unconfigured Target'
                  },
                  color: '#007bff'
                })}
                style={{
                  padding: '8px',
                  border: '1px solid #007bff',
                  borderRadius: '4px',
                  cursor: 'grab',
                  backgroundColor: '#007bff15',
                  fontSize: '11px',
                  marginBottom: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  minHeight: '50px'
                }}
                title="Drag to canvas to create a configurable target selector"
              >
                <span style={{ fontSize: '16px' }}>🎯</span>
                <div>
                  <div style={{ fontWeight: 'bold' }}>🎯 Target [WEBSOCKET TEST]</div>
                  <div style={{ color: '#666', fontSize: '10px' }}>Configurable target selector</div>
                  <div style={{ color: '#007bff', fontSize: '9px' }}>Connect actions to this target</div>
                </div>
              </div>
            </div>

            {/* Step Templates */}
            <div>
              <h4 style={{ fontSize: '12px', margin: '0 0 8px 0', color: '#333', fontWeight: 'bold' }}>🔧 Steps</h4>
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  draggable
                  onDragStart={() => setDraggedTemplate(template)}
                  style={{
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'grab',
                    backgroundColor: template.color + '15',
                    borderColor: template.color,
                    fontSize: '11px',
                    minHeight: '50px',
                    display: 'flex',
                    flexDirection: 'column',
                    marginBottom: '6px'
                  }}
                  title={`Library: ${template.library}\nCategory: ${template.category}\nType: ${template.type}`}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span>{template.icon}</span>
                    <span>{template.name}</span>
                  </div>
                  <div style={{ color: '#666', fontSize: '10px', lineHeight: '1.2', flex: 1 }}>
                    {template.description}
                  </div>
                  <div style={{ fontSize: '9px', color: '#999', marginTop: '3px' }}>
                    {template.library.replace('_', ' ')} • {template.category}
                  </div>
                </div>
              ))}
              
              {filteredTemplates.length === 0 && (
                <div style={{ textAlign: 'center', color: '#666', fontSize: '12px', padding: '20px' }}>
                  No steps found matching your criteria
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ padding: '15px', borderTop: '1px solid #ddd' }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <button
              onClick={() => setShowConfigPanel(!showConfigPanel)}
              disabled={!selectedNode}
              style={{ 
                flex: 1,
                padding: '6px', 
                backgroundColor: selectedNode ? '#17a2b8' : '#6c757d', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                fontSize: '11px',
                cursor: selectedNode ? 'pointer' : 'not-allowed'
              }}
            >
              Configure Step
            </button>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={onCancel}
              style={{ 
                flex: 1,
                padding: '8px', 
                backgroundColor: '#6c757d', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                fontSize: '12px'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              style={{ 
                flex: 1,
                padding: '8px', 
                backgroundColor: '#007bff', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                fontSize: '12px'
              }}
            >
              Create Job
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div
          ref={canvasRef}
          style={{
            width: '100%',
            height: '100%',
            position: 'relative',
            backgroundColor: '#fafafa',
            backgroundImage: 'radial-gradient(circle, #ddd 1px, transparent 1px)',
            backgroundSize: '20px 20px',
            cursor: isConnecting ? 'crosshair' : 'default'
          }}
          onMouseMove={handleCanvasMouseMove}
          onMouseUp={handleCanvasMouseUp}
          onDrop={handleTemplateDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => {
            setSelectedNode(null);
            setShowConfigPanel(false);
          }}
        >
          {/* SVG for connections */}
          <svg
            ref={svgRef}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 1
            }}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon
                  points="0 0, 10 3.5, 0 7"
                  fill="#007bff"
                />
              </marker>
            </defs>
            {connections.map(renderConnection)}
            {renderTempConnection()}
          </svg>

          {/* Flow Nodes */}
          {nodes.map(node => {
            const template = nodeTemplates.find(t => t.type === node.type);
            const isSelected = selectedNode?.id === node.id;
            
            return (
              <div
                key={node.id}
                style={{
                  position: 'absolute',
                  left: node.x,
                  top: node.y,
                  width: node.width,
                  height: node.height,
                  backgroundColor: template?.color || '#007bff',
                  border: `3px solid ${isSelected ? '#ffc107' : (template?.color || '#007bff')}`,
                  borderRadius: node.type.includes('if') ? '50%' : '8px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'move',
                  zIndex: 2,
                  boxShadow: isSelected ? '0 4px 8px rgba(255,193,7,0.3)' : '0 2px 4px rgba(0,0,0,0.1)',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  userSelect: 'none',
                  padding: '4px'
                }}
                onMouseDown={(e) => handleNodeMouseDown(node, e)}
                onDoubleClick={() => handleNodeDoubleClick(node)}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNode(node);
                }}
              >
                <div style={{ fontSize: '16px', marginBottom: '2px' }}>
                  {template?.icon}
                </div>
                <div style={{ fontSize: '9px', lineHeight: '1.1', textAlign: 'center' }}>
                  {node.type === 'target.selector' ? 
                    (node.config.target_name || 'Unconfigured Target') : 
                    node.name
                  }
                </div>
                <div style={{ fontSize: '8px', opacity: 0.8, marginTop: '1px' }}>
                  {node.type === 'target.selector' ? 
                    (node.config.selected_targets?.length > 0 ? 
                      `${node.config.selected_targets.length} target${node.config.selected_targets.length > 1 ? 's' : ''}` : 
                      'Not configured'
                    ) : 
                    template?.library
                  }
                </div>

                {/* Input Ports */}
                {Array.from({ length: node.inputs }).map((_, i) => (
                  <div
                    key={`input-${i}`}
                    style={{
                      position: 'absolute',
                      left: -8,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: 16,
                      height: 16,
                      backgroundColor: '#fff',
                      border: '2px solid ' + (template?.color || '#007bff'),
                      borderRadius: '50%',
                      cursor: 'pointer',
                      pointerEvents: 'all',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '8px',
                      color: template?.color || '#007bff'
                    }}
                    onClick={(e) => handleInputPortClick(node.id, i, e)}
                    title="Input port - click to connect"
                  >
                    ●
                  </div>
                ))}

                {/* Output Ports */}
                {Array.from({ length: node.outputs }).map((_, i) => (
                  <div
                    key={`output-${i}`}
                    style={{
                      position: 'absolute',
                      right: -8,
                      top: node.outputs === 1 ? '50%' : `${25 + (i * 50)}%`,
                      transform: 'translateY(-50%)',
                      width: 16,
                      height: 16,
                      backgroundColor: template?.color || '#007bff',
                      border: '2px solid #fff',
                      borderRadius: '50%',
                      cursor: 'pointer',
                      pointerEvents: 'all',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '8px',
                      color: 'white'
                    }}
                    onClick={(e) => handleOutputPortClick(node.id, i, e)}
                    title="Output port - click to start connection"
                  >
                    ●
                  </div>
                ))}

                {/* Delete Button */}
                {node.type !== 'flow.start' && (
                  <button
                    style={{
                      position: 'absolute',
                      top: -10,
                      right: -10,
                      width: 20,
                      height: 20,
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '50%',
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      pointerEvents: 'all',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNode(node.id);
                    }}
                    title="Delete node"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Configuration Panel */}
      {showConfigPanel && selectedNode && (
        <div style={{
          position: 'absolute',
          right: '20px',
          top: '20px',
          width: '350px',
          maxHeight: '80vh',
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '15px',
            borderBottom: '1px solid #ddd',
            backgroundColor: '#f8f9fa',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <h5 style={{ margin: 0, fontSize: '14px' }}>Configure: {selectedNode.name}</h5>
            <button
              onClick={() => setShowConfigPanel(false)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '18px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
          </div>
          
          <div style={{ padding: '15px', overflowY: 'auto', flex: 1 }}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
                Step Name
              </label>
              <input
                type="text"
                value={selectedNode.config.name || selectedNode.name}
                onChange={(e) => updateNodeConfig(selectedNode.id, { name: e.target.value })}
                style={{
                  width: '100%',
                  padding: '6px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              />
            </div>

            {/* Special configuration for target selector */}
            {selectedNode.type === 'target.selector' && (
              <div style={{ marginBottom: '20px', padding: '10px', border: '1px solid #007bff', borderRadius: '4px', backgroundColor: '#f8f9ff' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#007bff' }}>Target Configuration</h4>
                
                <div style={{ marginBottom: '10px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
                    Target Type
                  </label>
                  <select
                    value={selectedNode.config.target_type || 'single'}
                    onChange={(e) => updateNodeConfig(selectedNode.id, { target_type: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '6px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}
                  >
                    <option value="single">Single Target</option>
                    <option value="multiple">Multiple Targets</option>
                    <option value="group">Target Group</option>
                  </select>
                </div>

                {(selectedNode.config.target_type === 'single' || selectedNode.config.target_type === 'multiple') && (
                  <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
                      Target Names (comma-separated)
                    </label>
                    <textarea
                      value={selectedNode.config.target_names || ''}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { 
                        target_names: e.target.value,
                        target_name: e.target.value.split(',').length === 1 ? e.target.value.trim() : `${e.target.value.split(',').length} targets`
                      })}
                      placeholder="Enter target names separated by commas (e.g., server1, server2, server3)"
                      rows={3}
                      style={{
                        width: '100%',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '11px',
                        resize: 'vertical'
                      }}
                    />
                  </div>
                )}

                {selectedNode.config.target_type === 'group' && (
                  <div style={{ marginBottom: '10px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
                      Select Target Groups
                    </label>
                    <div style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px', padding: '5px' }}>
                      {/* Target groups would go here - for now show placeholder */}
                      <div style={{ padding: '10px', textAlign: 'center', color: '#666', fontSize: '11px' }}>
                        Target groups not yet implemented
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Dynamic configuration based on node type */}
            {Object.entries(selectedNode.config).map(([key, value]) => {
              if (key === 'name') return null; // Already handled above
              
              return (
                <div key={key} style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', fontWeight: 'bold' }}>
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </label>
                  
                  {typeof value === 'boolean' ? (
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { [key]: e.target.checked })}
                    />
                  ) : typeof value === 'number' ? (
                    <input
                      type="number"
                      value={value}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { [key]: parseInt(e.target.value) || 0 })}
                      style={{
                        width: '100%',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    />
                  ) : Array.isArray(value) ? (
                    <textarea
                      value={JSON.stringify(value, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          updateNodeConfig(selectedNode.id, { [key]: parsed });
                        } catch (err) {
                          // Invalid JSON, don't update
                        }
                      }}
                      rows={3}
                      style={{
                        width: '100%',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                      }}
                    />
                  ) : typeof value === 'object' ? (
                    <textarea
                      value={JSON.stringify(value, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          updateNodeConfig(selectedNode.id, { [key]: parsed });
                        } catch (err) {
                          // Invalid JSON, don't update
                        }
                      }}
                      rows={4}
                      style={{
                        width: '100%',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                      }}
                    />
                  ) : (
                    <input
                      type="text"
                      value={String(value)}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { [key]: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '12px'
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualJobBuilder;
