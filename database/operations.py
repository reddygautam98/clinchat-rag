"""
Database Utilities and Helper Functions
Unified database operations for both Google Gemini and Groq APIs
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from database.connection import get_db_context, ai_logger
from database.models import (
    User, Conversation, ProviderResponse, ClinicalDocument,
    DocumentAnalysis, ProviderMetrics, SystemUsage, AuditLog,
    ProviderType, AnalysisType, UrgencyLevel, FusionStrategy
)

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manager for conversation database operations"""
    
    @staticmethod
    def create_conversation(
        session: Session,
        input_text: str,
        analysis_type: AnalysisType = AnalysisType.GENERAL,
        urgency_level: UrgencyLevel = UrgencyLevel.NORMAL,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Conversation:
        """Create a new conversation record"""
        try:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                input_text=input_text,
                analysis_type=analysis_type,
                urgency_level=urgency_level,
                metadata=metadata or {}
            )
            
            session.add(conversation)
            session.flush()  # Get the ID without committing
            
            logger.info(f"📝 Created conversation: {conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    @staticmethod
    def update_conversation_results(
        session: Session,
        conversation_id: str,
        final_analysis: str,
        confidence_score: float,
        processing_time_total: float,
        fusion_strategy: Optional[FusionStrategy] = None,
        primary_provider: Optional[ProviderType] = None,
        secondary_provider: Optional[ProviderType] = None,
        clinical_entities: Optional[Dict] = None
    ) -> bool:
        """Update conversation with final results"""
        try:
            conversation = session.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return False
            
            # Update results
            conversation.final_analysis = final_analysis
            conversation.confidence_score = confidence_score
            conversation.processing_time_total = processing_time_total
            conversation.fusion_strategy = fusion_strategy
            conversation.primary_provider = primary_provider
            conversation.secondary_provider = secondary_provider
            conversation.clinical_entities = clinical_entities
            conversation.completed_at = datetime.now(timezone.utc)
            
            session.flush()
            
            logger.info(f"✅ Updated conversation results: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update conversation: {e}")
            raise
    
    @staticmethod
    def get_conversation_history(
        session: Session,
        user_id: Optional[str] = None,
        limit: int = 50,
        analysis_type: Optional[AnalysisType] = None
    ) -> List[Conversation]:
        """Get conversation history for a user"""
        try:
            query = session.query(Conversation)
            
            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            
            if analysis_type:
                query = query.filter(Conversation.analysis_type == analysis_type)
            
            conversations = query.order_by(
                desc(Conversation.created_at)
            ).limit(limit).all()
            
            logger.info(f"📋 Retrieved {len(conversations)} conversations")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise

class ProviderResponseManager:
    """Manager for AI provider response operations"""
    
    @staticmethod
    def log_provider_response(
        session: Session,
        conversation_id: str,
        provider: ProviderType,
        model_name: str,
        request_payload: Dict,
        response_text: str,
        processing_time: float,
        success: bool = True,
        error_message: Optional[str] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        cost_total: Optional[float] = None,
        response_metadata: Optional[Dict] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> ProviderResponse:
        """Log AI provider response"""
        try:
            provider_response = ProviderResponse(
                conversation_id=conversation_id,
                provider=provider,
                model_name=model_name,
                request_payload=request_payload,
                response_text=response_text,
                response_metadata=response_metadata or {},
                processing_time=processing_time,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=(tokens_input or 0) + (tokens_output or 0),
                cost_total=cost_total,
                success=success,
                error_message=error_message,
                started_at=started_at or datetime.now(timezone.utc),
                completed_at=completed_at or datetime.now(timezone.utc)
            )
            
            session.add(provider_response)
            session.flush()
            
            logger.info(f"🤖 Logged {provider.value} response: {provider_response.id}")
            return provider_response
            
        except Exception as e:
            logger.error(f"Failed to log provider response: {e}")
            raise
    
    @staticmethod
    def get_provider_performance(
        session: Session,
        provider: ProviderType,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get provider performance metrics"""
        try:
            cutoff_time = datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            ) - timezone.timedelta(hours=hours)
            
            # Query performance data
            responses = session.query(ProviderResponse).filter(
                and_(
                    ProviderResponse.provider == provider,
                    ProviderResponse.created_at >= cutoff_time
                )
            ).all()
            
            if not responses:
                return {
                    "provider": provider.value,
                    "total_requests": 0,
                    "success_rate": 0.0,
                    "avg_processing_time": 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            
            # Calculate metrics
            total_requests = len(responses)
            successful_requests = sum(1 for r in responses if r.success)
            success_rate = successful_requests / total_requests
            
            processing_times = [r.processing_time for r in responses if r.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            total_tokens = sum(r.tokens_total or 0 for r in responses)
            total_cost = sum(r.cost_total or 0 for r in responses)
            
            return {
                "provider": provider.value,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "avg_processing_time": avg_processing_time,
                "min_processing_time": min(processing_times) if processing_times else 0,
                "max_processing_time": max(processing_times) if processing_times else 0,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "time_period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get provider performance: {e}")
            raise

class ClinicalDocumentManager:
    """Manager for clinical document operations"""
    
    @staticmethod
    def create_document(
        session: Session,
        filename: str,
        file_type: str,
        file_size: int,
        file_hash: str,
        extracted_text: str,
        user_id: Optional[str] = None,
        original_filename: Optional[str] = None
    ) -> ClinicalDocument:
        """Create a new clinical document record"""
        try:
            document = ClinicalDocument(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename or filename,
                file_type=file_type,
                file_size=file_size,
                file_hash=file_hash,
                extracted_text=extracted_text,
                status="uploaded"
            )
            
            session.add(document)
            session.flush()
            
            logger.info(f"📄 Created clinical document: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to create clinical document: {e}")
            raise
    
    @staticmethod
    def log_document_analysis(
        session: Session,
        document_id: str,
        analysis_type: AnalysisType,
        provider: ProviderType,
        model_name: str,
        summary: str,
        key_findings: Dict,
        recommendations: Dict,
        confidence_score: float,
        conversation_id: Optional[str] = None
    ) -> DocumentAnalysis:
        """Log analysis results for a clinical document"""
        try:
            analysis = DocumentAnalysis(
                document_id=document_id,
                conversation_id=conversation_id,
                analysis_type=analysis_type,
                provider=provider,
                model_name=model_name,
                summary=summary,
                key_findings=key_findings,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
            session.add(analysis)
            session.flush()
            
            logger.info(f"📊 Logged document analysis: {analysis.id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to log document analysis: {e}")
            raise

class AnalyticsManager:
    """Manager for analytics and metrics operations"""
    
    @staticmethod
    def update_hourly_metrics(
        session: Session,
        provider: ProviderType,
        model_name: str,
        operation_type: str,
        processing_time: float,
        success: bool,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost: float = 0.0,
        confidence_score: Optional[float] = None
    ) -> None:
        """Update hourly aggregated metrics"""
        try:
            current_hour = datetime.now(timezone.utc).replace(
                minute=0, second=0, microsecond=0
            )
            
            # Get or create metrics record for this hour
            metrics = session.query(ProviderMetrics).filter(
                and_(
                    ProviderMetrics.provider == provider,
                    ProviderMetrics.model_name == model_name,
                    ProviderMetrics.operation_type == operation_type,
                    ProviderMetrics.date_hour == current_hour
                )
            ).first()
            
            if not metrics:
                # Create new metrics record
                metrics = ProviderMetrics(
                    provider=provider,
                    model_name=model_name,
                    operation_type=operation_type,
                    date_hour=current_hour,
                    request_count=0,
                    success_count=0,
                    error_count=0,
                    total_processing_time=0.0,
                    total_tokens_input=0,
                    total_tokens_output=0,
                    total_cost=0.0
                )
                session.add(metrics)
            
            # Update metrics
            metrics.request_count += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1
            
            # Update timing
            metrics.total_processing_time += processing_time
            metrics.avg_processing_time = metrics.total_processing_time / metrics.request_count
            
            # Update min/max processing time
            if not metrics.min_processing_time or processing_time < metrics.min_processing_time:
                metrics.min_processing_time = processing_time
            if not metrics.max_processing_time or processing_time > metrics.max_processing_time:
                metrics.max_processing_time = processing_time
            
            # Update token usage
            metrics.total_tokens_input += tokens_input
            metrics.total_tokens_output += tokens_output
            metrics.total_cost += cost
            
            # Update confidence score
            if confidence_score is not None:
                if metrics.avg_confidence_score:
                    # Calculate running average
                    total_confidence = metrics.avg_confidence_score * (metrics.request_count - 1) + confidence_score
                    metrics.avg_confidence_score = total_confidence / metrics.request_count
                else:
                    metrics.avg_confidence_score = confidence_score
            
            session.flush()
            
            logger.debug(f"📈 Updated hourly metrics: {provider.value} - {operation_type}")
            
        except Exception as e:
            logger.error(f"Failed to update hourly metrics: {e}")
            raise
    
    @staticmethod
    def get_system_analytics(
        session: Session,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get comprehensive system analytics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)
            
            # Conversation analytics
            total_conversations = session.query(Conversation).filter(
                Conversation.created_at >= cutoff_date
            ).count()
            
            # Provider usage
            provider_usage = session.query(
                ProviderResponse.provider,
                func.count(ProviderResponse.id).label('count')
            ).filter(
                ProviderResponse.created_at >= cutoff_date
            ).group_by(ProviderResponse.provider).all()
            
            # Analysis type breakdown
            analysis_breakdown = session.query(
                Conversation.analysis_type,
                func.count(Conversation.id).label('count')
            ).filter(
                Conversation.created_at >= cutoff_date
            ).group_by(Conversation.analysis_type).all()
            
            # Performance metrics
            avg_processing_time = session.query(
                func.avg(Conversation.processing_time_total)
            ).filter(
                and_(
                    Conversation.created_at >= cutoff_date,
                    Conversation.processing_time_total.isnot(None)
                )
            ).scalar() or 0.0
            
            # Success rates
            total_responses = session.query(ProviderResponse).filter(
                ProviderResponse.created_at >= cutoff_date
            ).count()
            
            successful_responses = session.query(ProviderResponse).filter(
                and_(
                    ProviderResponse.created_at >= cutoff_date,
                    ProviderResponse.success == True
                )
            ).count()
            
            success_rate = successful_responses / total_responses if total_responses > 0 else 0.0
            
            return {
                "time_period_days": days,
                "total_conversations": total_conversations,
                "provider_usage": {
                    usage.provider.value: usage.count for usage in provider_usage
                },
                "analysis_breakdown": {
                    analysis.analysis_type.value: analysis.count for analysis in analysis_breakdown
                },
                "performance": {
                    "avg_processing_time": avg_processing_time,
                    "total_responses": total_responses,
                    "successful_responses": successful_responses,
                    "success_rate": success_rate
                },
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            raise

class AuditManager:
    """Manager for audit logging and compliance"""
    
    @staticmethod
    def log_action(
        session: Session,
        action_type: str,
        success: bool,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        response_code: Optional[int] = None,
        error_message: Optional[str] = None,
        contains_phi: bool = False,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """Log an action for audit trail"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=endpoint,
                method=method,
                success=success,
                response_code=response_code,
                error_message=error_message,
                contains_phi=contains_phi,
                details=details or {}
            )
            
            session.add(audit_log)
            session.flush()
            
            logger.info(f"🔍 Audit logged: {action_type} - {'✅' if success else '❌'}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            raise

# Convenience functions for common operations
def log_fusion_conversation(
    input_text: str,
    final_analysis: str,
    confidence_score: float,
    processing_time_total: float,
    fusion_strategy: FusionStrategy,
    primary_provider: ProviderType,
    gemini_response: Optional[Dict] = None,
    groq_response: Optional[Dict] = None,
    analysis_type: AnalysisType = AnalysisType.GENERAL,
    urgency_level: UrgencyLevel = UrgencyLevel.NORMAL,
    user_id: Optional[str] = None,
    clinical_entities: Optional[Dict] = None
) -> str:
    """
    Log a complete fusion AI conversation with provider responses
    Returns conversation ID
    """
    try:
        with get_db_context() as session:
            # Create conversation
            conversation = ConversationManager.create_conversation(
                session=session,
                input_text=input_text,
                analysis_type=analysis_type,
                urgency_level=urgency_level,
                user_id=user_id
            )
            
            # Log Gemini response if available
            if gemini_response:
                ProviderResponseManager.log_provider_response(
                    session=session,
                    conversation_id=conversation.id,
                    provider=ProviderType.GOOGLE_GEMINI,
                    **gemini_response
                )
            
            # Log Groq response if available
            if groq_response:
                ProviderResponseManager.log_provider_response(
                    session=session,
                    conversation_id=conversation.id,
                    provider=ProviderType.GROQ,
                    **groq_response
                )
            
            # Update conversation with final results
            ConversationManager.update_conversation_results(
                session=session,
                conversation_id=conversation.id,
                final_analysis=final_analysis,
                confidence_score=confidence_score,
                processing_time_total=processing_time_total,
                fusion_strategy=fusion_strategy,
                primary_provider=primary_provider,
                clinical_entities=clinical_entities
            )
            
            logger.info(f"🔮 Fusion conversation logged: {conversation.id}")
            return conversation.id
            
    except Exception as e:
        logger.error(f"Failed to log fusion conversation: {e}")
        raise