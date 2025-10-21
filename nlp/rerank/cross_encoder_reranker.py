"""
Cross-Encoder Reranker Implementation
Provides semantic reranking using cross-encoder models for improved relevance scoring
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Constants
WORD_PATTERN = r'\b\w+\b'

@dataclass
class RerankingConfig:
    """Configuration for cross-encoder reranking"""
    model_name: str = "lightweight_medical"
    max_length: int = 512
    batch_size: int = 8
    score_threshold: float = 0.0
    weight_vector: float = 0.6
    weight_cross_encoder: float = 0.4

class SimpleCrossEncoderReranker:
    """
    Simplified cross-encoder reranker for medical text
    Uses rule-based semantic matching as a lightweight alternative to transformer models
    """
    
    def __init__(self, config: Optional[RerankingConfig] = None):
        """
        Initialize cross-encoder reranker
        
        Args:
            config: Configuration for reranking parameters
        """
        self.config = config or RerankingConfig()
        self.medical_term_weights = self._build_medical_weights()
        self.semantic_patterns = self._build_semantic_patterns()
        
    def _build_medical_weights(self) -> Dict[str, float]:
        """Build weighting scheme for medical terms"""
        return {
            # High priority medical terms
            'diagnosis': 3.0, 'treatment': 3.0, 'medication': 3.0, 'symptom': 3.0,
            'disease': 2.5, 'condition': 2.5, 'procedure': 2.5, 'therapy': 2.5,
            'patient': 2.0, 'clinical': 2.0, 'medical': 2.0, 'health': 2.0,
            
            # Specific medical conditions
            'diabetes': 3.0, 'hypertension': 3.0, 'cancer': 3.0, 'heart': 3.0,
            'blood': 2.5, 'pressure': 2.5, 'glucose': 2.5, 'cholesterol': 2.5,
            
            # Medical measurements
            'level': 2.0, 'test': 2.0, 'result': 2.0, 'value': 2.0,
            'normal': 2.0, 'elevated': 2.0, 'high': 2.0, 'low': 2.0,
            
            # Temporal terms
            'acute': 2.5, 'chronic': 2.5, 'recent': 2.0, 'history': 2.0,
            
            # Common medical actions
            'prescribed': 2.5, 'administered': 2.5, 'monitored': 2.0, 'evaluated': 2.0
        }
    
    def _build_semantic_patterns(self) -> List[Dict[str, Any]]:
        """Build semantic matching patterns for medical queries"""
        return [
            # Diagnostic patterns
            {
                'pattern': r'\b(diagnos|condition|disease)\w*\b',
                'weight': 2.5,
                'category': 'diagnosis'
            },
            # Treatment patterns
            {
                'pattern': r'\b(treat|therap|medicin|drug)\w*\b',
                'weight': 2.5,
                'category': 'treatment'
            },
            # Measurement patterns
            {
                'pattern': r'\b(level|value|result|test|reading)\w*\b',
                'weight': 2.0,
                'category': 'measurement'
            },
            # Symptom patterns
            {
                'pattern': r'\b(pain|ache|symptom|complaint|present)\w*\b',
                'weight': 2.0,
                'category': 'symptom'
            },
            # Temporal patterns
            {
                'pattern': r'\b(acute|chronic|recent|history|previous|current)\w*\b',
                'weight': 1.5,
                'category': 'temporal'
            }
        ]
    
    def _extract_query_intent(self, query: str) -> Dict[str, float]:
        """Extract semantic intent from query"""
        query_lower = query.lower()
        intent_scores = {}
        
        # Check semantic patterns
        for pattern_info in self.semantic_patterns:
            matches = re.findall(pattern_info['pattern'], query_lower)
            if matches:
                category = pattern_info['category']
                intent_scores[category] = intent_scores.get(category, 0) + \
                                        pattern_info['weight'] * len(matches)
        
        return intent_scores
    
    def _calculate_semantic_score(self, query: str, document: str) -> float:
        """
        Calculate semantic relevance score between query and document
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Semantic relevance score (0-1)
        """
        query_lower = query.lower()
        doc_lower = document.lower()
        
        # Extract query intent
        query_intent = self._extract_query_intent(query)
        
        # Tokenize query and document
        query_tokens = re.findall(WORD_PATTERN, query_lower)
        doc_tokens = re.findall(WORD_PATTERN, doc_lower)
        
        if not query_tokens or not doc_tokens:
            return 0.0
        
        score = 0.0
        
        # Score based on term overlap with medical weighting
        for token in query_tokens:
            if token in doc_tokens:
                weight = self.medical_term_weights.get(token, 1.0)
                
                # Boost score if token matches query intent
                for intent_category, intent_weight in query_intent.items():
                    if self._token_matches_intent(token, intent_category):
                        weight *= (1 + intent_weight * 0.1)
                
                score += weight
            else:
                # Partial credit for related terms
                related_score = self._find_related_terms(token, doc_tokens)
                if related_score > 0:
                    weight = self.medical_term_weights.get(token, 1.0) * 0.5
                    score += weight * related_score
        
        # Normalize by total possible weight
        max_possible_score = sum(self.medical_term_weights.get(token, 1.0) 
                               for token in query_tokens)
        
        if max_possible_score > 0:
            normalized_score = score / max_possible_score
        else:
            normalized_score = 0.0
        
        # Apply intent boosting
        intent_boost = sum(query_intent.values()) * 0.05  # Small boost for intent matching
        final_score = min(1.0, normalized_score + intent_boost)
        
        return final_score
    
    def _token_matches_intent(self, token: str, intent_category: str) -> bool:
        """Check if a token matches a specific intent category"""
        intent_mappings = {
            'diagnosis': ['diagnos', 'condition', 'disease', 'disorder'],
            'treatment': ['treat', 'therap', 'medicin', 'drug', 'prescrib'],
            'measurement': ['level', 'value', 'result', 'test', 'reading', 'lab'],
            'symptom': ['pain', 'ache', 'symptom', 'complaint', 'present'],
            'temporal': ['acute', 'chronic', 'recent', 'history', 'previous']
        }
        
        category_terms = intent_mappings.get(intent_category, [])
        return any(term in token for term in category_terms)
    
    def _find_related_terms(self, query_token: str, doc_tokens: List[str]) -> float:
        """Find semantically related terms in document"""
        # Check direct medical relations
        score = self._check_direct_relations(query_token, doc_tokens)
        if score > 0:
            return score
        
        # Check medical affixes
        return self._check_medical_affixes(query_token, doc_tokens)
    
    def _check_direct_relations(self, query_token: str, doc_tokens: List[str]) -> float:
        """Check for direct medical term relationships"""
        medical_relations = {
            'diabetes': ['diabetic', 'glucose', 'insulin', 'blood sugar'],
            'hypertension': ['pressure', 'blood pressure', 'elevated', 'high'],
            'cholesterol': ['lipid', 'hdl', 'ldl', 'triglyceride'],
            'heart': ['cardiac', 'cardiovascular', 'coronary'],
            'blood': ['hematology', 'hemoglobin', 'hematocrit'],
            'kidney': ['renal', 'nephro'],
            'liver': ['hepatic', 'hepato']
        }
        
        for base_term, related_terms in medical_relations.items():
            if base_term in query_token:
                for doc_token in doc_tokens:
                    if any(related in doc_token for related in related_terms):
                        return 0.7  # High relatedness
        return 0.0
    
    def _check_medical_affixes(self, query_token: str, doc_tokens: List[str]) -> float:
        """Check for common medical prefixes/suffixes"""
        medical_affixes = [
            ('cardio', 'heart'), ('neuro', 'nerve'), ('gastro', 'stomach'),
            ('hepato', 'liver'), ('nephro', 'kidney'), ('pulmo', 'lung')
        ]
        
        for prefix, _ in medical_affixes:
            if prefix in query_token:
                for doc_token in doc_tokens:
                    if prefix in doc_token:
                        return 0.5  # Moderate relatedness
        
        return 0.0
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], 
               top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder semantic scoring
        
        Args:
            query: Search query
            documents: List of document dicts with 'content' field
            top_k: Number of top results to return
            
        Returns:
            Reranked list of documents with cross-encoder scores
        """
        if not documents:
            return []
        
        # Score each document
        scored_docs = []
        for doc in documents:
            content = doc.get('content', '')
            
            # Calculate cross-encoder score
            ce_score = self._calculate_semantic_score(query, content)
            
            # Create enhanced document
            enhanced_doc = doc.copy()
            enhanced_doc['cross_encoder_score'] = ce_score
            
            # Combine with existing scores
            if 'similarity_score' in doc:
                # Weighted combination
                combined_score = (self.config.weight_vector * doc['similarity_score'] + 
                                self.config.weight_cross_encoder * ce_score)
                enhanced_doc['combined_score'] = combined_score
                enhanced_doc['ranking_method'] = 'hybrid_vector_ce'
            elif 'bm25_score' in doc:
                # Combine with BM25 if available
                bm25_weight = 0.3
                ce_weight = 0.7
                combined_score = bm25_weight * doc['bm25_score'] + ce_weight * ce_score
                enhanced_doc['combined_score'] = combined_score
                enhanced_doc['ranking_method'] = 'hybrid_bm25_ce'
            else:
                enhanced_doc['combined_score'] = ce_score
                enhanced_doc['ranking_method'] = 'cross_encoder_only'
            
            scored_docs.append(enhanced_doc)
        
        # Sort by combined score
        scored_docs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        # Filter by threshold
        scored_docs = [doc for doc in scored_docs 
                      if doc.get('cross_encoder_score', 0) >= self.config.score_threshold]
        
        # Return top_k results
        if top_k:
            scored_docs = scored_docs[:top_k]
        
        logger.info(f"Cross-encoder reranked {len(documents)} documents, "
                   f"returning top {len(scored_docs)}")
        return scored_docs
    
    def explain_ranking(self, query: str, document: str) -> Dict[str, Any]:
        """
        Provide explanation for document ranking
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Dictionary with ranking explanation
        """
        query_intent = self._extract_query_intent(query)
        semantic_score = self._calculate_semantic_score(query, document)
        
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        doc_tokens = re.findall(r'\b\w+\b', document.lower())
        
        matched_terms = []
        for token in query_tokens:
            if token in doc_tokens:
                weight = self.medical_term_weights.get(token, 1.0)
                matched_terms.append({'term': token, 'weight': weight})
        
        return {
            'semantic_score': semantic_score,
            'query_intent': query_intent,
            'matched_terms': matched_terms,
            'query_tokens': len(query_tokens),
            'doc_tokens': len(doc_tokens),
            'coverage': len(matched_terms) / len(query_tokens) if query_tokens else 0
        }

def main():
    """Demo of cross-encoder reranker"""
    
    # Sample documents
    documents = [
        {
            'doc_id': 'doc1',
            'content': 'Patient diagnosed with diabetes mellitus and prescribed insulin therapy',
            'similarity_score': 0.7
        },
        {
            'doc_id': 'doc2', 
            'content': 'Blood pressure readings indicate hypertension requiring treatment',
            'similarity_score': 0.8
        },
        {
            'doc_id': 'doc3',
            'content': 'Glucose levels elevated in recent lab tests for diabetic patient',
            'similarity_score': 0.6
        }
    ]
    
    print("🧠 Cross-Encoder Reranker Demo")
    print("=" * 40)
    
    # Initialize reranker
    config = RerankingConfig(weight_vector=0.5, weight_cross_encoder=0.5)
    reranker = SimpleCrossEncoderReranker(config)
    
    # Test query
    query = "diabetes treatment glucose levels"
    print(f"Query: '{query}'")
    
    # Show original ranking
    print("\nOriginal Vector Ranking:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. Score: {doc['similarity_score']:.3f} - {doc['content']}")
    
    # Rerank with cross-encoder
    reranked = reranker.rerank(query, documents)
    
    print("\nCross-Encoder Reranked Results:")
    for i, doc in enumerate(reranked):
        print(f"{i+1}. Combined: {doc['combined_score']:.3f} "
              f"(Vector: {doc['similarity_score']:.3f}, CE: {doc['cross_encoder_score']:.3f})")
        print(f"   {doc['content']}")
    
    # Show explanation for top result
    if reranked:
        top_doc = reranked[0]
        explanation = reranker.explain_ranking(query, top_doc['content'])
        print("\nRanking Explanation for Top Result:")
        print(f"  Semantic Score: {explanation['semantic_score']:.3f}")
        print(f"  Query Intent: {explanation['query_intent']}")
        print(f"  Matched Terms: {explanation['matched_terms']}")
        print(f"  Coverage: {explanation['coverage']:.2%}")

if __name__ == "__main__":
    main()