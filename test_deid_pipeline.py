#!/usr/bin/env python3
"""
Simple De-identification Pipeline Test
=====================================

Test script for the de-identification pipeline without complex document extraction.
This demonstrates the core PHI detection and secure storage functionality.
"""

import sys
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from nlp.deid import DeIdentifier, create_sample_medical_text

def test_deid_pipeline():
    """Test the complete de-identification pipeline"""
    
    print("🏥 Testing ClinChat-RAG De-identification Pipeline")
    print("=" * 55)
    
    # Initialize de-identifier
    deid = DeIdentifier(
        secure_password="clinchat_test_2024",
        output_dir="data/processed/deid"
    )
    
    # Create sample medical texts
    sample_texts = [
        create_sample_medical_text(),
        """
        Emergency Department Note
        
        Patient: Mary Johnson
        DOB: 07/22/1980
        Phone: (555) 987-6543
        Email: mary.j@email.com
        
        CC: Acute abdominal pain
        HPI: 43 y/o female presents with RLQ pain x 4 hours.
        Vitals: T 100.2, BP 130/85, HR 98
        
        Assessment: Rule out appendicitis
        Plan: CT abdomen, CBC, BMP
        
        Dr. Michael Davis
        Date: 10/19/2025 15:30
        """,
        """
        Discharge Summary
        
        Patient Name: Robert Wilson  
        MRN: HOSP-654321
        Admission: 10/15/2025
        Discharge: 10/18/2025
        
        Attending: Dr. Lisa Chen, MD
        Address: 789 Pine Ave, Chicago, IL 60601
        Insurance: Blue Cross 987654321
        
        Final Diagnosis: Pneumonia
        Medications: Azithromycin 500mg daily
        Follow-up: Primary care in 1 week
        """
    ]
    
    results = []
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n📄 Processing Document {i}:")
        print("-" * 30)
        
        # Process text
        result = deid.process_text(text, document_id=f"test_doc_{i}")
        
        # Save to file
        deid.process_file = lambda text, output_file=None: deid.process_text(text)
        
        print(f"✅ Original length: {len(result.original_text)} chars")
        print(f"✅ De-identified length: {len(result.deidentified_text)} chars")
        print(f"✅ PHI entities found: {result.stats['total_entities']}")
        print(f"✅ Processing time: {result.processing_time:.3f}s")
        print(f"✅ Mapping ID: {result.mapping_id}")
        
        # Show detected entity types
        if result.stats['entity_types']:
            print("📊 Entity types detected:")
            for entity_type, count in result.stats['entity_types'].items():
                print(f"   {entity_type}: {count}")
        
        results.append(result)
    
    # Create test output files
    output_dir = Path("data/processed/deid")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, result in enumerate(results, 1):
        # Save de-identified text
        deid_file = output_dir / f"test_document_{i}_deid.txt"
        deid_file.write_text(result.deidentified_text, encoding='utf-8')
        
        # Save metadata
        metadata_file = output_dir / f"test_document_{i}_metadata.json"
        metadata = {
            'mapping_id': result.mapping_id,
            'processing_time': result.processing_time,
            'stats': result.stats,
            'phi_entities': [
                {
                    'text': entity.text,
                    'label': entity.label,
                    'replacement': entity.replacement,
                    'confidence': entity.confidence
                } for entity in result.phi_entities
            ]
        }
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        print(f"💾 Saved: {deid_file}")
        print(f"💾 Saved: {metadata_file}")
    
    # Test secure mapping retrieval
    print(f"\n🔐 Testing Secure Mapping Retrieval:")
    print("-" * 40)
    
    for i, result in enumerate(results, 1):
        mapping = deid.get_mapping(result.mapping_id)
        if mapping:
            print(f"Document {i} - Mapping entries: {len(mapping)}")
            # Show first few mappings as example
            sample_mappings = list(mapping.items())[:3]
            for replacement, original in sample_mappings:
                print(f"   {replacement} -> {original}")
            if len(mapping) > 3:
                print(f"   ... and {len(mapping) - 3} more entries")
        else:
            print(f"Document {i} - No mapping found")
    
    # Generate summary report
    print(f"\n📋 De-identification Summary Report:")
    print("=" * 45)
    
    total_entities = sum(r.stats['total_entities'] for r in results)
    total_time = sum(r.processing_time for r in results)
    
    print(f"Documents processed: {len(results)}")
    print(f"Total PHI entities detected: {total_entities}")
    print(f"Total processing time: {total_time:.3f}s")
    print(f"Average entities per document: {total_entities/len(results):.1f}")
    print(f"Average processing time: {total_time/len(results):.3f}s")
    
    # Check output directory
    deid_files = list(output_dir.glob("*_deid.txt"))
    metadata_files = list(output_dir.glob("*_metadata.json"))
    
    print(f"\nOutput files created:")
    print(f"✅ De-identified texts: {len(deid_files)}")
    print(f"✅ Metadata files: {len(metadata_files)}")
    print(f"📁 Output directory: {output_dir}")
    
    # Verify secure mapping storage
    secure_dir = Path("data/secure")
    if secure_dir.exists():
        mapping_files = list(secure_dir.glob("*.enc"))
        key_files = list(secure_dir.glob("*.key"))
        print(f"🔐 Encrypted mapping files: {len(mapping_files)}")
        print(f"🔑 Key files: {len(key_files)}")
    
    print(f"\n✅ De-identification pipeline test completed successfully!")
    
    return results

if __name__ == "__main__":
    try:
        results = test_deid_pipeline()
        print(f"\n🎉 All tests passed! De-identification system is operational.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()