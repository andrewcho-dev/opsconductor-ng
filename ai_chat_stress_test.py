#!/usr/bin/env python3
"""
OpsConductor AI Chat Stress Test Framework

This framework will test the AI chat functionality with:
1. Basic IT knowledge questions (Level 1)
2. Complex multi-tier scenarios (Level 2-5) 
3. Continuous load testing over several hours
4. Performance monitoring and response analysis
"""

import asyncio
import aiohttp
import json
import time
import random
import logging
import argparse
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

class AIChatStressTest:
    def __init__(self, base_url: str = "http://localhost:3100", duration_hours: float = 4.0, interval_ms: int = 3000):
        self.base_url = base_url.rstrip('/')
        self.duration_hours = duration_hours
        self.question_interval_ms = interval_ms
        self.max_duration_ms = duration_hours * 60 * 60 * 1000
        
        # Test state
        self.total_questions = 0
        self.successful_responses = 0
        self.error_responses = 0
        self.response_times = []
        self.conversation_ids = set()
        self.test_results = []
        self.start_time = time.time() * 1000
        
        # Progression system
        self.current_level = 1
        self.questions_per_level = 20
        self.current_level_count = 0
        
        # Auth
        self.auth_token = None
        self.session = None
        
        # Logging
        log_filename = f"ai_chat_stress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🚀 AI Chat Stress Test initialized")
        self.logger.info(f"   Target: {self.base_url}")
        self.logger.info(f"   Duration: {duration_hours} hours")
        self.logger.info(f"   Initial interval: {interval_ms}ms")
        self.logger.info(f"   Log file: {log_filename}")

    def get_question_bank(self) -> Dict[int, List[str]]:
        """Question banks organized by complexity level"""
        return {
            1: [  # Basic IT Knowledge
                "What is DNS?",
                "Explain what DHCP does",
                "What is the difference between TCP and UDP?",
                "How does SSH work?",
                "What is a firewall?",
                "Explain what NAT is",
                "What is a subnet mask?",
                "How does ARP work?",
                "What is VLAN?",
                "Explain what BGP does",
                "What is SNMP?",
                "How does VPN work?",
                "What is load balancing?",
                "Explain DNS caching",
                "What is port forwarding?",
                "How does RAID work?",
                "What is the OSI model?",
                "Explain what IPv6 is",
                "What is SSL/TLS?",
                "How does QoS work?"
            ],
            
            2: [  # Intermediate Multi-Component
                "How would you troubleshoot slow network performance affecting multiple VLANs?",
                "Design a secure network architecture for a 200-person company",
                "Explain how to implement high availability for a web application",
                "How would you migrate from IPv4 to IPv6 without downtime?",
                "Design a disaster recovery plan for critical systems",
                "How would you implement network segmentation for compliance?",
                "Explain setting up site-to-site VPN with redundancy",
                "How would you optimize database performance under high load?",
                "Design a monitoring solution for microservices architecture",
                "How would you implement zero-trust network security?",
                "Explain setting up automated backup strategies",
                "How would you design CI/CD pipeline with security scanning?",
                "Design a scalable logging and monitoring system",
                "How would you implement container orchestration with Kubernetes?",
                "Explain multi-region cloud architecture design"
            ],
            
            3: [  # Advanced Complex Scenarios  
                "A global e-commerce site has 500ms delays during peak hours across microservices with Kubernetes, Redis, PostgreSQL read replicas, and CDN. Users report checkout timeouts after 30s. How do you diagnose and resolve while maintaining 99.9% uptime?",
                "Design comprehensive security for healthcare org processing 100k+ patient records daily. Must comply with HIPAA, support multi-auth, implement zero-trust, provide audit logs, handle breach scenarios. Include network segmentation, encryption, automated threat detection.",
                "Financial trading firm needs sub-10ms latency migration of legacy monolith to cloud-native architecture processing 1M transactions/second during market hours. Design complete migration with data consistency, real-time replication, rollback procedures, performance monitoring.",
                "Implement disaster recovery for multinational corp with US/Europe/Asia datacenters. Handle regional failures, maintain data sovereignty, support RTO 4hrs/RPO 1hr, include automated failover with approval gates, cost optimization, regular DR testing.",
                "Streaming platform with 40% monthly growth needs to scale for 10M concurrent users with 4K video. Current architecture includes encoding pipelines, CDN, recommendation engines, analytics. Design scalable architecture with auto-scaling, cost optimization, global distribution."
            ],
            
            4: [  # Expert-Level Multi-Domain
                "Multinational bank implementing real-time fraud detection processing 500k transactions/second across 50 countries with local data residency laws, sub-50ms response times, legacy mainframe integration, explainable AI for regulatory compliance. Design complete architecture including data pipeline, ML models, edge processing, regulatory reporting, incident response.",
                "Design zero-downtime migration for social media platform with 1B users from monolith to event-driven microservices. Maintain real-time features (messaging, notifications, feeds), preserve data relationships, support gradual rollout with instant rollback, handle 2M concurrent users during migration.",
                "Space tech company needs satellite constellation management for 10k+ satellites processing telemetry real-time, handling intermittent connectivity, autonomous orbital adjustments, ground station coordination. Include redundancy, space-grade security, multi-country regulatory compliance.",
                "Architect quantum-resistant cryptographic infrastructure for critical national infrastructure. Support hybrid classical-quantum encryption, post-quantum algorithms, seamless key rotation across 100k+ devices, backward compatibility during transition, quantum key distribution networks."
            ],
            
            5: [  # Extreme Complexity - Automation Focus
                "Create comprehensive IT automation workflow that automatically detects, diagnoses, and remediates complex infrastructure issues across hybrid cloud. Handle network outages, database performance degradation, application crashes, security incidents, capacity planning. Include self-learning, approval workflows, rollback mechanisms, ITSM integration. Provide specific automation scripts.",
                "Design AI-powered infrastructure orchestration system that automatically provisions, scales, optimizes resources across multi-cloud based on predictive analytics, cost optimization, performance requirements, compliance constraints. Include IaC generation, automated testing, security policy enforcement, change management.",
                "Build fully automated datacenter migration system for 10k+ VMs from on-premises to cloud with zero downtime. Include dependency mapping, automated testing, rollback procedures, performance validation, compliance verification. System should adapt to issues and optimize migration path real-time.",
                "Develop autonomous incident response system detecting, classifying, responding to security incidents across multi-vendor environments. Integrate SIEM, threat intelligence, EDR, network monitoring. Include automated containment, evidence collection, threat hunting, regulatory notifications.",
                "Create intelligent capacity planning and resource optimization system for global cloud infrastructure predicting needs 6 months ahead, auto-negotiating vendor contracts, optimizing workload placement for cost/performance, just-in-time provisioning. Include carbon footprint optimization and sustainability metrics."
            ]
        }

    def get_random_question(self) -> str:
        """Get random question from current level"""
        question_bank = self.get_question_bank()
        questions = question_bank.get(self.current_level, question_bank[1])
        return random.choice(questions)

    async def authenticate(self) -> bool:
        """Attempt to authenticate with the system"""
        credentials = [
            {"email": "admin@opsconductor.com", "password": "admin123"},
            {"email": "admin", "password": "admin123"}, 
            {"username": "admin", "password": "admin123"}
        ]
        
        for cred in credentials:
            try:
                self.logger.info(f"Attempting authentication with {cred}")
                async with self.session.post(f"{self.base_url}/api/v1/auth/login", json=cred) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'access_token' in data:
                            self.auth_token = data['access_token']
                            self.logger.info("✅ Successfully authenticated")
                            return True
            except Exception as e:
                self.logger.warning(f"Auth attempt failed: {e}")
                continue
        
        self.logger.warning("⚠️  All authentication attempts failed. Proceeding without auth.")
        return False

    async def send_chat_message(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a single chat message"""
        start_time = time.time() * 1000
        
        try:
            # Prepare request
            request_data = {
                "message": message,
                "user_id": 1
            }
            if conversation_id:
                request_data["conversation_id"] = conversation_id
            
            # Set headers
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Send request
            async with self.session.post(
                f"{self.base_url}/api/v1/ai/chat", 
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                response_time = time.time() * 1000 - start_time
                self.response_times.append(response_time)
                self.total_questions += 1
                
                if response.status == 200:
                    data = await response.json()
                    self.successful_responses += 1
                    
                    # Store conversation ID
                    if 'conversation_id' in data:
                        self.conversation_ids.add(data['conversation_id'])
                    
                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "level": self.current_level,
                        "question": message,
                        "response": data.get("response", ""),
                        "response_time": response_time,
                        "success": True,
                        "conversation_id": data.get("conversation_id"),
                        "intent": data.get("intent"),
                        "confidence": data.get("confidence")
                    }
                    
                    self.test_results.append(result)
                    self.logger.info(f"Q{self.total_questions} [L{self.current_level}] ({response_time:.0f}ms): {message[:100]}...")
                    self.logger.info(f"A{self.total_questions}: {data.get('response', '')[:150]}...")
                    
                    return result
                else:
                    error_msg = f"HTTP {response.status}"
                    raise Exception(error_msg)
                    
        except Exception as e:
            response_time = time.time() * 1000 - start_time
            self.total_questions += 1
            self.error_responses += 1
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "level": self.current_level,
                "question": message,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }
            
            self.test_results.append(result)
            self.logger.error(f"❌ FAILED Q{self.total_questions} [L{self.current_level}] ({response_time:.0f}ms): {e}")
            
            return result

    def progress_level(self):
        """Progress to next complexity level"""
        if self.current_level < 5:
            self.current_level += 1
            self.current_level_count = 0
            
            # Reduce interval as complexity increases (more aggressive testing)
            self.question_interval_ms = max(1000, int(self.question_interval_ms * 0.8))
            
            self.logger.info(f"🔥 PROGRESSING TO LEVEL {self.current_level} - New interval: {self.question_interval_ms}ms")
        else:
            # At max level, reset counter but stay at level 5
            self.current_level_count = 0
            self.logger.info("🚀 CONTINUING LEVEL 5 - MAXIMUM COMPLEXITY SUSTAINED")

    def generate_stats(self) -> Dict[str, Any]:
        """Generate performance statistics"""
        if not self.response_times:
            return {}
        
        runtime_minutes = (time.time() * 1000 - self.start_time) / (1000 * 60)
        success_rate = (self.successful_responses / self.total_questions * 100) if self.total_questions > 0 else 0
        
        return {
            "total_questions": self.total_questions,
            "successful_responses": self.successful_responses, 
            "error_responses": self.error_responses,
            "success_rate": round(success_rate, 1),
            "avg_response_time": round(statistics.mean(self.response_times)),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "runtime_minutes": round(runtime_minutes, 1),
            "current_level": self.current_level,
            "conversation_count": len(self.conversation_ids),
            "questions_per_minute": round(self.total_questions / runtime_minutes, 1) if runtime_minutes > 0 else 0
        }

    def print_status(self):
        """Print status update"""
        stats = self.generate_stats()
        
        print("\n" + "="*100)
        print(f"🤖 AI CHAT STRESS TEST STATUS - Level {stats.get('current_level', 1)}")
        print("="*100)
        print(f"📊 Questions: {stats.get('total_questions', 0)} | Success Rate: {stats.get('success_rate', 0)}% | Errors: {stats.get('error_responses', 0)}")
        print(f"⚡ Response Times: Avg {stats.get('avg_response_time', 0)}ms | Min {stats.get('min_response_time', 0)}ms | Max {stats.get('max_response_time', 0)}ms")
        print(f"⏱️  Runtime: {stats.get('runtime_minutes', 0)} minutes | Rate: {stats.get('questions_per_minute', 0)} Q/min")
        print("="*100 + "\n")

    async def run_stress_test(self):
        """Main test execution loop"""
        print(f"\n🚀 STARTING AI CHAT BOMBARDMENT STRESS TEST")
        print(f"⏱️  Duration: {self.duration_hours} hours")
        print(f"🎯 Target: {self.base_url}")
        print(f"📈 Progressive complexity: 5 levels")
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        try:
            # Try to authenticate
            await self.authenticate()
            
            last_status_update = time.time() * 1000
            status_interval_ms = 2 * 60 * 1000  # Status every 2 minutes
            
            self.logger.info(f"Starting {self.duration_hours}-hour bombardment test")
            
            while (time.time() * 1000 - self.start_time) < self.max_duration_ms:
                try:
                    # Get random question for current level
                    question = self.get_random_question()
                    
                    # Send the question
                    await self.send_chat_message(question)
                    
                    # Track level progression
                    self.current_level_count += 1
                    if self.current_level_count >= self.questions_per_level:
                        self.progress_level()
                    
                    # Status updates
                    current_time = time.time() * 1000
                    if current_time - last_status_update > status_interval_ms:
                        self.print_status()
                        last_status_update = current_time
                    
                    # Variable delay with randomization
                    jitter = random.random() * 2000  # Up to 2s random delay
                    delay = (self.question_interval_ms + jitter) / 1000
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Main loop error: {e}")
                    await asyncio.sleep(5)  # Brief pause on errors
            
            # Final results
            print("\n🏁 STRESS TEST COMPLETED!")
            self.print_status()
            
            # Save detailed results
            final_stats = self.generate_stats()
            results_filename = f"ai_chat_final_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            full_results = {
                "test_configuration": {
                    "duration_hours": self.duration_hours,
                    "base_url": self.base_url,
                    "questions_per_level": self.questions_per_level
                },
                "final_stats": final_stats,
                "detailed_results": self.test_results[-100:] if len(self.test_results) > 100 else self.test_results  # Last 100 for size
            }
            
            with open(results_filename, 'w') as f:
                json.dump(full_results, f, indent=2)
            
            self.logger.info(f"📁 Final results saved to: {results_filename}")
            
            return final_stats
            
        finally:
            await self.session.close()

async def main():
    parser = argparse.ArgumentParser(description="AI Chat Stress Test")
    parser.add_argument('--url', default='http://localhost:3100', help='Base URL for API')
    parser.add_argument('--duration', type=float, default=4.0, help='Test duration in hours')
    parser.add_argument('--interval', type=int, default=3000, help='Initial interval between questions (ms)')
    
    args = parser.parse_args()
    
    print(f'🤖 AI Chat Stress Test Configuration:')
    print(f'   Duration: {args.duration} hours')
    print(f'   URL: {args.url}')
    print(f'   Interval: {args.interval}ms')
    print('\nStarting in 3 seconds...\n')
    
    await asyncio.sleep(3)
    
    tester = AIChatStressTest(
        base_url=args.url,
        duration_hours=args.duration,
        interval_ms=args.interval
    )
    
    await tester.run_stress_test()

if __name__ == "__main__":
    asyncio.run(main())