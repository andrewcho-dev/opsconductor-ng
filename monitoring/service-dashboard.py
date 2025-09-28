#!/usr/bin/env python3
"""
OpsConductor Service Monitoring Dashboard
Real-time monitoring of all services with bulletproof startup status
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import sys

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ServiceMonitorDashboard:
    def __init__(self):
        self.services = {
            "postgres": {"url": "http://localhost:5432", "type": "database"},
            "redis": {"url": "http://localhost:6379", "type": "cache"},
            "keycloak": {"url": "http://localhost:8090", "type": "auth"},
            "kong": {"url": "http://localhost:3000", "type": "gateway"},
            "identity-service": {"url": "http://localhost:3001", "type": "service"},
            "asset-service": {"url": "http://localhost:3002", "type": "service"},
            "automation-service": {"url": "http://localhost:3003", "type": "service"},
            "communication-service": {"url": "http://localhost:3004", "type": "service"},
            "frontend": {"url": "http://localhost:80", "type": "frontend"}
        }
        self.last_check = {}
        self.status_history = {}
    
    async def check_service_health(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single service"""
        result = {
            "name": name,
            "status": "unknown",
            "response_time": 0,
            "error": None,
            "details": {},
            "startup_status": None
        }
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try different health endpoints
                endpoints = ["/ready", "/health", "/health/ready", "/"]
                
                for endpoint in endpoints:
                    try:
                        url = f"{config['url']}{endpoint}"
                        async with session.get(url) as response:
                            response_time = (time.time() - start_time) * 1000
                            result["response_time"] = response_time
                            
                            if response.status == 200:
                                result["status"] = "healthy"
                                try:
                                    data = await response.json()
                                    result["details"] = data
                                except:
                                    result["details"] = {"text": await response.text()}
                                break
                            elif response.status == 503:
                                result["status"] = "starting"
                                try:
                                    data = await response.json()
                                    result["details"] = data
                                except:
                                    pass
                                break
                    except Exception as e:
                        continue
                
                # Try to get startup status if it's a service
                if config["type"] == "service" and result["status"] in ["healthy", "starting"]:
                    try:
                        startup_url = f"{config['url']}/startup-status"
                        async with session.get(startup_url) as response:
                            if response.status == 200:
                                result["startup_status"] = await response.json()
                    except:
                        pass
                
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "unhealthy"
            result["response_time"] = (time.time() - start_time) * 1000
        
        return result
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check all services concurrently"""
        tasks = []
        for name, config in self.services.items():
            tasks.append(self.check_service_health(name, config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        service_status = {}
        for result in results:
            if isinstance(result, dict):
                service_status[result["name"]] = result
            else:
                # Handle exceptions
                print(f"Error checking service: {result}")
        
        return service_status
    
    def get_status_icon(self, status: str) -> str:
        """Get colored status icon"""
        icons = {
            "healthy": f"{Colors.GREEN}●{Colors.END}",
            "starting": f"{Colors.YELLOW}●{Colors.END}",
            "unhealthy": f"{Colors.RED}●{Colors.END}",
            "unknown": f"{Colors.WHITE}●{Colors.END}"
        }
        return icons.get(status, f"{Colors.WHITE}?{Colors.END}")
    
    def format_response_time(self, ms: float) -> str:
        """Format response time with color coding"""
        if ms < 100:
            return f"{Colors.GREEN}{ms:.1f}ms{Colors.END}"
        elif ms < 500:
            return f"{Colors.YELLOW}{ms:.1f}ms{Colors.END}"
        else:
            return f"{Colors.RED}{ms:.1f}ms{Colors.END}"
    
    def print_service_status(self, status: Dict[str, Any]):
        """Print formatted service status"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"{Colors.BOLD}{Colors.CYAN}OpsConductor Service Monitor Dashboard{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Group services by type
        service_types = {
            "Infrastructure": ["postgres", "redis"],
            "Authentication": ["keycloak"],
            "Gateway": ["kong"],
            "Core Services": ["identity-service", "asset-service", "automation-service", "communication-service"],
            "Frontend": ["frontend"]
        }
        
        for category, service_names in service_types.items():
            print(f"{Colors.BOLD}{Colors.WHITE}{category}:{Colors.END}")
            
            for service_name in service_names:
                if service_name in status:
                    service = status[service_name]
                    icon = self.get_status_icon(service["status"])
                    response_time = self.format_response_time(service["response_time"])
                    
                    print(f"  {icon} {service_name:<20} {response_time}")
                    
                    # Show error if any
                    if service["error"]:
                        print(f"    {Colors.RED}Error: {service['error']}{Colors.END}")
                    
                    # Show startup status for services
                    if service.get("startup_status"):
                        startup = service["startup_status"]
                        state = startup.get("state", "unknown")
                        if state == "healthy":
                            state_color = Colors.GREEN
                        elif state in ["starting", "pending"]:
                            state_color = Colors.YELLOW
                        else:
                            state_color = Colors.RED
                        
                        print(f"    {Colors.BLUE}Startup: {state_color}{state}{Colors.END}")
                        
                        if startup.get("last_error"):
                            print(f"    {Colors.RED}Last Error: {startup['last_error']}{Colors.END}")
                        
                        # Show dependencies
                        deps = startup.get("dependencies", [])
                        if deps:
                            dep_names = [dep["name"] for dep in deps]
                            print(f"    {Colors.CYAN}Dependencies: {', '.join(dep_names)}{Colors.END}")
                else:
                    print(f"  {Colors.WHITE}?{Colors.END} {service_name:<20} {Colors.RED}Not checked{Colors.END}")
            
            print()
        
        # Overall system status
        healthy_count = sum(1 for s in status.values() if s["status"] == "healthy")
        total_count = len(status)
        
        if healthy_count == total_count:
            overall_color = Colors.GREEN
            overall_status = "ALL SYSTEMS OPERATIONAL"
        elif healthy_count > total_count * 0.7:
            overall_color = Colors.YELLOW
            overall_status = "SOME ISSUES DETECTED"
        else:
            overall_color = Colors.RED
            overall_status = "SYSTEM DEGRADED"
        
        print(f"{Colors.BOLD}{overall_color}{overall_status}{Colors.END}")
        print(f"Services: {Colors.GREEN}{healthy_count}{Colors.END}/{total_count} healthy")
        print()
        print(f"{Colors.CYAN}Press Ctrl+C to exit{Colors.END}")
    
    async def run_dashboard(self, interval: int = 5):
        """Run the monitoring dashboard"""
        print(f"{Colors.CYAN}Starting OpsConductor Service Monitor...{Colors.END}")
        
        try:
            while True:
                status = await self.check_all_services()
                self.print_service_status(status)
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.CYAN}Dashboard stopped.{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}Dashboard error: {e}{Colors.END}")

async def main():
    """Main function"""
    dashboard = ServiceMonitorDashboard()
    
    # Check if we should run once or continuously
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        status = await dashboard.check_all_services()
        dashboard.print_service_status(status)
    else:
        await dashboard.run_dashboard()

if __name__ == "__main__":
    asyncio.run(main())