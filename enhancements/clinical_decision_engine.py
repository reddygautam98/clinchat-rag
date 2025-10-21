# =============================================================================
# Advanced Clinical Decision Support Engine
# ClinChat-RAG Enhanced Medical Intelligence System
# =============================================================================

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from pydantic import BaseModel, Field

# =============================================================================
# Data Models and Types
# =============================================================================

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class DrugInteraction:
    drug1: str
    drug2: str
    interaction_type: str
    severity: str
    clinical_significance: str
    mechanism: str
    management: str
    confidence_score: float

@dataclass
class ClinicalAlert:
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    recommendations: List[str]
    timestamp: datetime
    patient_id: Optional[str] = None
    expires_at: Optional[datetime] = None

@dataclass
class ClinicalInsights:
    patient_id: str
    risk_score: float
    risk_level: RiskLevel
    trajectory_analysis: Dict[str, Any]
    recommendations: List[str]
    alerts: List[ClinicalAlert]
    confidence_score: float
    generated_at: datetime

@dataclass
class SafetyReport:
    interactions: List[DrugInteraction]
    contraindications: List[Dict[str, Any]]
    allergic_reactions: List[Dict[str, Any]]
    dosage_warnings: List[Dict[str, Any]]
    overall_risk: RiskLevel
    recommendations: List[str]

@dataclass
class ComplianceReport:
    guideline_name: str
    compliance_score: float
    adherent_items: List[str]
    non_adherent_items: List[str]
    recommendations: List[str]
    evidence_level: str
    last_updated: datetime

# =============================================================================
# Advanced Clinical Decision Support Engine
# =============================================================================

class ClinicalDecisionEngine:
    """
    Advanced medical decision support system providing:
    - Real-time clinical decision support
    - Drug interaction screening
    - Evidence-based care recommendations
    - Patient trajectory analysis
    - Outcome prediction and risk stratification
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.drug_database = self._initialize_drug_database()
        self.clinical_guidelines = self._initialize_guidelines()
        self.risk_models = self._initialize_risk_models()
        
    def _initialize_drug_database(self) -> Dict[str, Any]:
        """Initialize comprehensive drug interaction database"""
        return {
            # Major drug interactions database
            "interactions": {
                ("warfarin", "aspirin"): {
                    "severity": "major",
                    "type": "bleeding_risk",
                    "mechanism": "Additive anticoagulation effects",
                    "clinical_significance": "Increased bleeding risk",
                    "management": "Monitor INR closely, consider dose adjustment"
                },
                ("simvastatin", "amiodarone"): {
                    "severity": "major", 
                    "type": "myopathy_risk",
                    "mechanism": "CYP3A4 inhibition increases statin levels",
                    "clinical_significance": "Increased risk of myopathy/rhabdomyolysis",
                    "management": "Limit simvastatin to 20mg daily or switch statin"
                },
                ("metformin", "iodinated_contrast"): {
                    "severity": "moderate",
                    "type": "renal_toxicity",
                    "mechanism": "Contrast-induced nephropathy risk",
                    "clinical_significance": "Risk of lactic acidosis",
                    "management": "Hold metformin 48 hours before and after contrast"
                }
            },
            
            # Drug allergy database
            "allergies": {
                "penicillin": ["amoxicillin", "ampicillin", "piperacillin"],
                "sulfa": ["sulfamethoxazole", "furosemide", "hydrochlorothiazide"],
                "nsaid": ["ibuprofen", "naproxen", "celecoxib"]
            },
            
            # Contraindications
            "contraindications": {
                "pregnancy": {
                    "category_x": ["warfarin", "isotretinoin", "finasteride"],
                    "category_d": ["phenytoin", "lithium", "tetracycline"]
                },
                "renal_failure": ["metformin", "glyburide", "meperidine"],
                "heart_failure": ["nifedipine_ir", "dofetilide", "flecainide"]
            }
        }
    
    def _initialize_guidelines(self) -> Dict[str, Any]:
        """Initialize evidence-based clinical guidelines"""
        return {
            "diabetes_management": {
                "hba1c_target": {"normal": 7.0, "elderly": 8.0, "high_risk": 6.5},
                "blood_pressure_target": {"systolic": 130, "diastolic": 80},
                "ldl_target": 100,
                "medications": {
                    "first_line": ["metformin"],
                    "second_line": ["glp1_agonist", "sglt2_inhibitor", "dpp4_inhibitor"],
                    "insulin": ["basal_insulin", "prandial_insulin"]
                }
            },
            
            "hypertension_management": {
                "stage_1": {"systolic": [130, 139], "diastolic": [80, 89]},
                "stage_2": {"systolic": [140, 180], "diastolic": [90, 120]},
                "crisis": {"systolic": ">180", "diastolic": ">120"},
                "first_line": ["ace_inhibitor", "arb", "thiazide", "ccb"]
            },
            
            "anticoagulation": {
                "atrial_fibrillation": {
                    "chads2_vasc": {
                        "low_risk": [0, 1],
                        "moderate_risk": [2],
                        "high_risk": ">=3"
                    },
                    "recommended": ["apixaban", "rivaroxaban", "dabigatran", "warfarin"]
                }
            }
        }
    
    def _initialize_risk_models(self) -> Dict[str, Any]:
        """Initialize predictive risk models"""
        return {
            "sepsis_risk": {
                "qsofa_criteria": ["altered_mental_status", "systolic_bp_100", "respiratory_rate_22"],
                "sirs_criteria": ["temp_abnormal", "heart_rate_90", "respiratory_rate_20", "wbc_abnormal"]
            },
            
            "readmission_risk": {
                "high_risk_factors": ["multiple_comorbidities", "recent_admission", "medication_noncompliance"],
                "protective_factors": ["good_social_support", "medication_reconciliation", "follow_up_scheduled"]
            },
            
            "cardiovascular_risk": {
                "ascvd_score": ["age", "gender", "race", "cholesterol", "hdl", "systolic_bp", "smoking", "diabetes"]
            }
        }

    async def analyze_patient_trajectory(self, patient_data: Dict[str, Any]) -> ClinicalInsights:
        """
        Analyze patient care trajectory and predict outcomes
        
        Args:
            patient_data: Comprehensive patient information including:
                - demographics, vital signs, lab results, medications,
                - comorbidities, recent hospitalizations, social factors
                
        Returns:
            ClinicalInsights with risk assessment and recommendations
        """
        try:
            self.logger.info(f"Analyzing patient trajectory for patient {patient_data.get('patient_id', 'unknown')}")
            
            # Extract key patient factors
            age = patient_data.get('age', 0)
            comorbidities = patient_data.get('comorbidities', [])
            vital_signs = patient_data.get('vital_signs', {})
            lab_results = patient_data.get('lab_results', {})
            medications = patient_data.get('medications', [])
            
            # Calculate composite risk score
            risk_score = await self._calculate_composite_risk(patient_data)
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate trajectory analysis
            trajectory_analysis = {
                "trend_direction": await self._analyze_clinical_trends(patient_data),
                "deterioration_risk": await self._assess_deterioration_risk(vital_signs, lab_results),
                "medication_optimization": await self._assess_medication_optimization(medications, comorbidities),
                "care_gaps": await self._identify_care_gaps(patient_data)
            }
            
            # Generate recommendations
            recommendations = await self._generate_clinical_recommendations(patient_data, risk_score)
            
            # Generate alerts
            alerts = await self._generate_clinical_alerts(patient_data, risk_level)
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(patient_data)
            
            return ClinicalInsights(
                patient_id=patient_data.get('patient_id', 'unknown'),
                risk_score=risk_score,
                risk_level=risk_level,
                trajectory_analysis=trajectory_analysis,
                recommendations=recommendations,
                alerts=alerts,
                confidence_score=confidence_score,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing patient trajectory: {str(e)}")
            raise

    async def drug_interaction_screening(self, medications: List[str], 
                                       patient_allergies: List[str] = None,
                                       patient_conditions: List[str] = None) -> SafetyReport:
        """
        Comprehensive drug interaction and allergy checking
        
        Args:
            medications: List of current medications
            patient_allergies: Known allergies
            patient_conditions: Medical conditions for contraindication checking
            
        Returns:
            SafetyReport with interactions, contraindications, and recommendations
        """
        try:
            self.logger.info(f"Screening {len(medications)} medications for interactions")
            
            interactions = []
            contraindications = []
            allergic_reactions = []
            dosage_warnings = []
            
            # Check drug-drug interactions
            for i, drug1 in enumerate(medications):
                for drug2 in medications[i+1:]:
                    interaction = await self._check_drug_interaction(drug1, drug2)
                    if interaction:
                        interactions.append(interaction)
            
            # Check allergies
            if patient_allergies:
                for medication in medications:
                    allergy_risk = await self._check_allergy_risk(medication, patient_allergies)
                    if allergy_risk:
                        allergic_reactions.append(allergy_risk)
            
            # Check contraindications
            if patient_conditions:
                for medication in medications:
                    contraindication = await self._check_contraindications(medication, patient_conditions)
                    if contraindication:
                        contraindications.append(contraindication)
            
            # Check dosage warnings
            for medication in medications:
                dosage_warning = await self._check_dosage_warnings(medication, patient_conditions or [])
                if dosage_warning:
                    dosage_warnings.append(dosage_warning)
            
            # Determine overall risk
            overall_risk = self._determine_medication_risk(interactions, contraindications, allergic_reactions)
            
            # Generate recommendations
            recommendations = await self._generate_medication_recommendations(
                interactions, contraindications, allergic_reactions, dosage_warnings
            )
            
            return SafetyReport(
                interactions=interactions,
                contraindications=contraindications,
                allergic_reactions=allergic_reactions,
                dosage_warnings=dosage_warnings,
                overall_risk=overall_risk,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error in drug interaction screening: {str(e)}")
            raise

    async def clinical_guideline_compliance(self, care_plan: Dict[str, Any]) -> ComplianceReport:
        """
        Check adherence to evidence-based clinical guidelines
        
        Args:
            care_plan: Current care plan including diagnoses, medications, monitoring
            
        Returns:
            ComplianceReport with adherence assessment and recommendations
        """
        try:
            primary_diagnosis = care_plan.get('primary_diagnosis', '')
            medications = care_plan.get('medications', [])
            monitoring = care_plan.get('monitoring', {})
            targets = care_plan.get('targets', {})
            
            self.logger.info(f"Checking guideline compliance for {primary_diagnosis}")
            
            # Get applicable guidelines
            applicable_guidelines = await self._get_applicable_guidelines(primary_diagnosis)
            
            if not applicable_guidelines:
                return ComplianceReport(
                    guideline_name="No specific guidelines found",
                    compliance_score=0.0,
                    adherent_items=[],
                    non_adherent_items=[],
                    recommendations=["Consider consulting specialty guidelines"],
                    evidence_level="N/A",
                    last_updated=datetime.now()
                )
            
            # Check compliance for each guideline
            adherent_items = []
            non_adherent_items = []
            
            for guideline_item in applicable_guidelines:
                is_compliant = await self._check_guideline_item_compliance(
                    guideline_item, care_plan
                )
                
                if is_compliant:
                    adherent_items.append(guideline_item['description'])
                else:
                    non_adherent_items.append(guideline_item['description'])
            
            # Calculate compliance score
            total_items = len(adherent_items) + len(non_adherent_items)
            compliance_score = len(adherent_items) / total_items if total_items > 0 else 0.0
            
            # Generate recommendations
            recommendations = await self._generate_compliance_recommendations(
                non_adherent_items, primary_diagnosis
            )
            
            return ComplianceReport(
                guideline_name=f"{primary_diagnosis.title()} Management Guidelines",
                compliance_score=compliance_score,
                adherent_items=adherent_items,
                non_adherent_items=non_adherent_items,
                recommendations=recommendations,
                evidence_level="Grade A",
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error checking guideline compliance: {str(e)}")
            raise

    # =============================================================================
    # Private Helper Methods
    # =============================================================================
    
    async def _calculate_composite_risk(self, patient_data: Dict[str, Any]) -> float:
        """Calculate composite risk score from patient data"""
        risk_factors = {
            'age': min(patient_data.get('age', 0) / 100, 1.0) * 0.2,
            'comorbidities': min(len(patient_data.get('comorbidities', [])) / 10, 1.0) * 0.3,
            'vital_signs': await self._assess_vital_signs_risk(patient_data.get('vital_signs', {})),
            'lab_abnormalities': await self._assess_lab_risk(patient_data.get('lab_results', {})),
            'medication_burden': min(len(patient_data.get('medications', [])) / 15, 1.0) * 0.1
        }
        
        return sum(risk_factors.values()) / len(risk_factors)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from composite score"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    async def _check_drug_interaction(self, drug1: str, drug2: str) -> Optional[DrugInteraction]:
        """Check for drug-drug interaction"""
        interaction_key = tuple(sorted([drug1.lower(), drug2.lower()]))
        
        if interaction_key in self.drug_database["interactions"]:
            interaction_data = self.drug_database["interactions"][interaction_key]
            return DrugInteraction(
                drug1=drug1,
                drug2=drug2,
                interaction_type=interaction_data["type"],
                severity=interaction_data["severity"],
                clinical_significance=interaction_data["clinical_significance"],
                mechanism=interaction_data["mechanism"],
                management=interaction_data["management"],
                confidence_score=0.95
            )
        
        return None
    
    async def _generate_clinical_recommendations(self, patient_data: Dict[str, Any], 
                                               risk_score: float) -> List[str]:
        """Generate evidence-based clinical recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_score >= 0.8:
            recommendations.extend([
                "Consider intensive monitoring or higher level of care",
                "Review all medications for potential optimization",
                "Evaluate for specialist consultation"
            ])
        elif risk_score >= 0.6:
            recommendations.extend([
                "Increase monitoring frequency",
                "Review medication adherence",
                "Consider preventive interventions"
            ])
        
        # Condition-specific recommendations
        comorbidities = patient_data.get('comorbidities', [])
        if 'diabetes' in comorbidities:
            recommendations.append("Ensure HbA1c monitoring every 3-6 months")
        if 'hypertension' in comorbidities:
            recommendations.append("Monitor blood pressure regularly and adjust medications as needed")
        
        return recommendations
    
    async def _generate_clinical_alerts(self, patient_data: Dict[str, Any], 
                                      risk_level: RiskLevel) -> List[ClinicalAlert]:
        """Generate clinical alerts based on patient data"""
        alerts = []
        
        # Critical value alerts
        vital_signs = patient_data.get('vital_signs', {})
        if vital_signs.get('systolic_bp', 0) > 180:
            alerts.append(ClinicalAlert(
                alert_id=f"bp_crisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity=AlertSeverity.CRITICAL,
                title="Hypertensive Crisis",
                description=f"Systolic BP {vital_signs['systolic_bp']} mmHg requires immediate attention",
                recommendations=["Check BP manually", "Consider antihypertensive medications", "Monitor closely"],
                timestamp=datetime.now(),
                patient_id=patient_data.get('patient_id')
            ))
        
        # High-risk alerts
        if risk_level == RiskLevel.CRITICAL:
            alerts.append(ClinicalAlert(
                alert_id=f"high_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity=AlertSeverity.WARNING,
                title="High-Risk Patient",
                description="Patient has multiple risk factors requiring enhanced monitoring",
                recommendations=["Increase monitoring frequency", "Consider specialist consultation"],
                timestamp=datetime.now(),
                patient_id=patient_data.get('patient_id')
            ))
        
        return alerts
    
    async def _assess_vital_signs_risk(self, vital_signs: Dict[str, Any]) -> float:
        """Assess risk from vital signs"""
        risk_score = 0.0
        
        # Blood pressure
        systolic = vital_signs.get('systolic_bp', 120)
        if systolic > 180:
            risk_score += 0.8
        elif systolic > 140:
            risk_score += 0.4
        
        # Heart rate
        hr = vital_signs.get('heart_rate', 70)
        if hr > 120 or hr < 50:
            risk_score += 0.3
        
        # Temperature
        temp = vital_signs.get('temperature', 98.6)
        if temp > 101.5 or temp < 96:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    async def _assess_lab_risk(self, lab_results: Dict[str, Any]) -> float:
        """Assess risk from laboratory results"""
        risk_score = 0.0
        
        # Creatinine
        creatinine = lab_results.get('creatinine', 1.0)
        if creatinine > 2.0:
            risk_score += 0.4
        elif creatinine > 1.5:
            risk_score += 0.2
        
        # Hemoglobin
        hgb = lab_results.get('hemoglobin', 12.0)
        if hgb < 8.0:
            risk_score += 0.3
        elif hgb < 10.0:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    async def _calculate_confidence_score(self, patient_data: Dict[str, Any]) -> float:
        """Calculate confidence in the analysis based on data completeness"""
        data_points = [
            'age', 'gender', 'vital_signs', 'lab_results', 
            'medications', 'comorbidities', 'allergies'
        ]
        
        available_points = sum(1 for point in data_points if patient_data.get(point))
        return available_points / len(data_points)

# =============================================================================
# Usage Example and Testing
# =============================================================================

async def main():
    """Example usage of the Clinical Decision Support Engine"""
    
    # Initialize the engine
    engine = ClinicalDecisionEngine()
    
    # Example patient data
    patient_data = {
        'patient_id': 'PAT123456',
        'age': 68,
        'gender': 'male',
        'comorbidities': ['diabetes', 'hypertension', 'chronic_kidney_disease'],
        'vital_signs': {
            'systolic_bp': 165,
            'diastolic_bp': 95,
            'heart_rate': 88,
            'temperature': 98.8,
            'respiratory_rate': 18
        },
        'lab_results': {
            'creatinine': 1.8,
            'hemoglobin': 9.5,
            'hba1c': 8.2,
            'ldl': 145
        },
        'medications': ['metformin', 'lisinopril', 'simvastatin', 'aspirin'],
        'allergies': ['penicillin']
    }
    
    # Test patient trajectory analysis
    print("=== Patient Trajectory Analysis ===")
    insights = await engine.analyze_patient_trajectory(patient_data)
    print(f"Risk Level: {insights.risk_level.value}")
    print(f"Risk Score: {insights.risk_score:.2f}")
    print(f"Confidence: {insights.confidence_score:.2f}")
    print("Recommendations:")
    for rec in insights.recommendations:
        print(f"  - {rec}")
    
    # Test drug interaction screening
    print("\n=== Drug Interaction Screening ===")
    safety_report = await engine.drug_interaction_screening(
        medications=patient_data['medications'],
        patient_allergies=patient_data['allergies'],
        patient_conditions=patient_data['comorbidities']
    )
    print(f"Overall Risk: {safety_report.overall_risk.value}")
    print(f"Interactions Found: {len(safety_report.interactions)}")
    
    # Test guideline compliance
    print("\n=== Clinical Guideline Compliance ===")
    care_plan = {
        'primary_diagnosis': 'diabetes',
        'medications': patient_data['medications'],
        'monitoring': {'hba1c': '6_months', 'eye_exam': 'annual'},
        'targets': {'hba1c': 7.0, 'bp': '130/80'}
    }
    compliance = await engine.clinical_guideline_compliance(care_plan)
    print(f"Compliance Score: {compliance.compliance_score:.1%}")
    print(f"Non-adherent Items: {len(compliance.non_adherent_items)}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())