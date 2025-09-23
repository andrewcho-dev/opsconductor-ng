"""
Phase 3 Learning Integration Test
Tests the external knowledge integration and learning effectiveness monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import the new learning components
from learning.external_knowledge_integrator import ExternalKnowledgeIntegrator
from learning.learning_effectiveness_monitor import (
    LearningEffectivenessMonitor, 
    LearningMetricType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3LearningIntegrationTest:
    """Test suite for Phase 3 learning integration components"""
    
    def __init__(self):
        self.test_results = []
        self.knowledge_integrator = ExternalKnowledgeIntegrator()
        self.effectiveness_monitor = LearningEffectivenessMonitor()
    
    async def test_external_knowledge_integration(self):
        """Test external knowledge integration capabilities"""
        logger.info("🔍 Testing External Knowledge Integration...")
        
        try:
            # Test security advisories integration
            advisories = await self.knowledge_integrator.integrate_security_advisories()
            
            success = (
                len(advisories) > 0 and
                all(hasattr(advisory, 'id') for advisory in advisories) and
                all(hasattr(advisory, 'severity') for advisory in advisories) and
                all(hasattr(advisory, 'mitigation_steps') for advisory in advisories)
            )
            
            self.test_results.append({
                "test": "Security Advisories Integration",
                "success": success,
                "advisories_count": len(advisories),
                "details": f"Integrated {len(advisories)} security advisories"
            })
            
            logger.info(f"✅ Security Advisories: {len(advisories)} integrated")
            
        except Exception as e:
            self.test_results.append({
                "test": "Security Advisories Integration",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Security Advisories Integration failed: {e}")
    
    async def test_best_practices_integration(self):
        """Test best practices integration"""
        logger.info("📚 Testing Best Practices Integration...")
        
        try:
            practices = await self.knowledge_integrator.integrate_best_practices()
            
            success = (
                len(practices) > 0 and
                all(hasattr(practice, 'domain') for practice in practices) and
                all(hasattr(practice, 'implementation_steps') for practice in practices) and
                all(len(practice.implementation_steps) > 0 for practice in practices)
            )
            
            self.test_results.append({
                "test": "Best Practices Integration",
                "success": success,
                "practices_count": len(practices),
                "domains": list(set(practice.domain for practice in practices)),
                "details": f"Integrated {len(practices)} best practices"
            })
            
            logger.info(f"✅ Best Practices: {len(practices)} integrated")
            
        except Exception as e:
            self.test_results.append({
                "test": "Best Practices Integration",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Best Practices Integration failed: {e}")
    
    async def test_community_knowledge_integration(self):
        """Test community knowledge integration"""
        logger.info("🌐 Testing Community Knowledge Integration...")
        
        try:
            community_data = await self.knowledge_integrator.integrate_community_knowledge()
            
            success = (
                isinstance(community_data, dict) and
                'trending_technologies' in community_data and
                'common_issues' in community_data and
                'emerging_patterns' in community_data and
                len(community_data['trending_technologies']) > 0
            )
            
            self.test_results.append({
                "test": "Community Knowledge Integration",
                "success": success,
                "trending_tech_count": len(community_data.get('trending_technologies', [])),
                "common_issues_count": len(community_data.get('common_issues', [])),
                "details": f"Integrated community knowledge with {len(community_data)} categories"
            })
            
            logger.info(f"✅ Community Knowledge: {len(community_data)} categories integrated")
            
        except Exception as e:
            self.test_results.append({
                "test": "Community Knowledge Integration",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Community Knowledge Integration failed: {e}")
    
    async def test_relevant_knowledge_retrieval(self):
        """Test relevant knowledge retrieval"""
        logger.info("🎯 Testing Relevant Knowledge Retrieval...")
        
        try:
            # First ensure we have some knowledge integrated
            await self.knowledge_integrator.integrate_security_advisories()
            await self.knowledge_integrator.integrate_best_practices()
            await self.knowledge_integrator.integrate_community_knowledge()
            
            # Test retrieval for different domains
            test_cases = [
                ("security", "implement zero trust security"),
                ("devops", "infrastructure as code best practices"),
                ("monitoring", "application performance monitoring setup")
            ]
            
            retrieval_results = []
            for domain, query_context in test_cases:
                relevant_knowledge = await self.knowledge_integrator.get_relevant_knowledge(domain, query_context)
                
                has_relevant_data = (
                    len(relevant_knowledge.get('security_advisories', [])) > 0 or
                    len(relevant_knowledge.get('best_practices', [])) > 0 or
                    len(relevant_knowledge.get('community_insights', {}).get('trending_technologies', [])) > 0
                )
                
                retrieval_results.append({
                    'domain': domain,
                    'query_context': query_context,
                    'has_relevant_data': has_relevant_data,
                    'security_advisories_count': len(relevant_knowledge.get('security_advisories', [])),
                    'best_practices_count': len(relevant_knowledge.get('best_practices', [])),
                    'community_insights': bool(relevant_knowledge.get('community_insights'))
                })
            
            success = any(result['has_relevant_data'] for result in retrieval_results)
            
            self.test_results.append({
                "test": "Relevant Knowledge Retrieval",
                "success": success,
                "test_cases": len(test_cases),
                "successful_retrievals": sum(1 for r in retrieval_results if r['has_relevant_data']),
                "details": retrieval_results
            })
            
            logger.info(f"✅ Knowledge Retrieval: {sum(1 for r in retrieval_results if r['has_relevant_data'])}/{len(test_cases)} successful")
            
        except Exception as e:
            self.test_results.append({
                "test": "Relevant Knowledge Retrieval",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Relevant Knowledge Retrieval failed: {e}")
    
    def test_learning_effectiveness_monitoring(self):
        """Test learning effectiveness monitoring"""
        logger.info("📊 Testing Learning Effectiveness Monitoring...")
        
        try:
            # Set baseline metrics
            test_domains = ["security", "devops", "monitoring"]
            for domain in test_domains:
                self.effectiveness_monitor.set_baseline_metric(
                    domain, LearningMetricType.CONFIDENCE_IMPROVEMENT, 0.6
                )
                self.effectiveness_monitor.set_baseline_metric(
                    domain, LearningMetricType.ACCURACY_IMPROVEMENT, 0.7
                )
            
            # Record some learning metrics
            for domain in test_domains:
                # Simulate learning improvements
                self.effectiveness_monitor.record_learning_metric(
                    LearningMetricType.CONFIDENCE_IMPROVEMENT,
                    domain,
                    0.75,  # Improved from baseline of 0.6
                    {"test_context": "simulated_learning"}
                )
                
                self.effectiveness_monitor.record_learning_metric(
                    LearningMetricType.ACCURACY_IMPROVEMENT,
                    domain,
                    0.82,  # Improved from baseline of 0.7
                    {"test_context": "simulated_learning"}
                )
            
            # Test learning session tracking
            session_id = self.effectiveness_monitor.start_learning_session("security")
            self.effectiveness_monitor.end_learning_session(
                session_id,
                interactions_count=10,
                successful_interactions=8,
                average_confidence=0.78,
                knowledge_items_learned=5
            )
            
            # Calculate domain effectiveness
            effectiveness_results = []
            for domain in test_domains:
                domain_effectiveness = self.effectiveness_monitor.calculate_domain_effectiveness(domain)
                effectiveness_results.append(domain_effectiveness)
            
            success = (
                len(effectiveness_results) == len(test_domains) and
                all(result['effectiveness_score'] > 0 for result in effectiveness_results) and
                all(result['metrics_count'] > 0 for result in effectiveness_results)
            )
            
            self.test_results.append({
                "test": "Learning Effectiveness Monitoring",
                "success": success,
                "domains_tested": len(test_domains),
                "avg_effectiveness_score": sum(r['effectiveness_score'] for r in effectiveness_results) / len(effectiveness_results),
                "details": effectiveness_results
            })
            
            logger.info(f"✅ Learning Effectiveness: {len(test_domains)} domains monitored")
            
        except Exception as e:
            self.test_results.append({
                "test": "Learning Effectiveness Monitoring",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Learning Effectiveness Monitoring failed: {e}")
    
    def test_effectiveness_reporting(self):
        """Test effectiveness reporting"""
        logger.info("📋 Testing Effectiveness Reporting...")
        
        try:
            # Generate effectiveness report
            report = self.effectiveness_monitor.generate_effectiveness_report(time_period_days=1)
            
            success = (
                hasattr(report, 'report_id') and
                hasattr(report, 'overall_effectiveness_score') and
                hasattr(report, 'domain_scores') and
                hasattr(report, 'recommendations') and
                len(report.domain_scores) > 0
            )
            
            self.test_results.append({
                "test": "Effectiveness Reporting",
                "success": success,
                "report_id": report.report_id,
                "overall_score": report.overall_effectiveness_score,
                "domains_in_report": len(report.domain_scores),
                "recommendations_count": len(report.recommendations),
                "details": f"Generated report with {len(report.domain_scores)} domains"
            })
            
            logger.info(f"✅ Effectiveness Report: {report.report_id} generated")
            
        except Exception as e:
            self.test_results.append({
                "test": "Effectiveness Reporting",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Effectiveness Reporting failed: {e}")
    
    def test_learning_trends_analysis(self):
        """Test learning trends analysis"""
        logger.info("📈 Testing Learning Trends Analysis...")
        
        try:
            # Test trends for different domains and metrics
            trend_results = []
            test_cases = [
                ("security", LearningMetricType.CONFIDENCE_IMPROVEMENT),
                ("devops", LearningMetricType.ACCURACY_IMPROVEMENT),
                ("monitoring", LearningMetricType.CONFIDENCE_IMPROVEMENT)
            ]
            
            for domain, metric_type in test_cases:
                trends = self.effectiveness_monitor.get_learning_trends(domain, metric_type, time_period_days=1)
                trend_results.append(trends)
            
            success = (
                len(trend_results) == len(test_cases) and
                all('trend' in result for result in trend_results) and
                all('domain' in result for result in trend_results)
            )
            
            self.test_results.append({
                "test": "Learning Trends Analysis",
                "success": success,
                "trends_analyzed": len(trend_results),
                "details": trend_results
            })
            
            logger.info(f"✅ Learning Trends: {len(trend_results)} trend analyses completed")
            
        except Exception as e:
            self.test_results.append({
                "test": "Learning Trends Analysis",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Learning Trends Analysis failed: {e}")
    
    def test_cross_domain_learning_analysis(self):
        """Test cross-domain learning analysis"""
        logger.info("🔄 Testing Cross-Domain Learning Analysis...")
        
        try:
            analysis = self.effectiveness_monitor.get_cross_domain_learning_analysis()
            
            success = (
                isinstance(analysis, dict) and
                'analysis' in analysis and
                ('domains_analyzed' in analysis or 'message' in analysis)
            )
            
            self.test_results.append({
                "test": "Cross-Domain Learning Analysis",
                "success": success,
                "analysis_status": analysis.get('analysis', 'unknown'),
                "domains_analyzed": analysis.get('domains_analyzed', 0),
                "transfer_patterns": len(analysis.get('transfer_patterns', [])),
                "details": analysis
            })
            
            logger.info(f"✅ Cross-Domain Analysis: {analysis.get('analysis', 'completed')}")
            
        except Exception as e:
            self.test_results.append({
                "test": "Cross-Domain Learning Analysis",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Cross-Domain Learning Analysis failed: {e}")
    
    async def run_all_tests(self):
        """Run all Phase 3 learning integration tests"""
        logger.info("🧠 AI-Intent-Based Strategy - Phase 3 Learning Integration Test")
        logger.info("External Knowledge Integration & Learning Effectiveness Monitoring")
        logger.info("=" * 80)
        logger.info("🚀 Starting Phase 3 Learning Integration Tests")
        logger.info("=" * 80)
        
        # Run external knowledge integration tests
        await self.test_external_knowledge_integration()
        await self.test_best_practices_integration()
        await self.test_community_knowledge_integration()
        await self.test_relevant_knowledge_retrieval()
        
        # Run learning effectiveness monitoring tests
        self.test_learning_effectiveness_monitoring()
        self.test_effectiveness_reporting()
        self.test_learning_trends_analysis()
        self.test_cross_domain_learning_analysis()
        
        # Generate summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test summary"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("📋 PHASE 3 LEARNING INTEGRATION TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\n📊 Detailed Results:")
        logger.info("-" * 60)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}")
            if "details" in result and isinstance(result["details"], str):
                logger.info(f"    {result['details']}")
            elif "error" in result:
                logger.info(f"    Error: {result['error']}")
        
        # Feature validation summary
        logger.info("\n🎯 Phase 3 Learning Features Validated:")
        logger.info("-" * 60)
        
        feature_status = {
            "External Knowledge Integration": any("Knowledge Integration" in r["test"] for r in self.test_results if r["success"]),
            "Security Advisories Integration": any("Security Advisories" in r["test"] for r in self.test_results if r["success"]),
            "Best Practices Integration": any("Best Practices" in r["test"] for r in self.test_results if r["success"]),
            "Community Knowledge Integration": any("Community Knowledge" in r["test"] for r in self.test_results if r["success"]),
            "Learning Effectiveness Monitoring": any("Learning Effectiveness" in r["test"] for r in self.test_results if r["success"]),
            "Effectiveness Reporting": any("Effectiveness Reporting" in r["test"] for r in self.test_results if r["success"]),
            "Learning Trends Analysis": any("Learning Trends" in r["test"] for r in self.test_results if r["success"]),
            "Cross-Domain Learning Analysis": any("Cross-Domain" in r["test"] for r in self.test_results if r["success"])
        }
        
        for feature, validated in feature_status.items():
            status = "✅" if validated else "❌"
            logger.info(f"{status} {feature}")
        
        # Overall assessment
        if success_rate >= 90:
            logger.info(f"\n🎉 Phase 3 Learning Integration: EXCELLENT ({success_rate:.1f}% pass rate)")
        elif success_rate >= 75:
            logger.info(f"\n✅ Phase 3 Learning Integration: SUCCESSFUL ({success_rate:.1f}% pass rate)")
        elif success_rate >= 50:
            logger.info(f"\n⚠️  Phase 3 Learning Integration: PARTIAL ({success_rate:.1f}% pass rate)")
        else:
            logger.info(f"\n❌ Phase 3 Learning Integration: NEEDS WORK ({success_rate:.1f}% pass rate)")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"phase3_learning_test_results_{timestamp}.json"
        
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 3 - Learning Integration",
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "feature_validation": feature_status
        }
        
        try:
            with open(results_file, 'w') as f:
                json.dump(detailed_results, f, indent=2, default=str)
            logger.info(f"\n📄 Detailed results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

async def main():
    """Main test execution"""
    test_suite = Phase3LearningIntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())