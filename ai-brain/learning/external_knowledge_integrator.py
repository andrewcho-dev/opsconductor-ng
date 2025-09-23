"""
External Knowledge Integrator for AI-Intent-Based Strategy Phase 3
Integrates external knowledge sources into the SME brain system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SecurityAdvisory:
    """Security advisory data structure"""
    id: str
    title: str
    severity: str
    description: str
    affected_systems: List[str]
    mitigation_steps: List[str]
    published_date: datetime
    source: str

@dataclass
class BestPractice:
    """Best practice data structure"""
    id: str
    domain: str
    title: str
    description: str
    implementation_steps: List[str]
    benefits: List[str]
    updated_date: datetime
    source: str

@dataclass
class KnowledgeUpdate:
    """Knowledge update tracking"""
    source: str
    last_updated: datetime
    items_processed: int
    success_rate: float
    errors: List[str]

class ExternalKnowledgeIntegrator:
    """
    Integrates external knowledge sources into the SME brain system
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.knowledge_cache = {}
        self.update_history: List[KnowledgeUpdate] = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration for external knowledge sources"""
        default_config = {
            "security_sources": {
                "cve_api": "https://cve.circl.lu/api/",
                "nist_nvd": "https://services.nvd.nist.gov/rest/json/",
                "update_interval_hours": 24
            },
            "best_practices_sources": {
                "devops_practices": "internal://devops-knowledge-base",
                "security_practices": "internal://security-knowledge-base",
                "update_interval_hours": 168  # Weekly
            },
            "community_sources": {
                "github_advisories": "https://api.github.com/advisories",
                "stackoverflow_trends": "internal://stackoverflow-trends",
                "update_interval_hours": 72  # Every 3 days
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    async def integrate_security_advisories(self) -> List[SecurityAdvisory]:
        """
        Integrate latest security advisories from external sources
        """
        logger.info("🔒 Integrating security advisories...")
        
        advisories = []
        errors = []
        
        try:
            # Simulate CVE integration (in real implementation, would call actual APIs)
            mock_advisories = [
                SecurityAdvisory(
                    id="CVE-2024-0001",
                    title="Critical vulnerability in container runtime",
                    severity="CRITICAL",
                    description="Remote code execution vulnerability in container runtime",
                    affected_systems=["docker", "containerd", "kubernetes"],
                    mitigation_steps=[
                        "Update container runtime to latest version",
                        "Implement network segmentation",
                        "Enable security monitoring"
                    ],
                    published_date=datetime.now() - timedelta(days=1),
                    source="NVD"
                ),
                SecurityAdvisory(
                    id="CVE-2024-0002",
                    title="SQL injection vulnerability in web frameworks",
                    severity="HIGH",
                    description="SQL injection vulnerability affecting multiple web frameworks",
                    affected_systems=["django", "flask", "express"],
                    mitigation_steps=[
                        "Update framework to patched version",
                        "Implement input validation",
                        "Use parameterized queries"
                    ],
                    published_date=datetime.now() - timedelta(days=2),
                    source="GitHub Security Advisory"
                )
            ]
            
            advisories.extend(mock_advisories)
            
            # Cache the advisories
            self.knowledge_cache['security_advisories'] = {
                'data': advisories,
                'last_updated': datetime.now()
            }
            
            logger.info(f"✅ Integrated {len(advisories)} security advisories")
            
        except Exception as e:
            error_msg = f"Failed to integrate security advisories: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Record update history
        self.update_history.append(KnowledgeUpdate(
            source="security_advisories",
            last_updated=datetime.now(),
            items_processed=len(advisories),
            success_rate=1.0 if not errors else 0.0,
            errors=errors
        ))
        
        return advisories
    
    async def integrate_best_practices(self) -> List[BestPractice]:
        """
        Integrate evolving best practices from various sources
        """
        logger.info("📚 Integrating best practices...")
        
        best_practices = []
        errors = []
        
        try:
            # Simulate best practices integration
            mock_practices = [
                BestPractice(
                    id="BP-DEVOPS-001",
                    domain="devops",
                    title="Infrastructure as Code Best Practices",
                    description="Comprehensive guide for implementing Infrastructure as Code",
                    implementation_steps=[
                        "Choose appropriate IaC tool (Terraform, CloudFormation, etc.)",
                        "Implement version control for infrastructure code",
                        "Set up automated testing for infrastructure changes",
                        "Implement proper state management",
                        "Create modular and reusable infrastructure components"
                    ],
                    benefits=[
                        "Improved consistency and repeatability",
                        "Reduced manual errors",
                        "Better change tracking and rollback capabilities",
                        "Enhanced collaboration between teams"
                    ],
                    updated_date=datetime.now() - timedelta(days=7),
                    source="DevOps Community"
                ),
                BestPractice(
                    id="BP-SECURITY-001",
                    domain="security",
                    title="Zero Trust Security Implementation",
                    description="Best practices for implementing Zero Trust security model",
                    implementation_steps=[
                        "Implement identity verification for all users and devices",
                        "Apply least privilege access principles",
                        "Implement micro-segmentation",
                        "Enable continuous monitoring and analytics",
                        "Implement strong encryption for data in transit and at rest"
                    ],
                    benefits=[
                        "Reduced attack surface",
                        "Better visibility into network traffic",
                        "Improved compliance posture",
                        "Enhanced data protection"
                    ],
                    updated_date=datetime.now() - timedelta(days=3),
                    source="Security Community"
                ),
                BestPractice(
                    id="BP-MONITORING-001",
                    domain="monitoring",
                    title="Observability-Driven Development",
                    description="Best practices for implementing comprehensive observability",
                    implementation_steps=[
                        "Implement structured logging across all services",
                        "Set up distributed tracing for request flows",
                        "Create meaningful metrics and dashboards",
                        "Implement proactive alerting strategies",
                        "Establish SLIs and SLOs for critical services"
                    ],
                    benefits=[
                        "Faster incident resolution",
                        "Proactive issue detection",
                        "Better understanding of system behavior",
                        "Improved user experience"
                    ],
                    updated_date=datetime.now() - timedelta(days=5),
                    source="SRE Community"
                )
            ]
            
            best_practices.extend(mock_practices)
            
            # Cache the best practices
            self.knowledge_cache['best_practices'] = {
                'data': best_practices,
                'last_updated': datetime.now()
            }
            
            logger.info(f"✅ Integrated {len(best_practices)} best practices")
            
        except Exception as e:
            error_msg = f"Failed to integrate best practices: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Record update history
        self.update_history.append(KnowledgeUpdate(
            source="best_practices",
            last_updated=datetime.now(),
            items_processed=len(best_practices),
            success_rate=1.0 if not errors else 0.0,
            errors=errors
        ))
        
        return best_practices
    
    async def integrate_community_knowledge(self) -> Dict[str, Any]:
        """
        Integrate community knowledge from various sources
        """
        logger.info("🌐 Integrating community knowledge...")
        
        community_data = {}
        errors = []
        
        try:
            # Simulate community knowledge integration
            community_data = {
                "trending_technologies": [
                    {
                        "name": "Kubernetes",
                        "trend_score": 95,
                        "growth_rate": 15.2,
                        "community_size": 150000,
                        "key_discussions": [
                            "Service mesh adoption patterns",
                            "Multi-cluster management strategies",
                            "Security best practices"
                        ]
                    },
                    {
                        "name": "Terraform",
                        "trend_score": 88,
                        "growth_rate": 12.8,
                        "community_size": 85000,
                        "key_discussions": [
                            "State management strategies",
                            "Module design patterns",
                            "Cloud provider integrations"
                        ]
                    },
                    {
                        "name": "Prometheus",
                        "trend_score": 82,
                        "growth_rate": 10.5,
                        "community_size": 65000,
                        "key_discussions": [
                            "Alerting rule optimization",
                            "Long-term storage solutions",
                            "Federation strategies"
                        ]
                    }
                ],
                "common_issues": [
                    {
                        "category": "container_orchestration",
                        "issue": "Pod scheduling failures",
                        "frequency": 45,
                        "common_solutions": [
                            "Check resource requests and limits",
                            "Verify node capacity and taints",
                            "Review pod affinity rules"
                        ]
                    },
                    {
                        "category": "infrastructure_automation",
                        "issue": "Terraform state conflicts",
                        "frequency": 38,
                        "common_solutions": [
                            "Implement proper state locking",
                            "Use remote state backends",
                            "Coordinate team workflows"
                        ]
                    }
                ],
                "emerging_patterns": [
                    {
                        "pattern": "GitOps for infrastructure management",
                        "adoption_rate": 65,
                        "benefits": [
                            "Improved change tracking",
                            "Automated deployments",
                            "Better security posture"
                        ]
                    },
                    {
                        "pattern": "Platform engineering teams",
                        "adoption_rate": 58,
                        "benefits": [
                            "Standardized development workflows",
                            "Reduced cognitive load for developers",
                            "Improved operational efficiency"
                        ]
                    }
                ]
            }
            
            # Cache the community knowledge
            self.knowledge_cache['community_knowledge'] = {
                'data': community_data,
                'last_updated': datetime.now()
            }
            
            logger.info("✅ Integrated community knowledge successfully")
            
        except Exception as e:
            error_msg = f"Failed to integrate community knowledge: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Record update history
        self.update_history.append(KnowledgeUpdate(
            source="community_knowledge",
            last_updated=datetime.now(),
            items_processed=len(community_data),
            success_rate=1.0 if not errors else 0.0,
            errors=errors
        ))
        
        return community_data
    
    async def get_relevant_knowledge(self, domain: str, query_context: str) -> Dict[str, Any]:
        """
        Get relevant knowledge for a specific domain and context
        """
        relevant_knowledge = {
            "security_advisories": [],
            "best_practices": [],
            "community_insights": {}
        }
        
        # Get security advisories
        if 'security_advisories' in self.knowledge_cache:
            advisories = self.knowledge_cache['security_advisories']['data']
            relevant_knowledge['security_advisories'] = [
                advisory for advisory in advisories
                if domain.lower() in [system.lower() for system in advisory.affected_systems]
                or any(keyword in query_context.lower() for keyword in [advisory.title.lower(), advisory.description.lower()])
            ]
        
        # Get best practices
        if 'best_practices' in self.knowledge_cache:
            practices = self.knowledge_cache['best_practices']['data']
            relevant_knowledge['best_practices'] = [
                practice for practice in practices
                if practice.domain.lower() == domain.lower()
                or any(keyword in query_context.lower() for keyword in [practice.title.lower(), practice.description.lower()])
            ]
        
        # Get community insights
        if 'community_knowledge' in self.knowledge_cache:
            community_data = self.knowledge_cache['community_knowledge']['data']
            relevant_knowledge['community_insights'] = {
                "trending_technologies": [
                    tech for tech in community_data.get('trending_technologies', [])
                    if tech['name'].lower() in query_context.lower()
                ],
                "common_issues": [
                    issue for issue in community_data.get('common_issues', [])
                    if issue['category'].lower() == domain.lower()
                    or any(keyword in query_context.lower() for keyword in [issue['issue'].lower()])
                ]
            }
        
        return relevant_knowledge
    
    async def update_all_knowledge_sources(self) -> Dict[str, Any]:
        """
        Update all external knowledge sources
        """
        logger.info("🔄 Updating all external knowledge sources...")
        
        results = {}
        
        # Update security advisories
        try:
            advisories = await self.integrate_security_advisories()
            results['security_advisories'] = {
                'success': True,
                'count': len(advisories),
                'last_updated': datetime.now()
            }
        except Exception as e:
            results['security_advisories'] = {
                'success': False,
                'error': str(e),
                'last_updated': datetime.now()
            }
        
        # Update best practices
        try:
            practices = await self.integrate_best_practices()
            results['best_practices'] = {
                'success': True,
                'count': len(practices),
                'last_updated': datetime.now()
            }
        except Exception as e:
            results['best_practices'] = {
                'success': False,
                'error': str(e),
                'last_updated': datetime.now()
            }
        
        # Update community knowledge
        try:
            community_data = await self.integrate_community_knowledge()
            results['community_knowledge'] = {
                'success': True,
                'count': len(community_data),
                'last_updated': datetime.now()
            }
        except Exception as e:
            results['community_knowledge'] = {
                'success': False,
                'error': str(e),
                'last_updated': datetime.now()
            }
        
        logger.info("✅ External knowledge update completed")
        return results
    
    def get_update_history(self) -> List[KnowledgeUpdate]:
        """Get the history of knowledge updates"""
        return self.update_history
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get the current status of knowledge cache"""
        status = {}
        
        for source, cache_data in self.knowledge_cache.items():
            status[source] = {
                'last_updated': cache_data['last_updated'],
                'item_count': len(cache_data['data']) if isinstance(cache_data['data'], list) else 1,
                'age_hours': (datetime.now() - cache_data['last_updated']).total_seconds() / 3600
            }
        
        return status