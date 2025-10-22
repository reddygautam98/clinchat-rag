#!/usr/bin/env python3
"""
Clinical Staff Training System
Interactive training platform for ClinChat-RAG Clinical AI Assistant
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from enum import Enum

logger = logging.getLogger(__name__)

class TrainingModuleType(Enum):
    """Types of training modules"""
    INTRODUCTION = "introduction"
    BASIC_USAGE = "basic_usage"
    ADVANCED_FEATURES = "advanced_features"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    SECURITY_PROTOCOLS = "security_protocols"
    AI_INTERACTION = "ai_interaction"
    PATIENT_DATA = "patient_data"
    EMERGENCY_PROCEDURES = "emergency_procedures"
    TROUBLESHOOTING = "troubleshooting"

@dataclass
class TrainingModule:
    """Individual training module"""
    id: str
    title: str
    description: str
    module_type: TrainingModuleType
    duration_minutes: int
    prerequisites: List[str]
    learning_objectives: List[str]
    content_sections: List[Dict[str, Any]]
    quiz_questions: List[Dict[str, Any]]
    practical_exercises: List[Dict[str, Any]]
    resources: List[str]
    certification_required: bool = False

@dataclass
class UserProgress:
    """User training progress tracking"""
    user_id: str
    module_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_section: int = 0
    quiz_score: Optional[float] = None
    certification_earned: bool = False
    time_spent_minutes: int = 0
    notes: str = ""

@dataclass
class TrainingSession:
    """Individual training session"""
    session_id: str
    user_id: str
    module_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    sections_completed: List[int] = None
    interactions: List[Dict[str, Any]] = None
    feedback: Optional[str] = None

class TrainingContentManager:
    """Manages training content and delivery"""
    
    def __init__(self, content_path: str = "training/content"):
        self.content_path = Path(content_path)
        self.modules: Dict[str, TrainingModule] = {}
        self.load_training_modules()
    
    def load_training_modules(self):
        """Load all training modules from content directory"""
        
        # Module 1: System Introduction
        intro_module = TrainingModule(
            id="intro_001",
            title="ClinChat-RAG Introduction",
            description="Welcome to ClinChat-RAG Clinical AI Assistant",
            module_type=TrainingModuleType.INTRODUCTION,
            duration_minutes=30,
            prerequisites=[],
            learning_objectives=[
                "Understand ClinChat-RAG's purpose and capabilities",
                "Navigate the main interface",
                "Access help and support resources",
                "Understand basic AI assistant concepts"
            ],
            content_sections=[
                {
                    "section_id": 1,
                    "title": "Welcome to ClinChat-RAG",
                    "type": "video",
                    "content": "introduction_video.mp4",
                    "transcript": "Welcome to ClinChat-RAG, your AI-powered clinical assistant...",
                    "duration": 5
                },
                {
                    "section_id": 2,
                    "title": "System Overview",
                    "type": "interactive",
                    "content": "system_tour.html",
                    "duration": 10
                },
                {
                    "section_id": 3,
                    "title": "Key Features",
                    "type": "text",
                    "content": """
                    ClinChat-RAG provides:
                    • AI-powered clinical decision support
                    • HIPAA-compliant patient data management
                    • Real-time EHR integration (FHIR R4)
                    • Mobile and desktop access
                    • Advanced search and retrieval
                    """,
                    "duration": 8
                },
                {
                    "section_id": 4,
                    "title": "Getting Started",
                    "type": "hands_on",
                    "content": "first_login_guide.html",
                    "duration": 7
                }
            ],
            quiz_questions=[
                {
                    "question": "What is the primary purpose of ClinChat-RAG?",
                    "type": "multiple_choice",
                    "options": [
                        "Patient scheduling",
                        "AI-powered clinical decision support",
                        "Billing management",
                        "Equipment maintenance"
                    ],
                    "correct_answer": 1,
                    "explanation": "ClinChat-RAG is designed to provide AI-powered clinical decision support to healthcare professionals."
                },
                {
                    "question": "Is ClinChat-RAG HIPAA compliant?",
                    "type": "true_false",
                    "correct_answer": True,
                    "explanation": "Yes, ClinChat-RAG is fully HIPAA compliant with enterprise-grade security."
                }
            ],
            practical_exercises=[
                {
                    "exercise_id": 1,
                    "title": "First Login",
                    "description": "Complete your first login to the system",
                    "steps": [
                        "Navigate to the ClinChat-RAG login page",
                        "Enter your credentials",
                        "Complete two-factor authentication",
                        "Explore the dashboard"
                    ],
                    "expected_outcome": "Successfully logged in and viewed dashboard"
                }
            ],
            resources=[
                "User Manual (PDF)",
                "Quick Reference Card",
                "Video Library",
                "Support Contact Information"
            ]
        )
        
        # Module 2: Basic Usage
        basic_usage_module = TrainingModule(
            id="basic_001",
            title="Basic System Usage",
            description="Learn fundamental operations and navigation",
            module_type=TrainingModuleType.BASIC_USAGE,
            duration_minutes=45,
            prerequisites=["intro_001"],
            learning_objectives=[
                "Navigate the system efficiently",
                "Perform basic patient searches",
                "Use the AI chat interface",
                "Access and view patient records",
                "Understand basic security practices"
            ],
            content_sections=[
                {
                    "section_id": 1,
                    "title": "Navigation Basics",
                    "type": "interactive",
                    "content": "navigation_tutorial.html",
                    "duration": 10
                },
                {
                    "section_id": 2,
                    "title": "Patient Search and Selection",
                    "type": "video",
                    "content": "patient_search_demo.mp4",
                    "duration": 12
                },
                {
                    "section_id": 3,
                    "title": "AI Chat Interface",
                    "type": "hands_on",
                    "content": "chat_practice.html",
                    "duration": 15
                },
                {
                    "section_id": 4,
                    "title": "Document Management",
                    "type": "interactive",
                    "content": "document_handling.html",
                    "duration": 8
                }
            ],
            quiz_questions=[
                {
                    "question": "How do you search for a patient in the system?",
                    "type": "multiple_choice",
                    "options": [
                        "Use the search bar with patient name or ID",
                        "Browse through all patients",
                        "Ask the AI to find them",
                        "Check recent patients list"
                    ],
                    "correct_answer": 0,
                    "explanation": "Use the search bar at the top of the interface with patient name, ID, or other identifiers."
                }
            ],
            practical_exercises=[
                {
                    "exercise_id": 1,
                    "title": "Patient Search Practice",
                    "description": "Find and access a patient record",
                    "steps": [
                        "Use search bar to find patient 'John Smith'",
                        "Select correct patient from results",
                        "Review patient demographics",
                        "Access recent visit history"
                    ],
                    "expected_outcome": "Successfully located and accessed patient record"
                }
            ],
            resources=[
                "Navigation Quick Guide",
                "Search Tips and Tricks",
                "Patient Data Overview"
            ]
        )
        
        # Module 3: HIPAA Compliance Training
        hipaa_module = TrainingModule(
            id="hipaa_001",
            title="HIPAA Compliance and Security",
            description="Essential HIPAA compliance training for healthcare professionals",
            module_type=TrainingModuleType.HIPAA_COMPLIANCE,
            duration_minutes=60,
            prerequisites=["intro_001"],
            learning_objectives=[
                "Understand HIPAA requirements",
                "Recognize PHI and handle it appropriately",
                "Follow proper access controls",
                "Report security incidents",
                "Maintain audit compliance"
            ],
            content_sections=[
                {
                    "section_id": 1,
                    "title": "HIPAA Overview",
                    "type": "text",
                    "content": """
                    HIPAA (Health Insurance Portability and Accountability Act) protects patient health information.
                    
                    Key Components:
                    • Privacy Rule - protects PHI
                    • Security Rule - safeguards ePHI
                    • Breach Notification Rule - requires notification of breaches
                    • Enforcement Rule - penalties for violations
                    """,
                    "duration": 15
                },
                {
                    "section_id": 2,
                    "title": "PHI Identification and Handling",
                    "type": "interactive",
                    "content": "phi_examples.html",
                    "duration": 20
                },
                {
                    "section_id": 3,
                    "title": "Access Controls and Authentication",
                    "type": "video",
                    "content": "access_control_demo.mp4",
                    "duration": 15
                },
                {
                    "section_id": 4,
                    "title": "Incident Reporting",
                    "type": "text",
                    "content": "Steps for reporting security incidents and potential breaches",
                    "duration": 10
                }
            ],
            quiz_questions=[
                {
                    "question": "Which of the following is considered PHI?",
                    "type": "multiple_choice",
                    "options": [
                        "Patient's favorite color",
                        "Patient's medical record number",
                        "Hospital cafeteria menu",
                        "Weather report"
                    ],
                    "correct_answer": 1,
                    "explanation": "Medical record numbers are unique identifiers that constitute PHI under HIPAA."
                }
            ],
            practical_exercises=[
                {
                    "exercise_id": 1,
                    "title": "PHI Identification Exercise",
                    "description": "Identify PHI elements in sample records",
                    "steps": [
                        "Review sample patient record",
                        "Identify all PHI elements",
                        "Determine appropriate access levels",
                        "Practice proper handling procedures"
                    ],
                    "expected_outcome": "Correctly identified all PHI elements"
                }
            ],
            resources=[
                "HIPAA Compliance Manual",
                "PHI Quick Reference",
                "Incident Reporting Forms"
            ],
            certification_required=True
        )
        
        # Module 4: AI Interaction Best Practices
        ai_interaction_module = TrainingModule(
            id="ai_001",
            title="AI Interaction Best Practices",
            description="Effective communication with the AI assistant",
            module_type=TrainingModuleType.AI_INTERACTION,
            duration_minutes=40,
            prerequisites=["basic_001"],
            learning_objectives=[
                "Formulate effective AI queries",
                "Interpret AI responses appropriately",
                "Understand AI limitations",
                "Use AI for clinical decision support",
                "Maintain professional judgment"
            ],
            content_sections=[
                {
                    "section_id": 1,
                    "title": "Effective Query Formulation",
                    "type": "interactive",
                    "content": "query_examples.html",
                    "duration": 15
                },
                {
                    "section_id": 2,
                    "title": "Interpreting AI Responses",
                    "type": "video",
                    "content": "ai_response_interpretation.mp4",
                    "duration": 12
                },
                {
                    "section_id": 3,
                    "title": "AI Limitations and Safeguards",
                    "type": "text",
                    "content": "Understanding when NOT to rely on AI recommendations",
                    "duration": 8
                },
                {
                    "section_id": 4,
                    "title": "Clinical Decision Support",
                    "type": "hands_on",
                    "content": "clinical_scenarios.html",
                    "duration": 5
                }
            ],
            quiz_questions=[
                {
                    "question": "When should you NOT follow an AI recommendation?",
                    "type": "multiple_choice",
                    "options": [
                        "When it conflicts with your clinical judgment",
                        "When the patient requests it",
                        "When it's too complex",
                        "Never, always follow AI recommendations"
                    ],
                    "correct_answer": 0,
                    "explanation": "AI is a tool to support, not replace, clinical judgment. Always use professional discretion."
                }
            ],
            practical_exercises=[
                {
                    "exercise_id": 1,
                    "title": "Clinical Query Practice",
                    "description": "Practice formulating effective clinical queries",
                    "steps": [
                        "Review patient case scenario",
                        "Formulate appropriate AI query",
                        "Evaluate AI response",
                        "Make clinical decision with AI support"
                    ],
                    "expected_outcome": "Successfully used AI for clinical decision support"
                }
            ],
            resources=[
                "AI Query Templates",
                "Clinical Scenario Library",
                "Best Practices Guide"
            ]
        )
        
        # Store modules
        self.modules = {
            "intro_001": intro_module,
            "basic_001": basic_usage_module,
            "hipaa_001": hipaa_module,
            "ai_001": ai_interaction_module
        }
        
        logger.info(f"Loaded {len(self.modules)} training modules")
    
    def get_module(self, module_id: str) -> Optional[TrainingModule]:
        """Get specific training module"""
        return self.modules.get(module_id)
    
    def get_modules_by_type(self, module_type: TrainingModuleType) -> List[TrainingModule]:
        """Get modules of specific type"""
        return [module for module in self.modules.values() 
                if module.module_type == module_type]
    
    def get_recommended_path(self, role: str) -> List[str]:
        """Get recommended training path for role"""
        paths = {
            "physician": ["intro_001", "basic_001", "hipaa_001", "ai_001"],
            "nurse": ["intro_001", "basic_001", "hipaa_001"],
            "admin": ["intro_001", "hipaa_001"],
            "researcher": ["intro_001", "basic_001", "ai_001"]
        }
        return paths.get(role, ["intro_001", "basic_001"])

class TrainingProgressTracker:
    """Tracks user progress through training modules"""
    
    def __init__(self, db_path: str = "training/progress.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize training progress database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT,
                module_id TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                current_section INTEGER DEFAULT 0,
                quiz_score REAL,
                certification_earned BOOLEAN DEFAULT FALSE,
                time_spent_minutes INTEGER DEFAULT 0,
                notes TEXT,
                PRIMARY KEY (user_id, module_id)
            )
        """)
        
        # Training sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                module_id TEXT,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                sections_completed TEXT,
                interactions TEXT,
                feedback TEXT
            )
        """)
        
        # Certifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certifications (
                user_id TEXT,
                module_id TEXT,
                earned_at TIMESTAMP,
                expires_at TIMESTAMP,
                certificate_id TEXT,
                PRIMARY KEY (user_id, module_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start_module(self, user_id: str, module_id: str) -> UserProgress:
        """Start training module for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        progress = UserProgress(
            user_id=user_id,
            module_id=module_id,
            started_at=datetime.now()
        )
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_progress 
            (user_id, module_id, started_at, current_section, time_spent_minutes)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, module_id, progress.started_at, 0, 0))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Started training module {module_id} for user {user_id}")
        return progress
    
    def update_progress(self, user_id: str, module_id: str, 
                       section: int, time_spent: int):
        """Update user progress in module"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_progress 
            SET current_section = ?, time_spent_minutes = ?
            WHERE user_id = ? AND module_id = ?
        """, (section, time_spent, user_id, module_id))
        
        conn.commit()
        conn.close()
    
    def complete_module(self, user_id: str, module_id: str, 
                       quiz_score: Optional[float] = None):
        """Mark module as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_progress 
            SET completed_at = ?, quiz_score = ?
            WHERE user_id = ? AND module_id = ?
        """, (datetime.now(), quiz_score, user_id, module_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Completed training module {module_id} for user {user_id}")
    
    def get_user_progress(self, user_id: str) -> List[UserProgress]:
        """Get all progress for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM user_progress WHERE user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        progress_list = []
        for row in rows:
            progress = UserProgress(
                user_id=row[0],
                module_id=row[1],
                started_at=datetime.fromisoformat(row[2]),
                completed_at=datetime.fromisoformat(row[3]) if row[3] else None,
                current_section=row[4],
                quiz_score=row[5],
                certification_earned=bool(row[6]),
                time_spent_minutes=row[7],
                notes=row[8] or ""
            )
            progress_list.append(progress)
        
        return progress_list

class TrainingDeliveryEngine:
    """Delivers interactive training content"""
    
    def __init__(self, content_manager: TrainingContentManager,
                 progress_tracker: TrainingProgressTracker):
        self.content_manager = content_manager
        self.progress_tracker = progress_tracker
    
    def generate_training_page(self, user_id: str, module_id: str) -> str:
        """Generate interactive training page"""
        module = self.content_manager.get_module(module_id)
        if not module:
            return "Module not found"
        
        progress = self.progress_tracker.get_user_progress(user_id)
        current_progress = next((p for p in progress if p.module_id == module_id), None)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{module.title} - ClinChat Training</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                .training-container {{ max-width: 1000px; margin: 0 auto; }}
                .section-content {{ min-height: 400px; }}
                .progress-indicator {{ height: 10px; }}
                .quiz-question {{ margin: 20px 0; }}
                .exercise-step {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container training-container">
                <header class="mb-4">
                    <h1>{module.title}</h1>
                    <p class="lead">{module.description}</p>
                    <div class="progress">
                        <div class="progress-bar" style="width: {self._calculate_progress(current_progress, module)}%"></div>
                    </div>
                    <small>Estimated time: {module.duration_minutes} minutes</small>
                </header>
                
                <main>
                    <div id="training-sections">
                        {self._generate_sections_html(module)}
                    </div>
                    
                    <div id="quiz-section" style="display: none;">
                        {self._generate_quiz_html(module)}
                    </div>
                    
                    <div id="exercises-section" style="display: none;">
                        {self._generate_exercises_html(module)}
                    </div>
                </main>
                
                <footer class="mt-4">
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-secondary" onclick="previousSection()">Previous</button>
                        <button class="btn btn-primary" onclick="nextSection()">Next</button>
                    </div>
                </footer>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                let currentSection = {current_progress.current_section if current_progress else 0};
                let totalSections = {len(module.content_sections)};
                
                function nextSection() {{
                    if (currentSection < totalSections - 1) {{
                        currentSection++;
                        updateDisplay();
                        reportProgress();
                    }} else {{
                        showQuiz();
                    }}
                }}
                
                function previousSection() {{
                    if (currentSection > 0) {{
                        currentSection--;
                        updateDisplay();
                    }}
                }}
                
                function updateDisplay() {{
                    // Hide all sections
                    document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
                    // Show current section
                    document.getElementById('section-' + currentSection).style.display = 'block';
                    // Update progress bar
                    let progress = (currentSection / totalSections) * 100;
                    document.querySelector('.progress-bar').style.width = progress + '%';
                }}
                
                function showQuiz() {{
                    document.getElementById('training-sections').style.display = 'none';
                    document.getElementById('quiz-section').style.display = 'block';
                }}
                
                function reportProgress() {{
                    fetch('/api/training/progress', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            user_id: '{user_id}',
                            module_id: '{module_id}',
                            section: currentSection,
                            timestamp: new Date().toISOString()
                        }})
                    }});
                }}
                
                // Initialize display
                updateDisplay();
            </script>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_sections_html(self, module: TrainingModule) -> str:
        """Generate HTML for training sections"""
        sections_html = ""
        
        for i, section in enumerate(module.content_sections):
            sections_html += f"""
            <div id="section-{i}" class="content-section" style="display: {'block' if i == 0 else 'none'};">
                <h2>{section['title']}</h2>
                <div class="section-content">
                    {self._render_section_content(section)}
                </div>
            </div>
            """
        
        return sections_html
    
    def _render_section_content(self, section: Dict[str, Any]) -> str:
        """Render individual section content based on type"""
        content_type = section.get('type', 'text')
        
        if content_type == 'text':
            return f"<div class='text-content'><pre>{section['content']}</pre></div>"
        elif content_type == 'video':
            return f"""
            <div class='video-content'>
                <video controls width="100%">
                    <source src="/training/videos/{section['content']}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
            </div>
            """
        elif content_type == 'interactive':
            return f"""
            <div class='interactive-content'>
                <iframe src="/training/interactive/{section['content']}" 
                        width="100%" height="400px" frameborder="0"></iframe>
            </div>
            """
        elif content_type == 'hands_on':
            return f"""
            <div class='hands-on-content'>
                <div class="alert alert-info">
                    <strong>Hands-On Exercise</strong><br>
                    Follow the interactive guide below to practice.
                </div>
                <iframe src="/training/exercises/{section['content']}" 
                        width="100%" height="500px" frameborder="0"></iframe>
            </div>
            """
        
        return "<p>Content not available</p>"
    
    def _generate_quiz_html(self, module: TrainingModule) -> str:
        """Generate HTML for quiz section"""
        if not module.quiz_questions:
            return "<p>No quiz available for this module.</p>"
        
        quiz_html = "<h2>Knowledge Check</h2>"
        
        for i, question in enumerate(module.quiz_questions):
            quiz_html += f"""
            <div class="quiz-question card">
                <div class="card-body">
                    <h5>Question {i + 1}</h5>
                    <p>{question['question']}</p>
                    
                    <div id="question-{i}-options">
            """
            
            if question['type'] == 'multiple_choice':
                for j, option in enumerate(question['options']):
                    quiz_html += f"""
                    <div class="form-check">
                        <input class="form-check-input" type="radio" 
                               name="question-{i}" value="{j}" id="q{i}o{j}">
                        <label class="form-check-label" for="q{i}o{j}">
                            {option}
                        </label>
                    </div>
                    """
            elif question['type'] == 'true_false':
                quiz_html += """
                <div class="form-check">
                    <input class="form-check-input" type="radio" 
                           name="question-{}" value="true" id="q{}true">
                    <label class="form-check-label" for="q{}true">True</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="radio" 
                           name="question-{}" value="false" id="q{}false">
                    <label class="form-check-label" for="q{}false">False</label>
                </div>
                """.format(i, i, i, i, i)
            
            quiz_html += """
                    </div>
                    <div id="question-{}-feedback" class="alert" style="display: none;"></div>
                </div>
            </div>
            """.format(i)
        
        quiz_html += """
        <button class="btn btn-success" onclick="submitQuiz()">Submit Quiz</button>
        """
        
        return quiz_html
    
    def _generate_exercises_html(self, module: TrainingModule) -> str:
        """Generate HTML for practical exercises"""
        if not module.practical_exercises:
            return "<p>No practical exercises for this module.</p>"
        
        exercises_html = "<h2>Practical Exercises</h2>"
        
        for exercise in module.practical_exercises:
            exercises_html += f"""
            <div class="exercise card">
                <div class="card-body">
                    <h5>{exercise['title']}</h5>
                    <p>{exercise['description']}</p>
                    
                    <h6>Steps:</h6>
                    <ol>
            """
            
            for step in exercise['steps']:
                exercises_html += f"<li class='exercise-step'>{step}</li>"
            
            exercises_html += f"""
                    </ol>
                    
                    <div class="alert alert-success">
                        <strong>Expected Outcome:</strong> {exercise['expected_outcome']}
                    </div>
                    
                    <button class="btn btn-primary" onclick="completeExercise('{exercise['exercise_id']}')">
                        Mark as Complete
                    </button>
                </div>
            </div>
            """
        
        return exercises_html
    
    def _calculate_progress(self, progress: Optional[UserProgress], 
                          module: TrainingModule) -> int:
        """Calculate completion percentage"""
        if not progress:
            return 0
        
        if progress.completed_at:
            return 100
        
        total_sections = len(module.content_sections)
        if total_sections == 0:
            return 0
        
        return int((progress.current_section / total_sections) * 100)

def create_training_system():
    """Initialize complete training system"""
    
    # Create training directories
    Path("training/content").mkdir(parents=True, exist_ok=True)
    Path("training/videos").mkdir(parents=True, exist_ok=True)
    Path("training/interactive").mkdir(parents=True, exist_ok=True)
    Path("training/exercises").mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    content_manager = TrainingContentManager()
    progress_tracker = TrainingProgressTracker()
    delivery_engine = TrainingDeliveryEngine(content_manager, progress_tracker)
    
    return {
        "content_manager": content_manager,
        "progress_tracker": progress_tracker,
        "delivery_engine": delivery_engine,
        "modules": content_manager.modules
    }

# Example usage and demonstration
async def demo_training_system():
    """Demonstrate the training system"""
    
    print("🎓 Creating ClinChat-RAG Training System...")
    training_system = create_training_system()
    
    print(f"📚 Loaded {len(training_system['modules'])} training modules:")
    for module_id, module in training_system['modules'].items():
        print(f"   • {module.title} ({module.duration_minutes} min)")
    
    # Simulate user training
    user_id = "dr_smith_001"
    module_id = "intro_001"
    
    print(f"\n👨‍⚕️ Starting training for user {user_id}")
    
    # Start module
    progress_tracker = training_system['progress_tracker']
    progress = progress_tracker.start_module(user_id, module_id)
    print(f"   Started: {module_id}")
    
    # Simulate progress updates
    for section in range(1, 4):
        progress_tracker.update_progress(user_id, module_id, section, section * 10)
        print(f"   Completed section {section}")
    
    # Complete module
    quiz_score = 85.0
    progress_tracker.complete_module(user_id, module_id, quiz_score)
    print(f"   Completed with quiz score: {quiz_score}%")
    
    # Generate training page
    delivery_engine = training_system['delivery_engine']
    training_page = delivery_engine.generate_training_page(user_id, module_id)
    
    # Save training page
    with open("training/sample_training_page.html", "w") as f:
        f.write(training_page)
    
    print("✅ Training system demonstration complete!")
    print("📄 Sample training page saved to: training/sample_training_page.html")

if __name__ == "__main__":
    asyncio.run(demo_training_system())