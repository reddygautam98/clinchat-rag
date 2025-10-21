# Enhanced ClinChat-RAG Modules
# Advanced Clinical Intelligence System

"""
ClinChat-RAG Enhancement Modules

This package contains advanced medical intelligence modules:
- Clinical Decision Support Engine
- Multi-Modal Medical Data Processing  
- Voice-Controlled Clinical Interface
- Predictive Analytics Suite
- Enhanced Integration Engine
"""

__version__ = "3.0.0"
__author__ = "ClinChat-RAG Development Team"

# Import main classes for easy access
try:
    from .clinical_decision_engine import ClinicalDecisionEngine, ClinicalInsights, SafetyReport, ComplianceReport
    from .medical_data_fusion import MedicalDataFusion, ImageAnalysis, TrendAnalysis, VitalInsights
    from .clinical_voice_interface import ClinicalVoiceInterface, VoiceCommand, ClinicalNote
    from .predictive_analytics import MedicalPredictiveAnalytics, RiskScore, SepsisAlert, AdherenceScore
    from .enhanced_integration import ClinChatEnhancedEngine
    
    __all__ = [
        'ClinicalDecisionEngine', 'ClinicalInsights', 'SafetyReport', 'ComplianceReport',
        'MedicalDataFusion', 'ImageAnalysis', 'TrendAnalysis', 'VitalInsights',
        'ClinicalVoiceInterface', 'VoiceCommand', 'ClinicalNote',
        'MedicalPredictiveAnalytics', 'RiskScore', 'SepsisAlert', 'AdherenceScore',
        'ClinChatEnhancedEngine'
    ]
    
except ImportError as e:
    # Handle missing dependencies gracefully
    print(f"Warning: Some enhancement modules could not be loaded: {e}")
    __all__ = []