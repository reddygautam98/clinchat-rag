"""
ClinChat-RAG Clinician Onboarding System
Comprehensive onboarding workflow for healthcare professionals
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

import asyncio
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class OnboardingStatus(Enum):
    """Onboarding process status enumeration"""
    INVITED = "invited"
    IN_PROGRESS = "in_progress"
    TRAINING_COMPLETE = "training_complete"
    ASSESSMENT_PENDING = "assessment_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class TrainingModuleStatus(Enum):
    """Training module completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ClinicianProfile:
    """Clinician profile data structure"""
    first_name: str
    last_name: str
    email: str
    medical_license: str
    specialty: str
    institution: str
    years_experience: int
    phone: Optional[str] = None
    department: Optional[str] = None
    supervisor: Optional[str] = None

@dataclass
class TrainingModule:
    """Training module definition"""
    module_id: str
    title: str
    description: str
    content_type: str  # 'video', 'document', 'interactive', 'quiz'
    duration_minutes: int
    passing_score: int
    content_path: str
    prerequisites: List[str]
    is_mandatory: bool = True

@dataclass
class AssessmentResult:
    """Training assessment result"""
    module_id: str
    score: int
    max_score: int
    passed: bool
    attempt_number: int
    feedback: Optional[str] = None
    answers: Optional[Dict] = None

# Database Models
class Clinician(Base):
    __tablename__ = "clinicians"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    medical_license = Column(String(50), nullable=False, index=True)
    specialty = Column(String(100), nullable=False)
    institution = Column(String(200), nullable=False)
    department = Column(String(100))
    years_experience = Column(Integer, nullable=False)
    phone = Column(String(20))
    supervisor = Column(String(200))
    
    status = Column(String(20), nullable=False, default=OnboardingStatus.INVITED.value)
    invited_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    approved_at = Column(DateTime)
    approved_by = Column(String(200))
    
    # Relationships
    training_progress = relationship("TrainingProgress", back_populates="clinician")
    assessments = relationship("Assessment", back_populates="clinician")
    feedback = relationship("ClinicianFeedback", back_populates="clinician")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrainingContent(Base):
    __tablename__ = "training_content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(String(20), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    passing_score = Column(Integer, nullable=False, default=80)
    content_path = Column(String(500), nullable=False)
    prerequisites = Column(Text)  # JSON array of prerequisite module IDs
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrainingProgress(Base):
    __tablename__ = "training_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id"), nullable=False)
    module_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=TrainingModuleStatus.NOT_STARTED.value)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    score = Column(Integer)
    attempts = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    
    # Relationships
    clinician = relationship("Clinician", back_populates="training_progress")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id"), nullable=False)
    module_id = Column(String(50), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    answers = Column(Text)  # JSON of answers
    feedback = Column(Text)
    
    # Relationships
    clinician = relationship("Clinician", back_populates="assessments")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ClinicianFeedback(Base):
    __tablename__ = "clinician_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("clinicians.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # 'system_improvement', 'training_feedback', 'bug_report'
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(10), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    status = Column(String(20), nullable=False, default='open')  # 'open', 'in_review', 'resolved', 'closed'
    response = Column(Text)
    responded_by = Column(String(200))
    responded_at = Column(DateTime)
    
    # Relationships
    clinician = relationship("Clinician", back_populates="feedback")
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class OnboardingSystem:
    """Main onboarding system coordinator"""
    
    def __init__(self, database_url: str, email_config: Dict[str, str]):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.email_config = email_config
        
        # Initialize training modules
        self.training_modules = self._initialize_training_modules()
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
    def _initialize_training_modules(self) -> List[TrainingModule]:
        """Initialize standard training modules"""
        return [
            TrainingModule(
                module_id="hipaa_basics",
                title="HIPAA Fundamentals for AI Systems",
                description="Essential HIPAA knowledge for using AI in healthcare",
                content_type="interactive",
                duration_minutes=45,
                passing_score=90,
                content_path="/training/hipaa_basics/",
                prerequisites=[],
                is_mandatory=True
            ),
            TrainingModule(
                module_id="phi_handling",
                title="Protected Health Information Handling",
                description="Best practices for PHI in AI-assisted clinical workflows",
                content_type="video",
                duration_minutes=30,
                passing_score=85,
                content_path="/training/phi_handling/",
                prerequisites=["hipaa_basics"],
                is_mandatory=True
            ),
            TrainingModule(
                module_id="ai_limitations",
                title="Understanding AI Limitations in Clinical Practice",
                description="Critical understanding of AI capabilities and limitations",
                content_type="interactive",
                duration_minutes=60,
                passing_score=90,
                content_path="/training/ai_limitations/",
                prerequisites=["hipaa_basics"],
                is_mandatory=True
            ),
            TrainingModule(
                module_id="system_usage",
                title="ClinChat-RAG System Usage",
                description="Hands-on training with the ClinChat-RAG system",
                content_type="interactive",
                duration_minutes=90,
                passing_score=80,
                content_path="/training/system_usage/",
                prerequisites=["phi_handling", "ai_limitations"],
                is_mandatory=True
            ),
            TrainingModule(
                module_id="error_reporting",
                title="Error Recognition and Reporting",
                description="How to identify and report AI errors or inappropriate responses",
                content_type="document",
                duration_minutes=20,
                passing_score=85,
                content_path="/training/error_reporting/",
                prerequisites=["system_usage"],
                is_mandatory=True
            ),
            TrainingModule(
                module_id="clinical_decision_support",
                title="AI as Clinical Decision Support",
                description="Integrating AI insights into clinical decision-making",
                content_type="video",
                duration_minutes=40,
                passing_score=80,
                content_path="/training/clinical_decision_support/",
                prerequisites=["system_usage"],
                is_mandatory=False
            )
        ]
    
    async def invite_clinician(self, profile: ClinicianProfile, invited_by: str) -> str:
        """Send invitation to clinician to start onboarding"""
        try:
            # Check if clinician already exists
            existing = self.session.query(Clinician).filter_by(email=profile.email).first()
            if existing:
                if existing.status == OnboardingStatus.APPROVED.value:
                    raise ValueError(f"Clinician {profile.email} is already onboarded")
                else:
                    # Update existing record
                    clinician = existing
            else:
                # Create new clinician record
                clinician = Clinician(
                    email=profile.email,
                    first_name=profile.first_name,
                    last_name=profile.last_name,
                    medical_license=profile.medical_license,
                    specialty=profile.specialty,
                    institution=profile.institution,
                    department=profile.department,
                    years_experience=profile.years_experience,
                    phone=profile.phone,
                    supervisor=profile.supervisor
                )
                self.session.add(clinician)
            
            # Generate invitation token
            invitation_token = str(uuid.uuid4())
            
            # Send invitation email
            await self._send_invitation_email(profile.email, invitation_token, profile.first_name)
            
            self.session.commit()
            
            logger.info(f"Invitation sent to {profile.email} by {invited_by}")
            return str(clinician.id)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to invite clinician {profile.email}: {str(e)}")
            raise
    
    async def start_onboarding(self, clinician_id: str, invitation_token: str) -> Dict[str, Any]:
        """Start the onboarding process for a clinician"""
        try:
            clinician = self.session.query(Clinician).filter_by(id=clinician_id).first()
            if not clinician:
                raise ValueError("Invalid clinician ID")
            
            # Update status and timestamp
            clinician.status = OnboardingStatus.IN_PROGRESS.value
            clinician.started_at = datetime.utcnow()
            
            # Initialize training progress for mandatory modules
            for module in self.training_modules:
                if module.is_mandatory:
                    progress = TrainingProgress(
                        clinician_id=clinician.id,
                        module_id=module.module_id,
                        status=TrainingModuleStatus.NOT_STARTED.value
                    )
                    self.session.add(progress)
            
            self.session.commit()
            
            # Return onboarding dashboard data
            return await self._get_onboarding_dashboard(clinician_id)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to start onboarding for {clinician_id}: {str(e)}")
            raise
    
    async def get_training_module(self, module_id: str) -> Dict[str, Any]:
        """Get training module content and metadata"""
        try:
            module = next((m for m in self.training_modules if m.module_id == module_id), None)
            if not module:
                raise ValueError(f"Training module {module_id} not found")
            
            # Load content based on type
            content_path = Path(f"onboarding/content{module.content_path}")
            
            if module.content_type == "interactive":
                content = await self._load_interactive_content(content_path)
            elif module.content_type == "video":
                content = await self._load_video_content(content_path)
            elif module.content_type == "document":
                content = await self._load_document_content(content_path)
            else:
                content = {"type": "unknown", "message": "Content type not supported"}
            
            return {
                "module": asdict(module),
                "content": content
            }
            
        except Exception as e:
            logger.error(f"Failed to get training module {module_id}: {str(e)}")
            raise
    
    async def update_training_progress(self, clinician_id: str, module_id: str, 
                                    time_spent: int, completed: bool = False) -> bool:
        """Update training progress for a module"""
        try:
            progress = self.session.query(TrainingProgress).filter_by(
                clinician_id=clinician_id, module_id=module_id
            ).first()
            
            if not progress:
                # Create new progress record
                progress = TrainingProgress(
                    clinician_id=clinician_id,
                    module_id=module_id,
                    status=TrainingModuleStatus.IN_PROGRESS.value,
                    started_at=datetime.utcnow()
                )
                self.session.add(progress)
            
            # Update progress
            if progress.status == TrainingModuleStatus.NOT_STARTED.value:
                progress.status = TrainingModuleStatus.IN_PROGRESS.value
                progress.started_at = datetime.utcnow()
            
            progress.time_spent_minutes += time_spent
            
            if completed:
                progress.status = TrainingModuleStatus.COMPLETED.value
                progress.completed_at = datetime.utcnow()
            
            self.session.commit()
            
            # Check if all training is complete
            await self._check_training_completion(clinician_id)
            
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update training progress: {str(e)}")
            raise
    
    async def submit_assessment(self, clinician_id: str, module_id: str, 
                              answers: Dict[str, Any]) -> AssessmentResult:
        """Submit and grade module assessment"""
        try:
            # Get module info
            module = next((m for m in self.training_modules if m.module_id == module_id), None)
            if not module:
                raise ValueError(f"Module {module_id} not found")
            
            # Get current attempt number
            attempt_count = self.session.query(Assessment).filter_by(
                clinician_id=clinician_id, module_id=module_id
            ).count()
            attempt_number = attempt_count + 1
            
            # Load assessment questions and grade
            questions = await self._load_assessment_questions(module_id)
            score, max_score, feedback = await self._grade_assessment(questions, answers)
            passed = score >= module.passing_score
            
            # Create assessment record
            assessment = Assessment(
                clinician_id=clinician_id,
                module_id=module_id,
                attempt_number=attempt_number,
                score=score,
                max_score=max_score,
                passed=passed,
                answers=json.dumps(answers),
                feedback=feedback
            )
            self.session.add(assessment)
            
            # Update training progress
            progress = self.session.query(TrainingProgress).filter_by(
                clinician_id=clinician_id, module_id=module_id
            ).first()
            
            if progress:
                progress.score = score
                progress.attempts = attempt_number
                if passed:
                    progress.status = TrainingModuleStatus.COMPLETED.value
                    progress.completed_at = datetime.utcnow()
                else:
                    progress.status = TrainingModuleStatus.FAILED.value
            
            self.session.commit()
            
            # Check overall training completion
            if passed:
                await self._check_training_completion(clinician_id)
            
            return AssessmentResult(
                module_id=module_id,
                score=score,
                max_score=max_score,
                passed=passed,
                attempt_number=attempt_number,
                feedback=feedback,
                answers=answers
            )
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to submit assessment: {str(e)}")
            raise
    
    async def submit_feedback(self, clinician_id: str, feedback_type: str, 
                            subject: str, message: str, priority: str = "medium") -> str:
        """Submit feedback from clinician"""
        try:
            feedback = ClinicianFeedback(
                clinician_id=clinician_id,
                feedback_type=feedback_type,
                subject=subject,
                message=message,
                priority=priority
            )
            self.session.add(feedback)
            self.session.commit()
            
            logger.info(f"Feedback submitted by clinician {clinician_id}: {subject}")
            
            # Send notification to admin team
            await self._notify_feedback_received(feedback)
            
            return str(feedback.id)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to submit feedback: {str(e)}")
            raise
    
    async def approve_clinician(self, clinician_id: str, approved_by: str, 
                              notes: Optional[str] = None) -> bool:
        """Approve clinician for system access"""
        try:
            clinician = self.session.query(Clinician).filter_by(id=clinician_id).first()
            if not clinician:
                raise ValueError("Clinician not found")
            
            # Verify training completion
            if clinician.status != OnboardingStatus.TRAINING_COMPLETE.value:
                raise ValueError("Training not complete")
            
            # Update status
            clinician.status = OnboardingStatus.APPROVED.value
            clinician.approved_at = datetime.utcnow()
            clinician.approved_by = approved_by
            
            self.session.commit()
            
            # Send approval notification
            await self._send_approval_email(clinician.email, clinician.first_name)
            
            logger.info(f"Clinician {clinician.email} approved by {approved_by}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to approve clinician: {str(e)}")
            raise
    
    async def _get_onboarding_dashboard(self, clinician_id: str) -> Dict[str, Any]:
        """Get onboarding dashboard data"""
        clinician = self.session.query(Clinician).filter_by(id=clinician_id).first()
        if not clinician:
            raise ValueError("Clinician not found")
        
        # Get training progress
        progress_records = self.session.query(TrainingProgress).filter_by(
            clinician_id=clinician_id
        ).all()
        
        progress_dict = {p.module_id: p for p in progress_records}
        
        # Build module progress
        modules_progress = []
        for module in self.training_modules:
            if module.is_mandatory:
                progress = progress_dict.get(module.module_id)
                modules_progress.append({
                    "module": asdict(module),
                    "status": progress.status if progress else TrainingModuleStatus.NOT_STARTED.value,
                    "score": progress.score if progress else None,
                    "attempts": progress.attempts if progress else 0,
                    "time_spent": progress.time_spent_minutes if progress else 0
                })
        
        return {
            "clinician": {
                "id": str(clinician.id),
                "name": f"{clinician.first_name} {clinician.last_name}",
                "email": clinician.email,
                "status": clinician.status,
                "started_at": clinician.started_at.isoformat() if clinician.started_at else None
            },
            "modules": modules_progress,
            "overall_progress": await self._calculate_overall_progress(clinician_id)
        }
    
    async def _check_training_completion(self, clinician_id: str) -> None:
        """Check if all mandatory training is complete"""
        mandatory_modules = [m.module_id for m in self.training_modules if m.is_mandatory]
        
        completed_modules = self.session.query(TrainingProgress).filter_by(
            clinician_id=clinician_id,
            status=TrainingModuleStatus.COMPLETED.value
        ).filter(TrainingProgress.module_id.in_(mandatory_modules)).count()
        
        if completed_modules == len(mandatory_modules):
            # All training complete
            clinician = self.session.query(Clinician).filter_by(id=clinician_id).first()
            if clinician:
                clinician.status = OnboardingStatus.TRAINING_COMPLETE.value
                clinician.completed_at = datetime.utcnow()
                self.session.commit()
                
                # Notify admin for approval
                await self._notify_training_complete(clinician)
    
    async def _calculate_overall_progress(self, clinician_id: str) -> Dict[str, Any]:
        """Calculate overall training progress"""
        mandatory_modules = [m.module_id for m in self.training_modules if m.is_mandatory]
        total_modules = len(mandatory_modules)
        
        progress_records = self.session.query(TrainingProgress).filter_by(
            clinician_id=clinician_id
        ).filter(TrainingProgress.module_id.in_(mandatory_modules)).all()
        
        completed = len([p for p in progress_records if p.status == TrainingModuleStatus.COMPLETED.value])
        in_progress = len([p for p in progress_records if p.status == TrainingModuleStatus.IN_PROGRESS.value])
        
        return {
            "total_modules": total_modules,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_modules - completed - in_progress,
            "completion_percentage": (completed / total_modules) * 100 if total_modules > 0 else 0
        }
    
    # Email notification methods would be implemented here
    async def _send_invitation_email(self, email: str, token: str, first_name: str) -> None:
        """Send invitation email"""
        # Implementation would send actual email
        logger.info(f"Sending invitation email to {email}")
    
    async def _send_approval_email(self, email: str, first_name: str) -> None:
        """Send approval notification email"""
        logger.info(f"Sending approval email to {email}")
    
    async def _notify_training_complete(self, clinician: Clinician) -> None:
        """Notify admin that clinician completed training"""
        logger.info(f"Training complete notification for {clinician.email}")
    
    async def _notify_feedback_received(self, feedback: ClinicianFeedback) -> None:
        """Notify admin team of new feedback"""
        logger.info(f"New feedback received: {feedback.subject}")
    
    # Content loading methods would be implemented here
    async def _load_interactive_content(self, path: Path) -> Dict[str, Any]:
        """Load interactive training content"""
        return {"type": "interactive", "content": "Interactive content would be loaded here"}
    
    async def _load_video_content(self, path: Path) -> Dict[str, Any]:
        """Load video training content"""
        return {"type": "video", "content": "Video content metadata would be loaded here"}
    
    async def _load_document_content(self, path: Path) -> Dict[str, Any]:
        """Load document training content"""
        return {"type": "document", "content": "Document content would be loaded here"}
    
    async def _load_assessment_questions(self, module_id: str) -> List[Dict[str, Any]]:
        """Load assessment questions for module"""
        return [{"question": "Sample question", "type": "multiple_choice", "options": ["A", "B", "C", "D"], "correct": "A"}]
    
    async def _grade_assessment(self, questions: List[Dict], answers: Dict) -> tuple:
        """Grade assessment answers"""
        # Implementation would actually grade the assessment
        return 85, 100, "Good work! Review section 3 for improvement."

# FastAPI Integration
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

class OnboardingAPI:
    """FastAPI integration for onboarding system"""
    
    def __init__(self, onboarding_system: OnboardingSystem):
        self.onboarding = onboarding_system
        self.app = FastAPI(title="ClinChat-RAG Onboarding API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.post("/onboarding/invite")
        async def invite_clinician(profile: ClinicianProfile, invited_by: str):
            try:
                clinician_id = await self.onboarding.invite_clinician(profile, invited_by)
                return {"success": True, "clinician_id": clinician_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/onboarding/{clinician_id}/dashboard")
        async def get_dashboard(clinician_id: str):
            try:
                dashboard = await self.onboarding._get_onboarding_dashboard(clinician_id)
                return dashboard
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @self.app.post("/onboarding/{clinician_id}/feedback")
        async def submit_feedback(clinician_id: str, feedback_type: str, 
                                subject: str, message: str, priority: str = "medium"):
            try:
                feedback_id = await self.onboarding.submit_feedback(
                    clinician_id, feedback_type, subject, message, priority
                )
                return {"success": True, "feedback_id": feedback_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))