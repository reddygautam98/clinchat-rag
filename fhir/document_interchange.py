#!/usr/bin/env python3
"""
Clinical Document Interchange Module
Document management and clinical data interchange for ClinChat-RAG
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Clinical document types"""
    DISCHARGE_SUMMARY = "discharge_summary"
    PROGRESS_NOTE = "progress_note"
    LAB_RESULT = "lab_result"
    IMAGING_REPORT = "imaging_report"
    PATHOLOGY_REPORT = "pathology_report"
    CONSULTATION_NOTE = "consultation_note"
    PROCEDURE_NOTE = "procedure_note"
    MEDICATION_LIST = "medication_list"

class DocumentStatus(Enum):
    """Document status values"""
    CURRENT = "current"
    SUPERSEDED = "superseded"
    ENTERED_IN_ERROR = "entered-in-error"

@dataclass
class DocumentMetadata:
    """Clinical document metadata"""
    document_id: str
    patient_id: str
    document_type: DocumentType
    status: DocumentStatus
    creation_date: datetime
    last_modified: datetime
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    mime_type: str = "text/plain"
    size_bytes: int = 0

@dataclass
class DocumentContent:
    """Clinical document content"""
    document_id: str
    content_text: Optional[str] = None
    content_base64: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    annotations: Optional[List[Dict[str, Any]]] = None

class ClinicalDocumentManager:
    """Clinical document management system"""
    
    def __init__(self):
        """Initialize document manager"""
        self.documents: Dict[str, DocumentMetadata] = {}
        self.content_store: Dict[str, DocumentContent] = {}
    
    def create_document(self, patient_id: str, document_type: DocumentType,
                       content: str, author_id: Optional[str] = None,
                       title: Optional[str] = None) -> str:
        """Create new clinical document"""
        
        # Generate document ID
        document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.documents)}"
        
        # Create metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            patient_id=patient_id,
            document_type=document_type,
            status=DocumentStatus.CURRENT,
            creation_date=datetime.now(),
            last_modified=datetime.now(),
            author_id=author_id,
            title=title or f"{document_type.value.replace('_', ' ').title()}",
            mime_type="text/plain",
            size_bytes=len(content.encode('utf-8'))
        )
        
        # Create content
        document_content = DocumentContent(
            document_id=document_id,
            content_text=content
        )
        
        # Store document
        self.documents[document_id] = metadata
        self.content_store[document_id] = document_content
        
        logger.info(f"Created document {document_id} for patient {patient_id}")
        return document_id
    
    def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata"""
        return self.documents.get(document_id)
    
    def get_document_content(self, document_id: str) -> Optional[DocumentContent]:
        """Get document content"""
        return self.content_store.get(document_id)
    
    def get_patient_documents(self, patient_id: str) -> List[DocumentMetadata]:
        """Get all documents for a patient"""
        return [
            doc for doc in self.documents.values()
            if doc.patient_id == patient_id and doc.status == DocumentStatus.CURRENT
        ]
    
    def update_document(self, document_id: str, content: str,
                       author_id: Optional[str] = None) -> bool:
        """Update existing document"""
        if document_id not in self.documents:
            return False
        
        # Update metadata
        metadata = self.documents[document_id]
        metadata.last_modified = datetime.now()
        metadata.size_bytes = len(content.encode('utf-8'))
        
        if author_id:
            metadata.author_id = author_id
        
        # Update content
        if document_id in self.content_store:
            self.content_store[document_id].content_text = content
        else:
            self.content_store[document_id] = DocumentContent(
                document_id=document_id,
                content_text=content
            )
        
        logger.info(f"Updated document {document_id}")
        return True
    
    def delete_document(self, document_id: str) -> bool:
        """Mark document as entered in error"""
        if document_id not in self.documents:
            return False
        
        self.documents[document_id].status = DocumentStatus.ENTERED_IN_ERROR
        self.documents[document_id].last_modified = datetime.now()
        
        logger.info(f"Marked document {document_id} as entered in error")
        return True
    
    def search_documents(self, patient_id: Optional[str] = None,
                        document_type: Optional[DocumentType] = None,
                        author_id: Optional[str] = None,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None) -> List[DocumentMetadata]:
        """Search documents by criteria"""
        results = []
        
        for doc in self.documents.values():
            # Skip documents marked as entered in error
            if doc.status == DocumentStatus.ENTERED_IN_ERROR:
                continue
            
            # Apply filters
            if patient_id and doc.patient_id != patient_id:
                continue
            
            if document_type and doc.document_type != document_type:
                continue
            
            if author_id and doc.author_id != author_id:
                continue
            
            if date_from and doc.creation_date < date_from:
                continue
            
            if date_to and doc.creation_date > date_to:
                continue
            
            results.append(doc)
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x.creation_date, reverse=True)
        return results

class DocumentInterchange:
    """Document interchange service for external systems"""
    
    def __init__(self, document_manager: ClinicalDocumentManager):
        """Initialize document interchange"""
        self.document_manager = document_manager
    
    def export_document_to_fhir(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Export document as FHIR DocumentReference"""
        metadata = self.document_manager.get_document_metadata(document_id)
        content = self.document_manager.get_document_content(document_id)
        
        if not metadata or not content:
            return None
        
        # Create FHIR DocumentReference resource
        fhir_resource = {
            "resourceType": "DocumentReference",
            "id": document_id,
            "status": self._map_status_to_fhir(metadata.status),
            "type": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": self._map_type_to_loinc(metadata.document_type),
                    "display": metadata.title or metadata.document_type.value
                }]
            },
            "subject": {
                "reference": f"Patient/{metadata.patient_id}"
            },
            "date": metadata.creation_date.isoformat(),
            "content": [{
                "attachment": {
                    "contentType": metadata.mime_type,
                    "size": metadata.size_bytes,
                    "title": metadata.title
                }
            }]
        }
        
        # Add content data
        if content.content_text:
            encoded_content = base64.b64encode(
                content.content_text.encode('utf-8')
            ).decode('ascii')
            fhir_resource["content"][0]["attachment"]["data"] = encoded_content
        
        # Add author if available
        if metadata.author_id:
            fhir_resource["author"] = [{
                "reference": f"Practitioner/{metadata.author_id}"
            }]
        
        return fhir_resource
    
    def import_document_from_fhir(self, fhir_resource: Dict[str, Any]) -> Optional[str]:
        """Import document from FHIR DocumentReference"""
        try:
            # Extract patient ID
            patient_ref = fhir_resource.get("subject", {}).get("reference", "")
            patient_id = patient_ref.replace("Patient/", "") if patient_ref.startswith("Patient/") else ""
            
            if not patient_id:
                logger.error("No patient ID found in FHIR resource")
                return None
            
            # Extract document type
            document_type = self._map_fhir_type_to_local(fhir_resource)
            
            # Extract content
            content_text = ""
            content_list = fhir_resource.get("content", [])
            
            if content_list:
                attachment = content_list[0].get("attachment", {})
                
                # Decode base64 content if present
                if attachment.get("data"):
                    try:
                        content_bytes = base64.b64decode(attachment["data"])
                        content_text = content_bytes.decode('utf-8')
                    except Exception as e:
                        logger.error(f"Failed to decode document content: {e}")
                        return None
            
            # Extract metadata
            title = None
            if content_list and content_list[0].get("attachment", {}).get("title"):
                title = content_list[0]["attachment"]["title"]
            
            # Extract author
            author_id = None
            authors = fhir_resource.get("author", [])
            if authors:
                author_ref = authors[0].get("reference", "")
                if author_ref.startswith("Practitioner/"):
                    author_id = author_ref.replace("Practitioner/", "")
            
            # Create document
            document_id = self.document_manager.create_document(
                patient_id=patient_id,
                document_type=document_type,
                content=content_text,
                author_id=author_id,
                title=title
            )
            
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to import FHIR document: {e}")
            return None
    
    def export_patient_bundle(self, patient_id: str) -> Dict[str, Any]:
        """Export all patient documents as FHIR Bundle"""
        documents = self.document_manager.get_patient_documents(patient_id)
        
        # Create FHIR Bundle
        bundle = {
            "resourceType": "Bundle",
            "id": f"patient-docs-{patient_id}",
            "type": "collection",
            "timestamp": datetime.now().isoformat(),
            "total": len(documents),
            "entry": []
        }
        
        # Add each document as bundle entry
        for doc in documents:
            fhir_resource = self.export_document_to_fhir(doc.document_id)
            if fhir_resource:
                bundle["entry"].append({
                    "resource": fhir_resource
                })
        
        return bundle
    
    def _map_status_to_fhir(self, status: DocumentStatus) -> str:
        """Map internal status to FHIR status"""
        mapping = {
            DocumentStatus.CURRENT: "current",
            DocumentStatus.SUPERSEDED: "superseded",
            DocumentStatus.ENTERED_IN_ERROR: "entered-in-error"
        }
        return mapping.get(status, "current")
    
    def _map_type_to_loinc(self, doc_type: DocumentType) -> str:
        """Map document type to LOINC code"""
        mapping = {
            DocumentType.DISCHARGE_SUMMARY: "18842-5",
            DocumentType.PROGRESS_NOTE: "11506-3",
            DocumentType.LAB_RESULT: "11502-2",
            DocumentType.IMAGING_REPORT: "18748-4",
            DocumentType.PATHOLOGY_REPORT: "11529-5",
            DocumentType.CONSULTATION_NOTE: "11488-4",
            DocumentType.PROCEDURE_NOTE: "28570-0",
            DocumentType.MEDICATION_LIST: "10160-0"
        }
        return mapping.get(doc_type, "34133-9")  # Default: Summary of episode note
    
    def _map_fhir_type_to_local(self, fhir_resource: Dict[str, Any]) -> DocumentType:
        """Map FHIR document type to local document type"""
        # Extract LOINC code from FHIR resource
        type_coding = fhir_resource.get("type", {}).get("coding", [{}])[0]
        loinc_code = type_coding.get("code", "")
        
        # Map LOINC codes to document types
        mapping = {
            "18842-5": DocumentType.DISCHARGE_SUMMARY,
            "11506-3": DocumentType.PROGRESS_NOTE,
            "11502-2": DocumentType.LAB_RESULT,
            "18748-4": DocumentType.IMAGING_REPORT,
            "11529-5": DocumentType.PATHOLOGY_REPORT,
            "11488-4": DocumentType.CONSULTATION_NOTE,
            "28570-0": DocumentType.PROCEDURE_NOTE,
            "10160-0": DocumentType.MEDICATION_LIST
        }
        
        return mapping.get(loinc_code, DocumentType.PROGRESS_NOTE)

# Example usage and testing
def create_sample_documents():
    """Create sample clinical documents for testing"""
    
    doc_manager = ClinicalDocumentManager()
    
    # Create discharge summary
    discharge_content = """
    DISCHARGE SUMMARY
    
    Patient: John Doe
    DOB: 1980-01-15
    MRN: 12345678
    
    ADMISSION DATE: 2024-01-01
    DISCHARGE DATE: 2024-01-05
    
    DIAGNOSIS:
    Primary: Acute myocardial infarction
    Secondary: Hypertension, Type 2 diabetes mellitus
    
    HOSPITAL COURSE:
    Patient presented with chest pain and was diagnosed with STEMI.
    Underwent primary PCI with stent placement to LAD.
    Recovery was uncomplicated.
    
    DISCHARGE MEDICATIONS:
    - Aspirin 81mg daily
    - Clopidogrel 75mg daily
    - Metoprolol 50mg twice daily
    - Atorvastatin 80mg daily
    
    FOLLOW-UP:
    Cardiology in 1 week
    Primary care in 2 weeks
    """
    
    doc_id = doc_manager.create_document(
        patient_id="patient_123",
        document_type=DocumentType.DISCHARGE_SUMMARY,
        content=discharge_content,
        author_id="dr_smith",
        title="Discharge Summary - MI"
    )
    
    print(f"Created document: {doc_id}")
    
    # Create progress note
    progress_content = """
    PROGRESS NOTE
    
    Date: 2024-01-10
    Time: 14:30
    
    SUBJECTIVE:
    Patient reports feeling well. No chest pain or shortness of breath.
    Taking medications as prescribed.
    
    OBJECTIVE:
    Vital signs stable. Heart rate 68, BP 128/78
    Incision site healing well, no signs of infection.
    
    ASSESSMENT:
    Post-MI recovery progressing well.
    
    PLAN:
    Continue current medications.
    Cardiac rehabilitation referral.
    Return in 1 month.
    """
    
    doc_id2 = doc_manager.create_document(
        patient_id="patient_123",
        document_type=DocumentType.PROGRESS_NOTE,
        content=progress_content,
        author_id="dr_jones",
        title="Follow-up Visit"
    )
    
    print(f"Created document: {doc_id2}")
    
    # Test document interchange
    interchange = DocumentInterchange(doc_manager)
    
    # Export to FHIR
    fhir_resource = interchange.export_document_to_fhir(doc_id)
    print(f"Exported FHIR resource: {fhir_resource['resourceType']} with ID {fhir_resource['id']}")
    
    # Export patient bundle
    bundle = interchange.export_patient_bundle("patient_123")
    print(f"Created bundle with {bundle['total']} documents")
    
    return doc_manager, interchange

if __name__ == "__main__":
    # Run sample document creation
    manager, interchange = create_sample_documents()
    
    # List all documents for patient
    docs = manager.get_patient_documents("patient_123")
    print(f"\nPatient has {len(docs)} documents:")
    
    for doc in docs:
        print(f"- {doc.title} ({doc.document_type.value}) - {doc.creation_date}")