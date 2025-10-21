"""
GDPR/HIPAA Right to be Forgotten Implementation for ClinChat-RAG
Comprehensive data deletion workflows across all storage systems
"""

import json
import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib

from .cloud_storage import StorageManager, StorageConfig
from .rbac_audit import access_controller, ActionType, AccessResult

class DeletionReason(Enum):
    """Reasons for data deletion requests"""
    GDPR_REQUEST = "gdpr_request"
    HIPAA_REQUEST = "hipaa_request"
    RETENTION_EXPIRY = "retention_expiry"
    DATA_CORRECTION = "data_correction"
    LEGAL_HOLD_RELEASE = "legal_hold_release"
    PATIENT_WITHDRAWAL = "patient_withdrawal"
    SYSTEM_CLEANUP = "system_cleanup"

class DeletionStatus(Enum):
    """Status of deletion requests"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"

class DeletionScope(Enum):
    """Scope of data to be deleted"""
    COMPLETE_ERASURE = "complete_erasure"  # Everything related to subject
    SPECIFIC_DATA = "specific_data"  # Only specified datasets
    ANONYMIZATION = "anonymization"  # Convert to anonymous data
    PSEUDONYMIZATION = "pseudonymization"  # Remove direct identifiers

@dataclass
class DataSubject:
    """Data subject for deletion requests"""
    subject_id: str
    subject_type: str  # "patient", "user", "researcher", "device"
    
    # Identifiers
    primary_identifiers: List[str] = field(default_factory=list)  # MRN, user_id, etc.
    secondary_identifiers: List[str] = field(default_factory=list)  # email, phone, etc.
    
    # Context
    jurisdiction: str = "US"  # For determining applicable laws
    consent_status: Optional[str] = None

@dataclass
class DeletionRequest:
    """Formal deletion request"""
    request_id: str
    subject: DataSubject
    
    # Request details  
    reason: DeletionReason
    scope: DeletionScope
    requested_by: str  # User ID who made request
    requested_at: datetime
    
    # Legal requirements
    legal_basis: str  # GDPR Article 17, HIPAA Right of Access, etc.
    verification_required: bool = True
    retention_override: bool = False  # Override legal retention requirements
    
    # Processing
    status: DeletionStatus = DeletionStatus.PENDING
    scheduled_date: Optional[datetime] = None
    completion_deadline: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    
    # Tracking
    affected_systems: List[str] = field(default_factory=list)
    deletion_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Verification
    verification_evidence: Dict[str, str] = field(default_factory=dict)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

@dataclass
class DeletionResult:
    """Result of deletion operation"""
    system_name: str
    success: bool
    records_deleted: int
    files_deleted: int
    backups_processed: int
    
    # Details
    deletion_method: str  # "secure_delete", "anonymize", "pseudonymize"
    verification_hash: Optional[str] = None
    error_message: Optional[str] = None
    
    # Compliance
    compliance_certificate: Optional[str] = None
    deletion_timestamp: datetime = field(default_factory=datetime.now)

class DeletionDatabase:
    """Database for managing deletion requests and audit trails"""
    
    def __init__(self, db_path: str = "data/deletion_requests.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize deletion request database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Deletion requests
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS deletion_requests (
                        request_id TEXT PRIMARY KEY,
                        subject_id TEXT NOT NULL,
                        subject_type TEXT NOT NULL,
                        primary_identifiers TEXT NOT NULL,  -- JSON array
                        secondary_identifiers TEXT,         -- JSON array
                        jurisdiction TEXT DEFAULT 'US',
                        reason TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        requested_by TEXT NOT NULL,
                        requested_at TIMESTAMP NOT NULL,
                        legal_basis TEXT NOT NULL,
                        verification_required BOOLEAN DEFAULT TRUE,
                        retention_override BOOLEAN DEFAULT FALSE,
                        status TEXT DEFAULT 'pending',
                        scheduled_date TIMESTAMP,
                        completion_deadline TIMESTAMP NOT NULL,
                        affected_systems TEXT,              -- JSON array
                        approved_by TEXT,
                        approved_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Deletion operations log
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS deletion_operations (
                        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT NOT NULL,
                        system_name TEXT NOT NULL,
                        operation_type TEXT NOT NULL,       -- delete, anonymize, etc.
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        success BOOLEAN,
                        records_affected INTEGER DEFAULT 0,
                        files_affected INTEGER DEFAULT 0,
                        backups_affected INTEGER DEFAULT 0,
                        deletion_method TEXT,
                        verification_hash TEXT,
                        error_message TEXT,
                        compliance_certificate TEXT,
                        performed_by TEXT NOT NULL,
                        FOREIGN KEY (request_id) REFERENCES deletion_requests (request_id)
                    )
                """)
                
                # Data inventory for tracking what needs deletion
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_inventory (
                        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        system_name TEXT NOT NULL,
                        data_type TEXT NOT NULL,            -- "structured", "unstructured", "backup"
                        location TEXT NOT NULL,             -- table, file path, etc.
                        subject_identifier_fields TEXT,     -- JSON array of fields containing identifiers
                        retention_period_days INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(system_name, location)
                    )
                """)
                
                # Legal holds (prevent deletion)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS legal_holds (
                        hold_id TEXT PRIMARY KEY,
                        subject_id TEXT NOT NULL,
                        hold_reason TEXT NOT NULL,
                        applied_by TEXT NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        case_reference TEXT
                    )
                """)
                
                # Create indices
                conn.execute("CREATE INDEX IF NOT EXISTS idx_deletion_requests_subject ON deletion_requests(subject_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_deletion_requests_status ON deletion_requests(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_deletion_operations_request ON deletion_operations(request_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_legal_holds_subject ON legal_holds(subject_id)")
                
                self.logger.info("Deletion request database initialized")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize deletion database: {e}")
            raise

class DataInventoryManager:
    """Manages inventory of data across all systems for deletion purposes"""
    
    def __init__(self, db: DeletionDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._register_default_inventory()
    
    def _register_default_inventory(self):
        """Register default data inventory for ClinChat-RAG systems"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                inventory_items = [
                    # Vector database
                    ("vector_db", "structured", "embeddings_index", ["doc_id", "metadata.patient_id", "metadata.mrn"]),
                    ("vector_db", "structured", "document_metadata", ["patient_id", "mrn", "user_id"]),
                    
                    # Cloud storage
                    ("s3_storage", "unstructured", "phi/", ["filename", "metadata.patient_id"]),
                    ("s3_storage", "unstructured", "data/", ["filename", "metadata.user_id"]),
                    
                    # Application database
                    ("app_db", "structured", "user_sessions", ["user_id", "ip_address"]),
                    ("app_db", "structured", "query_history", ["user_id", "session_id", "query_content"]),
                    ("app_db", "structured", "feedback", ["user_id", "session_id", "query", "response"]),
                    
                    # RBAC system
                    ("rbac_db", "structured", "users", ["user_id", "username", "email"]),
                    ("rbac_db", "structured", "audit_log", ["user_id", "ip_address", "session_id"]),
                    ("rbac_db", "structured", "sessions", ["user_id", "ip_address"]),
                    
                    # Monitoring system
                    ("monitoring_db", "structured", "access_logs", ["user_id", "ip_address"]),
                    ("monitoring_db", "structured", "performance_logs", ["session_id", "user_id"]),
                    
                    # Backups
                    ("backup_s3", "backup", "daily_backups/", ["*"]),
                    ("backup_s3", "backup", "monthly_backups/", ["*"]),
                ]
                
                for system_name, data_type, location, identifier_fields in inventory_items:
                    conn.execute("""
                        INSERT OR REPLACE INTO data_inventory 
                        (system_name, data_type, location, subject_identifier_fields, retention_period_days)
                        VALUES (?, ?, ?, ?, ?)
                    """, (system_name, data_type, location, json.dumps(identifier_fields), 2555))  # 7 years default
                
                self.logger.info("Default data inventory registered")
                
        except Exception as e:
            self.logger.error(f"Failed to register data inventory: {e}")
    
    def find_data_locations(self, subject: DataSubject) -> List[Dict[str, Any]]:
        """Find all data locations for a subject"""
        locations = []
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT system_name, data_type, location, subject_identifier_fields, retention_period_days
                    FROM data_inventory
                """)
                
                all_identifiers = subject.primary_identifiers + subject.secondary_identifiers
                
                for system_name, data_type, location, fields_json, retention_days in cursor.fetchall():
                    identifier_fields = json.loads(fields_json)
                    
                    # Check if any identifier fields match subject identifiers
                    relevant = False
                    if "*" in identifier_fields:  # Backup systems
                        relevant = True
                    else:
                        for field in identifier_fields:
                            if any(identifier in field.lower() for identifier in [id.lower() for id in all_identifiers]):
                                relevant = True
                                break
                    
                    if relevant:
                        locations.append({
                            "system_name": system_name,
                            "data_type": data_type,
                            "location": location,
                            "identifier_fields": identifier_fields,
                            "retention_period_days": retention_days
                        })
                
        except Exception as e:
            self.logger.error(f"Failed to find data locations: {e}")
        
        return locations

class SystemDeletionInterface:
    """Interface for system-specific deletion operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def delete_from_vector_db(self, subject: DataSubject, scope: DeletionScope) -> DeletionResult:
        """Delete/anonymize data from vector database"""
        try:
            from improvements.scalable_vectordb import vector_db_manager
            
            # Find documents by subject identifiers
            doc_ids_to_delete = []
            
            # Search for documents containing subject identifiers
            for identifier in subject.primary_identifiers + subject.secondary_identifiers:
                # This would need to be implemented based on actual vector DB search capabilities
                # For now, simulate finding document IDs
                search_results = await vector_db_manager.search(
                    query_vector=[0.0] * 768,  # Placeholder
                    filters=None,
                    top_k=1000
                )
                
                for result in search_results:
                    if any(identifier in result.content or 
                          identifier in str(result.metadata) for identifier in subject.primary_identifiers):
                        doc_ids_to_delete.append(result.doc_id)
            
            doc_ids_to_delete = list(set(doc_ids_to_delete))  # Remove duplicates
            
            if scope == DeletionScope.COMPLETE_ERASURE:
                # Hard delete
                success = await vector_db_manager.delete(doc_ids_to_delete)
                method = "secure_delete"
            
            elif scope == DeletionScope.ANONYMIZATION:
                # Replace with anonymized versions
                # This would require re-embedding anonymized content
                success = True  # Placeholder
                method = "anonymize"
            
            else:
                success = True
                method = "pseudonymize"
            
            return DeletionResult(
                system_name="vector_db",
                success=success,
                records_deleted=len(doc_ids_to_delete),
                files_deleted=0,
                backups_processed=0,
                deletion_method=method,
                verification_hash=self._generate_verification_hash(doc_ids_to_delete)
            )
            
        except Exception as e:
            self.logger.error(f"Vector DB deletion failed: {e}")
            return DeletionResult(
                system_name="vector_db",
                success=False,
                records_deleted=0,
                files_deleted=0,
                backups_processed=0,
                deletion_method="failed",
                error_message=str(e)
            )
    
    async def delete_from_cloud_storage(self, subject: DataSubject, scope: DeletionScope,
                                       storage_manager: StorageManager) -> DeletionResult:
        """Delete/anonymize data from cloud storage"""
        try:
            files_deleted = 0
            
            # Find files containing subject identifiers
            all_objects = storage_manager.storage.list_objects()
            
            for obj in all_objects:
                should_delete = False
                
                # Check metadata and content for identifiers
                for identifier in subject.primary_identifiers + subject.secondary_identifiers:
                    if (identifier in obj.get('key', '') or 
                        identifier in str(obj.get('metadata', {})) or
                        (obj.get('phi_detected') and subject.subject_type == 'patient')):
                        should_delete = True
                        break
                
                if should_delete:
                    if scope == DeletionScope.COMPLETE_ERASURE:
                        success = storage_manager.secure_delete_medical_data(obj['key'], f"deletion_system_{subject.subject_id}")
                        if success:
                            files_deleted += 1
                    
                    elif scope == DeletionScope.ANONYMIZATION:
                        # Download, anonymize, re-upload
                        data, metadata = storage_manager.retrieve_medical_data(obj['key'], f"deletion_system_{subject.subject_id}")
                        anonymized_data = self._anonymize_content(data.decode('utf-8'), subject)
                        
                        storage_manager.store_medical_data(
                            anonymized_data,
                            f"anonymized_{obj['key']}",
                            f"deletion_system_{subject.subject_id}",
                            "anonymized"
                        )
                        
                        # Delete original
                        storage_manager.secure_delete_medical_data(obj['key'], f"deletion_system_{subject.subject_id}")
                        files_deleted += 1
            
            return DeletionResult(
                system_name="cloud_storage",
                success=True,
                records_deleted=0,
                files_deleted=files_deleted,
                backups_processed=0,
                deletion_method=scope.value,
                verification_hash=self._generate_verification_hash([subject.subject_id])
            )
            
        except Exception as e:
            self.logger.error(f"Cloud storage deletion failed: {e}")
            return DeletionResult(
                system_name="cloud_storage",
                success=False,
                records_deleted=0,
                files_deleted=0,
                backups_processed=0,
                deletion_method="failed",
                error_message=str(e)
            )
    
    async def delete_from_rbac_system(self, subject: DataSubject, scope: DeletionScope) -> DeletionResult:
        """Delete data from RBAC and audit systems"""
        try:
            from .rbac_audit import rbac_db
            
            records_deleted = 0
            
            with sqlite3.connect(rbac_db.db_path) as conn:
                cursor = conn.cursor()
                
                # Find relevant records
                for identifier in subject.primary_identifiers + subject.secondary_identifiers:
                    if scope == DeletionScope.COMPLETE_ERASURE:
                        # Delete audit logs (careful - may need retention for legal reasons)
                        cursor.execute("DELETE FROM audit_log WHERE user_id = ?", (identifier,))
                        records_deleted += cursor.rowcount
                        
                        # Delete sessions
                        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (identifier,))
                        records_deleted += cursor.rowcount
                        
                        # For users, mark as deleted rather than hard delete
                        cursor.execute("""
                            UPDATE users SET 
                                email = 'deleted@deleted.com',
                                full_name = 'DELETED USER',
                                is_active = FALSE
                            WHERE user_id = ?
                        """, (identifier,))
                        records_deleted += cursor.rowcount
                    
                    elif scope == DeletionScope.ANONYMIZATION:
                        # Anonymize audit logs
                        cursor.execute("""
                            UPDATE audit_log SET 
                                user_id = 'ANONYMOUS_USER',
                                ip_address = '0.0.0.0',
                                user_agent = 'ANONYMIZED'
                            WHERE user_id = ?
                        """, (identifier,))
                        records_deleted += cursor.rowcount
                
                conn.commit()
            
            return DeletionResult(
                system_name="rbac_system",
                success=True,
                records_deleted=records_deleted,
                files_deleted=0,
                backups_processed=0,
                deletion_method=scope.value
            )
            
        except Exception as e:
            self.logger.error(f"RBAC system deletion failed: {e}")
            return DeletionResult(
                system_name="rbac_system",
                success=False,
                records_deleted=0,
                files_deleted=0,
                backups_processed=0,
                deletion_method="failed",
                error_message=str(e)
            )
    
    def _anonymize_content(self, content: str, subject: DataSubject) -> str:
        """Anonymize content by removing/replacing identifiers"""
        anonymized = content
        
        for identifier in subject.primary_identifiers + subject.secondary_identifiers:
            # Simple replacement - in production, use sophisticated anonymization
            anonymized = anonymized.replace(identifier, "[REDACTED]")
        
        return anonymized
    
    def _generate_verification_hash(self, data: List[str]) -> str:
        """Generate verification hash for deletion proof"""
        content = json.dumps(sorted(data)) + str(datetime.now().isoformat())
        return hashlib.sha256(content.encode()).hexdigest()

class RightToBeForgottenManager:
    """Main manager for GDPR/HIPAA deletion workflows"""
    
    def __init__(self):
        self.db = DeletionDatabase()
        self.inventory = DataInventoryManager(self.db)
        self.deletion_interface = SystemDeletionInterface()
        self.logger = logging.getLogger(__name__)
    
    async def submit_deletion_request(self, subject: DataSubject, reason: DeletionReason,
                                    scope: DeletionScope, requested_by: str,
                                    legal_basis: str) -> str:
        """Submit a new deletion request"""
        try:
            import uuid
            request_id = str(uuid.uuid4())
            
            # Check for legal holds
            if await self._check_legal_holds(subject):
                raise ValueError("Subject has active legal holds - deletion not permitted")
            
            # Find affected systems
            affected_locations = self.inventory.find_data_locations(subject)
            affected_systems = list(set([loc["system_name"] for loc in affected_locations]))
            
            # Create deletion request
            request = DeletionRequest(
                request_id=request_id,
                subject=subject,
                reason=reason,
                scope=scope,
                requested_by=requested_by,
                requested_at=datetime.now(),
                legal_basis=legal_basis,
                affected_systems=affected_systems
            )
            
            # Store in database
            await self._store_deletion_request(request)
            
            # Log audit event
            access_controller._log_audit_entry(
                user_id=requested_by,
                action_type=ActionType.DATA_ACCESS,  # Need new type for deletion
                access_result=AccessResult.GRANTED,
                resource_type="deletion_request",
                resource_id=request_id
            )
            
            self.logger.info(f"Deletion request {request_id} submitted for subject {subject.subject_id}")
            return request_id
            
        except Exception as e:
            self.logger.error(f"Failed to submit deletion request: {e}")
            raise
    
    async def process_deletion_request(self, request_id: str, approved_by: str) -> Dict[str, Any]:
        """Process an approved deletion request"""
        try:
            # Get request
            request = await self._get_deletion_request(request_id)
            if not request:
                raise ValueError("Deletion request not found")
            
            if request.status != DeletionStatus.PENDING:
                raise ValueError(f"Request is not pending (status: {request.status})")
            
            # Update status
            await self._update_request_status(request_id, DeletionStatus.IN_PROGRESS)
            
            results = []
            overall_success = True
            
            # Process each affected system
            for system_name in request.affected_systems:
                try:
                    if system_name == "vector_db":
                        result = await self.deletion_interface.delete_from_vector_db(
                            request.subject, request.scope
                        )
                    
                    elif system_name == "cloud_storage":
                        # Would need to pass actual storage manager
                        result = await self.deletion_interface.delete_from_cloud_storage(
                            request.subject, request.scope, None  # Placeholder
                        )
                    
                    elif system_name == "rbac_system":
                        result = await self.deletion_interface.delete_from_rbac_system(
                            request.subject, request.scope
                        )
                    
                    else:
                        # Unknown system
                        result = DeletionResult(
                            system_name=system_name,
                            success=False,
                            records_deleted=0,
                            files_deleted=0,
                            backups_processed=0,
                            deletion_method="unknown_system",
                            error_message=f"No deletion handler for system: {system_name}"
                        )
                    
                    results.append(result)
                    
                    if not result.success:
                        overall_success = False
                    
                    # Log operation
                    await self._log_deletion_operation(request_id, result, approved_by)
                    
                except Exception as e:
                    self.logger.error(f"Deletion failed for system {system_name}: {e}")
                    overall_success = False
                    
                    error_result = DeletionResult(
                        system_name=system_name,
                        success=False,
                        records_deleted=0,
                        files_deleted=0,
                        backups_processed=0,
                        deletion_method="error",
                        error_message=str(e)
                    )
                    results.append(error_result)
                    await self._log_deletion_operation(request_id, error_result, approved_by)
            
            # Update final status
            final_status = DeletionStatus.COMPLETED if overall_success else DeletionStatus.PARTIAL
            await self._update_request_status(request_id, final_status)
            
            # Generate compliance certificate
            certificate = await self._generate_compliance_certificate(request_id, results)
            
            return {
                "request_id": request_id,
                "status": final_status.value,
                "results": [result.__dict__ for result in results],
                "compliance_certificate": certificate,
                "total_records_deleted": sum(r.records_deleted for r in results),
                "total_files_deleted": sum(r.files_deleted for r in results)
            }
            
        except Exception as e:
            await self._update_request_status(request_id, DeletionStatus.FAILED)
            self.logger.error(f"Deletion processing failed: {e}")
            raise
    
    async def _check_legal_holds(self, subject: DataSubject) -> bool:
        """Check if subject has active legal holds"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM legal_holds 
                    WHERE subject_id = ? AND is_active = TRUE 
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (subject.subject_id,))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Legal hold check failed: {e}")
            return True  # Err on the side of caution
    
    async def _store_deletion_request(self, request: DeletionRequest):
        """Store deletion request in database"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT INTO deletion_requests (
                        request_id, subject_id, subject_type, primary_identifiers,
                        secondary_identifiers, jurisdiction, reason, scope, requested_by,
                        requested_at, legal_basis, verification_required, retention_override,
                        status, completion_deadline, affected_systems
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.request_id, request.subject.subject_id, request.subject.subject_type,
                    json.dumps(request.subject.primary_identifiers),
                    json.dumps(request.subject.secondary_identifiers),
                    request.subject.jurisdiction, request.reason.value, request.scope.value,
                    request.requested_by, request.requested_at, request.legal_basis,
                    request.verification_required, request.retention_override,
                    request.status.value, request.completion_deadline,
                    json.dumps(request.affected_systems)
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to store deletion request: {e}")
            raise
    
    async def _get_deletion_request(self, request_id: str) -> Optional[DeletionRequest]:
        """Retrieve deletion request from database"""
        # Implementation would reconstruct DeletionRequest from database
        # This is a simplified placeholder
        return None
    
    async def _update_request_status(self, request_id: str, status: DeletionStatus):
        """Update deletion request status"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    UPDATE deletion_requests SET status = ? WHERE request_id = ?
                """, (status.value, request_id))
                
        except Exception as e:
            self.logger.error(f"Failed to update request status: {e}")
    
    async def _log_deletion_operation(self, request_id: str, result: DeletionResult, performed_by: str):
        """Log deletion operation result"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT INTO deletion_operations (
                        request_id, system_name, operation_type, completed_at, success,
                        records_affected, files_affected, backups_affected, deletion_method,
                        verification_hash, error_message, performed_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_id, result.system_name, "deletion", result.deletion_timestamp,
                    result.success, result.records_deleted, result.files_deleted,
                    result.backups_processed, result.deletion_method,
                    result.verification_hash, result.error_message, performed_by
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to log deletion operation: {e}")
    
    async def _generate_compliance_certificate(self, request_id: str, results: List[DeletionResult]) -> str:
        """Generate compliance certificate for deletion"""
        certificate = {
            "request_id": request_id,
            "completion_date": datetime.now().isoformat(),
            "systems_processed": len(results),
            "total_records_deleted": sum(r.records_deleted for r in results),
            "total_files_deleted": sum(r.files_deleted for r in results),
            "verification_hashes": [r.verification_hash for r in results if r.verification_hash],
            "compliance_standard": "GDPR Article 17 / HIPAA Privacy Rule"
        }
        
        # In production, this would be cryptographically signed
        certificate_json = json.dumps(certificate, sort_keys=True)
        certificate_hash = hashlib.sha256(certificate_json.encode()).hexdigest()
        
        return f"CERT-{certificate_hash[:16]}"

# Global manager instance
deletion_manager = RightToBeForgottenManager()

# Export main components
__all__ = [
    'RightToBeForgottenManager',
    'DeletionDatabase',
    'DataInventoryManager',
    'SystemDeletionInterface',
    'DeletionRequest',
    'DataSubject',
    'DeletionReason',
    'DeletionStatus',
    'DeletionScope',
    'DeletionResult',
    'deletion_manager'
]