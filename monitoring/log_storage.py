"""
ClinChat-RAG Log Management System
Secure log storage, rotation, compression, and retention
"""

import os
import gzip
import shutil
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import schedule
import time
from cryptography.fernet import Fernet
import tarfile

LOGS_DIR = Path("logs")
ARCHIVE_DIR = Path("logs/archive")
DATABASE_PATH = Path("logs/clinchat_logs.db")

@dataclass
class LogRetentionPolicy:
    """Log retention policy configuration"""
    raw_logs_days: int = 30        # Keep raw logs for 30 days
    compressed_logs_days: int = 90  # Keep compressed logs for 90 days
    database_logs_days: int = 365   # Keep database logs for 1 year
    max_log_size_mb: int = 50      # Max size before rotation
    compression_enabled: bool = True
    encryption_enabled: bool = True

class SecureLogStorage:
    """Secure log storage with encryption, compression, and retention"""
    
    def __init__(self, retention_policy: Optional[LogRetentionPolicy] = None):
        self.retention_policy = retention_policy or LogRetentionPolicy()
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.retention_policy.encryption_enabled else None
        
        # Create directories
        LOGS_DIR.mkdir(exist_ok=True)
        ARCHIVE_DIR.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Start background tasks
        self._start_maintenance_scheduler()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for log files"""
        key_file = LOGS_DIR / ".log_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file (Unix systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(key_file, 0o600)
            
            return key
    
    def _init_database(self):
        """Initialize SQLite database for log indexing and fast queries"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Queries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queries (
                    session_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    query_length INTEGER NOT NULL,
                    use_hybrid_search BOOLEAN NOT NULL,
                    user_ip_hash TEXT,
                    user_agent_hash TEXT,
                    total_latency_ms REAL,
                    success BOOLEAN,
                    error_type TEXT,
                    confidence_score REAL,
                    source_count INTEGER,
                    hallucination_flag BOOLEAN,
                    human_review_flag BOOLEAN
                )
            ''')
            
            # Retrieval table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retrievals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    retrieval_method TEXT NOT NULL,
                    retrieval_latency_ms REAL NOT NULL,
                    avg_score REAL,
                    FOREIGN KEY (session_id) REFERENCES queries (session_id)
                )
            ''')
            
            # LLM interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    llm_latency_ms REAL NOT NULL,
                    temperature REAL,
                    response_hash TEXT NOT NULL,
                    response_length INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES queries (session_id)
                )
            ''')
            
            # Errors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT
                )
            ''')
            
            # Security events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    ip_hash TEXT,
                    user_agent_hash TEXT,
                    risk_score REAL,
                    details TEXT
                )
            ''')
            
            # Metrics snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_queries INTEGER,
                    successful_queries INTEGER,
                    failed_queries INTEGER,
                    average_latency REAL,
                    queries_per_minute INTEGER,
                    hallucination_flags INTEGER
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retrievals_timestamp ON retrievals (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_timestamp ON llm_interactions (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_snapshots (timestamp)')
            
            conn.commit()
    
    def store_log_entry(self, log_type: str, log_data: Dict[str, Any]):
        """Store log entry in database for fast querying"""
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                if log_type == 'query':
                    cursor.execute('''
                        INSERT OR REPLACE INTO queries 
                        (session_id, timestamp, query_hash, query_length, use_hybrid_search, 
                         user_ip_hash, user_agent_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log_data['session_id'],
                        log_data['timestamp'],
                        log_data['query_hash'],
                        log_data['query_length'],
                        log_data['use_hybrid_search'],
                        log_data['user_ip_hash'],
                        log_data['user_agent_hash']
                    ))
                
                elif log_type == 'response':
                    cursor.execute('''
                        UPDATE queries SET
                        total_latency_ms = ?, success = ?, error_type = ?,
                        confidence_score = ?, source_count = ?, 
                        hallucination_flag = ?, human_review_flag = ?
                        WHERE session_id = ?
                    ''', (
                        log_data['total_latency_ms'],
                        log_data['success'],
                        log_data.get('error_type'),
                        log_data.get('confidence_score'),
                        log_data['source_count'],
                        log_data.get('hallucination_flag'),
                        log_data.get('human_review_flag'),
                        log_data['session_id']
                    ))
                
                elif log_type == 'retrieval':
                    avg_score = sum(log_data['retrieval_scores']) / len(log_data['retrieval_scores']) if log_data['retrieval_scores'] else 0
                    cursor.execute('''
                        INSERT INTO retrievals 
                        (session_id, timestamp, chunk_count, retrieval_method, 
                         retrieval_latency_ms, avg_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        log_data['session_id'],
                        log_data['timestamp'],
                        log_data['chunk_count'],
                        log_data['retrieval_method'],
                        log_data['retrieval_latency_ms'],
                        avg_score
                    ))
                
                elif log_type == 'llm':
                    cursor.execute('''
                        INSERT INTO llm_interactions 
                        (session_id, timestamp, model_name, prompt_tokens, completion_tokens,
                         total_tokens, llm_latency_ms, temperature, response_hash, response_length)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log_data['session_id'],
                        log_data['timestamp'],
                        log_data['model_name'],
                        log_data.get('prompt_tokens'),
                        log_data.get('completion_tokens'),
                        log_data.get('total_tokens'),
                        log_data['llm_latency_ms'],
                        log_data['temperature'],
                        log_data['response_hash'],
                        log_data['response_length']
                    ))
                
                elif log_type == 'error':
                    cursor.execute('''
                        INSERT INTO errors 
                        (session_id, timestamp, error_type, error_message, stack_trace)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        log_data.get('session_id'),
                        log_data['timestamp'],
                        log_data['error_type'],
                        log_data['error_message'],
                        log_data.get('stack_trace')
                    ))
                
                elif log_type == 'security':
                    cursor.execute('''
                        INSERT INTO security_events 
                        (session_id, timestamp, event_type, ip_hash, user_agent_hash, 
                         risk_score, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log_data['session_id'],
                        log_data['timestamp'],
                        log_data['event_type'],
                        log_data['ip_hash'],
                        log_data['user_agent_hash'],
                        log_data.get('risk_score'),
                        json.dumps(log_data.get('details', {}))
                    ))
                
                elif log_type == 'metrics':
                    metrics = log_data['metrics']
                    cursor.execute('''
                        INSERT INTO metrics_snapshots 
                        (timestamp, total_queries, successful_queries, failed_queries,
                         average_latency, queries_per_minute, hallucination_flags)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        log_data['timestamp'],
                        metrics['total_queries'],
                        metrics['successful_queries'],
                        metrics['failed_queries'],
                        metrics['average_latency'],
                        metrics.get('queries_per_minute', 0),
                        metrics['hallucination_flags']
                    ))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error storing log entry: {e}")
    
    def compress_log_file(self, log_file_path: Path) -> Path:
        """Compress a log file and optionally encrypt it"""
        compressed_path = ARCHIVE_DIR / f"{log_file_path.name}.gz"
        
        with open(log_file_path, 'rb') as f_in:
            data = f_in.read()
            
            # Encrypt if enabled
            if self.fernet:
                data = self.fernet.encrypt(data)
            
            # Compress
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.write(data)
        
        return compressed_path
    
    def rotate_logs(self):
        """Rotate logs based on size and age"""
        for log_file in LOGS_DIR.glob("*.log"):
            try:
                # Check file size
                size_mb = log_file.stat().st_size / (1024 * 1024)
                
                # Check file age
                file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                should_rotate = (
                    size_mb > self.retention_policy.max_log_size_mb or
                    file_age.days > self.retention_policy.raw_logs_days
                )
                
                if should_rotate:
                    # Create timestamped backup
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = ARCHIVE_DIR / f"{log_file.stem}_{timestamp}.log"
                    
                    # Move to archive
                    shutil.move(log_file, backup_path)
                    
                    # Compress if enabled
                    if self.retention_policy.compression_enabled:
                        compressed_path = self.compress_log_file(backup_path)
                        backup_path.unlink()  # Remove uncompressed version
                        print(f"Rotated and compressed log: {compressed_path}")
                    else:
                        print(f"Rotated log: {backup_path}")
                        
            except Exception as e:
                print(f"Error rotating log {log_file}: {e}")
    
    def cleanup_old_logs(self):
        """Clean up old logs based on retention policy"""
        now = datetime.now()
        
        # Clean up compressed logs
        for archive_file in ARCHIVE_DIR.glob("*.gz"):
            try:
                file_age = now - datetime.fromtimestamp(archive_file.stat().st_mtime)
                
                if file_age.days > self.retention_policy.compressed_logs_days:
                    archive_file.unlink()
                    print(f"Deleted old compressed log: {archive_file}")
                    
            except Exception as e:
                print(f"Error cleaning up {archive_file}: {e}")
        
        # Clean up database records
        try:
            cutoff_date = now - timedelta(days=self.retention_policy.database_logs_days)
            cutoff_str = cutoff_date.isoformat()
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Delete old records
                for table in ['queries', 'retrievals', 'llm_interactions', 'errors', 
                            'security_events', 'metrics_snapshots']:
                    cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_str,))
                
                # Vacuum to reclaim space
                cursor.execute('VACUUM')
                conn.commit()
                
                print(f"Cleaned up database records older than {cutoff_date}")
                
        except Exception as e:
            print(f"Error cleaning up database: {e}")
    
    def create_backup(self) -> Path:
        """Create a complete backup of logs and database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"logs/backup_clinchat_{timestamp}.tar.gz")
        
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add database
            if DATABASE_PATH.exists():
                tar.add(DATABASE_PATH, arcname="clinchat_logs.db")
            
            # Add log files
            for log_file in LOGS_DIR.glob("*.log"):
                tar.add(log_file, arcname=f"logs/{log_file.name}")
            
            # Add archived logs
            for archive_file in ARCHIVE_DIR.glob("*"):
                tar.add(archive_file, arcname=f"archive/{archive_file.name}")
        
        print(f"Created backup: {backup_path}")
        return backup_path
    
    def get_dashboard_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for dashboard over specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Query metrics
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_queries,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_queries,
                        AVG(total_latency_ms) as avg_latency,
                        AVG(confidence_score) as avg_confidence,
                        SUM(CASE WHEN hallucination_flag = 1 THEN 1 ELSE 0 END) as hallucination_flags,
                        AVG(source_count) as avg_sources
                    FROM queries 
                    WHERE timestamp > ?
                ''', (cutoff_str,))
                
                row = cursor.fetchone()
                
                # Get latency percentiles
                cursor.execute('''
                    SELECT total_latency_ms 
                    FROM queries 
                    WHERE timestamp > ? AND total_latency_ms IS NOT NULL
                    ORDER BY total_latency_ms
                ''', (cutoff_str,))
                
                latencies = [row[0] for row in cursor.fetchall()]
                
                p50 = latencies[len(latencies)//2] if latencies else 0
                p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
                p99 = latencies[int(len(latencies)*0.99)] if latencies else 0
                
                # Get QPS over time (hourly buckets)
                cursor.execute('''
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as queries
                    FROM queries 
                    WHERE timestamp > ?
                    GROUP BY hour
                    ORDER BY hour
                ''', (cutoff_str,))
                
                qps_data = [(hour, queries/3600) for hour, queries in cursor.fetchall()]
                
                return {
                    'summary': {
                        'total_queries': row[0] or 0,
                        'successful_queries': row[1] or 0,
                        'failed_queries': row[2] or 0,
                        'success_rate': (row[1] or 0) / max(row[0] or 1, 1) * 100,
                        'avg_latency_ms': row[3] or 0,
                        'avg_confidence': row[4] or 0,
                        'hallucination_flags': row[5] or 0,
                        'avg_sources': row[6] or 0
                    },
                    'latency_percentiles': {
                        'p50': p50,
                        'p95': p95,
                        'p99': p99
                    },
                    'qps_hourly': qps_data,
                    'period_hours': hours,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Error getting dashboard metrics: {e}")
            return {}
    
    def _start_maintenance_scheduler(self):
        """Start background maintenance tasks"""
        def run_maintenance():
            schedule.every(6).hours.do(self.rotate_logs)
            schedule.every().day.at("02:00").do(self.cleanup_old_logs)
            schedule.every().sunday.at("03:00").do(self.create_backup)
            
            while True:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
        
        maintenance_thread = threading.Thread(target=run_maintenance, daemon=True)
        maintenance_thread.start()

# Global log storage instance
log_storage = SecureLogStorage()

# Hook into the secure logger to store in database
def enhanced_store_log_entry(log_type: str, log_data: Any):
    """Enhanced log storage that also updates the database"""
    if hasattr(log_data, '__dict__'):
        log_dict = log_data.__dict__
    elif isinstance(log_data, dict):
        log_dict = log_data
    else:
        try:
            log_dict = json.loads(log_data)
        except:
            return
    
    log_storage.store_log_entry(log_type, log_dict)

# Export main components
__all__ = [
    'SecureLogStorage',
    'LogRetentionPolicy', 
    'log_storage',
    'enhanced_store_log_entry'
]