/**
 * OpsConductor AI Chat Stress Test Framework
 * 
 * This framework will test the AI chat functionality with:
 * 1. Basic IT knowledge questions (Level 1)
 * 2. Complex multi-tier scenarios (Level 2-5) 
 * 3. Continuous load testing over several hours
 * 4. Performance monitoring and response analysis
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class AIChatStressTester {
  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:3000';
    this.totalQuestions = 0;
    this.successfulResponses = 0;
    this.errorResponses = 0;
    this.responseTimes = [];
    this.conversationIds = new Set();
    this.testResults = [];
    this.startTime = Date.now();
    this.maxTestDurationHours = 4; // Run for 4 hours
    this.questionIntervalMs = 5000; // 5 seconds between questions initially
    this.currentLevel = 1;
    this.questionsPerLevel = 50;
    this.currentLevelCount = 0;
    this.logFile = `ai-chat-test-${new Date().toISOString().slice(0,19).replace(/[:.]/g, '-')}.log`;
    
    // Authentication token (you'll need to set this)
    this.authToken = null;
    
    // Initialize axios with interceptors
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

    // Request interceptor
    this.api.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });

    // Response interceptor for metrics
    this.api.interceptors.response.use(
      (response) => {
        this.successfulResponses++;
        return response;
      },
      (error) => {
        this.errorResponses++;
        this.log(`ERROR: ${error.message}`, 'error');
        return Promise.reject(error);
      }
    );
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
    
    console.log(logEntry.trim());
    fs.appendFileSync(this.logFile, logEntry);
  }

  // Level 1: Basic IT Knowledge Questions
  getBasicITQuestions() {
    return [
      "What is TCP/IP?",
      "Explain what DNS does",
      "What is the difference between HTTP and HTTPS?",
      "What is a firewall?",
      "How does SSH work?",
      "What is DHCP?",
      "Explain what a subnet mask is",
      "What is the purpose of NAT?",
      "What is RAID?",
      "Explain what a VPN is",
      "What is the difference between a hub and a switch?",
      "What is ARP?",
      "Explain what BGP is",
      "What is SNMP?",
      "What is the difference between TCP and UDP?",
      "What is a proxy server?",
      "Explain what load balancing is",
      "What is DNS caching?",
      "What is port forwarding?",
      "Explain what VLAN is",
      "What is the OSI model?",
      "What is IPv6?",
      "Explain what SSL/TLS is",
      "What is a DMZ?",
      "What is network segmentation?",
      "Explain what QoS is",
      "What is ICMP?",
      "What is the difference between routing and switching?",
      "What is a MAC address?",
      "Explain what NTP is",
      "What is bandwidth vs throughput?",
      "What is network latency?",
      "Explain what a CDN is",
      "What is packet loss?",
      "What is network topology?",
      "Explain what multicast is",
      "What is a network gateway?",
      "What is the purpose of spanning tree protocol?",
      "Explain what MPLS is",
      "What is network redundancy?",
      "What is the difference between Layer 2 and Layer 3 switching?",
      "What is OSPF?",
      "Explain what EIGRP is",
      "What is a routing table?",
      "What is network convergence?",
      "Explain what HSRP is",
      "What is VRRP?",
      "What is link aggregation?",
      "Explain what PoE is",
      "What is jumbo frames?"
    ];
  }

  // Level 2: Intermediate Multi-Component Questions
  getIntermediateQuestions() {
    return [
      "How would you troubleshoot a slow network connection that affects multiple users in different VLANs?",
      "Design a network architecture for a company with 500 employees across 3 locations",
      "Explain how to implement high availability for a web application with database backend",
      "What steps would you take to secure a corporate network against external threats?",
      "How would you migrate a company from IPv4 to IPv6 without service disruption?",
      "Design a disaster recovery plan for a data center with critical business applications",
      "How would you implement QoS policies to prioritize voice traffic over data traffic?",
      "Explain the process of setting up a site-to-site VPN between two branch offices",
      "How would you design a scalable monitoring solution for a multi-tier application?",
      "What approach would you use to segment a network for PCI compliance?",
      "How would you implement zero-trust network architecture for a remote workforce?",
      "Design a backup strategy for a hybrid cloud environment",
      "Explain how to set up automated failover for a critical database server",
      "How would you optimize network performance for a video streaming service?",
      "Design a security incident response plan for a financial services company",
      "How would you implement container orchestration with Kubernetes for high availability?",
      "Explain the process of migrating applications to microservices architecture",
      "How would you design a CI/CD pipeline with automated testing and deployment?",
      "What steps would you take to implement infrastructure as code using Terraform?",
      "How would you set up centralized logging and monitoring using ELK stack?",
      "Design a multi-region AWS architecture for a global e-commerce platform",
      "Explain how to implement database sharding for a high-traffic application",
      "How would you design a secure API gateway for microservices?",
      "What approach would you use for blue-green deployments in production?",
      "How would you implement automated security scanning in your CI/CD pipeline?",
      "Design a cost-optimization strategy for cloud infrastructure",
      "Explain how to set up cross-region database replication with failover",
      "How would you implement service mesh architecture using Istio?",
      "Design a data pipeline for real-time analytics using Kafka and Spark",
      "How would you set up automated backup and recovery for Kubernetes stateful applications?"
    ];
  }

  // Level 3: Advanced Complex Scenarios
  getAdvancedQuestions() {
    return [
      "A global e-commerce platform is experiencing intermittent 500ms response delays during peak hours across multiple regions. The application uses microservices architecture with Kubernetes, Redis caching, PostgreSQL with read replicas, and CDN. Users report that checkout processes sometimes timeout after 30 seconds. How would you systematically diagnose and resolve this issue while maintaining 99.9% uptime?",
      "Design and implement a comprehensive security framework for a healthcare organization processing 100,000+ patient records daily. The solution must comply with HIPAA, support multiple authentication methods, implement zero-trust principles, provide audit logging, and handle data breach scenarios. Include network segmentation, encryption at rest and in transit, and automated threat detection.",
      "A financial trading firm needs to migrate their legacy monolithic trading system to a cloud-native architecture while maintaining sub-10ms latency requirements and 99.99% availability. The system processes 1 million transactions per second during market hours. Design a complete migration strategy including data consistency, real-time replication, rollback procedures, and performance monitoring.",
      "Implement a disaster recovery solution for a multinational corporation with data centers in US, Europe, and Asia. The solution must handle regional failures, maintain data sovereignty compliance, support RTO of 4 hours and RPO of 1 hour, and include automated failover with manual approval gates for critical systems. Include cost optimization and regular disaster recovery testing.",
      "A streaming media platform experiencing 40% growth month-over-month needs to scale their infrastructure to handle 10 million concurrent users with 4K video streaming. Current architecture includes video encoding pipelines, content delivery networks, recommendation engines, and user analytics. Design a scalable architecture with auto-scaling, cost optimization, and global content distribution.",
      "Design a comprehensive DevSecOps pipeline for a government contractor that must comply with FedRAMP requirements. The pipeline must include automated security scanning, SAST/DAST tools, infrastructure compliance checking, secrets management, and automated deployment to multiple classification levels. Include approval workflows and audit trails.",
      "A SaaS company with 50,000+ customers needs to implement multi-tenancy with data isolation, custom branding, and tenant-specific configurations while maintaining a single codebase. The solution must support horizontal scaling, backup isolation per tenant, and comply with GDPR data residency requirements across multiple regions.",
      "Implement a real-time fraud detection system for a payment processor handling 100,000 transactions per minute. The system must integrate with multiple data sources, use machine learning models, provide real-time scoring, maintain low latency, and include manual review workflows for flagged transactions. Include A/B testing for model improvements.",
      "Design a hybrid cloud architecture for a manufacturing company that needs to integrate IoT sensors from 200+ factories worldwide with cloud-based analytics while maintaining local processing capabilities. Include edge computing, data aggregation, real-time alerting, and compliance with industrial security standards.",
      "A telecommunications company needs to implement network function virtualization (NFV) to replace physical network appliances with software-based solutions. Design a complete SDN architecture with orchestration, service chaining, performance monitoring, and migration strategy from physical to virtual network functions while maintaining carrier-grade reliability."
    ];
  }

  // Level 4: Expert-Level Multi-Domain Questions
  getExpertQuestions() {
    return [
      "A multinational bank is implementing a real-time fraud detection system that must process 500,000 transactions per second across 50 countries while complying with local data residency laws, maintaining sub-50ms response times, integrating with legacy mainframe systems, and providing explainable AI decisions for regulatory compliance. Design the complete architecture including data pipeline, ML models, edge processing, regulatory reporting, and incident response procedures.",
      "Design and implement a zero-downtime migration strategy for a social media platform with 1 billion users from a monolithic architecture to event-driven microservices. The migration must maintain real-time features (messaging, notifications, feeds), preserve all user data relationships, support gradual rollout with instant rollback capability, and handle peak traffic of 2 million concurrent users during the migration.",
      "A space technology company needs to design a satellite constellation management system that coordinates 10,000+ satellites, processes telemetry data in real-time, handles intermittent connectivity, implements autonomous decision-making for orbital adjustments, and provides ground station coordination. Include redundancy, space-grade security, and regulatory compliance for multiple countries.",
      "Architect a quantum-resistant cryptographic infrastructure for a critical national infrastructure provider. The solution must support hybrid classical-quantum encryption, implement post-quantum cryptographic algorithms, provide seamless key rotation across 100,000+ devices, maintain backward compatibility during the transition period, and include quantum key distribution networks.",
      "Design a global content delivery and edge computing platform that can dynamically optimize content delivery based on user behavior, network conditions, and geographic regulations. The system must support real-time personalization for 500 million users, handle massive traffic spikes during global events, implement intelligent caching strategies, and provide developers with a unified API for edge functions.",
      "A healthcare consortium needs to implement a federated learning system across 1,000+ hospitals for COVID-19 research while maintaining patient privacy, complying with HIPAA/GDPR, supporting different EHR systems, providing differential privacy guarantees, and enabling real-time model updates. Include data quality validation, bias detection, and regulatory approval workflows.",
      "Design a comprehensive cybersecurity framework for a smart city initiative covering 50+ different IoT device types, critical infrastructure systems, citizen services applications, and emergency response systems. The solution must provide real-time threat detection, automated incident response, privacy protection for citizen data, and resilience against state-level cyber attacks.",
      "Implement an autonomous trading system for a hedge fund that can analyze market conditions across global exchanges, execute complex multi-asset strategies, manage risk in real-time, comply with financial regulations in different jurisdictions, and adapt to changing market conditions using reinforcement learning. Include backtesting infrastructure and regulatory reporting.",
      "A global logistics company needs to optimize delivery routes for 100,000+ vehicles across 200 countries using real-time traffic data, weather conditions, customs information, and customer preferences. The system must integrate with existing ERP systems, provide carbon footprint optimization, handle supply chain disruptions, and support autonomous vehicle integration.",
      "Design a digital twin platform for a smart manufacturing ecosystem that can simulate and optimize production across 500+ factories worldwide. The platform must integrate with industrial IoT sensors, support predictive maintenance, optimize supply chains in real-time, comply with environmental regulations, and enable virtual factory design and testing."
    ];
  }

  // Level 5: Extreme Complexity - AI/Automation Focused
  getExtremeQuestions() {
    return [
      "Create a comprehensive IT automation workflow that can automatically detect, diagnose, and remediate complex infrastructure issues across hybrid cloud environments. The system should handle network outages, database performance degradation, application crashes, security incidents, and capacity planning. Include self-learning capabilities, approval workflows for critical changes, rollback mechanisms, and integration with existing ITSM tools. Provide specific automation scripts for common scenarios.",
      "Design and implement an AI-powered infrastructure orchestration system that can automatically provision, scale, and optimize resources across multiple cloud providers based on predictive analytics, cost optimization, performance requirements, and compliance constraints. Include infrastructure as code generation, automated testing, security policy enforcement, and change management workflows.",
      "Build a fully automated datacenter migration system that can assess, plan, and execute the migration of 10,000+ virtual machines and associated services from on-premises to cloud with zero downtime. Include dependency mapping, automated testing, rollback procedures, performance validation, and compliance verification. The system should adapt to unexpected issues and optimize the migration path in real-time.",
      "Develop an autonomous incident response system that can detect, classify, and respond to security incidents across complex multi-vendor environments. The system should integrate with SIEM tools, threat intelligence feeds, endpoint detection systems, and network monitoring tools. Include automated containment, evidence collection, threat hunting, and regulatory notification workflows.",
      "Create an intelligent capacity planning and resource optimization system for a global cloud infrastructure that can predict resource needs 6 months in advance, automatically negotiate contracts with vendors, optimize workload placement for cost and performance, and implement just-in-time provisioning. Include carbon footprint optimization and sustainability metrics.",
      "Design a self-healing infrastructure platform that can automatically detect and remediate issues before they impact users. The system should learn from historical incidents, predict failures using ML models, implement proactive fixes, manage dependencies, and continuously optimize system reliability. Include integration with chaos engineering practices.",
      "Build an automated compliance and governance framework that can continuously monitor and enforce policies across cloud resources, applications, and data pipelines. The system should automatically remediate violations, generate compliance reports, manage exceptions, and adapt to changing regulatory requirements across different jurisdictions.",
      "Develop an AI-driven network optimization system that can automatically adjust routing, implement traffic engineering, optimize bandwidth allocation, and predict network failures. The system should integrate with SDN controllers, analyze traffic patterns in real-time, and implement autonomous network healing capabilities.",
      "Create a comprehensive automation platform for DevSecOps that can automatically generate secure code, implement security testing, manage vulnerabilities, deploy applications with zero-touch security approval, and provide continuous security monitoring. Include AI-powered threat modeling and automated security architecture recommendations.",
      "Design an autonomous cloud cost optimization system that can analyze spending patterns, predict future costs, automatically implement cost-saving measures, negotiate better rates with vendors, and optimize resource allocation across multiple cloud providers. Include FinOps integration, budget management, and ROI analysis for optimization initiatives."
    ];
  }

  // Get appropriate questions based on current level
  getCurrentLevelQuestions() {
    switch (this.currentLevel) {
      case 1: return this.getBasicITQuestions();
      case 2: return this.getIntermediateQuestions();
      case 3: return this.getAdvancedQuestions();
      case 4: return this.getExpertQuestions();
      case 5: return this.getExtremeQuestions();
      default: return this.getBasicITQuestions();
    }
  }

  // Authenticate with the system
  async authenticate() {
    try {
      // You'll need to modify this with actual login credentials
      const loginResponse = await this.api.post('/api/v1/auth/login', {
        email: 'admin@opsconductor.com',
        password: 'admin123'
      });

      this.authToken = loginResponse.data.access_token;
      this.log(`Successfully authenticated`, 'success');
      return true;
    } catch (error) {
      this.log(`Authentication failed: ${error.message}`, 'error');
      return false;
    }
  }

  // Send a single chat message
  async sendChatMessage(message, conversationId = null) {
    const startTime = Date.now();
    
    try {
      const request = {
        message: message,
        user_id: 1,
        ...(conversationId && { conversation_id: conversationId })
      };

      const response = await this.api.post('/api/v1/ai/chat', request);
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      this.responseTimes.push(responseTime);
      this.totalQuestions++;

      // Store conversation ID for future requests
      if (response.data.conversation_id) {
        this.conversationIds.add(response.data.conversation_id);
      }

      const result = {
        timestamp: new Date().toISOString(),
        level: this.currentLevel,
        question: message,
        response: response.data.response,
        responseTime: responseTime,
        success: true,
        conversationId: response.data.conversation_id,
        intent: response.data.intent,
        confidence: response.data.confidence,
        routing: response.data._routing
      };

      this.testResults.push(result);

      this.log(`Q${this.totalQuestions} [L${this.currentLevel}] (${responseTime}ms): ${message.substring(0, 100)}...`);
      this.log(`A${this.totalQuestions}: ${response.data.response.substring(0, 200)}...`);

      return result;

    } catch (error) {
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      const result = {
        timestamp: new Date().toISOString(),
        level: this.currentLevel,
        question: message,
        responseTime: responseTime,
        success: false,
        error: error.message
      };

      this.testResults.push(result);
      this.log(`FAILED Q${this.totalQuestions} [L${this.currentLevel}]: ${error.message}`, 'error');
      
      return result;
    }
  }

  // Progress to next level
  progressToNextLevel() {
    if (this.currentLevel < 5) {
      this.currentLevel++;
      this.currentLevelCount = 0;
      this.log(`PROGRESSING TO LEVEL ${this.currentLevel}`, 'info');
      
      // Increase difficulty by reducing interval between questions
      this.questionIntervalMs = Math.max(2000, this.questionIntervalMs * 0.8);
      this.log(`New question interval: ${this.questionIntervalMs}ms`);
    }
  }

  // Generate performance statistics
  generateStats() {
    if (this.responseTimes.length === 0) return {};

    const avgResponseTime = this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
    const minResponseTime = Math.min(...this.responseTimes);
    const maxResponseTime = Math.max(...this.responseTimes);
    const successRate = (this.successfulResponses / this.totalQuestions) * 100;
    const runTimeMinutes = (Date.now() - this.startTime) / (1000 * 60);

    return {
      totalQuestions: this.totalQuestions,
      successfulResponses: this.successfulResponses,
      errorResponses: this.errorResponses,
      successRate: successRate.toFixed(2),
      avgResponseTime: avgResponseTime.toFixed(2),
      minResponseTime,
      maxResponseTime,
      runTimeMinutes: runTimeMinutes.toFixed(2),
      currentLevel: this.currentLevel,
      conversationCount: this.conversationIds.size,
      questionsPerMinute: (this.totalQuestions / runTimeMinutes).toFixed(2)
    };
  }

  // Save detailed results to file
  saveResults() {
    const stats = this.generateStats();
    const resultsFile = `ai-chat-results-${new Date().toISOString().slice(0,19).replace(/[:.]/g, '-')}.json`;
    
    const fullResults = {
      summary: stats,
      testConfiguration: {
        maxTestDurationHours: this.maxTestDurationHours,
        questionsPerLevel: this.questionsPerLevel,
        startingInterval: 5000,
        baseUrl: this.baseUrl
      },
      detailedResults: this.testResults
    };

    fs.writeFileSync(resultsFile, JSON.stringify(fullResults, null, 2));
    this.log(`Results saved to ${resultsFile}`, 'info');
  }

  // Print periodic status updates
  printStatus() {
    const stats = this.generateStats();
    
    this.log('='.repeat(80), 'info');
    this.log(`STATUS UPDATE - Level ${this.currentLevel} - Questions: ${stats.totalQuestions}`, 'info');
    this.log(`Success Rate: ${stats.successRate}% | Avg Response: ${stats.avgResponseTime}ms`, 'info');
    this.log(`Runtime: ${stats.runTimeMinutes} min | QPM: ${stats.questionsPerMinute}`, 'info');
    this.log(`Conversations: ${stats.conversationCount} | Errors: ${stats.errorResponses}`, 'info');
    this.log('='.repeat(80), 'info');
  }

  // Main test execution loop
  async runStressTest() {
    this.log('Starting AI Chat Stress Test Framework', 'info');
    
    // Authenticate first
    const authenticated = await this.authenticate();
    if (!authenticated) {
      this.log('Cannot proceed without authentication', 'error');
      return;
    }

    const maxDurationMs = this.maxTestDurationHours * 60 * 60 * 1000;
    let lastStatusUpdate = Date.now();
    const statusUpdateInterval = 5 * 60 * 1000; // 5 minutes

    this.log(`Test will run for ${this.maxTestDurationHours} hours`, 'info');
    this.log(`Starting with Level 1 questions, ${this.questionsPerLevel} per level`, 'info');

    while (Date.now() - this.startTime < maxDurationMs) {
      try {
        // Get questions for current level
        const questions = this.getCurrentLevelQuestions();
        const randomQuestion = questions[Math.floor(Math.random() * questions.length)];

        // Send the question
        await this.sendChatMessage(randomQuestion);
        
        // Track level progression
        this.currentLevelCount++;
        if (this.currentLevelCount >= this.questionsPerLevel) {
          this.progressToNextLevel();
        }

        // Periodic status updates
        if (Date.now() - lastStatusUpdate > statusUpdateInterval) {
          this.printStatus();
          this.saveResults(); // Save intermediate results
          lastStatusUpdate = Date.now();
        }

        // Wait before next question (with some randomization)
        const jitter = Math.random() * 1000; // Add up to 1s random delay
        await new Promise(resolve => setTimeout(resolve, this.questionIntervalMs + jitter));

      } catch (error) {
        this.log(`Test loop error: ${error.message}`, 'error');
        // Continue testing even if individual questions fail
      }
    }

    // Final results
    this.log('Test completed!', 'success');
    this.printStatus();
    this.saveResults();
  }
}

// Export for use in Node.js
module.exports = AIChatStressTester;

// If run directly, start the test
if (require.main === module) {
  const tester = new AIChatStressTester();
  tester.runStressTest().catch(console.error);
}