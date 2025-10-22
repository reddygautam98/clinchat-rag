#!/usr/bin/env python3
"""
HIPAA Risk Assessment Module
Comprehensive compliance checking and regulatory reporting for ClinChat-RAG
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os
import hashlib
import sqlite3
from pathlib import Path

# Database integration
try:
    from database.connection import get_db_context
    from database.models import AuditLog, User, ClinicalDocument
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk assessment levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComplianceStatus(Enum):
    """HIPAA compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNKNOWN = "unknown"

@dataclass
class RiskAssessmentItem:
    """Individual risk assessment finding"""
    category: str
    title: str
    description: str
    risk_level: RiskLevel
    compliance_status: ComplianceStatus
    remediation_steps: List[str]
    estimated_effort_hours: int
    deadline_days: int
    affected_systems: List[str]
    regulatory_reference: str

@dataclass
class HIPAARiskReport:
    """Complete HIPAA risk assessment report"""
    assessment_id: str
    timestamp: datetime
    overall_risk_score: float
    compliance_percentage: float
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    findings: List[RiskAssessmentItem]
    recommendations: List[str]
    next_assessment_date: datetime

class HIPAARiskAssessment:
    """HIPAA Risk Assessment Engine"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize HIPAA risk assessment engine"""
        self.config_path = config_path or "compliance/hipaa_config.json"
        self.assessment_db = "compliance/risk_assessments.db"
        self._initialize_database()
        self._load_compliance_rules()
        
    def _initialize_database(self):
        """Initialize assessment database"""
        db_path = Path(self.assessment_db)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.assessment_db)
        cursor = conn.cursor()
        
        # Create risk assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                overall_risk_score REAL NOT NULL,
                compliance_percentage REAL NOT NULL,
                critical_issues INTEGER NOT NULL,
                high_issues INTEGER NOT NULL,
                medium_issues INTEGER NOT NULL,
                low_issues INTEGER NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create remediation tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remediation_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_to TEXT,
                due_date TEXT,
                completed_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_id) REFERENCES risk_assessments (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _load_compliance_rules(self):
        """Load HIPAA compliance rules and checks"""
        self.compliance_rules = {
            "administrative_safeguards": {
                "security_officer": {
                    "required": True,
                    "description": "Designated security officer responsible for HIPAA compliance",
                    "check_method": "check_security_officer_designation"
                },
                "workforce_training": {
                    "required": True,
                    "description": "All workforce members trained on HIPAA requirements",
                    "check_method": "check_workforce_training"
                },
                "access_management": {
                    "required": True,
                    "description": "Proper access authorization and management procedures",
                    "check_method": "check_access_management"
                },
                "incident_procedures": {
                    "required": True,
                    "description": "Security incident response procedures",
                    "check_method": "check_incident_procedures"
                }
            },
            "physical_safeguards": {
                "facility_controls": {
                    "required": True,
                    "description": "Physical access controls to facilities and workstations",
                    "check_method": "check_facility_controls"
                },
                "workstation_security": {
                    "required": True,
                    "description": "Workstation and device security controls",
                    "check_method": "check_workstation_security"
                },
                "device_controls": {
                    "required": True,
                    "description": "Controls for mobile devices and media",
                    "check_method": "check_device_controls"
                }
            },
            "technical_safeguards": {
                "access_control": {
                    "required": True,
                    "description": "Technical access control systems",
                    "check_method": "check_technical_access_control"
                },
                "audit_controls": {
                    "required": True,
                    "description": "Audit logging and monitoring systems",
                    "check_method": "check_audit_controls"
                },
                "integrity": {
                    "required": True,
                    "description": "Data integrity protection mechanisms",
                    "check_method": "check_data_integrity"
                },
                "transmission_security": {
                    "required": True,
                    "description": "Secure data transmission controls",
                    "check_method": "check_transmission_security"
                }
            }
        }
    
    async def conduct_full_assessment(self) -> HIPAARiskReport:
        """Conduct comprehensive HIPAA risk assessment"""
        logger.info("Starting comprehensive HIPAA risk assessment...")
        
        assessment_id = self._generate_assessment_id()
        findings = []
        
        # Administrative Safeguards Assessment
        admin_findings = await self._assess_administrative_safeguards()
        findings.extend(admin_findings)
        
        # Physical Safeguards Assessment  
        physical_findings = await self._assess_physical_safeguards()
        findings.extend(physical_findings)
        
        # Technical Safeguards Assessment
        technical_findings = await self._assess_technical_safeguards()
        findings.extend(technical_findings)
        
        # Business Associate Assessment
        ba_findings = await self._assess_business_associates()
        findings.extend(ba_findings)
        
        # Data Handling Assessment
        data_findings = await self._assess_data_handling()
        findings.extend(data_findings)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(findings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings)
        
        # Create assessment report
        report = HIPAARiskReport(
            assessment_id=assessment_id,
            timestamp=datetime.now(),
            overall_risk_score=risk_metrics["overall_risk_score"],
            compliance_percentage=risk_metrics["compliance_percentage"],
            critical_issues=risk_metrics["critical_issues"],
            high_issues=risk_metrics["high_issues"],
            medium_issues=risk_metrics["medium_issues"],
            low_issues=risk_metrics["low_issues"],
            findings=findings,
            recommendations=recommendations,
            next_assessment_date=datetime.now() + timedelta(days=180)  # 6 months
        )
        
        # Save assessment to database
        await self._save_assessment(report)
        
        logger.info(f"HIPAA risk assessment completed. ID: {assessment_id}")
        return report
    
    async def _assess_administrative_safeguards(self) -> List[RiskAssessmentItem]:
        """Assess administrative safeguards compliance"""
        findings = []
        
        # Security Officer Check
        security_officer_finding = await self._check_security_officer_designation()
        findings.append(security_officer_finding)
        
        # Workforce Training Check
        training_finding = await self._check_workforce_training()
        findings.append(training_finding)
        
        # Access Management Check
        access_mgmt_finding = await self._check_access_management()
        findings.append(access_mgmt_finding)
        
        # Incident Procedures Check
        incident_finding = await self._check_incident_procedures()
        findings.append(incident_finding)
        
        return findings
    
    async def _assess_physical_safeguards(self) -> List[RiskAssessmentItem]:
        """Assess physical safeguards compliance"""
        findings = []
        
        # Facility Controls Check
        facility_finding = RiskAssessmentItem(
            category="Physical Safeguards",
            title="Facility Access Controls",
            description="Cloud-based deployment on AWS with physical security managed by AWS data centers",
            risk_level=RiskLevel.LOW,
            compliance_status=ComplianceStatus.COMPLIANT,
            remediation_steps=[],
            estimated_effort_hours=0,
            deadline_days=0,
            affected_systems=["AWS Infrastructure"],
            regulatory_reference="45 CFR 164.310(a)"
        )
        findings.append(facility_finding)
        
        # Workstation Security Check
        workstation_finding = await self._check_workstation_security()
        findings.append(workstation_finding)
        
        return findings
    
    async def _assess_technical_safeguards(self) -> List[RiskAssessmentItem]:
        """Assess technical safeguards compliance"""
        findings = []
        
        # Access Control Check
        access_control_finding = await self._check_technical_access_control()
        findings.append(access_control_finding)
        
        # Audit Controls Check  
        audit_finding = await self._check_audit_controls()
        findings.append(audit_finding)
        
        # Data Integrity Check
        integrity_finding = await self._check_data_integrity()
        findings.append(integrity_finding)
        
        # Transmission Security Check
        transmission_finding = await self._check_transmission_security()
        findings.append(transmission_finding)
        
        return findings
    
    async def _assess_business_associates(self) -> List[RiskAssessmentItem]:
        """Assess Business Associate Agreement compliance"""
        findings = []
        
        # Google Gemini BAA Check
        google_baa_finding = RiskAssessmentItem(
            category="Business Associates",
            title="Google Gemini BAA Required",
            description="Business Associate Agreement needed with Google for Gemini API usage with PHI",
            risk_level=RiskLevel.CRITICAL,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
            remediation_steps=[
                "Contact Google Cloud sales team for BAA execution",
                "Review and negotiate BAA terms for Gemini API",
                "Implement BAA tracking and renewal system",
                "Document BAA execution in compliance records"
            ],
            estimated_effort_hours=16,
            deadline_days=30,
            affected_systems=["Fusion AI Engine", "Google Gemini Integration"],
            regulatory_reference="45 CFR 164.502(e)"
        )
        findings.append(google_baa_finding)
        
        # Groq BAA Check
        groq_baa_finding = RiskAssessmentItem(
            category="Business Associates",
            title="Groq BAA Required",
            description="Business Associate Agreement needed with Groq for API usage with PHI",
            risk_level=RiskLevel.CRITICAL,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
            remediation_steps=[
                "Contact Groq legal team for BAA execution",
                "Review Groq's HIPAA compliance documentation",
                "Negotiate and execute BAA for clinical data processing",
                "Implement BAA tracking for renewal management"
            ],
            estimated_effort_hours=12,
            deadline_days=30,
            affected_systems=["Fusion AI Engine", "Groq Integration"],
            regulatory_reference="45 CFR 164.502(e)"
        )
        findings.append(groq_baa_finding)
        
        return findings
    
    async def _assess_data_handling(self) -> List[RiskAssessmentItem]:
        """Assess PHI data handling compliance"""
        findings = []
        
        # PHI Detection Check
        phi_detection_finding = RiskAssessmentItem(
            category="Data Handling",
            title="PHI Detection System Validation",
            description="PHI detection algorithms need validation and testing with clinical data sets",
            risk_level=RiskLevel.HIGH,
            compliance_status=ComplianceStatus.PARTIAL,
            remediation_steps=[
                "Implement comprehensive PHI detection testing suite",
                "Validate detection accuracy with clinical test data",
                "Document detection algorithm performance metrics",
                "Create false positive/negative handling procedures"
            ],
            estimated_effort_hours=24,
            deadline_days=45,
            affected_systems=["NLP Pipeline", "De-identification Engine"],
            regulatory_reference="45 CFR 164.514(b)"
        )
        findings.append(phi_detection_finding)
        
        # Data Encryption Check
        encryption_finding = await self._check_data_encryption()
        findings.append(encryption_finding)
        
        return findings
    
    async def _check_security_officer_designation(self) -> RiskAssessmentItem:
        """Check if security officer is properly designated"""
        # Check environment variables and configuration
        admin_email = os.getenv("ADMIN_EMAIL")
        
        if admin_email and "@" in admin_email:
            return RiskAssessmentItem(
                category="Administrative Safeguards",
                title="Security Officer Designation",
                description="Security officer designated in system configuration",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                remediation_steps=[],
                estimated_effort_hours=0,
                deadline_days=0,
                affected_systems=["User Management"],
                regulatory_reference="45 CFR 164.308(a)(2)"
            )
        else:
            return RiskAssessmentItem(
                category="Administrative Safeguards",
                title="Security Officer Not Designated",
                description="No security officer designated in system configuration",
                risk_level=RiskLevel.HIGH,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Designate qualified security officer",
                    "Update ADMIN_EMAIL environment variable",
                    "Document security officer responsibilities",
                    "Implement security officer training program"
                ],
                estimated_effort_hours=8,
                deadline_days=14,
                affected_systems=["User Management", "Access Control"],
                regulatory_reference="45 CFR 164.308(a)(2)"
            )
    
    async def _check_workforce_training(self) -> RiskAssessmentItem:
        """Check workforce HIPAA training status"""
        return RiskAssessmentItem(
            category="Administrative Safeguards",
            title="Workforce Training Program",
            description="HIPAA training program needs implementation for all system users",
            risk_level=RiskLevel.HIGH,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
            remediation_steps=[
                "Develop HIPAA training curriculum",
                "Implement training tracking system",
                "Create training completion certificates",
                "Schedule regular training updates"
            ],
            estimated_effort_hours=20,
            deadline_days=60,
            affected_systems=["User Management", "Training System"],
            regulatory_reference="45 CFR 164.308(a)(5)"
        )
    
    async def _check_access_management(self) -> RiskAssessmentItem:
        """Check access authorization and management procedures"""
        # Check if RBAC is enabled
        rbac_enabled = os.getenv("ENABLE_RBAC", "false").lower() == "true"
        
        if rbac_enabled:
            return RiskAssessmentItem(
                category="Administrative Safeguards",
                title="Access Management System",
                description="Role-based access control system implemented",
                risk_level=RiskLevel.MEDIUM,
                compliance_status=ComplianceStatus.PARTIAL,
                remediation_steps=[
                    "Implement comprehensive access review procedures",
                    "Create access request and approval workflows",
                    "Document minimum necessary access principles",
                    "Implement automated access reviews"
                ],
                estimated_effort_hours=12,
                deadline_days=30,
                affected_systems=["Authentication", "Authorization"],
                regulatory_reference="45 CFR 164.308(a)(4)"
            )
        else:
            return RiskAssessmentItem(
                category="Administrative Safeguards",
                title="Access Management Missing",
                description="Role-based access control not properly implemented",
                risk_level=RiskLevel.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Enable RBAC system (ENABLE_RBAC=true)",
                    "Implement role-based access controls",
                    "Create user access provisioning procedures",
                    "Implement access review and audit processes"
                ],
                estimated_effort_hours=16,
                deadline_days=14,
                affected_systems=["Authentication", "Authorization", "User Management"],
                regulatory_reference="45 CFR 164.308(a)(4)"
            )
    
    async def _check_incident_procedures(self) -> RiskAssessmentItem:
        """Check security incident response procedures"""
        return RiskAssessmentItem(
            category="Administrative Safeguards",
            title="Security Incident Procedures",
            description="Formal security incident response procedures need implementation",
            risk_level=RiskLevel.HIGH,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
            remediation_steps=[
                "Develop incident response plan and procedures",
                "Create incident reporting and notification system",
                "Implement breach notification procedures",
                "Establish incident response team and training"
            ],
            estimated_effort_hours=16,
            deadline_days=30,
            affected_systems=["Security Monitoring", "Incident Management"],
            regulatory_reference="45 CFR 164.308(a)(6)"
        )
    
    async def _check_workstation_security(self) -> RiskAssessmentItem:
        """Check workstation security controls"""
        return RiskAssessmentItem(
            category="Physical Safeguards",
            title="Workstation Security Controls",
            description="Workstation access controls and security policies need implementation",
            risk_level=RiskLevel.MEDIUM,
            compliance_status=ComplianceStatus.PARTIAL,
            remediation_steps=[
                "Implement workstation access control policies",
                "Create secure workstation configuration standards",
                "Implement automatic screen locks and timeouts",
                "Document workstation security procedures"
            ],
            estimated_effort_hours=8,
            deadline_days=45,
            affected_systems=["Workstation Management"],
            regulatory_reference="45 CFR 164.310(b)"
        )
    
    async def _check_technical_access_control(self) -> RiskAssessmentItem:
        """Check technical access control implementation"""
        # Check authentication configuration
        jwt_secret = os.getenv("SECRET_KEY", "")
        
        if len(jwt_secret) >= 32 and jwt_secret != "your_super_secret_jwt_key_here_min_32_characters":
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Access Control System",
                description="Technical access control system implemented with JWT authentication",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                remediation_steps=[
                    "Implement multi-factor authentication",
                    "Add session timeout controls",
                    "Enhance password complexity requirements"
                ],
                estimated_effort_hours=8,
                deadline_days=60,
                affected_systems=["Authentication API"],
                regulatory_reference="45 CFR 164.312(a)"
            )
        else:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Weak Access Control Configuration",
                description="JWT secret key is default or weak, compromising access control security",
                risk_level=RiskLevel.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Generate strong JWT secret key (32+ characters)",
                    "Implement proper secrets management",
                    "Add multi-factor authentication",
                    "Implement session management controls"
                ],
                estimated_effort_hours=4,
                deadline_days=7,
                affected_systems=["Authentication API", "User Sessions"],
                regulatory_reference="45 CFR 164.312(a)"
            )
    
    async def _check_audit_controls(self) -> RiskAssessmentItem:
        """Check audit logging and controls"""
        audit_enabled = os.getenv("ENABLE_AUDIT_LOGGING", "false").lower() == "true"
        
        if audit_enabled:
            return RiskAssessmentItem(
                category="Technical Safeguards", 
                title="Audit Controls System",
                description="Basic audit logging enabled, but needs enhancement for full HIPAA compliance",
                risk_level=RiskLevel.MEDIUM,
                compliance_status=ComplianceStatus.PARTIAL,
                remediation_steps=[
                    "Enhance audit logging to capture all PHI access",
                    "Implement tamper-proof audit log storage",
                    "Create audit log review and monitoring procedures",
                    "Add automated anomaly detection for audit logs"
                ],
                estimated_effort_hours=20,
                deadline_days=30,
                affected_systems=["Audit Logging", "Database"],
                regulatory_reference="45 CFR 164.312(b)"
            )
        else:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Audit Controls Missing",
                description="Audit logging not enabled - critical HIPAA requirement missing",
                risk_level=RiskLevel.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Enable comprehensive audit logging (ENABLE_AUDIT_LOGGING=true)",
                    "Implement audit log capture for all PHI access",
                    "Create tamper-proof audit log storage system",
                    "Implement audit log monitoring and review procedures"
                ],
                estimated_effort_hours=16,
                deadline_days=14,
                affected_systems=["Audit System", "Database", "API"],
                regulatory_reference="45 CFR 164.312(b)"
            )
    
    async def _check_data_integrity(self) -> RiskAssessmentItem:
        """Check data integrity protection mechanisms"""
        encryption_enabled = os.getenv("ENABLE_FIELD_ENCRYPTION", "false").lower() == "true"
        
        if encryption_enabled:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Data Integrity Controls",
                description="Field-level encryption enabled for data integrity protection",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                remediation_steps=[
                    "Implement data integrity verification checksums",
                    "Add database backup integrity verification",
                    "Create data corruption detection and recovery procedures"
                ],
                estimated_effort_hours=12,
                deadline_days=60,
                affected_systems=["Database", "Backup System"],
                regulatory_reference="45 CFR 164.312(c)"
            )
        else:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Data Integrity Controls Missing",
                description="Field-level encryption not enabled, data integrity at risk",
                risk_level=RiskLevel.HIGH,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Enable field-level encryption (ENABLE_FIELD_ENCRYPTION=true)",
                    "Implement data integrity checksums and verification",
                    "Create secure backup and recovery procedures",
                    "Implement database integrity monitoring"
                ],
                estimated_effort_hours=16,
                deadline_days=21,
                affected_systems=["Database", "Data Storage"],
                regulatory_reference="45 CFR 164.312(c)"
            )
    
    async def _check_transmission_security(self) -> RiskAssessmentItem:
        """Check data transmission security"""
        use_tls = os.getenv("USE_TLS", "false").lower() == "true"
        
        if use_tls:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Transmission Security",
                description="TLS encryption configured for secure data transmission",
                risk_level=RiskLevel.LOW,
                compliance_status=ComplianceStatus.COMPLIANT,
                remediation_steps=[
                    "Verify TLS 1.3 is used for all connections",
                    "Implement certificate management procedures",
                    "Add transmission integrity verification"
                ],
                estimated_effort_hours=4,
                deadline_days=30,
                affected_systems=["API Gateway", "Web Server"],
                regulatory_reference="45 CFR 164.312(e)"
            )
        else:
            return RiskAssessmentItem(
                category="Technical Safeguards",
                title="Transmission Security Missing",
                description="TLS encryption not properly configured for data transmission",
                risk_level=RiskLevel.HIGH,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Enable TLS encryption (USE_TLS=true)",
                    "Configure TLS certificates and key management",
                    "Implement end-to-end encryption for all PHI transmission",
                    "Add transmission integrity verification"
                ],
                estimated_effort_hours=8,
                deadline_days=14,
                affected_systems=["API Gateway", "Web Server", "Load Balancer"],
                regulatory_reference="45 CFR 164.312(e)"
            )
    
    async def _check_data_encryption(self) -> RiskAssessmentItem:
        """Check data encryption implementation"""
        encryption_key = os.getenv("ENCRYPTION_KEY", "")
        
        if len(encryption_key) >= 32 and encryption_key != "your_32_character_encryption_key_here":
            return RiskAssessmentItem(
                category="Data Handling",
                title="Data Encryption System",
                description="Data encryption configured but key management needs improvement",
                risk_level=RiskLevel.MEDIUM,
                compliance_status=ComplianceStatus.PARTIAL,
                remediation_steps=[
                    "Implement proper encryption key management system",
                    "Use AWS KMS or similar key management service",
                    "Implement key rotation procedures",
                    "Add encryption key backup and recovery procedures"
                ],
                estimated_effort_hours=12,
                deadline_days=30,
                affected_systems=["Database", "File Storage"],
                regulatory_reference="45 CFR 164.312(a)(2)(iv)"
            )
        else:
            return RiskAssessmentItem(
                category="Data Handling",
                title="Weak Data Encryption",
                description="Encryption key is default or weak, PHI data at risk",
                risk_level=RiskLevel.CRITICAL,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                remediation_steps=[
                    "Generate strong encryption key (32+ characters)",
                    "Implement AWS KMS or similar key management",
                    "Enable encryption for all PHI data at rest",
                    "Implement secure key storage and rotation"
                ],
                estimated_effort_hours=8,
                deadline_days=7,
                affected_systems=["Database", "File Storage", "Backup System"],
                regulatory_reference="45 CFR 164.312(a)(2)(iv)"
            )
    
    def _calculate_risk_metrics(self, findings: List[RiskAssessmentItem]) -> Dict[str, Any]:
        """Calculate overall risk metrics from findings"""
        total_findings = len(findings)
        if total_findings == 0:
            return {
                "overall_risk_score": 0.0,
                "compliance_percentage": 100.0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0
            }
        
        # Count issues by severity
        critical_issues = sum(1 for f in findings if f.risk_level == RiskLevel.CRITICAL)
        high_issues = sum(1 for f in findings if f.risk_level == RiskLevel.HIGH)
        medium_issues = sum(1 for f in findings if f.risk_level == RiskLevel.MEDIUM)
        low_issues = sum(1 for f in findings if f.risk_level == RiskLevel.LOW)
        
        # Calculate weighted risk score (0-100)
        risk_weights = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 10,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 1
        }
        
        total_risk_score = sum(risk_weights[f.risk_level] for f in findings)
        max_possible_score = total_findings * risk_weights[RiskLevel.CRITICAL]
        overall_risk_score = (total_risk_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        # Calculate compliance percentage
        compliant_count = sum(1 for f in findings if f.compliance_status == ComplianceStatus.COMPLIANT)
        partial_count = sum(1 for f in findings if f.compliance_status == ComplianceStatus.PARTIAL)
        compliance_percentage = ((compliant_count + (partial_count * 0.5)) / total_findings) * 100
        
        return {
            "overall_risk_score": overall_risk_score,
            "compliance_percentage": compliance_percentage,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "low_issues": low_issues
        }
    
    def _generate_recommendations(self, findings: List[RiskAssessmentItem]) -> List[str]:
        """Generate prioritized recommendations based on findings"""
        recommendations = []
        
        # Critical issues first
        critical_findings = [f for f in findings if f.risk_level == RiskLevel.CRITICAL]
        if critical_findings:
            recommendations.append(
                f"🚨 IMMEDIATE ACTION: Address {len(critical_findings)} critical security issues within 7 days"
            )
            for finding in critical_findings:
                recommendations.append(f"   • {finding.title}: {finding.remediation_steps[0]}")
        
        # High priority issues
        high_findings = [f for f in findings if f.risk_level == RiskLevel.HIGH]
        if high_findings:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: Resolve {len(high_findings)} high-risk issues within 30 days"
            )
        
        # Compliance status summary
        non_compliant = sum(1 for f in findings if f.compliance_status == ComplianceStatus.NON_COMPLIANT)
        if non_compliant > 0:
            recommendations.append(
                f"📋 COMPLIANCE: {non_compliant} non-compliant areas require immediate attention"
            )
        
        # General recommendations
        recommendations.extend([
            "🔒 Implement comprehensive secrets management system",
            "📚 Develop HIPAA training program for all users", 
            "🔍 Establish regular compliance monitoring and assessment schedule",
            "📄 Document all security policies and procedures",
            "🤝 Execute Business Associate Agreements with all AI providers"
        ])
        
        return recommendations
    
    def _generate_assessment_id(self) -> str:
        """Generate unique assessment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_input = f"hipaa_assessment_{timestamp}_{os.getpid()}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"HIPAA_{timestamp}_{hash_value}"
    
    async def _save_assessment(self, report: HIPAARiskReport):
        """Save assessment report to database"""
        conn = sqlite3.connect(self.assessment_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO risk_assessments (
                id, timestamp, overall_risk_score, compliance_percentage,
                critical_issues, high_issues, medium_issues, low_issues, report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report.assessment_id,
            report.timestamp.isoformat(),
            report.overall_risk_score,
            report.compliance_percentage,
            report.critical_issues,
            report.high_issues,
            report.medium_issues,
            report.low_issues,
            json.dumps(asdict(report), default=str)
        ))
        
        conn.commit()
        conn.close()
    
    async def generate_compliance_report(self, assessment_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate formatted compliance report"""
        if assessment_id:
            # Get specific assessment
            report = await self._get_assessment_by_id(assessment_id)
        else:
            # Get latest assessment
            report = await self.conduct_full_assessment()
        
        # Generate report sections
        executive_summary = self._generate_executive_summary(report)
        detailed_findings = self._generate_detailed_findings(report)
        remediation_plan = self._generate_remediation_plan(report)
        
        return {
            "assessment_id": report.assessment_id,
            "timestamp": report.timestamp,
            "executive_summary": executive_summary,
            "detailed_findings": detailed_findings,
            "remediation_plan": remediation_plan,
            "compliance_percentage": report.compliance_percentage,
            "overall_risk_score": report.overall_risk_score,
            "next_assessment_date": report.next_assessment_date
        }
    
    def _generate_executive_summary(self, report: HIPAARiskReport) -> str:
        """Generate executive summary of risk assessment"""
        risk_status = "HIGH RISK" if report.overall_risk_score > 70 else \
                     "MEDIUM RISK" if report.overall_risk_score > 40 else "LOW RISK"
        
        compliance_status = "NON-COMPLIANT" if report.compliance_percentage < 70 else \
                           "PARTIALLY COMPLIANT" if report.compliance_percentage < 90 else \
                           "COMPLIANT"
        
        return f"""
HIPAA Risk Assessment Executive Summary
Assessment ID: {report.assessment_id}
Date: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

OVERALL STATUS: {risk_status} | {compliance_status}
Compliance Level: {report.compliance_percentage:.1f}%
Risk Score: {report.overall_risk_score:.1f}/100

CRITICAL ISSUES: {report.critical_issues}
HIGH PRIORITY: {report.high_issues}
MEDIUM PRIORITY: {report.medium_issues}
LOW PRIORITY: {report.low_issues}

{' '.join(report.recommendations[:3])}

Next Assessment Due: {report.next_assessment_date.strftime('%Y-%m-%d')}
        """
    
    def _generate_detailed_findings(self, report: HIPAARiskReport) -> List[Dict[str, Any]]:
        """Generate detailed findings for report"""
        return [
            {
                "category": finding.category,
                "title": finding.title,
                "description": finding.description,
                "risk_level": finding.risk_level.value,
                "compliance_status": finding.compliance_status.value,
                "remediation_steps": finding.remediation_steps,
                "estimated_effort_hours": finding.estimated_effort_hours,
                "deadline_days": finding.deadline_days,
                "affected_systems": finding.affected_systems,
                "regulatory_reference": finding.regulatory_reference
            }
            for finding in report.findings
        ]
    
    def _generate_remediation_plan(self, report: HIPAARiskReport) -> List[Dict[str, Any]]:
        """Generate prioritized remediation plan"""
        # Sort findings by risk level and deadline
        priority_order = {
            RiskLevel.CRITICAL: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 4
        }
        
        sorted_findings = sorted(
            report.findings,
            key=lambda x: (priority_order[x.risk_level], x.deadline_days)
        )
        
        remediation_plan = []
        for i, finding in enumerate(sorted_findings, 1):
            remediation_plan.append({
                "priority": i,
                "title": finding.title,
                "category": finding.category,
                "risk_level": finding.risk_level.value,
                "estimated_effort_hours": finding.estimated_effort_hours,
                "deadline_days": finding.deadline_days,
                "remediation_steps": finding.remediation_steps,
                "affected_systems": finding.affected_systems
            })
        
        return remediation_plan

# CLI interface for running assessments
async def main():
    """Main CLI interface for HIPAA risk assessment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClinChat-RAG HIPAA Risk Assessment")
    parser.add_argument("--assess", action="store_true", help="Conduct full risk assessment")
    parser.add_argument("--report", type=str, help="Generate report for assessment ID")
    parser.add_argument("--output", type=str, default="console", choices=["console", "json", "html"], 
                       help="Output format")
    
    args = parser.parse_args()
    
    assessment_engine = HIPAARiskAssessment()
    
    if args.assess:
        print("🔍 Conducting HIPAA Risk Assessment...")
        report = await assessment_engine.conduct_full_assessment()
        
        if args.output == "json":
            print(json.dumps(asdict(report), default=str, indent=2))
        else:
            # Console output
            print(f"\n{'='*60}")
            print(f"HIPAA RISK ASSESSMENT COMPLETE")
            print(f"{'='*60}")
            print(f"Assessment ID: {report.assessment_id}")
            print(f"Timestamp: {report.timestamp}")
            print(f"Overall Risk Score: {report.overall_risk_score:.1f}/100")
            print(f"Compliance Percentage: {report.compliance_percentage:.1f}%")
            print(f"\nIssue Summary:")
            print(f"  Critical: {report.critical_issues}")
            print(f"  High: {report.high_issues}")
            print(f"  Medium: {report.medium_issues}")
            print(f"  Low: {report.low_issues}")
            print(f"\nTop Recommendations:")
            for rec in report.recommendations[:5]:
                print(f"  • {rec}")
            
    elif args.report:
        compliance_report = await assessment_engine.generate_compliance_report(args.report)
        
        if args.output == "json":
            print(json.dumps(compliance_report, default=str, indent=2))
        else:
            print(compliance_report["executive_summary"])

if __name__ == "__main__":
    asyncio.run(main())