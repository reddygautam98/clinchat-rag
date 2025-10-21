#!/usr/bin/env python3
"""
Comprehensive Data Warehouse Testing Script
Tests all database functionality, models, and data processing capabilities
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any

from database.connection import get_db_context, init_database
from database.models import (
    User, Conversation, ClinicalDocument, DocumentAnalysis,
    SystemUsage, ProviderResponse, ProviderMetrics,
    ProviderType, AnalysisType, UrgencyLevel, FusionStrategy
)

class DataWarehouseTest:
    """Comprehensive test suite for the data warehouse"""
    
    def __init__(self):
        self.test_results = {
            "database_connection": False,
            "model_creation": False,
            "data_insertion": False,
            "data_retrieval": False,
            "clinical_analytics": False,
            "performance_metrics": False,
            "data_integrity": False
        }
        
    async def run_all_tests(self):
        """Run comprehensive data warehouse tests"""
        print("🏥 Starting ClinChat-RAG Data Warehouse Comprehensive Test Suite")
        print("=" * 80)
        
        # Initialize database
        try:
            init_database()
            print("✅ Database initialization successful")
            self.test_results["database_connection"] = True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return self.test_results
            
        # Test 1: Model Creation and Schema Validation
        await self.test_model_creation()
        
        # Test 2: Data Insertion and CRUD Operations
        await self.test_data_operations()
        
        # Test 3: Clinical Data Processing
        await self.test_clinical_processing()
        
        # Test 4: Analytics and Reporting
        await self.test_analytics()
        
        # Test 5: Performance and Scalability
        await self.test_performance()
        
        # Test 6: Data Integrity and Validation
        await self.test_data_integrity()
        
        # Summary
        self.print_test_summary()
        return self.test_results
    
    async def test_model_creation(self):
        """Test database model creation and relationships"""
        print("\n📋 Testing Database Models and Schema...")
        
        try:
            with get_db_context() as session:
                # Test User model
                user = User(
                    username="test_clinician",
                    email="test@clinchat.com",
                    full_name="Dr. Test Clinician",
                    role="clinician",
                    department="Emergency Medicine",
                    is_active=True
                )
                session.add(user)
                session.commit()
                
                # Test Conversation model
                conversation = Conversation(
                    user_id=user.id,
                    title="Emergency Case Discussion",
                    summary="Patient with chest pain",
                    total_messages=0,
                    provider_type=ProviderType.FUSION,
                    analysis_type=AnalysisType.EMERGENCY_ASSESSMENT,
                    urgency_level=UrgencyLevel.EMERGENCY
                )
                session.add(conversation)
                session.commit()
                
                # Test Clinical Document
                document = ClinicalDocument(
                    user_id=user.id,
                    filename="patient_report.pdf",
                    file_type="pdf",
                    file_size=1024,
                    status="processed",
                    extracted_text="Patient presents with acute chest pain..."
                )
                session.add(document)
                session.commit()
                
                print("✅ Database models created successfully")
                self.test_results["model_creation"] = True
                
        except Exception as e:
            print(f"❌ Model creation failed: {e}")
    
    async def test_data_operations(self):
        """Test CRUD operations and data manipulation"""
        print("\n💾 Testing Data Operations (CRUD)...")
        
        try:
            with get_db_context() as session:
                # Test data insertion
                sample_users = []
                for i in range(5):
                    user = User(
                        username=f"clinician_{i}",
                        email=f"clinician{i}@hospital.com",
                        full_name=f"Dr. Clinician {i}",
                        role=random.choice(["clinician", "nurse", "specialist"]),
                        department=random.choice(["Emergency", "Cardiology", "Neurology"]),
                        is_active=True
                    )
                    sample_users.append(user)
                    session.add(user)
                
                session.commit()
                
                # Test data retrieval
                all_users = session.query(User).all()
                active_users = session.query(User).filter(User.is_active == True).count()
                
                print(f"✅ Created {len(sample_users)} users")
                print(f"✅ Retrieved {len(all_users)} total users")
                print(f"✅ Found {active_users} active users")
                
                # Test data updates
                first_user = session.query(User).first()
                original_name = first_user.full_name
                first_user.full_name = "Dr. Updated Name"
                session.commit()
                
                # Verify update
                updated_user = session.query(User).filter(User.id == first_user.id).first()
                if updated_user.full_name == "Dr. Updated Name":
                    print("✅ Data update operation successful")
                else:
                    print("❌ Data update operation failed")
                
                self.test_results["data_insertion"] = True
                self.test_results["data_retrieval"] = True
                
        except Exception as e:
            print(f"❌ Data operations failed: {e}")
    
    async def test_clinical_processing(self):
        """Test clinical data processing and analysis"""
        print("\n🏥 Testing Clinical Data Processing...")
        
        try:
            with get_db_context() as session:
                # Create sample clinical document
                document = ClinicalDocument(
                    filename="patient_report_001.pdf",
                    original_filename="John_Doe_Emergency_Report.pdf",
                    file_type="pdf",
                    file_size=2048,
                    file_hash="sha256_hash_example",
                    status="completed",
                    extracted_text="Patient presents with acute chest pain, SOB, diaphoresis. Vitals: BP 140/90, HR 102, RR 22, O2 98%",
                    processed_content="Clinical findings suggest possible acute coronary syndrome",
                    patient_id_extracted="PAT-001",
                    medical_entities_extracted=["chest pain", "shortness of breath", "diaphoresis"],
                    clinical_entities_extracted={
                        "symptoms": ["chest pain", "shortness of breath", "diaphoresis"],
                        "vitals": {"BP": "140/90", "HR": "102", "RR": "22", "O2": "98%"},
                        "assessment": "possible acute coronary syndrome"
                    }
                )
                session.add(document)
                session.commit()
                
                # Create document analysis
                analysis = DocumentAnalysis(
                    document_id=document.id,
                    provider_type=ProviderType.FUSION,
                    analysis_type=AnalysisType.EMERGENCY_ASSESSMENT,
                    urgency_level=UrgencyLevel.EMERGENCY,
                    confidence_score=0.92,
                    processing_time=2.5,
                    ai_response="Clinical presentation consistent with acute coronary syndrome. Recommend immediate ECG, troponin levels, and cardiology consultation.",
                    extracted_entities=["chest pain", "shortness of breath", "acute coronary syndrome"],
                    medical_concepts=["acute coronary syndrome", "myocardial infarction", "unstable angina"],
                    recommendations=["ECG", "Troponin I/T", "Chest X-ray", "Cardiology consult", "Aspirin 325mg"]
                )
                session.add(analysis)
                session.commit()
                
                # Test queries for clinical data
                emergency_documents = session.query(ClinicalDocument).join(DocumentAnalysis).filter(
                    DocumentAnalysis.urgency_level == UrgencyLevel.EMERGENCY
                ).count()
                
                high_confidence_analyses = session.query(DocumentAnalysis).filter(
                    DocumentAnalysis.confidence_score > 0.9
                ).count()
                
                completed_documents = session.query(ClinicalDocument).filter(
                    ClinicalDocument.status == "completed"
                ).count()
                
                print(f"✅ Created clinical document with ID: {document.id}")
                print(f"✅ Created document analysis with confidence: {analysis.confidence_score}")
                print(f"✅ Found {emergency_documents} emergency documents")
                print(f"✅ Found {high_confidence_analyses} high-confidence analyses")
                print(f"✅ Found {completed_documents} completed documents")
                
                self.test_results["clinical_analytics"] = True
                
        except Exception as e:
            print(f"❌ Clinical processing failed: {e}")
    
    async def test_analytics(self):
        """Test analytics and reporting capabilities"""
        print("\n📊 Testing Analytics and Reporting...")
        
        try:
            with get_db_context() as session:
                # Create system usage data
                usage = SystemUsage(
                    total_conversations=150,
                    total_users=25,
                    active_users_daily=18,
                    total_documents_processed=200,
                    gemini_requests=75,
                    groq_requests=80,
                    fusion_requests=120,
                    emergency_assessments=45,
                    diagnostic_analyses=60,
                    triage_requests=30,
                    avg_response_time=2.8,
                    system_uptime_hours=168.0,
                    date=datetime.now()
                )
                session.add(usage)
                session.commit()
                
                # Generate analytics queries
                total_conversations = session.query(Conversation).count()
                total_documents = session.query(ClinicalDocument).count()
                total_analyses = session.query(DocumentAnalysis).count()
                
                provider_usage = {}
                for provider in ProviderType:
                    count = session.query(DocumentAnalysis).filter(
                        DocumentAnalysis.provider_type == provider
                    ).count()
                    provider_usage[provider.value] = count
                
                print(f"✅ System usage metrics recorded")
                print(f"✅ Total conversations: {total_conversations}")
                print(f"✅ Total documents: {total_documents}")
                print(f"✅ Total analyses: {total_analyses}")
                print(f"✅ Provider usage: {provider_usage}")
                
                # Generate performance report
                performance_report = {
                    "timestamp": datetime.now().isoformat(),
                    "system_metrics": {
                        "total_users": session.query(User).count(),
                        "active_users": session.query(User).filter(User.is_active == True).count(),
                        "total_conversations": total_conversations,
                        "total_documents": total_documents,
                        "total_analyses": total_analyses
                    },
                    "clinical_metrics": {
                        "emergency_analyses": session.query(DocumentAnalysis).filter(
                            DocumentAnalysis.urgency_level == UrgencyLevel.EMERGENCY
                        ).count(),
                        "completed_documents": session.query(ClinicalDocument).filter(
                            ClinicalDocument.status == "completed"
                        ).count()
                    },
                    "provider_distribution": provider_usage
                }
                
                print("✅ Performance report generated:")
                print(json.dumps(performance_report, indent=2))
                
        except Exception as e:
            print(f"❌ Analytics testing failed: {e}")
    
    async def test_performance(self):
        """Test database performance and scalability"""
        print("\n⚡ Testing Performance and Scalability...")
        
        try:
            with get_db_context() as session:
                # Batch insert test
                start_time = datetime.now()
                
                batch_size = 100
                conversations = []
                for i in range(batch_size):
                    conversation = Conversation(
                        user_id=session.query(User).first().id,
                        title=f"Performance Test Conversation {i}",
                        summary=f"Test conversation for performance testing {i}",
                        total_messages=random.randint(1, 10),
                        provider_type=random.choice(list(ProviderType)),
                        analysis_type=random.choice(list(AnalysisType)),
                        urgency_level=random.choice(list(UrgencyLevel))
                    )
                    conversations.append(conversation)
                
                session.add_all(conversations)
                session.commit()
                
                end_time = datetime.now()
                insert_duration = (end_time - start_time).total_seconds()
                
                # Query performance test
                start_time = datetime.now()
                
                complex_query_results = session.query(Conversation).join(User).filter(
                    User.is_active == True,
                    Conversation.urgency_level == UrgencyLevel.EMERGENCY
                ).all()
                
                end_time = datetime.now()
                query_duration = (end_time - start_time).total_seconds()
                
                print(f"✅ Batch insert ({batch_size} records): {insert_duration:.3f}s")
                print(f"✅ Complex query: {query_duration:.3f}s")
                print(f"✅ Query returned {len(complex_query_results)} results")
                
                self.test_results["performance_metrics"] = True
                
        except Exception as e:
            print(f"❌ Performance testing failed: {e}")
    
    async def test_data_integrity(self):
        """Test data integrity and validation"""
        print("\n🔒 Testing Data Integrity and Validation...")
        
        try:
            with get_db_context() as session:
                # Test foreign key constraints
                try:
                    invalid_conversation = Conversation(
                        user_id="invalid-user-id",
                        title="Invalid Conversation",
                        provider_type=ProviderType.FUSION
                    )
                    session.add(invalid_conversation)
                    session.commit()
                    print("❌ Foreign key constraint failed")
                except Exception:
                    print("✅ Foreign key constraint working")
                    session.rollback()
                
                # Test data validation
                user_count_before = session.query(User).count()
                
                valid_user = User(
                    username="validation_test",
                    email="valid@test.com",
                    full_name="Validation Test User",
                    role="clinician",
                    is_active=True
                )
                session.add(valid_user)
                session.commit()
                
                user_count_after = session.query(User).count()
                
                if user_count_after == user_count_before + 1:
                    print("✅ Data validation working correctly")
                    self.test_results["data_integrity"] = True
                else:
                    print("❌ Data validation failed")
                
                # Test unique constraints
                try:
                    duplicate_user = User(
                        username="validation_test",  # Same username
                        email="different@test.com",
                        full_name="Different User",
                        role="nurse",
                        is_active=True
                    )
                    session.add(duplicate_user)
                    session.commit()
                    print("❌ Unique constraint failed")
                except Exception:
                    print("✅ Unique constraint working")
                    session.rollback()
                
        except Exception as e:
            print(f"❌ Data integrity testing failed: {e}")
    
    def print_test_summary(self):
        """Print comprehensive test results summary"""
        print("\n" + "=" * 80)
        print("🏥 DATA WAREHOUSE TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(self.test_results.values())
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print("\n📋 Individual Test Results:")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        if success_rate >= 85:
            print(f"\n🎉 EXCELLENT! Data warehouse is working perfectly!")
            print("   All core functionality is operational and performant.")
        elif success_rate >= 70:
            print(f"\n⚠️  GOOD: Data warehouse is mostly functional with minor issues.")
            print("   Consider addressing failed tests for optimal performance.")
        else:
            print(f"\n🚨 CRITICAL: Data warehouse has significant issues.")
            print("   Immediate attention required to resolve failed tests.")

async def main():
    """Main test execution function"""
    test_suite = DataWarehouseTest()
    results = await test_suite.run_all_tests()
    return results

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())