/**
 * Unit tests for ChatIntentRouter
 */

import { analyzeIntent, executeEcho, searchTools } from './chatIntentRouter';

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