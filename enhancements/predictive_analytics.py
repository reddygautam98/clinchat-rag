# =============================================================================
# Predictive Analytics Suite for Clinical Intelligence
# ClinChat-RAG Enhanced Medical Intelligence System
# =============================================================================

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, confusion_matrix
import joblib
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# Data Models and Types
# =============================================================================

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class PredictionConfidence(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"

@dataclass
class RiskScore:
    patient_id: str
    risk_type: str  # readmission, mortality, sepsis, etc.
    score: float  # 0.0 to 1.0
    risk_level: RiskLevel
    confidence: PredictionConfidence
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]
    model_version: str
    prediction_timestamp: datetime
    validity_period: timedelta

@dataclass
class SepsisAlert:
    alert_id: str
    patient_id: str
    severity: AlertSeverity
    probability: float
    qsofa_score: int
    sirs_criteria_met: int
    triggering_factors: List[str]
    clinical_indicators: Dict[str, Any]
    recommended_actions: List[str]
    alert_timestamp: datetime
    expires_at: datetime

@dataclass
class AdherenceScore:
    patient_id: str
    medication_name: str
    predicted_adherence: float  # 0.0 to 1.0
    adherence_level: str  # poor, fair, good, excellent
    risk_factors: List[str]
    protective_factors: List[str]
    intervention_recommendations: List[str]
    confidence_score: float
    prediction_date: datetime
    review_date: datetime

@dataclass
class OutcomePrediction:
    prediction_id: str
    patient_id: str
    outcome_type: str
    probability: float
    time_horizon: str  # 24h, 48h, 7d, 30d, etc.
    feature_importance: Dict[str, float]
    clinical_context: Dict[str, Any]
    model_metrics: Dict[str, float]
    generated_at: datetime

# =============================================================================
# Medical Predictive Analytics Engine
# =============================================================================

class MedicalPredictiveAnalytics:
    """
    AI-powered medical prediction engine providing:
    - 30-day readmission risk prediction
    - Early sepsis detection and alerting
    - Medication adherence prediction
    - Clinical outcome forecasting
    - Length of stay optimization
    - Mortality risk assessment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scalers = {}
        self.feature_encoders = {}
        self.model_metrics = {}
        
        # Initialize prediction models
        self._initialize_prediction_models()
        
        # Load pre-trained models if available
        self._load_pretrained_models()
        
        # Clinical scoring systems
        self.scoring_systems = self._initialize_scoring_systems()
        
    def _initialize_prediction_models(self):
        """Initialize machine learning models for different predictions"""
        
        # Readmission Risk Model
        self.models['readmission'] = {
            'classifier': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'features': [
                'age', 'gender_encoded', 'length_of_stay', 'num_comorbidities',
                'num_medications', 'discharge_disposition', 'admission_type',
                'num_previous_admissions', 'charlson_score', 'emergency_visit_count'
            ],
            'target': 'readmitted_30d'
        }
        
        # Sepsis Risk Model
        self.models['sepsis'] = {
            'classifier': GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'features': [
                'temperature', 'heart_rate', 'respiratory_rate', 'systolic_bp',
                'white_blood_cells', 'lactate', 'creatinine', 'bilirubin',
                'platelets', 'glasgow_coma_scale', 'age', 'comorbidity_count'
            ],
            'target': 'sepsis_probability'
        }
        
        # Medication Adherence Model
        self.models['adherence'] = {
            'classifier': RandomForestClassifier(
                n_estimators=80,
                max_depth=8,
                min_samples_split=3,
                random_state=42
            ),
            'features': [
                'age', 'gender_encoded', 'medication_complexity', 'cost_burden',
                'side_effects_reported', 'cognitive_status', 'social_support',
                'depression_score', 'health_literacy', 'pharmacy_access'
            ],
            'target': 'adherent'
        }
        
        # Length of Stay Model
        self.models['length_of_stay'] = {
            'regressor': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'features': [
                'age', 'gender_encoded', 'admission_type', 'primary_diagnosis_encoded',
                'comorbidity_count', 'severity_score', 'lab_abnormalities',
                'procedure_count', 'icu_admission'
            ],
            'target': 'length_of_stay_days'
        }
        
    def _initialize_scoring_systems(self) -> Dict[str, Any]:
        """Initialize clinical scoring systems"""
        return {
            'qsofa': {
                'altered_mental_status': 1,
                'systolic_bp_leq_100': 1,
                'respiratory_rate_geq_22': 1,
                'max_score': 3,
                'high_risk_threshold': 2
            },
            
            'sirs': {
                'temperature_high': 1,  # >38°C or <36°C
                'heart_rate_high': 1,   # >90 bpm
                'respiratory_rate_high': 1,  # >20/min
                'white_blood_cells_abnormal': 1,  # >12k or <4k
                'max_score': 4,
                'positive_threshold': 2
            },
            
            'chads2_vasc': {
                'chf': 1,
                'hypertension': 1,
                'age_65_74': 1,
                'age_75_plus': 2,
                'diabetes': 1,
                'stroke_tia': 2,
                'vascular_disease': 1,
                'female_gender': 1,
                'max_score': 9
            },
            
            'charlson_comorbidity': {
                'myocardial_infarction': 1,
                'congestive_heart_failure': 1,
                'peripheral_vascular_disease': 1,
                'cerebrovascular_disease': 1,
                'dementia': 1,
                'copd': 1,
                'rheumatic_disease': 1,
                'peptic_ulcer': 1,
                'mild_liver_disease': 1,
                'diabetes': 1,
                'diabetes_complications': 2,
                'hemiplegia': 2,
                'renal_disease': 2,
                'malignancy': 2,
                'moderate_liver_disease': 3,
                'metastatic_solid_tumor': 6,
                'aids': 6
            }
        }

    async def readmission_risk_prediction(self, patient_data: Dict[str, Any]) -> RiskScore:
        """
        Predict 30-day readmission risk
        
        Args:
            patient_data: Comprehensive patient information
            
        Returns:
            RiskScore with readmission probability and recommendations
        """
        try:
            self.logger.info(f"Predicting readmission risk for patient {patient_data.get('patient_id', 'unknown')}")
            
            # Extract and prepare features
            features = await self._prepare_readmission_features(patient_data)
            
            # Make prediction
            if 'readmission' in self.models and hasattr(self.models['readmission']['classifier'], 'predict_proba'):
                model = self.models['readmission']['classifier']
                scaler = self.scalers.get('readmission')
                
                if scaler:
                    features_scaled = scaler.transform([features])
                else:
                    features_scaled = [features]
                
                probability = model.predict_proba(features_scaled)[0][1]  # Probability of readmission
            else:
                # Fallback to rule-based prediction
                probability = await self._rule_based_readmission_risk(patient_data)
            
            # Determine risk level
            risk_level = self._determine_risk_level(probability)
            
            # Calculate confidence
            confidence = await self._calculate_prediction_confidence(
                patient_data, features, 'readmission'
            )
            
            # Identify contributing factors
            contributing_factors = await self._identify_readmission_factors(patient_data, probability)
            
            # Generate recommendations
            recommendations = await self._generate_readmission_recommendations(
                patient_data, probability, contributing_factors
            )
            
            return RiskScore(
                patient_id=patient_data.get('patient_id', 'unknown'),
                risk_type='30_day_readmission',
                score=probability,
                risk_level=risk_level,
                confidence=confidence,
                contributing_factors=contributing_factors,
                recommendations=recommendations,
                model_version='readmission_v2.1',
                prediction_timestamp=datetime.now(),
                validity_period=timedelta(days=7)
            )
            
        except Exception as e:
            self.logger.error(f"Error predicting readmission risk: {str(e)}")
            raise

    async def sepsis_early_warning(self, vital_signs: Dict[str, Any], 
                                 lab_results: Dict[str, Any],
                                 patient_context: Dict[str, Any] = None) -> SepsisAlert:
        """
        Early sepsis detection and alerting
        
        Args:
            vital_signs: Current vital signs
            lab_results: Recent laboratory results
            patient_context: Additional patient information
            
        Returns:
            SepsisAlert with probability and recommended actions
        """
        try:
            patient_id = (patient_context or {}).get('patient_id', 'unknown')
            self.logger.info(f"Evaluating sepsis risk for patient {patient_id}")
            
            # Calculate qSOFA score
            qsofa_score = await self._calculate_qsofa_score(vital_signs, patient_context)
            
            # Calculate SIRS criteria
            sirs_score = await self._calculate_sirs_criteria(vital_signs, lab_results)
            
            # Machine learning prediction
            ml_probability = await self._ml_sepsis_prediction(vital_signs, lab_results, patient_context)
            
            # Combine scores for overall probability
            probability = await self._combine_sepsis_scores(qsofa_score, sirs_score, ml_probability)
            
            # Determine alert severity
            severity = self._determine_sepsis_severity(probability, qsofa_score, sirs_score)
            
            # Identify triggering factors
            triggering_factors = await self._identify_sepsis_triggers(
                vital_signs, lab_results, qsofa_score, sirs_score
            )
            
            # Compile clinical indicators
            clinical_indicators = {
                'qsofa_score': qsofa_score,
                'sirs_criteria': sirs_score,
                'ml_probability': ml_probability,
                'vital_signs': vital_signs,
                'lab_results': lab_results
            }
            
            # Generate recommended actions
            recommended_actions = await self._generate_sepsis_actions(probability, severity, triggering_factors)
            
            # Create alert
            alert_id = f"sepsis_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_id}"
            
            return SepsisAlert(
                alert_id=alert_id,
                patient_id=patient_id,
                severity=severity,
                probability=probability,
                qsofa_score=qsofa_score,
                sirs_criteria_met=sirs_score,
                triggering_factors=triggering_factors,
                clinical_indicators=clinical_indicators,
                recommended_actions=recommended_actions,
                alert_timestamp=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=4)
            )
            
        except Exception as e:
            self.logger.error(f"Error in sepsis early warning: {str(e)}")
            raise

    async def medication_adherence_prediction(self, patient_profile: Dict[str, Any],
                                            medication_details: Dict[str, Any]) -> AdherenceScore:
        """
        Predict medication adherence likelihood
        
        Args:
            patient_profile: Patient demographics and characteristics
            medication_details: Specific medication information
            
        Returns:
            AdherenceScore with predicted adherence and interventions
        """
        try:
            patient_id = patient_profile.get('patient_id', 'unknown')
            medication_name = medication_details.get('medication_name', 'unknown')
            
            self.logger.info(f"Predicting adherence for {medication_name} in patient {patient_id}")
            
            # Prepare features for adherence prediction
            features = await self._prepare_adherence_features(patient_profile, medication_details)
            
            # Make prediction
            if 'adherence' in self.models and hasattr(self.models['adherence']['classifier'], 'predict_proba'):
                model = self.models['adherence']['classifier']
                scaler = self.scalers.get('adherence')
                
                if scaler:
                    features_scaled = scaler.transform([features])
                else:
                    features_scaled = [features]
                
                adherence_probability = model.predict_proba(features_scaled)[0][1]
            else:
                # Rule-based fallback
                adherence_probability = await self._rule_based_adherence_prediction(
                    patient_profile, medication_details
                )
            
            # Determine adherence level
            if adherence_probability >= 0.8:
                adherence_level = "excellent"
            elif adherence_probability >= 0.6:
                adherence_level = "good"
            elif adherence_probability >= 0.4:
                adherence_level = "fair"
            else:
                adherence_level = "poor"
            
            # Identify risk and protective factors
            risk_factors = await self._identify_adherence_risk_factors(patient_profile, medication_details)
            protective_factors = await self._identify_adherence_protective_factors(patient_profile, medication_details)
            
            # Generate intervention recommendations
            interventions = await self._generate_adherence_interventions(
                adherence_probability, risk_factors, protective_factors
            )
            
            # Calculate confidence score
            confidence_score = await self._calculate_adherence_confidence(patient_profile, medication_details)
            
            return AdherenceScore(
                patient_id=patient_id,
                medication_name=medication_name,
                predicted_adherence=adherence_probability,
                adherence_level=adherence_level,
                risk_factors=risk_factors,
                protective_factors=protective_factors,
                intervention_recommendations=interventions,
                confidence_score=confidence_score,
                prediction_date=datetime.now(),
                review_date=datetime.now() + timedelta(days=30)
            )
            
        except Exception as e:
            self.logger.error(f"Error predicting medication adherence: {str(e)}")
            raise

    async def clinical_outcome_prediction(self, patient_data: Dict[str, Any],
                                        outcome_type: str,
                                        time_horizon: str = "30d") -> OutcomePrediction:
        """
        Predict various clinical outcomes
        
        Args:
            patient_data: Comprehensive patient information
            outcome_type: Type of outcome (mortality, complications, etc.)
            time_horizon: Prediction time frame
            
        Returns:
            OutcomePrediction with probability and feature importance
        """
        try:
            patient_id = patient_data.get('patient_id', 'unknown')
            self.logger.info(f"Predicting {outcome_type} for patient {patient_id} over {time_horizon}")
            
            # Prepare features based on outcome type
            features, feature_names = await self._prepare_outcome_features(patient_data, outcome_type)
            
            # Make prediction based on outcome type
            if outcome_type == 'mortality':
                probability = await self._predict_mortality_risk(features, patient_data, time_horizon)
            elif outcome_type == 'complications':
                probability = await self._predict_complication_risk(features, patient_data, time_horizon)
            elif outcome_type == 'length_of_stay':
                probability = await self._predict_length_of_stay(features, patient_data)
            else:
                probability = await self._generic_outcome_prediction(features, outcome_type, time_horizon)
            
            # Calculate feature importance (mock implementation)
            feature_importance = await self._calculate_feature_importance(features, feature_names, outcome_type)
            
            # Compile clinical context
            clinical_context = {
                'age': patient_data.get('age'),
                'primary_diagnosis': patient_data.get('primary_diagnosis'),
                'comorbidities': patient_data.get('comorbidities', []),
                'current_medications': len(patient_data.get('medications', [])),
                'vital_signs_status': patient_data.get('vital_signs_status', 'stable')
            }
            
            # Model performance metrics (would be from validation)
            model_metrics = {
                'auc_roc': 0.85,
                'precision': 0.78,
                'recall': 0.82,
                'f1_score': 0.80,
                'calibration_score': 0.88
            }
            
            prediction_id = f"{outcome_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{patient_id}"
            
            return OutcomePrediction(
                prediction_id=prediction_id,
                patient_id=patient_id,
                outcome_type=outcome_type,
                probability=probability,
                time_horizon=time_horizon,
                feature_importance=feature_importance,
                clinical_context=clinical_context,
                model_metrics=model_metrics,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error predicting clinical outcome: {str(e)}")
            raise

    # =============================================================================
    # Helper Methods for Scoring Systems
    # =============================================================================
    
    async def _calculate_qsofa_score(self, vital_signs: Dict[str, Any], 
                                   patient_context: Dict[str, Any] = None) -> int:
        """Calculate quick Sequential Organ Failure Assessment (qSOFA) score"""
        score = 0
        
        # Altered mental status (GCS < 15 or confusion)
        gcs = vital_signs.get('glasgow_coma_scale', 15)
        mental_status = patient_context.get('mental_status', 'alert') if patient_context else 'alert'
        
        if gcs < 15 or mental_status in ['confused', 'lethargic', 'obtunded']:
            score += 1
        
        # Systolic blood pressure ≤ 100 mmHg
        systolic_bp = vital_signs.get('systolic_bp', vital_signs.get('blood_pressure_systolic', 120))
        if systolic_bp <= 100:
            score += 1
        
        # Respiratory rate ≥ 22/min
        respiratory_rate = vital_signs.get('respiratory_rate', 16)
        if respiratory_rate >= 22:
            score += 1
        
        return score
    
    async def _calculate_sirs_criteria(self, vital_signs: Dict[str, Any], 
                                     lab_results: Dict[str, Any]) -> int:
        """Calculate Systemic Inflammatory Response Syndrome (SIRS) criteria"""
        criteria_met = 0
        
        # Temperature > 38°C (100.4°F) or < 36°C (96.8°F)
        temperature = vital_signs.get('temperature', 98.6)
        if temperature > 100.4 or temperature < 96.8:
            criteria_met += 1
        
        # Heart rate > 90 bpm
        heart_rate = vital_signs.get('heart_rate', 70)
        if heart_rate > 90:
            criteria_met += 1
        
        # Respiratory rate > 20/min
        respiratory_rate = vital_signs.get('respiratory_rate', 16)
        if respiratory_rate > 20:
            criteria_met += 1
        
        # White blood cell count > 12,000/μL or < 4,000/μL
        wbc = lab_results.get('white_blood_cells', lab_results.get('wbc', 7.0))
        if wbc > 12.0 or wbc < 4.0:
            criteria_met += 1
        
        return criteria_met
    
    def _determine_risk_level(self, probability: float) -> RiskLevel:
        """Determine risk level from probability score"""
        if probability >= 0.8:
            return RiskLevel.CRITICAL
        elif probability >= 0.6:
            return RiskLevel.HIGH
        elif probability >= 0.4:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _determine_sepsis_severity(self, probability: float, qsofa_score: int, sirs_score: int) -> AlertSeverity:
        """Determine sepsis alert severity"""
        if probability >= 0.8 or qsofa_score >= 2:
            return AlertSeverity.CRITICAL
        elif probability >= 0.6 or (qsofa_score >= 1 and sirs_score >= 2):
            return AlertSeverity.URGENT
        elif probability >= 0.4 or sirs_score >= 2:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    # =============================================================================
    # Rule-based Fallback Methods
    # =============================================================================
    
    async def _rule_based_readmission_risk(self, patient_data: Dict[str, Any]) -> float:
        """Rule-based readmission risk calculation"""
        risk_score = 0.0
        
        # Age factor
        age = patient_data.get('age', 50)
        if age >= 75:
            risk_score += 0.3
        elif age >= 65:
            risk_score += 0.2
        
        # Comorbidity count
        comorbidities = len(patient_data.get('comorbidities', []))
        risk_score += min(comorbidities * 0.1, 0.3)
        
        # Recent admissions
        recent_admissions = patient_data.get('recent_admissions_30d', 0)
        risk_score += min(recent_admissions * 0.2, 0.4)
        
        # Length of stay
        los = patient_data.get('length_of_stay', 3)
        if los >= 7:
            risk_score += 0.2
        elif los <= 1:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    async def _rule_based_adherence_prediction(self, patient_profile: Dict[str, Any],
                                             medication_details: Dict[str, Any]) -> float:
        """Rule-based medication adherence prediction"""
        adherence_score = 0.7  # Base score
        
        # Age factors
        age = patient_profile.get('age', 50)
        if 40 <= age <= 70:
            adherence_score += 0.1
        elif age > 80:
            adherence_score -= 0.1
        
        # Medication complexity
        daily_frequency = medication_details.get('daily_frequency', 1)
        if daily_frequency > 3:
            adherence_score -= 0.2
        elif daily_frequency == 1:
            adherence_score += 0.1
        
        # Side effects
        if medication_details.get('side_effects_reported', False):
            adherence_score -= 0.2
        
        # Cost burden
        cost_level = medication_details.get('cost_level', 'low')
        if cost_level == 'high':
            adherence_score -= 0.2
        elif cost_level == 'low':
            adherence_score += 0.1
        
        # Social support
        social_support = patient_profile.get('social_support', 'moderate')
        if social_support == 'high':
            adherence_score += 0.1
        elif social_support == 'low':
            adherence_score -= 0.15
        
        return max(0.0, min(1.0, adherence_score))

# =============================================================================
# Usage Example and Testing
# =============================================================================

async def main():
    """Example usage of the Medical Predictive Analytics Engine"""
    
    # Initialize the analytics engine
    analytics = MedicalPredictiveAnalytics()
    
    print("=== Medical Predictive Analytics Demo ===")
    
    # Example patient data for readmission risk
    patient_data = {
        'patient_id': 'PAT789012',
        'age': 72,
        'gender': 'female',
        'length_of_stay': 5,
        'comorbidities': ['diabetes', 'hypertension', 'heart_failure'],
        'medications': ['metformin', 'lisinopril', 'furosemide', 'metoprolol'],
        'recent_admissions_30d': 1,
        'discharge_disposition': 'home',
        'primary_diagnosis': 'heart_failure_exacerbation'
    }
    
    # Test readmission risk prediction
    print("\n=== 30-Day Readmission Risk Prediction ===")
    readmission_risk = await analytics.readmission_risk_prediction(patient_data)
    print(f"Patient ID: {readmission_risk.patient_id}")
    print(f"Risk Score: {readmission_risk.score:.3f}")
    print(f"Risk Level: {readmission_risk.risk_level.value}")
    print(f"Confidence: {readmission_risk.confidence.value}")
    print("Recommendations:")
    for rec in readmission_risk.recommendations:
        print(f"  - {rec}")
    
    # Example vital signs and labs for sepsis detection
    vital_signs = {
        'temperature': 101.8,
        'heart_rate': 105,
        'respiratory_rate': 24,
        'systolic_bp': 95,
        'diastolic_bp': 60,
        'glasgow_coma_scale': 14
    }
    
    lab_results = {
        'white_blood_cells': 13.5,
        'lactate': 2.8,
        'creatinine': 1.6,
        'platelets': 180
    }
    
    # Test sepsis early warning
    print("\n=== Sepsis Early Warning System ===")
    sepsis_alert = await analytics.sepsis_early_warning(
        vital_signs, lab_results, {'patient_id': 'PAT789012'}
    )
    print(f"Alert Severity: {sepsis_alert.severity.value}")
    print(f"Sepsis Probability: {sepsis_alert.probability:.3f}")
    print(f"qSOFA Score: {sepsis_alert.qsofa_score}/3")
    print(f"SIRS Criteria Met: {sepsis_alert.sirs_criteria_met}/4")
    print("Recommended Actions:")
    for action in sepsis_alert.recommended_actions:
        print(f"  - {action}")
    
    # Example medication adherence prediction
    medication_details = {
        'medication_name': 'metformin',
        'daily_frequency': 2,
        'cost_level': 'low',
        'side_effects_reported': False
    }
    
    patient_profile = {
        'patient_id': 'PAT789012',
        'age': 72,
        'social_support': 'moderate',
        'health_literacy': 'adequate',
        'depression_score': 'minimal'
    }
    
    # Test medication adherence prediction
    print("\n=== Medication Adherence Prediction ===")
    adherence_score = await analytics.medication_adherence_prediction(
        patient_profile, medication_details
    )
    print(f"Medication: {adherence_score.medication_name}")
    print(f"Predicted Adherence: {adherence_score.predicted_adherence:.1%}")
    print(f"Adherence Level: {adherence_score.adherence_level}")
    print(f"Confidence: {adherence_score.confidence_score:.3f}")
    print("Intervention Recommendations:")
    for intervention in adherence_score.intervention_recommendations:
        print(f"  - {intervention}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())