# ClinChat-RAG Production Runbook

## Overview

This runbook provides operational procedures for the ClinChat-RAG medical AI assistant system in production. This is a HIPAA-compliant system handling Protected Health Information (PHI) and requires specialized operational procedures.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Monitoring & Alerting](#monitoring--alerting)
3. [Deployment Procedures](#deployment-procedures)
4. [Incident Response](#incident-response)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Backup & Recovery](#backup--recovery)
7. [Security Procedures](#security-procedures)
8. [Compliance & Audit](#compliance--audit)
9. [Emergency Contacts](#emergency-contacts)

---

## System Architecture

### Production Environment
- **Environment**: AWS EKS Cluster in `us-east-1`
- **Application**: FastAPI backend with LangChain RAG pipeline
- **Database**: Amazon RDS PostgreSQL (Multi-AZ)
- **Vector Store**: Amazon OpenSearch Service
- **Load Balancer**: Application Load Balancer (ALB) with WAF
- **Monitoring**: CloudWatch, Prometheus, Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Key Components
```
Internet → WAF → ALB → EKS Pods → RDS/OpenSearch
                ↓
        CloudWatch Monitoring
                ↓
           Alert Manager
```

### HIPAA Compliance Features
- ✅ End-to-end encryption (TLS 1.2+)
- ✅ Encrypted storage (RDS, OpenSearch, EBS)
- ✅ Access logging and audit trails
- ✅ Role-based access control (RBAC)
- ✅ PHI detection and masking
- ✅ Automated backup with encryption

---

## Monitoring & Alerting

### Key Metrics to Monitor

#### Application Metrics
- **Response Time**: P95 < 2s, P99 < 5s
- **Error Rate**: < 1% for 4xx, < 0.1% for 5xx
- **Throughput**: Current RPS vs historical baseline
- **PHI Detection Rate**: Should be > 95% accuracy

#### Infrastructure Metrics
- **CPU Usage**: < 70% average across nodes
- **Memory Usage**: < 80% average across nodes
- **Database Connections**: < 80% of max connections
- **Disk Space**: > 20% free space on all volumes

#### Security Metrics
- **Failed Authentication**: > 10 failures per minute
- **Suspicious Access**: Access from unexpected geolocations
- **Vulnerability Scans**: Any new critical/high findings

### Monitoring Dashboards

#### Main Dashboard (Grafana)
```
URL: https://monitoring.clinchat-rag.example.com/grafana
Access: Production monitoring team

Key panels:
- Service Health Overview
- Request/Response metrics
- Error rate trends
- Infrastructure utilization
- Security events
```

#### Application Dashboard
```
URL: https://clinchat-rag.example.com/monitoring
Access: Authenticated users with monitoring role

Features:
- Real-time system status
- Performance metrics
- User activity summary
- PHI protection stats
```

### Alert Channels
- **Slack**: `#clinchat-production-alerts`
- **PagerDuty**: On-call escalation
- **Email**: Production team distribution list
- **SMS**: Critical alerts only

### Alert Thresholds

#### Critical Alerts (Immediate Response)
- Service completely down (0% success rate)
- Database connection failure
- PHI exposure detected
- Security breach indicators
- RTO/RPO violations during incidents

#### Warning Alerts (15-minute Response)
- Error rate > 5%
- Response time P95 > 3s
- CPU/Memory > 85%
- Disk space < 15%

#### Info Alerts (1-hour Response)
- Deployment completed
- Weekly backup status
- Security scan results
- Performance degradation trends

---

## Deployment Procedures

### Pre-Deployment Checklist
- [ ] Security scans passed (SAST, DAST, dependency check)
- [ ] HIPAA compliance validation completed
- [ ] Staging environment fully tested
- [ ] Rollback plan prepared
- [ ] Change management approval obtained
- [ ] Business stakeholders notified

### Deployment Process

#### 1. Pre-Deployment Validation
```bash
# Validate staging environment
python scripts/smoke-tests.py --environment staging

# Check security compliance
python scripts/validate-hipaa-compliance.py

# Verify rollback plan
kubectl get deployments -n clinchat-rag
kubectl rollout history deployment/clinchat-rag-api -n clinchat-rag
```

#### 2. Production Deployment
```bash
# Deploy using GitHub Actions
# Trigger: Create and publish a release in GitHub

# Manual deployment (emergency only)
kubectl set image deployment/clinchat-rag-api \
  api=ghcr.io/yourorg/clinchat-rag:v1.2.3 \
  -n clinchat-rag

kubectl rollout status deployment/clinchat-rag-api -n clinchat-rag
```

#### 3. Post-Deployment Validation
```bash
# Run smoke tests
python scripts/smoke-tests.py --environment production

# Validate HIPAA compliance
python scripts/validate-production-hipaa.py

# Check monitoring dashboards
# Verify all metrics are within normal ranges
```

### Deployment Windows
- **Preferred**: Tuesdays/Thursdays, 10 AM - 2 PM EST
- **Avoid**: Fridays, weekends, holidays
- **Emergency**: 24/7 with appropriate approvals

---

## Incident Response

### Incident Classification

#### Severity 1 - Critical (15-minute response)
- Complete service outage
- PHI data breach or exposure
- Security compromise
- HIPAA compliance violation

#### Severity 2 - High (1-hour response)
- Partial service degradation affecting > 50% users
- Database performance issues
- Authentication system failures
- Failed security controls

#### Severity 3 - Medium (4-hour response)
- Performance degradation < 50% users
- Non-critical feature failures
- Monitoring/logging issues
- Documentation/training gaps

#### Severity 4 - Low (Next business day)
- Cosmetic issues
- Enhancement requests
- Informational security alerts
- Scheduled maintenance

### Incident Response Process

#### 1. Incident Detection
```bash
# Check service health
kubectl get pods -n clinchat-rag
kubectl get services -n clinchat-rag
kubectl describe deployment clinchat-rag-api -n clinchat-rag

# Check recent logs
kubectl logs -f deployment/clinchat-rag-api -n clinchat-rag --tail=100
```

#### 2. Initial Assessment
- Determine severity level
- Identify impacted users/services
- Assess HIPAA/security implications
- Notify incident commander

#### 3. Incident Response Team Assembly
- **Incident Commander**: Senior DevOps Engineer
- **Technical Lead**: Senior Backend Developer
- **Security Officer**: CISO or delegate
- **Communications**: Product Manager
- **HIPAA Officer**: Privacy Officer or delegate

#### 4. Mitigation Steps
```bash
# Quick rollback if needed
kubectl rollout undo deployment/clinchat-rag-api -n clinchat-rag

# Scale up replicas for load issues
kubectl scale deployment clinchat-rag-api --replicas=10 -n clinchat-rag

# Check database connections
python scripts/check-db-health.py

# Validate external dependencies
python scripts/check-external-services.py
```

#### 5. Communication Templates

##### Internal Notification (Slack)
```
🚨 INCIDENT: [SEV-1/2/3/4] - [Brief Description]

Status: INVESTIGATING/MITIGATING/RESOLVED
Impact: [User impact description]
ETA: [Estimated resolution time]
Incident Commander: @username
War Room: #incident-YYYY-MM-DD-NNN

Updates will be provided every 30 minutes.
```

##### External Communication (Status Page)
```
We are currently experiencing issues with our ClinChat-RAG service. 
Our team is actively investigating and working on a resolution. 
We will provide updates every 30 minutes until resolved.

Impact: [Brief description without technical details]
Started: [Timestamp]
Updates: [Link to status page]
```

### Post-Incident Process

#### 1. Incident Resolution
- Confirm service restoration
- Validate monitoring/alerting
- Update stakeholders
- Document timeline

#### 2. Post-Incident Review (Within 48 hours)
- Root cause analysis
- Timeline reconstruction
- Response effectiveness assessment
- Action items identification

#### 3. Follow-up Actions
- Implement preventive measures
- Update runbooks/procedures
- Enhance monitoring/alerting
- Training gap analysis

---

## Troubleshooting Guide

### Common Issues

#### Application Not Starting
```bash
# Check pod status
kubectl get pods -n clinchat-rag

# Check pod logs
kubectl logs [pod-name] -n clinchat-rag

# Check events
kubectl get events -n clinchat-rag --sort-by='.lastTimestamp'

# Common causes:
# - Configuration errors
# - Image pull failures
# - Resource constraints
# - Database connectivity
```

#### High Response Times
```bash
# Check CPU/Memory usage
kubectl top pods -n clinchat-rag

# Scale horizontally
kubectl scale deployment clinchat-rag-api --replicas=5 -n clinchat-rag

# Check database performance
python scripts/check-db-performance.py

# Check vector database
python scripts/check-opensearch-health.py
```

#### Database Connection Issues
```bash
# Check RDS status in AWS Console
aws rds describe-db-instances --db-instance-identifier clinchat-rag-prod

# Check connection from pod
kubectl exec -it [pod-name] -n clinchat-rag -- \
  psql -h [rds-endpoint] -U clinchat_user -d clinchat_rag -c "SELECT 1;"

# Check security groups
aws ec2 describe-security-groups --group-ids [rds-sg-id]
```

#### OpenSearch Performance Issues
```bash
# Check cluster health
curl -X GET "https://[opensearch-endpoint]/_cluster/health?pretty"

# Check indices status
curl -X GET "https://[opensearch-endpoint]/_cat/indices?v"

# Monitor query performance
curl -X GET "https://[opensearch-endpoint]/_nodes/stats/indices/search?pretty"
```

### Log Analysis

#### Application Logs Location
```bash
# Real-time logs
kubectl logs -f deployment/clinchat-rag-api -n clinchat-rag

# Centralized logging (ELK Stack)
URL: https://logs.clinchat-rag.example.com
Index pattern: clinchat-rag-*
```

#### Key Log Patterns to Monitor
```bash
# Error patterns
grep -E "(ERROR|FATAL|Exception)" /var/log/clinchat-rag/app.log

# PHI detection alerts
grep "PHI_DETECTED" /var/log/clinchat-rag/security.log

# Performance issues
grep "SLOW_QUERY\|TIMEOUT" /var/log/clinchat-rag/performance.log

# Authentication failures
grep "AUTH_FAILED" /var/log/clinchat-rag/audit.log
```

---

## Backup & Recovery

### Backup Schedule

#### Database Backups
- **Automated RDS Snapshots**: Daily at 3 AM UTC
- **Manual Snapshots**: Before major deployments
- **Cross-Region Replication**: Daily to `us-west-2`
- **Retention**: 30 days for automated, 90 days for manual

#### Vector Database Backups
- **OpenSearch Snapshots**: Daily at 4 AM UTC
- **S3 Repository**: `clinchat-rag-opensearch-backups`
- **Retention**: 30 days

#### Application Configuration
- **Kubernetes Manifests**: Git repository with daily backup
- **Secrets**: AWS Secrets Manager with cross-region replication
- **Infrastructure**: Terraform state in S3 with versioning

### Recovery Procedures

#### Database Recovery
```bash
# List available snapshots
aws rds describe-db-snapshots --db-instance-identifier clinchat-rag-prod

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier clinchat-rag-recovery \
  --db-snapshot-identifier [snapshot-id]

# Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier clinchat-rag-prod \
  --target-db-instance-identifier clinchat-rag-pitr \
  --restore-time 2023-12-01T12:00:00.000Z
```

#### OpenSearch Recovery
```bash
# Restore snapshot
curl -X POST "https://[opensearch-endpoint]/_snapshot/s3-repository/[snapshot-name]/_restore" \
  -H 'Content-Type: application/json' \
  -d '{"indices": "*", "ignore_unavailable": true}'

# Monitor restore progress
curl -X GET "https://[opensearch-endpoint]/_recovery?pretty"
```

### Disaster Recovery Plan

#### RTO/RPO Targets
- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 1 hour

#### DR Site Setup
- **Primary Region**: `us-east-1`
- **DR Region**: `us-west-2`
- **Failover Method**: Manual with automated data replication

#### DR Activation Process
1. Assess primary site status
2. Notify incident commander
3. Activate DR infrastructure
4. Update DNS records
5. Validate service functionality
6. Notify stakeholders

---

## Security Procedures

### Access Management

#### Production Access
- **Principle**: Least privilege access
- **Authentication**: Multi-factor authentication required
- **Authorization**: Role-based access control (RBAC)
- **Audit**: All access logged and monitored

#### Access Levels
```yaml
# Read-only monitoring
roles: ["monitoring:read"]
permissions: ["kubectl get", "kubectl describe"]

# Application support
roles: ["support:apps"]
permissions: ["kubectl logs", "kubectl exec"]

# Infrastructure admin
roles: ["admin:infrastructure"]
permissions: ["kubectl *", "terraform *"]

# Security admin
roles: ["admin:security"]
permissions: ["full access with audit"]
```

### Security Monitoring

#### Real-time Monitoring
- Failed authentication attempts
- Suspicious access patterns
- PHI access without authorization
- Configuration changes
- Privilege escalations

#### Security Incident Response
```bash
# Immediate actions for security incidents
# 1. Isolate affected systems
kubectl cordon [node-name]
kubectl drain [node-name] --ignore-daemonsets

# 2. Preserve evidence
kubectl get events --all-namespaces > security-incident-events.log
kubectl logs deployment/clinchat-rag-api -n clinchat-rag > security-incident-logs.log

# 3. Notify security team
# Use security incident communication template

# 4. Activate incident response plan
# Follow incident response procedures above
```

### Vulnerability Management

#### Regular Security Scans
- **Container Images**: Daily Trivy scans
- **Dependencies**: Daily Safety/Snyk scans
- **Infrastructure**: Weekly compliance scans
- **Penetration Testing**: Quarterly by third party

#### Patch Management
- **Critical Vulnerabilities**: 24-48 hours
- **High Vulnerabilities**: 1 week
- **Medium Vulnerabilities**: 1 month
- **Low Vulnerabilities**: Next maintenance window

---

## Compliance & Audit

### HIPAA Compliance Monitoring

#### Daily Checks
```bash
# Run HIPAA compliance validation
python scripts/validate-hipaa-compliance.py --environment production

# Check encryption status
python scripts/validate-encryption.py

# Verify access controls
python scripts/validate-rbac.py

# PHI handling validation
python scripts/validate-phi-protection.py
```

#### Monthly Compliance Reports
- Access control review
- Audit log analysis
- Encryption status verification
- Incident summary
- Training compliance status

### Audit Procedures

#### Audit Log Locations
```bash
# Application audit logs
/var/log/clinchat-rag/audit/

# System audit logs
/var/log/audit/

# Database audit logs
RDS Performance Insights + CloudWatch

# AWS CloudTrail
S3 bucket: clinchat-rag-cloudtrail-logs
```

#### Audit Log Retention
- **Application Logs**: 7 years
- **System Logs**: 7 years  
- **Database Logs**: 7 years
- **AWS CloudTrail**: 7 years

#### External Audits
- **Schedule**: Annual HIPAA compliance audit
- **Auditor**: Certified third-party auditor
- **Scope**: Full technical and administrative controls
- **Deliverables**: Compliance report and remediation plan

---

## Emergency Contacts

### Primary Contacts

#### Incident Commander
- **Name**: [Senior DevOps Engineer]
- **Phone**: +1-XXX-XXX-XXXX
- **Email**: oncall-devops@company.com
- **Backup**: [Principal Engineer]

#### Security Officer
- **Name**: [CISO]
- **Phone**: +1-XXX-XXX-XXXX
- **Email**: security-incidents@company.com
- **Backup**: [Security Manager]

#### HIPAA Privacy Officer
- **Name**: [Privacy Officer]
- **Phone**: +1-XXX-XXX-XXXX
- **Email**: privacy@company.com
- **Backup**: [Compliance Manager]

### Escalation Matrix

#### Level 1 - Technical Team (0-15 minutes)
- On-call DevOps Engineer
- Senior Backend Developer
- Database Administrator

#### Level 2 - Management (15-30 minutes)
- Engineering Manager
- Product Manager
- Security Manager

#### Level 3 - Executive (30-60 minutes)
- VP Engineering
- CISO
- Chief Privacy Officer

#### Level 4 - C-Level (1+ hours for Sev-1)
- CTO
- CEO (for data breaches)
- Legal Counsel

### External Contacts

#### AWS Support
- **Account**: Enterprise Support
- **Phone**: 1-800-221-0634
- **Case URL**: https://console.aws.amazon.com/support/

#### Security Partners
- **Incident Response Firm**: [Company Name]
- **Forensics Team**: [Company Name]
- **Legal Counsel**: [Law Firm Name]

### Communication Channels

#### Internal
- **Slack**: #clinchat-production-alerts
- **Email**: production-team@company.com
- **PagerDuty**: ClinChat-RAG Production

#### External
- **Status Page**: https://status.clinchat-rag.example.com
- **Customer Support**: support@company.com
- **Media Relations**: press@company.com

---

## Appendix

### Quick Reference Commands

```bash
# Check overall system health
kubectl get pods,svc,ingress -n clinchat-rag

# View recent application logs
kubectl logs deployment/clinchat-rag-api -n clinchat-rag --tail=50

# Scale application
kubectl scale deployment clinchat-rag-api --replicas=5 -n clinchat-rag

# Rollback to previous version
kubectl rollout undo deployment/clinchat-rag-api -n clinchat-rag

# Check database connectivity
python scripts/check-db-connection.py

# Run smoke tests
python scripts/smoke-tests.py --environment production

# Validate HIPAA compliance
python scripts/validate-hipaa-compliance.py
```

### Important URLs

```
Production Application: https://clinchat-rag.example.com
Monitoring Dashboard: https://monitoring.clinchat-rag.example.com
Status Page: https://status.clinchat-rag.example.com
Documentation: https://docs.clinchat-rag.example.com
GitHub Repository: https://github.com/company/clinchat-rag
```

### Document Version
- **Version**: 1.0
- **Last Updated**: December 2024
- **Next Review**: March 2025
- **Owner**: Platform Engineering Team