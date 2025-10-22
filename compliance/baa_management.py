#!/usr/bin/env python3
"""
Business Associate Agreement (BAA) Management System
Automated compliance tracking and renewal management for AI provider BAAs
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os

logger = logging.getLogger(__name__)

class BAAStatus(Enum):
    """BAA status enumeration"""
    PENDING = "pending"
    EXECUTED = "executed"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    UNDER_REVIEW = "under_review"

class ComplianceLevel(Enum):
    """Compliance level enumeration"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    REQUIRES_UPDATE = "requires_update"

@dataclass
class BAAProvider:
    """Business Associate information"""
    provider_id: str
    provider_name: str
    contact_email: str
    contact_person: str
    legal_entity_name: str
    address: str
    phone: str
    website: str
    services_provided: List[str]
    data_types_processed: List[str]

@dataclass
class BAAAgreement:
    """Business Associate Agreement details"""
    baa_id: str
    provider_id: str
    status: BAAStatus
    execution_date: Optional[datetime]
    expiration_date: Optional[datetime]
    renewal_date: Optional[datetime]
    document_path: str
    version: str
    compliance_level: ComplianceLevel
    last_review_date: Optional[datetime]
    next_review_date: Optional[datetime]
    terms_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    notes: str

@dataclass
class ComplianceAlert:
    """Compliance alert for BAA management"""
    alert_id: str
    baa_id: str
    provider_name: str
    alert_type: str
    severity: str
    message: str
    due_date: datetime
    created_at: datetime
    resolved: bool
    resolution_notes: str

class BAAManager:
    """Business Associate Agreement Management System"""
    
    def __init__(self, db_path: str = "compliance/baa_management.db"):
        """Initialize BAA management system"""
        self.db_path = db_path
        self._initialize_database()
        self._initialize_providers()
        
    def _initialize_database(self):
        """Initialize BAA management database"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Providers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baa_providers (
                provider_id TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                contact_person TEXT NOT NULL,
                legal_entity_name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                website TEXT,
                services_provided TEXT,  -- JSON array
                data_types_processed TEXT,  -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # BAA Agreements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baa_agreements (
                baa_id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_date TEXT,
                expiration_date TEXT,
                renewal_date TEXT,
                document_path TEXT,
                version TEXT,
                compliance_level TEXT,
                last_review_date TEXT,
                next_review_date TEXT,
                terms_summary TEXT,  -- JSON
                risk_assessment TEXT,  -- JSON
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES baa_providers (provider_id)
            )
        ''')
        
        # Compliance Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_alerts (
                alert_id TEXT PRIMARY KEY,
                baa_id TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                due_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT,
                FOREIGN KEY (baa_id) REFERENCES baa_agreements (baa_id)
            )
        ''')
        
        # Compliance History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                baa_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                performed_by TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (baa_id) REFERENCES baa_agreements (baa_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _initialize_providers(self):
        """Initialize default AI providers"""
        default_providers = [
            BAAProvider(
                provider_id="google_gemini",
                provider_name="Google Gemini",
                contact_email="cloud-sales@google.com",
                contact_person="Google Cloud Sales Team",
                legal_entity_name="Google LLC",
                address="1600 Amphitheatre Parkway, Mountain View, CA 94043",
                phone="+1-650-253-0000",
                website="https://cloud.google.com/",
                services_provided=["AI/ML Services", "Natural Language Processing", "Generative AI"],
                data_types_processed=["Clinical Text", "Medical Documents", "Patient Communications"]
            ),
            BAAProvider(
                provider_id="groq",
                provider_name="Groq",
                contact_email="legal@groq.com",
                contact_person="Groq Legal Team",
                legal_entity_name="Groq, Inc.",
                address="1900 University Avenue, East Palo Alto, CA 94303",
                phone="+1-650-000-0000",
                website="https://groq.com/",
                services_provided=["AI Inference", "Language Processing", "High-Speed AI Compute"],
                data_types_processed=["Clinical Text", "Medical Queries", "Diagnostic Information"]
            )
        ]
        
        for provider in default_providers:
            self.add_provider(provider)
    
    def add_provider(self, provider: BAAProvider) -> bool:
        """Add or update BAA provider"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO baa_providers (
                    provider_id, provider_name, contact_email, contact_person,
                    legal_entity_name, address, phone, website,
                    services_provided, data_types_processed, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                provider.provider_id,
                provider.provider_name,
                provider.contact_email,
                provider.contact_person,
                provider.legal_entity_name,
                provider.address,
                provider.phone,
                provider.website,
                json.dumps(provider.services_provided),
                json.dumps(provider.data_types_processed),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Added/updated provider: {provider.provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding provider {provider.provider_name}: {e}")
            return False
    
    def create_baa_agreement(self, provider_id: str, terms_summary: Dict[str, Any]) -> str:
        """Create new BAA agreement"""
        baa_id = f"BAA_{provider_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        agreement = BAAAgreement(
            baa_id=baa_id,
            provider_id=provider_id,
            status=BAAStatus.PENDING,
            execution_date=None,
            expiration_date=None,
            renewal_date=None,
            document_path="",
            version="1.0",
            compliance_level=ComplianceLevel.PENDING_REVIEW,
            last_review_date=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=90),
            terms_summary=terms_summary,
            risk_assessment={},
            notes="Initial BAA creation"
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO baa_agreements (
                    baa_id, provider_id, status, execution_date, expiration_date,
                    renewal_date, document_path, version, compliance_level,
                    last_review_date, next_review_date, terms_summary,
                    risk_assessment, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agreement.baa_id,
                agreement.provider_id,
                agreement.status.value,
                agreement.execution_date.isoformat() if agreement.execution_date else None,
                agreement.expiration_date.isoformat() if agreement.expiration_date else None,
                agreement.renewal_date.isoformat() if agreement.renewal_date else None,
                agreement.document_path,
                agreement.version,
                agreement.compliance_level.value,
                agreement.last_review_date.isoformat(),
                agreement.next_review_date.isoformat(),
                json.dumps(agreement.terms_summary),
                json.dumps(agreement.risk_assessment),
                agreement.notes
            ))
            
            conn.commit()
            conn.close()
            
            # Log the action
            self._log_compliance_action(baa_id, "created", f"BAA agreement created for {provider_id}")
            
            logger.info(f"Created BAA agreement: {baa_id}")
            return baa_id
            
        except Exception as e:
            logger.error(f"Error creating BAA agreement for {provider_id}: {e}")
            return ""
    
    def execute_baa(self, baa_id: str, execution_date: datetime, expiration_date: datetime, 
                   document_path: str) -> bool:
        """Mark BAA as executed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE baa_agreements SET
                    status = ?,
                    execution_date = ?,
                    expiration_date = ?,
                    renewal_date = ?,
                    document_path = ?,
                    compliance_level = ?,
                    updated_at = ?
                WHERE baa_id = ?
            ''', (
                BAAStatus.EXECUTED.value,
                execution_date.isoformat(),
                expiration_date.isoformat(),
                (expiration_date - timedelta(days=90)).isoformat(),  # Renewal 90 days before expiry
                document_path,
                ComplianceLevel.COMPLIANT.value,
                datetime.now().isoformat(),
                baa_id
            ))
            
            conn.commit()
            conn.close()
            
            # Log the action
            self._log_compliance_action(baa_id, "executed", f"BAA executed with expiration {expiration_date}")
            
            # Create renewal reminder alert
            self._create_renewal_alert(baa_id, expiration_date)
            
            logger.info(f"Executed BAA: {baa_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing BAA {baa_id}: {e}")
            return False
    
    def get_baa_status(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get current BAA status for provider"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ba.*, bp.provider_name 
                FROM baa_agreements ba
                JOIN baa_providers bp ON ba.provider_id = bp.provider_id
                WHERE ba.provider_id = ?
                ORDER BY ba.created_at DESC
                LIMIT 1
            ''', (provider_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting BAA status for {provider_id}: {e}")
            return None
    
    def get_all_baa_status(self) -> List[Dict[str, Any]]:
        """Get status of all BAA agreements"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ba.*, bp.provider_name, bp.contact_email
                FROM baa_agreements ba
                JOIN baa_providers bp ON ba.provider_id = bp.provider_id
                ORDER BY ba.provider_id, ba.created_at DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting all BAA status: {e}")
            return []
    
    def check_compliance_status(self) -> Dict[str, Any]:
        """Check overall BAA compliance status"""
        all_baas = self.get_all_baa_status()
        
        total_providers = len(set(baa['provider_id'] for baa in all_baas))
        executed_baas = len([baa for baa in all_baas if baa['status'] == BAAStatus.EXECUTED.value])
        expired_baas = len([baa for baa in all_baas if baa['status'] == BAAStatus.EXPIRED.value])
        pending_baas = len([baa for baa in all_baas if baa['status'] == BAAStatus.PENDING.value])
        
        # Check for expiring BAAs (within 90 days)
        expiring_soon = []
        for baa in all_baas:
            if baa['expiration_date']:
                exp_date = datetime.fromisoformat(baa['expiration_date'])
                if exp_date <= datetime.now() + timedelta(days=90):
                    expiring_soon.append(baa)
        
        compliance_percentage = (executed_baas / total_providers * 100) if total_providers > 0 else 0
        
        return {
            "total_providers": total_providers,
            "executed_baas": executed_baas,
            "expired_baas": expired_baas,
            "pending_baas": pending_baas,
            "expiring_soon": len(expiring_soon),
            "compliance_percentage": compliance_percentage,
            "compliance_status": "COMPLIANT" if compliance_percentage >= 100 else 
                               "PARTIALLY_COMPLIANT" if compliance_percentage >= 50 else "NON_COMPLIANT",
            "expiring_agreements": expiring_soon
        }
    
    def _create_renewal_alert(self, baa_id: str, expiration_date: datetime):
        """Create renewal reminder alert"""
        renewal_date = expiration_date - timedelta(days=90)
        
        # Get provider information
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bp.provider_name
            FROM baa_agreements ba
            JOIN baa_providers bp ON ba.provider_id = bp.provider_id
            WHERE ba.baa_id = ?
        ''', (baa_id,))
        
        result = cursor.fetchone()
        provider_name = result[0] if result else "Unknown"
        conn.close()
        
        alert = ComplianceAlert(
            alert_id=f"RENEWAL_{baa_id}_{datetime.now().strftime('%Y%m%d')}",
            baa_id=baa_id,
            provider_name=provider_name,
            alert_type="renewal_reminder",
            severity="high",
            message=f"BAA for {provider_name} requires renewal within 90 days",
            due_date=renewal_date,
            created_at=datetime.now(),
            resolved=False,
            resolution_notes=""
        )
        
        self._save_alert(alert)
    
    def _save_alert(self, alert: ComplianceAlert):
        """Save compliance alert to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO compliance_alerts (
                    alert_id, baa_id, provider_name, alert_type, severity,
                    message, due_date, created_at, resolved, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.baa_id,
                alert.provider_name,
                alert.alert_type,
                alert.severity,
                alert.message,
                alert.due_date.isoformat(),
                alert.created_at.isoformat(),
                alert.resolved,
                alert.resolution_notes
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving alert {alert.alert_id}: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active compliance alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM compliance_alerts
                WHERE resolved = FALSE
                ORDER BY severity DESC, due_date ASC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Mark alert as resolved"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE compliance_alerts
                SET resolved = TRUE, resolution_notes = ?
                WHERE alert_id = ?
            ''', (resolution_notes, alert_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Resolved alert: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    def _log_compliance_action(self, baa_id: str, action_type: str, details: str, 
                              performed_by: str = "system"):
        """Log compliance action for audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO compliance_history (
                    baa_id, action_type, action_details, performed_by
                ) VALUES (?, ?, ?, ?)
            ''', (baa_id, action_type, details, performed_by))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging compliance action: {e}")
    
    async def send_compliance_notifications(self) -> Dict[str, Any]:
        """Send email notifications for compliance alerts"""
        alerts = self.get_active_alerts()
        notifications_sent = 0
        
        smtp_config = {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "use_tls": os.getenv("SMTP_TLS", "true").lower() == "true"
        }
        
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        
        if not smtp_config["username"] or not smtp_config["password"]:
            logger.warning("SMTP configuration incomplete, notifications not sent")
            return {"notifications_sent": 0, "error": "SMTP configuration incomplete"}
        
        try:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])
            if smtp_config["use_tls"]:
                server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            
            for alert in alerts:
                subject = f"BAA Compliance Alert: {alert['alert_type'].replace('_', ' ').title()}"
                
                body = f"""
BAA Compliance Alert

Provider: {alert['provider_name']}
Alert Type: {alert['alert_type'].replace('_', ' ').title()}
Severity: {alert['severity'].upper()}
Message: {alert['message']}
Due Date: {alert['due_date']}

Please review and take appropriate action.

ClinChat-RAG Compliance System
                """
                
                msg = MimeMultipart()
                msg['From'] = smtp_config["username"]
                msg['To'] = admin_email
                msg['Subject'] = subject
                msg.attach(MimeText(body, 'plain'))
                
                server.send_message(msg)
                notifications_sent += 1
            
            server.quit()
            
            return {
                "notifications_sent": notifications_sent,
                "total_alerts": len(alerts),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error sending compliance notifications: {e}")
            return {
                "notifications_sent": 0,
                "error": str(e),
                "success": False
            }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive BAA compliance report"""
        compliance_status = self.check_compliance_status()
        all_baas = self.get_all_baa_status()
        active_alerts = self.get_active_alerts()
        
        # Provider-specific status
        provider_status = {}
        for baa in all_baas:
            provider_id = baa['provider_id']
            if provider_id not in provider_status:
                provider_status[provider_id] = {
                    "provider_name": baa['provider_name'],
                    "status": baa['status'],
                    "compliance_level": baa['compliance_level'],
                    "execution_date": baa['execution_date'],
                    "expiration_date": baa['expiration_date'],
                    "next_review_date": baa['next_review_date']
                }
        
        # Recommendations
        recommendations = []
        
        if compliance_status["pending_baas"] > 0:
            recommendations.append(
                f"Execute {compliance_status['pending_baas']} pending BAA agreements immediately"
            )
        
        if compliance_status["expiring_soon"] > 0:
            recommendations.append(
                f"Renew {compliance_status['expiring_soon']} BAA agreements expiring within 90 days"
            )
        
        if compliance_status["compliance_percentage"] < 100:
            recommendations.append(
                "Achieve 100% BAA compliance before processing any PHI data"
            )
        
        return {
            "report_date": datetime.now().isoformat(),
            "overall_compliance": compliance_status,
            "provider_status": provider_status,
            "active_alerts": active_alerts,
            "recommendations": recommendations,
            "next_actions": [
                "Review and execute pending BAA agreements",
                "Schedule renewal meetings for expiring agreements",
                "Implement automated compliance monitoring",
                "Establish regular compliance review schedule"
            ]
        }

# CLI Interface
async def main():
    """Main CLI interface for BAA management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClinChat-RAG BAA Management System")
    parser.add_argument("--status", action="store_true", help="Show BAA compliance status")
    parser.add_argument("--create", type=str, help="Create BAA for provider ID")
    parser.add_argument("--execute", nargs=2, metavar=('BAA_ID', 'DOCUMENT_PATH'), 
                       help="Execute BAA agreement")
    parser.add_argument("--alerts", action="store_true", help="Show active compliance alerts")
    parser.add_argument("--report", action="store_true", help="Generate compliance report")
    parser.add_argument("--notify", action="store_true", help="Send compliance notifications")
    
    args = parser.parse_args()
    
    baa_manager = BAAManager()
    
    if args.status:
        status = baa_manager.check_compliance_status()
        print("\n🏥 BAA COMPLIANCE STATUS")
        print("=" * 40)
        print(f"Overall Status: {status['compliance_status']}")
        print(f"Compliance Percentage: {status['compliance_percentage']:.1f}%")
        print(f"Total Providers: {status['total_providers']}")
        print(f"Executed BAAs: {status['executed_baas']}")
        print(f"Pending BAAs: {status['pending_baas']}")
        print(f"Expiring Soon: {status['expiring_soon']}")
        
    elif args.create:
        default_terms = {
            "data_processing_scope": "Clinical document analysis and AI inference",
            "retention_period": "As needed for service provision",
            "security_requirements": "HIPAA-compliant encryption and access controls",
            "breach_notification": "Within 24 hours of discovery",
            "termination_clause": "30 days written notice"
        }
        
        baa_id = baa_manager.create_baa_agreement(args.create, default_terms)
        if baa_id:
            print(f"✅ Created BAA agreement: {baa_id}")
        else:
            print(f"❌ Failed to create BAA for provider: {args.create}")
    
    elif args.execute:
        baa_id, doc_path = args.execute
        execution_date = datetime.now()
        expiration_date = execution_date + timedelta(days=365)  # 1 year
        
        success = baa_manager.execute_baa(baa_id, execution_date, expiration_date, doc_path)
        if success:
            print(f"✅ Executed BAA: {baa_id}")
        else:
            print(f"❌ Failed to execute BAA: {baa_id}")
    
    elif args.alerts:
        alerts = baa_manager.get_active_alerts()
        print(f"\n🚨 ACTIVE COMPLIANCE ALERTS ({len(alerts)})")
        print("=" * 50)
        
        for alert in alerts:
            print(f"Provider: {alert['provider_name']}")
            print(f"Type: {alert['alert_type']}")
            print(f"Severity: {alert['severity'].upper()}")
            print(f"Message: {alert['message']}")
            print(f"Due: {alert['due_date']}")
            print("-" * 30)
    
    elif args.report:
        report = baa_manager.generate_compliance_report()
        print(json.dumps(report, indent=2, default=str))
    
    elif args.notify:
        result = await baa_manager.send_compliance_notifications()
        if result["success"]:
            print(f"✅ Sent {result['notifications_sent']} notifications")
        else:
            print(f"❌ Failed to send notifications: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())