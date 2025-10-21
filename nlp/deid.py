#!/usr/bin/env python3
"""
De-identification and Normalization Module
=========================================

This module provides comprehensive PHI (Protected Health Information) detection and 
de-identification for clinical documents using spaCy NER and custom pattern matching.

Features:
- Named Entity Recognition for medical PHI
- Pattern-based detection for IDs, phone numbers, emails
- Date normalization and anonymization
- Secure encrypted mapping storage for compliance
- HIPAA-compliant de-identification rules

Author: ClinChat-RAG Team
License: MIT
"""

import re
import spacy
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import random
import string
import phonenumbers
import dateparser
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PHIEntity:
    """Represents a detected PHI entity"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    replacement: str
    entity_type: str

@dataclass 
class DeIDResult:
    """Results from de-identification process"""
    original_text: str
    deidentified_text: str
    phi_entities: List[PHIEntity]
    mapping_id: str
    processing_time: float
    stats: Dict[str, int]

class SecureMapping:
    """Handles encrypted storage of PHI mappings for compliance"""
    
    def __init__(self, password: str = None, key_file: str = None):
        """Initialize secure mapping with encryption"""
        self.key_file = Path(key_file) if key_file else Path("data/secure/mapping.key")
        self.mapping_file = self.key_file.parent / "phi_mapping.enc"
        
        # Ensure secure directory exists
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate or load encryption key
        if password:
            self.key = self._derive_key_from_password(password)
        else:
            self.key = self._get_or_create_key()
            
        self.fernet = Fernet(self.key)
        
    def _derive_key_from_password(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = b'clinchat_phi_salt'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
        
    def _get_or_create_key(self) -> bytes:
        """Get existing key or create new one"""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Secure the key file permissions
            os.chmod(self.key_file, 0o600)
            return key
    
    def store_mapping(self, mapping_id: str, phi_mapping: Dict[str, str]) -> None:
        """Store PHI mapping securely"""
        # Load existing mappings
        all_mappings = self.load_all_mappings()
        
        # Add new mapping
        all_mappings[mapping_id] = {
            'timestamp': datetime.now().isoformat(),
            'mapping': phi_mapping
        }
        
        # Encrypt and save
        encrypted_data = self.fernet.encrypt(json.dumps(all_mappings).encode())
        self.mapping_file.write_bytes(encrypted_data)
        
        logger.info(f"🔐 Stored PHI mapping: {mapping_id}")
        
    def load_mapping(self, mapping_id: str) -> Optional[Dict[str, str]]:
        """Load specific PHI mapping"""
        all_mappings = self.load_all_mappings()
        return all_mappings.get(mapping_id, {}).get('mapping')
        
    def load_all_mappings(self) -> Dict[str, Any]:
        """Load all PHI mappings"""
        if not self.mapping_file.exists():
            return {}
            
        try:
            encrypted_data = self.mapping_file.read_bytes()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            return {}

class PHIDetector:
    """Advanced PHI detection using spaCy NER and custom patterns"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize PHI detector with spaCy model"""
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"✅ Loaded spaCy model: {model_name}")
        except OSError:
            logger.error(f"❌ Could not load spaCy model: {model_name}")
            raise
            
        # Medical and PHI patterns
        self.patterns = self._create_phi_patterns()
        
        # Replacement generators
        self.replacement_generators = self._create_replacement_generators()
        
    def _create_phi_patterns(self) -> Dict[str, re.Pattern]:
        """Create regex patterns for PHI detection"""
        patterns = {
            # Medical Record Numbers
            'mrn': re.compile(r'\b(?:MRN|Medical Record|Record Number|Chart)[:\s#]*([A-Z0-9-]{6,15})\b', re.IGNORECASE),
            
            # Social Security Numbers
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            
            # Phone Numbers (various formats)
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            
            # Email Addresses
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            
            # Addresses (basic pattern)
            'address': re.compile(r'\b\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl)\b', re.IGNORECASE),
            
            # ZIP Codes
            'zip': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            
            # Dates (various formats)
            'date': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE),
            
            # Credit Card Numbers
            'ccn': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            
            # Drug Enforcement Administration (DEA) Numbers
            'dea': re.compile(r'\b[A-Z]{2}\d{7}\b'),
            
            # National Provider Identifier (NPI)
            'npi': re.compile(r'\b\d{10}\b'),
            
            # Account Numbers
            'account': re.compile(r'\b(?:Account|Acct)[:\s#]*([A-Z0-9-]{8,20})\b', re.IGNORECASE),
            
            # License Plate Numbers
            'license_plate': re.compile(r'\b[A-Z0-9]{2,3}[-\s]?[A-Z0-9]{2,4}\b'),
            
            # URLs/Websites
            'url': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            
            # IP Addresses
            'ip': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        }
        
        return patterns
    
    def _create_replacement_generators(self) -> Dict[str, callable]:
        """Create replacement text generators"""
        return {
            'PERSON': lambda: f"[NAME_{random.randint(1000, 9999)}]",
            'ORG': lambda: f"[ORGANIZATION_{random.randint(100, 999)}]", 
            'GPE': lambda: f"[LOCATION_{random.randint(100, 999)}]",
            'DATE': lambda: f"[DATE_{random.randint(1, 12)}/{random.randint(1, 28)}/XXXX]",
            'TIME': lambda: f"[TIME_{random.randint(1, 12)}:XX]",
            'MONEY': lambda: f"[AMOUNT_XXX]",
            'QUANTITY': lambda: f"[QUANTITY_XXX]",
            'ORDINAL': lambda: f"[ORDINAL_XXX]",
            'CARDINAL': lambda: f"[NUMBER_XXX]",
            'mrn': lambda: f"[MRN_{random.randint(100000, 999999)}]",
            'ssn': lambda: f"[SSN_XXX-XX-{random.randint(1000, 9999)}]",
            'phone': lambda: f"[PHONE_XXX-XXX-{random.randint(1000, 9999)}]",
            'email': lambda: f"[EMAIL_{random.randint(100, 999)}@example.com]",
            'address': lambda: f"[ADDRESS_{random.randint(100, 999)} STREET NAME]",
            'zip': lambda: f"[ZIP_{random.randint(10000, 99999)}]",
            'date': lambda: f"[DATE_XX/XX/XXXX]",
            'ccn': lambda: f"[CCN_XXXX-XXXX-XXXX-{random.randint(1000, 9999)}]",
            'dea': lambda: f"[DEA_{random.choice('ABCDEFGH')}{random.choice('ABCDEFGH')}{random.randint(1000000, 9999999)}]",
            'npi': lambda: f"[NPI_{random.randint(1000000000, 9999999999)}]",
            'account': lambda: f"[ACCOUNT_{random.randint(10000000, 99999999)}]",
            'license_plate': lambda: f"[PLATE_{random.randint(100, 999)}-{random.randint(100, 999)}]",
            'url': lambda: f"[URL_https://example.com/{random.randint(100, 999)}]",
            'ip': lambda: f"[IP_{random.randint(1, 255)}.{random.randint(1, 255)}.XXX.XXX]"
        }
    
    def detect_phi(self, text: str) -> List[PHIEntity]:
        """Detect PHI entities in text"""
        entities = []
        
        # Process with spaCy NER
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'TIME', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
                replacement = self.replacement_generators.get(ent.label_, lambda: f"[{ent.label_}_XXX]")()
                
                entities.append(PHIEntity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.9,  # spaCy entities have high confidence
                    replacement=replacement,
                    entity_type='NER'
                ))
        
        # Pattern-based detection
        for pattern_name, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                # Check if already detected by NER (avoid duplicates)
                start, end = match.span()
                is_duplicate = any(
                    abs(ent.start - start) < 5 and abs(ent.end - end) < 5 
                    for ent in entities
                )
                
                if not is_duplicate:
                    replacement = self.replacement_generators.get(pattern_name, lambda: f"[{pattern_name.upper()}_XXX]")()
                    
                    entities.append(PHIEntity(
                        text=match.group(),
                        label=pattern_name.upper(),
                        start=start,
                        end=end,
                        confidence=0.8,  # Pattern matches have slightly lower confidence
                        replacement=replacement,
                        entity_type='PATTERN'
                    ))
        
        # Sort by position for proper replacement
        entities.sort(key=lambda x: x.start, reverse=True)
        
        return entities

class TextNormalizer:
    """Handles text normalization for dates, phone numbers, addresses"""
    
    def __init__(self):
        """Initialize text normalizer"""
        pass
    
    def normalize_dates(self, text: str) -> str:
        """Normalize various date formats"""
        # Common date patterns and their normalized replacements
        date_patterns = [
            (r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', r'[DATE_\1/\2/\3]'),
            (r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', r'[DATE_\2/\3/\1]'),
        ]
        
        normalized_text = text
        for pattern, replacement in date_patterns:
            normalized_text = re.sub(pattern, replacement, normalized_text)
            
        return normalized_text
    
    def normalize_phones(self, text: str) -> str:
        """Normalize phone number formats"""
        # Find and normalize phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        
        def phone_replacer(match):
            return f"[PHONE_XXX-XXX-{match.group(3)}]"
        
        return re.sub(phone_pattern, phone_replacer, text)
    
    def normalize_addresses(self, text: str) -> str:
        """Normalize address formats"""
        address_pattern = r'\b(\d+)\s+([A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl))\b'
        
        def address_replacer(match):
            return f"[ADDRESS_{match.group(1)} STREET NAME]"
        
        return re.sub(address_pattern, address_replacer, text, flags=re.IGNORECASE)

class DeIdentifier:
    """Main de-identification engine"""
    
    def __init__(self, 
                 model_name: str = "en_core_web_sm",
                 secure_password: str = None,
                 output_dir: str = "data/processed/deid"):
        """Initialize de-identification engine"""
        
        self.phi_detector = PHIDetector(model_name)
        self.text_normalizer = TextNormalizer()
        self.secure_mapping = SecureMapping(password=secure_password)
        self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🏥 De-identification engine initialized")
    
    def process_text(self, text: str, document_id: str = None) -> DeIDResult:
        """Process text and remove PHI"""
        start_time = datetime.now()
        
        # Generate document ID if not provided
        if not document_id:
            document_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Detect PHI entities
        phi_entities = self.phi_detector.detect_phi(text)
        
        # Create de-identified text
        deidentified_text = text
        phi_mapping = {}
        
        # Replace PHI entities (iterate in reverse order to maintain positions)
        for entity in phi_entities:
            # Store original -> replacement mapping
            phi_mapping[entity.replacement] = entity.text
            
            # Replace in text
            deidentified_text = (
                deidentified_text[:entity.start] + 
                entity.replacement + 
                deidentified_text[entity.end:]
            )
        
        # Apply text normalization
        deidentified_text = self.text_normalizer.normalize_dates(deidentified_text)
        deidentified_text = self.text_normalizer.normalize_phones(deidentified_text)
        deidentified_text = self.text_normalizer.normalize_addresses(deidentified_text)
        
        # Store secure mapping
        mapping_id = f"doc_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.secure_mapping.store_mapping(mapping_id, phi_mapping)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Generate statistics
        stats = {
            'total_entities': len(phi_entities),
            'entity_types': {},
            'confidence_avg': sum(e.confidence for e in phi_entities) / len(phi_entities) if phi_entities else 0
        }
        
        for entity in phi_entities:
            stats['entity_types'][entity.label] = stats['entity_types'].get(entity.label, 0) + 1
        
        result = DeIDResult(
            original_text=text,
            deidentified_text=deidentified_text,
            phi_entities=phi_entities,
            mapping_id=mapping_id,
            processing_time=processing_time,
            stats=stats
        )
        
        logger.info(f"📋 Processed document {document_id}: {len(phi_entities)} PHI entities detected")
        
        return result
    
    def process_file(self, input_file: str, output_file: str = None) -> DeIDResult:
        """Process file and save de-identified version"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Read input file
        text = input_path.read_text(encoding='utf-8')
        
        # Process text
        result = self.process_text(text, document_id=input_path.stem)
        
        # Determine output file path
        if not output_file:
            output_file = self.output_dir / f"{input_path.stem}_deid.txt"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save de-identified text
        output_path.write_text(result.deidentified_text, encoding='utf-8')
        
        # Save metadata
        metadata_file = output_path.with_suffix('.json')
        metadata = {
            'mapping_id': result.mapping_id,
            'processing_time': result.processing_time,
            'stats': result.stats,
            'entities': [asdict(entity) for entity in result.phi_entities],
            'timestamp': datetime.now().isoformat()
        }
        
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        logger.info(f"💾 Saved de-identified file: {output_path}")
        logger.info(f"📊 Saved metadata: {metadata_file}")
        
        return result
    
    def batch_process(self, input_dir: str, pattern: str = "*.txt") -> List[DeIDResult]:
        """Process multiple files in a directory"""
        input_path = Path(input_dir)
        results = []
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        files = list(input_path.glob(pattern))
        logger.info(f"🔄 Processing {len(files)} files from {input_dir}")
        
        for file_path in files:
            try:
                result = self.process_file(str(file_path))
                results.append(result)
                logger.info(f"✅ Processed: {file_path.name}")
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
        
        return results
    
    def get_mapping(self, mapping_id: str) -> Optional[Dict[str, str]]:
        """Retrieve PHI mapping for compliance review"""
        return self.secure_mapping.load_mapping(mapping_id)

def create_sample_medical_text() -> str:
    """Create sample medical text for testing"""
    return """
    MEDICAL RECORD
    
    Patient: John Smith
    MRN: MED-123456
    DOB: 03/15/1975
    SSN: 123-45-6789
    Phone: (555) 123-4567
    Email: john.smith@email.com
    Address: 123 Main Street, Anytown, NY 12345
    
    Date of Service: January 15, 2024
    Provider: Dr. Sarah Johnson, MD
    Facility: Regional Medical Center
    
    CHIEF COMPLAINT:
    The patient presents with chest pain and shortness of breath.
    
    HISTORY OF PRESENT ILLNESS:
    Mr. Smith is a 48-year-old male who developed acute onset chest pain 
    approximately 2 hours prior to presentation. Pain is described as 
    crushing, substernal, radiating to left arm. Associated symptoms 
    include diaphoresis and nausea.
    
    PAST MEDICAL HISTORY:
    - Hypertension diagnosed 2018
    - Hyperlipidemia
    - Family history of coronary artery disease
    
    MEDICATIONS:
    - Lisinopril 10mg daily
    - Atorvastatin 40mg daily
    
    PHYSICAL EXAMINATION:
    Vitals: BP 150/90, HR 95, RR 20, Temp 98.6°F
    General: Anxious appearing male in mild distress
    
    ASSESSMENT AND PLAN:
    Acute coronary syndrome cannot be ruled out. Will obtain EKG, 
    cardiac enzymes, and chest X-ray. Consider cardiology consultation.
    
    Dr. Sarah Johnson, MD
    License: MD123456
    DEA: BJ1234567
    NPI: 1234567890
    """

# Example usage and testing
if __name__ == "__main__":
    # Initialize de-identifier
    deid = DeIdentifier(secure_password="clinchat_secure_2024")
    
    # Create sample text
    sample_text = create_sample_medical_text()
    
    print("🏥 ClinChat-RAG De-identification System")
    print("=" * 50)
    
    # Process sample text
    result = deid.process_text(sample_text, "sample_001")
    
    print(f"Original text length: {len(result.original_text)} characters")
    print(f"De-identified length: {len(result.deidentified_text)} characters")
    print(f"PHI entities detected: {result.stats['total_entities']}")
    print(f"Processing time: {result.processing_time:.3f} seconds")
    print(f"Mapping ID: {result.mapping_id}")
    
    print("\n📊 Entity Types Found:")
    for entity_type, count in result.stats['entity_types'].items():
        print(f"  {entity_type}: {count}")
    
    print(f"\n🔒 De-identified Text Preview:")
    print("-" * 50)
    print(result.deidentified_text[:500] + "...")
    
    print(f"\n🔑 Sample PHI Mapping (first 3 entries):")
    print("-" * 50)
    mapping = deid.get_mapping(result.mapping_id)
    if mapping:
        for i, (replacement, original) in enumerate(list(mapping.items())[:3]):
            print(f"  {replacement} -> {original}")
        if len(mapping) > 3:
            print(f"  ... and {len(mapping) - 3} more entries")