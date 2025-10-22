#!/usr/bin/env python3
"""
Enhanced Audit Logging System for HIPAA Compliance
Comprehensive audit trail with tamper-proof storage and compliance reporting
"""

import asyncio
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from pathlib import Path
import os
import uuid
import threading
from cryptography.fernet import Fernet
import gzip
import base64

# Database integration
try:
    from database.connection import get_db_context
    from database.models import User
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PHI_ACCESS = "phi_access"
    PHI_EXPORT = "phi_export"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_ACCESS = "document_access"
    DOCUMENT_DELETE = "document_delete"
    AI_ANALYSIS = "ai_analysis"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    API_ACCESS = "api_access"
    DATABASE_QUERY = "database_query"
    BACKUP_RESTORE = "backup_restore"
    SYSTEM_ERROR = "system_error"

class AuditSeverity(Enum):
    """Severity levels for audit events"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ComplianceStandard(Enum):
    """Compliance standards"""
    HIPAA = "hipaa"
    GXP = "gxp"
    FDA_21CFR11 = "fda_21cfr11"
    GDPR = "gdpr"
    SOX = "sox"

@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    action: str
    description: str
    details: Dict[str, Any]
    compliance_standards: List[ComplianceStandard]
    phi_involved: bool
    outcome: str  # success, failure, partial
    error_message: Optional[str] = None
    hash_signature: Optional[str] = field(default=None, init=False)
    previous_hash: Optional[str] = field(default=None, init=False)

@dataclass
class AuditQuery:
    """Query parameters for audit log searches"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[AuditEventType]] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[AuditSeverity] = None
    phi_involved: Optional[bool] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None
    limit: int = 1000
    offset: int = 0

class EnhancedAuditLogger:
    """Enhanced audit logging system with HIPAA compliance"""
    
    def __init__(self, db_path: str = "compliance/audit_logs.db", 
                 encryption_key: Optional[str] = None):
        """Initialize enhanced audit logger"""
        self.db_path = db_path
        self.encryption_key = encryption_key or os.getenv("AUDIT_ENCRYPTION_KEY")
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
            logger.warning("Generated new audit encryption key - store securely!")
        
        self.cipher = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) 
                           else self.encryption_key)
        self._lock = threading.Lock()
        self._initialize_database()
        self._last_hash = self._get_last_hash()
        
    def _initialize_database(self):
        """Initialize audit logging database with tamper-proof design"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main audit events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                source_ip TEXT,
                user_agent TEXT,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                action TEXT NOT NULL,
                description TEXT NOT NULL,
                details TEXT,  -- Encrypted JSON
                compliance_standards TEXT,  -- JSON array
                phi_involved BOOLEAN NOT NULL,
                outcome TEXT NOT NULL,
                error_message TEXT,
                hash_signature TEXT NOT NULL,
                previous_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audit log integrity table for tamper detection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_integrity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                start_event_id TEXT NOT NULL,
                end_event_id TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                batch_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                verified BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Audit log access tracking (who accessed the audit logs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                query_parameters TEXT,  -- JSON
                records_accessed INTEGER,
                access_reason TEXT,
                supervisor_approval TEXT
            )
        ''')
        
        # Compliance reporting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                compliance_standard TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                total_events INTEGER NOT NULL,
                phi_events INTEGER NOT NULL,
                security_events INTEGER NOT NULL,
                report_data TEXT,  -- JSON
                generated_at TEXT NOT NULL,
                generated_by TEXT NOT NULL
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_phi ON audit_events(phi_involved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_events(severity)')
        
        conn.commit()
        conn.close()
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last audit event for chain integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT hash_signature FROM audit_events
                ORDER BY timestamp DESC, event_id DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else "genesis_hash"
            
        except Exception as e:
            logger.error(f"Error getting last hash: {e}")
            return "genesis_hash"
    
    def _calculate_event_hash(self, event: AuditEvent) -> str:
        """Calculate tamper-proof hash for audit event"""
        # Create hash input from critical event data
        hash_input = (
            f"{event.event_id}|{event.timestamp.isoformat()}|"
            f"{event.event_type.value}|{event.user_id}|{event.action}|"
            f"{event.resource_type}|{event.resource_id}|{event.phi_involved}|"
            f"{event.outcome}|{self._last_hash}"
        )
        
        # Use HMAC for additional security
        secret_key = (self.encryption_key + "audit_hash_salt").encode()
        signature = hmac.new(secret_key, hash_input.encode(), hashlib.sha256).hexdigest()
        
        return signature
    
    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> str:
        """Encrypt sensitive audit data"""
        try:
            json_data = json.dumps(data, default=str)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting audit data: {e}")
            return base64.b64encode(json.dumps({"error": "encryption_failed"}).encode()).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt sensitive audit data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Error decrypting audit data: {e}")
            return {"error": "decryption_failed"}
    
    async def log_event(self, event: AuditEvent) -> bool:
        """Log audit event with tamper-proof storage"""
        try:
            with self._lock:
                # Calculate hash signature
                event.previous_hash = self._last_hash
                event.hash_signature = self._calculate_event_hash(event)
                
                # Encrypt sensitive details
                encrypted_details = self._encrypt_sensitive_data(event.details)
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_events (
                        event_id, timestamp, event_type, severity, user_id, session_id,
                        source_ip, user_agent, resource_type, resource_id, action,
                        description, details, compliance_standards, phi_involved,
                        outcome, error_message, hash_signature, previous_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.severity.value,
                    event.user_id,
                    event.session_id,
                    event.source_ip,
                    event.user_agent,
                    event.resource_type,
                    event.resource_id,
                    event.action,
                    event.description,
                    encrypted_details,
                    json.dumps([std.value for std in event.compliance_standards]),
                    event.phi_involved,
                    event.outcome,
                    event.error_message,
                    event.hash_signature,
                    event.previous_hash
                ))
                
                conn.commit()
                conn.close()
                
                # Update last hash for chain integrity
                self._last_hash = event.hash_signature
                
                # Log to file system as backup
                self._backup_to_file(event)
                
                return True
                
        except Exception as e:
            logger.error(f"Error logging audit event {event.event_id}: {e}")
            return False
    
    def _backup_to_file(self, event: AuditEvent):
        """Backup audit event to file system"""
        try:
            backup_dir = Path("logs/audit_backup")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create daily backup files
            date_str = event.timestamp.strftime("%Y%m%d")
            backup_file = backup_dir / f"audit_{date_str}.log"
            
            # Create backup entry
            backup_entry = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "action": event.action,
                "resource": f"{event.resource_type}/{event.resource_id}",
                "phi_involved": event.phi_involved,
                "outcome": event.outcome,
                "hash": event.hash_signature
            }
            
            # Append to backup file
            with open(backup_file, "a") as f:
                f.write(json.dumps(backup_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error creating audit backup: {e}")
    
    async def log_phi_access(self, user_id: str, resource_type: str, resource_id: str,
                           action: str, session_id: str, source_ip: str,
                           details: Optional[Dict[str, Any]] = None) -> str:
        """Log PHI access event"""
        event_id = str(uuid.uuid4())
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=AuditEventType.PHI_ACCESS,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip,
            user_agent=None,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=f"PHI access: {action} on {resource_type}",
            details=details or {},
            compliance_standards=[ComplianceStandard.HIPAA],
            phi_involved=True,
            outcome="success"
        )
        
        await self.log_event(event)
        return event_id
    
    async def log_user_authentication(self, user_id: str, action: str, outcome: str,
                                    source_ip: str, details: Optional[Dict[str, Any]] = None) -> str:
        """Log user authentication event"""
        event_id = str(uuid.uuid4())
        
        event_type = AuditEventType.USER_LOGIN if action == "login" else AuditEventType.USER_LOGOUT
        severity = AuditSeverity.MEDIUM if outcome == "success" else AuditSeverity.HIGH
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            session_id=None,
            source_ip=source_ip,
            user_agent=details.get("user_agent") if details else None,
            resource_type="authentication",
            resource_id=None,
            action=action,
            description=f"User {action}: {outcome}",
            details=details or {},
            compliance_standards=[ComplianceStandard.HIPAA, ComplianceStandard.GXP],
            phi_involved=False,
            outcome=outcome,
            error_message=details.get("error") if details and outcome == "failure" else None
        )
        
        await self.log_event(event)
        return event_id
    
    async def log_ai_analysis(self, user_id: str, analysis_type: str, provider: str,
                            document_id: str, session_id: str, processing_time: float,
                            phi_detected: bool, details: Optional[Dict[str, Any]] = None) -> str:
        """Log AI analysis event"""
        event_id = str(uuid.uuid4())
        
        event_details = {
            "analysis_type": analysis_type,
            "ai_provider": provider,
            "processing_time_seconds": processing_time,
            "phi_detected": phi_detected,
            **(details or {})
        }
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=AuditEventType.AI_ANALYSIS,
            severity=AuditSeverity.HIGH if phi_detected else AuditSeverity.MEDIUM,
            user_id=user_id,
            session_id=session_id,
            source_ip=None,
            user_agent=None,
            resource_type="clinical_document",
            resource_id=document_id,
            action="ai_analysis",
            description=f"AI analysis using {provider}: {analysis_type}",
            details=event_details,
            compliance_standards=[ComplianceStandard.HIPAA, ComplianceStandard.FDA_21CFR11],
            phi_involved=phi_detected,
            outcome="success"
        )
        
        await self.log_event(event)
        return event_id
    
    async def log_security_event(self, event_type: str, severity: AuditSeverity,
                               description: str, source_ip: Optional[str] = None,
                               details: Optional[Dict[str, Any]] = None) -> str:
        """Log security event"""
        event_id = str(uuid.uuid4())
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            user_id=None,
            session_id=None,
            source_ip=source_ip,
            user_agent=None,
            resource_type="system",
            resource_id=None,
            action=event_type,
            description=description,
            details=details or {},
            compliance_standards=[ComplianceStandard.HIPAA, ComplianceStandard.GXP],
            phi_involved=False,
            outcome="detected"
        )
        
        await self.log_event(event)
        return event_id
    
    async def query_audit_logs(self, query: AuditQuery, 
                             user_id: str, reason: str = "compliance_review") -> List[Dict[str, Any]]:
        """Query audit logs with access tracking"""
        # Log the audit access
        access_id = await self._log_audit_access(user_id, query, reason)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            sql_query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if query.start_date:
                sql_query += " AND timestamp >= ?"
                params.append(query.start_date.isoformat())
                
            if query.end_date:
                sql_query += " AND timestamp <= ?"
                params.append(query.end_date.isoformat())
                
            if query.event_types:
                placeholders = ",".join(["?" for _ in query.event_types])
                sql_query += f" AND event_type IN ({placeholders})"
                params.extend([et.value for et in query.event_types])
                
            if query.user_id:
                sql_query += " AND user_id = ?"
                params.append(query.user_id)
                
            if query.resource_type:
                sql_query += " AND resource_type = ?"
                params.append(query.resource_type)
                
            if query.severity:
                sql_query += " AND severity = ?"
                params.append(query.severity.value)
                
            if query.phi_involved is not None:
                sql_query += " AND phi_involved = ?"
                params.append(query.phi_involved)
            
            sql_query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([query.limit, query.offset])
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to list of dictionaries and decrypt details
            results = []
            for row in rows:
                record = dict(zip(columns, row))
                
                # Decrypt details if present
                if record["details"]:
                    record["details"] = self._decrypt_sensitive_data(record["details"])
                
                # Parse compliance standards
                if record["compliance_standards"]:
                    record["compliance_standards"] = json.loads(record["compliance_standards"])
                
                results.append(record)
            
            conn.close()
            
            # Update access log with count
            self._update_audit_access_count(access_id, len(results))
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying audit logs: {e}")
            return []
    
    async def _log_audit_access(self, user_id: str, query: AuditQuery, reason: str) -> str:
        """Log access to audit logs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            access_id = str(uuid.uuid4())
            query_params = {
                "start_date": query.start_date.isoformat() if query.start_date else None,
                "end_date": query.end_date.isoformat() if query.end_date else None,
                "event_types": [et.value for et in query.event_types] if query.event_types else None,
                "user_id": query.user_id,
                "resource_type": query.resource_type,
                "severity": query.severity.value if query.severity else None,
                "phi_involved": query.phi_involved,
                "limit": query.limit,
                "offset": query.offset
            }
            
            cursor.execute('''
                INSERT INTO audit_access_log (
                    access_timestamp, user_id, query_parameters, 
                    records_accessed, access_reason, supervisor_approval
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                json.dumps(query_params),
                0,  # Will be updated later
                reason,
                None  # TODO: Implement supervisor approval workflow
            ))
            
            conn.commit()
            conn.close()
            
            return access_id
            
        except Exception as e:
            logger.error(f"Error logging audit access: {e}")
            return ""
    
    def _update_audit_access_count(self, access_id: str, record_count: int):
        """Update the number of records accessed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE audit_access_log
                SET records_accessed = ?
                WHERE rowid = (
                    SELECT rowid FROM audit_access_log
                    WHERE access_timestamp = (
                        SELECT MAX(access_timestamp) FROM audit_access_log
                    )
                    LIMIT 1
                )
            ''', (record_count,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating audit access count: {e}")
    
    async def verify_audit_integrity(self) -> Dict[str, Any]:
        """Verify audit log integrity and detect tampering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all audit events ordered by timestamp
            cursor.execute('''
                SELECT event_id, timestamp, event_type, user_id, action,
                       resource_type, resource_id, phi_involved, outcome,
                       hash_signature, previous_hash
                FROM audit_events
                ORDER BY timestamp ASC, event_id ASC
            ''')
            
            events = cursor.fetchall()
            conn.close()
            
            if not events:
                return {"status": "no_events", "integrity": True, "issues": []}
            
            integrity_issues = []
            previous_hash = "genesis_hash"
            verified_count = 0
            
            for event in events:
                event_id, timestamp, event_type, user_id, action, resource_type, resource_id, phi_involved, outcome, hash_signature, stored_previous_hash = event
                
                # Verify hash chain
                if stored_previous_hash != previous_hash:
                    integrity_issues.append({
                        "event_id": event_id,
                        "issue": "hash_chain_broken",
                        "expected_previous_hash": previous_hash,
                        "actual_previous_hash": stored_previous_hash
                    })
                
                # Recalculate hash to verify integrity
                hash_input = (
                    f"{event_id}|{timestamp}|{event_type}|{user_id}|{action}|"
                    f"{resource_type}|{resource_id}|{phi_involved}|{outcome}|{previous_hash}"
                )
                
                secret_key = (self.encryption_key + "audit_hash_salt").encode()
                expected_hash = hmac.new(secret_key, hash_input.encode(), hashlib.sha256).hexdigest()
                
                if expected_hash != hash_signature:
                    integrity_issues.append({
                        "event_id": event_id,
                        "issue": "hash_mismatch",
                        "expected_hash": expected_hash,
                        "actual_hash": hash_signature
                    })
                else:
                    verified_count += 1
                
                previous_hash = hash_signature
            
            integrity_percentage = (verified_count / len(events)) * 100
            
            return {
                "status": "verified",
                "integrity": len(integrity_issues) == 0,
                "total_events": len(events),
                "verified_events": verified_count,
                "integrity_percentage": integrity_percentage,
                "issues": integrity_issues,
                "verification_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verifying audit integrity: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_compliance_report(self, standard: ComplianceStandard,
                                       start_date: datetime, end_date: datetime,
                                       user_id: str) -> Dict[str, Any]:
        """Generate compliance report for specific standard"""
        report_id = f"COMP_{standard.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Query relevant events
        query = AuditQuery(
            start_date=start_date,
            end_date=end_date,
            compliance_standards=[standard]
        )
        
        events = await self.query_audit_logs(query, user_id, f"compliance_report_{standard.value}")
        
        # Analyze events
        total_events = len(events)
        phi_events = len([e for e in events if e["phi_involved"]])
        security_events = len([e for e in events if e["event_type"] == AuditEventType.SECURITY_EVENT.value])
        failed_events = len([e for e in events if e["outcome"] == "failure"])
        
        # User activity analysis
        user_activity = {}
        for event in events:
            if event["user_id"]:
                if event["user_id"] not in user_activity:
                    user_activity[event["user_id"]] = {"total": 0, "phi_access": 0}
                user_activity[event["user_id"]]["total"] += 1
                if event["phi_involved"]:
                    user_activity[event["user_id"]]["phi_access"] += 1
        
        # Event type distribution
        event_distribution = {}
        for event in events:
            event_type = event["event_type"]
            event_distribution[event_type] = event_distribution.get(event_type, 0) + 1
        
        # Risk assessment
        risk_score = 0
        risk_factors = []
        
        if failed_events > 0:
            risk_score += min(failed_events * 2, 20)
            risk_factors.append(f"{failed_events} failed authentication attempts")
        
        if security_events > 0:
            risk_score += min(security_events * 5, 30)
            risk_factors.append(f"{security_events} security events detected")
        
        # High PHI access users
        high_phi_users = [uid for uid, activity in user_activity.items() 
                         if activity["phi_access"] > 50]
        if high_phi_users:
            risk_score += len(high_phi_users) * 3
            risk_factors.append(f"{len(high_phi_users)} users with high PHI access")
        
        risk_level = "HIGH" if risk_score > 30 else "MEDIUM" if risk_score > 10 else "LOW"
        
        report_data = {
            "report_id": report_id,
            "compliance_standard": standard.value,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "phi_events": phi_events,
                "security_events": security_events,
                "failed_events": failed_events,
                "unique_users": len(user_activity)
            },
            "user_activity": user_activity,
            "event_distribution": event_distribution,
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors
            },
            "compliance_recommendations": self._generate_compliance_recommendations(
                standard, total_events, phi_events, security_events, failed_events
            )
        }
        
        # Save report
        await self._save_compliance_report(report_id, standard, start_date, end_date, 
                                         total_events, phi_events, security_events, 
                                         report_data, user_id)
        
        return report_data
    
    def _generate_compliance_recommendations(self, standard: ComplianceStandard,
                                          total_events: int, phi_events: int,
                                          security_events: int, failed_events: int) -> List[str]:
        """Generate compliance recommendations based on audit analysis"""
        recommendations = []
        
        if standard == ComplianceStandard.HIPAA:
            if phi_events == 0:
                recommendations.append("No PHI access events recorded - ensure proper event logging")
            elif phi_events > 1000:
                recommendations.append("High volume of PHI access - implement additional monitoring")
            
            if security_events > 0:
                recommendations.append("Security events detected - review and strengthen security controls")
            
            if failed_events > 10:
                recommendations.append("Multiple authentication failures - implement account lockout policies")
            
            recommendations.extend([
                "Conduct regular audit log reviews (minimum quarterly)",
                "Implement automated anomaly detection for PHI access patterns",
                "Ensure all users complete HIPAA training annually",
                "Maintain audit logs for minimum 6 years as required by HIPAA"
            ])
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Continue monitoring and maintain current security posture")
        
        return recommendations
    
    async def _save_compliance_report(self, report_id: str, standard: ComplianceStandard,
                                    start_date: datetime, end_date: datetime,
                                    total_events: int, phi_events: int,
                                    security_events: int, report_data: Dict[str, Any],
                                    generated_by: str):
        """Save compliance report to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO compliance_reports (
                    report_id, report_type, compliance_standard, start_date, end_date,
                    total_events, phi_events, security_events, report_data,
                    generated_at, generated_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                "audit_analysis",
                standard.value,
                start_date.isoformat(),
                end_date.isoformat(),
                total_events,
                phi_events,
                security_events,
                json.dumps(report_data, default=str),
                datetime.now().isoformat(),
                generated_by
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving compliance report: {e}")

# CLI Interface
async def main():
    """Main CLI interface for audit logging"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClinChat-RAG Enhanced Audit Logging")
    parser.add_argument("--verify", action="store_true", help="Verify audit log integrity")
    parser.add_argument("--query", action="store_true", help="Query audit logs")
    parser.add_argument("--report", type=str, choices=["hipaa", "gxp", "fda"], 
                       help="Generate compliance report")
    parser.add_argument("--days", type=int, default=30, help="Days to look back for reports")
    parser.add_argument("--user", type=str, default="admin", help="User ID for operations")
    
    args = parser.parse_args()
    
    audit_logger = EnhancedAuditLogger()
    
    if args.verify:
        print("🔍 Verifying audit log integrity...")
        result = await audit_logger.verify_audit_integrity()
        
        print(f"Status: {result['status']}")
        if result.get('integrity'):
            print("✅ Audit log integrity verified")
            print(f"Total events: {result['total_events']}")
            print(f"Verified events: {result['verified_events']}")
            print(f"Integrity: {result['integrity_percentage']:.1f}%")
        else:
            print("❌ Integrity issues detected:")
            for issue in result.get('issues', []):
                print(f"  Event {issue['event_id']}: {issue['issue']}")
    
    elif args.query:
        query = AuditQuery(
            start_date=datetime.now() - timedelta(days=args.days),
            end_date=datetime.now(),
            limit=50
        )
        
        events = await audit_logger.query_audit_logs(query, args.user, "cli_query")
        
        print(f"📋 Found {len(events)} audit events (last {args.days} days)")
        for event in events[:10]:  # Show first 10
            print(f"  {event['timestamp']}: {event['event_type']} - {event['description']}")
    
    elif args.report:
        standard_map = {
            "hipaa": ComplianceStandard.HIPAA,
            "gxp": ComplianceStandard.GXP,
            "fda": ComplianceStandard.FDA_21CFR11
        }
        
        standard = standard_map[args.report]
        start_date = datetime.now() - timedelta(days=args.days)
        end_date = datetime.now()
        
        print(f"📊 Generating {standard.value.upper()} compliance report...")
        
        report = await audit_logger.generate_compliance_report(
            standard, start_date, end_date, args.user
        )
        
        print(f"\nCompliance Report: {report['report_id']}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Total Events: {report['summary']['total_events']}")
        print(f"PHI Events: {report['summary']['phi_events']}")
        print(f"Security Events: {report['summary']['security_events']}")
        print(f"Risk Level: {report['risk_assessment']['risk_level']}")
        
        print("\nRecommendations:")
        for rec in report['compliance_recommendations']:
            print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(main())