"""
Redis Streams Monitoring Dashboard
Web-based monitoring interface for Redis Streams
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import structlog
import uvloop
from aiohttp import web, WSMsgType
import aiohttp_jinja2
import jinja2

# Add shared directory to path
sys.path.append('/app/shared')

from redis_streams import (
    RedisStreamsClient, 
    create_streams_client
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class StreamsMonitor:
    """Redis Streams monitoring dashboard"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_STREAMS_URL", "redis://redis-streams:6379/0")
        self.password = os.getenv("REDIS_PASSWORD", "opsconductor-streams-2024")
        self.port = int(os.getenv("MONITOR_PORT", "8090"))
        self.refresh_interval = int(os.getenv("REFRESH_INTERVAL", "5"))
        
        self.client: Optional[RedisStreamsClient] = None
        self.app = web.Application()
        self.websockets: List[web.WebSocketResponse] = []
        
        self._setup_routes()
        self._setup_templates()
    
    def _setup_routes(self):
        """Setup web routes"""
        self.app.router.add_get('/', self.dashboard)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/api/streams', self.get_streams_info)
        self.app.router.add_get('/api/stream/{stream}', self.get_stream_details)
        self.app.router.add_get('/api/pending/{stream}/{group}', self.get_pending_messages)
        self.app.router.add_get('/api/metrics', self.get_metrics)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_static('/static', '/app/static', name='static')
    
    def _setup_templates(self):
        """Setup Jinja2 templates"""
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.DictLoader({
                'dashboard.html': self._get_dashboard_template()
            })
        )
    
    async def start(self):
        """Start the monitoring dashboard"""
        try:
            logger.info("Starting Redis Streams Monitor",
                       port=self.port,
                       redis_url=self.redis_url)
            
            # Initialize Redis client
            self.client = await create_streams_client(self.redis_url, self.password)
            
            # Start background tasks
            asyncio.create_task(self._broadcast_updates())
            
            # Start web server
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            logger.info("Monitor dashboard started successfully",
                       url=f"http://0.0.0.0:{self.port}")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("Failed to start monitor", error=str(e))
            raise
    
    async def dashboard(self, request):
        """Main dashboard page"""
        return aiohttp_jinja2.render_template('dashboard.html', request, {
            'title': 'Redis Streams Monitor',
            'refresh_interval': self.refresh_interval
        })
    
    async def health_check(self, request):
        """Health check endpoint"""
        try:
            if self.client:
                await self.client.redis_client.ping()
                return web.json_response({'status': 'healthy'})
            else:
                return web.json_response({'status': 'unhealthy'}, status=503)
        except Exception as e:
            return web.json_response({'status': 'unhealthy', 'error': str(e)}, status=503)
    
    async def get_streams_info(self, request):
        """Get information about all streams"""
        try:
            streams_info = {}
            
            for service, stream_name in self.client.MAIN_STREAMS.items():
                info = await self.client.get_stream_info(service)
                streams_info[service] = info
            
            # Add dead letter queue info
            try:
                dead_letter_info = await self.client.redis_client.xinfo_stream(self.client.DEAD_LETTER_STREAM)
                streams_info['dead_letter'] = {
                    'stream': self.client.DEAD_LETTER_STREAM,
                    'length': dead_letter_info.get('length', 0),
                    'first_entry': dead_letter_info.get('first-entry'),
                    'last_entry': dead_letter_info.get('last-entry')
                }
            except:
                streams_info['dead_letter'] = {'length': 0}
            
            return web.json_response(streams_info)
            
        except Exception as e:
            logger.error("Failed to get streams info", error=str(e))
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_stream_details(self, request):
        """Get detailed information about a specific stream"""
        try:
            stream = request.match_info['stream']
            
            # Get stream info
            info = await self.client.get_stream_info(stream)
            
            # Get recent messages
            stream_name = self.client.MAIN_STREAMS.get(stream, f"opsconductor:{stream}:events")
            recent_messages = await self.client.redis_client.xrevrange(
                stream_name, count=10
            )
            
            # Format messages
            formatted_messages = []
            for msg_id, fields in recent_messages:
                formatted_messages.append({
                    'id': msg_id,
                    'timestamp': datetime.fromtimestamp(float(fields.get('timestamp', 0))).isoformat(),
                    'event_type': fields.get('event_type', ''),
                    'service': fields.get('service', ''),
                    'priority': fields.get('priority', ''),
                    'data': json.loads(fields.get('data', '{}'))
                })
            
            info['recent_messages'] = formatted_messages
            
            return web.json_response(info)
            
        except Exception as e:
            logger.error("Failed to get stream details", stream=stream, error=str(e))
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_pending_messages(self, request):
        """Get pending messages for a consumer group"""
        try:
            stream = request.match_info['stream']
            group = request.match_info['group']
            
            pending = await self.client.get_pending_messages(stream, group)
            
            # Format pending messages
            formatted_pending = []
            for msg_info in pending:
                formatted_pending.append({
                    'id': msg_info[0],
                    'consumer': msg_info[1],
                    'idle_time': msg_info[2],
                    'delivery_count': msg_info[3]
                })
            
            return web.json_response({
                'stream': stream,
                'group': group,
                'pending_count': len(formatted_pending),
                'pending_messages': formatted_pending
            })
            
        except Exception as e:
            logger.error("Failed to get pending messages", 
                        stream=stream, group=group, error=str(e))
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_metrics(self, request):
        """Get Redis and streams metrics"""
        try:
            # Redis info
            redis_info = await self.client.redis_client.info()
            
            # Memory usage
            memory_info = {
                'used_memory': redis_info.get('used_memory', 0),
                'used_memory_human': redis_info.get('used_memory_human', '0B'),
                'used_memory_peak': redis_info.get('used_memory_peak', 0),
                'used_memory_peak_human': redis_info.get('used_memory_peak_human', '0B')
            }
            
            # Connection info
            connection_info = {
                'connected_clients': redis_info.get('connected_clients', 0),
                'total_connections_received': redis_info.get('total_connections_received', 0),
                'total_commands_processed': redis_info.get('total_commands_processed', 0)
            }
            
            # Performance metrics
            performance_info = {
                'instantaneous_ops_per_sec': redis_info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0)
            }
            
            # Calculate hit ratio
            hits = performance_info['keyspace_hits']
            misses = performance_info['keyspace_misses']
            hit_ratio = hits / (hits + misses) * 100 if (hits + misses) > 0 else 0
            performance_info['hit_ratio'] = round(hit_ratio, 2)
            
            return web.json_response({
                'memory': memory_info,
                'connections': connection_info,
                'performance': performance_info,
                'uptime_seconds': redis_info.get('uptime_in_seconds', 0),
                'redis_version': redis_info.get('redis_version', 'unknown')
            })
            
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            return web.json_response({'error': str(e)}, status=500)
    
    async def websocket_handler(self, request):
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.append(ws)
        logger.info("WebSocket client connected", total_clients=len(self.websockets))
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Handle client messages if needed
                    pass
                elif msg.type == WSMsgType.ERROR:
                    logger.error("WebSocket error", error=ws.exception())
        except Exception as e:
            logger.error("WebSocket handler error", error=str(e))
        finally:
            if ws in self.websockets:
                self.websockets.remove(ws)
            logger.info("WebSocket client disconnected", total_clients=len(self.websockets))
        
        return ws
    
    async def _broadcast_updates(self):
        """Broadcast updates to all connected WebSocket clients"""
        while True:
            try:
                await asyncio.sleep(self.refresh_interval)
                
                if not self.websockets:
                    continue
                
                # Get current data
                streams_info = {}
                for service in self.client.MAIN_STREAMS.keys():
                    try:
                        info = await self.client.get_stream_info(service)
                        streams_info[service] = info
                    except:
                        pass
                
                # Get metrics
                try:
                    redis_info = await self.client.redis_client.info()
                    metrics = {
                        'timestamp': time.time(),
                        'ops_per_sec': redis_info.get('instantaneous_ops_per_sec', 0),
                        'connected_clients': redis_info.get('connected_clients', 0),
                        'used_memory': redis_info.get('used_memory', 0)
                    }
                except:
                    metrics = {'timestamp': time.time()}
                
                # Broadcast to all clients
                update_data = {
                    'type': 'update',
                    'streams': streams_info,
                    'metrics': metrics
                }
                
                # Remove disconnected clients
                active_websockets = []
                for ws in self.websockets:
                    try:
                        await ws.send_str(json.dumps(update_data))
                        active_websockets.append(ws)
                    except:
                        pass  # Client disconnected
                
                self.websockets = active_websockets
                
            except Exception as e:
                logger.error("Error broadcasting updates", error=str(e))
    
    def _get_dashboard_template(self):
        """Get the HTML template for the dashboard"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 1rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
        .metric { display: flex; justify-content: space-between; margin: 0.5rem 0; }
        .metric-label { font-weight: 500; }
        .metric-value { color: #27ae60; font-weight: bold; }
        .status { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; }
        .status.healthy { background: #d4edda; color: #155724; }
        .status.warning { background: #fff3cd; color: #856404; }
        .status.error { background: #f8d7da; color: #721c24; }
        .stream-list { list-style: none; }
        .stream-item { padding: 0.5rem; margin: 0.25rem 0; background: #f8f9fa; border-radius: 4px; }
        .stream-name { font-weight: bold; color: #2c3e50; }
        .stream-stats { font-size: 0.9rem; color: #6c757d; margin-top: 0.25rem; }
        .refresh-indicator { position: fixed; top: 1rem; right: 1rem; padding: 0.5rem 1rem; background: #3498db; color: white; border-radius: 4px; }
        .chart-container { height: 200px; margin: 1rem 0; }
        #connectionStatus { position: fixed; bottom: 1rem; right: 1rem; padding: 0.5rem 1rem; border-radius: 4px; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>Real-time Redis Streams Monitoring Dashboard</p>
    </div>
    
    <div class="container">
        <div class="grid">
            <div class="card">
                <h3>Redis Metrics</h3>
                <div id="redisMetrics">
                    <div class="metric">
                        <span class="metric-label">Operations/sec:</span>
                        <span class="metric-value" id="opsPerSec">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Connected Clients:</span>
                        <span class="metric-value" id="connectedClients">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Memory Used:</span>
                        <span class="metric-value" id="memoryUsed">-</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Hit Ratio:</span>
                        <span class="metric-value" id="hitRatio">-</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Stream Overview</h3>
                <ul class="stream-list" id="streamsList">
                    <li>Loading streams...</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>Dead Letter Queue</h3>
                <div id="deadLetterInfo">
                    <div class="metric">
                        <span class="metric-label">Messages:</span>
                        <span class="metric-value" id="deadLetterCount">-</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h3>Stream Details</h3>
            <div id="streamDetails">
                <p>Select a stream to view details...</p>
            </div>
        </div>
    </div>
    
    <div id="connectionStatus" class="disconnected">Connecting...</div>
    <div class="refresh-indicator" id="refreshIndicator" style="display: none;">Updating...</div>
    
    <script>
        let ws = null;
        let reconnectInterval = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'connected';
                if (reconnectInterval) {
                    clearInterval(reconnectInterval);
                    reconnectInterval = null;
                }
                loadInitialData();
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'update') {
                    updateDashboard(data);
                }
            };
            
            ws.onclose = function() {
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'disconnected';
                
                if (!reconnectInterval) {
                    reconnectInterval = setInterval(connectWebSocket, 5000);
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        async function loadInitialData() {
            try {
                // Load streams info
                const streamsResponse = await fetch('/api/streams');
                const streamsData = await streamsResponse.json();
                updateStreamsDisplay(streamsData);
                
                // Load metrics
                const metricsResponse = await fetch('/api/metrics');
                const metricsData = await metricsResponse.json();
                updateMetricsDisplay(metricsData);
                
            } catch (error) {
                console.error('Error loading initial data:', error);
            }
        }
        
        function updateDashboard(data) {
            document.getElementById('refreshIndicator').style.display = 'block';
            
            if (data.streams) {
                updateStreamsDisplay(data.streams);
            }
            
            if (data.metrics) {
                updateMetricsFromWebSocket(data.metrics);
            }
            
            setTimeout(() => {
                document.getElementById('refreshIndicator').style.display = 'none';
            }, 500);
        }
        
        function updateStreamsDisplay(streams) {
            const streamsList = document.getElementById('streamsList');
            streamsList.innerHTML = '';
            
            Object.entries(streams).forEach(([service, info]) => {
                if (service === 'dead_letter') {
                    document.getElementById('deadLetterCount').textContent = info.length || 0;
                    return;
                }
                
                const li = document.createElement('li');
                li.className = 'stream-item';
                li.innerHTML = `
                    <div class="stream-name">${service}</div>
                    <div class="stream-stats">
                        Messages: ${info.length || 0} | 
                        Groups: ${info.consumer_groups ? info.consumer_groups.length : 0}
                    </div>
                `;
                li.onclick = () => loadStreamDetails(service);
                streamsList.appendChild(li);
            });
        }
        
        function updateMetricsDisplay(metrics) {
            document.getElementById('opsPerSec').textContent = metrics.performance?.instantaneous_ops_per_sec || 0;
            document.getElementById('connectedClients').textContent = metrics.connections?.connected_clients || 0;
            document.getElementById('memoryUsed').textContent = metrics.memory?.used_memory_human || '0B';
            document.getElementById('hitRatio').textContent = (metrics.performance?.hit_ratio || 0) + '%';
        }
        
        function updateMetricsFromWebSocket(metrics) {
            document.getElementById('opsPerSec').textContent = metrics.ops_per_sec || 0;
            document.getElementById('connectedClients').textContent = metrics.connected_clients || 0;
            
            if (metrics.used_memory) {
                const mb = Math.round(metrics.used_memory / 1024 / 1024);
                document.getElementById('memoryUsed').textContent = mb + 'MB';
            }
        }
        
        async function loadStreamDetails(stream) {
            try {
                const response = await fetch(`/api/stream/${stream}`);
                const data = await response.json();
                
                const detailsDiv = document.getElementById('streamDetails');
                detailsDiv.innerHTML = `
                    <h4>Stream: ${stream}</h4>
                    <div class="metric">
                        <span class="metric-label">Total Messages:</span>
                        <span class="metric-value">${data.length || 0}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Consumer Groups:</span>
                        <span class="metric-value">${data.consumer_groups ? data.consumer_groups.length : 0}</span>
                    </div>
                    <h5>Recent Messages:</h5>
                    <div style="max-height: 300px; overflow-y: auto;">
                        ${data.recent_messages ? data.recent_messages.map(msg => `
                            <div style="border: 1px solid #ddd; margin: 0.5rem 0; padding: 0.5rem; border-radius: 4px;">
                                <strong>${msg.event_type}</strong> (${msg.priority})
                                <br><small>${msg.timestamp}</small>
                                <br><code>${JSON.stringify(msg.data, null, 2)}</code>
                            </div>
                        `).join('') : 'No recent messages'}
                    </div>
                `;
                
            } catch (error) {
                console.error('Error loading stream details:', error);
            }
        }
        
        // Initialize
        connectWebSocket();
    </script>
</body>
</html>
        """

async def main():
    """Main entry point"""
    uvloop.install()
    
    monitor = StreamsMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error("Monitor failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())