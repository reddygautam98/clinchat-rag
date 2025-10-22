"""
FHIR Integration Module Initialization
HL7 FHIR R4 compatibility for EHR integration
"""

from .fhir_config import (
    FHIRServerConfig,
    FHIRMappingConfig,
    FHIRConfigManager,
    FHIRServerTemplates,
    FHIRServerType,
    AuthenticationMethod
)

from .patient_exchange import (
    FHIRPatientExchange,
    PatientData,
    PatientMatcher,
    DocumentProcessor
)

from .document_interchange import (
    ClinicalDocumentManager,
    DocumentInterchange,
    DocumentMetadata,
    DocumentContent,
    DocumentType,
    DocumentStatus
)

__version__ = "1.0.0"
__author__ = "ClinChat-RAG Development Team"

__all__ = [
    # Configuration
    "FHIRServerConfig",
    "FHIRMappingConfig", 
    "FHIRConfigManager",
    "FHIRServerTemplates",
    "FHIRServerType",
    "AuthenticationMethod",
    
    # Patient Exchange
    "FHIRPatientExchange",
    "PatientData",
    "PatientMatcher",
    "DocumentProcessor",
    
    # Document Interchange
    "ClinicalDocumentManager",
    "DocumentInterchange", 
    "DocumentMetadata",
    "DocumentContent",
    "DocumentType",
    "DocumentStatus"
]

# Module-level constants
SUPPORTED_FHIR_VERSION = "4.0.1"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Standard FHIR resource types
CORE_FHIR_RESOURCES = [
    "Patient",
    "Practitioner", 
    "Organization",
    "Observation",
    "DiagnosticReport",
    "DocumentReference",
    "Condition",
    "MedicationRequest",
    "Procedure",
    "Encounter",
    "AllergyIntolerance"
]

def get_version_info():
    """Get FHIR integration module version information"""
    return {
        "version": __version__,
        "fhir_version": SUPPORTED_FHIR_VERSION,
        "supported_resources": CORE_FHIR_RESOURCES,
        "module_name": "ClinChat-RAG FHIR Integration"
    }