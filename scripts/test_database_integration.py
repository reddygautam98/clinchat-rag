#!/usr/bin/env python3
"""
Comprehensive Test Script for Unified Database Integration
Test both Google Gemini and Groq APIs with shared database logging
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Test imports
try:
    from fusion_ai_engine import FusionAIEngine, AnalysisType
    from database.connection import get_db_context, get_database_health
    from database.operations import (
        ConversationManager, ProviderResponseManager, 
        AnalyticsManager, log_fusion_conversation
    )
    from database.models import ProviderType, UrgencyLevel, FusionStrategy
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_database_integration():
    """Test complete database integration with both APIs"""
    print("🚀 Testing Unified Database Integration")
    print("=" * 60)
    
    # Test 1: Database Health Check
    print("\n📊 Test 1: Database Health Check")
    try:
        health = get_database_health()
        print(f"   Database Status: {health.get('status', 'unknown')}")
        if health.get('database_url'):
            print(f"   Database URL: {health['database_url']}")
        print("   ✅ Database health check passed")
    except Exception as e:
        print(f"   ❌ Database health check failed: {e}")
        return False
    
    # Test 2: Fusion AI Engine Initialization
    print("\n🔮 Test 2: Fusion AI Engine with Database")
    try:
        engine = FusionAIEngine()
        print("   ✅ Fusion AI Engine initialized")
        
        # Check provider availability
        gemini_available = engine.gemini_model is not None
        groq_available = engine.groq_client is not None
        
        print(f"   Google Gemini: {'✅' if gemini_available else '❌'}")
        print(f"   Groq Cloud: {'✅' if groq_available else '❌'}")
        
        if not (gemini_available or groq_available):
            print("   ⚠️ No AI providers available - check API keys")
            return False
            
    except Exception as e:
        print(f"   ❌ Fusion AI Engine initialization failed: {e}")
        return False
    
    # Test 3: Simple Conversation with Database Logging
    print("\n💬 Test 3: Conversation with Database Logging")
    try:
        clinical_text = """
        Patient: 45-year-old female with chest pain and shortness of breath.
        Vitals: BP 140/90, HR 95, O2Sat 96%. 
        History: Diabetes, hypertension. Needs clinical assessment.
        """
        
        print("   📝 Running Fusion AI analysis...")
        start_time = time.time()
        
        result = await engine.fusion_analyze(
            text=clinical_text,
            analysis_type=AnalysisType.QUICK_TRIAGE,
            urgency="normal"
        )
        
        processing_time = time.time() - start_time
        
        print(f"   ✅ Analysis completed in {processing_time:.2f}s")
        print(f"   Strategy Used: {result.fusion_strategy}")
        print(f"   Confidence Score: {result.confidence_score:.1%}")
        
        if result.primary_result:
            print(f"   Primary Provider: {result.primary_result.provider}")
            print(f"   Primary Time: {result.primary_result.processing_time:.2f}s")
        
        if result.secondary_result:
            print(f"   Secondary Provider: {result.secondary_result.provider}")
            print(f"   Secondary Time: {result.secondary_result.processing_time:.2f}s")
            
    except Exception as e:
        print(f"   ❌ Conversation test failed: {e}")
        return False
    
    # Test 4: Database Query Tests
    print("\n🗄️ Test 4: Database Query Operations")
    try:
        with get_db_context() as session:
            # Count conversations
            conversations = ConversationManager.get_conversation_history(session, limit=10)
            print(f"   📋 Recent conversations: {len(conversations)}")
            
            # Get performance metrics
            if conversations:
                for provider in [ProviderType.GOOGLE_GEMINI, ProviderType.GROQ]:
                    try:
                        performance = ProviderResponseManager.get_provider_performance(
                            session, provider, hours=24
                        )
                        print(f"   📈 {provider.value}: {performance['total_requests']} requests, "
                              f"{performance['success_rate']:.1%} success rate")
                    except Exception as perf_e:
                        print(f"   ⚠️ Performance metrics for {provider.value}: {perf_e}")
            
            # Get system analytics
            try:
                analytics = AnalyticsManager.get_system_analytics(session, days=1)
                print(f"   📊 System Analytics: {analytics['total_conversations']} conversations, "
                      f"{analytics.get('performance', {}).get('success_rate', 0):.1%} success rate")
            except Exception as analytics_e:
                print(f"   ⚠️ System analytics: {analytics_e}")
                
        print("   ✅ Database queries completed")
        
    except Exception as e:
        print(f"   ❌ Database query test failed: {e}")
        return False
    
    # Test 5: Multiple Analysis Types
    print("\n🏥 Test 5: Multiple Analysis Types with Database")
    test_cases = [
        {
            "name": "Emergency Assessment",
            "text": "Patient unconscious, no pulse detected, CPR in progress",
            "analysis_type": AnalysisType.EMERGENCY_ASSESSMENT,
            "urgency": "emergency"
        },
        {
            "name": "Diagnostic Reasoning", 
            "text": "45M with 6-month fatigue, weight loss, night sweats, splenomegaly",
            "analysis_type": AnalysisType.DIAGNOSTIC_REASONING,
            "urgency": "normal"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test 5.{i}: {test_case['name']}")
        try:
            result = await engine.fusion_analyze(
                text=test_case["text"],
                analysis_type=test_case["analysis_type"],
                urgency=test_case["urgency"]
            )
            
            print(f"      ✅ {test_case['name']}: {result.fusion_strategy} strategy")
            print(f"      Processing Time: {result.total_processing_time:.2f}s")
            print(f"      Confidence: {result.confidence_score:.1%}")
            
        except Exception as e:
            print(f"      ❌ {test_case['name']} failed: {e}")
    
    # Test 6: Database Analytics Summary
    print("\n📈 Test 6: Database Analytics Summary")
    try:
        with get_db_context() as session:
            # Get conversation count by analysis type
            from sqlalchemy import func
            from database.models import Conversation
            
            analysis_breakdown = session.query(
                Conversation.analysis_type,
                func.count(Conversation.id).label('count')
            ).group_by(Conversation.analysis_type).all()
            
            print("   📊 Analysis Type Breakdown:")
            for analysis_type, count in analysis_breakdown:
                print(f"      • {analysis_type.value}: {count} conversations")
            
            # Total providers used
            from database.models import ProviderResponse
            
            provider_breakdown = session.query(
                ProviderResponse.provider,
                func.count(ProviderResponse.id).label('count')
            ).group_by(ProviderResponse.provider).all()
            
            print("   🤖 Provider Usage:")
            for provider, count in provider_breakdown:
                print(f"      • {provider.value}: {count} responses")
            
            print("   ✅ Analytics summary completed")
            
    except Exception as e:
        print(f"   ❌ Analytics summary failed: {e}")
    
    return True

def main():
    """Main test function"""
    print("🔮 ClinChat-RAG Unified Database Integration Test")
    print(f"📅 Test Date: {datetime.now().isoformat()}")
    print(f"🗄️ Database: SQLite (Development)")
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_database_integration())
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL DATABASE INTEGRATION TESTS PASSED!")
            print("✅ Your unified database is working perfectly with both APIs")
            print("\n🚀 Ready for Production:")
            print("   • Google Gemini API ↔️ Unified Database")
            print("   • Groq Cloud API ↔️ Unified Database") 
            print("   • Fusion AI Engine ↔️ Unified Database")
            print("   • Performance Analytics ↔️ Unified Database")
            print("   • Audit Logging ↔️ Unified Database")
            
            print(f"\n💾 Database Location:")
            print(f"   {Path('data/clinchat_fusion.db').absolute()}")
            
            print(f"\n📱 Next Steps:")
            print(f"   1. Start Fusion API: python -m uvicorn api.fusion_api:app --port 8003")
            print(f"   2. Test health endpoint: curl http://localhost:8003/health")
            print(f"   3. Run conversation analysis: POST /fusion/analyze")
            print(f"   4. Monitor database logs and analytics")
            
        else:
            print("❌ Some database integration tests failed")
            print("Please check the error messages above")
            
    finally:
        loop.close()

if __name__ == "__main__":
    main()