"""
Hybrid Search Manager
Combines vector search with BM25 and cross-encoder reranking for improved precision and recall
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .bm25_reranker import BM25Reranker
from .cross_encoder_reranker import SimpleCrossEncoderReranker, RerankingConfig

logger = logging.getLogger(__name__)

class RerankingMethod(Enum):
    """Available reranking methods"""
    BM25_ONLY = "bm25_only"
    CROSS_ENCODER_ONLY = "cross_encoder_only"
    HYBRID_BM25_CE = "hybrid_bm25_ce"
    VECTOR_BM25 = "vector_bm25"
    VECTOR_CE = "vector_ce"
    FULL_HYBRID = "full_hybrid"

@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search"""
    method: RerankingMethod = RerankingMethod.HYBRID_BM25_CE
    bm25_weight: float = 0.3
    cross_encoder_weight: float = 0.4
    vector_weight: float = 0.3
    top_k_retrieval: int = 20
    final_top_k: int = 5
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    score_threshold: float = 0.1
    
    def __post_init__(self):
        """Validate configuration"""
        total_weight = self.bm25_weight + self.cross_encoder_weight + self.vector_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.bm25_weight /= total_weight
            self.cross_encoder_weight /= total_weight
            self.vector_weight /= total_weight

class HybridSearchManager:
    """
    Manages hybrid search combining vector retrieval with multiple reranking methods
    Pipeline: metadata filtering -> vector retrieval -> reranking
    """
    
    def __init__(self, config: Optional[HybridSearchConfig] = None):
        """
        Initialize hybrid search manager
        
        Args:
            config: Configuration for hybrid search
        """
        self.config = config or HybridSearchConfig()
        self.bm25_reranker = None
        self.cross_encoder_reranker = None
        self._initialize_rerankers()
        
    def _initialize_rerankers(self):
        """Initialize reranking components"""
        # Initialize BM25 reranker
        if self.config.method in [
            RerankingMethod.BM25_ONLY,
            RerankingMethod.HYBRID_BM25_CE,
            RerankingMethod.VECTOR_BM25,
            RerankingMethod.FULL_HYBRID
        ]:
            self.bm25_reranker = BM25Reranker()
            logger.info("Initialized BM25 reranker")
        
        # Initialize cross-encoder reranker
        if self.config.method in [
            RerankingMethod.CROSS_ENCODER_ONLY,
            RerankingMethod.HYBRID_BM25_CE,
            RerankingMethod.VECTOR_CE,
            RerankingMethod.FULL_HYBRID
        ]:
            ce_config = RerankingConfig(
                weight_vector=self.config.vector_weight,
                weight_cross_encoder=self.config.cross_encoder_weight
            )
            self.cross_encoder_reranker = SimpleCrossEncoderReranker(ce_config)
            logger.info("Initialized cross-encoder reranker")
    
    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build search index for documents
        
        Args:
            documents: List of documents with content and metadata
        """
        if self.bm25_reranker:
            # Extract content for BM25 indexing
            content_list = [doc.get('content', '') for doc in documents]
            self.bm25_reranker.build_index(content_list)
            logger.info(f"Built BM25 index for {len(documents)} documents")
    
    def apply_metadata_filters(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply metadata filtering to documents
        
        Args:
            documents: List of documents to filter
            
        Returns:
            Filtered list of documents
        """
        if not self.config.metadata_filters:
            return documents
        
        filtered_docs = []
        for doc in documents:
            if self._document_passes_filters(doc):
                filtered_docs.append(doc)
        
        logger.info(f"Metadata filtering: {len(documents)} -> {len(filtered_docs)} documents")
        return filtered_docs
    
    def _document_passes_filters(self, doc: Dict[str, Any]) -> bool:
        """Check if a document passes all metadata filters"""
        metadata = doc.get('metadata', {})
        
        for filter_key, filter_value in self.config.metadata_filters.items():
            if isinstance(filter_value, list):
                # Multiple allowed values
                if metadata.get(filter_key) not in filter_value:
                    return False
            else:
                # Single value
                if metadata.get(filter_key) != filter_value:
                    return False
        
        return True
    
    def hybrid_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search with reranking
        
        Args:
            query: Search query
            documents: List of candidate documents from vector search
            top_k: Number of results to return (defaults to config)
            
        Returns:
            Reranked list of documents with hybrid scores
        """
        if not documents:
            return []
        
        final_top_k = top_k or self.config.final_top_k
        
        # Step 1: Apply metadata filters
        filtered_docs = self.apply_metadata_filters(documents)
        if not filtered_docs:
            logger.warning("No documents passed metadata filtering")
            return []
        
        # Step 2: Limit to top_k_retrieval for efficiency
        retrieval_docs = filtered_docs[:self.config.top_k_retrieval]
        
        # Step 3: Apply reranking based on method
        reranked_docs = self._apply_reranking(query, retrieval_docs)
        
        # Step 4: Filter by score threshold
        high_quality_docs = [
            doc for doc in reranked_docs
            if doc.get('final_score', 0) >= self.config.score_threshold
        ]
        
        # Step 5: Return final top_k
        final_results = high_quality_docs[:final_top_k]
        
        logger.info(f"Hybrid search: {len(documents)} -> {len(filtered_docs)} -> "
                   f"{len(retrieval_docs)} -> {len(high_quality_docs)} -> {len(final_results)}")
        
        return final_results
    
    def _apply_reranking(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply reranking based on configured method"""
        
        if self.config.method == RerankingMethod.BM25_ONLY:
            return self._rerank_bm25_only(query, documents)
        
        elif self.config.method == RerankingMethod.CROSS_ENCODER_ONLY:
            return self._rerank_ce_only(query, documents)
        
        elif self.config.method == RerankingMethod.HYBRID_BM25_CE:
            return self._rerank_hybrid_bm25_ce(query, documents)
        
        elif self.config.method == RerankingMethod.VECTOR_BM25:
            return self._rerank_vector_bm25(query, documents)
        
        elif self.config.method == RerankingMethod.VECTOR_CE:
            return self._rerank_vector_ce(query, documents)
        
        elif self.config.method == RerankingMethod.FULL_HYBRID:
            return self._rerank_full_hybrid(query, documents)
        
        else:
            logger.error(f"Unknown reranking method: {self.config.method}")
            return documents
    
    def _rerank_bm25_only(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using BM25 only"""
        if not self.bm25_reranker:
            return documents
        
        reranked = self.bm25_reranker.rerank(query, documents)
        for doc in reranked:
            doc['final_score'] = doc.get('bm25_score', 0)
            doc['reranking_method'] = 'bm25_only'
        
        return reranked
    
    def _rerank_ce_only(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using cross-encoder only"""
        if not self.cross_encoder_reranker:
            return documents
        
        reranked = self.cross_encoder_reranker.rerank(query, documents)
        for doc in reranked:
            doc['final_score'] = doc.get('cross_encoder_score', 0)
            doc['reranking_method'] = 'cross_encoder_only'
        
        return reranked
    
    def _rerank_hybrid_bm25_ce(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using BM25 + Cross-encoder hybrid"""
        if not self.bm25_reranker or not self.cross_encoder_reranker:
            return documents
        
        # Apply BM25 first
        bm25_docs = self.bm25_reranker.rerank(query, documents)
        
        # Then apply cross-encoder
        final_docs = self.cross_encoder_reranker.rerank(query, bm25_docs)
        
        # Combine scores
        for doc in final_docs:
            bm25_score = doc.get('bm25_score', 0)
            ce_score = doc.get('cross_encoder_score', 0)
            
            final_score = (self.config.bm25_weight * bm25_score + 
                          self.config.cross_encoder_weight * ce_score)
            
            doc['final_score'] = final_score
            doc['reranking_method'] = 'hybrid_bm25_ce'
        
        # Re-sort by final score
        final_docs.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return final_docs
    
    def _rerank_vector_bm25(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using Vector + BM25 hybrid"""
        if not self.bm25_reranker:
            return documents
        
        reranked = self.bm25_reranker.rerank(query, documents)
        
        for doc in reranked:
            vector_score = doc.get('similarity_score', 0)
            bm25_score = doc.get('bm25_score', 0)
            
            final_score = (self.config.vector_weight * vector_score + 
                          self.config.bm25_weight * bm25_score)
            
            doc['final_score'] = final_score
            doc['reranking_method'] = 'vector_bm25'
        
        reranked.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return reranked
    
    def _rerank_vector_ce(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using Vector + Cross-encoder hybrid"""
        if not self.cross_encoder_reranker:
            return documents
        
        reranked = self.cross_encoder_reranker.rerank(query, documents)
        
        for doc in reranked:
            vector_score = doc.get('similarity_score', 0)
            ce_score = doc.get('cross_encoder_score', 0)
            
            final_score = (self.config.vector_weight * vector_score + 
                          self.config.cross_encoder_weight * ce_score)
            
            doc['final_score'] = final_score
            doc['reranking_method'] = 'vector_ce'
        
        reranked.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return reranked
    
    def _rerank_full_hybrid(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank using full hybrid: Vector + BM25 + Cross-encoder"""
        if not self.bm25_reranker or not self.cross_encoder_reranker:
            return self._rerank_vector_bm25(query, documents)
        
        # Apply BM25 first
        bm25_docs = self.bm25_reranker.rerank(query, documents)
        
        # Then apply cross-encoder
        final_docs = self.cross_encoder_reranker.rerank(query, bm25_docs)
        
        # Combine all three scores
        for doc in final_docs:
            vector_score = doc.get('similarity_score', 0)
            bm25_score = doc.get('bm25_score', 0)
            ce_score = doc.get('cross_encoder_score', 0)
            
            final_score = (self.config.vector_weight * vector_score + 
                          self.config.bm25_weight * bm25_score +
                          self.config.cross_encoder_weight * ce_score)
            
            doc['final_score'] = final_score
            doc['reranking_method'] = 'full_hybrid'
        
        # Re-sort by final score
        final_docs.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return final_docs
    
    def get_search_stats(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed statistics about search performance
        
        Args:
            query: Search query
            documents: List of documents
            
        Returns:
            Dictionary with search statistics
        """
        stats = {
            'query': query,
            'total_documents': len(documents),
            'method': self.config.method.value,
            'config': {
                'bm25_weight': self.config.bm25_weight,
                'cross_encoder_weight': self.config.cross_encoder_weight,
                'vector_weight': self.config.vector_weight,
                'top_k_retrieval': self.config.top_k_retrieval,
                'final_top_k': self.config.final_top_k,
                'score_threshold': self.config.score_threshold
            }
        }
        
        # Add reranker-specific stats
        if self.bm25_reranker and documents:
            # Use first document content for analysis
            first_content = documents[0].get('content', '')
            bm25_stats = self.bm25_reranker.get_term_scores(query, first_content)
            stats['bm25_analysis'] = bm25_stats
        
        if self.cross_encoder_reranker and documents:
            ce_explanation = self.cross_encoder_reranker.explain_ranking(
                query, documents[0].get('content', '')
            )
            stats['cross_encoder_analysis'] = ce_explanation
        
        return stats

def main():
    """Demo of hybrid search manager"""
    
    # Sample documents with vector scores
    documents = [
        {
            'doc_id': 'doc1',
            'content': 'Patient has diabetes mellitus type 2 with elevated glucose levels requiring insulin therapy and dietary modifications',
            'similarity_score': 0.8,
            'metadata': {'type': 'medical_record', 'specialty': 'endocrinology'}
        },
        {
            'doc_id': 'doc2',
            'content': 'Blood pressure readings consistently elevated indicating hypertension requiring medication adjustment',
            'similarity_score': 0.6,
            'metadata': {'type': 'medical_record', 'specialty': 'cardiology'}
        },
        {
            'doc_id': 'doc3',
            'content': 'Recent lab results show glucose levels at 180 mg/dL, HbA1c at 8.5% indicating poor diabetes control',
            'similarity_score': 0.7,
            'metadata': {'type': 'lab_result', 'specialty': 'endocrinology'}
        },
        {
            'doc_id': 'doc4',
            'content': 'Patient education provided on diabetes management, blood glucose monitoring, and medication compliance',
            'similarity_score': 0.75,
            'metadata': {'type': 'education', 'specialty': 'endocrinology'}
        }
    ]
    
    print("🔍 Hybrid Search Manager Demo")
    print("=" * 50)
    
    # Test query
    query = "diabetes glucose management treatment"
    print(f"Query: '{query}'")
    
    # Test different reranking methods
    methods = [
        RerankingMethod.BM25_ONLY,
        RerankingMethod.CROSS_ENCODER_ONLY,
        RerankingMethod.HYBRID_BM25_CE,
        RerankingMethod.FULL_HYBRID
    ]
    
    for method in methods:
        print(f"\n--- {method.value.upper()} ---")
        
        # Configure hybrid search
        config = HybridSearchConfig(
            method=method,
            bm25_weight=0.3,
            cross_encoder_weight=0.4,
            vector_weight=0.3,
            final_top_k=3,
            metadata_filters={'specialty': 'endocrinology'}  # Filter to endocrinology only
        )
        
        # Initialize manager
        manager = HybridSearchManager(config)
        manager.build_index(documents)
        
        # Perform hybrid search
        results = manager.hybrid_search(query, documents)
        
        # Display results
        for i, doc in enumerate(results):
            final_score = doc.get('final_score', 0)
            method_name = doc.get('reranking_method', 'unknown')
            print(f"{i+1}. Score: {final_score:.3f} ({method_name})")
            print(f"   {doc['content'][:80]}...")
        
        # Show search stats
        stats = manager.get_search_stats(query, documents)
        print(f"   Filtered from {stats['total_documents']} documents")

if __name__ == "__main__":
    main()