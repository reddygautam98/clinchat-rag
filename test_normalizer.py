"""
Test script for Medical Text Normalizer
Validates normalization functionality across all medical text types
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from nlp.normalizer import MedicalTextNormalizer

def test_medical_normalizer():
    """Test all normalization functions"""
    
    print("🧪 Testing Medical Text Normalizer")
    print("=" * 50)
    
    normalizer = MedicalTextNormalizer()
    
    # Test 1: Medical abbreviations
    test_text_1 = "pt c/o SOB and chest pain, h/o MI and HTN, r/o PE"
    print("\n🔬 Test 1: Medical Abbreviations")
    print(f"Input:  {test_text_1}")
    result_1 = normalizer.normalize_text(test_text_1)
    print(f"Output: {result_1['normalized']}")
    print(f"Changes: {result_1['changes_made']}")
    
    # Test 2: Vital signs
    test_text_2 = "BP 145/92, HR 98 bpm, temp 98.6F, RR 22, O2 sat 96%"
    print("\n🔬 Test 2: Vital Signs")
    print(f"Input:  {test_text_2}")
    result_2 = normalizer.normalize_text(test_text_2)
    print(f"Output: {result_2['normalized']}")
    print(f"Changes: {result_2['changes_made']}")
    
    # Test 3: Medications
    test_text_3 = "ASA 81mg qd, Lisinopril 10mg bid, Metformin 500mg tid"
    print("\n🔬 Test 3: Medications")
    print(f"Input:  {test_text_3}")
    result_3 = normalizer.normalize_text(test_text_3)
    print(f"Output: {result_3['normalized']}")
    print(f"Changes: {result_3['changes_made']}")
    
    # Test 4: Dates and phone numbers
    test_text_4 = "DOB 01/15/1980, phone (555) 123-4567, follow up on 12/25/2023"
    print("\n🔬 Test 4: Dates and Phone Numbers")
    print(f"Input:  {test_text_4}")
    result_4 = normalizer.normalize_text(test_text_4)
    print(f"Output: {result_4['normalized']}")
    print(f"Changes: {result_4['changes_made']}")
    
    # Test 5: Addresses
    test_text_5 = "Lives at 123 Main Street, Anytown, NY 12345"
    print("\n🔬 Test 5: Address Normalization")
    print(f"Input:  {test_text_5}")
    result_5 = normalizer.normalize_text(test_text_5)
    print(f"Output: {result_5['normalized']}")
    print(f"Changes: {result_5['changes_made']}")
    
    # Test 6: Comprehensive medical text
    comprehensive_text = """
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
    """
    
    print("\n🔬 Test 6: Comprehensive Medical Text")
    print("Input:")
    print(comprehensive_text)
    result_6 = normalizer.normalize_text(comprehensive_text)
    print("\nNormalized Output:")
    print(result_6['normalized'])
    print(f"\nChanges Made: {result_6['changes_made']}")
    print(f"Original Length: {result_6['length_original']}")
    print(f"Normalized Length: {result_6['length_normalized']}")
    
    # Test 7: Error handling
    print("\n🔬 Test 7: Error Handling")
    try:
        result_7 = normalizer.normalize_text("")
        print("Empty string handled successfully")
        print(f"Result: {result_7}")
    except Exception as e:
        print(f"Error with empty string: {e}")
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    test_medical_normalizer()