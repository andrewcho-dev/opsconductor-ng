/**
 * Unit tests for ChatIntentRouter
 */

import { analyzeIntent, executeEcho, executeTool, searchTools } from './chatIntentRouter';

describe('ChatIntentRouter', () => {
  describe('analyzeIntent', () => {
    test('should detect "ping" as exec.echo intent', () => {
      const result = analyzeIntent('ping');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('should detect "PING" (case-insensitive) as exec.echo intent', () => {
      const result = analyzeIntent('PING');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('should detect "Please echo this back exactly:" prefix', () => {
      const result = analyzeIntent('Please echo this back exactly: OpsConductor v1.1.0');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('OpsConductor v1.1.0');
    });

    test('should handle case-insensitive echo prefix', () => {
      const result = analyzeIntent('PLEASE ECHO THIS BACK EXACTLY: test message');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('test message');
    });

    test('should detect Windows platform in selector search', () => {
      const result = analyzeIntent('List two packet capture utilities for Windows');
      expect(result.intent).toBe('selector.search');
      expect(result.platform).toBe('windows');
      expect(result.query).toBe('List two packet capture utilities for Windows');
    });

    test('should detect Linux platform in selector search', () => {
      const result = analyzeIntent('Show me network diagnostics tools for Linux');
      expect(result.intent).toBe('selector.search');
      expect(result.platform).toBe('linux');
      expect(result.query).toBe('Show me network diagnostics tools for Linux');
    });

    test('should default to selector search for general queries', () => {
      const result = analyzeIntent('Find three tools that can help troubleshoot DNS problems');
      expect(result.intent).toBe('selector.search');
      expect(result.platform).toBeUndefined();
      expect(result.query).toBe('Find three tools that can help troubleshoot DNS problems');
    });

    test('should handle empty input', () => {
      const result = analyzeIntent('');
      expect(result.intent).toBe('selector.search');
    });

    test('should trim whitespace', () => {
      const result = analyzeIntent('  ping  ');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('should detect Windows list directory command', () => {
      const result = analyzeIntent('show directory of c drive on 192.168.50.211');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('windows_list_directory');
      expect(result.toolParams).toEqual({
        host: '192.168.50.211',
        path: 'C:\\'
      });
    });

    test('should detect DNS lookup command', () => {
      const result = analyzeIntent('dns lookup example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('dns_lookup');
      expect(result.toolParams).toEqual({
        domain: 'example.com',
        record_type: 'A'
      });
    });

    test('should detect TCP port check command', () => {
      const result = analyzeIntent('check port 80 on 127.0.0.1');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('tcp_port_check');
      expect(result.toolParams).toEqual({
        host: '127.0.0.1',
        port: 80
      });
    });

    test('should detect HTTP check command', () => {
      const result = analyzeIntent('http check https://example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('http_check');
      expect(result.toolParams).toEqual({
        url: 'https://example.com',
        method: 'GET'
      });
    });

    test('should detect traceroute command', () => {
      const result = analyzeIntent('traceroute google.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('traceroute');
      expect(result.toolParams).toEqual({
        host: 'google.com'
      });
    });

    test('should detect ping command with host', () => {
      const result = analyzeIntent('ping 8.8.8.8');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('shell_ping');
      expect(result.toolParams).toEqual({
        host: '8.8.8.8'
      });
    });

    test('should route "tools" queries to selector search', () => {
      const result = analyzeIntent('What tools can help troubleshoot DNS issues?');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('What tools can help troubleshoot DNS issues?');
    });
  });

  describe('executeEcho', () => {
    // Mock fetch for testing
    global.fetch = jest.fn();

    beforeEach(() => {
      (global.fetch as jest.Mock).mockClear();
    });

    test('should call /ai/execute with correct payload', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          output: 'pong',
          trace_id: 'test-trace-123',
          duration_ms: 5.5,
          tool: 'echo'
        })
      });

      const result = await executeEcho('ping', 'test-trace-123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ai/execute'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Trace-Id': 'test-trace-123'
          }),
          body: JSON.stringify({
            tool: 'echo',
            input: 'ping'
          })
        })
      );

      expect(result.success).toBe(true);
      expect(result.output).toBe('pong');
      expect(result.trace_id).toBe('test-trace-123');
    });

    test('should handle echo with exact text', async () => {
      const exactText = 'OpsConductor walking skeleton v1.1.0';
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          output: exactText,
          trace_id: 'test-trace-456',
          duration_ms: 6.2,
          tool: 'echo'
        })
      });

      const result = await executeEcho(exactText);

      expect(result.success).toBe(true);
      expect(result.output).toBe(exactText);
    });

    test('should handle HTTP errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      const result = await executeEcho('ping');

      expect(result.success).toBe(false);
      expect(result.error).toContain('500');
    });

    test('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await executeEcho('ping');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network error');
    });
  });

  describe('executeTool', () => {
    global.fetch = jest.fn();

    beforeEach(() => {
      (global.fetch as jest.Mock).mockClear();
    });

    test('should call /ai/tools/execute with correct payload', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          tool: 'dns_lookup',
          output: { domain: 'example.com', ip: '93.184.216.34' },
          trace_id: 'test-trace-tool-123',
          duration_ms: 125.5
        })
      });

      const result = await executeTool('dns_lookup', { domain: 'example.com' }, 'test-trace-tool-123');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ai/tools/execute'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Trace-Id': 'test-trace-tool-123'
          }),
          body: JSON.stringify({
            name: 'dns_lookup',
            params: { domain: 'example.com' }
          })
        })
      );

      expect(result.success).toBe(true);
      expect(result.tool).toBe('dns_lookup');
      expect(result.output).toEqual({ domain: 'example.com', ip: '93.184.216.34' });
    });

    test('should handle tool execution errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Invalid parameters'
      });

      const result = await executeTool('tcp_port_check', { host: 'invalid', port: 99999 });

      expect(result.success).toBe(false);
      expect(result.error).toContain('400');
    });

    test('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Connection refused'));

      const result = await executeTool('http_check', { url: 'http://localhost:9999' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Connection refused');
    });
  });

  describe('searchTools', () => {
    global.fetch = jest.fn();

    beforeEach(() => {
      (global.fetch as jest.Mock).mockClear();
    });

    test('should call selector API with correct query params', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tools: [
            { name: 'nslookup', description: 'DNS lookup tool', platform: 'windows' },
            { name: 'dig', description: 'DNS query tool', platform: 'linux' }
          ]
        })
      });

      const result = await searchTools('DNS troubleshooting tools', undefined, 3, 'test-trace-789');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/selector/search?query=DNS+troubleshooting+tools&k=3'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-Trace-Id': 'test-trace-789'
          })
        })
      );

      expect(result.tools).toHaveLength(2);
      expect(result.count).toBe(2);
    });

    test('should include platform parameter when specified', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tools: [
            { name: 'Wireshark', description: 'Packet analyzer', platform: 'windows' }
          ]
        })
      });

      await searchTools('packet capture', 'windows', 3);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('platform=windows'),
        expect.any(Object)
      );
    });

    test('should handle empty results', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tools: []
        })
      });

      const result = await searchTools('nonexistent tool');

      expect(result.tools).toHaveLength(0);
      expect(result.count).toBe(0);
    });

    test('should handle API errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      const result = await searchTools('test query');

      expect(result.tools).toHaveLength(0);
      expect(result.count).toBe(0);
    });
  });
});