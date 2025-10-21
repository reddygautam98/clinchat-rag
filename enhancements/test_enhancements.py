# =============================================================================
# ClinChat-RAG Enhancement Validation Script
# Test all enhancement modules for functionality and integration
# =============================================================================

import asyncio
import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_clinical_decision_engine():
    """Test the Clinical Decision Support Engine"""
    try:
        logger.info("🧪 Testing Clinical Decision Support Engine...")
        
        from clinical_decision_engine import ClinicalDecisionEngine
        
        engine = ClinicalDecisionEngine()
        
        # Test patient data
        test_patient = {
            'patient_id': 'TEST001',
            'age': 68,
            'gender': 'male',
            'comorbidities': ['diabetes', 'hypertension', 'chronic_kidney_disease'],
            'vital_signs': {
                'systolic_bp': 165,
                'diastolic_bp': 95,
                'heart_rate': 88,
                'temperature': 98.8
            },
            'lab_results': {
                'creatinine': 1.8,
                'hemoglobin': 9.5,
                'hba1c': 8.2
            },
            'medications': ['metformin', 'lisinopril', 'simvastatin'],
            'allergies': ['penicillin']
        }
        
        # Test trajectory analysis
        insights = await engine.analyze_patient_trajectory(test_patient)
        logger.info(f"✅ Trajectory Analysis: Risk Level = {insights.risk_level.value}, Score = {insights.risk_score:.3f}")
        
        # Test drug screening
        safety_report = await engine.drug_interaction_screening(
            medications=test_patient['medications'],
            patient_allergies=test_patient['allergies'],
            patient_conditions=test_patient['comorbidities']
        )
        logger.info(f"✅ Drug Screening: Risk Level = {safety_report.overall_risk.value}, Interactions = {len(safety_report.interactions)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Clinical Decision Engine Test Failed: {str(e)}")
        return False

async def test_medical_data_fusion():
    """Test the Medical Data Fusion Engine"""
    try:
        logger.info("🧪 Testing Medical Data Fusion Engine...")
        
        from medical_data_fusion import MedicalDataFusion
        
        engine = MedicalDataFusion()
        
        # Test lab trend analysis
        lab_history = [
            {"patient_id": "TEST001", "test_name": "creatinine", "value": 1.2, "date": "2024-10-01T08:00:00"},
            {"patient_id": "TEST001", "test_name": "creatinine", "value": 1.4, "date": "2024-10-08T08:00:00"},
            {"patient_id": "TEST001", "test_name": "creatinine", "value": 1.6, "date": "2024-10-15T08:00:00"},
            {"patient_id": "TEST001", "test_name": "hemoglobin", "value": 10.2, "date": "2024-10-01T08:00:00"},
            {"patient_id": "TEST001", "test_name": "hemoglobin", "value": 10.8, "date": "2024-10-08T08:00:00"},
            {"patient_id": "TEST001", "test_name": "hemoglobin", "value": 11.5, "date": "2024-10-15T08:00:00"},
        ]
        
        trend_analysis = await engine.process_lab_trends(lab_history, analysis_days=30)
        logger.info(f"✅ Lab Trends: Overall Trajectory = {trend_analysis.overall_trajectory.value}, Trends Analyzed = {len(trend_analysis.lab_trends)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Medical Data Fusion Test Failed: {str(e)}")
        return False

async def test_voice_interface():
    """Test the Voice Interface Engine"""
    try:
        logger.info("🧪 Testing Voice Interface Engine...")
        
        from clinical_voice_interface import ClinicalVoiceInterface, VoiceCommand, VoiceCommandType
        
        interface = ClinicalVoiceInterface()
        
        # Test voice session
        session_id = await interface.start_voice_session("TEST_USER", "documentation")
        logger.info(f"✅ Voice Session Started: {session_id}")
        
        # Test command processing (mock)
        test_command = VoiceCommand(
            command_id="test_cmd_001",
            command_type=VoiceCommandType.DOCUMENTATION,
            raw_text="Start progress note for patient",
            processed_text="start progress note for patient",
            confidence_score=0.85,
            intent="start_note",
            parameters={"note_type": "progress_note"},
            timestamp=datetime.now()
        )
        
        result = await interface.execute_voice_command(test_command)
        logger.info(f"✅ Voice Command Executed: Status = {result['status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Voice Interface Test Failed: {str(e)}")
        return False

async def test_predictive_analytics():
    """Test the Predictive Analytics Engine"""
    try:
        logger.info("🧪 Testing Predictive Analytics Engine...")
        
        from predictive_analytics import MedicalPredictiveAnalytics
        
        analytics = MedicalPredictiveAnalytics()
        
        # Test readmission prediction
        patient_data = {
            'patient_id': 'TEST001',
            'age': 72,
            'gender': 'female',
            'comorbidities': ['diabetes', 'hypertension', 'heart_failure'],
            'medications': ['metformin', 'lisinopril', 'furosemide'],
            'recent_admissions_30d': 1,
            'length_of_stay': 5
        }
        
        readmission_risk = await analytics.readmission_risk_prediction(patient_data)
        logger.info(f"✅ Readmission Risk: Score = {readmission_risk.score:.3f}, Level = {readmission_risk.risk_level.value}")
        
        # Test sepsis warning
        vital_signs = {
            'temperature': 101.8,
            'heart_rate': 105,
            'respiratory_rate': 24,
            'systolic_bp': 95
        }
        
        lab_results = {
            'white_blood_cells': 13.5,
            'lactate': 2.8
        }
        
        sepsis_alert = await analytics.sepsis_early_warning(
            vital_signs=vital_signs,
            lab_results=lab_results,
            patient_context={'patient_id': 'TEST001'}
        )
        logger.info(f"✅ Sepsis Alert: Probability = {sepsis_alert.probability:.3f}, Severity = {sepsis_alert.severity.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Predictive Analytics Test Failed: {str(e)}")
        return False

async def test_integration_engine():
    """Test the Enhanced Integration Engine"""
    try:
        logger.info("🧪 Testing Enhanced Integration Engine...")
        
        from enhanced_integration import ClinChatEnhancedEngine, PatientAnalysisRequest
        
        engine = ClinChatEnhancedEngine()
        
        # Test comprehensive analysis
        request = PatientAnalysisRequest(
            patient_id="TEST001",
            patient_data={
                "age": 68,
                "gender": "male",
                "comorbidities": ["diabetes", "hypertension"],
                "medications": ["metformin", "lisinopril"],
                "vital_signs": {
                    "systolic_bp": 165,
                    "heart_rate": 88
                },
                "lab_results": {
                    "creatinine": 1.8,
                    "white_blood_cells": 12.5
                }
            },
            analysis_types=["trajectory", "drug_screening", "predictive"]
        )
        
        result = await engine.comprehensive_patient_analysis(request)
        logger.info(f"✅ Comprehensive Analysis: Patient = {result.patient_id}, Confidence = {result.confidence_score:.3f}")
        logger.info(f"✅ Analysis Components: Insights = {bool(result.clinical_insights)}, Safety = {bool(result.safety_report)}, Predictive = {bool(result.predictive_scores)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration Engine Test Failed: {str(e)}")
        return False

async def run_system_validation():
    """Run comprehensive system validation"""
    logger.info("🚀 Starting ClinChat-RAG Enhancement Validation...")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test all modules
    test_results['clinical_decision'] = await test_clinical_decision_engine()
    test_results['medical_data_fusion'] = await test_medical_data_fusion()
    test_results['voice_interface'] = await test_voice_interface()
    test_results['predictive_analytics'] = await test_predictive_analytics()
    test_results['integration_engine'] = await test_integration_engine()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🎯 VALIDATION SUMMARY:")
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for module, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {module.replace('_', ' ').title()}: {status}")
    
    logger.info("=" * 60)
    success_rate = (passed / total) * 100
    logger.info(f"🏆 OVERALL RESULT: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 SYSTEM VALIDATION SUCCESSFUL! Ready for production.")
    elif success_rate >= 60:
        logger.info("⚠️  SYSTEM PARTIALLY VALIDATED. Some issues need attention.")
    else:
        logger.info("🚨 SYSTEM VALIDATION FAILED. Major issues detected.")
    
    return test_results

if __name__ == "__main__":
    try:
        # Run the validation
        results = asyncio.run(run_system_validation())
        
        # Exit with appropriate code
        passed = sum(results.values())
        total = len(results)
        
        if passed == total:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Some failures
            
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR: Validation script failed: {str(e)}")
        sys.exit(2)  # Critical failure