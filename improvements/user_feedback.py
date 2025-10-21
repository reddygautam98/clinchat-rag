"""
User Feedback Loop System for ClinChat-RAG
Implements thumbs up/down feedback collection and retraining data pipeline
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from pathlib import Path

@dataclass
class FeedbackEntry:
    """Individual user feedback entry"""
    feedback_id: str
    session_id: str
    user_id: Optional[str]
    query: str
    response: str
    sources: List[Dict[str, Any]]
    
    # Feedback data
    feedback_type: str  # "thumbs_up", "thumbs_down", "detailed"
    rating: int  # 1-5 scale
    feedback_text: Optional[str]
    
    # Context data
    response_time: float
    retrieval_count: int
    rerank_score: Optional[float]
    
    # Metadata
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    # Analysis flags
    is_medical_critical: bool = False
    requires_review: bool = False
    is_processed: bool = False

@dataclass
class FeedbackAnalytics:
    """Aggregated feedback analytics"""
    total_feedback: int
    positive_feedback: int
    negative_feedback: int
    average_rating: float
    
    # Time-based metrics
    feedback_last_24h: int
    feedback_last_week: int
    feedback_last_month: int
    
    # Quality metrics
    critical_issues: int
    pending_review: int
    processing_rate: float
    
    # User engagement
    unique_users: int
    repeat_users: int
    session_count: int

class FeedbackType(Enum):
    """Types of user feedback"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    DETAILED = "detailed"
    RATING_ONLY = "rating_only"
    CORRECTION = "correction"

class FeedbackSeverity(Enum):
    """Severity levels for negative feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeedbackDatabase:
    """SQLite database for storing user feedback"""
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize feedback database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        user_id TEXT,
                        query TEXT NOT NULL,
                        response TEXT NOT NULL,
                        sources TEXT NOT NULL,  -- JSON
                        feedback_type TEXT NOT NULL,
                        rating INTEGER,
                        feedback_text TEXT,
                        response_time REAL,
                        retrieval_count INTEGER,
                        rerank_score REAL,
                        timestamp REAL NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        is_medical_critical BOOLEAN DEFAULT FALSE,
                        requires_review BOOLEAN DEFAULT FALSE,
                        is_processed BOOLEAN DEFAULT FALSE,
                        severity TEXT DEFAULT 'low',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_analysis (
                        analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feedback_id TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analysis_result TEXT NOT NULL,  -- JSON
                        confidence_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (feedback_id) REFERENCES feedback (feedback_id)
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS retraining_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feedback_id TEXT NOT NULL,
                        query TEXT NOT NULL,
                        positive_docs TEXT,  -- JSON list of good documents
                        negative_docs TEXT,  -- JSON list of bad documents
                        corrected_response TEXT,
                        training_weight REAL DEFAULT 1.0,
                        is_used BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (feedback_id) REFERENCES feedback (feedback_id)
                    )
                """)
                
                # Create indices for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_processed ON feedback(is_processed)")
                
                self.logger.info("Initialized feedback database")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize feedback database: {e}")
            raise
    
    def store_feedback(self, feedback: FeedbackEntry) -> bool:
        """Store user feedback in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO feedback VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    feedback.feedback_id,
                    feedback.session_id,
                    feedback.user_id,
                    feedback.query,
                    feedback.response,
                    json.dumps(feedback.sources),
                    feedback.feedback_type,
                    feedback.rating,
                    feedback.feedback_text,
                    feedback.response_time,
                    feedback.retrieval_count,
                    feedback.rerank_score,
                    feedback.timestamp.timestamp(),
                    feedback.ip_address,
                    feedback.user_agent,
                    feedback.is_medical_critical,
                    feedback.requires_review,
                    feedback.is_processed,
                    self._determine_severity(feedback).value
                ))
                
                self.logger.info(f"Stored feedback: {feedback.feedback_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store feedback: {e}")
            return False
    
    def _determine_severity(self, feedback: FeedbackEntry) -> FeedbackSeverity:
        """Determine severity level of feedback"""
        # Critical medical keywords
        critical_keywords = [
            'dosage', 'contraindication', 'interaction', 'allergy', 'toxicity',
            'emergency', 'fatal', 'death', 'severe', 'adverse reaction'
        ]
        
        # High severity keywords
        high_keywords = [
            'incorrect', 'wrong', 'dangerous', 'misleading', 'harmful',
            'side effect', 'warning', 'caution', 'risk'
        ]
        
        if feedback.feedback_type == FeedbackType.THUMBS_DOWN.value:
            query_text = feedback.query.lower()
            feedback_text = (feedback.feedback_text or "").lower()
            
            if any(keyword in query_text or keyword in feedback_text 
                   for keyword in critical_keywords):
                return FeedbackSeverity.CRITICAL
            elif any(keyword in query_text or keyword in feedback_text 
                     for keyword in high_keywords):
                return FeedbackSeverity.HIGH
            elif feedback.rating and feedback.rating <= 2:
                return FeedbackSeverity.MEDIUM
            else:
                return FeedbackSeverity.LOW
        
        return FeedbackSeverity.LOW
    
    def get_feedback_analytics(self, days: int = 30) -> FeedbackAnalytics:
        """Get aggregated feedback analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Time boundaries
                now = time.time()
                day_ago = now - 86400
                week_ago = now - (7 * 86400)
                month_ago = now - (30 * 86400)
                period_ago = now - (days * 86400)
                
                # Total feedback
                cursor.execute(
                    "SELECT COUNT(*) FROM feedback WHERE timestamp >= ?",
                    (period_ago,)
                )
                total_feedback = cursor.fetchone()[0]
                
                # Positive/negative feedback
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN feedback_type = 'thumbs_up' OR rating >= 4 THEN 1 ELSE 0 END),
                        SUM(CASE WHEN feedback_type = 'thumbs_down' OR rating <= 2 THEN 1 ELSE 0 END)
                    FROM feedback WHERE timestamp >= ?
                """, (period_ago,))
                
                positive, negative = cursor.fetchone()
                positive = positive or 0
                negative = negative or 0
                
                # Average rating
                cursor.execute(
                    "SELECT AVG(rating) FROM feedback WHERE rating IS NOT NULL AND timestamp >= ?",
                    (period_ago,)
                )
                avg_rating = cursor.fetchone()[0] or 0.0
                
                # Time-based metrics
                cursor.execute("SELECT COUNT(*) FROM feedback WHERE timestamp >= ?", (day_ago,))
                feedback_24h = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM feedback WHERE timestamp >= ?", (week_ago,))
                feedback_week = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM feedback WHERE timestamp >= ?", (month_ago,))
                feedback_month = cursor.fetchone()[0]
                
                # Quality metrics
                cursor.execute(
                    "SELECT COUNT(*) FROM feedback WHERE is_medical_critical = 1 AND timestamp >= ?",
                    (period_ago,)
                )
                critical_issues = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT COUNT(*) FROM feedback WHERE requires_review = 1 AND timestamp >= ?",
                    (period_ago,)
                )
                pending_review = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT COUNT(*) FROM feedback WHERE is_processed = 1 AND timestamp >= ?",
                    (period_ago,)
                )
                processed = cursor.fetchone()[0]
                processing_rate = (processed / total_feedback * 100) if total_feedback > 0 else 0
                
                # User engagement
                cursor.execute(
                    "SELECT COUNT(DISTINCT user_id) FROM feedback WHERE user_id IS NOT NULL AND timestamp >= ?",
                    (period_ago,)
                )
                unique_users = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT user_id FROM feedback 
                        WHERE user_id IS NOT NULL AND timestamp >= ?
                        GROUP BY user_id 
                        HAVING COUNT(*) > 1
                    )
                """, (period_ago,))
                repeat_users = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT COUNT(DISTINCT session_id) FROM feedback WHERE timestamp >= ?",
                    (period_ago,)
                )
                session_count = cursor.fetchone()[0]
                
                return FeedbackAnalytics(
                    total_feedback=total_feedback,
                    positive_feedback=positive,
                    negative_feedback=negative,
                    average_rating=round(avg_rating, 2),
                    feedback_last_24h=feedback_24h,
                    feedback_last_week=feedback_week,
                    feedback_last_month=feedback_month,
                    critical_issues=critical_issues,
                    pending_review=pending_review,
                    processing_rate=round(processing_rate, 2),
                    unique_users=unique_users,
                    repeat_users=repeat_users,
                    session_count=session_count
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get feedback analytics: {e}")
            return FeedbackAnalytics(0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0.0, 0, 0, 0)

class FeedbackProcessor:
    """Processes user feedback for insights and retraining data"""
    
    def __init__(self, db: FeedbackDatabase):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def process_negative_feedback(self, feedback_id: str) -> Dict[str, Any]:
        """Process negative feedback to extract improvement insights"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get feedback details
                cursor.execute("""
                    SELECT query, response, sources, feedback_text, rating
                    FROM feedback WHERE feedback_id = ?
                """, (feedback_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {"error": "Feedback not found"}
                
                query, response, sources_json, feedback_text, rating = result
                sources = json.loads(sources_json)
                
                # Analyze feedback
                analysis = {
                    "feedback_id": feedback_id,
                    "issues_identified": self._identify_issues(query, response, feedback_text, rating),
                    "source_relevance": self._analyze_source_relevance(sources, query),
                    "response_quality": self._analyze_response_quality(response, query),
                    "suggested_improvements": self._suggest_improvements(query, response, feedback_text),
                    "retraining_value": self._assess_retraining_value(query, response, sources, feedback_text)
                }
                
                # Store analysis
                cursor.execute("""
                    INSERT INTO feedback_analysis 
                    (feedback_id, analysis_type, analysis_result, confidence_score)
                    VALUES (?, ?, ?, ?)
                """, (
                    feedback_id,
                    "negative_feedback_analysis",
                    json.dumps(analysis),
                    analysis.get("retraining_value", 0.5)
                ))
                
                # Mark as processed
                cursor.execute(
                    "UPDATE feedback SET is_processed = 1 WHERE feedback_id = ?",
                    (feedback_id,)
                )
                
                conn.commit()
                return analysis
                
        except Exception as e:
            self.logger.error(f"Failed to process negative feedback: {e}")
            return {"error": str(e)}
    
    def _identify_issues(self, query: str, response: str, feedback_text: Optional[str], rating: Optional[int]) -> List[str]:
        """Identify specific issues from feedback"""
        issues = []
        
        if rating and rating <= 2:
            issues.append("low_user_rating")
        
        if feedback_text:
            feedback_lower = feedback_text.lower()
            
            if any(word in feedback_lower for word in ["incorrect", "wrong", "inaccurate"]):
                issues.append("factual_error")
            
            if any(word in feedback_lower for word in ["incomplete", "missing", "partial"]):
                issues.append("incomplete_information")
            
            if any(word in feedback_lower for word in ["confusing", "unclear", "complex"]):
                issues.append("clarity_issues")
            
            if any(word in feedback_lower for word in ["irrelevant", "off-topic", "unrelated"]):
                issues.append("relevance_issues")
            
            if any(word in feedback_lower for word in ["outdated", "old", "obsolete"]):
                issues.append("outdated_information")
        
        # Check response quality indicators
        if len(response) < 50:
            issues.append("response_too_short")
        elif len(response) > 2000:
            issues.append("response_too_long")
        
        return issues
    
    def _analyze_source_relevance(self, sources: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Analyze relevance of retrieved sources"""
        if not sources:
            return {"relevance_score": 0.0, "issues": ["no_sources"]}
        
        # Simple relevance analysis based on source metadata
        total_sources = len(sources)
        high_relevance = sum(1 for source in sources if source.get("score", 0) > 0.8)
        medium_relevance = sum(1 for source in sources if 0.5 <= source.get("score", 0) <= 0.8)
        
        relevance_score = (high_relevance * 1.0 + medium_relevance * 0.6) / total_sources
        
        issues = []
        if relevance_score < 0.3:
            issues.append("low_source_relevance")
        if high_relevance == 0:
            issues.append("no_high_relevance_sources")
        if total_sources < 3:
            issues.append("insufficient_sources")
        
        return {
            "relevance_score": round(relevance_score, 2),
            "total_sources": total_sources,
            "high_relevance_count": high_relevance,
            "medium_relevance_count": medium_relevance,
            "issues": issues
        }
    
    def _analyze_response_quality(self, response: str, query: str) -> Dict[str, Any]:
        """Analyze quality of generated response"""
        quality_metrics = {
            "length": len(response),
            "has_medical_terms": self._contains_medical_terms(response),
            "has_citations": "[" in response and "]" in response,
            "has_disclaimers": any(word in response.lower() for word in ["consult", "doctor", "physician", "medical professional"]),
            "sentence_count": len([s for s in response.split('.') if s.strip()]),
            "readability_score": self._estimate_readability(response)
        }
        
        # Calculate overall quality score
        quality_score = 0.0
        if 100 <= quality_metrics["length"] <= 1500:
            quality_score += 0.2
        if quality_metrics["has_medical_terms"]:
            quality_score += 0.2
        if quality_metrics["has_citations"]:
            quality_score += 0.2
        if quality_metrics["has_disclaimers"]:
            quality_score += 0.2
        if quality_metrics["readability_score"] > 0.5:
            quality_score += 0.2
        
        return {
            "quality_score": round(quality_score, 2),
            "metrics": quality_metrics
        }
    
    def _contains_medical_terms(self, text: str) -> bool:
        """Check if text contains medical terminology"""
        medical_terms = [
            "patient", "treatment", "diagnosis", "medication", "drug", "dose",
            "clinical", "therapy", "disease", "condition", "symptom", "adverse"
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in medical_terms)
    
    def _estimate_readability(self, text: str) -> float:
        """Simple readability estimation"""
        sentences = [s for s in text.split('.') if s.strip()]
        if not sentences:
            return 0.0
        
        words = text.split()
        avg_sentence_length = len(words) / len(sentences)
        
        # Simple scoring: prefer moderate sentence length
        if 10 <= avg_sentence_length <= 20:
            return 0.8
        elif 8 <= avg_sentence_length <= 25:
            return 0.6
        else:
            return 0.3
    
    def _suggest_improvements(self, query: str, response: str, feedback_text: Optional[str]) -> List[str]:
        """Suggest specific improvements based on feedback"""
        suggestions = []
        
        if feedback_text:
            feedback_lower = feedback_text.lower()
            
            if "more detail" in feedback_lower or "incomplete" in feedback_lower:
                suggestions.append("add_more_comprehensive_information")
            
            if "simpler" in feedback_lower or "complex" in feedback_lower:
                suggestions.append("simplify_language_and_explanations")
            
            if "source" in feedback_lower or "reference" in feedback_lower:
                suggestions.append("improve_source_citations")
            
            if "recent" in feedback_lower or "updated" in feedback_lower:
                suggestions.append("use_more_recent_sources")
        
        # Response-based suggestions
        if len(response) < 100:
            suggestions.append("provide_more_detailed_response")
        
        if not any(word in response.lower() for word in ["consult", "doctor", "physician"]):
            suggestions.append("add_medical_disclaimer")
        
        return suggestions
    
    def _assess_retraining_value(self, query: str, response: str, sources: List[Dict], feedback_text: Optional[str]) -> float:
        """Assess the value of this feedback for model retraining"""
        value = 0.0
        
        # High value if specific corrections provided
        if feedback_text and any(word in feedback_text.lower() for word in ["should be", "correct answer", "actually"]):
            value += 0.4
        
        # Value based on query specificity
        if len(query.split()) > 5:  # Specific queries are more valuable
            value += 0.2
        
        # Value based on source quality
        if sources and any(source.get("score", 0) > 0.8 for source in sources):
            value += 0.2
        
        # Value based on medical criticality
        medical_keywords = ["dosage", "drug", "treatment", "diagnosis", "contraindication"]
        if any(keyword in query.lower() for keyword in medical_keywords):
            value += 0.2
        
        return min(value, 1.0)

class FeedbackManager:
    """Main manager for user feedback collection and processing"""
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db = FeedbackDatabase(db_path)
        self.processor = FeedbackProcessor(self.db)
        self.logger = logging.getLogger(__name__)
    
    async def collect_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Collect user feedback and return feedback ID"""
        try:
            # Generate feedback ID
            feedback_id = f"fb_{int(time.time() * 1000)}_{hash(feedback_data.get('query', '')) % 10000}"
            
            # Create feedback entry
            feedback = FeedbackEntry(
                feedback_id=feedback_id,
                session_id=feedback_data.get("session_id", "unknown"),
                user_id=feedback_data.get("user_id"),
                query=feedback_data["query"],
                response=feedback_data["response"],
                sources=feedback_data.get("sources", []),
                feedback_type=feedback_data["feedback_type"],
                rating=feedback_data.get("rating"),
                feedback_text=feedback_data.get("feedback_text"),
                response_time=feedback_data.get("response_time", 0.0),
                retrieval_count=feedback_data.get("retrieval_count", 0),
                rerank_score=feedback_data.get("rerank_score"),
                timestamp=datetime.now(),
                ip_address=feedback_data.get("ip_address"),
                user_agent=feedback_data.get("user_agent"),
                is_medical_critical=self._is_medical_critical(feedback_data),
                requires_review=self._requires_review(feedback_data)
            )
            
            # Store feedback
            if self.db.store_feedback(feedback):
                self.logger.info(f"Collected feedback: {feedback_id}")
                
                # Process negative feedback immediately
                if feedback.feedback_type in [FeedbackType.THUMBS_DOWN.value, "negative"] or \
                   (feedback.rating and feedback.rating <= 2):
                    await self.processor.process_negative_feedback(feedback_id)
                
                return feedback_id
            else:
                raise Exception("Failed to store feedback")
                
        except Exception as e:
            self.logger.error(f"Failed to collect feedback: {e}")
            raise
    
    def _is_medical_critical(self, feedback_data: Dict[str, Any]) -> bool:
        """Determine if feedback relates to medical-critical content"""
        critical_keywords = [
            "dosage", "dose", "contraindication", "interaction", "allergy",
            "emergency", "fatal", "death", "toxicity", "adverse reaction",
            "side effect", "warning", "danger"
        ]
        
        query = feedback_data.get("query", "").lower()
        feedback_text = feedback_data.get("feedback_text", "").lower()
        
        return any(keyword in query or keyword in feedback_text for keyword in critical_keywords)
    
    def _requires_review(self, feedback_data: Dict[str, Any]) -> bool:
        """Determine if feedback requires human review"""
        # Always review negative feedback on medical-critical content
        if self._is_medical_critical(feedback_data):
            return True
        
        # Review very low ratings
        if feedback_data.get("rating", 5) <= 2:
            return True
        
        # Review thumbs down with detailed text
        if (feedback_data.get("feedback_type") == FeedbackType.THUMBS_DOWN.value and 
            feedback_data.get("feedback_text")):
            return True
        
        return False
    
    def get_analytics(self, days: int = 30) -> FeedbackAnalytics:
        """Get feedback analytics for dashboard"""
        return self.db.get_feedback_analytics(days)
    
    async def get_retraining_candidates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get feedback entries suitable for model retraining"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Get high-value negative feedback with analysis
                cursor.execute("""
                    SELECT f.feedback_id, f.query, f.response, f.sources, f.feedback_text,
                           fa.analysis_result, fa.confidence_score
                    FROM feedback f
                    JOIN feedback_analysis fa ON f.feedback_id = fa.feedback_id
                    WHERE f.feedback_type IN ('thumbs_down', 'negative') 
                          AND fa.confidence_score > 0.6
                          AND f.is_processed = 1
                    ORDER BY fa.confidence_score DESC, f.timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                candidates = []
                for row in cursor.fetchall():
                    feedback_id, query, response, sources, feedback_text, analysis_json, confidence = row
                    
                    try:
                        analysis = json.loads(analysis_json)
                        candidates.append({
                            "feedback_id": feedback_id,
                            "query": query,
                            "response": response,
                            "sources": json.loads(sources),
                            "feedback_text": feedback_text,
                            "analysis": analysis,
                            "confidence": confidence
                        })
                    except json.JSONDecodeError:
                        continue
                
                return candidates
                
        except Exception as e:
            self.logger.error(f"Failed to get retraining candidates: {e}")
            return []

# Global feedback manager
feedback_manager = FeedbackManager()

# Export main components
__all__ = [
    'FeedbackManager',
    'FeedbackDatabase',
    'FeedbackProcessor',
    'FeedbackEntry',
    'FeedbackAnalytics',
    'FeedbackType',
    'FeedbackSeverity',
    'feedback_manager'
]