#!/usr/bin/env python3
"""
Simplified De-identification Module for ClinChat-RAG
==================================================

This module provides simplified PHI detection and secure storage functionality
without requiring complex ML dependencies.
"""

import re
import json
import time
import hashlib
import random
import string
from pathlib import Path
from typing import Dict, List, Tuple, Optional, NamedTuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# PHI Entity class
class PHIEntity(NamedTuple):
    text: str
    label: str
    start: int
    end: int
    replacement: str
    confidence: float = 1.0

# De-identification result class
class DeIDResult(NamedTuple):
    original_text: str
    deidentified_text: str
    phi_entities: List[PHIEntity]
    mapping_id: str
    processing_time: float
    stats: Dict

class SimplePHIDetector:
    """Simplified PHI detector using regex patterns"""
    
    def __init__(self):
        self.patterns = {
            'PERSON': [
                r'\b(?:Dr\.?|Doctor|Mr\.?|Mrs\.?|Ms\.?|Miss)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Names
            ],
            'DATE': [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            ],
            'PHONE': [
                r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
                r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
            ],
            'EMAIL': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'SSN': [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b',
            ],
            'MRN': [
                r'\bMRN:?\s*[A-Z0-9-]+',
                r'\b[A-Z]{2,4}-\d{5,8}\b',
            ],
            'ADDRESS': [
                r'\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Ct|Court)\b',
            ],
            'AGE': [
                r'\b\d{1,3}\s*(?:years?|yrs?|y/o|yo)\s*old\b',
                r'\b\d{1,3}\s*y/?o\b',
            ],
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for label, patterns in self.patterns.items():
            self.compiled_patterns[label] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def detect_phi(self, text: str) -> List[PHIEntity]:
        """Detect PHI entities in text using regex patterns"""
        entities = []
        
        for label, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    entity = PHIEntity(
                        text=match.group(),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        replacement=self._generate_replacement(label),
                        confidence=0.8  # Lower confidence for regex-based detection
                    )
                    entities.append(entity)
        
        # Sort by start position and remove overlaps
        entities.sort(key=lambda x: x.start)
        return self._remove_overlaps(entities)
    
    def _remove_overlaps(self, entities: List[PHIEntity]) -> List[PHIEntity]:
        """Remove overlapping entities, keeping the longest ones"""
        if not entities:
            return entities
        
        filtered = [entities[0]]
        for entity in entities[1:]:
            if entity.start >= filtered[-1].end:
                filtered.append(entity)
            elif len(entity.text) > len(filtered[-1].text):
                filtered[-1] = entity
        
        return filtered
    
    def _generate_replacement(self, label: str) -> str:
        """Generate appropriate replacement text for each PHI type"""
        replacements = {
            'PERSON': lambda: f"[PERSON_{random.randint(1000, 9999)}]",
            'DATE': lambda: f"[DATE_{random.randint(1000, 9999)}]",
            'PHONE': lambda: f"[PHONE_{random.randint(1000, 9999)}]",
            'EMAIL': lambda: f"[EMAIL_{random.randint(1000, 9999)}]",
            'SSN': lambda: f"[SSN_{random.randint(1000, 9999)}]",
            'MRN': lambda: f"[MRN_{random.randint(1000, 9999)}]",
            'ADDRESS': lambda: f"[ADDRESS_{random.randint(1000, 9999)}]",
            'AGE': lambda: f"[AGE_{random.randint(1000, 9999)}]",
        }
        
        return replacements.get(label, lambda: f"[{label}_{random.randint(1000, 9999)}]")()

class SecureMapping:
    """Secure encrypted storage for PHI mappings"""
    
    def __init__(self, password: str, secure_dir: str = "data/secure"):
        self.secure_dir = Path(secure_dir)
        self.secure_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate encryption key from password
        salt = b'clinchat_salt_2024'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
        
        self.mapping_file = self.secure_dir / "phi_mapping.enc"
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load encrypted mappings from file"""
        if not self.mapping_file.exists():
            return {}
        
        try:
            with open(self.mapping_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            print(f"Warning: Could not load existing mappings: {e}")
            return {}
    
    def _save_mappings(self):
        """Save encrypted mappings to file"""
        try:
            json_data = json.dumps(self.mappings, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
            
            with open(self.mapping_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restricted permissions (Windows)
            if os.name == 'nt':
                os.chmod(self.mapping_file, 0o600)
        except Exception as e:
            print(f"Error saving mappings: {e}")
    
    def store_mapping(self, mapping_id: str, phi_map: Dict[str, str]):
        """Store PHI mapping with encryption"""
        self.mappings[mapping_id] = phi_map
        self._save_mappings()
    
    def get_mapping(self, mapping_id: str) -> Optional[Dict[str, str]]:
        """Retrieve PHI mapping by ID"""
        return self.mappings.get(mapping_id)

class SimpleDeIdentifier:
    """Simplified de-identification system"""
    
    def __init__(self, secure_password: str, output_dir: str = "data/processed/deid"):
        self.phi_detector = SimplePHIDetector()
        self.secure_mapping = SecureMapping(secure_password)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_text(self, text: str, document_id: str = None) -> DeIDResult:
        """Process text and remove PHI"""
        start_time = time.time()
        
        # Generate document ID if not provided
        if document_id is None:
            document_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Detect PHI entities
        phi_entities = self.phi_detector.detect_phi(text)
        
        # Create de-identified text
        deidentified_text = text
        phi_mapping = {}
        
        # Replace PHI entities (in reverse order to maintain positions)
        for entity in reversed(phi_entities):
            deidentified_text = (
                deidentified_text[:entity.start] + 
                entity.replacement + 
                deidentified_text[entity.end:]
            )
            phi_mapping[entity.replacement] = entity.text
        
        # Generate mapping ID and store securely
        mapping_id = f"{document_id}_{int(time.time())}"
        if phi_mapping:
            self.secure_mapping.store_mapping(mapping_id, phi_mapping)
        
        # Calculate stats
        entity_types = {}
        for entity in phi_entities:
            entity_types[entity.label] = entity_types.get(entity.label, 0) + 1
        
        stats = {
            'total_entities': len(phi_entities),
            'entity_types': entity_types,
            'original_length': len(text),
            'deidentified_length': len(deidentified_text)
        }
        
        processing_time = time.time() - start_time
        
        return DeIDResult(
            original_text=text,
            deidentified_text=deidentified_text,
            phi_entities=phi_entities,
            mapping_id=mapping_id,
            processing_time=processing_time,
            stats=stats
        )
    
    def get_mapping(self, mapping_id: str) -> Optional[Dict[str, str]]:
        """Retrieve PHI mapping by ID"""
        return self.secure_mapping.get_mapping(mapping_id)

def create_sample_medical_text() -> str:
    """Create sample medical text for testing"""
    return """
    PATIENT MEDICAL RECORD
    ===================
    
    Patient Name: John Smith
    Date of Birth: 03/15/1975
    Medical Record Number: HOSP-123456
    Phone: (555) 123-4567
    Email: john.smith@email.com
    Address: 123 Main St, Springfield, IL 62701
    
    Date of Visit: 10/15/2025
    Attending Physician: Dr. Sarah Johnson
    
    CHIEF COMPLAINT:
    48 year old male presents with chest pain
    
    HISTORY OF PRESENT ILLNESS:
    Patient reports onset of chest pain 2 hours ago while at work.
    Pain is substernal, radiating to left arm. 
    
    VITAL SIGNS:
    BP: 140/90, HR: 88, Temp: 98.6°F, RR: 18
    
    ASSESSMENT AND PLAN:
    1. Chest pain - rule out MI
       - EKG, troponins, chest X-ray
       - Aspirin 325mg given
    
    2. Hypertension
       - Continue current medications
       - Follow up with PCP Dr. Michael Davis in 1 week
    
    MEDICATIONS:
    - Lisinopril 10mg daily
    - Metformin 500mg BID
    
    Patient SSN: 123-45-6789
    Insurance ID: BC987654321
    
    Next appointment: 10/22/2025 at 2:00 PM
    
    Electronically signed by:
    Dr. Sarah Johnson, MD
    Date: 10/15/2025 14:30:00
    """

# Aliases for backward compatibility
DeIdentifier = SimpleDeIdentifier
PHIDetector = SimplePHIDetector

if __name__ == "__main__":
    # Test the simplified de-identification system
    print("🏥 Testing Simplified De-identification System")
    print("=" * 50)
    
    # Create test instance
    deid = SimpleDeIdentifier("test_password_2024")
    
    # Process sample text
    sample_text = create_sample_medical_text()
    result = deid.process_text(sample_text, "test_sample")
    
    print(f"✅ Processing completed in {result.processing_time:.3f}s")
    print(f"✅ PHI entities detected: {result.stats['total_entities']}")
    print(f"✅ Entity types: {result.stats['entity_types']}")
    print(f"✅ Mapping ID: {result.mapping_id}")
    
    # Show some de-identified text
    preview_length = 300
    print(f"\n📄 De-identified text preview ({preview_length} chars):")
    print("-" * 50)
    print(result.deidentified_text[:preview_length] + "...")
    
    # Test mapping retrieval
    mapping = deid.get_mapping(result.mapping_id)
    print(f"\n🔐 Mapping entries: {len(mapping) if mapping else 0}")
    
    print("\n✅ Simplified de-identification test completed!")