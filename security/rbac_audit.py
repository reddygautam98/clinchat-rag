"""
Role-Based Access Control (RBAC) and Audit Logging System for ClinChat-RAG
Implements comprehensive access control with detailed audit trails for HIPAA compliance
"""

import json
import logging
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps
import jwt
from pathlib import Path

@dataclass
class User:
    """User entity with RBAC properties"""
    user_id: str
    username: str
    email: str
    full_name: str
    
    # RBAC properties
    roles: List[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    
    # Account status
    is_active: bool = True
    is_locked: bool = False
    password_hash: str = ""
    
    # HIPAA compliance
    hipaa_trained: bool = False
    training_expiry: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"

@dataclass
class Role:
    """Role definition with permissions"""
    role_id: str
    role_name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    
    # Hierarchy
    parent_roles: List[str] = field(default_factory=list)
    
    # Medical context
    department: Optional[str] = None
    specialization: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"

@dataclass
class Permission:
    """Permission definition"""
    permission_id: str
    permission_name: str
    description: str
    resource_type: str  # "data", "api", "ui", "admin"
    action: str  # "read", "write", "delete", "execute"
    
    # Context restrictions
    phi_access: bool = False
    emergency_access: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)

class ActionType(Enum):
    """Types of auditable actions"""
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    DATA_QUERY = "data_query"
    DATA_EXPORT = "data_export"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_ASSIGN = "role_assign"
    PERMISSION_GRANT = "permission_grant"
    SYSTEM_CONFIG = "system_config"
    PHI_ACCESS = "phi_access"
    EMERGENCY_ACCESS = "emergency_access"
    
class AccessResult(Enum):
    """Access control results"""
    GRANTED = "granted"
    DENIED = "denied"
    CONDITIONAL = "conditional"  # Requires additional approval

@dataclass
class AuditLogEntry:
    """Comprehensive audit log entry"""
    log_id: str
    timestamp: datetime
    
    # User context
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    
    # Action details
    action_type: ActionType
    resource_type: str
    resource_id: Optional[str]
    
    # Access control
    access_result: AccessResult
    permissions_used: List[str]
    
    # Context
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    
    # PHI handling
    phi_accessed: bool = False
    phi_types: List[str] = field(default_factory=list)
    
    # Compliance
    hipaa_justification: Optional[str] = None
    emergency_access: bool = False
    
    # Technical details
    processing_time_ms: int = 0
    error_message: Optional[str] = None

class RBACDatabase:
    """Database layer for RBAC and audit logging"""
    
    def __init__(self, db_path: str = "data/rbac.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize RBAC and audit database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_locked BOOLEAN DEFAULT FALSE,
                        hipaa_trained BOOLEAN DEFAULT FALSE,
                        training_expiry TIMESTAMP,
                        last_login TIMESTAMP,
                        failed_login_attempts INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system'
                    )
                """)
                
                # Roles table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS roles (
                        role_id TEXT PRIMARY KEY,
                        role_name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        department TEXT,
                        specialization TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system'
                    )
                """)
                
                # Permissions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS permissions (
                        permission_id TEXT PRIMARY KEY,
                        permission_name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        resource_type TEXT NOT NULL,
                        action TEXT NOT NULL,
                        phi_access BOOLEAN DEFAULT FALSE,
                        emergency_access BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # User-Role assignments
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_roles (
                        user_id TEXT NOT NULL,
                        role_id TEXT NOT NULL,
                        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        assigned_by TEXT NOT NULL,
                        expires_at TIMESTAMP,
                        PRIMARY KEY (user_id, role_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (role_id) REFERENCES roles (role_id)
                    )
                """)
                
                # Role-Permission assignments
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS role_permissions (
                        role_id TEXT NOT NULL,
                        permission_id TEXT NOT NULL,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        granted_by TEXT NOT NULL,
                        PRIMARY KEY (role_id, permission_id),
                        FOREIGN KEY (role_id) REFERENCES roles (role_id),
                        FOREIGN KEY (permission_id) REFERENCES permissions (permission_id)
                    )
                """)
                
                # Direct user permissions (overrides)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_permissions (
                        user_id TEXT NOT NULL,
                        permission_id TEXT NOT NULL,
                        granted BOOLEAN DEFAULT TRUE,
                        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        granted_by TEXT NOT NULL,
                        expires_at TIMESTAMP,
                        justification TEXT,
                        PRIMARY KEY (user_id, permission_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (permission_id) REFERENCES permissions (permission_id)
                    )
                """)
                
                # Comprehensive audit log
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        log_id TEXT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT NOT NULL,
                        session_id TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        action_type TEXT NOT NULL,
                        resource_type TEXT,
                        resource_id TEXT,
                        access_result TEXT NOT NULL,
                        permissions_used TEXT, -- JSON array
                        request_data TEXT,     -- JSON
                        response_data TEXT,    -- JSON
                        phi_accessed BOOLEAN DEFAULT FALSE,
                        phi_types TEXT,        -- JSON array
                        hipaa_justification TEXT,
                        emergency_access BOOLEAN DEFAULT FALSE,
                        processing_time_ms INTEGER DEFAULT 0,
                        error_message TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Session management
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Create indices for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_phi ON audit_log(phi_accessed)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)")
                
                self.logger.info("RBAC database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize RBAC database: {e}")
            raise

    def create_default_roles_permissions(self):
        """Create default roles and permissions for medical system"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Default permissions
                permissions = [
                    # Data permissions
                    ("data.read.public", "Read Public Data", "data", "read", False, False),
                    ("data.read.internal", "Read Internal Data", "data", "read", False, False),
                    ("data.read.phi", "Read PHI Data", "data", "read", True, False),
                    ("data.write.public", "Write Public Data", "data", "write", False, False),
                    ("data.write.internal", "Write Internal Data", "data", "write", False, False),
                    ("data.write.phi", "Write PHI Data", "data", "write", True, False),
                    ("data.export.deidentified", "Export De-identified Data", "data", "export", False, False),
                    ("data.export.phi", "Export PHI Data", "data", "export", True, False),
                    
                    # API permissions
                    ("api.query.basic", "Basic Query API", "api", "execute", False, False),
                    ("api.query.advanced", "Advanced Query API", "api", "execute", False, False),
                    ("api.llm.general", "General LLM Access", "api", "execute", False, False),
                    ("api.llm.phi", "PHI LLM Access", "api", "execute", True, False),
                    
                    # Admin permissions
                    ("admin.users.read", "Read Users", "admin", "read", False, False),
                    ("admin.users.write", "Manage Users", "admin", "write", False, False),
                    ("admin.roles.write", "Manage Roles", "admin", "write", False, False),
                    ("admin.audit.read", "Read Audit Logs", "admin", "read", False, False),
                    ("admin.system.config", "System Configuration", "admin", "write", False, False),
                    
                    # Emergency access
                    ("emergency.data.access", "Emergency Data Access", "data", "read", True, True),
                    ("emergency.override", "Emergency Override", "admin", "execute", True, True)
                ]
                
                for perm_id, name, resource, action, phi, emergency in permissions:
                    conn.execute("""
                        INSERT OR IGNORE INTO permissions 
                        (permission_id, permission_name, description, resource_type, action, phi_access, emergency_access)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (perm_id, name, name, resource, action, phi, emergency))
                
                # Default roles
                roles = [
                    ("physician", "Physician", "Licensed medical doctor with full clinical access"),
                    ("nurse", "Nurse", "Registered nurse with patient care access"),
                    ("researcher", "Researcher", "Medical researcher with data analysis access"),
                    ("admin", "Administrator", "System administrator with full access"),
                    ("viewer", "Viewer", "Read-only access to de-identified data"),
                    ("emergency", "Emergency Access", "Emergency access role for critical situations")
                ]
                
                for role_id, name, desc in roles:
                    conn.execute("""
                        INSERT OR IGNORE INTO roles (role_id, role_name, description)
                        VALUES (?, ?, ?)
                    """, (role_id, name, desc))
                
                # Role-permission assignments
                role_permissions = [
                    # Physician - full access
                    ("physician", "data.read.phi"),
                    ("physician", "data.write.phi"),
                    ("physician", "api.query.advanced"),
                    ("physician", "api.llm.phi"),
                    
                    # Nurse - patient care access
                    ("nurse", "data.read.phi"),
                    ("nurse", "data.write.internal"),
                    ("nurse", "api.query.basic"),
                    ("nurse", "api.llm.general"),
                    
                    # Researcher - data analysis
                    ("researcher", "data.read.internal"),
                    ("researcher", "data.export.deidentified"),
                    ("researcher", "api.query.advanced"),
                    ("researcher", "api.llm.general"),
                    
                    # Admin - system management
                    ("admin", "admin.users.write"),
                    ("admin", "admin.roles.write"),
                    ("admin", "admin.audit.read"),
                    ("admin", "admin.system.config"),
                    
                    # Viewer - read-only
                    ("viewer", "data.read.public"),
                    ("viewer", "api.query.basic"),
                    
                    # Emergency - critical access
                    ("emergency", "emergency.data.access"),
                    ("emergency", "emergency.override")
                ]
                
                for role_id, perm_id in role_permissions:
                    conn.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_by)
                        VALUES (?, ?, 'system')
                    """, (role_id, perm_id))
                
                conn.commit()
                self.logger.info("Default roles and permissions created")
                
        except Exception as e:
            self.logger.error(f"Failed to create default roles/permissions: {e}")
            raise

class AccessController:
    """Main access control engine"""
    
    def __init__(self, db: RBACDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._permission_cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    def authenticate_user(self, username: str, password: str, ip_address: str, 
                         user_agent: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and create session"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user
                cursor.execute("""
                    SELECT user_id, username, password_hash, is_active, is_locked, 
                           failed_login_attempts, hipaa_trained, training_expiry
                    FROM users WHERE username = ?
                """, (username,))
                
                user_row = cursor.fetchone()
                if not user_row:
                    self._log_access_attempt(None, ActionType.LOGIN, AccessResult.DENIED, 
                                           ip_address, user_agent, "User not found")
                    return None
                
                user_id, username, password_hash, is_active, is_locked, failed_attempts, hipaa_trained, training_expiry = user_row
                
                # Check account status
                if is_locked:
                    self._log_access_attempt(user_id, ActionType.LOGIN, AccessResult.DENIED,
                                           ip_address, user_agent, "Account locked")
                    return None
                
                if not is_active:
                    self._log_access_attempt(user_id, ActionType.LOGIN, AccessResult.DENIED,
                                           ip_address, user_agent, "Account disabled")
                    return None
                
                # Verify password
                if not self._verify_password(password, password_hash):
                    # Increment failed attempts
                    failed_attempts += 1
                    cursor.execute("""
                        UPDATE users SET failed_login_attempts = ?, 
                               is_locked = CASE WHEN ? >= 5 THEN TRUE ELSE FALSE END
                        WHERE user_id = ?
                    """, (failed_attempts, failed_attempts, user_id))
                    
                    self._log_access_attempt(user_id, ActionType.LOGIN, AccessResult.DENIED,
                                           ip_address, user_agent, f"Invalid password ({failed_attempts} attempts)")
                    return None
                
                # Check HIPAA training
                if hipaa_trained and training_expiry:
                    if datetime.fromisoformat(training_expiry) < datetime.utcnow():
                        self._log_access_attempt(user_id, ActionType.LOGIN, AccessResult.DENIED,
                                               ip_address, user_agent, "HIPAA training expired")
                        return None
                
                # Create session
                session_id = self._create_session(user_id, ip_address, user_agent)
                
                # Reset failed attempts and update last login
                cursor.execute("""
                    UPDATE users SET failed_login_attempts = 0, last_login = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                
                # Log successful login
                self._log_access_attempt(user_id, ActionType.LOGIN, AccessResult.GRANTED,
                                       ip_address, user_agent, "Successful login", session_id)
                
                # Get user permissions
                permissions = self._get_user_permissions(user_id)
                
                return {
                    "user_id": user_id,
                    "username": username,
                    "session_id": session_id,
                    "permissions": list(permissions),
                    "hipaa_trained": hipaa_trained
                }
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return None
    
    def check_permission(self, user_id: str, session_id: str, permission: str,
                        resource_id: str = None, phi_context: bool = False,
                        emergency_access: bool = False) -> Tuple[bool, str]:
        """Check if user has specific permission"""
        try:
            # Validate session
            if not self._validate_session(session_id, user_id):
                return False, "Invalid or expired session"
            
            # Get user permissions (with caching)
            permissions = self._get_user_permissions_cached(user_id)
            
            # Check basic permission
            if permission not in permissions:
                self._log_access_check(user_id, session_id, permission, resource_id, 
                                     AccessResult.DENIED, "Permission not granted")
                return False, "Permission not granted"
            
            # Additional checks for PHI access
            if phi_context:
                if not self._check_phi_permission(user_id, permission):
                    self._log_access_check(user_id, session_id, permission, resource_id,
                                         AccessResult.DENIED, "PHI access not authorized")
                    return False, "PHI access not authorized"
            
            # Emergency access logging
            if emergency_access:
                self._log_emergency_access(user_id, session_id, permission, resource_id)
            
            self._log_access_check(user_id, session_id, permission, resource_id,
                                 AccessResult.GRANTED, "Access granted")
            return True, "Access granted"
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False, f"Permission check error: {str(e)}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        # In production, use proper password hashing (bcrypt, scrypt, etc.)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def _create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create user session"""
        import uuid
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=8)  # 8-hour sessions
        
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, user_id, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_id, ip_address, user_agent, expires_at))
        
        return session_id
    
    def _validate_session(self, session_id: str, user_id: str) -> bool:
        """Validate user session"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, expires_at, is_active FROM sessions 
                    WHERE session_id = ? AND user_id = ?
                """, (session_id, user_id))
                
                session = cursor.fetchone()
                if not session:
                    return False
                
                session_user_id, expires_at, is_active = session
                
                if not is_active:
                    return False
                
                if datetime.fromisoformat(expires_at) < datetime.utcnow():
                    # Expire session
                    cursor.execute("UPDATE sessions SET is_active = FALSE WHERE session_id = ?", 
                                 (session_id,))
                    conn.commit()
                    return False
                
                # Update last activity
                cursor.execute("""
                    UPDATE sessions SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_id = ?
                """, (session_id,))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return False
    
    def _get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for user (including role-based)"""
        permissions = set()
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get permissions from roles
                cursor.execute("""
                    SELECT DISTINCT p.permission_id
                    FROM permissions p
                    JOIN role_permissions rp ON p.permission_id = rp.permission_id
                    JOIN user_roles ur ON rp.role_id = ur.role_id
                    WHERE ur.user_id = ? 
                      AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
                """, (user_id,))
                
                for (perm,) in cursor.fetchall():
                    permissions.add(perm)
                
                # Get direct user permissions (overrides)
                cursor.execute("""
                    SELECT permission_id, granted FROM user_permissions
                    WHERE user_id = ? 
                      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (user_id,))
                
                for perm_id, granted in cursor.fetchall():
                    if granted:
                        permissions.add(perm_id)
                    else:
                        permissions.discard(perm_id)  # Explicit denial
                
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {e}")
        
        return permissions
    
    def _get_user_permissions_cached(self, user_id: str) -> Set[str]:
        """Get user permissions with caching"""
        cache_key = f"permissions:{user_id}"
        now = time.time()
        
        if cache_key in self._permission_cache:
            cached_data, timestamp = self._permission_cache[cache_key]
            if now - timestamp < self._cache_timeout:
                return cached_data
        
        permissions = self._get_user_permissions(user_id)
        self._permission_cache[cache_key] = (permissions, now)
        return permissions
    
    def _check_phi_permission(self, user_id: str, permission: str) -> bool:
        """Check if user can access PHI with this permission"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if permission allows PHI access
                cursor.execute("""
                    SELECT phi_access FROM permissions WHERE permission_id = ?
                """, (permission,))
                
                result = cursor.fetchone()
                return result and result[0]
                
        except Exception as e:
            self.logger.error(f"PHI permission check failed: {e}")
            return False
    
    def _log_access_attempt(self, user_id: Optional[str], action: ActionType, 
                           result: AccessResult, ip_address: str, user_agent: str,
                           details: str, session_id: str = None):
        """Log access attempt"""
        self._log_audit_entry(
            user_id=user_id or "unknown",
            session_id=session_id,
            action_type=action,
            access_result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=details if result == AccessResult.DENIED else None
        )
    
    def _log_access_check(self, user_id: str, session_id: str, permission: str,
                         resource_id: str, result: AccessResult, details: str):
        """Log permission check"""
        self._log_audit_entry(
            user_id=user_id,
            session_id=session_id,
            action_type=ActionType.DATA_ACCESS,
            access_result=result,
            resource_id=resource_id,
            permissions_used=[permission],
            error_message=details if result == AccessResult.DENIED else None
        )
    
    def _log_emergency_access(self, user_id: str, session_id: str, 
                             permission: str, resource_id: str):
        """Log emergency access"""
        self._log_audit_entry(
            user_id=user_id,
            session_id=session_id,
            action_type=ActionType.EMERGENCY_ACCESS,
            access_result=AccessResult.GRANTED,
            resource_id=resource_id,
            permissions_used=[permission],
            emergency_access=True
        )
    
    def _log_audit_entry(self, user_id: str, session_id: str = None, 
                        action_type: ActionType = ActionType.DATA_ACCESS,
                        access_result: AccessResult = AccessResult.GRANTED,
                        resource_type: str = None, resource_id: str = None,
                        permissions_used: List[str] = None,
                        ip_address: str = None, user_agent: str = None,
                        phi_accessed: bool = False, phi_types: List[str] = None,
                        emergency_access: bool = False, error_message: str = None):
        """Log comprehensive audit entry"""
        try:
            import uuid
            log_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_log (
                        log_id, user_id, session_id, ip_address, user_agent,
                        action_type, resource_type, resource_id, access_result,
                        permissions_used, phi_accessed, phi_types, emergency_access,
                        error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id, user_id, session_id, ip_address, user_agent,
                    action_type.value, resource_type, resource_id, access_result.value,
                    json.dumps(permissions_used or []),
                    phi_accessed, json.dumps(phi_types or []),
                    emergency_access, error_message
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to log audit entry: {e}")

def require_permission(permission: str, phi_context: bool = False):
    """Decorator for enforcing permissions on API endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request context (implementation depends on web framework)
            # This is a simplified example
            request = kwargs.get('request')  # Assume request object passed
            if not request:
                return {"error": "No request context", "status_code": 400}
            
            user_id = request.headers.get('X-User-ID')
            session_id = request.headers.get('X-Session-ID')
            
            if not user_id or not session_id:
                return {"error": "Authentication required", "status_code": 401}
            
            # Check permission
            access_controller = kwargs.get('access_controller')
            if not access_controller:
                return {"error": "Access controller not available", "status_code": 500}
            
            has_permission, reason = access_controller.check_permission(
                user_id, session_id, permission, phi_context=phi_context
            )
            
            if not has_permission:
                return {"error": f"Access denied: {reason}", "status_code": 403}
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Global instances
rbac_db = RBACDatabase()
access_controller = AccessController(rbac_db)

# Export main components
__all__ = [
    'RBACDatabase',
    'AccessController', 
    'User',
    'Role',
    'Permission',
    'AuditLogEntry',
    'ActionType',
    'AccessResult',
    'require_permission',
    'rbac_db',
    'access_controller'
]