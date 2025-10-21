"""
Integrated Improvements System for ClinChat-RAG
Brings together metadata filtering, scalable vector databases, cross-encoder reranking, and user feedback
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import time
from datetime import datetime

# Import improvement modules
from .metadata_filters import MetadataFilter, metadata_filter_engine, CommonFilterPresets
from .scalable_vectordb import (
    VectorDatabaseManager, VectorDatabaseConfig, VectorSearchResult,
    OPENSEARCH_CONFIG, PINECONE_CONFIG
)
from .cross_encoder_rerank import (
    RerankingManager, RerankingConfig, RerankingResult,
    MEDICAL_RERANKING_CONFIG
)
from .user_feedback import FeedbackManager, FeedbackType, FeedbackEntry

@dataclass
class EnhancedSearchConfig:
    """Configuration for the enhanced search system"""
    # Vector database settings
    vector_db_type: str = "opensearch"  # "opensearch", "pinecone", "faiss"
    vector_db_config: Optional[VectorDatabaseConfig] = None
    
    # Reranking settings
    enable_reranking: bool = True
    reranking_config: Optional[RerankingConfig] = None
    
    # Metadata filtering
    enable_metadata_filtering: bool = True
    default_filters: Optional[MetadataFilter] = None
    
    # User feedback
    enable_feedback_collection: bool = True
    feedback_db_path: str = "data/feedback.db"
    
    # Performance settings
    max_candidates: int = 100
    final_top_k: int = 10
    timeout_seconds: int = 30

@dataclass 
class EnhancedSearchResult:
    """Enhanced search result with all improvement features"""
    doc_id: str
    content: str
    
    # Scoring information
    semantic_score: float
    rerank_score: Optional[float]
    final_score: float
    confidence: float
    
    # Metadata and context
    metadata: Dict[str, Any]
    source_info: Dict[str, Any]
    
    # Performance metrics
    retrieval_time: float
    rerank_time: Optional[float] = None

class EnhancedRAGSystem:
    """Enhanced RAG system with all improvements integrated"""
    
    def __init__(self, config: EnhancedSearchConfig):
        self.config = config
        
        # Initialize components
        self.vector_db = VectorDatabaseManager()
        self.reranker = RerankingManager() if config.enable_reranking else None
        self.feedback_manager = FeedbackManager(config.feedback_db_path) if config.enable_feedback_collection else None
        
        # State tracking
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("Initializing enhanced RAG system...")
            
            # Initialize vector database
            vector_config = self.config.vector_db_config or self._get_default_vector_config()
            if not await self.vector_db.initialize(vector_config):
                self.logger.error("Failed to initialize vector database")
                return False
            
            # Initialize reranker if enabled
            if self.reranker:
                rerank_config = self.config.reranking_config or MEDICAL_RERANKING_CONFIG
                if not await self.reranker.initialize(rerank_config):
                    self.logger.error("Failed to initialize reranker")
                    return False
            
            self.is_initialized = True
            self.logger.info("Enhanced RAG system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced RAG system: {e}")
            return False
    
    def _get_default_vector_config(self) -> VectorDatabaseConfig:
        """Get default vector database configuration"""
        if self.config.vector_db_type == "opensearch":
            return OPENSEARCH_CONFIG
        elif self.config.vector_db_type == "pinecone":
            return PINECONE_CONFIG
        else:
            # Fallback to OpenSearch
            return OPENSEARCH_CONFIG
    
    async def enhanced_search(self, 
                            query: str,
                            query_vector: List[float],
                            filters: Optional[MetadataFilter] = None,
                            domain_context: Optional[str] = None,
                            session_id: Optional[str] = None,
                            user_id: Optional[str] = None) -> Tuple[List[EnhancedSearchResult], Dict[str, Any]]:
        """
        Perform enhanced search with all improvements
        
        Returns:
            Tuple of (search_results, performance_metrics)
        """
        if not self.is_initialized:
            raise RuntimeError("Enhanced RAG system not initialized")
        
        start_time = time.time()
        performance_metrics = {
            "total_time": 0.0,
            "retrieval_time": 0.0,
            "filtering_time": 0.0,
            "reranking_time": 0.0,
            "candidates_retrieved": 0,
            "candidates_after_filtering": 0,
            "final_results": 0
        }
        
        try:
            # Step 1: Vector similarity search
            retrieval_start = time.time()
            
            # Apply metadata filtering if enabled and filters provided
            search_filters = filters or self.config.default_filters
            
            # Get initial candidates from vector database
            vector_results = await self.vector_db.search(
                query_vector=query_vector,
                filters=search_filters,
                top_k=self.config.max_candidates
            )
            
            performance_metrics["retrieval_time"] = time.time() - retrieval_start
            performance_metrics["candidates_retrieved"] = len(vector_results)
            
            if not vector_results:
                self.logger.warning(f"No results found for query: {query[:50]}...")
                return [], performance_metrics
            
            # Step 2: Additional metadata filtering if enabled
            filtering_start = time.time()
            
            if self.config.enable_metadata_filtering and search_filters:
                # Convert vector results to format for metadata filtering
                candidates_for_filtering = [
                    {
                        "doc_id": result.doc_id,
                        "content": result.content,
                        "score": result.score,
                        "metadata": result.metadata
                    }
                    for result in vector_results
                ]
                
                # Apply metadata filtering engine
                filtered_candidates = metadata_filter_engine.apply_filters(
                    candidates_for_filtering, 
                    search_filters
                )
            else:
                filtered_candidates = [
                    {
                        "doc_id": result.doc_id,
                        "content": result.content,
                        "score": result.score,
                        "metadata": result.metadata
                    }
                    for result in vector_results
                ]
            
            performance_metrics["filtering_time"] = time.time() - filtering_start
            performance_metrics["candidates_after_filtering"] = len(filtered_candidates)
            
            # Step 3: Cross-encoder reranking if enabled
            reranking_start = time.time()
            
            if self.reranker and filtered_candidates:
                reranked_results = await self.reranker.rerank_results(
                    query=query,
                    candidates=filtered_candidates,
                    domain_context=domain_context
                )
                
                performance_metrics["reranking_time"] = time.time() - reranking_start
                
                # Convert reranked results to enhanced format
                enhanced_results = []
                for result in reranked_results:
                    enhanced_result = EnhancedSearchResult(
                        doc_id=result.doc_id,
                        content=result.content,
                        semantic_score=result.original_score,
                        rerank_score=result.rerank_score,
                        final_score=result.final_score,
                        confidence=result.confidence,
                        metadata=result.metadata,
                        source_info={
                            "retrieval_method": "vector_similarity",
                            "reranked": True,
                            "domain_context": domain_context
                        },
                        retrieval_time=performance_metrics["retrieval_time"],
                        rerank_time=performance_metrics["reranking_time"]
                    )
                    enhanced_results.append(enhanced_result)
            
            else:
                # No reranking - use filtered results directly
                performance_metrics["reranking_time"] = time.time() - reranking_start
                
                enhanced_results = []
                for i, candidate in enumerate(filtered_candidates[:self.config.final_top_k]):
                    enhanced_result = EnhancedSearchResult(
                        doc_id=candidate["doc_id"],
                        content=candidate["content"],
                        semantic_score=candidate["score"],
                        rerank_score=None,
                        final_score=candidate["score"],
                        confidence=min(candidate["score"], 1.0),
                        metadata=candidate["metadata"],
                        source_info={
                            "retrieval_method": "vector_similarity",
                            "reranked": False,
                            "domain_context": domain_context
                        },
                        retrieval_time=performance_metrics["retrieval_time"]
                    )
                    enhanced_results.append(enhanced_result)
            
            # Final metrics
            performance_metrics["final_results"] = len(enhanced_results)
            performance_metrics["total_time"] = time.time() - start_time
            
            self.logger.info(
                f"Enhanced search completed: {performance_metrics['candidates_retrieved']} → "
                f"{performance_metrics['candidates_after_filtering']} → {performance_metrics['final_results']} "
                f"(total: {performance_metrics['total_time']:.3f}s)"
            )
            
            return enhanced_results, performance_metrics
            
        except Exception as e:
            self.logger.error(f"Enhanced search failed: {e}")
            performance_metrics["total_time"] = time.time() - start_time
            return [], performance_metrics
    
    async def collect_user_feedback(self, 
                                  feedback_data: Dict[str, Any]) -> Optional[str]:
        """Collect user feedback for continuous improvement"""
        if not self.feedback_manager:
            self.logger.warning("Feedback collection not enabled")
            return None
        
        try:
            feedback_id = await self.feedback_manager.collect_feedback(feedback_data)
            self.logger.info(f"Collected user feedback: {feedback_id}")
            return feedback_id
            
        except Exception as e:
            self.logger.error(f"Failed to collect feedback: {e}")
            return None
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Get comprehensive system analytics"""
        analytics = {
            "system_status": "initialized" if self.is_initialized else "not_initialized",
            "configuration": {
                "vector_db_type": self.config.vector_db_type,
                "reranking_enabled": self.config.enable_reranking,
                "metadata_filtering_enabled": self.config.enable_metadata_filtering,
                "feedback_collection_enabled": self.config.enable_feedback_collection
            }
        }
        
        # Add vector database stats
        if self.is_initialized:
            try:
                vector_stats = asyncio.create_task(self.vector_db.get_stats())
                analytics["vector_database"] = vector_stats
            except Exception as e:
                analytics["vector_database"] = {"error": str(e)}
        
        # Add reranking stats
        if self.reranker:
            analytics["reranking"] = self.reranker.get_reranking_stats()
        
        # Add feedback stats
        if self.feedback_manager:
            try:
                feedback_analytics = self.feedback_manager.get_analytics()
                analytics["feedback"] = {
                    "total_feedback": feedback_analytics.total_feedback,
                    "positive_feedback": feedback_analytics.positive_feedback,
                    "negative_feedback": feedback_analytics.negative_feedback,
                    "average_rating": feedback_analytics.average_rating,
                    "feedback_last_24h": feedback_analytics.feedback_last_24h,
                    "critical_issues": feedback_analytics.critical_issues,
                    "unique_users": feedback_analytics.unique_users
                }
            except Exception as e:
                analytics["feedback"] = {"error": str(e)}
        
        return analytics
    
    async def get_preset_filters(self, preset_name: str) -> Optional[MetadataFilter]:
        """Get predefined filter presets for common use cases"""
        preset_filters = {
            "oncology_trials_phase_3": CommonFilterPresets.oncology_trials_phase_3(),
            "recent_cardiology_guidelines": CommonFilterPresets.recent_cardiology_guidelines(),
            "fda_approved_drugs": CommonFilterPresets.fda_approved_drugs(),
            "high_quality_rcts": CommonFilterPresets.high_quality_rcts()
        }
        
        return preset_filters.get(preset_name)
    
    async def update_vector_database(self, 
                                   documents: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """Update vector database with new documents"""
        if not self.is_initialized:
            raise RuntimeError("System not initialized")
        
        try:
            success = await self.vector_db.upsert(documents)
            self.logger.info(f"Updated vector database with {len(documents)} documents")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update vector database: {e}")
            return False
    
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from vector database"""
        if not self.is_initialized:
            raise RuntimeError("System not initialized")
        
        try:
            success = await self.vector_db.delete(doc_ids)
            self.logger.info(f"Deleted {len(doc_ids)} documents from vector database")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            return False

# Convenience function to create system with default configuration
def create_enhanced_rag_system(vector_db_type: str = "opensearch",
                             enable_reranking: bool = True,
                             enable_feedback: bool = True) -> EnhancedRAGSystem:
    """Create enhanced RAG system with default configuration"""
    
    config = EnhancedSearchConfig(
        vector_db_type=vector_db_type,
        enable_reranking=enable_reranking,
        enable_metadata_filtering=True,
        enable_feedback_collection=enable_feedback,
        reranking_config=MEDICAL_RERANKING_CONFIG if enable_reranking else None
    )
    
    return EnhancedRAGSystem(config)

# Example usage configurations
CLINICAL_RESEARCH_CONFIG = EnhancedSearchConfig(
    vector_db_type="opensearch",
    enable_reranking=True,
    enable_metadata_filtering=True,
    enable_feedback_collection=True,
    reranking_config=RerankingConfig(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        high_confidence_threshold=0.9,
        medium_confidence_threshold=0.75,
        semantic_weight=0.5,
        rerank_weight=0.5,
        max_candidates=100,
        top_k=15
    ),
    max_candidates=100,
    final_top_k=15
)

GENERAL_MEDICAL_CONFIG = EnhancedSearchConfig(
    vector_db_type="opensearch", 
    enable_reranking=True,
    enable_metadata_filtering=True,
    enable_feedback_collection=True,
    reranking_config=MEDICAL_RERANKING_CONFIG,
    max_candidates=50,
    final_top_k=10
)

# Export main components
__all__ = [
    'EnhancedRAGSystem',
    'EnhancedSearchConfig',
    'EnhancedSearchResult', 
    'create_enhanced_rag_system',
    'CLINICAL_RESEARCH_CONFIG',
    'GENERAL_MEDICAL_CONFIG'
]