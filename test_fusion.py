#!/usr/bin/env python3
"""
ClinChat-RAG Quick Test Script
Tests the Fusion AI functionality directly
"""

import sys
import os
from pathlib import Path

def main():
    """Test the Fusion AI engine directly"""
    
    # Set up the Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("ClinChat-RAG Fusion AI Test")
    print("=" * 40)
    
    # Verify API keys
    gemini_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return 1
        
    if not groq_key:
        print("ERROR: GROQ_API_KEY not found in environment")
        return 1
    
    print("✓ API keys configured")
    
    # Test database connection
    try:
        from database.connection import DatabaseManager
        db = DatabaseManager()
        print("✓ Database manager loaded")
        
        # Test database connection
        with db.get_session() as session:
            print("✓ Database connection successful")
        
    except Exception as e:
        print(f"Database error: {e}")
        # Continue without database
    
    # Test Fusion AI engine
    try:
        from fusion_ai_engine import FusionAIEngine
        fusion = FusionAIEngine()
        print("✓ Fusion AI engine loaded")
        
        # Test a simple query
        import asyncio
        from fusion_ai_engine import AnalysisType
        
        test_query = "What is the primary purpose of this clinical assistant?"
        
        print(f"\nTesting Fusion AI with query: '{test_query}'")
        print("-" * 60)
        
        async def run_test():
            result = await fusion.fusion_analyze(
                text=test_query,
                analysis_type=AnalysisType.QUICK_TRIAGE
            )
            return result
        
        result = asyncio.run(run_test())
        
        print("✓ Fusion AI Response:")
        print(f"   Strategy: {result.fusion_strategy}")
        print(f"   Primary Provider: {result.primary_result.provider}")
        print(f"   Response: {result.consensus_analysis[:100]}...")
        print(f"   Confidence: {result.confidence_score}")
        print(f"   Processing Time: {result.total_processing_time:.2f}s")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Failed to test Fusion AI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())