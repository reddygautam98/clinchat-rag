"""
Quick Evaluation Runner for ClinChat-RAG
Simplified script to run baseline evaluation
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from evaluation_system import MedicalQAEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_baseline_evaluation():
    """Run baseline evaluation on the validation dataset"""
    
    print("🚀 Running ClinChat-RAG Baseline Evaluation")
    print("=" * 60)
    
    try:
        # Initialize paths
        current_dir = Path(__file__).parent
        dataset_path = current_dir / "tests" / "validation.jsonl" 
        reports_dir = current_dir / "reports"
        
        # Create reports directory
        reports_dir.mkdir(exist_ok=True)
        
        print(f"📁 Dataset: {dataset_path}")
        print(f"📁 Reports: {reports_dir}")
        
        # Check if dataset exists
        if not dataset_path.exists():
            logger.error(f"Validation dataset not found: {dataset_path}")
            return False
        
        # Initialize evaluator
        print("\n🔧 Initializing evaluation system...")
        evaluator = MedicalQAEvaluator()
        
        # Run evaluation with limited sample for demonstration
        print("🧪 Running evaluation (limited sample for demo)...")
        
        results = evaluator.run_full_evaluation(
            str(dataset_path),
            answer_sample_size=20  # Limited for demo/testing
        )
        
        # Generate timestamp for report files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON report
        json_report_path = reports_dir / f"baseline_evaluation_{timestamp}.json"
        evaluator.save_evaluation_report(results, str(json_report_path))
        
        # Generate human-readable markdown report
        md_report_path = reports_dir / f"baseline_evaluation_{timestamp}.md"
        evaluator.generate_markdown_report(results, str(md_report_path))
        
        # Display results summary
        print("\n" + "="*60)
        print("📊 BASELINE EVALUATION RESULTS")
        print("="*60)
        
        print(f"\n🔍 RETRIEVAL PERFORMANCE")
        print(f"   Total Questions Evaluated: {results.retrieval_metrics.total_queries}")
        print(f"   Recall@1:  {results.retrieval_metrics.recall_at_1:.3f}")
        print(f"   Recall@3:  {results.retrieval_metrics.recall_at_3:.3f}")
        print(f"   Recall@5:  {results.retrieval_metrics.recall_at_5:.3f}")
        print(f"   Recall@10: {results.retrieval_metrics.recall_at_10:.3f}")
        print(f"   MRR:       {results.retrieval_metrics.mrr:.3f}")
        print(f"   MAP:       {results.retrieval_metrics.map_score:.3f}")
        
        print(f"\n💬 ANSWER QUALITY")
        print(f"   Answers Evaluated: {results.answer_quality.total_answers}")
        print(f"   Clinical Correctness: {results.answer_quality.clinical_correctness_rate:.3f}")
        print(f"   Factual Accuracy:     {results.answer_quality.factual_accuracy_rate:.3f}")
        print(f"   Completeness:         {results.answer_quality.completeness_rate:.3f}")
        print(f"   Relevance:            {results.answer_quality.relevance_rate:.3f}")
        print(f"   Safety:               {results.answer_quality.safety_rate:.3f}")
        
        print(f"\n📈 PERFORMANCE BY CATEGORY")
        for category, metrics in results.per_category_metrics.items():
            print(f"   {category.capitalize():15} {metrics['count']:3d} questions ({metrics['percentage']:5.1f}%)")
        
        print(f"\n🏥 PERFORMANCE BY SPECIALTY") 
        for specialty, metrics in results.per_specialty_metrics.items():
            print(f"   {specialty.capitalize():15} {metrics['count']:3d} questions ({metrics['percentage']:5.1f}%)")
        
        print(f"\n📁 REPORTS GENERATED")
        print(f"   JSON Report:     {json_report_path}")
        print(f"   Markdown Report: {md_report_path}")
        
        # Performance assessment
        print(f"\n🎯 BASELINE ASSESSMENT")
        recall_5 = results.retrieval_metrics.recall_at_5
        clinical_correct = results.answer_quality.clinical_correctness_rate
        safety = results.answer_quality.safety_rate
        
        if recall_5 >= 0.7:
            print(f"   ✅ Retrieval: GOOD (Recall@5: {recall_5:.3f})")
        elif recall_5 >= 0.5:
            print(f"   🟡 Retrieval: FAIR (Recall@5: {recall_5:.3f})")
        else:
            print(f"   ❌ Retrieval: POOR (Recall@5: {recall_5:.3f})")
        
        if clinical_correct >= 0.8:
            print(f"   ✅ Clinical Quality: GOOD ({clinical_correct:.3f})")
        elif clinical_correct >= 0.6:
            print(f"   🟡 Clinical Quality: FAIR ({clinical_correct:.3f})")
        else:
            print(f"   ❌ Clinical Quality: POOR ({clinical_correct:.3f})")
        
        if safety >= 0.95:
            print(f"   ✅ Safety: EXCELLENT ({safety:.3f})")
        elif safety >= 0.85:
            print(f"   🟡 Safety: GOOD ({safety:.3f})")
        else:
            print(f"   ⚠️ Safety: NEEDS ATTENTION ({safety:.3f})")
        
        print("\n🎉 Baseline evaluation completed successfully!")
        print(f"📋 Review detailed reports for comprehensive analysis.")
        
        return True
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_dataset():
    """Quick validation of the dataset format"""
    
    dataset_path = Path(__file__).parent / "tests" / "validation.jsonl"
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        return False
    
    try:
        import json
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        valid_count = 0
        total_count = len(lines)
        
        for i, line in enumerate(lines):
            try:
                data = json.loads(line.strip())
                required_fields = ['question', 'answer', 'relevant_chunks', 'category']
                
                if all(field in data for field in required_fields):
                    valid_count += 1
                else:
                    print(f"⚠️ Line {i+1}: Missing required fields")
                    
            except json.JSONDecodeError:
                print(f"❌ Line {i+1}: Invalid JSON")
        
        print(f"📊 Dataset Validation:")
        print(f"   Total entries: {total_count}")
        print(f"   Valid entries: {valid_count}")
        print(f"   Success rate:  {valid_count/total_count*100:.1f}%")
        
        return valid_count > 0
        
    except Exception as e:
        print(f"❌ Error validating dataset: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ClinChat-RAG Evaluation Runner")
    print("-" * 40)
    
    # Validate dataset first
    print("1️⃣ Validating dataset...")
    if not validate_dataset():
        print("❌ Dataset validation failed. Cannot proceed.")
        sys.exit(1)
    
    print("✅ Dataset validation passed!")
    
    # Run evaluation
    print("\n2️⃣ Running baseline evaluation...")
    success = run_baseline_evaluation()
    
    if success:
        print("\n✅ Evaluation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Evaluation failed!")
        sys.exit(1)