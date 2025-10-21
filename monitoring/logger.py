"""
ClinChat-RAG Logging System
Comprehensive logging for queries, chunks, LLM outputs, latency, and security
"""

import json
import logging
import time
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading
from contextlib import contextmanager
import os

# Configure secure logging directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

@dataclass
class QueryLogEntry:
    """Structured log entry for medical queries"""
    session_id: str
    timestamp: datetime
    query_hash: str  # SHA-256 hash for privacy
    query_length: int
    use_hybrid_search: bool
    user_ip_hash: str  # Hashed IP for privacy
    user_agent_hash: str  # Hashed user agent
    
@dataclass
class RetrievalLogEntry:
    """Log entry for document retrieval"""
    session_id: str
    timestamp: datetime
    chunk_ids: List[str]
    chunk_count: int
    retrieval_scores: List[float]
    retrieval_method: str
    retrieval_latency_ms: float
    
@dataclass
class LLMLogEntry:
    """Log entry for LLM interactions"""
    session_id: str
    timestamp: datetime
    model_name: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    llm_latency_ms: float
    temperature: float
    response_hash: str  # SHA-256 hash for privacy
    response_length: int
    
@dataclass
class ResponseLogEntry:
    """Complete response log entry"""
    session_id: str
    timestamp: datetime
    total_latency_ms: float
    success: bool
    error_type: Optional[str]
    confidence_score: Optional[float]
    source_count: int
    hallucination_flag: Optional[bool]
    human_review_flag: Optional[bool]
    
@dataclass
class SecurityLogEntry:
    """Security and audit log entry"""
    session_id: str
    timestamp: datetime
    event_type: str  # 'query', 'error', 'security_alert'
    ip_hash: str
    user_agent_hash: str
    risk_score: Optional[float]
    details: Dict[str, Any]

class SecureLogger:
    """Secure, structured logger for ClinChat-RAG"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper())
        self.loggers = {}
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_latency": 0.0,
            "queries_per_minute": 0,
            "hallucination_flags": 0,
        }
        self.metrics_lock = threading.Lock()
        
        # Setup different log files
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup different loggers for different types of logs"""
        
        # Query Logger
        self.loggers['query'] = self._create_logger(
            'query_logger',
            LOGS_DIR / 'queries.log',
            max_bytes=50*1024*1024,  # 50MB
            backup_count=10
        )
        
        # Retrieval Logger
        self.loggers['retrieval'] = self._create_logger(
            'retrieval_logger',
            LOGS_DIR / 'retrieval.log',
            max_bytes=50*1024*1024,
            backup_count=10
        )
        
        # LLM Logger
        self.loggers['llm'] = self._create_logger(
            'llm_logger',
            LOGS_DIR / 'llm.log',
            max_bytes=50*1024*1024,
            backup_count=10
        )
        
        # Response Logger
        self.loggers['response'] = self._create_logger(
            'response_logger',
            LOGS_DIR / 'responses.log',
            max_bytes=50*1024*1024,
            backup_count=10
        )
        
        # Security Logger
        self.loggers['security'] = self._create_logger(
            'security_logger',
            LOGS_DIR / 'security.log',
            max_bytes=100*1024*1024,  # 100MB for security
            backup_count=20
        )
        
        # Error Logger
        self.loggers['error'] = self._create_logger(
            'error_logger',
            LOGS_DIR / 'errors.log',
            max_bytes=50*1024*1024,
            backup_count=15
        )
        
        # Metrics Logger (for dashboard)
        self.loggers['metrics'] = self._create_logger(
            'metrics_logger',
            LOGS_DIR / 'metrics.log',
            max_bytes=25*1024*1024,
            backup_count=5
        )
        
    def _create_logger(self, name: str, log_file: Path, max_bytes: int, backup_count: int) -> logging.Logger:
        """Create a configured logger with rotation"""
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Rotating file handler
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # JSON formatter for structured logging
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    @staticmethod
    def _hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for privacy"""
        if not data:
            return ""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]
    
    def log_query(self, query: str, use_hybrid_search: bool, user_ip: str = "", user_agent: str = "") -> str:
        """Log incoming query with privacy protection"""
        session_id = str(uuid.uuid4())
        
        entry = QueryLogEntry(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            query_hash=self._hash_sensitive_data(query),
            query_length=len(query),
            use_hybrid_search=use_hybrid_search,
            user_ip_hash=self._hash_sensitive_data(user_ip),
            user_agent_hash=self._hash_sensitive_data(user_agent)
        )
        
        self.loggers['query'].info(json.dumps(asdict(entry), default=str))
        
        # Update metrics
        with self.metrics_lock:
            self.metrics["total_queries"] += 1
            
        return session_id
    
    def log_retrieval(self, session_id: str, chunk_ids: List[str], scores: List[float], 
                     method: str, latency_ms: float):
        """Log document retrieval information"""
        entry = RetrievalLogEntry(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            chunk_ids=chunk_ids,
            chunk_count=len(chunk_ids),
            retrieval_scores=scores,
            retrieval_method=method,
            retrieval_latency_ms=latency_ms
        )
        
        self.loggers['retrieval'].info(json.dumps(asdict(entry), default=str))
    
    def log_llm_interaction(self, session_id: str, model_name: str, response: str,
                           prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None,
                           latency_ms: float = 0.0, temperature: float = 0.0):
        """Log LLM interaction with privacy protection"""
        entry = LLMLogEntry(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=(prompt_tokens or 0) + (completion_tokens or 0) if prompt_tokens and completion_tokens else None,
            llm_latency_ms=latency_ms,
            temperature=temperature,
            response_hash=self._hash_sensitive_data(response),
            response_length=len(response)
        )
        
        self.loggers['llm'].info(json.dumps(asdict(entry), default=str))
    
    def log_response(self, session_id: str, total_latency_ms: float, success: bool,
                    error_type: Optional[str] = None, confidence_score: Optional[float] = None,
                    source_count: int = 0, hallucination_flag: Optional[bool] = None,
                    human_review_flag: Optional[bool] = None):
        """Log complete response information"""
        entry = ResponseLogEntry(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            total_latency_ms=total_latency_ms,
            success=success,
            error_type=error_type,
            confidence_score=confidence_score,
            source_count=source_count,
            hallucination_flag=hallucination_flag,
            human_review_flag=human_review_flag
        )
        
        self.loggers['response'].info(json.dumps(asdict(entry), default=str))
        
        # Update metrics
        with self.metrics_lock:
            if success:
                self.metrics["successful_queries"] += 1
            else:
                self.metrics["failed_queries"] += 1
                
            # Update average latency (simple moving average)
            current_avg = self.metrics["average_latency"]
            total_queries = self.metrics["total_queries"]
            self.metrics["average_latency"] = (current_avg * (total_queries - 1) + total_latency_ms) / total_queries
            
            if hallucination_flag:
                self.metrics["hallucination_flags"] += 1
    
    def log_security_event(self, session_id: str, event_type: str, user_ip: str = "",
                          user_agent: str = "", risk_score: Optional[float] = None,
                          details: Optional[Dict[str, Any]] = None):
        """Log security events"""
        entry = SecurityLogEntry(
            session_id=session_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            ip_hash=self._hash_sensitive_data(user_ip),
            user_agent_hash=self._hash_sensitive_data(user_agent),
            risk_score=risk_score,
            details=details or {}
        )
        
        self.loggers['security'].warning(json.dumps(asdict(entry), default=str))
    
    def log_error(self, session_id: str, error_type: str, error_message: str, 
                 stack_trace: Optional[str] = None):
        """Log error information"""
        error_data = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace
        }
        
        self.loggers['error'].error(json.dumps(error_data, default=str))
    
    def log_metrics_snapshot(self):
        """Log current metrics for dashboard consumption"""
        with self.metrics_lock:
            metrics_snapshot = {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics.copy()
            }
        
        self.loggers['metrics'].info(json.dumps(metrics_snapshot, default=str))
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        with self.metrics_lock:
            return self.metrics.copy()

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
            
        return json.dumps(log_entry, default=str)

class LoggingContext:
    """Context manager for logging operations"""
    
    def __init__(self, logger: SecureLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.session_id = None
        self.start_time = None
        
    def __enter__(self):
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        latency_ms = (end_time - self.start_time) * 1000
        
        if exc_type:
            self.logger.log_error(
                self.session_id,
                exc_type.__name__,
                str(exc_val),
                str(exc_tb) if exc_tb else None
            )
            self.logger.log_response(
                self.session_id,
                latency_ms,
                success=False,
                error_type=exc_type.__name__
            )
        else:
            self.logger.log_response(
                self.session_id,
                latency_ms,
                success=True
            )

# Global logger instance
secure_logger = SecureLogger()

@contextmanager
def log_operation(operation_name: str):
    """Context manager for logging operations"""
    with LoggingContext(secure_logger, operation_name) as ctx:
        yield ctx

# Metrics collection thread
def start_metrics_collection():
    """Start background metrics collection"""
    def collect_metrics():
        while True:
            try:
                secure_logger.log_metrics_snapshot()
                time.sleep(60)  # Log metrics every minute
            except Exception as e:
                secure_logger.log_error("metrics_collector", "MetricsError", str(e))
                time.sleep(60)
    
    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()
    return metrics_thread