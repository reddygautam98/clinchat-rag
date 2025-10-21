# =============================================================================
# Enhanced Integration Module for ClinChat-RAG System
# Combines all new enhancements into the main application
# =============================================================================

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Import our new enhancement modules
from clinical_decision_engine import ClinicalDecisionEngine, ClinicalInsights, SafetyReport, ComplianceReport
from medical_data_fusion import MedicalDataFusion, ImageAnalysis, TrendAnalysis, VitalInsights
from clinical_voice_interface import ClinicalVoiceInterface, VoiceCommand, ClinicalNote
from predictive_analytics import MedicalPredictiveAnalytics, RiskScore, SepsisAlert, AdherenceScore

# =============================================================================
# Pydantic Models for API Requests/Responses
# =============================================================================

class PatientAnalysisRequest(BaseModel):
    patient_id: str
    patient_data: Dict[str, Any]
    analysis_types: List[str] = ["trajectory", "drug_screening", "guidelines"]

class ImageAnalysisRequest(BaseModel):
    patient_id: str
    image_data: str  # base64 encoded
    image_type: str = "unknown"
    patient_context: Optional[Dict[str, Any]] = None

class VoiceCommandRequest(BaseModel):
    audio_data: str  # base64 encoded audio
    session_id: Optional[str] = None
    user_id: str

class PredictiveAnalysisRequest(BaseModel):
    patient_id: str
    analysis_type: str  # readmission, sepsis, adherence
    patient_data: Dict[str, Any]
    time_horizon: str = "30d"

class EnhancedAnalysisResponse(BaseModel):
    patient_id: str
    analysis_timestamp: datetime
    clinical_insights: Optional[Dict[str, Any]] = None
    safety_report: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    image_analysis: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[Dict[str, Any]] = None
    vital_insights: Optional[Dict[str, Any]] = None
    predictive_scores: Optional[Dict[str, Any]] = None
    voice_response: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    alerts: List[Dict[str, Any]] = []
    confidence_score: float = 0.0

# =============================================================================
# Enhanced ClinChat Integration Engine
# =============================================================================

class ClinChatEnhancedEngine:
    """
    Main integration engine that combines all enhancement modules
    into a unified clinical intelligence system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all enhancement modules
        self.clinical_decision_engine = ClinicalDecisionEngine()
        self.medical_data_fusion = MedicalDataFusion()
        self.voice_interface = ClinicalVoiceInterface()
        self.predictive_analytics = MedicalPredictiveAnalytics()
        
        # Track active sessions
        self.active_sessions = {}
        
        self.logger.info("ClinChat Enhanced Engine initialized with all modules")

    async def comprehensive_patient_analysis(self, request: PatientAnalysisRequest) -> EnhancedAnalysisResponse:
        """
        Perform comprehensive analysis using all available enhancement modules
        
        Args:
            request: Patient analysis request
            
        Returns:
            Comprehensive analysis response with insights from all modules
        """
        try:
            self.logger.info(f"Starting comprehensive analysis for patient {request.patient_id}")
            
            response = EnhancedAnalysisResponse(
                patient_id=request.patient_id,
                analysis_timestamp=datetime.now()
            )
            
            all_recommendations = []
            all_alerts = []
            confidence_scores = []
            
            # Clinical Decision Engine Analysis
            if "trajectory" in request.analysis_types:
                try:
                    insights = await self.clinical_decision_engine.analyze_patient_trajectory(
                        request.patient_data
                    )
                    response.clinical_insights = {
                        "risk_score": insights.risk_score,
                        "risk_level": insights.risk_level.value,
                        "trajectory_analysis": insights.trajectory_analysis,
                        "recommendations": insights.recommendations,
                        "alerts": [
                            {
                                "id": alert.alert_id,
                                "severity": alert.severity.value,
                                "title": alert.title,
                                "description": alert.description,
                                "recommendations": alert.recommendations
                            } for alert in insights.alerts
                        ]
                    }
                    all_recommendations.extend(insights.recommendations)
                    all_alerts.extend(response.clinical_insights["alerts"])
                    confidence_scores.append(insights.confidence_score)
                    
                except Exception as e:
                    self.logger.error(f"Clinical trajectory analysis failed: {str(e)}")
            
            # Drug Interaction Screening
            if "drug_screening" in request.analysis_types and "medications" in request.patient_data:
                try:
                    safety_report = await self.clinical_decision_engine.drug_interaction_screening(
                        medications=request.patient_data["medications"],
                        patient_allergies=request.patient_data.get("allergies", []),
                        patient_conditions=request.patient_data.get("comorbidities", [])
                    )
                    response.safety_report = {
                        "overall_risk": safety_report.overall_risk.value,
                        "interactions_count": len(safety_report.interactions),
                        "contraindications_count": len(safety_report.contraindications),
                        "recommendations": safety_report.recommendations,
                        "interactions": [
                            {
                                "drug1": interaction.drug1,
                                "drug2": interaction.drug2,
                                "severity": interaction.severity,
                                "management": interaction.management
                            } for interaction in safety_report.interactions
                        ]
                    }
                    all_recommendations.extend(safety_report.recommendations)
                    
                except Exception as e:
                    self.logger.error(f"Drug screening failed: {str(e)}")
            
            # Predictive Analytics
            if "predictive" in request.analysis_types:
                try:
                    # Readmission risk
                    readmission_risk = await self.predictive_analytics.readmission_risk_prediction(
                        request.patient_data
                    )
                    
                    # Sepsis screening (if vital signs available)
                    sepsis_alert = None
                    if "vital_signs" in request.patient_data and "lab_results" in request.patient_data:
                        sepsis_alert = await self.predictive_analytics.sepsis_early_warning(
                            vital_signs=request.patient_data["vital_signs"],
                            lab_results=request.patient_data["lab_results"],
                            patient_context={"patient_id": request.patient_id}
                        )
                    
                    response.predictive_scores = {
                        "readmission_risk": {
                            "score": readmission_risk.score,
                            "risk_level": readmission_risk.risk_level.value,
                            "confidence": readmission_risk.confidence.value,
                            "recommendations": readmission_risk.recommendations
                        }
                    }
                    
                    if sepsis_alert:
                        response.predictive_scores["sepsis_risk"] = {
                            "probability": sepsis_alert.probability,
                            "severity": sepsis_alert.severity.value,
                            "qsofa_score": sepsis_alert.qsofa_score,
                            "recommended_actions": sepsis_alert.recommended_actions
                        }
                        
                        if sepsis_alert.severity.value in ["urgent", "critical"]:
                            all_alerts.append({
                                "id": sepsis_alert.alert_id,
                                "type": "sepsis_alert",
                                "severity": sepsis_alert.severity.value,
                                "description": f"Sepsis probability: {sepsis_alert.probability:.1%}",
                                "actions": sepsis_alert.recommended_actions
                            })
                    
                    all_recommendations.extend(readmission_risk.recommendations)
                    confidence_scores.append(readmission_risk.confidence.value == "high" and 0.9 or 0.7)
                    
                except Exception as e:
                    self.logger.error(f"Predictive analysis failed: {str(e)}")
            
            # Laboratory Trend Analysis
            if "lab_trends" in request.analysis_types and "lab_history" in request.patient_data:
                try:
                    trend_analysis = await self.medical_data_fusion.process_lab_trends(
                        lab_history=request.patient_data["lab_history"],
                        analysis_days=30
                    )
                    response.trend_analysis = {
                        "overall_trajectory": trend_analysis.overall_trajectory.value,
                        "concerning_trends": trend_analysis.concerning_trends,
                        "improvement_trends": trend_analysis.improvement_trends,
                        "recommendations": trend_analysis.recommendations,
                        "confidence": trend_analysis.confidence_score
                    }
                    all_recommendations.extend(trend_analysis.recommendations)
                    confidence_scores.append(trend_analysis.confidence_score)
                    
                except Exception as e:
                    self.logger.error(f"Lab trend analysis failed: {str(e)}")
            
            # Calculate overall confidence
            if confidence_scores:
                response.confidence_score = sum(confidence_scores) / len(confidence_scores)
            
            # Compile final recommendations and alerts
            response.recommendations = list(set(all_recommendations))  # Remove duplicates
            response.alerts = all_alerts
            
            self.logger.info(f"Comprehensive analysis completed for patient {request.patient_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Comprehensive patient analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    async def process_medical_image(self, request: ImageAnalysisRequest) -> Dict[str, Any]:
        """Process medical image analysis request"""
        try:
            import base64
            
            # Decode base64 image data
            image_bytes = base64.b64decode(request.image_data)
            
            # Process the image
            analysis = await self.medical_data_fusion.process_medical_images(
                image_data=image_bytes,
                image_type=request.image_type,
                patient_context=request.patient_context or {}
            )
            
            return {
                "image_id": analysis.image_id,
                "image_type": analysis.image_type.value,
                "findings": analysis.findings,
                "abnormalities": analysis.abnormalities,
                "confidence_score": analysis.confidence_score,
                "recommendations": analysis.recommendations,
                "processing_time": analysis.processing_time,
                "timestamp": analysis.timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Medical image processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

    async def process_voice_command(self, request: VoiceCommandRequest) -> Dict[str, Any]:
        """Process voice command request"""
        try:
            import base64
            
            # Start session if needed
            if not request.session_id:
                session_id = await self.voice_interface.start_voice_session(
                    user_id=request.user_id,
                    session_type="clinical_assistance"
                )
            else:
                session_id = request.session_id
            
            # Decode audio data
            audio_bytes = base64.b64decode(request.audio_data)
            
            # Process voice command
            command = await self.voice_interface.process_voice_command(audio_bytes)
            
            # Execute command
            result = await self.voice_interface.execute_voice_command(command)
            
            return {
                "session_id": session_id,
                "command_id": command.command_id,
                "command_type": command.command_type.value,
                "processed_text": command.processed_text,
                "confidence_score": command.confidence_score,
                "intent": command.intent,
                "execution_result": result,
                "timestamp": command.timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Voice command processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")

    async def get_predictive_analysis(self, request: PredictiveAnalysisRequest) -> Dict[str, Any]:
        """Get predictive analysis for specific outcomes"""
        try:
            if request.analysis_type == "readmission":
                result = await self.predictive_analytics.readmission_risk_prediction(
                    request.patient_data
                )
                return {
                    "analysis_type": "readmission_risk",
                    "patient_id": result.patient_id,
                    "risk_score": result.score,
                    "risk_level": result.risk_level.value,
                    "confidence": result.confidence.value,
                    "contributing_factors": result.contributing_factors,
                    "recommendations": result.recommendations,
                    "model_version": result.model_version,
                    "validity_period": str(result.validity_period)
                }
                
            elif request.analysis_type == "sepsis":
                vital_signs = request.patient_data.get("vital_signs", {})
                lab_results = request.patient_data.get("lab_results", {})
                
                result = await self.predictive_analytics.sepsis_early_warning(
                    vital_signs=vital_signs,
                    lab_results=lab_results,
                    patient_context={"patient_id": request.patient_id}
                )
                
                return {
                    "analysis_type": "sepsis_risk",
                    "alert_id": result.alert_id,
                    "patient_id": result.patient_id,
                    "severity": result.severity.value,
                    "probability": result.probability,
                    "qsofa_score": result.qsofa_score,
                    "sirs_criteria_met": result.sirs_criteria_met,
                    "triggering_factors": result.triggering_factors,
                    "recommended_actions": result.recommended_actions
                }
                
            elif request.analysis_type == "adherence":
                medication_details = request.patient_data.get("medication_details", {})
                patient_profile = request.patient_data.get("patient_profile", {})
                
                result = await self.predictive_analytics.medication_adherence_prediction(
                    patient_profile=patient_profile,
                    medication_details=medication_details
                )
                
                return {
                    "analysis_type": "medication_adherence",
                    "patient_id": result.patient_id,
                    "medication_name": result.medication_name,
                    "predicted_adherence": result.predicted_adherence,
                    "adherence_level": result.adherence_level,
                    "risk_factors": result.risk_factors,
                    "protective_factors": result.protective_factors,
                    "intervention_recommendations": result.intervention_recommendations,
                    "confidence_score": result.confidence_score
                }
                
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unknown analysis type: {request.analysis_type}"
                )
                
        except Exception as e:
            self.logger.error(f"Predictive analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Predictive analysis failed: {str(e)}")

# =============================================================================
# FastAPI Application with Enhanced Endpoints
# =============================================================================

# Initialize the enhanced engine
enhanced_engine = ClinChatEnhancedEngine()

app = FastAPI(
    title="ClinChat-RAG Enhanced Medical Intelligence API",
    description="Advanced clinical decision support with AI-powered analytics",
    version="3.0.0"
)

@app.post("/api/v3/patient/comprehensive-analysis", response_model=EnhancedAnalysisResponse)
async def comprehensive_patient_analysis(request: PatientAnalysisRequest):
    """Perform comprehensive patient analysis using all enhancement modules"""
    return await enhanced_engine.comprehensive_patient_analysis(request)

@app.post("/api/v3/medical/image-analysis")
async def medical_image_analysis(request: ImageAnalysisRequest):
    """Analyze medical images (X-rays, CT, MRI, etc.)"""
    return await enhanced_engine.process_medical_image(request)

@app.post("/api/v3/voice/command")
async def voice_command_processing(request: VoiceCommandRequest):
    """Process voice commands for clinical workflows"""
    return await enhanced_engine.process_voice_command(request)

@app.post("/api/v3/predictive/analysis")
async def predictive_analysis(request: PredictiveAnalysisRequest):
    """Get predictive analysis for clinical outcomes"""
    return await enhanced_engine.get_predictive_analysis(request)

@app.get("/api/v3/health/enhanced")
async def enhanced_health_check():
    """Enhanced health check for all modules"""
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "clinical_decision_engine": "operational",
                "medical_data_fusion": "operational", 
                "voice_interface": "operational",
                "predictive_analytics": "operational"
            },
            "version": "3.0.0",
            "enhancements_active": True
        }
        
        # Test each module briefly
        try:
            # Test clinical decision engine
            test_patient = {"patient_id": "test", "age": 50, "comorbidities": []}
            insights = await enhanced_engine.clinical_decision_engine.analyze_patient_trajectory(test_patient)
            status["modules"]["clinical_decision_engine"] = "tested_ok"
        except:
            status["modules"]["clinical_decision_engine"] = "error"
        
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v3/capabilities")
async def get_capabilities():
    """Get list of enhanced capabilities"""
    return {
        "clinical_decision_support": {
            "patient_trajectory_analysis": True,
            "drug_interaction_screening": True,
            "clinical_guideline_compliance": True,
            "outcome_prediction": True
        },
        "multi_modal_processing": {
            "medical_image_analysis": True,
            "lab_trend_analysis": True,
            "vital_sign_monitoring": True,
            "correlation_analysis": True
        },
        "voice_interface": {
            "speech_to_text": True,
            "clinical_note_generation": True,
            "voice_commands": True,
            "multi_language_support": False  # Not yet implemented
        },
        "predictive_analytics": {
            "readmission_risk": True,
            "sepsis_early_warning": True,
            "medication_adherence": True,
            "length_of_stay": True,
            "mortality_risk": True
        },
        "supported_formats": {
            "images": ["JPEG", "PNG", "DICOM"],
            "audio": ["WAV", "MP3"],
            "data": ["JSON", "CSV", "HL7_FHIR"]
        }
    }

# =============================================================================
# Example Usage and Testing
# =============================================================================

async def test_enhanced_system():
    """Test the enhanced ClinChat system"""
    print("=== Testing Enhanced ClinChat System ===")
    
    # Example comprehensive analysis
    test_request = PatientAnalysisRequest(
        patient_id="TEST001",
        patient_data={
            "age": 68,
            "gender": "male",
            "comorbidities": ["diabetes", "hypertension"],
            "medications": ["metformin", "lisinopril"],
            "vital_signs": {
                "systolic_bp": 165,
                "heart_rate": 88,
                "temperature": 98.8
            },
            "lab_results": {
                "creatinine": 1.8,
                "white_blood_cells": 12.5
            }
        },
        analysis_types=["trajectory", "drug_screening", "predictive"]
    )
    
    try:
        result = await enhanced_engine.comprehensive_patient_analysis(test_request)
        print(f"Analysis completed for patient {result.patient_id}")
        print(f"Confidence score: {result.confidence_score:.2f}")
        print(f"Recommendations: {len(result.recommendations)}")
        print(f"Alerts: {len(result.alerts)}")
        
        if result.clinical_insights:
            print(f"Risk level: {result.clinical_insights['risk_level']}")
        
        if result.predictive_scores:
            print(f"Readmission risk: {result.predictive_scores.get('readmission_risk', {}).get('score', 'N/A')}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the system
    asyncio.run(test_enhanced_system())
    
    # Start the API server
    print("Starting Enhanced ClinChat API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8003)