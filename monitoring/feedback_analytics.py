#!/usr/bin/env python3
"""
Performance Metrics and User Feedback System
Real-time monitoring and feedback collection for ClinChat-RAG
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sqlite3
import json
from pathlib import Path
import statistics
from enum import Enum

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of user feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    GENERAL_FEEDBACK = "general_feedback"
    TRAINING_FEEDBACK = "training_feedback"

class FeedbackPriority(Enum):
    """Feedback priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class UserFeedback:
    """User feedback record"""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    priority: FeedbackPriority
    title: str
    description: str
    category: str
    submitted_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale
    attachments: List[str] = None
    tags: List[str] = None

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    source: str
    context: Dict[str, Any] = None

@dataclass
class UserSession:
    """User session tracking"""
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    pages_visited: List[str] = None
    actions_performed: List[Dict[str, Any]] = None
    performance_issues: List[str] = None

class PerformanceDashboard:
    """Real-time performance monitoring dashboard"""
    
    def __init__(self, db_path: str = "monitoring/performance.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize performance monitoring database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                metric_id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                timestamp TIMESTAMP NOT NULL,
                source TEXT NOT NULL,
                context TEXT
            )
        """)
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                pages_visited TEXT,
                actions_performed TEXT,
                performance_issues TEXT
            )
        """)
        
        # Real-time alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_alerts (
                alert_id TEXT PRIMARY KEY,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                data TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_metric(self, metric: PerformanceMetric):
        """Record performance metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics 
            (metric_id, metric_name, value, unit, timestamp, source, context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.metric_id,
            metric.metric_name,
            metric.value,
            metric.unit,
            metric.timestamp,
            metric.source,
            json.dumps(metric.context) if metric.context else None
        ))
        
        conn.commit()
        conn.close()
        
        # Check for alerts
        self._check_performance_thresholds(metric)
    
    def _check_performance_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds thresholds and create alerts"""
        
        thresholds = {
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 5.0, "critical": 10.0},
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "memory_usage": {"warning": 85.0, "critical": 95.0}
        }
        
        if metric.metric_name in thresholds:
            threshold = thresholds[metric.metric_name]
            
            if metric.value >= threshold["critical"]:
                self._create_alert("critical", 
                                 f"Critical {metric.metric_name}: {metric.value}{metric.unit}",
                                 metric)
            elif metric.value >= threshold["warning"]:
                self._create_alert("warning",
                                 f"Warning {metric.metric_name}: {metric.value}{metric.unit}",
                                 metric)
    
    def _create_alert(self, severity: str, message: str, metric: PerformanceMetric):
        """Create performance alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        alert_id = f"alert_{datetime.now().isoformat()}_{metric.metric_name}"
        
        cursor.execute("""
            INSERT INTO performance_alerts
            (alert_id, alert_type, severity, message, created_at, data)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alert_id,
            "performance_threshold",
            severity,
            message,
            datetime.now(),
            json.dumps({
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "source": metric.source
            })
        ))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"Performance alert: {message}")
    
    def get_real_time_metrics(self, hours: int = 1) -> Dict[str, List[Dict]]:
        """Get real-time metrics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT metric_name, value, unit, timestamp, source
            FROM performance_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (since_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Group by metric name
        metrics_by_name = {}
        for row in rows:
            metric_name = row[0]
            if metric_name not in metrics_by_name:
                metrics_by_name[metric_name] = []
            
            metrics_by_name[metric_name].append({
                "value": row[1],
                "unit": row[2],
                "timestamp": row[3],
                "source": row[4]
            })
        
        return metrics_by_name
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(days=days)
        
        # Get response time statistics
        cursor.execute("""
            SELECT value FROM performance_metrics
            WHERE metric_name = 'response_time' AND timestamp >= ?
        """, (since_time,))
        
        response_times = [row[0] for row in cursor.fetchall()]
        
        # Get error rates
        cursor.execute("""
            SELECT AVG(value) FROM performance_metrics
            WHERE metric_name = 'error_rate' AND timestamp >= ?
        """, (since_time,))
        
        avg_error_rate = cursor.fetchone()[0] or 0
        
        # Get uptime
        cursor.execute("""
            SELECT COUNT(*) FROM performance_metrics
            WHERE metric_name = 'uptime' AND value > 0 AND timestamp >= ?
        """, (since_time,))
        
        uptime_count = cursor.fetchone()[0] or 0
        
        conn.close()
        
        summary = {
            "period_days": days,
            "response_time": {
                "avg": statistics.mean(response_times) if response_times else 0,
                "p50": statistics.median(response_times) if response_times else 0,
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
                "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0
            },
            "error_rate": avg_error_rate,
            "uptime_percentage": (uptime_count / (days * 24 * 4)) * 100,  # Assuming 15-min intervals
            "total_requests": len(response_times)
        }
        
        return summary

class FeedbackCollector:
    """Collects and manages user feedback"""
    
    def __init__(self, db_path: str = "monitoring/feedback.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize feedback database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                feedback_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                submitted_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                rating INTEGER,
                attachments TEXT,
                tags TEXT
            )
        """)
        
        # Feedback analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_analytics (
                date DATE,
                feedback_type TEXT,
                count INTEGER,
                avg_rating REAL,
                PRIMARY KEY (date, feedback_type)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def submit_feedback(self, feedback: UserFeedback) -> str:
        """Submit user feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_feedback
            (feedback_id, user_id, feedback_type, priority, title, description,
             category, submitted_at, rating, attachments, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.feedback_id,
            feedback.user_id,
            feedback.feedback_type.value,
            feedback.priority.value,
            feedback.title,
            feedback.description,
            feedback.category,
            feedback.submitted_at,
            feedback.rating,
            json.dumps(feedback.attachments) if feedback.attachments else None,
            json.dumps(feedback.tags) if feedback.tags else None
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Feedback submitted: {feedback.feedback_id}")
        return feedback.feedback_id
    
    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback summary and analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Total feedback count
        cursor.execute("""
            SELECT COUNT(*) FROM user_feedback
            WHERE submitted_at >= ?
        """, (since_date,))
        
        total_feedback = cursor.fetchone()[0]
        
        # Feedback by type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM user_feedback
            WHERE submitted_at >= ?
            GROUP BY feedback_type
        """, (since_date,))
        
        feedback_by_type = dict(cursor.fetchall())
        
        # Average rating
        cursor.execute("""
            SELECT AVG(rating)
            FROM user_feedback
            WHERE submitted_at >= ? AND rating IS NOT NULL
        """, (since_date,))
        
        avg_rating = cursor.fetchone()[0] or 0
        
        # Resolution rate
        cursor.execute("""
            SELECT COUNT(*) FROM user_feedback
            WHERE submitted_at >= ? AND resolved_at IS NOT NULL
        """, (since_date,))
        
        resolved_count = cursor.fetchone()[0]
        resolution_rate = (resolved_count / total_feedback * 100) if total_feedback > 0 else 0
        
        conn.close()
        
        return {
            "period_days": days,
            "total_feedback": total_feedback,
            "feedback_by_type": feedback_by_type,
            "average_rating": round(avg_rating, 2),
            "resolution_rate": round(resolution_rate, 1),
            "resolved_count": resolved_count
        }
    
    def generate_feedback_form_html(self) -> str:
        """Generate HTML feedback form"""
        
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ClinChat-RAG Feedback</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <div class="row justify-content-center">
                    <div class="col-md-8">
                        <h2>Feedback & Support</h2>
                        <p class="text-muted">Help us improve ClinChat-RAG by sharing your feedback</p>
                        
                        <form id="feedbackForm">
                            <div class="mb-3">
                                <label for="feedbackType" class="form-label">Feedback Type *</label>
                                <select class="form-select" id="feedbackType" name="feedback_type" required>
                                    <option value="">Select type...</option>
                                    <option value="bug_report">Bug Report</option>
                                    <option value="feature_request">Feature Request</option>
                                    <option value="usability_issue">Usability Issue</option>
                                    <option value="performance_issue">Performance Issue</option>
                                    <option value="training_feedback">Training Feedback</option>
                                    <option value="general_feedback">General Feedback</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label for="priority" class="form-label">Priority *</label>
                                <select class="form-select" id="priority" name="priority" required>
                                    <option value="">Select priority...</option>
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label for="title" class="form-label">Title *</label>
                                <input type="text" class="form-control" id="title" name="title" 
                                       placeholder="Brief description of the issue or suggestion" required>
                            </div>
                            
                            <div class="mb-3">
                                <label for="description" class="form-label">Description *</label>
                                <textarea class="form-control" id="description" name="description" rows="4"
                                         placeholder="Please provide detailed information..." required></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label for="category" class="form-label">Category</label>
                                <input type="text" class="form-control" id="category" name="category"
                                       placeholder="e.g., Patient Management, AI Chat, Reports">
                            </div>
                            
                            <div class="mb-3">
                                <label for="rating" class="form-label">Overall Experience Rating</label>
                                <div class="rating">
                                    <input type="radio" name="rating" value="5" id="star5">
                                    <label for="star5">★</label>
                                    <input type="radio" name="rating" value="4" id="star4">
                                    <label for="star4">★</label>
                                    <input type="radio" name="rating" value="3" id="star3">
                                    <label for="star3">★</label>
                                    <input type="radio" name="rating" value="2" id="star2">
                                    <label for="star2">★</label>
                                    <input type="radio" name="rating" value="1" id="star1">
                                    <label for="star1">★</label>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="attachments" class="form-label">Screenshots/Files</label>
                                <input type="file" class="form-control" id="attachments" name="attachments" 
                                       multiple accept=".png,.jpg,.jpeg,.pdf,.txt">
                                <small class="text-muted">Optional: Upload screenshots or relevant files</small>
                            </div>
                            
                            <div class="d-grid gap-2">
                                <button type="submit" class="btn btn-primary">Submit Feedback</button>
                                <button type="button" class="btn btn-outline-secondary" onclick="clearForm()">Clear Form</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            
            <style>
                .rating {
                    display: flex;
                    flex-direction: row-reverse;
                    justify-content: flex-end;
                }
                
                .rating input[type="radio"] {
                    display: none;
                }
                
                .rating label {
                    font-size: 2em;
                    color: #ddd;
                    cursor: pointer;
                    transition: color 0.2s;
                }
                
                .rating input[type="radio"]:checked ~ label,
                .rating label:hover,
                .rating label:hover ~ label {
                    color: #ffc107;
                }
            </style>
            
            <script>
                document.getElementById('feedbackForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const feedbackData = Object.fromEntries(formData.entries());
                    
                    // Add timestamp and generate ID
                    feedbackData.submitted_at = new Date().toISOString();
                    feedbackData.feedback_id = 'feedback_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                    
                    // Submit feedback
                    fetch('/api/feedback/submit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(feedbackData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Thank you for your feedback! Reference ID: ' + data.feedback_id);
                        clearForm();
                    })
                    .catch(error => {
                        alert('Error submitting feedback. Please try again.');
                        console.error('Error:', error);
                    });
                });
                
                function clearForm() {
                    document.getElementById('feedbackForm').reset();
                }
            </script>
        </body>
        </html>
        """

class UserAnalytics:
    """User behavior analytics and insights"""
    
    def __init__(self, db_path: str = "monitoring/analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User activity table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                activity_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                page TEXT,
                timestamp TIMESTAMP NOT NULL,
                session_id TEXT,
                data TEXT
            )
        """)
        
        # Daily usage statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                date DATE PRIMARY KEY,
                total_users INTEGER,
                total_sessions INTEGER,
                avg_session_duration REAL,
                page_views INTEGER,
                unique_pages INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def track_user_action(self, user_id: str, action: str, page: str = None,
                         session_id: str = None, data: Dict[str, Any] = None):
        """Track user action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        activity_id = f"activity_{datetime.now().isoformat()}_{user_id}"
        
        cursor.execute("""
            INSERT INTO user_activity
            (activity_id, user_id, action, page, timestamp, session_id, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_id,
            user_id,
            action,
            page,
            datetime.now(),
            session_id,
            json.dumps(data) if data else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Active users
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_activity
            WHERE timestamp >= ?
        """, (since_date,))
        
        active_users = cursor.fetchone()[0]
        
        # Most used features
        cursor.execute("""
            SELECT action, COUNT(*) as usage_count
            FROM user_activity
            WHERE timestamp >= ?
            GROUP BY action
            ORDER BY usage_count DESC
            LIMIT 10
        """, (since_date,))
        
        top_features = dict(cursor.fetchall())
        
        # Most visited pages
        cursor.execute("""
            SELECT page, COUNT(*) as page_views
            FROM user_activity
            WHERE timestamp >= ? AND page IS NOT NULL
            GROUP BY page
            ORDER BY page_views DESC
            LIMIT 10
        """, (since_date,))
        
        top_pages = dict(cursor.fetchall())
        
        # Daily activity trend
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as daily_users
            FROM user_activity
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (since_date,))
        
        daily_activity = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "period_days": days,
            "active_users": active_users,
            "top_features": top_features,
            "top_pages": top_pages,
            "daily_activity": daily_activity
        }

def create_monitoring_system():
    """Initialize complete monitoring and feedback system"""
    
    # Create monitoring directories
    Path("monitoring").mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    performance_dashboard = PerformanceDashboard()
    feedback_collector = FeedbackCollector()
    user_analytics = UserAnalytics()
    
    return {
        "performance": performance_dashboard,
        "feedback": feedback_collector,
        "analytics": user_analytics
    }

# Demo and example usage
def demo_monitoring_system():
    """Demonstrate the monitoring and feedback system"""
    
    print("📊 Creating ClinChat-RAG Monitoring System...")
    monitoring_system = create_monitoring_system()
    
    # Demo performance monitoring
    performance = monitoring_system["performance"]
    
    # Record sample metrics
    metrics = [
        PerformanceMetric("metric_1", "response_time", 0.5, "seconds", 
                         datetime.now(), "api_endpoint"),
        PerformanceMetric("metric_2", "error_rate", 2.1, "percent", 
                         datetime.now(), "system"),
        PerformanceMetric("metric_3", "cpu_usage", 45.2, "percent", 
                         datetime.now(), "server")
    ]
    
    for metric in metrics:
        performance.record_metric(metric)
    
    print("✅ Performance metrics recorded")
    
    # Demo feedback collection
    feedback = monitoring_system["feedback"]
    
    sample_feedback = UserFeedback(
        feedback_id="fb_001",
        user_id="dr_smith",
        feedback_type=FeedbackType.FEATURE_REQUEST,
        priority=FeedbackPriority.MEDIUM,
        title="Add voice input to chat",
        description="Would be great to have voice input for the AI chat feature",
        category="AI Chat",
        submitted_at=datetime.now(),
        rating=4
    )
    
    feedback.submit_feedback(sample_feedback)
    print("✅ Sample feedback submitted")
    
    # Generate feedback form
    feedback_form = feedback.generate_feedback_form_html()
    with open("monitoring/feedback_form.html", "w") as f:
        f.write(feedback_form)
    
    print("📝 Feedback form saved to: monitoring/feedback_form.html")
    
    # Demo analytics
    analytics = monitoring_system["analytics"]
    
    # Track sample user actions
    sample_actions = [
        ("dr_smith", "login", "dashboard"),
        ("dr_smith", "search_patient", "patients"),
        ("dr_smith", "ai_query", "chat"),
        ("nurse_jane", "login", "dashboard"),
        ("nurse_jane", "view_alerts", "alerts")
    ]
    
    for user_id, action, page in sample_actions:
        analytics.track_user_action(user_id, action, page)
    
    print("📈 User analytics recorded")
    
    # Get performance summary
    perf_summary = performance.get_performance_summary(days=1)
    feedback_summary = feedback.get_feedback_summary(days=1)
    usage_analytics = analytics.get_usage_analytics(days=1)
    
    print("\n📊 MONITORING SUMMARY:")
    print(f"   Performance: {perf_summary['total_requests']} requests tracked")
    print(f"   Feedback: {feedback_summary['total_feedback']} submissions")
    print(f"   Users: {usage_analytics['active_users']} active users")
    
    print("\n✅ Monitoring system demonstration complete!")

if __name__ == "__main__":
    demo_monitoring_system()