"""
BM25 Reranker Implementation
Provides BM25 scoring for hybrid search combining vector similarity with term frequency scoring
"""

import re
import math
import logging
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class BM25Reranker:
    """
    BM25 (Best Matching 25) reranker for improving search relevance
    Combines TF-IDF scoring with document length normalization
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Initialize BM25 reranker
        
        Args:
            k1: Controls term frequency normalization (typical: 1.2-2.0)
            b: Controls document length normalization (typical: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_freqs = defaultdict(int)  # Document frequency for each term
        self.idf_cache = {}  # Cached IDF values
        self.doc_lens = []  # Length of each document
        self.avgdl = 0  # Average document length
        self.N = 0  # Total number of documents
        
    def build_index(self, documents: List[str]) -> None:
        """
        Build BM25 index from document corpus
        
        Args:
            documents: List of document texts to index
        """
        self.corpus = documents
        self.N = len(documents)
        self.doc_lens = []
        self.doc_freqs = defaultdict(int)
        
        # Process each document
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lens.append(len(tokens))
            
            # Count unique terms in this document
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1
        
        # Calculate average document length
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0
        
        # Clear IDF cache
        self.idf_cache = {}
        
        logger.info(f"Built BM25 index for {self.N} documents, avgdl={self.avgdl:.2f}")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of lowercase tokens
        """
        # Simple tokenization - split on non-alphanumeric, keep medical terms
        text = text.lower()
        # Keep hyphens in medical terms (e.g., "anti-inflammatory")
        tokens = re.findall(r'\b[a-z]+(?:-[a-z]+)*\b', text)
        return tokens
    
    def _get_idf(self, term: str) -> float:
        """
        Calculate IDF (Inverse Document Frequency) for a term
        
        Args:
            term: The term to calculate IDF for
            
        Returns:
            IDF score for the term
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        # IDF = log((N - df(term) + 0.5) / (df(term) + 0.5))
        df = self.doc_freqs.get(term, 0)
        idf = math.log((self.N - df + 0.5) / (df + 0.5))
        self.idf_cache[term] = idf
        return idf
    
    def _get_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        Calculate BM25 score for a document given query tokens
        
        Args:
            query_tokens: Tokenized query terms
            doc_idx: Index of document in corpus
            
        Returns:
            BM25 score for the document
        """
        if doc_idx >= len(self.corpus):
            return 0.0
        
        doc = self.corpus[doc_idx]
        doc_tokens = self._tokenize(doc)
        doc_len = len(doc_tokens)
        
        # Count term frequencies in document
        doc_term_counts = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            tf = doc_term_counts.get(term, 0)
            if tf == 0:
                continue
            
            idf = self._get_idf(term)
            
            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], 
               top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Rerank documents using BM25 scoring
        
        Args:
            query: Search query
            documents: List of document dicts with 'content' field
            top_k: Number of top results to return (None for all)
            
        Returns:
            Reranked list of documents with BM25 scores
        """
        if not documents:
            return []
        
        # Extract document contents for scoring
        doc_contents = [doc.get('content', '') for doc in documents]
        
        # Build index if not already built or corpus changed
        if not self.corpus or len(self.corpus) != len(doc_contents):
            self.build_index(doc_contents)
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Score each document
        scored_docs = []
        for i, doc in enumerate(documents):
            bm25_score = self._get_score(query_tokens, i)
            
            # Add BM25 score to document
            enhanced_doc = doc.copy()
            enhanced_doc['bm25_score'] = bm25_score
            
            # Combine with existing similarity score if present
            if 'similarity_score' in doc:
                # Weighted combination (can be tuned)
                vector_weight = 0.7
                bm25_weight = 0.3
                combined_score = (vector_weight * doc['similarity_score'] + 
                                bm25_weight * bm25_score)
                enhanced_doc['combined_score'] = combined_score
                enhanced_doc['ranking_method'] = 'hybrid_vector_bm25'
            else:
                enhanced_doc['combined_score'] = bm25_score
                enhanced_doc['ranking_method'] = 'bm25_only'
            
            scored_docs.append(enhanced_doc)
        
        # Sort by combined score (higher is better)
        scored_docs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Return top_k results
        if top_k:
            scored_docs = scored_docs[:top_k]
        
        logger.info(f"Reranked {len(documents)} documents, returning top {len(scored_docs)}")
        return scored_docs
    
    def get_term_scores(self, query: str, document: str) -> Dict[str, float]:
        """
        Get per-term BM25 scores for analysis
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Dictionary mapping terms to their BM25 contributions
        """
        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(document)
        doc_term_counts = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        
        term_scores = {}
        for term in query_tokens:
            tf = doc_term_counts.get(term, 0)
            if tf == 0:
                term_scores[term] = 0.0
                continue
            
            idf = self._get_idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            
            term_scores[term] = idf * (numerator / denominator)
        
        return term_scores

def main():
    """Demo of BM25 reranker"""
    
    # Sample medical documents
    documents = [
        "Patient has diabetes mellitus type 2 with elevated glucose levels",
        "Blood pressure reading shows hypertension requiring medication",
        "Cholesterol levels are within normal range for this patient",
        "Glucose tolerance test indicates pre-diabetic condition",
        "Patient presents with chest pain and elevated blood pressure"
    ]
    
    # Sample document objects (simulating vector search results)
    doc_objects = []
    for i, content in enumerate(documents):
        doc_objects.append({
            'doc_id': f'doc_{i}',
            'content': content,
            'similarity_score': 0.8 - (i * 0.1),  # Decreasing vector scores
            'metadata': {'source': f'medical_record_{i}'}
        })
    
    print("🔄 BM25 Reranker Demo")
    print("=" * 40)
    
    # Initialize reranker
    reranker = BM25Reranker()
    
    # Test query
    query = "diabetes glucose levels"
    print(f"\nQuery: '{query}'")
    
    # Show original vector ranking
    print("\nOriginal Vector Ranking:")
    for i, doc in enumerate(doc_objects):
        print(f"{i+1}. Score: {doc['similarity_score']:.3f} - {doc['content'][:50]}...")
    
    # Rerank with BM25
    reranked_docs = reranker.rerank(query, doc_objects, top_k=5)
    
    print(f"\nBM25 Hybrid Reranked Results:")
    for i, doc in enumerate(reranked_docs):
        print(f"{i+1}. Combined: {doc['combined_score']:.3f} "
              f"(Vector: {doc['similarity_score']:.3f}, BM25: {doc['bm25_score']:.3f})")
        print(f"   {doc['content'][:60]}...")
    
    # Show term analysis for top result
    if reranked_docs:
        top_doc = reranked_docs[0]
        term_scores = reranker.get_term_scores(query, top_doc['content'])
        print(f"\nTerm Analysis for Top Result:")
        for term, score in term_scores.items():
            print(f"  '{term}': {score:.4f}")

if __name__ == "__main__":
    main()