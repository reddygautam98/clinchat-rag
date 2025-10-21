"""
ClinChat-RAG Monitoring Integration
Integration of logging, monitoring, and hallucination detection with main application
"""

import time
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from monitoring.logger import secure_logger, start_metrics_collection
from monitoring.middleware import setup_monitoring, MedicalMetricsLogger
from monitoring.log_storage import log_storage
from monitoring.hallucination_detection import analyze_and_flag_response, human_review_system

class MonitoringIntegration:
    """Central monitoring integration for ClinChat-RAG"""
    
    def __init__(self):
        self.enabled = True
        self.metrics_thread = None
        
    def initialize(self, app: FastAPI):
        """Initialize monitoring for FastAPI application"""
        
        # Set up monitoring middleware and endpoints
        setup_monitoring(app)
        
        # Start background metrics collection
        self.metrics_thread = start_metrics_collection()
        
        # Add monitoring-specific endpoints
        self._add_monitoring_endpoints(app)
        
        print("✅ ClinChat-RAG monitoring system initialized")
    
    def _add_monitoring_endpoints(self, app: FastAPI):
        """Add monitoring and review endpoints"""
        
        @app.get("/monitoring/dashboard")
        async def serve_dashboard():
            """Serve the monitoring dashboard"""
            from pathlib import Path
            dashboard_path = Path("monitoring/dashboard/index.html")
            
            if dashboard_path.exists():
                with open(dashboard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HTMLResponse(content)
            else:
                return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)
        
        @app.get("/monitoring/dashboard-data")
        async def get_dashboard_data(hours: int = 24):
            """Get dashboard metrics data"""
            try:
                dashboard_metrics = log_storage.get_dashboard_metrics(hours)
                current_metrics = secure_logger.get_current_metrics()
                
                return {
                    "current_metrics": current_metrics,
                    "dashboard_metrics": dashboard_metrics,
                    "timestamp": time.time()
                }
            except Exception as e:
                secure_logger.log_error("dashboard", "DashboardDataError", str(e))
                return JSONResponse(
                    {"error": "Failed to fetch dashboard data", "details": str(e)},
                    status_code=500
                )
        
        @app.get("/monitoring/review-queue")
        async def get_review_queue(reviewer_id: str = "default", limit: int = 10):
            """Get human review queue"""
            try:
                queue = human_review_system.get_review_queue(reviewer_id, limit)
                stats = human_review_system.get_review_stats()
                
                return {
                    "queue": queue,
                    "stats": stats,
                    "reviewer_id": reviewer_id
                }
            except Exception as e:
                secure_logger.log_error("review_system", "ReviewQueueError", str(e))
                return JSONResponse(
                    {"error": "Failed to fetch review queue", "details": str(e)},
                    status_code=500
                )
        
        @app.post("/monitoring/submit-review")
        async def submit_review(
            review_id: int,
            reviewer_id: str,
            approved: bool,
            notes: str = "",
            correction_needed: bool = False,
            corrected_answer: str = ""
        ):
            """Submit human review decision"""
            try:
                success = human_review_system.submit_review(
                    review_id, reviewer_id, approved, notes, 
                    correction_needed, corrected_answer
                )
                
                return {
                    "success": success,
                    "review_id": review_id,
                    "reviewer_id": reviewer_id
                }
            except Exception as e:
                secure_logger.log_error("review_system", "ReviewSubmissionError", str(e))
                return JSONResponse(
                    {"error": "Failed to submit review", "details": str(e)},
                    status_code=500
                )
        
        @app.get("/monitoring/logs/export")
        async def export_logs(format: str = "json", hours: int = 24):
            """Export logs for analysis"""
            try:
                if format.lower() == "backup":
                    backup_path = log_storage.create_backup()
                    return {"backup_path": str(backup_path), "format": "tar.gz"}
                else:
                    metrics = log_storage.get_dashboard_metrics(hours)
                    return metrics
            except Exception as e:
                secure_logger.log_error("log_export", "ExportError", str(e))
                return JSONResponse(
                    {"error": "Failed to export logs", "details": str(e)},
                    status_code=500
                )

def log_qa_interaction(session_id: str, question: str, answer: str, 
                      sources: List[Dict[str, Any]], retrieval_latency: float,
                      llm_latency: float, total_latency: float, 
                      confidence: Optional[float] = None) -> Optional[int]:
    """
    Comprehensive logging of QA interaction with hallucination detection
    
    Returns review_id if flagged for human review, None otherwise
    """
    
    try:
        # Log retrieval metrics
        chunk_ids = [source.get('doc_id', f'chunk_{i}') for i, source in enumerate(sources)]
        scores = [source.get('score', 0.0) for source in sources]
        
        MedicalMetricsLogger.log_retrieval_metrics(
            session_id, chunk_ids, scores, 
            "hybrid_search", retrieval_latency
        )
        
        # Log LLM metrics  
        MedicalMetricsLogger.log_llm_metrics(
            session_id, "groq_llama3", answer,
            llm_latency, confidence
        )
        
        # Analyze for hallucinations and submit for review if needed
        review_id = analyze_and_flag_response(
            session_id, question, answer, sources, confidence
        )
        
        # Log final response metrics
        secure_logger.log_response(
            session_id, total_latency * 1000, True,
            confidence_score=confidence,
            source_count=len(sources),
            hallucination_flag=review_id is not None,
            human_review_flag=review_id is not None
        )
        
        return review_id
        
    except Exception as e:
        secure_logger.log_error(session_id, "QALoggingError", str(e))
        return None

def create_monitoring_lifespan():
    """Create lifespan context manager for monitoring"""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        monitoring = MonitoringIntegration()
        monitoring.initialize(app)
        
        # Store monitoring instance for shutdown
        app.state.monitoring = monitoring
        
        yield
        
        # Shutdown
        if hasattr(app.state, 'monitoring'):
            print("🛑 Shutting down monitoring system")
    
    return lifespan

# Enhanced request logging decorator
def log_request_context():
    """Dependency to provide request logging context"""
    
    def get_request_context(request: Request):
        # Extract session info
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            # Create new session for this request
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            
            session_id = secure_logger.log_query(
                f"{request.method} {request.url.path}",
                use_hybrid_search=False,
                user_ip=client_ip,
                user_agent=user_agent
            )
        
        return {
            "session_id": session_id,
            "request": request,
            "start_time": time.time()
        }
    
    return get_request_context

# Monitoring configuration
MONITORING_CONFIG = {
    "enabled": True,
    "log_level": "INFO",
    "metrics_collection_interval": 60,  # seconds
    "dashboard_refresh_interval": 30,   # seconds
    "hallucination_detection": True,
    "human_review_required": True,
    "log_retention_days": 90,
    "backup_schedule": "weekly"
}

# Export main components
__all__ = [
    'MonitoringIntegration',
    'log_qa_interaction', 
    'create_monitoring_lifespan',
    'log_request_context',
    'MONITORING_CONFIG'
]