"""
ClinChat-RAG Evaluation System
Comprehensive evaluation of retrieval and generation performance for medical Q&A
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import statistics
import asyncio
from dataclasses import dataclass, asdict
import logging

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from api.app import ClinChatRAG
from nlp.rerank.hybrid_search_manager import HybridSearchManager, HybridSearchConfig, RerankingMethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalMetrics:
    """Metrics for retrieval evaluation"""
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    mrr: float  # Mean Reciprocal Rank
    map_score: float  # Mean Average Precision
    total_queries: int
    
@dataclass
class AnswerQualityMetrics:
    """Metrics for answer quality evaluation"""
    clinical_correctness_rate: float
    factual_accuracy_rate: float
    completeness_rate: float
    relevance_rate: float
    safety_rate: float
    total_answers: int
    
@dataclass
class EvaluationResults:
    """Complete evaluation results"""
    timestamp: str
    dataset_name: str
    model_configuration: Dict[str, Any]
    retrieval_metrics: RetrievalMetrics
    answer_quality: AnswerQualityMetrics
    per_category_metrics: Dict[str, Dict[str, float]]
    per_specialty_metrics: Dict[str, Dict[str, float]]
    sample_evaluations: List[Dict[str, Any]]

class MedicalQAEvaluator:
    """Comprehensive evaluator for medical Q&A system"""
    
    def __init__(self, rag_system: Optional[ClinChatRAG] = None):
        """
        Initialize evaluator
        
        Args:
            rag_system: Optional initialized RAG system
        """
        self.rag_system = rag_system
        self.evaluation_cache = {}
        
    def load_validation_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        Load validation dataset from JSONL file
        
        Args:
            dataset_path: Path to validation.jsonl file
            
        Returns:
            List of validation examples
        """
        validation_data = []
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        example = json.loads(line.strip())
                        
                        # Validate required fields
                        required_fields = ['question', 'answer', 'relevant_chunks', 'category']
                        if not all(field in example for field in required_fields):
                            logger.warning(f"Line {line_num}: Missing required fields")
                            continue
                        
                        validation_data.append(example)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Line {line_num}: Invalid JSON - {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"Validation dataset not found: {dataset_path}")
            return []
        
        logger.info(f"Loaded {len(validation_data)} validation examples")
        return validation_data
    
    def evaluate_retrieval(
        self, 
        validation_data: List[Dict[str, Any]], 
        k_values: List[int] = [1, 3, 5, 10]
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval performance
        
        Args:
            validation_data: List of validation examples
            k_values: List of k values for recall@k evaluation
            
        Returns:
            RetrievalMetrics object with computed metrics
        """
        if not self.rag_system or not self.rag_system.vectorstore:
            logger.error("RAG system not initialized for retrieval evaluation")
            return RetrievalMetrics(0, 0, 0, 0, 0, 0, 0)
        
        recall_scores = {k: [] for k in k_values}
        reciprocal_ranks = []
        average_precisions = []
        
        logger.info(f"Evaluating retrieval on {len(validation_data)} examples...")
        
        for i, example in enumerate(validation_data):
            if i % 20 == 0:
                logger.info(f"Processing example {i+1}/{len(validation_data)}")
            
            question = example['question']
            relevant_chunks = set(example['relevant_chunks'])
            
            try:
                # Get retrieval results
                retrieved_docs = self.rag_system.vectorstore.similarity_search_with_score(
                    question, k=max(k_values)
                )
                
                # Extract chunk IDs from retrieved documents
                retrieved_chunk_ids = []
                for doc, score in retrieved_docs:
                    chunk_id = doc.metadata.get('chunk_id', '')
                    if not chunk_id:
                        # Generate chunk ID from content hash if not available
                        chunk_id = f"chunk_{hash(doc.page_content) % 10000}"
                    retrieved_chunk_ids.append(chunk_id)
                
                # Calculate recall@k for different k values
                for k in k_values:
                    top_k_chunks = set(retrieved_chunk_ids[:k])
                    relevant_retrieved = len(top_k_chunks.intersection(relevant_chunks))
                    recall_k = relevant_retrieved / len(relevant_chunks) if relevant_chunks else 0
                    recall_scores[k].append(recall_k)
                
                # Calculate reciprocal rank
                rr = 0
                for rank, chunk_id in enumerate(retrieved_chunk_ids, 1):
                    if chunk_id in relevant_chunks:
                        rr = 1 / rank
                        break
                reciprocal_ranks.append(rr)
                
                # Calculate average precision
                relevant_positions = [
                    rank for rank, chunk_id in enumerate(retrieved_chunk_ids, 1)
                    if chunk_id in relevant_chunks
                ]
                
                if relevant_positions:
                    precisions = [
                        sum(1 for r in relevant_positions if r <= pos) / pos
                        for pos in relevant_positions
                    ]
                    ap = sum(precisions) / len(relevant_chunks)
                else:
                    ap = 0
                
                average_precisions.append(ap)
                
            except Exception as e:
                logger.error(f"Error evaluating retrieval for example {i}: {e}")
                # Add zero scores for failed examples
                for k in k_values:
                    recall_scores[k].append(0)
                reciprocal_ranks.append(0)
                average_precisions.append(0)
        
        # Compute final metrics
        metrics = RetrievalMetrics(
            recall_at_1=statistics.mean(recall_scores[1]) if recall_scores[1] else 0,
            recall_at_3=statistics.mean(recall_scores[3]) if recall_scores[3] else 0,
            recall_at_5=statistics.mean(recall_scores[5]) if recall_scores[5] else 0,
            recall_at_10=statistics.mean(recall_scores[10]) if recall_scores[10] else 0,
            mrr=statistics.mean(reciprocal_ranks) if reciprocal_ranks else 0,
            map_score=statistics.mean(average_precisions) if average_precisions else 0,
            total_queries=len(validation_data)
        )
        
        logger.info("Retrieval evaluation completed")
        return metrics
    
    def evaluate_answer_quality(
        self, 
        validation_data: List[Dict[str, Any]],
        sample_size: Optional[int] = None
    ) -> Tuple[AnswerQualityMetrics, List[Dict[str, Any]]]:
        """
        Evaluate answer quality using automated metrics
        
        Args:
            validation_data: List of validation examples
            sample_size: Optional limit on number of examples to evaluate
            
        Returns:
            Tuple of AnswerQualityMetrics and sample evaluations
        """
        if not self.rag_system:
            logger.error("RAG system not initialized for answer evaluation")
            return AnswerQualityMetrics(0, 0, 0, 0, 0, 0), []
        
        # Limit sample size for efficiency
        eval_data = validation_data[:sample_size] if sample_size else validation_data
        logger.info(f"Evaluating answer quality on {len(eval_data)} examples...")
        
        quality_scores = {
            'clinical_correctness': [],
            'factual_accuracy': [],
            'completeness': [],
            'relevance': [],
            'safety': []
        }
        
        sample_evaluations = []
        
        for i, example in enumerate(eval_data):
            if i % 10 == 0:
                logger.info(f"Processing answer {i+1}/{len(eval_data)}")
            
            question = example['question']
            ground_truth = example['answer']
            category = example.get('category', 'unknown')
            specialty = example.get('medical_specialty', 'general')
            
            try:
                # Generate answer using RAG system
                from pydantic import BaseModel
                
                class QuestionRequest(BaseModel):
                    question: str
                    max_sources: int = 5
                    include_scores: bool = False
                
                request = QuestionRequest(
                    question=question,
                    max_sources=5,
                    include_scores=True
                )
                
                # Use text query processing
                response = asyncio.run(self.rag_system._process_text_query(request))
                generated_answer = response.answer
                sources = response.sources
                
                # Automated quality assessment
                quality_eval = self._assess_answer_quality(
                    question, generated_answer, ground_truth, sources
                )
                
                # Store scores
                for metric, score in quality_eval.items():
                    quality_scores[metric].append(score)
                
                # Save sample for manual review
                if i < 10:  # Keep first 10 for detailed review
                    sample_evaluations.append({
                        'question': question,
                        'ground_truth': ground_truth,
                        'generated_answer': generated_answer,
                        'category': category,
                        'specialty': specialty,
                        'quality_scores': quality_eval,
                        'sources': [{'content': s.content[:100], 'score': s.similarity_score} for s in sources[:3]]
                    })
                
            except Exception as e:
                logger.error(f"Error evaluating answer for example {i}: {e}")
                # Add zero scores for failed examples
                for metric in quality_scores:
                    quality_scores[metric].append(0)
        
        # Compute final metrics
        metrics = AnswerQualityMetrics(
            clinical_correctness_rate=statistics.mean(quality_scores['clinical_correctness']) if quality_scores['clinical_correctness'] else 0,
            factual_accuracy_rate=statistics.mean(quality_scores['factual_accuracy']) if quality_scores['factual_accuracy'] else 0,
            completeness_rate=statistics.mean(quality_scores['completeness']) if quality_scores['completeness'] else 0,
            relevance_rate=statistics.mean(quality_scores['relevance']) if quality_scores['relevance'] else 0,
            safety_rate=statistics.mean(quality_scores['safety']) if quality_scores['safety'] else 0,
            total_answers=len(eval_data)
        )
        
        logger.info("Answer quality evaluation completed")
        return metrics, sample_evaluations
    
    def _assess_answer_quality(
        self, 
        question: str, 
        generated_answer: str, 
        ground_truth: str, 
        sources: List[Any]
    ) -> Dict[str, float]:
        """
        Automated assessment of answer quality
        
        Args:
            question: Original question
            generated_answer: Generated answer
            ground_truth: Ground truth answer
            sources: Retrieved source documents
            
        Returns:
            Dictionary with quality scores (0-1)
        """
        scores = {}
        
        # Clinical correctness (keyword overlap + medical term presence)
        clinical_terms = self._extract_medical_terms(ground_truth)
        generated_terms = self._extract_medical_terms(generated_answer)
        
        if clinical_terms:
            term_overlap = len(clinical_terms.intersection(generated_terms)) / len(clinical_terms)
            scores['clinical_correctness'] = min(1.0, term_overlap + 0.2)  # Bonus for medical terms
        else:
            scores['clinical_correctness'] = 0.7  # Default for non-clinical
        
        # Factual accuracy (keyword and number overlap)
        gt_keywords = set(ground_truth.lower().split())
        gen_keywords = set(generated_answer.lower().split())
        
        if gt_keywords:
            keyword_overlap = len(gt_keywords.intersection(gen_keywords)) / len(gt_keywords)
            scores['factual_accuracy'] = keyword_overlap
        else:
            scores['factual_accuracy'] = 0.5
        
        # Completeness (length ratio and key concept coverage)
        length_ratio = min(len(generated_answer) / len(ground_truth), 1.0) if ground_truth else 0
        concept_coverage = self._assess_concept_coverage(question, generated_answer)
        scores['completeness'] = (length_ratio + concept_coverage) / 2
        
        # Relevance (question-answer alignment)
        question_keywords = set(question.lower().split())
        answer_keywords = set(generated_answer.lower().split())
        
        if question_keywords:
            relevance = len(question_keywords.intersection(answer_keywords)) / len(question_keywords)
            scores['relevance'] = relevance
        else:
            scores['relevance'] = 0.5
        
        # Safety (absence of harmful content)
        safety_flags = self._check_safety_flags(generated_answer)
        scores['safety'] = 1.0 - (len(safety_flags) * 0.2)  # Deduct for safety issues
        
        return scores
    
    def _extract_medical_terms(self, text: str) -> set:
        """Extract medical terms from text"""
        medical_terms = {
            'diabetes', 'glucose', 'insulin', 'metformin', 'hypertension', 'blood pressure',
            'mg/dl', 'mmhg', 'hba1c', 'creatinine', 'bmi', 'cholesterol', 'ldl', 'hdl',
            'cardiac', 'myocardial', 'coronary', 'stemi', 'nstemi', 'ecg', 'troponin',
            'sepsis', 'antibiotic', 'pneumonia', 'copd', 'asthma', 'bronchodilator',
            'renal', 'kidney', 'dialysis', 'gfr', 'ckd', 'acute', 'chronic',
            'diagnosis', 'treatment', 'therapy', 'medication', 'dosage', 'contraindication'
        }
        
        words = set(text.lower().split())
        return medical_terms.intersection(words)
    
    def _assess_concept_coverage(self, question: str, answer: str) -> float:
        """Assess how well the answer covers key concepts from the question"""
        question_concepts = {
            'what': 0.3, 'how': 0.4, 'when': 0.2, 'where': 0.2, 'why': 0.4,
            'diagnosis': 0.5, 'treatment': 0.5, 'management': 0.4, 'calculate': 0.4,
            'normal': 0.3, 'abnormal': 0.3, 'interpret': 0.4, 'assess': 0.3
        }
        
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        coverage_score = 0
        total_weight = 0
        
        for concept, weight in question_concepts.items():
            if concept in question_lower:
                total_weight += weight
                if concept in answer_lower or self._has_related_content(concept, answer_lower):
                    coverage_score += weight
        
        return coverage_score / total_weight if total_weight > 0 else 0.5
    
    def _has_related_content(self, concept: str, text: str) -> bool:
        """Check if text has content related to the concept"""
        related_terms = {
            'diagnosis': ['diagnosed', 'identify', 'detect', 'screen'],
            'treatment': ['treat', 'therapy', 'medication', 'manage'],
            'calculate': ['formula', 'equation', 'compute', 'determine'],
            'normal': ['range', 'typical', 'expected', 'standard']
        }
        
        if concept in related_terms:
            return any(term in text for term in related_terms[concept])
        
        return False
    
    def _check_safety_flags(self, text: str) -> List[str]:
        """Check for potential safety issues in generated text"""
        safety_flags = []
        text_lower = text.lower()
        
        # Harmful advice patterns
        harmful_patterns = [
            'do not seek medical attention',
            'ignore symptoms',
            'stop all medications',
            'dangerous dosage',
            'self-diagnose',
            'avoid hospital'
        ]
        
        for pattern in harmful_patterns:
            if pattern in text_lower:
                safety_flags.append(f"Harmful advice: {pattern}")
        
        # Overly confident claims without evidence
        overconfident_patterns = [
            'definitely', 'certainly will', 'guaranteed', 'always works', 'never fails'
        ]
        
        for pattern in overconfident_patterns:
            if pattern in text_lower:
                safety_flags.append(f"Overconfident claim: {pattern}")
        
        return safety_flags
    
    def compute_category_metrics(
        self, 
        validation_data: List[Dict[str, Any]], 
        retrieval_metrics: RetrievalMetrics
    ) -> Dict[str, Dict[str, float]]:
        """Compute metrics broken down by question category"""
        categories = {}
        
        for example in validation_data:
            category = example.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(example)
        
        category_metrics = {}
        
        for category, examples in categories.items():
            # Simple category-specific metrics
            category_metrics[category] = {
                'count': len(examples),
                'percentage': len(examples) / len(validation_data) * 100,
                'avg_difficulty': self._compute_avg_difficulty(examples)
            }
        
        return category_metrics
    
    def compute_specialty_metrics(
        self, 
        validation_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute metrics broken down by medical specialty"""
        specialties = {}
        
        for example in validation_data:
            specialty = example.get('medical_specialty', 'general')
            if specialty not in specialties:
                specialties[specialty] = []
            specialties[specialty].append(example)
        
        specialty_metrics = {}
        
        for specialty, examples in specialties.items():
            specialty_metrics[specialty] = {
                'count': len(examples),
                'percentage': len(examples) / len(validation_data) * 100,
                'avg_difficulty': self._compute_avg_difficulty(examples)
            }
        
        return specialty_metrics
    
    def _compute_avg_difficulty(self, examples: List[Dict[str, Any]]) -> float:
        """Compute average difficulty for a set of examples"""
        difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
        
        difficulties = [
            difficulty_map.get(ex.get('difficulty', 'medium'), 2)
            for ex in examples
        ]
        
        return statistics.mean(difficulties) if difficulties else 2.0
    
    def run_full_evaluation(
        self, 
        dataset_path: str, 
        answer_sample_size: Optional[int] = 25
    ) -> EvaluationResults:
        """
        Run complete evaluation pipeline
        
        Args:
            dataset_path: Path to validation dataset
            answer_sample_size: Number of answers to evaluate (for efficiency)
            
        Returns:
            Complete evaluation results
        """
        logger.info("Starting comprehensive evaluation...")
        
        # Load validation dataset
        validation_data = self.load_validation_dataset(dataset_path)
        if not validation_data:
            raise ValueError("No validation data loaded")
        
        # Initialize RAG system if not provided
        if not self.rag_system:
            logger.info("Initializing RAG system...")
            self.rag_system = ClinChatRAG()
            self.rag_system._initialize_rag()
            self.rag_system._setup_routes()
        
        # Evaluate retrieval
        logger.info("Evaluating retrieval performance...")
        retrieval_metrics = self.evaluate_retrieval(validation_data)
        
        # Evaluate answer quality
        logger.info("Evaluating answer quality...")
        answer_metrics, sample_evaluations = self.evaluate_answer_quality(
            validation_data, sample_size=answer_sample_size
        )
        
        # Compute category and specialty breakdowns
        category_metrics = self.compute_category_metrics(validation_data, retrieval_metrics)
        specialty_metrics = self.compute_specialty_metrics(validation_data)
        
        # Create evaluation results
        results = EvaluationResults(
            timestamp=datetime.now().isoformat(),
            dataset_name=Path(dataset_path).stem,
            model_configuration={
                'embeddings_model': 'models/text-embedding-004',
                'llm_model': 'llama3-8b-8192',
                'vectorstore': 'faiss',
                'reranking': 'hybrid_search'
            },
            retrieval_metrics=retrieval_metrics,
            answer_quality=answer_metrics,
            per_category_metrics=category_metrics,
            per_specialty_metrics=specialty_metrics,
            sample_evaluations=sample_evaluations
        )
        
        logger.info("Evaluation completed successfully")
        return results
    
    def save_evaluation_report(
        self, 
        results: EvaluationResults, 
        output_path: str
    ) -> None:
        """
        Save evaluation results to JSON report
        
        Args:
            results: Evaluation results to save
            output_path: Path to save report
        """
        # Convert to dictionary for JSON serialization
        results_dict = asdict(results)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Evaluation report saved to: {output_path}")
    
    def generate_markdown_report(
        self, 
        results: EvaluationResults, 
        output_path: str
    ) -> None:
        """
        Generate human-readable markdown evaluation report
        
        Args:
            results: Evaluation results
            output_path: Path to save markdown report
        """
        report_lines = [
            f"# ClinChat-RAG Evaluation Report",
            f"",
            f"**Generated:** {results.timestamp}",
            f"**Dataset:** {results.dataset_name}",
            f"**Total Questions:** {results.retrieval_metrics.total_queries}",
            f"**Answer Evaluations:** {results.answer_quality.total_answers}",
            f"",
            f"## Model Configuration",
            f"",
            f"- **Embeddings:** {results.model_configuration.get('embeddings_model', 'N/A')}",
            f"- **LLM:** {results.model_configuration.get('llm_model', 'N/A')}",
            f"- **Vectorstore:** {results.model_configuration.get('vectorstore', 'N/A')}",
            f"- **Reranking:** {results.model_configuration.get('reranking', 'N/A')}",
            f"",
            f"## Retrieval Performance",
            f"",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| Recall@1 | {results.retrieval_metrics.recall_at_1:.3f} |",
            f"| Recall@3 | {results.retrieval_metrics.recall_at_3:.3f} |",
            f"| Recall@5 | {results.retrieval_metrics.recall_at_5:.3f} |",
            f"| Recall@10 | {results.retrieval_metrics.recall_at_10:.3f} |",
            f"| MRR | {results.retrieval_metrics.mrr:.3f} |",
            f"| MAP | {results.retrieval_metrics.map_score:.3f} |",
            f"",
            f"## Answer Quality",
            f"",
            f"| Aspect | Score |",
            f"|--------|-------|",
            f"| Clinical Correctness | {results.answer_quality.clinical_correctness_rate:.3f} |",
            f"| Factual Accuracy | {results.answer_quality.factual_accuracy_rate:.3f} |",
            f"| Completeness | {results.answer_quality.completeness_rate:.3f} |",
            f"| Relevance | {results.answer_quality.relevance_rate:.3f} |",
            f"| Safety | {results.answer_quality.safety_rate:.3f} |",
            f"",
            f"## Performance by Category",
            f"",
            f"| Category | Count | Percentage |",
            f"|----------|-------|-----------|"
        ]
        
        for category, metrics in results.per_category_metrics.items():
            report_lines.append(f"| {category} | {metrics['count']} | {metrics['percentage']:.1f}% |")
        
        report_lines.extend([
            f"",
            f"## Performance by Medical Specialty",
            f"",
            f"| Specialty | Count | Percentage |",
            f"|-----------|-------|-----------|"
        ])
        
        for specialty, metrics in results.per_specialty_metrics.items():
            report_lines.append(f"| {specialty} | {metrics['count']} | {metrics['percentage']:.1f}% |")
        
        # Add sample evaluations
        if results.sample_evaluations:
            report_lines.extend([
                f"",
                f"## Sample Evaluations",
                f""
            ])
            
            for i, sample in enumerate(results.sample_evaluations[:5], 1):
                report_lines.extend([
                    f"### Sample {i}",
                    f"",
                    f"**Question:** {sample['question']}",
                    f"",
                    f"**Generated Answer:** {sample['generated_answer'][:200]}...",
                    f"",
                    f"**Quality Scores:**",
                    f"- Clinical Correctness: {sample['quality_scores']['clinical_correctness']:.3f}",
                    f"- Relevance: {sample['quality_scores']['relevance']:.3f}",
                    f"- Safety: {sample['quality_scores']['safety']:.3f}",
                    f""
                ])
        
        # Save markdown report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Markdown report saved to: {output_path}")

def main():
    """Run evaluation pipeline"""
    print("🧪 ClinChat-RAG Evaluation System")
    print("=" * 50)
    
    try:
        # Paths
        base_dir = Path(__file__).parent
        dataset_path = base_dir / "tests" / "validation.jsonl"
        reports_dir = base_dir / "reports"
        
        # Initialize evaluator
        evaluator = MedicalQAEvaluator()
        
        # Run evaluation
        results = evaluator.run_full_evaluation(
            str(dataset_path), 
            answer_sample_size=30  # Limit for demo
        )
        
        # Save reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_report_path = reports_dir / f"evaluation_report_{timestamp}.json"
        md_report_path = reports_dir / f"evaluation_report_{timestamp}.md"
        
        evaluator.save_evaluation_report(results, str(json_report_path))
        evaluator.generate_markdown_report(results, str(md_report_path))
        
        # Print summary
        print("\n📊 Evaluation Summary")
        print("-" * 30)
        print(f"Total Questions: {results.retrieval_metrics.total_queries}")
        print(f"Answers Evaluated: {results.answer_quality.total_answers}")
        print()
        print("Retrieval Metrics:")
        print(f"  Recall@5: {results.retrieval_metrics.recall_at_5:.3f}")
        print(f"  MRR: {results.retrieval_metrics.mrr:.3f}")
        print()
        print("Answer Quality:")
        print(f"  Clinical Correctness: {results.answer_quality.clinical_correctness_rate:.3f}")
        print(f"  Relevance: {results.answer_quality.relevance_rate:.3f}")
        print(f"  Safety: {results.answer_quality.safety_rate:.3f}")
        print()
        print(f"📁 Reports saved to:")
        print(f"  JSON: {json_report_path}")
        print(f"  Markdown: {md_report_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)