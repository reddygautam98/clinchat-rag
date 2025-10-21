"""
ClinChat-RAG Hallucination Detection & Human Review System
Automated detection of potential hallucinations with human review integration
"""

import re
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import threading
from collections import defaultdict

from monitoring.logger import secure_logger

@dataclass
class HallucinationFlag:
    """Structured hallucination flag"""
    session_id: str
    timestamp: datetime
    confidence_score: float
    flag_reasons: List[str]
    severity: str  # 'low', 'medium', 'high'
    review_status: str  # 'pending', 'reviewed', 'approved', 'rejected'
    reviewer_notes: Optional[str] = None
    auto_detected: bool = True

class HallucinationDetector:
    """Detect potential hallucinations in medical responses"""
    
    def __init__(self):
        self.medical_terms = self._load_medical_terms()
        self.contradiction_patterns = self._load_contradiction_patterns()
        self.confidence_thresholds = {
            'high_risk': 0.3,     # Below 30% confidence is high risk
            'medium_risk': 0.6,   # 30-60% is medium risk
            'low_risk': 0.8       # 60-80% is low risk
        }
        self.flag_history = defaultdict(list)
    
    def _load_medical_terms(self) -> Dict[str, List[str]]:
        """Load medical terminology for validation"""
        return {
            'drugs': [
                'metformin', 'warfarin', 'aspirin', 'lisinopril', 'atorvastatin',
                'amlodipine', 'levothyroxine', 'omeprazole', 'simvastatin', 'losartan'
            ],
            'conditions': [
                'diabetes', 'hypertension', 'myocardial infarction', 'stroke', 'copd',
                'pneumonia', 'sepsis', 'heart failure', 'atrial fibrillation', 'asthma'
            ],
            'procedures': [
                'echocardiogram', 'ct scan', 'mri', 'x-ray', 'ekg', 'blood test',
                'biopsy', 'endoscopy', 'catheterization', 'ultrasound'
            ],
            'contraindications': [
                'contraindicated', 'contraindication', 'avoid', 'do not use',
                'not recommended', 'prohibited', 'forbidden'
            ]
        }
    
    def _load_contradiction_patterns(self) -> List[Dict[str, Any]]:
        """Load patterns that indicate potential contradictions"""
        return [
            {
                'pattern': r'safe.*dangerous|dangerous.*safe',
                'description': 'Contradictory safety statements',
                'severity': 'high'
            },
            {
                'pattern': r'increase.*decrease|decrease.*increase',
                'description': 'Contradictory directional statements',
                'severity': 'medium'
            },
            {
                'pattern': r'contraindicated.*recommended|recommended.*contraindicated',
                'description': 'Contradictory recommendations',
                'severity': 'high'
            },
            {
                'pattern': r'effective.*ineffective|ineffective.*effective',
                'description': 'Contradictory effectiveness claims',
                'severity': 'medium'
            }
        ]
    
    def analyze_response(self, session_id: str, question: str, answer: str, 
                        sources: List[Dict], confidence: Optional[float] = None) -> HallucinationFlag:
        """Analyze response for potential hallucinations"""
        
        flag_reasons = []
        severity = 'low'
        
        # 1. Confidence-based detection
        if confidence is not None:
            confidence_flags = self._check_confidence_levels(confidence)
            flag_reasons.extend(confidence_flags)
            
            if confidence < self.confidence_thresholds['high_risk']:
                severity = 'high'
            elif confidence < self.confidence_thresholds['medium_risk']:
                severity = 'medium'
        
        # 2. Source consistency check
        source_flags = self._check_source_consistency(answer, sources)
        flag_reasons.extend(source_flags)
        
        # 3. Medical contradiction detection
        contradiction_flags = self._check_contradictions(answer)
        flag_reasons.extend(contradiction_flags)
        if contradiction_flags:
            severity = max(severity, 'high', key=lambda x: ['low', 'medium', 'high'].index(x))
        
        # 4. Medical term validation
        term_flags = self._validate_medical_terms(answer)
        flag_reasons.extend(term_flags)
        
        # 5. Temporal consistency (dosage, timing)
        temporal_flags = self._check_temporal_consistency(answer)
        flag_reasons.extend(temporal_flags)
        
        # 6. Factual claim verification
        factual_flags = self._check_factual_claims(answer, question)
        flag_reasons.extend(factual_flags)
        
        # Create flag if issues detected
        if flag_reasons:
            flag = HallucinationFlag(
                session_id=session_id,
                timestamp=datetime.utcnow(),
                confidence_score=confidence or 0.5,
                flag_reasons=flag_reasons,
                severity=severity,
                review_status='pending',
                auto_detected=True
            )
            
            # Store flag
            self.flag_history[session_id].append(flag)
            return flag
        
        return None
    
    def _check_confidence_levels(self, confidence: float) -> List[str]:
        """Check confidence score thresholds"""
        flags = []
        
        if confidence < self.confidence_thresholds['high_risk']:
            flags.append(f'Very low confidence score: {confidence:.2f}')
        elif confidence < self.confidence_thresholds['medium_risk']:
            flags.append(f'Low confidence score: {confidence:.2f}')
        
        return flags
    
    def _check_source_consistency(self, answer: str, sources: List[Dict]) -> List[str]:
        """Check if answer is consistent with provided sources"""
        flags = []
        
        if not sources:
            flags.append('No supporting sources provided')
            return flags
        
        # Extract key medical terms from answer
        answer_terms = self._extract_medical_terms(answer.lower())
        
        # Check if key terms appear in sources
        source_content = ' '.join([
            source.get('content', '') + ' ' + source.get('snippet', '')
            for source in sources
        ]).lower()
        
        missing_terms = []
        for term in answer_terms:
            if term not in source_content:
                missing_terms.append(term)
        
        if len(missing_terms) > 2:  # Allow some variance
            flags.append(f'Answer contains terms not found in sources: {missing_terms[:3]}')
        
        # Check source relevance scores
        low_relevance_sources = [
            source for source in sources 
            if source.get('score', 1.0) < 0.5
        ]
        
        if len(low_relevance_sources) > len(sources) / 2:
            flags.append('Majority of sources have low relevance scores')
        
        return flags
    
    def _check_contradictions(self, answer: str) -> List[str]:
        """Check for internal contradictions in the answer"""
        flags = []
        
        for pattern_info in self.contradiction_patterns:
            if re.search(pattern_info['pattern'], answer.lower()):
                flags.append(f"Potential contradiction: {pattern_info['description']}")
        
        # Check for explicit contradictions
        contradiction_words = ['however', 'but', 'although', 'despite', 'contrary to']
        sentences = re.split(r'[.!?]+', answer)
        
        contradiction_count = 0
        for sentence in sentences:
            if any(word in sentence.lower() for word in contradiction_words):
                contradiction_count += 1
        
        if contradiction_count > 2:
            flags.append('Multiple contradictory statements detected')
        
        return flags
    
    def _validate_medical_terms(self, answer: str) -> List[str]:
        """Validate medical terminology usage"""
        flags = []
        
        # Check for common medical misspellings or incorrect usage
        problematic_patterns = [
            (r'dosage.*\d+.*times per day', 'Unclear dosage specification'),
            (r'take.*as needed.*daily', 'Contradictory dosage instructions'),
            (r'mg/kg.*adult', 'Pediatric dosing for adults'),
        ]
        
        for pattern, description in problematic_patterns:
            if re.search(pattern, answer.lower()):
                flags.append(f'Medical terminology issue: {description}')
        
        return flags
    
    def _check_temporal_consistency(self, answer: str) -> List[str]:
        """Check for temporal consistency in medical recommendations"""
        flags = []
        
        # Extract time-related information
        time_patterns = [
            r'(\d+)\s*(hour|day|week|month|year)s?',
            r'(daily|weekly|monthly|yearly)',
            r'(morning|afternoon|evening|night)',
            r'(before|after)\s*(meal|food|eating)'
        ]
        
        time_mentions = []
        for pattern in time_patterns:
            matches = re.findall(pattern, answer.lower())
            time_mentions.extend(matches)
        
        # Check for conflicting time instructions
        if len(set(time_mentions)) != len(time_mentions):
            flags.append('Conflicting temporal instructions detected')
        
        return flags
    
    def _check_factual_claims(self, answer: str, question: str) -> List[str]:
        """Check for potentially incorrect factual claims"""
        flags = []
        
        # Common medical fact patterns to verify
        suspicious_patterns = [
            (r'always.*safe', 'Absolute safety claims'),
            (r'never.*harmful', 'Absolute safety claims'),
            (r'100%.*effective', 'Absolute effectiveness claims'),
            (r'no.*side effects', 'Absolute safety claims'),
            (r'cures.*completely', 'Absolute cure claims')
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, answer.lower()):
                flags.append(f'Suspicious factual claim: {description}')
        
        # Check for unsupported numerical claims
        number_claims = re.findall(r'(\d+(?:\.\d+)?)%', answer)
        if len(number_claims) > 3:
            flags.append('Multiple unsupported statistical claims')
        
        return flags
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terms from text"""
        terms = []
        
        for category, term_list in self.medical_terms.items():
            for term in term_list:
                if term in text:
                    terms.append(term)
        
        return terms

class HumanReviewSystem:
    """System for human review of flagged responses"""
    
    def __init__(self):
        self.review_db_path = Path("logs/human_reviews.db")
        self._init_review_database()
        
    def _init_review_database(self):
        """Initialize human review database"""
        self.review_db_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.review_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS review_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources TEXT NOT NULL,
                    confidence_score REAL,
                    flag_reasons TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    reviewer_id TEXT,
                    review_timestamp TEXT,
                    reviewer_notes TEXT,
                    approved BOOLEAN,
                    correction_needed BOOLEAN DEFAULT FALSE,
                    corrected_answer TEXT,
                    priority INTEGER DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviewers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    expertise TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    reviews_completed INTEGER DEFAULT 0,
                    avg_review_time_minutes REAL DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_review_status ON review_queue (status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_review_priority ON review_queue (priority DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_review_timestamp ON review_queue (timestamp)
            ''')
            
            conn.commit()
    
    def submit_for_review(self, session_id: str, question: str, answer: str,
                         sources: List[Dict], flag: HallucinationFlag) -> int:
        """Submit a flagged response for human review"""
        
        priority = self._calculate_priority(flag)
        
        with sqlite3.connect(self.review_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO review_queue 
                (session_id, timestamp, question, answer, sources, confidence_score,
                 flag_reasons, severity, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                flag.timestamp.isoformat(),
                question,
                answer,
                json.dumps(sources),
                flag.confidence_score,
                json.dumps(flag.flag_reasons),
                flag.severity,
                priority
            ))
            
            review_id = cursor.lastrowid
            conn.commit()
        
        # Log the review submission
        secure_logger.log_security_event(
            session_id,
            'human_review_requested',
            details={
                'review_id': review_id,
                'severity': flag.severity,
                'reasons': flag.flag_reasons
            }
        )
        
        return review_id
    
    def _calculate_priority(self, flag: HallucinationFlag) -> int:
        """Calculate review priority (1=highest, 5=lowest)"""
        base_priority = {
            'high': 1,
            'medium': 3,
            'low': 4
        }.get(flag.severity, 5)
        
        # Increase priority for certain flag types
        high_priority_flags = [
            'contradictory safety statements',
            'contradictory recommendations',
            'absolute safety claims',
            'absolute cure claims'
        ]
        
        for reason in flag.flag_reasons:
            if any(priority_flag in reason.lower() for priority_flag in high_priority_flags):
                base_priority = max(1, base_priority - 1)
        
        return base_priority
    
    def get_review_queue(self, reviewer_id: str, limit: int = 10) -> List[Dict]:
        """Get pending reviews for a reviewer"""
        
        with sqlite3.connect(self.review_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, session_id, timestamp, question, answer, sources,
                       confidence_score, flag_reasons, severity, priority
                FROM review_queue 
                WHERE status = 'pending'
                ORDER BY priority ASC, timestamp ASC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            return [{
                'review_id': row[0],
                'session_id': row[1],
                'timestamp': row[2],
                'question': row[3],
                'answer': row[4],
                'sources': json.loads(row[5]),
                'confidence_score': row[6],
                'flag_reasons': json.loads(row[7]),
                'severity': row[8],
                'priority': row[9]
            } for row in rows]
    
    def submit_review(self, review_id: int, reviewer_id: str, approved: bool,
                     notes: str = "", correction_needed: bool = False,
                     corrected_answer: str = "") -> bool:
        """Submit human review decision"""
        
        try:
            with sqlite3.connect(self.review_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE review_queue 
                    SET status = 'reviewed', reviewer_id = ?, review_timestamp = ?,
                        reviewer_notes = ?, approved = ?, correction_needed = ?,
                        corrected_answer = ?
                    WHERE id = ?
                ''', (
                    reviewer_id,
                    datetime.utcnow().isoformat(),
                    notes,
                    approved,
                    correction_needed,
                    corrected_answer,
                    review_id
                ))
                
                # Update reviewer statistics
                cursor.execute('''
                    UPDATE reviewers 
                    SET reviews_completed = reviews_completed + 1
                    WHERE id = ?
                ''', (reviewer_id,))
                
                conn.commit()
                
                # Log the review completion
                cursor.execute('SELECT session_id FROM review_queue WHERE id = ?', (review_id,))
                session_id = cursor.fetchone()[0]
                
                secure_logger.log_security_event(
                    session_id,
                    'human_review_completed',
                    details={
                        'review_id': review_id,
                        'reviewer_id': reviewer_id,
                        'approved': approved,
                        'correction_needed': correction_needed
                    }
                )
                
                return True
                
        except Exception as e:
            secure_logger.log_error("review_system", "ReviewSubmissionError", str(e))
            return False
    
    def get_review_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get review system statistics"""
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.review_db_path) as conn:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'reviewed' AND approved = 1 THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'reviewed' AND approved = 0 THEN 1 ELSE 0 END) as rejected,
                    AVG(CASE WHEN status = 'reviewed' THEN 
                        (julianday(review_timestamp) - julianday(timestamp)) * 24 * 60 
                        ELSE NULL END) as avg_review_time_minutes
                FROM review_queue 
                WHERE timestamp > ?
            ''', (cutoff_date,))
            
            row = cursor.fetchone()
            
            # Severity breakdown
            cursor.execute('''
                SELECT severity, COUNT(*) 
                FROM review_queue 
                WHERE timestamp > ?
                GROUP BY severity
            ''', (cutoff_date,))
            
            severity_stats = dict(cursor.fetchall())
            
            return {
                'total_reviews': row[0] or 0,
                'pending_reviews': row[1] or 0,
                'approved_reviews': row[2] or 0,
                'rejected_reviews': row[3] or 0,
                'avg_review_time_minutes': row[4] or 0,
                'approval_rate': (row[2] or 0) / max(row[2] or 0 + row[3] or 0, 1) * 100,
                'severity_breakdown': severity_stats,
                'period_days': days
            }

# Global instances
hallucination_detector = HallucinationDetector()
human_review_system = HumanReviewSystem()

def analyze_and_flag_response(session_id: str, question: str, answer: str,
                            sources: List[Dict], confidence: Optional[float] = None) -> Optional[int]:
    """Analyze response and submit for review if flagged"""
    
    flag = hallucination_detector.analyze_response(
        session_id, question, answer, sources, confidence
    )
    
    if flag:
        # Submit for human review
        review_id = human_review_system.submit_for_review(
            session_id, question, answer, sources, flag
        )
        
        # Log the flagging
        secure_logger.log_response(
            session_id, 0, True,  # Latency will be updated elsewhere
            confidence_score=confidence,
            hallucination_flag=True,
            human_review_flag=True
        )
        
        return review_id
    
    return None

# Export main components
__all__ = [
    'HallucinationDetector',
    'HumanReviewSystem',
    'HallucinationFlag',
    'hallucination_detector',
    'human_review_system',
    'analyze_and_flag_response'
]