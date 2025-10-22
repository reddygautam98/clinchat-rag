#!/usr/bin/env python3
"""
HL7 FHIR R4 Integration Module
EHR integration with patient data exchange and clinical document interchange
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp
import xml.etree.ElementTree as ET
from pathlib import Path
import base64
import hashlib

# FHIR Python client (if available)
try:
    from fhirclient import client
    from fhirclient.models import patient, observation, diagnosticreport, documentreference
    FHIR_CLIENT_AVAILABLE = True
except ImportError:
    FHIR_CLIENT_AVAILABLE = False

# Database integration
try:
    from database.connection import get_db_context
    from database.models import ClinicalDocument, User
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class FHIRResourceType(Enum):
    """FHIR Resource types supported"""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"
    CONDITION = "Condition"
    MEDICATION_REQUEST = "MedicationRequest"
    PROCEDURE = "Procedure"
    ENCOUNTER = "Encounter"
    PRACTITIONER = "Practitioner"
    ORGANIZATION = "Organization"
    BUNDLE = "Bundle"

class FHIRVersion(Enum):
    """FHIR versions supported"""
    R4 = "4.0.1"
    R5 = "5.0.0"

@dataclass
class FHIREndpoint:
    """FHIR endpoint configuration"""
    base_url: str
    version: FHIRVersion
    auth_type: str  # "oauth2", "basic", "bearer", "none"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

@dataclass
class FHIRPatient:
    """FHIR Patient resource wrapper"""
    id: str
    identifier: List[Dict[str, str]]
    name: List[Dict[str, Any]]
    birth_date: Optional[str]
    gender: Optional[str]
    address: List[Dict[str, Any]]
    telecom: List[Dict[str, Any]]
    active: bool = True

@dataclass
class FHIRDocument:
    """FHIR DocumentReference wrapper"""
    id: str
    patient_id: str
    document_type: str
    content_type: str
    content_data: Optional[str]  # Base64 encoded
    content_url: Optional[str]
    creation_date: datetime
    author: Optional[str]
    description: Optional[str]
    status: str = "current"

class FHIRIntegrationEngine:
    """HL7 FHIR integration engine for EHR connectivity"""
    
    def __init__(self, endpoint: FHIREndpoint):
        """Initialize FHIR integration engine"""
        self.endpoint = endpoint
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_headers = {}
        self._initialize_auth()
        
    def _initialize_auth(self):
        """Initialize authentication headers"""
        if self.endpoint.auth_type == "bearer" and self.endpoint.access_token:
            self._auth_headers["Authorization"] = f"Bearer {self.endpoint.access_token}"
        elif self.endpoint.auth_type == "basic" and self.endpoint.username and self.endpoint.password:
            credentials = base64.b64encode(
                f"{self.endpoint.username}:{self.endpoint.password}".encode()
            ).decode()
            self._auth_headers["Authorization"] = f"Basic {credentials}"
        
        # Standard FHIR headers
        self._auth_headers.update({
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json; charset=UTF-8",
            "User-Agent": "ClinChat-RAG-FHIR/1.0"
        })
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.endpoint.timeout),
            headers=self._auth_headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test FHIR server connection and capabilities"""
        try:
            async with self as client:
                # Get capability statement
                url = f"{self.endpoint.base_url}/metadata"
                
                async with client.session.get(url) as response:
                    if response.status == 200:
                        capability_data = await response.json()
                        
                        return {
                            "status": "connected",
                            "fhir_version": capability_data.get("fhirVersion"),
                            "server_software": capability_data.get("software", {}).get("name"),
                            "server_version": capability_data.get("software", {}).get("version"),
                            "supported_resources": [
                                res.get("type") for res in 
                                capability_data.get("rest", [{}])[0].get("resource", [])
                            ],
                            "response_time_ms": response.headers.get("X-Response-Time"),
                            "last_updated": capability_data.get("date")
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}: {await response.text()}"
                        }
                        
        except Exception as e:
            logger.error(f"FHIR connection test failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def search_patients(self, search_params: Dict[str, str]) -> List[FHIRPatient]:
        """Search for patients using FHIR search parameters"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/Patient"
                
                async with client.session.get(url, params=search_params) as response:
                    if response.status == 200:
                        bundle_data = await response.json()
                        patients = []
                        
                        for entry in bundle_data.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "Patient":
                                patient = self._parse_patient_resource(resource)
                                patients.append(patient)
                        
                        return patients
                    else:
                        logger.error(f"Patient search failed: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Patient search error: {e}")
            return []
    
    async def get_patient(self, patient_id: str) -> Optional[FHIRPatient]:
        """Get specific patient by ID"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/Patient/{patient_id}"
                
                async with client.session.get(url) as response:
                    if response.status == 200:
                        patient_data = await response.json()
                        return self._parse_patient_resource(patient_data)
                    elif response.status == 404:
                        logger.warning(f"Patient {patient_id} not found")
                        return None
                    else:
                        logger.error(f"Get patient failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Get patient error: {e}")
            return None
    
    async def get_patient_documents(self, patient_id: str, 
                                  document_types: Optional[List[str]] = None) -> List[FHIRDocument]:
        """Get clinical documents for a patient"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/DocumentReference"
                params = {"patient": patient_id}
                
                if document_types:
                    params["type"] = ",".join(document_types)
                
                async with client.session.get(url, params=params) as response:
                    if response.status == 200:
                        bundle_data = await response.json()
                        documents = []
                        
                        for entry in bundle_data.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "DocumentReference":
                                document = self._parse_document_resource(resource)
                                documents.append(document)
                        
                        return documents
                    else:
                        logger.error(f"Document search failed: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []
    
    async def upload_document(self, document: FHIRDocument) -> Optional[str]:
        """Upload a clinical document as FHIR DocumentReference"""
        try:
            async with self as client:
                # Create FHIR DocumentReference resource
                doc_ref = self._create_document_reference(document)
                
                url = f"{self.endpoint.base_url}/DocumentReference"
                
                async with client.session.post(url, json=doc_ref) as response:
                    if response.status in [200, 201]:
                        created_resource = await response.json()
                        return created_resource.get("id")
                    else:
                        logger.error(f"Document upload failed: HTTP {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error details: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Document upload error: {e}")
            return None
    
    async def create_diagnostic_report(self, patient_id: str, analysis_result: Dict[str, Any],
                                     performer_id: Optional[str] = None) -> Optional[str]:
        """Create FHIR DiagnosticReport from AI analysis results"""
        try:
            async with self as client:
                # Create FHIR DiagnosticReport resource
                report = self._create_diagnostic_report_resource(
                    patient_id, analysis_result, performer_id
                )
                
                url = f"{self.endpoint.base_url}/DiagnosticReport"
                
                async with client.session.post(url, json=report) as response:
                    if response.status in [200, 201]:
                        created_resource = await response.json()
                        return created_resource.get("id")
                    else:
                        logger.error(f"DiagnosticReport creation failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"DiagnosticReport creation error: {e}")
            return None
    
    async def get_patient_observations(self, patient_id: str,
                                    observation_codes: Optional[List[str]] = None,
                                    date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Dict[str, Any]]:
        """Get patient observations (lab results, vital signs, etc.)"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/Observation"
                params = {"patient": patient_id}
                
                if observation_codes:
                    params["code"] = ",".join(observation_codes)
                
                if date_range:
                    start_date, end_date = date_range
                    params["date"] = f"ge{start_date.isoformat()}&date=le{end_date.isoformat()}"
                
                async with client.session.get(url, params=params) as response:
                    if response.status == 200:
                        bundle_data = await response.json()
                        observations = []
                        
                        for entry in bundle_data.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "Observation":
                                observations.append(resource)
                        
                        return observations
                    else:
                        logger.error(f"Observation search failed: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Observation search error: {e}")
            return []
    
    def _parse_patient_resource(self, resource: Dict[str, Any]) -> FHIRPatient:
        """Parse FHIR Patient resource to FHIRPatient object"""
        return FHIRPatient(
            id=resource.get("id", ""),
            identifier=resource.get("identifier", []),
            name=resource.get("name", []),
            birth_date=resource.get("birthDate"),
            gender=resource.get("gender"),
            address=resource.get("address", []),
            telecom=resource.get("telecom", []),
            active=resource.get("active", True)
        )
    
    def _parse_document_resource(self, resource: Dict[str, Any]) -> FHIRDocument:
        """Parse FHIR DocumentReference resource to FHIRDocument object"""
        content = resource.get("content", [{}])[0]
        attachment = content.get("attachment", {})
        
        return FHIRDocument(
            id=resource.get("id", ""),
            patient_id=self._extract_patient_id_from_reference(
                resource.get("subject", {}).get("reference", "")
            ),
            document_type=self._extract_code_from_concept(
                resource.get("type", {})
            ),
            content_type=attachment.get("contentType", ""),
            content_data=attachment.get("data"),
            content_url=attachment.get("url"),
            creation_date=self._parse_fhir_datetime(resource.get("date")),
            author=self._extract_author_from_resource(resource),
            description=resource.get("description"),
            status=resource.get("status", "current")
        )
    
    def _create_document_reference(self, document: FHIRDocument) -> Dict[str, Any]:
        """Create FHIR DocumentReference resource from FHIRDocument"""
        doc_ref = {
            "resourceType": "DocumentReference",
            "status": document.status,
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34133-9",
                    "display": "Summary of episode note"
                }]
            },
            "subject": {
                "reference": f"Patient/{document.patient_id}"
            },
            "date": document.creation_date.isoformat(),
            "content": [{
                "attachment": {
                    "contentType": document.content_type
                }
            }]
        }
        
        # Add content data or URL
        if document.content_data:
            doc_ref["content"][0]["attachment"]["data"] = document.content_data
        elif document.content_url:
            doc_ref["content"][0]["attachment"]["url"] = document.content_url
        
        # Add description if available
        if document.description:
            doc_ref["description"] = document.description
        
        # Add author if available
        if document.author:
            doc_ref["author"] = [{"reference": f"Practitioner/{document.author}"}]
        
        return doc_ref
    
    def _create_diagnostic_report_resource(self, patient_id: str, 
                                         analysis_result: Dict[str, Any],
                                         performer_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR DiagnosticReport resource from AI analysis results"""
        report = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "33747-0",
                    "display": "General medical examination"
                }]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": datetime.now().isoformat(),
            "issued": datetime.now().isoformat()
        }
        
        # Add performer if available
        if performer_id:
            report["performer"] = [{"reference": f"Practitioner/{performer_id}"}]
        
        # Add AI analysis results as conclusion
        if "analysis" in analysis_result:
            report["conclusion"] = analysis_result["analysis"]
        
        # Add confidence score as component
        if "confidence_score" in analysis_result:
            report["component"] = [{
                "code": {
                    "coding": [{
                        "system": "http://clinchat-rag.local/codes",
                        "code": "confidence-score",
                        "display": "AI Confidence Score"
                    }]
                },
                "valueQuantity": {
                    "value": analysis_result["confidence_score"],
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%"
                }
            }]
        
        return report
    
    def _extract_patient_id_from_reference(self, reference: str) -> str:
        """Extract patient ID from FHIR reference"""
        if reference.startswith("Patient/"):
            return reference.replace("Patient/", "")
        return reference
    
    def _extract_code_from_concept(self, concept: Dict[str, Any]) -> str:
        """Extract code from FHIR CodeableConcept"""
        coding = concept.get("coding", [{}])[0]
        return coding.get("code", "")
    
    def _parse_fhir_datetime(self, fhir_datetime: Optional[str]) -> datetime:
        """Parse FHIR datetime string"""
        if not fhir_datetime:
            return datetime.now()
        
        try:
            # Handle different FHIR date formats
            if "T" in fhir_datetime:
                # Full datetime
                return datetime.fromisoformat(fhir_datetime.replace("Z", "+00:00"))
            else:
                # Date only
                return datetime.strptime(fhir_datetime, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse FHIR datetime: {fhir_datetime}")
            return datetime.now()
    
    def _extract_author_from_resource(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract author information from FHIR resource"""
        authors = resource.get("author", [])
        if authors:
            author_ref = authors[0].get("reference", "")
            if author_ref.startswith("Practitioner/"):
                return author_ref.replace("Practitioner/", "")
        return None

class FHIRPatientMatcher:
    """Patient matching service for FHIR integration"""
    
    def __init__(self):
        """Initialize patient matcher"""
        pass
    
    async def match_patient(self, local_patient_data: Dict[str, Any],
                          fhir_engine: FHIRIntegrationEngine) -> Optional[str]:
        """Match local patient data to FHIR patient"""
        try:
            # Build search parameters based on available data
            search_params = {}
            
            # Search by identifier (MRN, SSN, etc.)
            if "mrn" in local_patient_data:
                search_params["identifier"] = local_patient_data["mrn"]
            
            # Search by name and birth date
            if "first_name" in local_patient_data and "last_name" in local_patient_data:
                search_params["given"] = local_patient_data["first_name"]
                search_params["family"] = local_patient_data["last_name"]
            
            if "birth_date" in local_patient_data:
                search_params["birthdate"] = local_patient_data["birth_date"]
            
            # Perform FHIR search
            patients = await fhir_engine.search_patients(search_params)
            
            # Match logic
            for patient in patients:
                match_score = self._calculate_match_score(local_patient_data, patient)
                if match_score > 0.8:  # High confidence match
                    return patient.id
            
            return None
            
        except Exception as e:
            logger.error(f"Patient matching error: {e}")
            return None
    
    def _calculate_match_score(self, local_data: Dict[str, Any], 
                             fhir_patient: FHIRPatient) -> float:
        """Calculate match score between local data and FHIR patient"""
        score = 0.0
        total_factors = 0
        
        # Name matching
        if "first_name" in local_data and fhir_patient.name:
            local_first = local_data["first_name"].lower()
            for name in fhir_patient.name:
                fhir_given = name.get("given", [])
                if fhir_given and local_first in [g.lower() for g in fhir_given]:
                    score += 0.3
                    break
            total_factors += 0.3
        
        if "last_name" in local_data and fhir_patient.name:
            local_last = local_data["last_name"].lower()
            for name in fhir_patient.name:
                fhir_family = name.get("family", "").lower()
                if fhir_family == local_last:
                    score += 0.3
                    break
            total_factors += 0.3
        
        # Birth date matching
        if "birth_date" in local_data and fhir_patient.birth_date:
            if local_data["birth_date"] == fhir_patient.birth_date:
                score += 0.4
            total_factors += 0.4
        
        # Return normalized score
        return score / total_factors if total_factors > 0 else 0.0

class FHIRBundleProcessor:
    """Process FHIR bundles for bulk operations"""
    
    def __init__(self, fhir_engine: FHIRIntegrationEngine):
        """Initialize bundle processor"""
        self.fhir_engine = fhir_engine
    
    async def process_patient_bundle(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient data bundle"""
        try:
            # Get patient demographics
            patient = await self.fhir_engine.get_patient(patient_id)
            
            # Get patient documents
            documents = await self.fhir_engine.get_patient_documents(patient_id)
            
            # Get recent observations (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            observations = await self.fhir_engine.get_patient_observations(
                patient_id, date_range=(start_date, end_date)
            )
            
            return {
                "patient": asdict(patient) if patient else None,
                "documents": [asdict(doc) for doc in documents],
                "observations": observations,
                "bundle_created": datetime.now().isoformat(),
                "bundle_scope": "comprehensive"
            }
            
        except Exception as e:
            logger.error(f"Bundle processing error: {e}")
            return {"error": str(e)}

# CLI Interface
async def main():
    """Main CLI interface for FHIR integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClinChat-RAG FHIR Integration")
    parser.add_argument("--test-connection", action="store_true", help="Test FHIR server connection")
    parser.add_argument("--search-patient", type=str, help="Search for patient by name")
    parser.add_argument("--get-patient", type=str, help="Get patient by ID")
    parser.add_argument("--get-documents", type=str, help="Get documents for patient ID")
    
    # FHIR server configuration
    parser.add_argument("--server", type=str, default="http://hapi.fhir.org/baseR4",
                       help="FHIR server base URL")
    parser.add_argument("--auth-type", type=str, default="none",
                       choices=["oauth2", "basic", "bearer", "none"],
                       help="Authentication type")
    parser.add_argument("--token", type=str, help="Bearer token for authentication")
    
    args = parser.parse_args()
    
    # Create FHIR endpoint configuration
    endpoint = FHIREndpoint(
        base_url=args.server,
        version=FHIRVersion.R4,
        auth_type=args.auth_type,
        access_token=args.token
    )
    
    # Create FHIR engine
    fhir_engine = FHIRIntegrationEngine(endpoint)
    
    if args.test_connection:
        print("🔍 Testing FHIR server connection...")
        result = await fhir_engine.test_connection()
        
        if result["status"] == "connected":
            print("✅ FHIR server connected successfully!")
            print(f"   Server: {result.get('server_software')} {result.get('server_version')}")
            print(f"   FHIR Version: {result.get('fhir_version')}")
            print(f"   Supported Resources: {len(result.get('supported_resources', []))}")
        else:
            print(f"❌ Connection failed: {result.get('error')}")
    
    elif args.search_patient:
        print(f"🔍 Searching for patient: {args.search_patient}")
        
        # Simple name search
        names = args.search_patient.split()
        search_params = {}
        
        if len(names) >= 2:
            search_params["given"] = names[0]
            search_params["family"] = names[1]
        else:
            search_params["name"] = args.search_patient
        
        patients = await fhir_engine.search_patients(search_params)
        
        print(f"Found {len(patients)} patients:")
        for patient in patients:
            name_str = ""
            if patient.name:
                name = patient.name[0]
                given = " ".join(name.get("given", []))
                family = name.get("family", "")
                name_str = f"{given} {family}".strip()
            
            print(f"  • ID: {patient.id}")
            print(f"    Name: {name_str}")
            print(f"    Birth Date: {patient.birth_date}")
            print(f"    Gender: {patient.gender}")
            print()
    
    elif args.get_patient:
        print(f"👤 Getting patient: {args.get_patient}")
        
        patient = await fhir_engine.get_patient(args.get_patient)
        
        if patient:
            print(f"Patient ID: {patient.id}")
            print(f"Active: {patient.active}")
            
            if patient.name:
                for name in patient.name:
                    given = " ".join(name.get("given", []))
                    family = name.get("family", "")
                    print(f"Name: {given} {family}")
            
            print(f"Birth Date: {patient.birth_date}")
            print(f"Gender: {patient.gender}")
            
            if patient.identifier:
                print("Identifiers:")
                for identifier in patient.identifier:
                    system = identifier.get("system", "")
                    value = identifier.get("value", "")
                    print(f"  {system}: {value}")
        else:
            print("❌ Patient not found")
    
    elif args.get_documents:
        print(f"📄 Getting documents for patient: {args.get_documents}")
        
        documents = await fhir_engine.get_patient_documents(args.get_documents)
        
        print(f"Found {len(documents)} documents:")
        for doc in documents:
            print(f"  • ID: {doc.id}")
            print(f"    Type: {doc.document_type}")
            print(f"    Content Type: {doc.content_type}")
            print(f"    Creation Date: {doc.creation_date}")
            print(f"    Status: {doc.status}")
            if doc.description:
                print(f"    Description: {doc.description}")
            print()

if __name__ == "__main__":
    asyncio.run(main())