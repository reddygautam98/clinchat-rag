#!/usr/bin/env python3
"""
FHIR Patient Data Exchange Module
Simplified patient data exchange and clinical document interchange
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import base64
import aiohttp

logger = logging.getLogger(__name__)

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

@dataclass
class PatientData:
    """Simplified patient data structure"""
    id: str
    name: Dict[str, str]
    birth_date: Optional[str]
    gender: Optional[str]
    identifiers: List[Dict[str, str]]
    active: bool = True

@dataclass
class ClinicalDocument:
    """Clinical document structure"""
    id: str
    patient_id: str
    document_type: str
    content_type: str
    content: Optional[str]
    creation_date: datetime
    author: Optional[str]
    status: str = "current"

class FHIRPatientExchange:
    """FHIR patient data exchange service"""
    
    def __init__(self, endpoint: FHIREndpoint):
        """Initialize FHIR patient exchange"""
        self.endpoint = endpoint
        self.session: Optional[aiohttp.ClientSession] = None
        self._auth_headers = self._build_auth_headers()
    
    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers"""
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json; charset=UTF-8",
            "User-Agent": "ClinChat-RAG-FHIR/1.0"
        }
        
        if self.endpoint.auth_type == "bearer" and self.endpoint.access_token:
            headers["Authorization"] = f"Bearer {self.endpoint.access_token}"
        elif self.endpoint.auth_type == "basic" and self.endpoint.username and self.endpoint.password:
            credentials = base64.b64encode(
                f"{self.endpoint.username}:{self.endpoint.password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
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
        """Test FHIR server connection"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/metadata"
                
                async with client.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "connected",
                            "fhir_version": data.get("fhirVersion"),
                            "server_name": data.get("software", {}).get("name")
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_patient(self, patient_id: str) -> Optional[PatientData]:
        """Get patient by ID"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/Patient/{patient_id}"
                
                async with client.session.get(url) as response:
                    if response.status == 200:
                        patient_resource = await response.json()
                        return self._parse_patient(patient_resource)
                    return None
        except Exception as e:
            logger.error(f"Get patient error: {e}")
            return None
    
    async def search_patients_by_name(self, first_name: str, last_name: str) -> List[PatientData]:
        """Search patients by name"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/Patient"
                params = {
                    "given": first_name,
                    "family": last_name
                }
                
                async with client.session.get(url, params=params) as response:
                    if response.status == 200:
                        bundle = await response.json()
                        patients = []
                        
                        for entry in bundle.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "Patient":
                                patient = self._parse_patient(resource)
                                patients.append(patient)
                        
                        return patients
                    return []
        except Exception as e:
            logger.error(f"Search patients error: {e}")
            return []
    
    async def get_patient_documents(self, patient_id: str) -> List[ClinicalDocument]:
        """Get clinical documents for patient"""
        try:
            async with self as client:
                url = f"{self.endpoint.base_url}/DocumentReference"
                params = {"patient": patient_id}
                
                async with client.session.get(url, params=params) as response:
                    if response.status == 200:
                        bundle = await response.json()
                        documents = []
                        
                        for entry in bundle.get("entry", []):
                            resource = entry.get("resource", {})
                            if resource.get("resourceType") == "DocumentReference":
                                document = self._parse_document(resource)
                                documents.append(document)
                        
                        return documents
                    return []
        except Exception as e:
            logger.error(f"Get documents error: {e}")
            return []
    
    def _parse_patient(self, resource: Dict[str, Any]) -> PatientData:
        """Parse FHIR Patient resource"""
        # Extract name
        name_data = {"first_name": "", "last_name": ""}
        if resource.get("name"):
            name = resource["name"][0]
            if name.get("given"):
                name_data["first_name"] = " ".join(name["given"])
            if name.get("family"):
                name_data["last_name"] = name["family"]
        
        # Extract identifiers
        identifiers = []
        for identifier in resource.get("identifier", []):
            identifiers.append({
                "system": identifier.get("system", ""),
                "value": identifier.get("value", "")
            })
        
        return PatientData(
            id=resource.get("id", ""),
            name=name_data,
            birth_date=resource.get("birthDate"),
            gender=resource.get("gender"),
            identifiers=identifiers,
            active=resource.get("active", True)
        )
    
    def _parse_document(self, resource: Dict[str, Any]) -> ClinicalDocument:
        """Parse FHIR DocumentReference resource"""
        # Extract patient ID from reference
        patient_ref = resource.get("subject", {}).get("reference", "")
        patient_id = patient_ref.replace("Patient/", "") if patient_ref.startswith("Patient/") else patient_ref
        
        # Extract document type
        doc_type = "unknown"
        if resource.get("type", {}).get("coding"):
            doc_type = resource["type"]["coding"][0].get("display", "unknown")
        
        # Extract content
        content_type = ""
        content = None
        if resource.get("content"):
            attachment = resource["content"][0].get("attachment", {})
            content_type = attachment.get("contentType", "")
            content = attachment.get("data")  # Base64 encoded
        
        # Parse creation date
        creation_date = datetime.now()
        if resource.get("date"):
            try:
                creation_date = datetime.fromisoformat(resource["date"].replace("Z", "+00:00"))
            except ValueError:
                pass
        
        return ClinicalDocument(
            id=resource.get("id", ""),
            patient_id=patient_id,
            document_type=doc_type,
            content_type=content_type,
            content=content,
            creation_date=creation_date,
            author=self._extract_author(resource),
            status=resource.get("status", "current")
        )
    
    def _extract_author(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract author from resource"""
        authors = resource.get("author", [])
        if authors:
            author_ref = authors[0].get("reference", "")
            return author_ref.replace("Practitioner/", "") if author_ref.startswith("Practitioner/") else None
        return None

class PatientMatcher:
    """Patient matching service"""
    
    @staticmethod
    def calculate_match_score(local_data: Dict[str, str], fhir_patient: PatientData) -> float:
        """Calculate patient match score"""
        score = 0.0
        
        # Name matching (60% weight)
        name_score = PatientMatcher._compare_names(local_data, fhir_patient.name)
        score += name_score * 0.6
        
        # Birth date matching (40% weight)
        if local_data.get("birth_date") and fhir_patient.birth_date:
            if local_data["birth_date"] == fhir_patient.birth_date:
                score += 0.4
        
        return score
    
    @staticmethod
    def _compare_names(local_data: Dict[str, str], fhir_name: Dict[str, str]) -> float:
        """Compare names for matching"""
        score = 0.0
        
        # First name comparison
        if local_data.get("first_name") and fhir_name.get("first_name"):
            local_first = local_data["first_name"].lower().strip()
            fhir_first = fhir_name["first_name"].lower().strip()
            
            if local_first == fhir_first:
                score += 0.5
            elif local_first in fhir_first or fhir_first in local_first:
                score += 0.3
        
        # Last name comparison
        if local_data.get("last_name") and fhir_name.get("last_name"):
            local_last = local_data["last_name"].lower().strip()
            fhir_last = fhir_name["last_name"].lower().strip()
            
            if local_last == fhir_last:
                score += 0.5
            elif local_last in fhir_last or fhir_last in local_last:
                score += 0.3
        
        return score

class DocumentProcessor:
    """Clinical document processor"""
    
    def __init__(self, fhir_exchange: FHIRPatientExchange):
        """Initialize document processor"""
        self.fhir_exchange = fhir_exchange
    
    async def get_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient summary"""
        try:
            # Get patient data
            patient = await self.fhir_exchange.get_patient(patient_id)
            if not patient:
                return {"error": "Patient not found"}
            
            # Get patient documents
            documents = await self.fhir_exchange.get_patient_documents(patient_id)
            
            # Build summary
            return {
                "patient": asdict(patient),
                "documents": [asdict(doc) for doc in documents],
                "document_count": len(documents),
                "summary_generated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Patient summary error: {e}")
            return {"error": str(e)}
    
    def extract_document_content(self, document: ClinicalDocument) -> Optional[str]:
        """Extract readable content from document"""
        if not document.content:
            return None
        
        try:
            # Decode base64 content
            decoded_content = base64.b64decode(document.content).decode('utf-8')
            return decoded_content
        except Exception as e:
            logger.error(f"Document content extraction error: {e}")
            return None

# Simple CLI for testing
async def test_fhir_connection():
    """Test FHIR server connection"""
    
    # Default to public HAPI FHIR server
    endpoint = FHIREndpoint(
        base_url="http://hapi.fhir.org/baseR4",
        version=FHIRVersion.R4,
        auth_type="none"
    )
    
    exchange = FHIRPatientExchange(endpoint)
    
    print("🔍 Testing FHIR server connection...")
    result = await exchange.test_connection()
    
    if result["status"] == "connected":
        print("✅ FHIR server connected successfully!")
        print(f"   Server: {result.get('server_name')}")
        print(f"   FHIR Version: {result.get('fhir_version')}")
    else:
        print(f"❌ Connection failed: {result.get('error')}")
    
    # Test patient search
    print("\n🔍 Searching for patients named 'John Smith'...")
    patients = await exchange.search_patients_by_name("John", "Smith")
    
    print(f"Found {len(patients)} patients:")
    for patient in patients[:3]:  # Show first 3
        print(f"  • ID: {patient.id}")
        print(f"    Name: {patient.name['first_name']} {patient.name['last_name']}")
        print(f"    Birth Date: {patient.birth_date}")
        print()

if __name__ == "__main__":
    asyncio.run(test_fhir_connection())