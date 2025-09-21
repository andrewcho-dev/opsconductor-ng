#!/usr/bin/env node

/**
 * AI Chat Stress Test Runner
 * 
 * This script will run comprehensive stress tests against the AI chat system
 * for several hours with progressively increasing complexity.
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class AIChatStressRunner {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || 'http://localhost:3100';
    this.maxDurationHours = options.maxDurationHours || 4;
    this.concurrentUsers = options.concurrentUsers || 1;
    this.questionIntervalMs = options.questionIntervalMs || 3000;
    
    this.totalQuestions = 0;
    this.successfulResponses = 0;
    this.errorResponses = 0;
    this.responseTimes = [];
    this.startTime = Date.now();
    this.currentLevel = 1;
    this.questionsPerLevel = 20;
    this.currentLevelCount = 0;
    
    // Create logs directory
    if (!fs.existsSync('logs')) {
      fs.mkdirSync('logs');
    }
    
    this.logFile = path.join('logs', `ai-chat-stress-${new Date().toISOString().slice(0,19).replace(/[:.]/g, '-')}.log`);
    this.authToken = null;
    
    this.setupAxios();
  }

  setupAxios() {
    this.api = axios.create({
      baseURL: this.baseUrl,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.api.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    console.log(logEntry);
    fs.appendFileSync(this.logFile, logEntry + '\n');
  }

  // Question banks organized by complexity level
  getQuestionBank() {
    return {
      1: [ // Basic IT Knowledge
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
      
      2: [ // Intermediate Multi-Component
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
      
      3: [ // Advanced Complex Scenarios  
        "A global e-commerce site has 500ms delays during peak hours across microservices with Kubernetes, Redis, PostgreSQL read replicas, and CDN. Users report checkout timeouts after 30s. How do you diagnose and resolve while maintaining 99.9% uptime?",
        "Design comprehensive security for healthcare org processing 100k+ patient records daily. Must comply with HIPAA, support multi-auth, implement zero-trust, provide audit logs, handle breach scenarios. Include network segmentation, encryption, automated threat detection.",
        "Financial trading firm needs sub-10ms latency migration of legacy monolith to cloud-native architecture processing 1M transactions/second during market hours. Design complete migration with data consistency, real-time replication, rollback procedures, performance monitoring.",
        "Implement disaster recovery for multinational corp with US/Europe/Asia datacenters. Handle regional failures, maintain data sovereignty, support RTO 4hrs/RPO 1hr, include automated failover with approval gates, cost optimization, regular DR testing.",
        "Streaming platform with 40% monthly growth needs to scale for 10M concurrent users with 4K video. Current architecture includes encoding pipelines, CDN, recommendation engines, analytics. Design scalable architecture with auto-scaling, cost optimization, global distribution."
      ],
      
      4: [ // Expert-Level Multi-Domain
        "Multinational bank implementing real-time fraud detection processing 500k transactions/second across 50 countries with local data residency laws, sub-50ms response times, legacy mainframe integration, explainable AI for regulatory compliance. Design complete architecture including data pipeline, ML models, edge processing, regulatory reporting, incident response.",
        "Design zero-downtime migration for social media platform with 1B users from monolith to event-driven microservices. Maintain real-time features (messaging, notifications, feeds), preserve data relationships, support gradual rollout with instant rollback, handle 2M concurrent users during migration.",
        "Space tech company needs satellite constellation management for 10k+ satellites processing telemetry real-time, handling intermittent connectivity, autonomous orbital adjustments, ground station coordination. Include redundancy, space-grade security, multi-country regulatory compliance.",
        "Architect quantum-resistant cryptographic infrastructure for critical national infrastructure. Support hybrid classical-quantum encryption, post-quantum algorithms, seamless key rotation across 100k+ devices, backward compatibility during transition, quantum key distribution networks."
      ],
      
      5: [ // Extreme Complexity - Automation Focus
        "Create comprehensive IT automation workflow that automatically detects, diagnoses, and remediates complex infrastructure issues across hybrid cloud. Handle network outages, database performance degradation, application crashes, security incidents, capacity planning. Include self-learning, approval workflows, rollback mechanisms, ITSM integration. Provide specific automation scripts.",
        "Design AI-powered infrastructure orchestration system that automatically provisions, scales, optimizes resources across multi-cloud based on predictive analytics, cost optimization, performance requirements, compliance constraints. Include IaC generation, automated testing, security policy enforcement, change management.",
        "Build fully automated datacenter migration system for 10k+ VMs from on-premises to cloud with zero downtime. Include dependency mapping, automated testing, rollback procedures, performance validation, compliance verification. System should adapt to issues and optimize migration path real-time.",
        "Develop autonomous incident response system detecting, classifying, responding to security incidents across multi-vendor environments. Integrate SIEM, threat intelligence, EDR, network monitoring. Include automated containment, evidence collection, threat hunting, regulatory notifications.",
        "Create intelligent capacity planning and resource optimization system for global cloud infrastructure predicting needs 6 months ahead, auto-negotiating vendor contracts, optimizing workload placement for cost/performance, just-in-time provisioning. Include carbon footprint optimization and sustainability metrics."
      ]
    };
  }

  // Get random question from current level
  getRandomQuestion() {
    const questionBank = this.getQuestionBank();
    const questions = questionBank[this.currentLevel];
    return questions[Math.floor(Math.random() * questions.length)];
  }

  // Attempt to authenticate
  async authenticate() {
    try {
      // Try common default credentials
      const credentials = [
        { email: 'admin@opsconductor.com', password: 'admin123' },
        { email: 'admin', password: 'admin123' },
        { username: 'admin', password: 'admin123' }
      ];

      for (const cred of credentials) {
        try {
          this.log(`Attempting authentication with ${JSON.stringify(cred)}`);
          const response = await this.api.post('/api/v1/auth/login', cred);
          
          if (response.data && response.data.access_token) {
            this.authToken = response.data.access_token;
            this.log('Successfully authenticated');
            return true;
          }
        } catch (error) {
          this.log(`Auth attempt failed: ${error.message}`);
          continue;
        }
      }
      
      this.log('All authentication attempts failed. Proceeding without auth (some features may not work).');
      return false;
    } catch (error) {
      this.log(`Authentication error: ${error.message}`);
      return false;
    }
  }

  // Send a chat message
  async sendChatMessage(message, conversationId = null) {
    const startTime = Date.now();
    
    try {
      const request = {
        message: message,
        user_id: 1,
        ...(conversationId && { conversation_id: conversationId })
      };

      const response = await this.api.post('/api/v1/ai/chat', request);
      const responseTime = Date.now() - startTime;
      
      this.responseTimes.push(responseTime);
      this.totalQuestions++;
      this.successfulResponses++;

      const result = {
        success: true,
        responseTime,
        question: message,
        response: response.data.response,
        level: this.currentLevel
      };

      this.log(`Q${this.totalQuestions} [L${this.currentLevel}] (${responseTime}ms): ${message.substring(0, 100)}...`);
      this.log(`A${this.totalQuestions}: ${response.data.response?.substring(0, 150) || 'No response'}...`);

      return result;

    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.totalQuestions++;
      this.errorResponses++;
      
      this.log(`FAILED Q${this.totalQuestions} [L${this.currentLevel}] (${responseTime}ms): ${error.message}`, 'error');
      
      return {
        success: false,
        responseTime,
        error: error.message,
        question: message,
        level: this.currentLevel
      };
    }
  }

  // Progress to next complexity level
  progressLevel() {
    if (this.currentLevel < 5) {
      this.currentLevel++;
      this.currentLevelCount = 0;
      
      // Reduce interval as complexity increases (more aggressive testing)
      this.questionIntervalMs = Math.max(1000, this.questionIntervalMs * 0.8);
      
      this.log(`🔥 PROGRESSING TO LEVEL ${this.currentLevel} - New interval: ${this.questionIntervalMs}ms`, 'info');
    } else {
      // At max level, reset counter but stay at level 5
      this.currentLevelCount = 0;
      this.log(`🚀 CONTINUING LEVEL 5 - MAXIMUM COMPLEXITY SUSTAINED`, 'info');
    }
  }

  // Generate and display statistics
  generateStats() {
    if (this.responseTimes.length === 0) return {};

    const avg = this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
    const min = Math.min(...this.responseTimes);
    const max = Math.max(...this.responseTimes);
    const runtime = (Date.now() - this.startTime) / (1000 * 60);
    const successRate = (this.successfulResponses / this.totalQuestions) * 100;

    return {
      totalQuestions: this.totalQuestions,
      successRate: successRate.toFixed(1),
      avgResponseTime: avg.toFixed(0),
      minResponseTime: min,
      maxResponseTime: max,
      runtimeMinutes: runtime.toFixed(1),
      currentLevel: this.currentLevel,
      questionsPerMinute: (this.totalQuestions / runtime).toFixed(1),
      errorCount: this.errorResponses
    };
  }

  // Print status update
  printStatus() {
    const stats = this.generateStats();
    
    console.log('\n' + '='.repeat(100));
    console.log(`🤖 AI CHAT STRESS TEST STATUS - Level ${stats.currentLevel}`);
    console.log('='.repeat(100));
    console.log(`📊 Questions: ${stats.totalQuestions} | Success Rate: ${stats.successRate}% | Errors: ${stats.errorCount}`);
    console.log(`⚡ Response Times: Avg ${stats.avgResponseTime}ms | Min ${stats.minResponseTime}ms | Max ${stats.maxResponseTime}ms`);
    console.log(`⏱️  Runtime: ${stats.runtimeMinutes} minutes | Rate: ${stats.questionsPerMinute} Q/min`);
    console.log('='.repeat(100) + '\n');
  }

  // Main execution loop
  async runStressTest() {
    console.log('\n🚀 STARTING AI CHAT BOMBARDMENT STRESS TEST');
    console.log(`⏱️  Duration: ${this.maxDurationHours} hours`);
    console.log(`🎯 Target: ${this.baseUrl}`);
    console.log(`📈 Progressive complexity: 5 levels`);
    
    // Try to authenticate
    await this.authenticate();
    
    const maxDuration = this.maxDurationHours * 60 * 60 * 1000;
    let lastStatusUpdate = Date.now();
    const statusInterval = 2 * 60 * 1000; // Status every 2 minutes
    
    this.log(`Starting ${this.maxDurationHours}-hour bombardment test`);
    
    while (Date.now() - this.startTime < maxDuration) {
      try {
        // Get random question for current level
        const question = this.getRandomQuestion();
        
        // Send the question
        await this.sendChatMessage(question);
        
        // Track level progression
        this.currentLevelCount++;
        if (this.currentLevelCount >= this.questionsPerLevel) {
          this.progressLevel();
        }
        
        // Status updates
        if (Date.now() - lastStatusUpdate > statusInterval) {
          this.printStatus();
          lastStatusUpdate = Date.now();
        }
        
        // Variable delay with randomization to simulate realistic usage
        const jitter = Math.random() * 2000; // Up to 2s random delay
        const delay = this.questionIntervalMs + jitter;
        await new Promise(resolve => setTimeout(resolve, delay));
        
      } catch (error) {
        this.log(`Main loop error: ${error.message}`, 'error');
        // Brief pause on errors
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
    
    // Final results
    console.log('\n🏁 STRESS TEST COMPLETED!');
    this.printStatus();
    
    // Save detailed results
    const finalStats = this.generateStats();
    const resultsFile = path.join('logs', `ai-chat-final-results-${new Date().toISOString().slice(0,19).replace(/[:.]/g, '-')}.json`);
    
    const fullResults = {
      testConfiguration: {
        duration: this.maxDurationHours,
        baseUrl: this.baseUrl,
        questionsPerLevel: this.questionsPerLevel
      },
      finalStats: finalStats,
      rawResponseTimes: this.responseTimes
    };
    
    fs.writeFileSync(resultsFile, JSON.stringify(fullResults, null, 2));
    this.log(`📁 Final results saved to: ${resultsFile}`);
    
    return finalStats;
  }
}

// CLI Interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};
  
  // Parse command line arguments
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace('--', '');
    const value = args[i + 1];
    
    if (key === 'duration') options.maxDurationHours = parseFloat(value);
    if (key === 'url') options.baseUrl = value;
    if (key === 'interval') options.questionIntervalMs = parseInt(value);
  }
  
  console.log('🤖 AI Chat Stress Test Configuration:');
  console.log(`   Duration: ${options.maxDurationHours || 4} hours`);
  console.log(`   URL: ${options.baseUrl || 'http://localhost:3100'}`);
  console.log(`   Interval: ${options.questionIntervalMs || 3000}ms`);
  console.log('\nStarting in 3 seconds...\n');
  
  setTimeout(() => {
    const runner = new AIChatStressRunner(options);
    runner.runStressTest().catch(console.error);
  }, 3000);
}

module.exports = AIChatStressRunner;