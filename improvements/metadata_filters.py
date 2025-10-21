"""
Enhanced Metadata Filtering System for ClinChat-RAG
Supports trial_id, date range, document type, and other clinical metadata filters
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import re
from pathlib import Path

class DocumentType(Enum):
    """Supported document types for filtering"""
    CLINICAL_TRIAL = "clinical_trial"
    RESEARCH_PAPER = "research_paper"
    DRUG_LABEL = "drug_label"
    CLINICAL_GUIDELINE = "clinical_guideline"
    CASE_STUDY = "case_study"
    PROTOCOL = "protocol"
    SAFETY_REPORT = "safety_report"
    REGULATORY_DOCUMENT = "regulatory_document"
    PATIENT_DATA = "patient_data"
    LAB_REPORT = "lab_report"

class TrialPhase(Enum):
    """Clinical trial phases for filtering"""
    PHASE_I = "phase_1"
    PHASE_II = "phase_2"
    PHASE_III = "phase_3"
    PHASE_IV = "phase_4"
    PRECLINICAL = "preclinical"

@dataclass
class MetadataFilter:
    """Comprehensive metadata filter specification"""
    
    # Trial-specific filters
    trial_ids: Optional[List[str]] = None
    trial_phases: Optional[List[TrialPhase]] = None
    study_types: Optional[List[str]] = None  # "randomized", "observational", etc.
    
    # Date filters
    date_from: Optional[Union[datetime, date, str]] = None
    date_to: Optional[Union[datetime, date, str]] = None
    publication_year_from: Optional[int] = None
    publication_year_to: Optional[int] = None
    
    # Document type filters
    document_types: Optional[List[DocumentType]] = None
    source_systems: Optional[List[str]] = None  # "pubmed", "clinicaltrials.gov", etc.
    
    # Medical domain filters
    therapeutic_areas: Optional[List[str]] = None  # "cardiology", "oncology", etc.
    drug_classes: Optional[List[str]] = None
    indication_codes: Optional[List[str]] = None  # ICD-10, SNOMED, etc.
    
    # Quality filters
    evidence_levels: Optional[List[str]] = None  # "A", "B", "C" evidence levels
    journal_tiers: Optional[List[str]] = None    # "tier_1", "tier_2", etc.
    minimum_sample_size: Optional[int] = None
    
    # Regulatory filters
    regulatory_agencies: Optional[List[str]] = None  # "FDA", "EMA", "PMDA", etc.
    approval_statuses: Optional[List[str]] = None    # "approved", "investigational", etc.
    
    # Text-based filters
    keywords_include: Optional[List[str]] = None
    keywords_exclude: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    institutions: Optional[List[str]] = None
    
    # Custom metadata filters
    custom_filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentMetadata:
    """Enhanced document metadata structure"""
    
    # Core identification
    doc_id: str
    title: str
    document_type: DocumentType
    source_system: str
    
    # Temporal information
    publication_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Trial-specific metadata
    trial_id: Optional[str] = None
    trial_phase: Optional[TrialPhase] = None
    study_type: Optional[str] = None
    primary_endpoint: Optional[str] = None
    sample_size: Optional[int] = None
    
    # Medical classification
    therapeutic_area: Optional[str] = None
    drug_name: Optional[str] = None
    drug_class: Optional[str] = None
    indication_codes: List[str] = field(default_factory=list)
    
    # Quality indicators
    evidence_level: Optional[str] = None
    journal_name: Optional[str] = None
    journal_tier: Optional[str] = None
    impact_factor: Optional[float] = None
    
    # Regulatory information
    regulatory_agency: Optional[str] = None
    approval_status: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    # Content metadata
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    institutions: List[str] = field(default_factory=list)
    
    # Processing metadata
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    processing_date: Optional[datetime] = None
    
    # Custom metadata
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

class MetadataFilterEngine:
    """Advanced metadata filtering engine for clinical documents"""
    
    def __init__(self):
        self.date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d", 
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S"
        ]
    
    def apply_filters(self, documents: List[DocumentMetadata], 
                     filters: MetadataFilter) -> List[DocumentMetadata]:
        """Apply comprehensive metadata filtering to document list"""
        
        filtered_docs = documents
        
        # Apply each filter category
        filtered_docs = self._filter_by_trials(filtered_docs, filters)
        filtered_docs = self._filter_by_dates(filtered_docs, filters)
        filtered_docs = self._filter_by_document_types(filtered_docs, filters)
        filtered_docs = self._filter_by_medical_domain(filtered_docs, filters)
        filtered_docs = self._filter_by_quality(filtered_docs, filters)
        filtered_docs = self._filter_by_regulatory(filtered_docs, filters)
        filtered_docs = self._filter_by_text(filtered_docs, filters)
        filtered_docs = self._filter_by_custom(filtered_docs, filters)
        
        return filtered_docs
    
    def _filter_by_trials(self, documents: List[DocumentMetadata], 
                         filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by trial-specific criteria"""
        
        filtered = documents
        
        # Filter by trial IDs
        if filters.trial_ids:
            trial_ids = set(filters.trial_ids)
            filtered = [doc for doc in filtered 
                       if doc.trial_id and doc.trial_id in trial_ids]
        
        # Filter by trial phases
        if filters.trial_phases:
            phases = set(filters.trial_phases)
            filtered = [doc for doc in filtered 
                       if doc.trial_phase and doc.trial_phase in phases]
        
        # Filter by study types
        if filters.study_types:
            study_types = set(s.lower() for s in filters.study_types)
            filtered = [doc for doc in filtered 
                       if doc.study_type and doc.study_type.lower() in study_types]
        
        return filtered
    
    def _filter_by_dates(self, documents: List[DocumentMetadata], 
                        filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by date ranges"""
        
        filtered = documents
        
        # Parse date filters
        date_from = self._parse_date(filters.date_from) if filters.date_from else None
        date_to = self._parse_date(filters.date_to) if filters.date_to else None
        
        # Filter by publication date range
        if date_from or date_to:
            def date_in_range(doc_date: Optional[datetime]) -> bool:
                if not doc_date:
                    return False
                if date_from and doc_date < date_from:
                    return False
                if date_to and doc_date > date_to:
                    return False
                return True
            
            filtered = [doc for doc in filtered 
                       if date_in_range(doc.publication_date)]
        
        # Filter by publication year range
        if filters.publication_year_from or filters.publication_year_to:
            def year_in_range(doc: DocumentMetadata) -> bool:
                if not doc.publication_date:
                    return False
                year = doc.publication_date.year
                if filters.publication_year_from and year < filters.publication_year_from:
                    return False
                if filters.publication_year_to and year > filters.publication_year_to:
                    return False
                return True
            
            filtered = [doc for doc in filtered if year_in_range(doc)]
        
        return filtered
    
    def _filter_by_document_types(self, documents: List[DocumentMetadata], 
                                 filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by document types and sources"""
        
        filtered = documents
        
        # Filter by document types
        if filters.document_types:
            doc_types = set(filters.document_types)
            filtered = [doc for doc in filtered if doc.document_type in doc_types]
        
        # Filter by source systems
        if filters.source_systems:
            sources = set(s.lower() for s in filters.source_systems)
            filtered = [doc for doc in filtered 
                       if doc.source_system.lower() in sources]
        
        return filtered
    
    def _filter_by_medical_domain(self, documents: List[DocumentMetadata], 
                                 filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by medical domain criteria"""
        
        filtered = documents
        
        # Filter by therapeutic areas
        if filters.therapeutic_areas:
            areas = set(a.lower() for a in filters.therapeutic_areas)
            filtered = [doc for doc in filtered 
                       if doc.therapeutic_area and doc.therapeutic_area.lower() in areas]
        
        # Filter by drug classes
        if filters.drug_classes:
            classes = set(c.lower() for c in filters.drug_classes)
            filtered = [doc for doc in filtered 
                       if doc.drug_class and doc.drug_class.lower() in classes]
        
        # Filter by indication codes
        if filters.indication_codes:
            codes = set(filters.indication_codes)
            filtered = [doc for doc in filtered 
                       if any(code in codes for code in doc.indication_codes)]
        
        return filtered
    
    def _filter_by_quality(self, documents: List[DocumentMetadata], 
                          filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by quality indicators"""
        
        filtered = documents
        
        # Filter by evidence levels
        if filters.evidence_levels:
            levels = set(filters.evidence_levels)
            filtered = [doc for doc in filtered 
                       if doc.evidence_level and doc.evidence_level in levels]
        
        # Filter by journal tiers
        if filters.journal_tiers:
            tiers = set(filters.journal_tiers)
            filtered = [doc for doc in filtered 
                       if doc.journal_tier and doc.journal_tier in tiers]
        
        # Filter by minimum sample size
        if filters.minimum_sample_size:
            min_size = filters.minimum_sample_size
            filtered = [doc for doc in filtered 
                       if doc.sample_size and doc.sample_size >= min_size]
        
        return filtered
    
    def _filter_by_regulatory(self, documents: List[DocumentMetadata], 
                             filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by regulatory criteria"""
        
        filtered = documents
        
        # Filter by regulatory agencies
        if filters.regulatory_agencies:
            agencies = set(a.upper() for a in filters.regulatory_agencies)
            filtered = [doc for doc in filtered 
                       if doc.regulatory_agency and doc.regulatory_agency.upper() in agencies]
        
        # Filter by approval statuses
        if filters.approval_statuses:
            statuses = set(s.lower() for s in filters.approval_statuses)
            filtered = [doc for doc in filtered 
                       if doc.approval_status and doc.approval_status.lower() in statuses]
        
        return filtered
    
    def _filter_by_text(self, documents: List[DocumentMetadata], 
                       filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by text-based criteria"""
        
        filtered = documents
        
        # Filter by included keywords
        if filters.keywords_include:
            def contains_keywords(doc: DocumentMetadata) -> bool:
                text_content = f"{doc.title} {doc.abstract or ''} {' '.join(doc.keywords)}"
                text_lower = text_content.lower()
                return any(keyword.lower() in text_lower for keyword in filters.keywords_include)
            
            filtered = [doc for doc in filtered if contains_keywords(doc)]
        
        # Filter out excluded keywords
        if filters.keywords_exclude:
            def excludes_keywords(doc: DocumentMetadata) -> bool:
                text_content = f"{doc.title} {doc.abstract or ''} {' '.join(doc.keywords)}"
                text_lower = text_content.lower()
                return not any(keyword.lower() in text_lower for keyword in filters.keywords_exclude)
            
            filtered = [doc for doc in filtered if excludes_keywords(doc)]
        
        # Filter by authors
        if filters.authors:
            authors = set(a.lower() for a in filters.authors)
            filtered = [doc for doc in filtered 
                       if any(author.lower() in authors for author in doc.authors)]
        
        # Filter by institutions
        if filters.institutions:
            institutions = set(i.lower() for i in filters.institutions)
            filtered = [doc for doc in filtered 
                       if any(inst.lower() in institutions for inst in doc.institutions)]
        
        return filtered
    
    def _filter_by_custom(self, documents: List[DocumentMetadata], 
                         filters: MetadataFilter) -> List[DocumentMetadata]:
        """Filter by custom metadata criteria"""
        
        if not filters.custom_filters:
            return documents
        
        filtered = documents
        
        for key, expected_value in filters.custom_filters.items():
            filtered = [doc for doc in filtered 
                       if key in doc.custom_metadata and 
                       doc.custom_metadata[key] == expected_value]
        
        return filtered
    
    def _parse_date(self, date_input: Union[datetime, date, str]) -> Optional[datetime]:
        """Parse date from various formats"""
        
        if isinstance(date_input, datetime):
            return date_input
        
        if isinstance(date_input, date):
            return datetime.combine(date_input, datetime.min.time())
        
        if isinstance(date_input, str):
            for date_format in self.date_formats:
                try:
                    return datetime.strptime(date_input, date_format)
                except ValueError:
                    continue
        
        return None
    
    def create_filter_summary(self, filters: MetadataFilter) -> Dict[str, Any]:
        """Create human-readable summary of applied filters"""
        
        summary = {}
        
        if filters.trial_ids:
            summary["Trial IDs"] = filters.trial_ids
        
        if filters.trial_phases:
            summary["Trial Phases"] = [phase.value for phase in filters.trial_phases]
        
        if filters.date_from or filters.date_to:
            date_range = []
            if filters.date_from:
                date_range.append(f"from {filters.date_from}")
            if filters.date_to:
                date_range.append(f"to {filters.date_to}")
            summary["Date Range"] = " ".join(date_range)
        
        if filters.document_types:
            summary["Document Types"] = [dt.value for dt in filters.document_types]
        
        if filters.therapeutic_areas:
            summary["Therapeutic Areas"] = filters.therapeutic_areas
        
        if filters.evidence_levels:
            summary["Evidence Levels"] = filters.evidence_levels
        
        if filters.keywords_include:
            summary["Include Keywords"] = filters.keywords_include
        
        if filters.keywords_exclude:
            summary["Exclude Keywords"] = filters.keywords_exclude
        
        return summary

# Example filter configurations for common use cases
class CommonFilterPresets:
    """Pre-configured filter sets for common clinical scenarios"""
    
    @staticmethod
    def oncology_trials_phase_3() -> MetadataFilter:
        """Filter for Phase III oncology trials"""
        return MetadataFilter(
            trial_phases=[TrialPhase.PHASE_III],
            therapeutic_areas=["oncology", "cancer"],
            document_types=[DocumentType.CLINICAL_TRIAL, DocumentType.RESEARCH_PAPER],
            evidence_levels=["A", "B"]
        )
    
    @staticmethod
    def recent_cardiology_guidelines() -> MetadataFilter:
        """Filter for recent cardiology clinical guidelines"""
        return MetadataFilter(
            therapeutic_areas=["cardiology", "cardiovascular"],
            document_types=[DocumentType.CLINICAL_GUIDELINE, DocumentType.RESEARCH_PAPER],
            publication_year_from=2020,
            journal_tiers=["tier_1", "tier_2"]
        )
    
    @staticmethod
    def fda_approved_drugs() -> MetadataFilter:
        """Filter for FDA-approved drug information"""
        return MetadataFilter(
            regulatory_agencies=["FDA"],
            approval_statuses=["approved"],
            document_types=[DocumentType.DRUG_LABEL, DocumentType.REGULATORY_DOCUMENT]
        )
    
    @staticmethod
    def high_quality_rcts(therapeutic_area: str) -> MetadataFilter:
        """Filter for high-quality randomized controlled trials"""
        return MetadataFilter(
            therapeutic_areas=[therapeutic_area],
            study_types=["randomized controlled trial", "RCT"],
            evidence_levels=["A"],
            minimum_sample_size=100,
            journal_tiers=["tier_1"]
        )

# Global filter engine instance
metadata_filter_engine = MetadataFilterEngine()

# Export main components
__all__ = [
    'MetadataFilter',
    'DocumentMetadata', 
    'DocumentType',
    'TrialPhase',
    'MetadataFilterEngine',
    'CommonFilterPresets',
    'metadata_filter_engine'
]