#!/usr/bin/env python3
"""
Simple De-identification Test
"""

from nlp.deid import DeIdentifier, create_sample_medical_text
import json
from pathlib import Path

def test_deid():
    # Test the de-identification system
    print('🏥 Testing ClinChat-RAG De-identification System')
    print('=' * 50)

    # Initialize de-identifier  
    deid = DeIdentifier(
        secure_password='clinchat_test_2024',
        output_dir='data/processed/deid'
    )

    # Create test document
    test_text = create_sample_medical_text()
    print('📄 Sample medical document created')
    print(f'Original length: {len(test_text)} characters')

    # Process the document
    result = deid.process_text(test_text, document_id='test_sample')
    print(f'✅ Processing completed in {result.processing_time:.3f}s')
    
    total_entities = result.stats['total_entities']
    print(f'✅ PHI entities detected: {total_entities}')
    print(f'✅ Mapping ID: {result.mapping_id}')

    # Save results
    output_dir = Path('data/processed/deid')
    output_dir.mkdir(parents=True, exist_ok=True)

    deid_file = output_dir / 'sample_deid.txt'
    deid_file.write_text(result.deidentified_text, encoding='utf-8')

    metadata_file = output_dir / 'sample_metadata.json' 
    metadata = {
        'mapping_id': result.mapping_id,
        'processing_time': result.processing_time,
        'stats': result.stats
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    print(f'💾 Saved de-identified text: {deid_file}')
    print(f'💾 Saved metadata: {metadata_file}')

    # Test mapping retrieval
    mapping = deid.get_mapping(result.mapping_id)
    print(f'🔐 Retrieved mapping with {len(mapping)} entries')

    print()
    print('✅ De-identification system test completed successfully!')
    print('📁 Check data/processed/deid/ for output files')
    
    return result

if __name__ == "__main__":
    test_deid()