"""
Advanced Cross-Encoder Reranking System for ClinChat-RAG
Implements fine-tuned cross-encoder reranking with medical-specific thresholds
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import numpy as np

try:
    from sentence_transformers import CrossEncoder
    from sentence_transformers.util import semantic_search
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

@dataclass
class RerankingResult:
    """Result from cross-encoder reranking"""
    doc_id: str
    content: str
    original_score: float
    rerank_score: float
    final_score: float
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class RerankingConfig:
    """Configuration for cross-encoder reranking"""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    batch_size: int = 32
    max_length: int = 512
    
    # Medical-specific thresholds
    high_confidence_threshold: float = 0.8
    medium_confidence_threshold: float = 0.6
    low_confidence_threshold: float = 0.3
    
    # Scoring weights
    semantic_weight: float = 0.6
    rerank_weight: float = 0.4
    
    # Performance settings
    use_gpu: bool = True
    max_candidates: int = 100
    top_k: int = 10

@dataclass
class MedicalDomainThresholds:
    """Domain-specific confidence thresholds for medical content"""
    # Drug information
    drug_interactions: float = 0.85
    dosing_guidelines: float = 0.9
    contraindications: float = 0.95
    
    # Clinical trials
    trial_results: float = 0.8
    inclusion_criteria: float = 0.75
    endpoint_analysis: float = 0.8
    
    # Diagnostic information
    differential_diagnosis: float = 0.85
    laboratory_values: float = 0.9
    imaging_findings: float = 0.8
    
    # Treatment protocols
    treatment_guidelines: float = 0.85
    surgical_procedures: float = 0.9
    emergency_protocols: float = 0.95
    
    # General medical
    pathophysiology: float = 0.75
    epidemiology: float = 0.7
    patient_education: float = 0.6

class CrossEncoderReranker(ABC):
    """Abstract base class for cross-encoder reranking implementations"""
    
    @abstractmethod
    async def initialize(self, config: RerankingConfig) -> bool:
        """Initialize the reranking model"""
        pass
    
    @abstractmethod
    async def rerank(self, query: str, candidates: List[Dict[str, Any]], 
                    domain_context: Optional[str] = None) -> List[RerankingResult]:
        """Rerank candidates using cross-encoder"""
        pass
    
    @abstractmethod
    def get_confidence_threshold(self, domain: str) -> float:
        """Get domain-specific confidence threshold"""
        pass

class SentenceTransformerReranker(CrossEncoderReranker):
    """Cross-encoder reranking using SentenceTransformers"""
    
    def __init__(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        
        self.model = None
        self.config = None
        self.thresholds = MedicalDomainThresholds()
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, config: RerankingConfig) -> bool:
        """Initialize cross-encoder model"""
        try:
            self.config = config
            
            # Load cross-encoder model
            self.model = CrossEncoder(
                config.model_name,
                max_length=config.max_length,
                device='cuda' if config.use_gpu and torch.cuda.is_available() else 'cpu'
            )
            
            self.logger.info(f"Initialized cross-encoder: {config.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cross-encoder: {e}")
            return False
    
    async def rerank(self, query: str, candidates: List[Dict[str, Any]], 
                    domain_context: Optional[str] = None) -> List[RerankingResult]:
        """Rerank candidates using cross-encoder model"""
        try:
            if not self.model:
                raise RuntimeError("Reranker not initialized")
            
            if not candidates:
                return []
            
            # Prepare query-document pairs
            pairs = []
            for candidate in candidates:
                content = candidate.get('content', '')
                # Truncate content if too long
                if len(content) > 2000:  # Conservative limit
                    content = content[:2000] + "..."
                pairs.append([query, content])
            
            # Get reranking scores in batches
            rerank_scores = []
            batch_size = self.config.batch_size
            
            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i:i + batch_size]
                batch_scores = self.model.predict(batch_pairs)
                
                # Convert to list if numpy array
                if hasattr(batch_scores, 'tolist'):
                    batch_scores = batch_scores.tolist()
                elif not isinstance(batch_scores, list):
                    batch_scores = [float(batch_scores)]
                
                rerank_scores.extend(batch_scores)
            
            # Determine confidence threshold based on domain
            confidence_threshold = self.get_confidence_threshold(domain_context or "general")
            
            # Create reranking results
            results = []
            for i, candidate in enumerate(candidates):
                original_score = candidate.get('score', 0.0)
                rerank_score = float(rerank_scores[i]) if i < len(rerank_scores) else 0.0
                
                # Calculate final score (weighted combination)
                final_score = (
                    self.config.semantic_weight * original_score +
                    self.config.rerank_weight * rerank_score
                )
                
                # Calculate confidence based on rerank score
                confidence = min(max(rerank_score, 0.0), 1.0)
                
                result = RerankingResult(
                    doc_id=candidate.get('doc_id', f"doc_{i}"),
                    content=candidate.get('content', ''),
                    original_score=original_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    confidence=confidence,
                    metadata=candidate.get('metadata', {})
                )
                
                # Only include results above confidence threshold
                if confidence >= confidence_threshold:
                    results.append(result)
            
            # Sort by final score (descending)
            results.sort(key=lambda x: x.final_score, reverse=True)
            
            # Return top-k results
            return results[:self.config.top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to rerank candidates: {e}")
            return []
    
    def get_confidence_threshold(self, domain: str) -> float:
        """Get confidence threshold for specific medical domain"""
        domain_lower = domain.lower()
        
        # Drug-related domains
        if any(keyword in domain_lower for keyword in ['drug', 'medication', 'pharmacology']):
            if 'interaction' in domain_lower:
                return self.thresholds.drug_interactions
            elif 'dosing' in domain_lower or 'dose' in domain_lower:
                return self.thresholds.dosing_guidelines
            elif 'contraindication' in domain_lower:
                return self.thresholds.contraindications
        
        # Clinical trial domains
        elif any(keyword in domain_lower for keyword in ['trial', 'study', 'clinical']):
            if 'result' in domain_lower or 'outcome' in domain_lower:
                return self.thresholds.trial_results
            elif 'inclusion' in domain_lower or 'criteria' in domain_lower:
                return self.thresholds.inclusion_criteria
            elif 'endpoint' in domain_lower:
                return self.thresholds.endpoint_analysis
        
        # Diagnostic domains
        elif any(keyword in domain_lower for keyword in ['diagnosis', 'diagnostic']):
            if 'differential' in domain_lower:
                return self.thresholds.differential_diagnosis
            elif 'lab' in domain_lower or 'laboratory' in domain_lower:
                return self.thresholds.laboratory_values
            elif 'imaging' in domain_lower or 'radiology' in domain_lower:
                return self.thresholds.imaging_findings
        
        # Treatment domains
        elif any(keyword in domain_lower for keyword in ['treatment', 'therapy', 'therapeutic']):
            if 'guideline' in domain_lower:
                return self.thresholds.treatment_guidelines
            elif 'surgery' in domain_lower or 'surgical' in domain_lower:
                return self.thresholds.surgical_procedures
            elif 'emergency' in domain_lower:
                return self.thresholds.emergency_protocols
        
        # General medical domains
        elif 'pathophysiology' in domain_lower:
            return self.thresholds.pathophysiology
        elif 'epidemiology' in domain_lower:
            return self.thresholds.epidemiology
        elif 'patient education' in domain_lower:
            return self.thresholds.patient_education
        
        # Default threshold
        return self.config.medium_confidence_threshold

class HuggingFaceReranker(CrossEncoderReranker):
    """Cross-encoder reranking using HuggingFace Transformers"""
    
    def __init__(self):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not installed. Install with: pip install transformers torch")
        
        self.model = None
        self.tokenizer = None
        self.config = None
        self.thresholds = MedicalDomainThresholds()
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, config: RerankingConfig) -> bool:
        """Initialize HuggingFace cross-encoder model"""
        try:
            self.config = config
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(config.model_name)
            
            # Move to GPU if available
            if config.use_gpu and torch.cuda.is_available():
                self.model = self.model.cuda()
            
            self.model.eval()  # Set to evaluation mode
            
            self.logger.info(f"Initialized HuggingFace cross-encoder: {config.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HuggingFace cross-encoder: {e}")
            return False
    
    async def rerank(self, query: str, candidates: List[Dict[str, Any]], 
                    domain_context: Optional[str] = None) -> List[RerankingResult]:
        """Rerank using HuggingFace model with batching"""
        try:
            if not self.model or not self.tokenizer:
                raise RuntimeError("Reranker not initialized")
            
            if not candidates:
                return []
            
            # Prepare input texts
            texts = []
            for candidate in candidates:
                content = candidate.get('content', '')
                if len(content) > 2000:
                    content = content[:2000] + "..."
                
                # Format as [CLS] query [SEP] document [SEP]
                text = f"{query} [SEP] {content}"
                texts.append(text)
            
            # Tokenize and get scores
            rerank_scores = []
            batch_size = self.config.batch_size
            
            with torch.no_grad():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    
                    # Tokenize batch
                    inputs = self.tokenizer(
                        batch_texts,
                        padding=True,
                        truncation=True,
                        max_length=self.config.max_length,
                        return_tensors='pt'
                    )
                    
                    # Move to GPU if available
                    if self.config.use_gpu and torch.cuda.is_available():
                        inputs = {k: v.cuda() for k, v in inputs.items()}
                    
                    # Get model outputs
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    
                    # Apply softmax to get probabilities
                    probs = torch.softmax(logits, dim=-1)
                    
                    # Extract positive class probabilities
                    if probs.shape[-1] == 2:  # Binary classification
                        batch_scores = probs[:, 1].cpu().tolist()
                    else:  # Single output
                        batch_scores = torch.sigmoid(logits).squeeze().cpu().tolist()
                        if not isinstance(batch_scores, list):
                            batch_scores = [batch_scores]
                    
                    rerank_scores.extend(batch_scores)
            
            # Get confidence threshold
            confidence_threshold = self.get_confidence_threshold(domain_context or "general")
            
            # Create results
            results = []
            for i, candidate in enumerate(candidates):
                original_score = candidate.get('score', 0.0)
                rerank_score = float(rerank_scores[i]) if i < len(rerank_scores) else 0.0
                
                final_score = (
                    self.config.semantic_weight * original_score +
                    self.config.rerank_weight * rerank_score
                )
                
                confidence = min(max(rerank_score, 0.0), 1.0)
                
                if confidence >= confidence_threshold:
                    result = RerankingResult(
                        doc_id=candidate.get('doc_id', f"doc_{i}"),
                        content=candidate.get('content', ''),
                        original_score=original_score,
                        rerank_score=rerank_score,
                        final_score=final_score,
                        confidence=confidence,
                        metadata=candidate.get('metadata', {})
                    )
                    results.append(result)
            
            # Sort and return top-k
            results.sort(key=lambda x: x.final_score, reverse=True)
            return results[:self.config.top_k]
            
        except Exception as e:
            self.logger.error(f"Failed to rerank with HuggingFace model: {e}")
            return []
    
    def get_confidence_threshold(self, domain: str) -> float:
        """Get domain-specific confidence threshold"""
        # Reuse the same logic as SentenceTransformerReranker
        return SentenceTransformerReranker.get_confidence_threshold(self, domain)

class RerankingManager:
    """Manager for cross-encoder reranking operations"""
    
    def __init__(self):
        self.rerankers = {
            "sentence_transformers": SentenceTransformerReranker,
            "huggingface": HuggingFaceReranker
        }
        self.active_reranker = None
        self.config = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, config: RerankingConfig, 
                        reranker_type: str = "sentence_transformers") -> bool:
        """Initialize reranking system"""
        try:
            if reranker_type not in self.rerankers:
                raise ValueError(f"Unsupported reranker type: {reranker_type}")
            
            # Create reranker instance
            reranker_class = self.rerankers[reranker_type]
            self.active_reranker = reranker_class()
            self.config = config
            
            # Initialize reranker
            success = await self.active_reranker.initialize(config)
            if success:
                self.logger.info(f"Initialized {reranker_type} reranker")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to initialize reranking manager: {e}")
            return False
    
    async def rerank_results(self, query: str, candidates: List[Dict[str, Any]], 
                           domain_context: Optional[str] = None) -> List[RerankingResult]:
        """Rerank search results"""
        if not self.active_reranker:
            raise RuntimeError("Reranking system not initialized")
        
        start_time = time.time()
        
        # Limit candidates to max_candidates
        if len(candidates) > self.config.max_candidates:
            candidates = candidates[:self.config.max_candidates]
        
        # Perform reranking
        results = await self.active_reranker.rerank(query, candidates, domain_context)
        
        # Log performance
        rerank_time = time.time() - start_time
        self.logger.info(
            f"Reranked {len(candidates)} candidates in {rerank_time:.3f}s, "
            f"returned {len(results)} results"
        )
        
        return results
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """Get reranking system statistics"""
        if not self.config:
            return {"error": "Reranking system not initialized"}
        
        return {
            "model_name": self.config.model_name,
            "batch_size": self.config.batch_size,
            "max_length": self.config.max_length,
            "top_k": self.config.top_k,
            "semantic_weight": self.config.semantic_weight,
            "rerank_weight": self.config.rerank_weight,
            "high_confidence_threshold": self.config.high_confidence_threshold,
            "medium_confidence_threshold": self.config.medium_confidence_threshold,
            "low_confidence_threshold": self.config.low_confidence_threshold,
            "use_gpu": self.config.use_gpu,
            "max_candidates": self.config.max_candidates
        }

# Configuration presets
MEDICAL_RERANKING_CONFIG = RerankingConfig(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    batch_size=16,
    max_length=512,
    high_confidence_threshold=0.85,
    medium_confidence_threshold=0.65,
    low_confidence_threshold=0.4,
    semantic_weight=0.6,
    rerank_weight=0.4,
    use_gpu=True,
    max_candidates=50,
    top_k=10
)

CLINICAL_TRIALS_CONFIG = RerankingConfig(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    batch_size=16,
    max_length=512,
    high_confidence_threshold=0.9,
    medium_confidence_threshold=0.75,
    low_confidence_threshold=0.5,
    semantic_weight=0.5,
    rerank_weight=0.5,
    use_gpu=True,
    max_candidates=100,
    top_k=15
)

# Global manager instance
reranking_manager = RerankingManager()

# Export main components
__all__ = [
    'CrossEncoderReranker',
    'RerankingManager',
    'RerankingConfig',
    'RerankingResult',
    'MedicalDomainThresholds',
    'SentenceTransformerReranker',
    'HuggingFaceReranker',
    'reranking_manager',
    'MEDICAL_RERANKING_CONFIG',
    'CLINICAL_TRIALS_CONFIG'
]