/**
 * Unit tests for Chat Intent Router
 */

import { analyzeIntent, ChatIntent } from './chatIntentRouter';

describe('ChatIntentRouter', () => {
  describe('analyzeIntent', () => {
    
    test('recognizes exact "ping" command', () => {
      const result = analyzeIntent('ping');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('recognizes "ping" case-insensitive', () => {
      const result = analyzeIntent('PING');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('recognizes echo command', () => {
      const result = analyzeIntent('please echo this back exactly: hello world');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('hello world');
    });

    test('recognizes asset count query - Windows 10', () => {
      const result = analyzeIntent('how many windows 10 os assets do we have?');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('asset_count');
      expect(result.toolParams).toEqual({ os: 'windows 10' });
    });

    test('recognizes asset count query - Windows 10 (no question mark)', () => {
      const result = analyzeIntent('how many windows 10 assets do we have');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('asset_count');
      expect(result.toolParams).toEqual({ os: 'windows 10' });
    });

    test('recognizes asset count query - Linux', () => {
      const result = analyzeIntent('how many linux os assets do we have?');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('asset_count');
      expect(result.toolParams).toEqual({ os: 'linux' });
    });

    test('recognizes asset count query - Ubuntu', () => {
      const result = analyzeIntent('how many ubuntu assets do we have?');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('asset_count');
      expect(result.toolParams).toEqual({ os: 'ubuntu' });
    });

    test('recognizes windows directory listing - show', () => {
      const result = analyzeIntent('show directory of the c drive on 192.168.50.211');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('windows_list_directory');
      expect(result.toolParams).toEqual({
        host: '192.168.50.211',
        path: 'C:\\'
      });
    });

    test('recognizes windows directory listing - list', () => {
      const result = analyzeIntent('list contents of c drive on server01');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('windows_list_directory');
      expect(result.toolParams).toEqual({
        host: 'server01',
        path: 'C:\\'
      });
    });

    test('recognizes windows directory listing - without "the"', () => {
      const result = analyzeIntent('show directory of c drive on 10.0.0.1');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('windows_list_directory');
      expect(result.toolParams).toEqual({
        host: '10.0.0.1',
        path: 'C:\\'
      });
    });

    test('recognizes DNS lookup', () => {
      const result = analyzeIntent('dns lookup example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('dns_lookup');
      expect(result.toolParams).toEqual({
        domain: 'example.com',
        record_type: 'A'
      });
    });

    test('recognizes DNS resolve', () => {
      const result = analyzeIntent('dns resolve google.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('dns_lookup');
      expect(result.toolParams).toEqual({
        domain: 'google.com',
        record_type: 'A'
      });
    });

    test('recognizes TCP port check', () => {
      const result = analyzeIntent('check port 443 on example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('tcp_port_check');
      expect(result.toolParams).toEqual({
        host: 'example.com',
        port: 443
      });
    });

    test('recognizes TCP port check with IP', () => {
      const result = analyzeIntent('check port 22 on 192.168.1.1');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('tcp_port_check');
      expect(result.toolParams).toEqual({
        host: '192.168.1.1',
        port: 22
      });
    });

    test('recognizes HTTP check', () => {
      const result = analyzeIntent('http check https://example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('http_check');
      expect(result.toolParams).toEqual({
        url: 'https://example.com',
        method: 'GET'
      });
    });

    test('recognizes fetch command', () => {
      const result = analyzeIntent('fetch http://api.example.com/health');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('http_check');
      expect(result.toolParams).toEqual({
        url: 'http://api.example.com/health',
        method: 'GET'
      });
    });

    test('recognizes traceroute', () => {
      const result = analyzeIntent('traceroute google.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('traceroute');
      expect(result.toolParams).toEqual({
        host: 'google.com'
      });
    });

    test('recognizes ping with host', () => {
      const result = analyzeIntent('ping 8.8.8.8');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('shell_ping');
      expect(result.toolParams).toEqual({
        host: '8.8.8.8'
      });
    });

    test('recognizes ping with hostname', () => {
      const result = analyzeIntent('ping server01.example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('shell_ping');
      expect(result.toolParams).toEqual({
        host: 'server01.example.com'
      });
    });

    test('falls back to selector search for tool queries', () => {
      const result = analyzeIntent('show me windows tools');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('show me windows tools');
      expect(result.platform).toBe('windows');
    });

    test('falls back to selector search for linux tool queries', () => {
      const result = analyzeIntent('find linux network tools');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('find linux network tools');
      expect(result.platform).toBe('linux');
    });

    test('falls back to selector search for generic queries', () => {
      const result = analyzeIntent('what can you do?');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('what can you do?');
      expect(result.platform).toBeUndefined();
    });

    test('handles empty input', () => {
      const result = analyzeIntent('');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('');
    });

    test('handles whitespace-only input', () => {
      const result = analyzeIntent('   ');
      expect(result.intent).toBe('selector.search');
      expect(result.query).toBe('');
    });

    test('trims input correctly', () => {
      const result = analyzeIntent('  ping  ');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('ping');
    });

    test('case-insensitive matching for all patterns', () => {
      const tests = [
        { input: 'PING', expected: 'exec.echo' },
        { input: 'DNS LOOKUP EXAMPLE.COM', expected: 'tool.execute' },
        { input: 'CHECK PORT 80 ON LOCALHOST', expected: 'tool.execute' },
        { input: 'HTTP CHECK HTTPS://EXAMPLE.COM', expected: 'tool.execute' },
        { input: 'TRACEROUTE GOOGLE.COM', expected: 'tool.execute' },
        { input: 'PING 127.0.0.1', expected: 'tool.execute' }
      ];

      tests.forEach(({ input, expected }) => {
        const result = analyzeIntent(input);
        expect(result.intent).toBe(expected as ChatIntent);
      });
    });

    test('does not match partial ping', () => {
      const result = analyzeIntent('pinging server');
      expect(result.intent).toBe('selector.search');
    });

    test('does not match ping in middle of sentence', () => {
      const result = analyzeIntent('I want to ping the server');
      expect(result.intent).toBe('selector.search');
    });

    test('handles special characters in echo', () => {
      const result = analyzeIntent('please echo this back exactly: hello @#$% world!');
      expect(result.intent).toBe('exec.echo');
      expect(result.input).toBe('hello @#$% world!');
    });

    test('handles hostnames with hyphens and underscores', () => {
      const result = analyzeIntent('ping my-server_01.example.com');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('shell_ping');
      expect(result.toolParams).toEqual({
        host: 'my-server_01.example.com'
      });
    });

    test('handles IPv6 addresses in port check', () => {
      const result = analyzeIntent('check port 80 on 2001:db8::1');
      expect(result.intent).toBe('tool.execute');
      expect(result.toolName).toBe('tcp_port_check');
      expect(result.toolParams).toEqual({
        host: '2001:db8::1',
        port: 80
      });
    });
  });
});