#!/usr/bin/env python3
"""
Simplified Data Warehouse Testing Script
Tests core database functionality with correct model fields
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any

from database.connection import get_db_context, init_database
from database.models import (
    User, Conversation, ClinicalDocument, DocumentAnalysis,
    SystemUsage, ProviderType, AnalysisType, UrgencyLevel, FusionStrategy
)

async def test_data_warehouse():
    """Test core data warehouse functionality"""
    print("🏥 Testing ClinChat-RAG Data Warehouse Core Functionality")
    print("=" * 70)
    
    # Initialize database
    init_database()
    print("✅ Database initialized")
    
    test_results = {
        "database_health": False,
        "user_management": False,
        "clinical_documents": False,
        "analytics": False,
        "data_integrity": False
    }
    
    try:
        with get_db_context() as session:
            # Test 1: User Management
            print("\n👥 Testing User Management...")
            user = User(
                username="test_doctor",
                email="doctor@hospital.com", 
                full_name="Dr. Test User",
                role="clinician",
                department="Emergency Medicine",
                is_active=True
            )
            session.add(user)
            session.commit()
            
            users_count = session.query(User).count()
            print(f"✅ Created user, total users: {users_count}")
            test_results["user_management"] = True
            
            # Test 2: Clinical Documents
            print("\n📄 Testing Clinical Document Processing...")
            document = ClinicalDocument(
                user_id=user.id,
                filename="patient_report.pdf",
                original_filename="patient_report_original.pdf",
                file_type="pdf",
                file_size=1024,
                file_hash="sha256_example_hash",
                status="completed",
                extracted_text="Patient presents with chest pain and shortness of breath.",
                processed_content="Clinical analysis suggests cardiac evaluation needed.",
                patient_id_extracted="PAT-001",
                document_type="emergency_note",
                clinical_entities_extracted={
                    "symptoms": ["chest pain", "shortness of breath"],
                    "patient_id": "PAT-001"
                },
                contains_phi=True,
                phi_redacted=False
            )
            session.add(document)
            session.commit()
            
            # Test Document Analysis
            analysis = DocumentAnalysis(
                document_id=document.id,
                analysis_type=AnalysisType.EMERGENCY_ASSESSMENT,
                provider=ProviderType.FUSION,
                model_name="fusion-gemini-groq",
                summary="Patient requires immediate cardiac workup",
                key_findings=["chest pain", "SOB", "possible ACS"],
                recommendations=["ECG", "Troponin", "Chest X-ray"],
                confidence_score=0.92,
                diagnoses_mentioned=["acute coronary syndrome"],
                medications_mentioned=["aspirin", "nitroglycerin"],
                procedures_mentioned=["ECG", "blood work"]
            )
            session.add(analysis)
            session.commit()
            
            docs_count = session.query(ClinicalDocument).count()
            analyses_count = session.query(DocumentAnalysis).count()
            print(f"✅ Created clinical document, total documents: {docs_count}")
            print(f"✅ Created document analysis, total analyses: {analyses_count}")
            test_results["clinical_documents"] = True
            
            # Test 3: Conversations
            print("\n💬 Testing Conversation Management...")
            conversation = Conversation(
                user_id=user.id,
                input_text="Patient with chest pain, what should I do?",
                analysis_type=AnalysisType.EMERGENCY_ASSESSMENT,
                urgency_level=UrgencyLevel.URGENT,
                fusion_strategy=FusionStrategy.SPEED_FIRST,
                primary_provider=ProviderType.GOOGLE_GEMINI,
                secondary_provider=ProviderType.GROQ,
                final_analysis="Recommend immediate cardiac evaluation",
                confidence_score=0.89,
                processing_time_total=2.5,
                clinical_entities=["chest pain", "emergency"],
                conversation_metadata={"source": "emergency_department"}
            )
            session.add(conversation)
            session.commit()
            
            conv_count = session.query(Conversation).count()
            print(f"✅ Created conversation, total conversations: {conv_count}")
            
            # Test 4: System Analytics
            print("\n📊 Testing System Analytics...")
            usage = SystemUsage(
                total_conversations=conv_count,
                total_users=users_count,
                active_users_daily=users_count,
                total_documents_processed=docs_count,
                gemini_requests=50,
                groq_requests=45,
                fusion_requests=25,
                emergency_assessments=1,
                diagnostic_analyses=0,
                triage_requests=0,
                avg_response_time=2.5,
                system_uptime_hours=24.0,
                date=datetime.now()
            )
            session.add(usage)
            session.commit()
            
            # Generate analytics report
            analytics_report = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {
                    "total_users": session.query(User).count(),
                    "active_users": session.query(User).filter(User.is_active == True).count(),
                    "total_conversations": session.query(Conversation).count(),
                    "total_documents": session.query(ClinicalDocument).count(),
                    "total_analyses": session.query(DocumentAnalysis).count()
                },
                "clinical_metrics": {
                    "emergency_analyses": session.query(DocumentAnalysis).filter(
                        DocumentAnalysis.analysis_type == AnalysisType.EMERGENCY_ASSESSMENT
                    ).count(),
                    "high_confidence": session.query(DocumentAnalysis).filter(
                        DocumentAnalysis.confidence_score > 0.9
                    ).count(),
                    "completed_documents": session.query(ClinicalDocument).filter(
                        ClinicalDocument.status == "completed"
                    ).count()
                },
                "provider_distribution": {
                    provider.value: session.query(DocumentAnalysis).filter(
                        DocumentAnalysis.provider == provider
                    ).count() for provider in ProviderType
                }
            }
            
            print("✅ Analytics report generated:")
            print(json.dumps(analytics_report, indent=2))
            test_results["analytics"] = True
            
            # Test 5: Data Integrity  
            print("\n🔒 Testing Data Integrity...")
            
            # Test foreign key constraints
            try:
                invalid_doc = ClinicalDocument(
                    user_id="invalid-user-id",
                    filename="test.pdf"
                )
                session.add(invalid_doc)
                session.commit()
                print("❌ Foreign key constraint failed")
            except Exception:
                print("✅ Foreign key constraints working")
                session.rollback()
                
            # Test data retrieval with joins
            user_with_docs = session.query(User).join(ClinicalDocument).filter(
                ClinicalDocument.status == "completed"
            ).first()
            
            if user_with_docs:
                print("✅ Complex queries with joins working")
                test_results["data_integrity"] = True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return test_results
    
    # Test Summary
    print("\n" + "=" * 70)
    print("📊 DATA WAREHOUSE TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(test_results.values())
    total = len(test_results)
    success_rate = (passed / total) * 100
    
    print(f"Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    if success_rate >= 80:
        print(f"\n🎉 EXCELLENT! Data warehouse is working well!")
    elif success_rate >= 60:
        print(f"\n⚠️  GOOD: Data warehouse is mostly functional.")
    else:
        print(f"\n🚨 NEEDS ATTENTION: Data warehouse has issues.")
        
    return test_results

if __name__ == "__main__":
    asyncio.run(test_data_warehouse())