"""
Medical Text Normalization Module
Standardizes medical text for improved consistency and searchability
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalTextNormalizer:
    """
    Comprehensive text normalization for medical documents
    Handles dates, phone numbers, addresses, and medical terminology
    """
    
    def __init__(self):
        self.setup_medical_mappings()
        self.setup_regex_patterns()
    
    def setup_medical_mappings(self):
        """Setup medical terminology standardization mappings"""
        
        # Medical abbreviations to full terms
        self.medical_abbreviations = {
            # Vital signs
            'bp': 'blood pressure',
            'hr': 'heart rate',
            'rr': 'respiratory rate',
            'temp': 'temperature',
            'o2 sat': 'oxygen saturation',
            'spo2': 'oxygen saturation',
            
            # Medical conditions
            'mi': 'myocardial infarction',
            'cad': 'coronary artery disease',
            'chf': 'congestive heart failure',
            'copd': 'chronic obstructive pulmonary disease',
            'dm': 'diabetes mellitus',
            'htn': 'hypertension',
            'afib': 'atrial fibrillation',
            'dvt': 'deep vein thrombosis',
            'pe': 'pulmonary embolism',
            'uri': 'upper respiratory infection',
            'uti': 'urinary tract infection',
            
            # Procedures
            'ekg': 'electrocardiogram',
            'ecg': 'electrocardiogram',
            'cxr': 'chest x-ray',
            'ct': 'computed tomography',
            'mri': 'magnetic resonance imaging',
            'us': 'ultrasound',
            'echo': 'echocardiogram',
            
            # Medications
            'asa': 'aspirin',
            'ace': 'angiotensin converting enzyme',
            'arb': 'angiotensin receptor blocker',
            'nsaid': 'nonsteroidal anti-inflammatory drug',
            'ppi': 'proton pump inhibitor',
            'h2': 'histamine-2 receptor antagonist',
            
            # Departments
            'ed': 'emergency department',
            'er': 'emergency room',
            'icu': 'intensive care unit',
            'ccu': 'cardiac care unit',
            'or': 'operating room',
            'pacu': 'post-anesthesia care unit',
            
            # Common medical terms
            'sob': 'shortness of breath',
            'n/v': 'nausea and vomiting',
            'r/o': 'rule out',
            'w/u': 'workup',
            'f/u': 'follow up',
            'h/o': 'history of',
            's/p': 'status post',
            'w/o': 'without',
            'c/o': 'complains of',
            'p/w': 'presents with'
        }
        
        # Dosage units standardization
        self.dosage_units = {
            'mg': 'milligrams',
            'mcg': 'micrograms',
            'ug': 'micrograms',
            'g': 'grams',
            'kg': 'kilograms',
            'ml': 'milliliters',
            'l': 'liters',
            'cc': 'cubic centimeters',
            'u': 'units',
            'iu': 'international units',
            'meq': 'milliequivalents'
        }
        
        # Frequency standardization
        self.frequency_mappings = {
            'qd': 'once daily',
            'bid': 'twice daily',
            'tid': 'three times daily',
            'qid': 'four times daily',
            'q4h': 'every 4 hours',
            'q6h': 'every 6 hours',
            'q8h': 'every 8 hours',
            'q12h': 'every 12 hours',
            'prn': 'as needed',
            'ac': 'before meals',
            'pc': 'after meals',
            'hs': 'at bedtime',
            'qhs': 'every night at bedtime'
        }
    
    def setup_regex_patterns(self):
        """Setup regular expression patterns for various normalizations"""
        
        # Date patterns (various formats)
        self.date_patterns = [
            # MM/DD/YYYY, MM-DD-YYYY
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b',
            # DD/MM/YYYY, DD-MM-YYYY  
            r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b',
            # Month DD, YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',
            # Mon DD, YYYY (abbreviated)
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
            # YYYY-MM-DD (ISO format)
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'
        ]
        
        # Time patterns
        self.time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\b',
            r'\b(\d{1,2}):(\d{2}):(\d{2})\b',
            r'\b(\d{4})\s*hours?\b'
        ]
        
        # Phone number patterns
        self.phone_patterns = [
            r'\b(\d{3})[.\-\s]?(\d{3})[.\-\s]?(\d{4})\b',
            r'\((\d{3})\)\s*(\d{3})[.\-\s]?(\d{4})\b'
        ]
        
        # Address patterns
        self.address_patterns = [
            r'\b\d+\s+[A-Za-z0-9\s]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Place|Pl)\b',
            r'\b[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(-\d{4})?\b'  # City, State ZIP
        ]
        
        # Vital signs patterns
        self.vital_patterns = {
            'blood_pressure': r'\b(\d{2,3})/(\d{2,3})\s*mmHg?\b',
            'heart_rate': r'\b(\d{2,3})\s*bpm\b',
            'temperature': r'\btemp\s+(\d{2,3}(?:\.\d)?)\s*°?F?\b',
            'respiratory_rate': r'\bRR\s+(\d{1,2})\b',
            'oxygen_saturation': r'\bO2\s+sat\s+(\d{2,3})%\b'
        }
        
        # Medication patterns
        self.medication_patterns = [
            r'\b([A-Za-z]+)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?)\s+(qd|bid|tid|qid|prn)\b',
            r'\b([A-Za-z]+)\s+(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?)\b'
        ]
    
    def normalize_dates(self, text: str) -> str:
        """Normalize various date formats to a standard format"""
        normalized_text = text
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                original = match.group(0)
                try:
                    # Parse different date formats
                    if '/' in original or '-' in original:
                        # Handle MM/DD/YYYY or DD/MM/YYYY
                        parts = re.split(r'[\/\-]', original)
                        if len(parts) == 3:
                            month, day, year = parts
                            normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            normalized_text = normalized_text.replace(original, normalized_date)
                    elif any(month in original.lower() for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        # Handle month name formats
                        date_obj = datetime.strptime(original, '%B %d, %Y')
                        normalized_date = date_obj.strftime('%Y-%m-%d')
                        normalized_text = normalized_text.replace(original, normalized_date)
                except Exception:
                    # If parsing fails, keep original
                    continue
        
        return normalized_text
    
    def normalize_phone_numbers(self, text: str) -> str:
        """Normalize phone numbers to a standard format"""
        normalized_text = text
        
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                original = match.group(0)
                try:
                    # Extract digits only
                    digits = re.sub(r'\D', '', original)
                    if len(digits) == 10:
                        # Format as (XXX) XXX-XXXX
                        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                        normalized_text = normalized_text.replace(original, formatted)
                except Exception:
                    continue
        
        return normalized_text
    
    def normalize_addresses(self, text: str) -> str:
        """Standardize address formats"""
        normalized_text = text
        
        # Street abbreviations
        street_abbrev = {
            'Street': 'St',
            'Avenue': 'Ave',
            'Road': 'Rd',
            'Boulevard': 'Blvd',
            'Lane': 'Ln',
            'Drive': 'Dr',
            'Court': 'Ct',
            'Circle': 'Cir',
            'Place': 'Pl'
        }
        
        for full, abbrev in street_abbrev.items():
            normalized_text = re.sub(rf'\b{full}\b', abbrev, normalized_text, flags=re.IGNORECASE)
        
        return normalized_text
    
    def normalize_medical_terms(self, text: str) -> str:
        """Expand medical abbreviations and standardize terminology"""
        normalized_text = text.lower()
        
        # Expand medical abbreviations
        for abbrev, full_term in self.medical_abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(abbrev)}\b'
            normalized_text = re.sub(pattern, full_term, normalized_text, flags=re.IGNORECASE)
        
        # Normalize dosage units
        for unit, full_unit in self.dosage_units.items():
            pattern = rf'\b(\d+(?:\.\d+)?)\s*{re.escape(unit)}\b'
            replacement = rf'\1 {full_unit}'
            normalized_text = re.sub(pattern, replacement, normalized_text, flags=re.IGNORECASE)
        
        # Normalize frequency terms
        for freq, full_freq in self.frequency_mappings.items():
            pattern = rf'\b{re.escape(freq)}\b'
            normalized_text = re.sub(pattern, full_freq, normalized_text, flags=re.IGNORECASE)
        
        return normalized_text
    
    def normalize_vital_signs(self, text: str) -> str:
        """Standardize vital signs format"""
        normalized_text = text
        
        # Handle specific vital sign patterns in order
        # Blood pressure first
        bp_pattern = r'\bBP\s+(\d{2,3})/(\d{2,3})\b'
        normalized_text = re.sub(bp_pattern, r'blood pressure \1/\2 mmHg', normalized_text, flags=re.IGNORECASE)
        
        # Heart rate
        hr_pattern = r'\bHR\s+(\d{2,3})\s*bpm\b'
        normalized_text = re.sub(hr_pattern, r'heart rate \1 beats per minute', normalized_text, flags=re.IGNORECASE)
        
        # Temperature
        temp_pattern = r'\btemp\s+(\d{2,3}(?:\.\d)?)\s*°?F?\b'
        normalized_text = re.sub(temp_pattern, r'temperature \1°F', normalized_text, flags=re.IGNORECASE)
        
        # Respiratory rate
        rr_pattern = r'\bRR\s+(\d{1,2})\b'
        normalized_text = re.sub(rr_pattern, r'respiratory rate \1 breaths per minute', normalized_text, flags=re.IGNORECASE)
        
        # Oxygen saturation
        o2_pattern = r'\bO2\s+sat\s+(\d{2,3})%\b'
        normalized_text = re.sub(o2_pattern, r'oxygen saturation \1%', normalized_text, flags=re.IGNORECASE)
        
        return normalized_text
    
    def normalize_medications(self, text: str) -> str:
        """Standardize medication format"""
        normalized_text = text
        
        for pattern in self.medication_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                original = match.group(0)
                groups = match.groups()
                
                if len(groups) >= 3:
                    med_name = groups[0]
                    dose = groups[1]
                    unit = groups[2]
                    
                    # Expand unit
                    expanded_unit = self.dosage_units.get(unit.lower(), unit)
                    
                    standardized = f"{med_name} {dose} {expanded_unit}"
                    
                    # Add frequency if present
                    if len(groups) == 4:
                        freq = groups[3]
                        expanded_freq = self.frequency_mappings.get(freq.lower(), freq)
                        standardized += f" {expanded_freq}"
                    
                    normalized_text = normalized_text.replace(original, standardized)
        
        return normalized_text
    
    def normalize_text(self, text: str, 
                      normalize_dates: bool = True,
                      normalize_phones: bool = True, 
                      normalize_addresses: bool = True,
                      normalize_medical: bool = True,
                      normalize_vitals: bool = True,
                      normalize_meds: bool = True) -> Dict[str, Any]:
        """
        Comprehensive text normalization
        
        Args:
            text: Input text to normalize
            normalize_dates: Whether to normalize dates
            normalize_phones: Whether to normalize phone numbers
            normalize_addresses: Whether to normalize addresses  
            normalize_medical: Whether to normalize medical terms
            normalize_vitals: Whether to normalize vital signs
            normalize_meds: Whether to normalize medications
            
        Returns:
            Dictionary with original and normalized text
        """
        
        original_text = text
        normalized_text = text
        
        try:
            if normalize_dates:
                normalized_text = self.normalize_dates(normalized_text)
                logger.debug("Applied date normalization")
            
            if normalize_phones:
                normalized_text = self.normalize_phone_numbers(normalized_text)
                logger.debug("Applied phone number normalization")
            
            if normalize_addresses:
                normalized_text = self.normalize_addresses(normalized_text)
                logger.debug("Applied address normalization")
            
            if normalize_medical:
                normalized_text = self.normalize_medical_terms(normalized_text)
                logger.debug("Applied medical term normalization")
            
            if normalize_vitals:
                normalized_text = self.normalize_vital_signs(normalized_text)
                logger.debug("Applied vital signs normalization")
            
            if normalize_meds:
                normalized_text = self.normalize_medications(normalized_text)
                logger.debug("Applied medication normalization")
            
            # Count changes made
            changes_made = original_text != normalized_text
            
            return {
                'original': original_text,
                'normalized': normalized_text,
                'changes_made': changes_made,
                'length_original': len(original_text),
                'length_normalized': len(normalized_text)
            }
            
        except Exception as e:
            logger.error(f"Error during normalization: {e}")
            return {
                'original': original_text,
                'normalized': original_text,  # Return original on error
                'changes_made': False,
                'error': str(e)
            }
    
    def normalize_file(self, input_file: str, output_file: str | None = None) -> Dict[str, Any]:
        """
        Normalize text in a file
        
        Args:
            input_file: Path to input file
            output_file: Path to output file (if None, overwrites input)
            
        Returns:
            Dictionary with normalization results
        """
        
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            # Read input file
            with open(input_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            # Normalize text
            result = self.normalize_text(original_text)
            
            # Write output file
            output_path = Path(output_file) if output_file else input_path
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['normalized'])
            
            logger.info(f"Normalized text written to: {output_path}")
            
            result['input_file'] = str(input_path)
            result['output_file'] = str(output_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error normalizing file: {e}")
            return {'error': str(e)}

def main():
    """Demo of medical text normalization"""
    
    normalizer = MedicalTextNormalizer()
    
    # Sample medical text with various formats
    sample_text = """
    Patient John Smith, DOB 01/15/1980, phone (555) 123-4567
    Lives at 123 Main Street, Anytown, NY 12345
    
    Chief Complaint: pt c/o SOB and chest pain
    
    Vitals: BP 145/92, HR 98 bpm, temp 98.6F, RR 22, O2 sat 96%
    
    Assessment: r/o MI, h/o HTN and DM
    
    Plan: 
    - EKG and CXR
    - ASA 81mg qd
    - Lisinopril 10mg bid
    - f/u in ED if symptoms worsen
    
    Medications:
    - Metformin 500mg bid
    - Atenolol 25mg qd
    """
    
    print("🏥 Medical Text Normalization Demo")
    print("=" * 50)
    print("\nOriginal Text:")
    print(sample_text)
    
    # Normalize the text
    result = normalizer.normalize_text(sample_text)
    
    print("\nNormalized Text:")
    print(result['normalized'])
    
    print(f"\nChanges Made: {result['changes_made']}")
    print(f"Original Length: {result['length_original']}")
    print(f"Normalized Length: {result['length_normalized']}")

if __name__ == "__main__":
    main()