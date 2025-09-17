#!/usr/bin/env python3
"""
OpsConductor AI Training Script - IT Knowledge Base Ingestion
Loads comprehensive IT knowledge into the AI system with proper chunking and rate limiting
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ITKnowledgeTrainer:
    """Trainer for ingesting IT knowledge into OpsConductor AI"""
    
    def __init__(self, base_url: str = "http://localhost:3005"):
        self.base_url = base_url
        self.session = requests.Session()
        self.stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
    def check_ai_health(self) -> bool:
        """Check if AI service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ AI Service is healthy")
                return True
            else:
                logger.error(f"❌ AI Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to AI service: {e}")
            return False
    
    def store_knowledge_chunk(self, content: str, category: str, retries: int = 3) -> bool:
        """Store a single chunk of knowledge with retries"""
        for attempt in range(retries):
            try:
                payload = {
                    "content": content,
                    "category": category
                }
                
                response = self.session.post(
                    f"{self.base_url}/ai/store-knowledge",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.warning(f"Failed to store chunk (attempt {attempt + 1}): {response.status_code}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                logger.warning(f"Error storing chunk (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
                
        return False
    
    def chunk_text(self, text: str, max_size: int = 2000) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > max_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
    
    def load_core_it_knowledge(self):
        """Load essential IT operations knowledge"""
        
        knowledge_base = {
            "system_administration": [
                """Linux System Administration:
                - User Management: useradd, usermod, userdel, passwd, chown, chmod
                - Process Management: ps, top, htop, kill, nice, renice, systemctl, service
                - Package Management: apt, yum, dnf, snap, flatpak, dpkg, rpm
                - File Systems: ext4, xfs, btrfs, zfs, mount, umount, df, du, fsck
                - Network Configuration: ip, ifconfig, netstat, ss, iptables, firewalld
                - Service Management: systemd units, init.d scripts, cron jobs, timers
                - Log Management: journalctl, rsyslog, logrotate, /var/log structure
                - Performance Tuning: kernel parameters, sysctl, ulimit, nice levels
                - Security: SELinux, AppArmor, auditd, fail2ban, firewall rules
                - Backup & Recovery: tar, rsync, dd, backup strategies, disaster recovery""",
                
                """Windows System Administration:
                - Active Directory: Domain Controllers, GPO, LDAP, DNS, DHCP
                - PowerShell: cmdlets, scripting, remoting, DSC, modules
                - IIS Management: application pools, bindings, certificates, logging
                - Registry Management: regedit, reg command, hives, keys, values
                - Event Logs: Event Viewer, wevtutil, log analysis, correlation
                - Performance Monitoring: PerfMon, WMI, Resource Monitor, Task Manager
                - Security: Windows Defender, BitLocker, Windows Firewall, UAC
                - Group Policy: Computer/User configuration, preferences, WMI filters
                - Hyper-V: Virtual machines, virtual switches, checkpoints, replication
                - Storage Spaces: Pools, virtual disks, tiering, deduplication"""
            ],
            
            "networking": [
                """Network Protocols and Standards:
                - OSI Model: Physical, Data Link, Network, Transport, Session, Presentation, Application
                - TCP/IP Stack: IP addressing, subnetting, CIDR, NAT, PAT, IPv4, IPv6
                - Routing Protocols: OSPF, BGP, EIGRP, RIP, static routing, route redistribution
                - Switching: VLANs, STP, RSTP, MSTP, port security, trunking, EtherChannel
                - Network Services: DNS, DHCP, NTP, SNMP, LDAP, RADIUS, TACACS+
                - Load Balancing: Round-robin, least connections, IP hash, health checks
                - VPN Technologies: IPSec, SSL/TLS VPN, DMVPN, site-to-site, remote access
                - SDN/NFV: OpenFlow, VXLAN, overlay networks, network virtualization
                - QoS: Traffic shaping, policing, queuing, DSCP, CoS marking
                - Network Security: Firewalls, IDS/IPS, DDoS protection, ACLs, NAC""",
                
                """Network Troubleshooting:
                - Diagnostic Tools: ping, traceroute, nslookup, dig, netcat, tcpdump, Wireshark
                - Performance Analysis: iperf, netperf, bandwidth monitoring, latency testing
                - Common Issues: DNS resolution, routing loops, broadcast storms, MTU issues
                - Cable Testing: cable testers, OTDR, TDR, certification testing
                - Protocol Analysis: packet capture, protocol decoding, traffic patterns
                - Network Monitoring: SNMP, NetFlow, sFlow, IPFIX, synthetic monitoring
                - Troubleshooting Methodology: OSI layer approach, divide and conquer, baseline comparison
                - Documentation: Network diagrams, IP schemas, change logs, runbooks"""
            ],
            
            "cloud_platforms": [
                """Amazon Web Services (AWS):
                - Compute: EC2, Lambda, ECS, EKS, Fargate, Batch, Lightsail
                - Storage: S3, EBS, EFS, FSx, Storage Gateway, Backup, Glacier
                - Database: RDS, DynamoDB, Aurora, ElastiCache, Neptune, DocumentDB
                - Networking: VPC, Route53, CloudFront, API Gateway, Direct Connect
                - Security: IAM, KMS, Secrets Manager, GuardDuty, Security Hub, WAF
                - Management: CloudFormation, CloudWatch, Systems Manager, Config
                - Developer Tools: CodeCommit, CodeBuild, CodeDeploy, CodePipeline
                - Analytics: Athena, EMR, Kinesis, QuickSight, Glue, DataPipeline
                - Best Practices: Well-Architected Framework, cost optimization, tagging
                - CLI Commands: aws ec2, aws s3, aws lambda, aws cloudformation""",
                
                """Microsoft Azure:
                - Compute: Virtual Machines, App Service, Functions, AKS, Container Instances
                - Storage: Blob Storage, File Storage, Queue Storage, Disk Storage, Archive
                - Database: SQL Database, Cosmos DB, Database for PostgreSQL/MySQL
                - Networking: Virtual Network, Load Balancer, Application Gateway, ExpressRoute
                - Identity: Azure AD, B2C, Managed Identities, Privileged Identity Management
                - Management: Resource Manager, Monitor, Automation, Policy, Blueprints
                - DevOps: Azure DevOps, Repos, Pipelines, Artifacts, Test Plans
                - Analytics: Synapse, Data Factory, Stream Analytics, HDInsight, Databricks
                - Security: Key Vault, Security Center, Sentinel, Information Protection
                - CLI Commands: az vm, az storage, az network, az group, az resource""",
                
                """Google Cloud Platform (GCP):
                - Compute: Compute Engine, App Engine, Cloud Functions, GKE, Cloud Run
                - Storage: Cloud Storage, Persistent Disk, Filestore, Cloud Storage Transfer
                - Database: Cloud SQL, Firestore, Bigtable, Spanner, Memorystore
                - Networking: VPC, Cloud Load Balancing, Cloud CDN, Cloud Interconnect
                - Identity: Cloud IAM, Identity Platform, Cloud Identity, BeyondCorp
                - Management: Deployment Manager, Cloud Console, Cloud Shell, Resource Manager
                - DevOps: Cloud Build, Container Registry, Source Repositories, Cloud Deploy
                - Data & Analytics: BigQuery, Dataflow, Dataproc, Composer, Data Catalog
                - AI/ML: Vertex AI, AutoML, AI Platform, Vision AI, Natural Language AI
                - CLI Commands: gcloud compute, gcloud storage, gcloud container, gcloud iam"""
            ],
            
            "containers_orchestration": [
                """Docker:
                - Core Concepts: Images, containers, registries, Dockerfile, layers
                - Docker Commands: run, build, push, pull, exec, logs, ps, inspect
                - Dockerfile Instructions: FROM, RUN, CMD, ENTRYPOINT, COPY, ADD, ENV, EXPOSE
                - Networking: Bridge, host, overlay, macvlan, network drivers
                - Storage: Volumes, bind mounts, tmpfs mounts, storage drivers
                - Docker Compose: services, networks, volumes, environment variables
                - Security: User namespaces, capabilities, seccomp, AppArmor, SELinux
                - Best Practices: Multi-stage builds, layer caching, .dockerignore, healthchecks
                - Registry Management: Docker Hub, private registries, Harbor, Artifactory
                - Troubleshooting: Container logs, resource limits, networking issues""",
                
                """Kubernetes:
                - Architecture: Control plane, nodes, etcd, API server, scheduler, controller manager
                - Workloads: Pods, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs
                - Services & Networking: Services, Ingress, NetworkPolicies, DNS, load balancing
                - Storage: PersistentVolumes, PersistentVolumeClaims, StorageClasses, CSI
                - Configuration: ConfigMaps, Secrets, environment variables, volume mounts
                - Security: RBAC, ServiceAccounts, PodSecurityPolicies, NetworkPolicies, OPA
                - Scaling: HPA, VPA, Cluster Autoscaler, manual scaling, resource quotas
                - Monitoring: Prometheus, Grafana, metrics-server, logging, tracing
                - Package Management: Helm charts, Kustomize, operators, GitOps
                - kubectl Commands: get, describe, logs, exec, port-forward, apply, delete"""
            ],
            
            "devops_cicd": [
                """CI/CD Pipelines:
                - Version Control: Git workflows, branching strategies, merge requests, code reviews
                - Build Automation: Maven, Gradle, npm, webpack, Make, build optimization
                - Testing: Unit tests, integration tests, E2E tests, test automation, coverage
                - Continuous Integration: Jenkins, GitLab CI, GitHub Actions, CircleCI, Travis CI
                - Continuous Deployment: Blue-green, canary, rolling updates, feature flags
                - Artifact Management: Nexus, Artifactory, package registries, versioning
                - Infrastructure as Code: Terraform, CloudFormation, Pulumi, CDK, Ansible
                - Configuration Management: Ansible, Puppet, Chef, Salt, DSC
                - Monitoring & Logging: ELK stack, Prometheus/Grafana, Datadog, New Relic
                - Security: SAST, DAST, dependency scanning, secrets management, compliance""",
                
                """DevOps Best Practices:
                - Agile Methodology: Scrum, Kanban, sprints, retrospectives, daily standups
                - GitOps: Repository as source of truth, declarative configs, automated sync
                - Site Reliability Engineering: SLIs, SLOs, SLAs, error budgets, toil reduction
                - Incident Management: On-call rotation, runbooks, post-mortems, RCA
                - Change Management: Change advisory board, rollback procedures, approvals
                - Documentation: README files, wikis, API docs, architecture diagrams
                - Collaboration Tools: Slack, Teams, Jira, Confluence, PagerDuty
                - Performance Testing: Load testing, stress testing, benchmarking, profiling
                - Chaos Engineering: Fault injection, disaster recovery testing, game days
                - Continuous Improvement: Metrics, KPIs, feedback loops, automation"""
            ],
            
            "databases": [
                """Relational Databases:
                - MySQL: Storage engines, replication, clustering, performance tuning, backup
                - PostgreSQL: MVCC, extensions, partitioning, streaming replication, VACUUM
                - Oracle: RAC, Data Guard, ASM, RMAN, performance tuning, PL/SQL
                - SQL Server: Always On, replication, SSIS, SSRS, SSAS, T-SQL, maintenance plans
                - Database Design: Normalization, denormalization, indexing, constraints
                - Query Optimization: Execution plans, index usage, statistics, query hints
                - Transactions: ACID properties, isolation levels, deadlocks, locking
                - Backup & Recovery: Full, differential, incremental, point-in-time recovery
                - High Availability: Clustering, replication, failover, load balancing
                - Security: Authentication, authorization, encryption, auditing, data masking""",
                
                """NoSQL Databases:
                - MongoDB: Documents, collections, sharding, replica sets, aggregation pipeline
                - Redis: Data structures, persistence, clustering, Sentinel, pub/sub
                - Cassandra: Column families, partitioning, replication, consistency levels
                - Elasticsearch: Indices, shards, replicas, mappings, queries, aggregations
                - DynamoDB: Tables, items, attributes, GSI, LSI, streams, auto-scaling
                - Neo4j: Nodes, relationships, properties, Cypher queries, graph algorithms
                - InfluxDB: Time series, measurements, tags, fields, retention policies
                - CouchDB: Documents, views, replication, conflict resolution, MapReduce
                - Key-Value Stores: Memcached, etcd, Consul, performance characteristics
                - CAP Theorem: Consistency, availability, partition tolerance trade-offs"""
            ],
            
            "monitoring_observability": [
                """Monitoring Systems:
                - Metrics Collection: Prometheus, Graphite, InfluxDB, CloudWatch, Azure Monitor
                - Visualization: Grafana, Kibana, Datadog, New Relic, custom dashboards
                - Log Management: ELK stack, Splunk, Fluentd, Logstash, centralized logging
                - APM Tools: AppDynamics, Dynatrace, New Relic, Datadog APM, Jaeger
                - Infrastructure Monitoring: Nagios, Zabbix, PRTG, SolarWinds, Icinga
                - Synthetic Monitoring: Pingdom, UptimeRobot, StatusCake, custom scripts
                - Real User Monitoring: Google Analytics, browser metrics, user journeys
                - Distributed Tracing: OpenTelemetry, Jaeger, Zipkin, AWS X-Ray
                - Alerting: PagerDuty, OpsGenie, VictorOps, alert fatigue prevention
                - SLI/SLO Definition: Availability, latency, throughput, error rates""",
                
                """Observability Practices:
                - Three Pillars: Metrics, logs, traces, and their relationships
                - Instrumentation: Application metrics, custom metrics, business metrics
                - Log Formats: Structured logging, JSON, correlation IDs, log levels
                - Metric Types: Counters, gauges, histograms, summaries, percentiles
                - Dashboards: Executive, operational, technical, mobile-responsive
                - Alert Design: Actionable alerts, severity levels, escalation policies
                - Capacity Planning: Resource utilization, growth projections, bottlenecks
                - Performance Analysis: Profiling, flame graphs, bottleneck identification
                - Root Cause Analysis: 5 Whys, fishbone diagrams, timeline correlation
                - Documentation: Runbooks, playbooks, knowledge base, incident reports"""
            ],
            
            "security": [
                """Security Fundamentals:
                - CIA Triad: Confidentiality, Integrity, Availability principles
                - Authentication: Multi-factor, SSO, OAuth, SAML, LDAP, Kerberos
                - Authorization: RBAC, ABAC, ACLs, principle of least privilege
                - Encryption: At rest, in transit, key management, HSMs, certificates
                - Network Security: Firewalls, IDS/IPS, VPNs, DMZ, segmentation
                - Application Security: OWASP Top 10, secure coding, input validation
                - Vulnerability Management: Scanning, patching, CVE tracking, remediation
                - Compliance: PCI DSS, HIPAA, GDPR, SOC 2, ISO 27001, auditing
                - Incident Response: Detection, containment, eradication, recovery
                - Security Tools: Nmap, Metasploit, Burp Suite, SIEM, vulnerability scanners""",
                
                """Cloud Security:
                - Identity Management: IAM policies, roles, service accounts, MFA
                - Data Protection: Encryption keys, secrets management, data classification
                - Network Security: Security groups, NACLs, WAF, DDoS protection
                - Compliance: Shared responsibility model, compliance frameworks
                - Monitoring: CloudTrail, Azure Monitor, Cloud Audit Logs, SIEM integration
                - Container Security: Image scanning, runtime protection, admission controllers
                - Serverless Security: Function permissions, API security, cold start attacks
                - DevSecOps: Shift-left security, SAST, DAST, dependency scanning
                - Zero Trust: Micro-segmentation, identity verification, least privilege
                - Threat Detection: GuardDuty, Security Center, anomaly detection"""
            ],
            
            "automation_scripting": [
                """Shell Scripting:
                - Bash Scripting: Variables, loops, conditionals, functions, arrays
                - Command Line Tools: grep, sed, awk, cut, sort, uniq, xargs
                - Process Control: Background jobs, signals, traps, process substitution
                - File Operations: Reading, writing, permissions, find, file tests
                - Text Processing: Regular expressions, pattern matching, string manipulation
                - Error Handling: Exit codes, error redirection, debugging techniques
                - Best Practices: Shellcheck, portability, security, performance
                - Advanced Features: Here documents, command substitution, parameter expansion
                - Scheduling: Cron, at, systemd timers, job dependencies
                - Utility Scripts: Backup, monitoring, log rotation, cleanup, reporting""",
                
                """Python Automation:
                - Core Libraries: os, sys, subprocess, shutil, pathlib, argparse
                - Network Automation: paramiko, netmiko, requests, urllib, socket
                - Cloud SDKs: boto3 (AWS), azure-mgmt, google-cloud libraries
                - Configuration Management: YAML, JSON, ConfigParser, environment variables
                - Database Access: psycopg2, PyMySQL, SQLAlchemy, pymongo
                - API Integration: REST, GraphQL, SOAP, authentication, rate limiting
                - Testing: unittest, pytest, mock, coverage, test automation
                - Logging: logging module, structured logging, log aggregation
                - Async Programming: asyncio, aiohttp, concurrent.futures
                - Package Management: pip, virtualenv, poetry, requirements.txt""",
                
                """PowerShell Automation:
                - Cmdlets: Get-, Set-, New-, Remove-, Test-, core cmdlets
                - Pipeline: Objects in pipeline, filtering, sorting, grouping
                - Scripting: Functions, modules, error handling, debugging
                - Remote Management: PSRemoting, Invoke-Command, PSSession
                - Active Directory: AD cmdlets, user/group management, GPO
                - Azure/AWS: Az module, AWS.Tools, cloud resource management
                - DSC: Configurations, resources, push/pull modes, LCM
                - Scheduled Tasks: Register-ScheduledTask, triggers, actions
                - REST APIs: Invoke-RestMethod, Invoke-WebRequest, JSON handling
                - Best Practices: Approved verbs, help documentation, Pester testing"""
            ]
        }
        
        logger.info("🚀 Starting IT Knowledge Base Training...")
        
        # Process each category
        for category, knowledge_items in knowledge_base.items():
            logger.info(f"\n📚 Loading category: {category}")
            category_stats = {'success': 0, 'failed': 0}
            
            for item in knowledge_items:
                # Chunk the knowledge item
                chunks = self.chunk_text(item, max_size=2000)
                logger.info(f"   Processing {len(chunks)} chunks...")
                
                for i, chunk in enumerate(chunks):
                    if self.store_knowledge_chunk(chunk, category):
                        category_stats['success'] += 1
                        self.stats['successful'] += 1
                        logger.debug(f"     ✅ Chunk {i+1}/{len(chunks)} stored")
                    else:
                        category_stats['failed'] += 1
                        self.stats['failed'] += 1
                        logger.warning(f"     ❌ Chunk {i+1}/{len(chunks)} failed")
                    
                    # Rate limiting to prevent overwhelming the service
                    time.sleep(0.5)
                
            logger.info(f"   Category complete: {category_stats['success']} successful, {category_stats['failed']} failed")
        
        self.stats['total'] = self.stats['successful'] + self.stats['failed']
    
    def load_troubleshooting_solutions(self):
        """Load common IT troubleshooting solutions"""
        
        solutions = [
            {
                "problem": "Server is running out of disk space",
                "solution": """1. Identify large files: du -sh /* | sort -rh | head -20
2. Check log files: find /var/log -type f -size +100M
3. Clean package cache: apt-get clean (Debian/Ubuntu) or yum clean all (RHEL/CentOS)
4. Remove old kernels: apt-get autoremove or package-cleanup --oldkernels
5. Check for core dumps: find / -name core -type f
6. Review Docker images/containers: docker system prune -a
7. Set up log rotation if not configured
8. Consider expanding disk or adding storage"""
            },
            {
                "problem": "Application performance is degraded",
                "solution": """1. Check system resources: top, htop, free -h, df -h
2. Review application logs for errors or warnings
3. Monitor database queries: slow query log, execution plans
4. Check network latency: ping, traceroute, mtr
5. Review recent changes: deployments, configurations, patches
6. Profile application: APM tools, profilers, flame graphs
7. Check for resource limits: ulimit -a, cgroups
8. Verify external dependencies: APIs, services, databases"""
            },
            {
                "problem": "Cannot connect to remote server via SSH",
                "solution": """1. Verify network connectivity: ping server_ip
2. Check SSH service status: systemctl status sshd
3. Verify firewall rules: iptables -L, ufw status
4. Check SSH configuration: /etc/ssh/sshd_config
5. Verify user permissions and authentication method
6. Check for failed login attempts: /var/log/auth.log
7. Test with verbose mode: ssh -vvv user@server
8. Verify DNS resolution: nslookup server_name"""
            },
            {
                "problem": "Database connection pool exhausted",
                "solution": """1. Check current connections: SHOW PROCESSLIST (MySQL) or pg_stat_activity (PostgreSQL)
2. Identify long-running queries and kill if necessary
3. Review application connection pooling settings
4. Check for connection leaks in application code
5. Increase max_connections in database configuration
6. Implement connection pooling: PgBouncer, ProxySQL
7. Add monitoring for connection usage
8. Review and optimize slow queries"""
            },
            {
                "problem": "Kubernetes pod keeps restarting",
                "solution": """1. Check pod logs: kubectl logs <pod-name> --previous
2. Describe pod: kubectl describe pod <pod-name>
3. Check events: kubectl get events --sort-by=.metadata.creationTimestamp
4. Verify resource limits: memory, CPU constraints
5. Check liveness/readiness probes configuration
6. Review container exit codes and reasons
7. Check for image pull errors or incorrect image tags
8. Verify ConfigMaps and Secrets are properly mounted
9. Check node resources: kubectl top nodes
10. Review recent deployments or configuration changes"""
            }
        ]
        
        logger.info("\n🔧 Loading Troubleshooting Solutions...")
        
        for i, solution_pair in enumerate(solutions, 1):
            logger.info(f"   Loading solution {i}/{len(solutions)}: {solution_pair['problem'][:50]}...")
            
            # Store the problem-solution pair
            content = f"{solution_pair['problem']}\n\n{solution_pair['solution']}"
            if self.store_knowledge_chunk(content, "troubleshooting"):
                self.stats['successful'] += 1
                logger.info(f"     ✅ Solution stored successfully")
            else:
                self.stats['failed'] += 1
                logger.warning(f"     ❌ Failed to store solution")
            
            time.sleep(0.5)  # Rate limiting
    
    def print_summary(self):
        """Print training summary"""
        print("\n" + "="*60)
        print("Training Summary")
        print("="*60)
        print(f"Total items processed: {self.stats['total']}")
        print(f"Successfully stored: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Success rate: {(self.stats['successful']/max(self.stats['total'],1))*100:.1f}%")
        print("="*60)

def main():
    """Main training execution"""
    trainer = ITKnowledgeTrainer()
    
    # Check AI service health
    if not trainer.check_ai_health():
        logger.error("AI service is not available. Please ensure it's running.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("OpsConductor AI Training System")
    print("IT Knowledge Base Ingestion")
    print("="*60)
    print("\nThis will load comprehensive IT operations knowledge into the AI system.")
    print("The process may take several minutes to complete.")
    
    response = input("\nDo you want to proceed? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled.")
        sys.exit(0)
    
    try:
        # Load core IT knowledge
        trainer.load_core_it_knowledge()
        
        # Load troubleshooting solutions
        trainer.load_troubleshooting_solutions()
        
        # Print summary
        trainer.print_summary()
        
        print("\n✅ Training completed successfully!")
        print("The AI system now has comprehensive IT operations knowledge.")
        print("\nYou can test it by:")
        print("  1. Asking questions via the chat interface")
        print("  2. Requesting automation workflows")
        print("  3. Getting troubleshooting recommendations")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        trainer.print_summary()
    except Exception as e:
        logger.error(f"Training failed: {e}")
        trainer.print_summary()
        sys.exit(1)

if __name__ == "__main__":
    main()