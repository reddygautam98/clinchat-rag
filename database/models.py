"""
Database Models for Unified Google Gemini & Groq API Integration
Comprehensive schema for conversations, analytics, and clinical data
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
import uuid

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint,
    Enum as SQLEnum, BigInteger
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import enum

# Import the base from connection module
from database.connection import Base

class ProviderType(enum.Enum):
    """AI Provider types"""
    GOOGLE_GEMINI = "google_gemini"
    GROQ = "groq"
    FUSION = "fusion"  # For fusion AI results

class AnalysisType(enum.Enum):
    """Clinical analysis types"""
    EMERGENCY_ASSESSMENT = "emergency_assessment"
    QUICK_TRIAGE = "quick_triage"
    DIAGNOSTIC_REASONING = "diagnostic_reasoning"
    TREATMENT_PLANNING = "treatment_planning"
    DETAILED_ANALYSIS = "detailed_analysis"
    GENERAL = "general"

class UrgencyLevel(enum.Enum):
    """Clinical urgency levels"""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    NORMAL = "normal"
    ROUTINE = "routine"

class FusionStrategy(enum.Enum):
    """Fusion AI strategies"""
    SPEED_FIRST = "speed_first"
    ACCURACY_FIRST = "accuracy_first"
    PARALLEL_CONSENSUS = "parallel_consensus"

# User Management
class User(Base):
    """User accounts for the clinical AI system"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(200))
    role = Column(String(50), default="clinician")  # clinician, admin, viewer
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# Core Conversation Management
class Conversation(Base):
    """Main conversation records for both APIs"""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(36), ForeignKey("user_sessions.id"), nullable=True)
    
    # Input data
    input_text = Column(Text, nullable=False)
    analysis_type = Column(SQLEnum(AnalysisType), default=AnalysisType.GENERAL)
    urgency_level = Column(SQLEnum(UrgencyLevel), default=UrgencyLevel.NORMAL)
    
    # Fusion AI specific
    fusion_strategy = Column(SQLEnum(FusionStrategy), nullable=True)
    primary_provider = Column(SQLEnum(ProviderType), nullable=True)
    secondary_provider = Column(SQLEnum(ProviderType), nullable=True)
    
    # Results
    final_analysis = Column(Text)
    confidence_score = Column(Float)
    processing_time_total = Column(Float)  # Total time for fusion processing
    
    # Clinical entities extracted
    clinical_entities = Column(JSON)
    
    # Additional metadata
    conversation_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    provider_responses = relationship("ProviderResponse", back_populates="conversation")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_user_created', 'user_id', 'created_at'),
        Index('idx_conversation_type_urgency', 'analysis_type', 'urgency_level'),
        Index('idx_conversation_provider', 'primary_provider'),
    )

class ProviderResponse(Base):
    """Individual AI provider responses (Gemini/Groq)"""
    __tablename__ = "provider_responses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    
    # Provider details
    provider = Column(SQLEnum(ProviderType), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    
    # Request/Response
    request_payload = Column(JSON)
    response_text = Column(Text)
    response_metadata = Column(JSON, default=dict)
    
    # Performance metrics
    processing_time = Column(Float)  # Time for this specific provider
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    tokens_total = Column(Integer)
    
    # Cost tracking
    cost_input = Column(Float)
    cost_output = Column(Float)
    cost_total = Column(Float)
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    http_status_code = Column(Integer)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="provider_responses")
    
    # Indexes
    __table_args__ = (
        Index('idx_provider_response_conversation', 'conversation_id'),
        Index('idx_provider_response_provider_model', 'provider', 'model_name'),
        Index('idx_provider_response_success', 'success'),
    )

# Clinical Data Management
class ClinicalDocument(Base):
    """Clinical documents processed by the system"""
    __tablename__ = "clinical_documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Document metadata
    filename = Column(String(255))
    original_filename = Column(String(255))
    file_type = Column(String(10))  # pdf, docx, txt, etc.
    file_size = Column(BigInteger)
    file_hash = Column(String(64))  # SHA-256 hash
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, error
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    
    # Content
    extracted_text = Column(Text)
    processed_content = Column(Text)
    
    # Clinical data
    patient_id_extracted = Column(String(100))
    document_type = Column(String(100))  # discharge_summary, lab_report, etc.
    clinical_entities_extracted = Column(JSON)
    
    # PHI handling
    contains_phi = Column(Boolean, default=False)
    phi_redacted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    analyses = relationship("DocumentAnalysis", back_populates="document")

class DocumentAnalysis(Base):
    """AI analysis results for clinical documents"""
    __tablename__ = "document_analyses"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("clinical_documents.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    
    # Analysis details
    analysis_type = Column(SQLEnum(AnalysisType))
    provider = Column(SQLEnum(ProviderType))
    model_name = Column(String(100))
    
    # Results
    summary = Column(Text)
    key_findings = Column(JSON)
    recommendations = Column(JSON)
    confidence_score = Column(Float)
    
    # Clinical insights
    diagnoses_mentioned = Column(JSON)
    medications_mentioned = Column(JSON)
    procedures_mentioned = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    document = relationship("ClinicalDocument", back_populates="analyses")

# Analytics and Performance Tracking
class ProviderMetrics(Base):
    """Performance metrics for AI providers"""
    __tablename__ = "provider_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Provider info
    provider = Column(SQLEnum(ProviderType), nullable=False)
    model_name = Column(String(100), nullable=False)
    operation_type = Column(String(50))  # analyze, summarize, extract, etc.
    
    # Performance data
    request_count = Column(Integer, default=1)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Timing metrics
    avg_processing_time = Column(Float)
    min_processing_time = Column(Float)
    max_processing_time = Column(Float)
    total_processing_time = Column(Float)
    
    # Token usage
    total_tokens_input = Column(BigInteger, default=0)
    total_tokens_output = Column(BigInteger, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Quality metrics
    avg_confidence_score = Column(Float)
    
    # Time period
    date_hour = Column(DateTime(timezone=True))  # Hourly aggregation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_provider_metrics_provider_date', 'provider', 'date_hour'),
        Index('idx_provider_metrics_model_operation', 'model_name', 'operation_type'),
        UniqueConstraint('provider', 'model_name', 'operation_type', 'date_hour', 
                        name='uq_provider_metrics_hourly'),
    )

class SystemUsage(Base):
    """System usage statistics"""
    __tablename__ = "system_usage"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Usage data
    total_conversations = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    active_users_daily = Column(Integer, default=0)
    total_documents_processed = Column(Integer, default=0)
    
    # Provider usage
    gemini_requests = Column(Integer, default=0)
    groq_requests = Column(Integer, default=0)
    fusion_requests = Column(Integer, default=0)
    
    # Clinical analysis breakdown
    emergency_assessments = Column(Integer, default=0)
    diagnostic_analyses = Column(Integer, default=0)
    triage_requests = Column(Integer, default=0)
    
    # Performance summary
    avg_response_time = Column(Float)
    system_uptime_hours = Column(Float)
    
    # Date
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_system_usage_date', 'date'),
        UniqueConstraint('date', name='uq_system_usage_daily'),
    )

# Audit and Compliance
class AuditLog(Base):
    """Audit trail for compliance and security"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User and session
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(36), nullable=True)
    ip_address = Column(String(45))
    
    # Action details
    action_type = Column(String(50), nullable=False)  # login, analyze, export, etc.
    resource_type = Column(String(50))  # conversation, document, user, etc.
    resource_id = Column(String(36))
    
    # Request details
    endpoint = Column(String(200))
    method = Column(String(10))
    user_agent = Column(Text)
    
    # Results
    success = Column(Boolean)
    response_code = Column(Integer)
    error_message = Column(Text)
    
    # PHI handling
    contains_phi = Column(Boolean, default=False)
    phi_access_justified = Column(Boolean, default=True)
    
    # Additional details
    audit_details = Column(JSON, default=dict)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action_type', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

# Configuration and Feature Flags
class SystemConfiguration(Base):
    """System configuration and feature flags"""
    __tablename__ = "system_configuration"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Configuration
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(20), default="string")  # string, boolean, integer, json
    description = Column(Text)
    
    # Configuration metadata
    category = Column(String(50))  # ai_providers, security, features, etc.
    is_active = Column(Boolean, default=True)
    is_sensitive = Column(Boolean, default=False)  # Don't log sensitive configs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_config_category', 'category'),
        Index('idx_system_config_active', 'is_active'),
    )