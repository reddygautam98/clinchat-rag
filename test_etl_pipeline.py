#!/usr/bin/env python3
"""
Data Warehouse ETL Pipeline Test
Tests ingestion of clinical datasets and data processing
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from database.connection import get_db_context, init_database
from database.models import (
    ClinicalDocument, DocumentAnalysis, SystemUsage,
    ProviderType, AnalysisType, UrgencyLevel
)

class ETLPipelineTest:
    """Test ETL pipeline functionality"""
    
    def __init__(self):
        self.data_dir = Path("scripts/data/raw")
        self.test_results = {
            "data_loading": False,
            "data_transformation": False,
            "data_storage": False,
            "data_analytics": False,
            "performance": False
        }
        
    def test_data_loading(self):
        """Test loading raw clinical datasets"""
        print("📥 Testing Data Loading...")
        
        try:
            # Load adverse events data
            ae_file = self.data_dir / "ae_data_safety_database_5k.csv"
            if ae_file.exists():
                ae_data = pd.read_csv(ae_file)
                print(f"✅ Loaded Adverse Events: {len(ae_data)} records")
                print(f"   Columns: {list(ae_data.columns)}")
                
                # Basic data quality checks
                print(f"   Missing values: {ae_data.isnull().sum().sum()}")
                print(f"   Duplicate records: {ae_data.duplicated().sum()}")
            
            # Load lab data
            lab_file = self.data_dir / "lab_data_chemistry_panel_5k.csv"
            if lab_file.exists():
                lab_data = pd.read_csv(lab_file)
                print(f"✅ Loaded Laboratory Data: {len(lab_data)} records")
                print(f"   Columns: {list(lab_data.columns)}")
                
                # Data quality assessment
                numeric_cols = lab_data.select_dtypes(include=['number']).columns
                print(f"   Numeric columns: {len(numeric_cols)}")
                
            self.test_results["data_loading"] = True
            return ae_data, lab_data
            
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            return None, None
    
    def test_data_transformation(self, ae_data, lab_data):
        """Test data transformation and cleansing"""
        print("\n🔄 Testing Data Transformation...")
        
        try:
            if ae_data is not None:
                # Transform adverse events data
                ae_transformed = ae_data.copy()
                
                # Clean and standardize (using correct column names)
                ae_transformed['ae_term'] = ae_transformed['ae_term'].str.strip().str.title()
                ae_transformed['severity_grade'] = pd.to_numeric(ae_transformed['severity_grade'], errors='coerce')
                
                # Create calculated fields
                ae_transformed['duration_days'] = (
                    pd.to_datetime(ae_transformed['end_date'], errors='coerce') - 
                    pd.to_datetime(ae_transformed['start_date'], errors='coerce')
                ).dt.days
                
                # Category encoding
                ae_transformed['severity_category'] = ae_transformed['severity_grade'].map({
                    1: 'Mild', 2: 'Mild', 3: 'Moderate', 4: 'Severe', 5: 'Life-threatening'
                })
                
                print(f"✅ Transformed adverse events data")
                print(f"   Added duration calculation")
                print(f"   Added severity categories")
                
            if lab_data is not None:
                # Transform lab data
                lab_transformed = lab_data.copy()
                
                # Standardize test names
                lab_transformed['test_name'] = lab_transformed['test_name'].str.strip().str.upper()
                
                # Handle numeric values
                lab_transformed['test_value'] = pd.to_numeric(lab_transformed['test_value'], errors='coerce')
                
                # Create abnormal flags
                lab_transformed['is_abnormal'] = lab_transformed['abnormal_flag'] == 'Y'
                
                print(f"✅ Transformed laboratory data")
                print(f"   Standardized test names")
                print(f"   Created abnormal indicators")
                
            self.test_results["data_transformation"] = True
            return ae_transformed, lab_transformed
            
        except Exception as e:
            print(f"❌ Data transformation failed: {e}")
            return ae_data, lab_data
    
    def test_data_storage(self, ae_data, lab_data):
        """Test storing processed data in warehouse"""
        print("\n💾 Testing Data Storage...")
        
        try:
            with get_db_context() as session:
                # Store sample adverse events as clinical documents
                sample_ae = ae_data.head(10) if ae_data is not None else []
                
                for idx, row in enumerate(sample_ae.itertuples()):
                    # Create clinical document record
                    document_text = f"""
                    Adverse Event Report
                    Patient ID: {row.patient_id}
                    Event: {row.ae_term}
                    Severity: {row.severity_grade}
                    Relationship: {row.relationship_to_drug}
                    Onset: {row.start_date}
                    Resolution: {row.end_date}
                    Outcome: {row.outcome}
                    Serious: {getattr(row, 'serious_flag', 'Unknown')}
                    """
                    
                    doc = ClinicalDocument(
                        filename=f"ae_report_{row.patient_id}_{idx}.txt",
                        original_filename=f"adverse_event_{row.patient_id}.txt",
                        file_type="txt",
                        file_size=len(document_text),
                        file_hash=f"hash_{idx}",
                        status="completed",
                        extracted_text=document_text,
                        patient_id_extracted=row.patient_id,
                        document_type="adverse_event_report",
                        clinical_entities_extracted={
                            "ae_term": row.ae_term,
                            "severity": row.severity_grade,
                            "patient_id": row.patient_id
                        }
                    )
                    session.add(doc)
                    
                session.commit()
                
                # Verify storage
                stored_docs = session.query(ClinicalDocument).filter(
                    ClinicalDocument.document_type == "adverse_event_report"
                ).count()
                
                print(f"✅ Stored {stored_docs} adverse event documents")
                
                # Store lab data as analyses
                if lab_data is not None:
                    sample_lab = lab_data.head(5)
                    
                    for idx, row in enumerate(sample_lab.itertuples()):
                        analysis = DocumentAnalysis(
                            document_id=session.query(ClinicalDocument).first().id,
                            analysis_type=AnalysisType.DIAGNOSTIC_REASONING,
                            provider=ProviderType.FUSION,
                            model_name="clinical-data-processor",
                        summary=f"Laboratory result for {row.test_name}: {row.test_value} {getattr(row, 'units', '')}",
                        key_findings=[row.test_name, str(row.test_value)],
                            recommendations=["Follow up if abnormal"] if getattr(row, 'abnormal_flag', 'N') == 'Y' else ["Normal result"],
                            confidence_score=0.95
                        )
                        session.add(analysis)
                    
                    session.commit()
                    
                    stored_analyses = session.query(DocumentAnalysis).filter(
                        DocumentAnalysis.model_name == "clinical-data-processor"
                    ).count()
                    
                    print(f"✅ Stored {stored_analyses} laboratory analyses")
                
            self.test_results["data_storage"] = True
            
        except Exception as e:
            print(f"❌ Data storage failed: {e}")
    
    def test_data_analytics(self):
        """Test analytics on stored data"""
        print("\n📊 Testing Data Analytics...")
        
        try:
            with get_db_context() as session:
                # Basic analytics queries
                total_documents = session.query(ClinicalDocument).count()
                ae_documents = session.query(ClinicalDocument).filter(
                    ClinicalDocument.document_type == "adverse_event_report"
                ).count()
                
                total_analyses = session.query(DocumentAnalysis).count()
                lab_analyses = session.query(DocumentAnalysis).filter(
                    DocumentAnalysis.model_name == "clinical-data-processor"
                ).count()
                
                # Generate analytics report
                analytics = {
                    "timestamp": datetime.now().isoformat(),
                    "warehouse_metrics": {
                        "total_documents": total_documents,
                        "adverse_event_reports": ae_documents,
                        "total_analyses": total_analyses,
                        "laboratory_analyses": lab_analyses
                    },
                    "data_types": {
                        "clinical_documents": session.query(ClinicalDocument.document_type).distinct().count(),
                        "analysis_providers": session.query(DocumentAnalysis.provider).distinct().count()
                    }
                }
                
                print("✅ Generated warehouse analytics:")
                print(json.dumps(analytics, indent=2))
                
                # Create system usage record
                usage = SystemUsage(
                    total_conversations=0,
                    total_users=1,
                    active_users_daily=1,
                    total_documents_processed=total_documents,
                    gemini_requests=0,
                    groq_requests=0,
                    fusion_requests=total_analyses,
                    emergency_assessments=0,
                    diagnostic_analyses=lab_analyses,
                    triage_requests=0,
                    avg_response_time=1.0,
                    system_uptime_hours=1.0,
                    date=datetime.now()
                )
                session.add(usage)
                session.commit()
                
                print("✅ Updated system usage metrics")
                
            self.test_results["data_analytics"] = True
            
        except Exception as e:
            print(f"❌ Analytics testing failed: {e}")
    
    def test_performance(self, ae_data, lab_data):
        """Test data processing performance"""
        print("\n⚡ Testing Performance...")
        
        try:
            # Measure data processing speed
            start_time = datetime.now()
            
            if ae_data is not None:
                # Process adverse events data
                ae_summary = {
                    "total_records": len(ae_data),
                    "unique_patients": ae_data['patient_id'].nunique(),
                    "unique_events": ae_data['ae_term'].nunique(),
                    "severe_events": (ae_data['severity_grade'] >= 4).sum(),
                    "drug_related": (ae_data['relationship_to_drug'].isin(['Probably Related', 'Definitely Related'])).sum()
                }
                
            if lab_data is not None:
                # Process lab data
                lab_summary = {
                    "total_records": len(lab_data),
                    "unique_patients": lab_data['patient_id'].nunique(),
                    "unique_tests": lab_data['test_name'].nunique(),
                    "abnormal_results": (lab_data['abnormal_flag'] == 'Y').sum()
                }
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            performance_metrics = {
                "processing_time_seconds": processing_time,
                "records_per_second": (len(ae_data) + len(lab_data)) / processing_time if processing_time > 0 else 0,
                "adverse_events_summary": ae_summary if ae_data is not None else {},
                "laboratory_summary": lab_summary if lab_data is not None else {}
            }
            
            print("✅ Performance metrics:")
            print(json.dumps(performance_metrics, indent=2))
            
            self.test_results["performance"] = True
            
        except Exception as e:
            print(f"❌ Performance testing failed: {e}")
    
    def run_all_tests(self):
        """Run complete ETL pipeline test"""
        print("🏥 Testing ClinChat-RAG Data Warehouse ETL Pipeline")
        print("=" * 60)
        
        # Initialize database
        init_database()
        print("✅ Database initialized")
        
        # Test data loading
        ae_data, lab_data = self.test_data_loading()
        
        # Test data transformation
        ae_transformed, lab_transformed = self.test_data_transformation(ae_data, lab_data)
        
        # Test data storage
        self.test_data_storage(ae_transformed, lab_transformed)
        
        # Test analytics
        self.test_data_analytics()
        
        # Test performance
        self.test_performance(ae_transformed, lab_transformed)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ETL PIPELINE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(self.test_results.values())
        total = len(self.test_results)
        success_rate = (passed / total) * 100
        
        print(f"Success Rate: {success_rate:.1f}% ({passed}/{total})")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT! ETL pipeline is working perfectly!")
        elif success_rate >= 60:
            print(f"\n⚠️  GOOD: ETL pipeline is mostly functional.")
        else:
            print(f"\n🚨 NEEDS ATTENTION: ETL pipeline has issues.")

if __name__ == "__main__":
    test = ETLPipelineTest()
    test.run_all_tests()