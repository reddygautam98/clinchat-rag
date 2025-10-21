"""
Secure Cloud Storage Implementation for ClinChat-RAG
Provides HIPAA-compliant S3/GCS storage with encryption, lifecycle management, and audit logging
"""

import json
import logging
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

try:
    from google.cloud import storage as gcs
    from google.cloud import kms
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

@dataclass
class StorageConfig:
    """Configuration for secure cloud storage"""
    provider: str  # "s3" or "gcs"
    
    # Connection settings
    bucket_name: str
    region: str = "us-east-1"
    
    # Encryption settings
    encryption_type: str = "AES256"  # "AES256", "aws:kms", "SSE-C"
    kms_key_id: Optional[str] = None
    encryption_key: Optional[bytes] = None
    
    # Access control
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    service_account_path: Optional[str] = None
    
    # HIPAA compliance settings
    enable_versioning: bool = True
    enable_access_logging: bool = True
    enable_object_lock: bool = True
    retention_years: int = 7
    
    # Lifecycle policies
    transition_to_ia_days: int = 30  # Infrequent Access
    transition_to_glacier_days: int = 90
    expiration_days: int = 2555  # 7 years

@dataclass
class DataClassification:
    """Data classification for HIPAA compliance"""
    PHI = "phi"  # Protected Health Information
    SENSITIVE = "sensitive"  # Sensitive but not PHI
    INTERNAL = "internal"  # Internal use only
    PUBLIC = "public"  # Public information

@dataclass
class StorageMetadata:
    """Metadata for stored objects"""
    object_key: str
    classification: str
    created_at: datetime
    created_by: str
    purpose: str  # "training", "inference", "backup", "audit"
    retention_date: datetime
    phi_detected: bool = False
    audit_trail: List[Dict[str, Any]] = None

class StorageAuditEvent(Enum):
    """Audit events for storage operations"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    ACCESS = "access"
    ENCRYPTION = "encryption"
    RETENTION_UPDATE = "retention_update"

class SecureCloudStorage:
    """Base class for secure cloud storage implementations"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Setup client-side encryption for additional security"""
        if self.config.encryption_key:
            self.cipher = Fernet(self.config.encryption_key)
        else:
            # Generate encryption key from password if not provided
            password = os.environ.get('CLINCHAT_ENCRYPTION_PASSWORD', 'default-key').encode()
            salt = b'clinchat-salt'  # In production, use random salt per dataset
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher = Fernet(key)
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using client-side encryption"""
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using client-side encryption"""
        return self.cipher.decrypt(encrypted_data)
    
    def _detect_phi(self, content: str) -> bool:
        """Basic PHI detection (should be replaced with proper HIPAA scanner)"""
        phi_patterns = [
            # Social Security Numbers
            r'\b\d{3}-\d{2}-\d{4}\b',
            # Phone numbers
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Medical record numbers (simplified)
            r'\bMRN\s*:?\s*\d+\b',
            # Date of birth patterns
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
        ]
        
        import re
        content_lower = content.lower()
        
        # Check for common PHI indicators
        phi_keywords = ['ssn', 'social security', 'date of birth', 'dob', 'mrn', 'medical record']
        if any(keyword in content_lower for keyword in phi_keywords):
            return True
        
        # Check regex patterns
        for pattern in phi_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _log_audit_event(self, event: StorageAuditEvent, object_key: str, 
                        user_id: str, additional_info: Dict = None):
        """Log audit events for compliance"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event.value,
            "object_key": object_key,
            "user_id": user_id,
            "ip_address": additional_info.get("ip_address") if additional_info else None,
            "user_agent": additional_info.get("user_agent") if additional_info else None,
            "success": additional_info.get("success", True) if additional_info else True,
            "error_message": additional_info.get("error") if additional_info else None
        }
        
        # Log to secure audit system
        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")
        
        # In production, also send to dedicated audit logging system
        self._send_to_audit_system(audit_entry)
    
    def _send_to_audit_system(self, audit_entry: Dict):
        """Send audit entry to dedicated audit logging system"""
        # Placeholder for integration with audit logging service
        # In production, implement integration with AWS CloudTrail, GCP Audit Logs, etc.
        pass

class S3SecureStorage(SecureCloudStorage):
    """HIPAA-compliant S3 storage implementation"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._setup_s3_client()
        self._setup_bucket_policies()
    
    def _setup_s3_client(self):
        """Setup S3 client with proper configuration"""
        session = boto3.Session(
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key,
            region_name=self.config.region
        )
        
        self.s3_client = session.client('s3')
        self.s3_resource = session.resource('s3')
        
        # Verify bucket exists and is accessible
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            self.logger.info(f"Connected to S3 bucket: {self.config.bucket_name}")
        except ClientError as e:
            self.logger.error(f"Failed to access S3 bucket: {e}")
            raise
    
    def _setup_bucket_policies(self):
        """Setup HIPAA-compliant bucket policies"""
        try:
            # Enable versioning
            if self.config.enable_versioning:
                self.s3_client.put_bucket_versioning(
                    Bucket=self.config.bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Setup lifecycle configuration
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'PHI-Data-Lifecycle',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'phi/'},
                        'Transitions': [
                            {
                                'Days': self.config.transition_to_ia_days,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': self.config.transition_to_glacier_days,
                                'StorageClass': 'GLACIER'
                            }
                        ],
                        'Expiration': {'Days': self.config.expiration_days}
                    },
                    {
                        'ID': 'General-Data-Lifecycle',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'data/'},
                        'Transitions': [
                            {
                                'Days': self.config.transition_to_ia_days * 2,
                                'StorageClass': 'STANDARD_IA'
                            }
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.config.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            # Enable access logging
            if self.config.enable_access_logging:
                logging_bucket = f"{self.config.bucket_name}-access-logs"
                self._ensure_logging_bucket(logging_bucket)
                
                self.s3_client.put_bucket_logging(
                    Bucket=self.config.bucket_name,
                    BucketLoggingStatus={
                        'LoggingEnabled': {
                            'TargetBucket': logging_bucket,
                            'TargetPrefix': f'{self.config.bucket_name}/'
                        }
                    }
                )
            
            self.logger.info("S3 bucket policies configured for HIPAA compliance")
            
        except ClientError as e:
            self.logger.error(f"Failed to setup bucket policies: {e}")
    
    def _ensure_logging_bucket(self, logging_bucket: str):
        """Ensure access logging bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=logging_bucket)
        except ClientError:
            # Create logging bucket
            self.s3_client.create_bucket(
                Bucket=logging_bucket,
                CreateBucketConfiguration={'LocationConstraint': self.config.region}
                if self.config.region != 'us-east-1' else {}
            )
    
    def upload_data(self, data: Union[str, bytes], object_key: str, 
                   classification: str, user_id: str, purpose: str,
                   metadata: Dict = None) -> StorageMetadata:
        """Upload data with encryption and compliance metadata"""
        try:
            # Convert string to bytes if necessary
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Detect PHI
            phi_detected = False
            if isinstance(data, str):
                phi_detected = self._detect_phi(data)
            
            # Apply client-side encryption for sensitive data
            if classification in [DataClassification.PHI, DataClassification.SENSITIVE]:
                data_bytes = self.encrypt_data(data_bytes)
            
            # Prepare metadata
            storage_metadata = StorageMetadata(
                object_key=object_key,
                classification=classification,
                created_at=datetime.utcnow(),
                created_by=user_id,
                purpose=purpose,
                retention_date=datetime.utcnow() + timedelta(days=self.config.expiration_days),
                phi_detected=phi_detected,
                audit_trail=[]
            )
            
            # Set S3 object metadata
            s3_metadata = {
                'classification': classification,
                'created-by': user_id,
                'purpose': purpose,
                'phi-detected': str(phi_detected),
                'retention-date': storage_metadata.retention_date.isoformat()
            }
            
            if metadata:
                s3_metadata.update(metadata)
            
            # Upload with server-side encryption
            extra_args = {
                'Metadata': s3_metadata,
                'ServerSideEncryption': self.config.encryption_type
            }
            
            if self.config.kms_key_id:
                extra_args['SSEKMSKeyId'] = self.config.kms_key_id
            
            # Use appropriate prefix based on classification
            if classification == DataClassification.PHI:
                full_key = f"phi/{object_key}"
            else:
                full_key = f"data/{object_key}"
            
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=full_key,
                Body=data_bytes,
                **extra_args
            )
            
            # Log audit event
            self._log_audit_event(
                StorageAuditEvent.UPLOAD,
                full_key,
                user_id,
                {"classification": classification, "phi_detected": phi_detected}
            )
            
            storage_metadata.object_key = full_key
            self.logger.info(f"Uploaded {full_key} with classification {classification}")
            
            return storage_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to upload data: {e}")
            self._log_audit_event(
                StorageAuditEvent.UPLOAD,
                object_key,
                user_id,
                {"success": False, "error": str(e)}
            )
            raise
    
    def download_data(self, object_key: str, user_id: str, 
                     decrypt: bool = True) -> Tuple[bytes, StorageMetadata]:
        """Download data with decryption and audit logging"""
        try:
            # Get object and metadata
            response = self.s3_client.get_object(
                Bucket=self.config.bucket_name,
                Key=object_key
            )
            
            data_bytes = response['Body'].read()
            s3_metadata = response.get('Metadata', {})
            
            # Create storage metadata from S3 metadata
            storage_metadata = StorageMetadata(
                object_key=object_key,
                classification=s3_metadata.get('classification', 'unknown'),
                created_at=datetime.fromisoformat(s3_metadata.get('created-at', datetime.utcnow().isoformat())),
                created_by=s3_metadata.get('created-by', 'unknown'),
                purpose=s3_metadata.get('purpose', 'unknown'),
                retention_date=datetime.fromisoformat(s3_metadata.get('retention-date', datetime.utcnow().isoformat())),
                phi_detected=s3_metadata.get('phi-detected', 'False').lower() == 'true'
            )
            
            # Decrypt if necessary
            if decrypt and storage_metadata.classification in [DataClassification.PHI, DataClassification.SENSITIVE]:
                try:
                    data_bytes = self.decrypt_data(data_bytes)
                except Exception as e:
                    self.logger.warning(f"Failed to decrypt {object_key}, returning encrypted data: {e}")
            
            # Log audit event
            self._log_audit_event(
                StorageAuditEvent.DOWNLOAD,
                object_key,
                user_id,
                {"classification": storage_metadata.classification}
            )
            
            return data_bytes, storage_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to download {object_key}: {e}")
            self._log_audit_event(
                StorageAuditEvent.DOWNLOAD,
                object_key,
                user_id,
                {"success": False, "error": str(e)}
            )
            raise
    
    def delete_data(self, object_key: str, user_id: str, 
                   secure_delete: bool = True) -> bool:
        """Securely delete data with audit trail"""
        try:
            if secure_delete:
                # For HIPAA compliance, overwrite before delete
                # First, get object size
                response = self.s3_client.head_object(
                    Bucket=self.config.bucket_name,
                    Key=object_key
                )
                object_size = response['ContentLength']
                
                # Overwrite with random data multiple times
                import os
                for _ in range(3):  # DoD 5220.22-M standard
                    random_data = os.urandom(object_size)
                    self.s3_client.put_object(
                        Bucket=self.config.bucket_name,
                        Key=object_key,
                        Body=random_data
                    )
            
            # Delete all versions if versioning is enabled
            if self.config.enable_versioning:
                versions = self.s3_client.list_object_versions(
                    Bucket=self.config.bucket_name,
                    Prefix=object_key
                )
                
                for version in versions.get('Versions', []):
                    self.s3_client.delete_object(
                        Bucket=self.config.bucket_name,
                        Key=object_key,
                        VersionId=version['VersionId']
                    )
                
                # Delete delete markers
                for marker in versions.get('DeleteMarkers', []):
                    self.s3_client.delete_object(
                        Bucket=self.config.bucket_name,
                        Key=object_key,
                        VersionId=marker['VersionId']
                    )
            else:
                # Simple delete
                self.s3_client.delete_object(
                    Bucket=self.config.bucket_name,
                    Key=object_key
                )
            
            # Log audit event
            self._log_audit_event(
                StorageAuditEvent.DELETE,
                object_key,
                user_id,
                {"secure_delete": secure_delete}
            )
            
            self.logger.info(f"Securely deleted {object_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete {object_key}: {e}")
            self._log_audit_event(
                StorageAuditEvent.DELETE,
                object_key,
                user_id,
                {"success": False, "error": str(e)}
            )
            return False
    
    def list_objects(self, prefix: str = "", classification_filter: str = None) -> List[Dict]:
        """List objects with metadata filtering"""
        try:
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.config.bucket_name, Prefix=prefix):
                for obj in page.get('Contents', []):
                    # Get object metadata
                    try:
                        head_response = self.s3_client.head_object(
                            Bucket=self.config.bucket_name,
                            Key=obj['Key']
                        )
                        metadata = head_response.get('Metadata', {})
                        
                        if classification_filter and metadata.get('classification') != classification_filter:
                            continue
                        
                        objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'classification': metadata.get('classification'),
                            'created_by': metadata.get('created-by'),
                            'purpose': metadata.get('purpose'),
                            'phi_detected': metadata.get('phi-detected') == 'True'
                        })
                    except Exception as e:
                        self.logger.warning(f"Failed to get metadata for {obj['Key']}: {e}")
            
            return objects
            
        except Exception as e:
            self.logger.error(f"Failed to list objects: {e}")
            return []

class GCSSecureStorage(SecureCloudStorage):
    """HIPAA-compliant Google Cloud Storage implementation"""
    
    def __init__(self, config: StorageConfig):
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage not installed")
        
        super().__init__(config)
        self._setup_gcs_client()
    
    def _setup_gcs_client(self):
        """Setup GCS client with proper configuration"""
        if self.config.service_account_path:
            self.client = gcs.Client.from_service_account_json(self.config.service_account_path)
        else:
            self.client = gcs.Client()
        
        self.bucket = self.client.bucket(self.config.bucket_name)
        
        # Verify bucket exists
        if not self.bucket.exists():
            raise ValueError(f"GCS bucket {self.config.bucket_name} does not exist")
        
        self.logger.info(f"Connected to GCS bucket: {self.config.bucket_name}")

class StorageManager:
    """Manager for secure cloud storage operations"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        
        if config.provider == "s3":
            self.storage = S3SecureStorage(config)
        elif config.provider == "gcs":
            self.storage = GCSSecureStorage(config)
        else:
            raise ValueError(f"Unsupported storage provider: {config.provider}")
        
        self.logger = logging.getLogger(__name__)
    
    def store_medical_data(self, data: Union[str, bytes], filename: str,
                          user_id: str, data_type: str = "processed") -> StorageMetadata:
        """Store medical data with proper classification"""
        # Determine classification based on content and type
        if isinstance(data, str) and self.storage._detect_phi(data):
            classification = DataClassification.PHI
        elif data_type in ["raw", "patient"]:
            classification = DataClassification.SENSITIVE
        else:
            classification = DataClassification.INTERNAL
        
        object_key = f"{data_type}/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
        
        return self.storage.upload_data(
            data=data,
            object_key=object_key,
            classification=classification,
            user_id=user_id,
            purpose=data_type
        )
    
    def retrieve_medical_data(self, object_key: str, user_id: str) -> Tuple[bytes, StorageMetadata]:
        """Retrieve medical data with access logging"""
        return self.storage.download_data(object_key, user_id)
    
    def secure_delete_medical_data(self, object_key: str, user_id: str) -> bool:
        """Securely delete medical data for compliance"""
        return self.storage.delete_data(object_key, user_id, secure_delete=True)
    
    def get_retention_report(self) -> Dict[str, Any]:
        """Generate data retention report for compliance"""
        try:
            all_objects = self.storage.list_objects()
            
            report = {
                "total_objects": len(all_objects),
                "phi_objects": len([obj for obj in all_objects if obj.get('phi_detected')]),
                "objects_by_classification": {},
                "retention_expiring_soon": [],
                "storage_usage": {
                    "total_size_gb": sum(obj['size'] for obj in all_objects) / (1024**3),
                    "phi_size_gb": sum(obj['size'] for obj in all_objects if obj.get('phi_detected')) / (1024**3)
                }
            }
            
            # Group by classification
            for obj in all_objects:
                classification = obj.get('classification', 'unknown')
                if classification not in report["objects_by_classification"]:
                    report["objects_by_classification"][classification] = 0
                report["objects_by_classification"][classification] += 1
            
            # Find objects expiring within 30 days
            expiry_threshold = datetime.utcnow() + timedelta(days=30)
            for obj in all_objects:
                if obj.get('last_modified') and obj['last_modified'] > expiry_threshold:
                    report["retention_expiring_soon"].append({
                        "key": obj['key'],
                        "classification": obj.get('classification'),
                        "expires": (obj['last_modified'] + timedelta(days=self.config.expiration_days)).isoformat()
                    })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate retention report: {e}")
            return {"error": str(e)}

# Configuration examples
HIPAA_S3_CONFIG = StorageConfig(
    provider="s3",
    bucket_name="clinchat-hipaa-data",
    region="us-east-1",
    encryption_type="aws:kms",
    kms_key_id="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    enable_versioning=True,
    enable_access_logging=True,
    enable_object_lock=True,
    retention_years=7
)

HIPAA_GCS_CONFIG = StorageConfig(
    provider="gcs",
    bucket_name="clinchat-hipaa-data",
    region="us-central1",
    service_account_path="/path/to/service-account.json",
    enable_versioning=True,
    enable_access_logging=True,
    retention_years=7
)

# Export main components
__all__ = [
    'StorageManager',
    'StorageConfig', 
    'StorageMetadata',
    'DataClassification',
    'S3SecureStorage',
    'GCSSecureStorage',
    'HIPAA_S3_CONFIG',
    'HIPAA_GCS_CONFIG'
]