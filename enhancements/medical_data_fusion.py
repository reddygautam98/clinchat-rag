# =============================================================================
# Multi-Modal Medical Data Processing Engine
# ClinChat-RAG Enhanced Medical Intelligence System
# =============================================================================

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
import io
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.signal import find_peaks
import cv2
from PIL import Image
import torch
import torchvision.transforms as transforms

# =============================================================================
# Data Models and Types
# =============================================================================

class ImageType(Enum):
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    MICROSCOPY = "microscopy"
    PHOTO = "photo"
    UNKNOWN = "unknown"

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    CRITICAL = "critical"

class AlertLevel(Enum):
    NORMAL = "normal"
    ATTENTION = "attention"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class ImageAnalysis:
    image_id: str
    image_type: ImageType
    findings: List[str]
    abnormalities: List[Dict[str, Any]]
    confidence_score: float
    recommendations: List[str]
    processing_time: float
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class LabTrend:
    test_name: str
    values: List[float]
    timestamps: List[datetime]
    trend_direction: TrendDirection
    slope: float
    r_squared: float
    normal_range: Tuple[float, float]
    latest_value: float
    days_trend: int

@dataclass
class TrendAnalysis:
    patient_id: str
    lab_trends: List[LabTrend]
    overall_trajectory: TrendDirection
    concerning_trends: List[str]
    improvement_trends: List[str]
    recommendations: List[str]
    confidence_score: float
    analysis_period: Tuple[datetime, datetime]

@dataclass
class VitalSignReading:
    timestamp: datetime
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[int] = None
    pain_score: Optional[int] = None

@dataclass
class VitalInsights:
    patient_id: str
    current_status: AlertLevel
    abnormal_values: List[str]
    trends: Dict[str, TrendDirection]
    alerts: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    monitoring_frequency: str
    last_updated: datetime

# =============================================================================
# Multi-Modal Medical Data Processing Engine
# =============================================================================

class MedicalDataFusion:
    """
    Comprehensive medical data engine processing:
    - Medical images (X-rays, CT, MRI, ultrasound)
    - Laboratory value trends over time
    - Real-time vital sign monitoring
    - Clinical photo documentation
    - Multi-modal correlation analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.image_models = self._initialize_image_models()
        self.lab_analyzers = self._initialize_lab_analyzers()
        self.vital_monitors = self._initialize_vital_monitors()
        
    def _initialize_image_models(self) -> Dict[str, Any]:
        """Initialize medical image analysis models"""
        return {
            "xray_classifier": {
                "model_type": "resnet50",
                "classes": ["normal", "pneumonia", "fracture", "mass", "atelectasis"],
                "confidence_threshold": 0.7
            },
            "ct_analyzer": {
                "model_type": "3d_cnn",
                "classes": ["normal", "tumor", "hemorrhage", "infarct"],
                "confidence_threshold": 0.8
            },
            "preprocessing": {
                "resize": (224, 224),
                "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}
            }
        }
    
    def _initialize_lab_analyzers(self) -> Dict[str, Any]:
        """Initialize laboratory trend analysis parameters"""
        return {
            "reference_ranges": {
                "hemoglobin": (12.0, 16.0),
                "hematocrit": (36.0, 46.0),
                "white_blood_cells": (4.5, 11.0),
                "platelets": (150, 450),
                "creatinine": (0.6, 1.2),
                "bun": (7, 20),
                "glucose": (70, 100),
                "hba1c": (4.0, 5.6),
                "total_cholesterol": (0, 200),
                "ldl_cholesterol": (0, 100),
                "hdl_cholesterol": (40, 80),
                "triglycerides": (0, 150),
                "ast": (10, 40),
                "alt": (7, 56),
                "bilirubin": (0.2, 1.2),
                "albumin": (3.5, 5.0),
                "sodium": (136, 145),
                "potassium": (3.5, 5.1),
                "chloride": (98, 107),
                "co2": (22, 29)
            },
            "critical_values": {
                "hemoglobin": (8.0, 18.0),
                "creatinine": (0.4, 3.0),
                "glucose": (40, 400),
                "potassium": (2.5, 6.0),
                "sodium": (120, 160)
            },
            "trend_analysis": {
                "minimum_points": 3,
                "significance_threshold": 0.05,
                "trend_days": [7, 30, 90]
            }
        }
    
    def _initialize_vital_monitors(self) -> Dict[str, Any]:
        """Initialize vital sign monitoring parameters"""
        return {
            "normal_ranges": {
                "heart_rate": {"adult": (60, 100), "elderly": (60, 100), "pediatric": (70, 120)},
                "systolic_bp": {"adult": (90, 140), "elderly": (90, 150), "pediatric": (80, 110)},
                "diastolic_bp": {"adult": (60, 90), "elderly": (60, 90), "pediatric": (50, 70)},
                "temperature": {"all": (97.0, 99.5)},
                "respiratory_rate": {"adult": (12, 20), "elderly": (12, 20), "pediatric": (20, 30)},
                "oxygen_saturation": {"all": (95, 100)}
            },
            "critical_thresholds": {
                "heart_rate": {"low": 50, "high": 120},
                "systolic_bp": {"low": 90, "high": 180},
                "temperature": {"low": 96.0, "high": 101.5},
                "oxygen_saturation": {"low": 90}
            },
            "monitoring_protocols": {
                "stable": "every_4_hours",
                "concerning": "every_2_hours", 
                "critical": "continuous"
            }
        }

    async def process_medical_images(self, image_data: bytes, 
                                   image_type: str = "unknown",
                                   patient_context: Dict[str, Any] = None) -> ImageAnalysis:
        """
        Analyze medical images (X-rays, CT, MRI, ultrasound)
        
        Args:
            image_data: Binary image data
            image_type: Type of medical image
            patient_context: Patient information for context
            
        Returns:
            ImageAnalysis with findings and recommendations
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Processing medical image of type: {image_type}")
            
            # Decode and preprocess image
            image = await self._decode_medical_image(image_data)
            processed_image = await self._preprocess_medical_image(image, image_type)
            
            # Detect image type if unknown
            if image_type == "unknown":
                image_type = await self._classify_image_type(processed_image)
            
            # Analyze image based on type
            analysis_results = await self._analyze_medical_image(processed_image, image_type)
            
            # Extract findings and abnormalities
            findings = await self._extract_findings(analysis_results, image_type)
            abnormalities = await self._detect_abnormalities(analysis_results, image_type)
            
            # Generate recommendations
            recommendations = await self._generate_image_recommendations(
                findings, abnormalities, patient_context
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create metadata
            metadata = {
                "original_size": f"{image.width}x{image.height}",
                "processed_size": f"{processed_image.shape[1]}x{processed_image.shape[0]}",
                "model_version": "v2.1.0",
                "preprocessing_steps": ["resize", "normalize", "enhance_contrast"]
            }
            
            return ImageAnalysis(
                image_id=f"IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                image_type=ImageType(image_type.lower()),
                findings=findings,
                abnormalities=abnormalities,
                confidence_score=analysis_results.get('confidence', 0.0),
                recommendations=recommendations,
                processing_time=processing_time,
                metadata=metadata,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing medical image: {str(e)}")
            raise

    async def process_lab_trends(self, lab_history: List[Dict[str, Any]], 
                               analysis_days: int = 30) -> TrendAnalysis:
        """
        Analyze laboratory value trends over time
        
        Args:
            lab_history: Historical laboratory results
            analysis_days: Number of days to analyze
            
        Returns:
            TrendAnalysis with trend directions and insights
        """
        try:
            self.logger.info(f"Analyzing lab trends over {analysis_days} days")
            
            # Filter data by analysis period
            cutoff_date = datetime.now() - timedelta(days=analysis_days)
            recent_labs = [
                lab for lab in lab_history 
                if datetime.fromisoformat(lab.get('date', '1900-01-01')) >= cutoff_date
            ]
            
            # Group by test name
            lab_groups = {}
            for lab in recent_labs:
                test_name = lab.get('test_name', '').lower()
                if test_name not in lab_groups:
                    lab_groups[test_name] = []
                lab_groups[test_name].append(lab)
            
            # Analyze trends for each test
            lab_trends = []
            concerning_trends = []
            improvement_trends = []
            
            for test_name, test_results in lab_groups.items():
                if len(test_results) >= 3:  # Minimum points for trend analysis
                    trend = await self._analyze_single_lab_trend(test_name, test_results)
                    lab_trends.append(trend)
                    
                    # Categorize trends
                    if trend.trend_direction == TrendDirection.DECLINING:
                        concerning_trends.append(f"{test_name}: declining trend")
                    elif trend.trend_direction == TrendDirection.IMPROVING:
                        improvement_trends.append(f"{test_name}: improving trend")
            
            # Determine overall trajectory
            overall_trajectory = await self._determine_overall_trajectory(lab_trends)
            
            # Generate recommendations
            recommendations = await self._generate_trend_recommendations(
                lab_trends, concerning_trends, improvement_trends
            )
            
            # Calculate confidence score
            confidence_score = await self._calculate_trend_confidence(lab_trends)
            
            # Determine analysis period
            if recent_labs:
                earliest = min(datetime.fromisoformat(lab['date']) for lab in recent_labs)
                latest = max(datetime.fromisoformat(lab['date']) for lab in recent_labs)
                analysis_period = (earliest, latest)
            else:
                analysis_period = (cutoff_date, datetime.now())
            
            return TrendAnalysis(
                patient_id=lab_history[0].get('patient_id', 'unknown') if lab_history else 'unknown',
                lab_trends=lab_trends,
                overall_trajectory=overall_trajectory,
                concerning_trends=concerning_trends,
                improvement_trends=improvement_trends,
                recommendations=recommendations,
                confidence_score=confidence_score,
                analysis_period=analysis_period
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing lab trends: {str(e)}")
            raise

    async def process_vital_signs(self, vitals_stream: Iterator[VitalSignReading],
                                patient_age_group: str = "adult") -> VitalInsights:
        """
        Real-time vital sign monitoring and alerting
        
        Args:
            vitals_stream: Stream of vital sign readings
            patient_age_group: Age group for appropriate normal ranges
            
        Returns:
            VitalInsights with current status and recommendations
        """
        try:
            self.logger.info("Processing vital signs stream for real-time monitoring")
            
            # Collect recent vital signs (last 24 hours)
            recent_vitals = []
            current_time = datetime.now()
            
            for vital in vitals_stream:
                if (current_time - vital.timestamp).total_seconds() <= 86400:  # 24 hours
                    recent_vitals.append(vital)
                    
                # Limit to last 100 readings for performance
                if len(recent_vitals) >= 100:
                    break
            
            if not recent_vitals:
                return VitalInsights(
                    patient_id="unknown",
                    current_status=AlertLevel.NORMAL,
                    abnormal_values=[],
                    trends={},
                    alerts=[],
                    recommendations=["No recent vital signs available"],
                    risk_factors=[],
                    monitoring_frequency="as_needed",
                    last_updated=datetime.now()
                )
            
            # Get most recent reading
            latest_vital = max(recent_vitals, key=lambda x: x.timestamp)
            
            # Check current values against normal ranges
            abnormal_values = await self._identify_abnormal_vitals(latest_vital, patient_age_group)
            
            # Analyze trends
            trends = await self._analyze_vital_trends(recent_vitals)
            
            # Determine current status
            current_status = await self._determine_vital_status(latest_vital, abnormal_values, patient_age_group)
            
            # Generate alerts
            alerts = await self._generate_vital_alerts(latest_vital, trends, patient_age_group)
            
            # Identify risk factors
            risk_factors = await self._identify_vital_risk_factors(recent_vitals, patient_age_group)
            
            # Generate recommendations
            recommendations = await self._generate_vital_recommendations(
                current_status, abnormal_values, trends, alerts
            )
            
            # Determine monitoring frequency
            monitoring_frequency = await self._determine_monitoring_frequency(current_status, alerts)
            
            return VitalInsights(
                patient_id=getattr(latest_vital, 'patient_id', 'unknown'),
                current_status=current_status,
                abnormal_values=abnormal_values,
                trends=trends,
                alerts=alerts,
                recommendations=recommendations,
                risk_factors=risk_factors,
                monitoring_frequency=monitoring_frequency,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing vital signs: {str(e)}")
            raise

    # =============================================================================
    # Multi-Modal Correlation Analysis
    # =============================================================================

    async def correlate_multimodal_data(self, 
                                      image_analysis: ImageAnalysis,
                                      lab_trends: TrendAnalysis,
                                      vital_insights: VitalInsights) -> Dict[str, Any]:
        """
        Correlate findings across multiple data modalities
        
        Args:
            image_analysis: Medical image analysis results
            lab_trends: Laboratory trend analysis
            vital_insights: Vital sign analysis
            
        Returns:
            Comprehensive multi-modal analysis
        """
        try:
            self.logger.info("Performing multi-modal correlation analysis")
            
            # Identify correlations
            correlations = []
            
            # Image-Lab correlations
            if image_analysis.image_type == ImageType.XRAY:
                # Check for pneumonia indicators in labs
                for trend in lab_trends.lab_trends:
                    if trend.test_name == "white_blood_cells" and trend.latest_value > 11.0:
                        if "pneumonia" in [finding.lower() for finding in image_analysis.findings]:
                            correlations.append({
                                "type": "image_lab_correlation",
                                "finding": "Pneumonia indicators",
                                "evidence": ["Chest X-ray findings", "Elevated WBC count"],
                                "confidence": 0.85
                            })
            
            # Vital-Lab correlations
            for vital_alert in vital_insights.alerts:
                if "blood pressure" in vital_alert.lower():
                    # Check for kidney function correlation
                    for trend in lab_trends.lab_trends:
                        if trend.test_name == "creatinine" and trend.trend_direction == TrendDirection.DECLINING:
                            correlations.append({
                                "type": "vital_lab_correlation",
                                "finding": "Hypertension with declining kidney function",
                                "evidence": ["Elevated blood pressure", "Rising creatinine levels"],
                                "confidence": 0.75
                            })
            
            # Generate integrated recommendations
            integrated_recommendations = await self._generate_integrated_recommendations(
                image_analysis, lab_trends, vital_insights, correlations
            )
            
            # Calculate overall risk assessment
            risk_assessment = await self._calculate_multimodal_risk(
                image_analysis, lab_trends, vital_insights
            )
            
            return {
                "correlations": correlations,
                "integrated_recommendations": integrated_recommendations,
                "risk_assessment": risk_assessment,
                "data_completeness": {
                    "imaging": bool(image_analysis.findings),
                    "laboratory": len(lab_trends.lab_trends) > 0,
                    "vitals": len(vital_insights.abnormal_values) >= 0
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in multi-modal correlation: {str(e)}")
            raise

    # =============================================================================
    # Private Helper Methods
    # =============================================================================
    
    async def _decode_medical_image(self, image_data: bytes) -> Image.Image:
        """Decode binary image data"""
        try:
            image_stream = io.BytesIO(image_data)
            image = Image.open(image_stream)
            return image.convert('RGB')
        except Exception as e:
            # Try base64 decoding if direct binary fails
            try:
                decoded_data = base64.b64decode(image_data)
                image_stream = io.BytesIO(decoded_data)
                image = Image.open(image_stream)
                return image.convert('RGB')
            except:
                raise ValueError(f"Unable to decode image data: {str(e)}")
    
    async def _preprocess_medical_image(self, image: Image.Image, image_type: str) -> np.ndarray:
        """Preprocess medical image for analysis"""
        # Resize to standard size
        target_size = self.image_models["preprocessing"]["resize"]
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        image_array = np.array(image) / 255.0
        
        # Enhance contrast for medical images
        if image_type in ["xray", "ct", "mri"]:
            image_array = self._enhance_medical_contrast(image_array)
        
        return image_array
    
    def _enhance_medical_contrast(self, image_array: np.ndarray) -> np.ndarray:
        """Enhance contrast for medical images"""
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(image_array.shape) == 3:
            # Convert to grayscale for medical images
            image_gray = np.dot(image_array[...,:3], [0.2989, 0.5870, 0.1140])
        else:
            image_gray = image_array
            
        # Apply histogram equalization
        image_eq = cv2.equalizeHist((image_gray * 255).astype(np.uint8)) / 255.0
        
        # Combine with original
        enhanced = 0.7 * image_gray + 0.3 * image_eq
        
        # Convert back to RGB if needed
        if len(image_array.shape) == 3:
            enhanced = np.stack([enhanced] * 3, axis=2)
            
        return enhanced
    
    async def _analyze_single_lab_trend(self, test_name: str, test_results: List[Dict]) -> LabTrend:
        """Analyze trend for a single laboratory test"""
        # Sort by date
        sorted_results = sorted(test_results, key=lambda x: x.get('date', '1900-01-01'))
        
        # Extract values and timestamps
        values = [float(result.get('value', 0)) for result in sorted_results]
        timestamps = [datetime.fromisoformat(result.get('date', '1900-01-01')) for result in sorted_results]
        
        # Calculate trend using linear regression
        x_numeric = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]  # Days from first reading
        
        if len(values) >= 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, values)
            r_squared = r_value ** 2
        else:
            slope, r_squared = 0.0, 0.0
        
        # Determine trend direction
        normal_range = self.lab_analyzers["reference_ranges"].get(test_name, (0, float('inf')))
        latest_value = values[-1] if values else 0.0
        
        if abs(slope) < 0.1:  # Minimal change
            trend_direction = TrendDirection.STABLE
        elif slope > 0:
            # Increasing - good or bad depends on the test
            if test_name in ["hemoglobin", "albumin"] and latest_value < normal_range[1]:
                trend_direction = TrendDirection.IMPROVING
            elif test_name in ["creatinine", "glucose"] and latest_value > normal_range[1]:
                trend_direction = TrendDirection.DECLINING
            else:
                trend_direction = TrendDirection.STABLE
        else:
            # Decreasing
            if test_name in ["creatinine", "glucose"] and latest_value > normal_range[0]:
                trend_direction = TrendDirection.IMPROVING
            elif test_name in ["hemoglobin", "albumin"] and latest_value > normal_range[0]:
                trend_direction = TrendDirection.DECLINING
            else:
                trend_direction = TrendDirection.STABLE
        
        # Check for critical trends
        if latest_value < normal_range[0] * 0.5 or latest_value > normal_range[1] * 2:
            trend_direction = TrendDirection.CRITICAL
        
        return LabTrend(
            test_name=test_name,
            values=values,
            timestamps=timestamps,
            trend_direction=trend_direction,
            slope=slope,
            r_squared=r_squared,
            normal_range=normal_range,
            latest_value=latest_value,
            days_trend=len(x_numeric)
        )
    
    async def _identify_abnormal_vitals(self, vital: VitalSignReading, age_group: str) -> List[str]:
        """Identify abnormal vital sign values"""
        abnormal = []
        ranges = self.vital_monitors["normal_ranges"]
        
        # Check heart rate
        if vital.heart_rate is not None:
            hr_range = ranges["heart_rate"].get(age_group, ranges["heart_rate"]["adult"])
            if vital.heart_rate < hr_range[0] or vital.heart_rate > hr_range[1]:
                abnormal.append(f"Heart rate: {vital.heart_rate} bpm (normal: {hr_range[0]}-{hr_range[1]})")
        
        # Check blood pressure
        if vital.blood_pressure_systolic is not None:
            bp_range = ranges["systolic_bp"].get(age_group, ranges["systolic_bp"]["adult"])
            if vital.blood_pressure_systolic < bp_range[0] or vital.blood_pressure_systolic > bp_range[1]:
                abnormal.append(f"Systolic BP: {vital.blood_pressure_systolic} mmHg (normal: {bp_range[0]}-{bp_range[1]})")
        
        # Check temperature
        if vital.temperature is not None:
            temp_range = ranges["temperature"]["all"]
            if vital.temperature < temp_range[0] or vital.temperature > temp_range[1]:
                abnormal.append(f"Temperature: {vital.temperature}°F (normal: {temp_range[0]}-{temp_range[1]})")
        
        # Check oxygen saturation
        if vital.oxygen_saturation is not None:
            spo2_range = ranges["oxygen_saturation"]["all"]
            if vital.oxygen_saturation < spo2_range[0]:
                abnormal.append(f"Oxygen saturation: {vital.oxygen_saturation}% (normal: ≥{spo2_range[0]}%)")
        
        return abnormal

# =============================================================================
# Usage Example and Testing
# =============================================================================

async def main():
    """Example usage of the Multi-Modal Medical Data Processing Engine"""
    
    # Initialize the engine
    engine = MedicalDataFusion()
    
    # Example lab history for trend analysis
    lab_history = [
        {"patient_id": "PAT123", "test_name": "creatinine", "value": 1.2, "date": "2024-10-01T08:00:00"},
        {"patient_id": "PAT123", "test_name": "creatinine", "value": 1.4, "date": "2024-10-08T08:00:00"},
        {"patient_id": "PAT123", "test_name": "creatinine", "value": 1.6, "date": "2024-10-15T08:00:00"},
        {"patient_id": "PAT123", "test_name": "hemoglobin", "value": 10.2, "date": "2024-10-01T08:00:00"},
        {"patient_id": "PAT123", "test_name": "hemoglobin", "value": 10.8, "date": "2024-10-08T08:00:00"},
        {"patient_id": "PAT123", "test_name": "hemoglobin", "value": 11.5, "date": "2024-10-15T08:00:00"},
    ]
    
    # Test lab trend analysis
    print("=== Laboratory Trend Analysis ===")
    trend_analysis = await engine.process_lab_trends(lab_history, analysis_days=30)
    print(f"Overall Trajectory: {trend_analysis.overall_trajectory.value}")
    print(f"Number of Trends Analyzed: {len(trend_analysis.lab_trends)}")
    print("Concerning Trends:")
    for trend in trend_analysis.concerning_trends:
        print(f"  - {trend}")
    
    # Example vital signs stream
    def create_vital_stream():
        """Create example vital signs stream"""
        vitals = []
        base_time = datetime.now() - timedelta(hours=6)
        
        for i in range(10):
            vital = VitalSignReading(
                timestamp=base_time + timedelta(minutes=30*i),
                heart_rate=85 + np.random.randint(-10, 15),
                blood_pressure_systolic=135 + np.random.randint(-15, 20),
                blood_pressure_diastolic=85 + np.random.randint(-10, 10),
                temperature=98.6 + np.random.uniform(-1, 2),
                respiratory_rate=16 + np.random.randint(-2, 4),
                oxygen_saturation=97 + np.random.randint(-2, 3)
            )
            vitals.append(vital)
        
        return iter(vitals)
    
    # Test vital signs monitoring
    print("\n=== Vital Signs Monitoring ===")
    vital_stream = create_vital_stream()
    vital_insights = await engine.process_vital_signs(vital_stream, "adult")
    print(f"Current Status: {vital_insights.current_status.value}")
    print(f"Abnormal Values: {len(vital_insights.abnormal_values)}")
    print(f"Active Alerts: {len(vital_insights.alerts)}")
    print(f"Monitoring Frequency: {vital_insights.monitoring_frequency}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())