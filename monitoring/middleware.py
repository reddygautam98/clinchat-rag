"""
ClinChat-RAG Monitoring Middleware
FastAPI middleware for QPS, latency, and medical-specific metrics collection
"""

import time
import json
from typing import Dict, Optional
from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

from monitoring.logger import secure_logger

# Prometheus metrics
REQUEST_COUNT = Counter(
    'clinchat_requests_total', 
    'Total requests', 
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'clinchat_request_duration_seconds', 
    'Request latency', 
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    'clinchat_active_requests', 
    'Active requests'
)

QPS_GAUGE = Gauge(
    'clinchat_queries_per_second', 
    'Queries per second'
)

ERROR_RATE = Gauge(
    'clinchat_error_rate', 
    'Error rate percentage'
)

HALLUCINATION_FLAGS = Counter(
    'clinchat_hallucination_flags_total', 
    'Total hallucination flags'
)

CONFIDENCE_SCORE = Histogram(
    'clinchat_confidence_score', 
    'Response confidence scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

RETRIEVAL_LATENCY = Histogram(
    'clinchat_retrieval_duration_seconds',
    'Document retrieval latency',
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

LLM_LATENCY = Histogram(
    'clinchat_llm_duration_seconds',
    'LLM response latency', 
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0]
)

SOURCE_COUNT = Histogram(
    'clinchat_sources_count',
    'Number of sources returned',
    buckets=[1, 2, 3, 5, 8, 10, 15, 20]
)

class MetricsCollector:
    """Centralized metrics collection and QPS calculation"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)  # Keep last 1000 requests
        self.error_count = 0
        self.total_count = 0
        self.lock = threading.Lock()
        
        # Start background QPS calculation
        self._start_qps_calculation()
    
    def record_request(self, latency: float, is_error: bool = False):
        """Record a request for QPS calculation"""
        with self.lock:
            current_time = time.time()
            self.request_times.append(current_time)
            self.total_count += 1
            
            if is_error:
                self.error_count += 1
    
    def get_qps(self, window_seconds: int = 60) -> float:
        """Calculate QPS over the specified window"""
        with self.lock:
            if not self.request_times:
                return 0.0
                
            current_time = time.time()
            cutoff_time = current_time - window_seconds
            
            # Count requests in the time window
            recent_requests = sum(1 for req_time in self.request_times if req_time > cutoff_time)
            return recent_requests / window_seconds
    
    def get_error_rate(self) -> float:
        """Calculate error rate percentage"""
        with self.lock:
            if self.total_count == 0:
                return 0.0
            return (self.error_count / self.total_count) * 100
    
    def _start_qps_calculation(self):
        """Start background QPS calculation thread"""
        def update_qps():
            while True:
                try:
                    qps = self.get_qps()
                    error_rate = self.get_error_rate()
                    
                    QPS_GAUGE.set(qps)
                    ERROR_RATE.set(error_rate)
                    
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    secure_logger.log_error("metrics_collector", "QPSCalculationError", str(e))
                    time.sleep(10)
        
        thread = threading.Thread(target=update_qps, daemon=True)
        thread.start()

# Global metrics collector
metrics_collector = MetricsCollector()

class MonitoringMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for comprehensive monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.medical_endpoints = {'/qa', '/hybrid-search', '/health'}
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with monitoring"""
        start_time = time.time()
        session_id = None
        
        # Extract client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        try:
            # Log incoming request for medical endpoints
            if request.url.path in self.medical_endpoints:
                if request.method == "POST" and request.url.path == "/qa":
                    session_id = await self._log_qa_request(request, client_ip, user_agent)
                else:
                    session_id = secure_logger.log_query(
                        f"{request.method} {request.url.path}",
                        use_hybrid_search=False,
                        user_ip=client_ip,
                        user_agent=user_agent
                    )
            
            # Process request
            response = await call_next(request)
            
            # Calculate latency
            end_time = time.time()
            latency = end_time - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(latency)
            
            # Record in metrics collector
            is_error = response.status_code >= 400
            metrics_collector.record_request(latency, is_error)
            
            # Log response for medical endpoints
            if session_id:
                secure_logger.log_response(
                    session_id,
                    latency * 1000,  # Convert to milliseconds
                    success=not is_error,
                    error_type=f"HTTP_{response.status_code}" if is_error else None
                )
            
            # Add monitoring headers
            response.headers["X-Response-Time"] = f"{latency:.3f}s"
            response.headers["X-Session-ID"] = session_id or "N/A"
            
            return response
            
        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            
            # Record error metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            metrics_collector.record_request(latency, is_error=True)
            
            # Log error
            if session_id:
                secure_logger.log_error(session_id, type(e).__name__, str(e))
                secure_logger.log_response(
                    session_id,
                    latency * 1000,
                    success=False,
                    error_type=type(e).__name__
                )
            
            raise
        finally:
            ACTIVE_REQUESTS.dec()
    
    async def _log_qa_request(self, request: Request, client_ip: str, user_agent: str) -> str:
        """Log QA request details"""
        try:
            # Read request body
            body = await request.body()
            if body:
                data = json.loads(body)
                query = data.get("question", "")
                use_hybrid_search = data.get("use_hybrid_search", False)
                
                return secure_logger.log_query(
                    query,
                    use_hybrid_search,
                    client_ip,
                    user_agent
                )
        except Exception as e:
            secure_logger.log_error("middleware", "RequestLoggingError", str(e))
        
        return secure_logger.log_query(
            "Unknown query",
            False,
            client_ip,
            user_agent
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"

class MedicalMetricsLogger:
    """Logger for medical-specific metrics"""
    
    @staticmethod
    def log_retrieval_metrics(session_id: str, chunk_ids: list, scores: list, 
                            method: str, latency_seconds: float):
        """Log retrieval-specific metrics"""
        secure_logger.log_retrieval(session_id, chunk_ids, scores, method, latency_seconds * 1000)
        
        RETRIEVAL_LATENCY.observe(latency_seconds)
        SOURCE_COUNT.observe(len(chunk_ids))
    
    @staticmethod 
    def log_llm_metrics(session_id: str, model_name: str, response: str,
                       latency_seconds: float, confidence: Optional[float] = None):
        """Log LLM-specific metrics"""
        secure_logger.log_llm_interaction(
            session_id, model_name, response, 
            latency_ms=latency_seconds * 1000
        )
        
        LLM_LATENCY.observe(latency_seconds)
        
        if confidence is not None:
            CONFIDENCE_SCORE.observe(confidence)
    
    @staticmethod
    def log_hallucination_flag(session_id: str, flagged: bool, confidence: float,
                              review_needed: bool = False):
        """Log hallucination detection"""
        if flagged:
            HALLUCINATION_FLAGS.inc()
        
        secure_logger.log_response(
            session_id, 0, True,  # Latency will be updated elsewhere
            confidence_score=confidence,
            hallucination_flag=flagged,
            human_review_flag=review_needed
        )

def setup_monitoring(app: FastAPI):
    """Setup monitoring middleware and endpoints"""
    
    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    @app.get("/monitoring/health")
    async def monitoring_health():
        """Monitoring system health check"""
        metrics = secure_logger.get_current_metrics()
        qps = metrics_collector.get_qps()
        error_rate = metrics_collector.get_error_rate()
        
        return {
            "status": "healthy",
            "metrics": {
                **metrics,
                "current_qps": qps,
                "error_rate_percent": error_rate
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.get("/monitoring/dashboard-data")
    async def get_dashboard_data():
        """Get data for monitoring dashboard"""
        metrics = secure_logger.get_current_metrics()
        
        return {
            "current_metrics": {
                **metrics,
                "qps": metrics_collector.get_qps(),
                "error_rate": metrics_collector.get_error_rate()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Export key components
__all__ = [
    'MonitoringMiddleware',
    'MedicalMetricsLogger', 
    'setup_monitoring',
    'metrics_collector'
]