#!/usr/bin/env python3
"""
Enhanced Chunking Test with Medical Sections
===========================================

Test chunking with proper medical section headers for better metadata extraction.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from nlp.chunker import MedicalChunker, ChunkStorage

def create_structured_medical_document():
    """Create a well-structured medical document with clear sections"""
    return """
CHIEF COMPLAINT:
Patient presents with severe abdominal pain radiating to the back, nausea, and vomiting for the past 6 hours. Pain started suddenly while eating dinner and has progressively worsened.

HISTORY OF PRESENT ILLNESS:
This is a 45-year-old male with no significant past medical history who presents to the emergency department with acute onset of severe epigastric pain. The pain began approximately 6 hours ago while eating a large meal and has been constant since onset. Patient describes the pain as sharp, knife-like, and radiating straight through to his back. He rates the pain as 9 out of 10 in severity. The pain is associated with nausea and multiple episodes of bilious vomiting. Patient denies fever, chills, diarrhea, or changes in urination. He has not had similar episodes in the past.

PAST MEDICAL HISTORY:
1. No significant past medical history
2. No prior surgeries
3. No known chronic medical conditions
4. Last physical examination was 2 years ago and was reportedly normal

MEDICATIONS:
Patient reports taking no regular medications. Occasional ibuprofen for headaches, last taken 1 week ago. No prescription medications, herbal supplements, or over-the-counter medications taken regularly.

ALLERGIES:
No known drug allergies. No food allergies. No environmental allergies reported by patient or documented in previous medical records.

SOCIAL HISTORY:
Patient works as an accountant for a local firm. He is married with two teenage children. Social alcohol use, approximately 2-3 beers per week, usually on weekends. Denies tobacco use, never smoked cigarettes. Denies illicit drug use. Regular exercise consists of walking 3-4 times per week for 30 minutes. Diet consists of regular American diet without specific restrictions.

FAMILY HISTORY:
Father died at age 70 from complications of diabetes and heart disease. Mother is alive at age 68 with history of high blood pressure and arthritis. One brother, age 47, with no known medical problems. One sister, age 43, with history of gallbladder surgery at age 40. No family history of cancer, sudden death, or inherited disorders.

REVIEW OF SYSTEMS:
Constitutional: Denies fever, chills, night sweats, or unintentional weight loss
Cardiovascular: Denies chest pain, palpitations, shortness of breath, or leg swelling  
Respiratory: Denies cough, shortness of breath, or wheezing
Gastrointestinal: Positive for abdominal pain, nausea, and vomiting as described above. Denies diarrhea, constipation, blood in stool, or black tarry stools
Genitourinary: Denies painful urination, blood in urine, or changes in urinary frequency
Musculoskeletal: Denies joint pain, muscle weakness, or back pain (other than pain radiating from abdomen)
Neurological: Denies headache, dizziness, weakness, numbness, or tingling
Psychiatric: Denies depression, anxiety, or sleep problems

PHYSICAL EXAMINATION:
VITAL SIGNS:
Temperature: 100.2°F (37.9°C) - low grade fever
Blood Pressure: 145/92 mmHg - elevated, likely related to pain
Heart Rate: 110 beats per minute - tachycardic
Respiratory Rate: 20 breaths per minute - upper limit of normal
Oxygen Saturation: 98% on room air - normal
Weight: 185 lbs (84 kg)
Height: 5'10" (178 cm)

GENERAL APPEARANCE:
Patient appears uncomfortable and is lying still in bed. He is alert and oriented to person, place, and time. Appears to be in moderate to severe pain based on facial expressions and guarding behavior.

CARDIOVASCULAR:
Regular rate and rhythm, tachycardic. S1 and S2 heart sounds present. No murmurs, rubs, or gallops heard. No jugular venous distension. Peripheral pulses palpable and equal bilaterally.

PULMONARY:
Clear to auscultation bilaterally. No wheezes, rales, or rhonchi. Normal respiratory effort without use of accessory muscles.

ABDOMINAL:
Inspection reveals no obvious distension or visible masses. Auscultation demonstrates hypoactive bowel sounds in all four quadrants. Palpation reveals severe tenderness in the epigastric region with guarding and rigidity. No rebound tenderness elicited. No masses or organomegaly palpated. Murphy's sign negative. McBurney's point non-tender.

ASSESSMENT:
Based on the clinical presentation of sudden onset severe epigastric pain radiating to the back, associated with nausea and vomiting, along with physical examination findings, the most likely diagnosis is acute pancreatitis. Differential diagnosis includes peptic ulcer disease with possible perforation, biliary colic, and small bowel obstruction.

PLAN:
1. Laboratory studies including complete blood count, comprehensive metabolic panel, lipase, amylase, and liver function tests
2. CT scan of the abdomen and pelvis with IV contrast to evaluate for pancreatitis and rule out other causes
3. NPO status (nothing by mouth) until diagnosis confirmed
4. IV fluid resuscitation with normal saline
5. Pain management with IV morphine as needed
6. Anti-emetic medication for nausea and vomiting
7. Monitor vital signs and urine output closely
8. Gastroenterology consultation if pancreatitis confirmed
9. Surgical consultation if signs of complications develop
"""

def test_enhanced_chunking():
    """Test chunking with proper medical sections"""
    
    print("🏥 Enhanced Medical Chunking Test")
    print("=" * 40)
    
    # Create chunker with smaller chunks to demonstrate multiple chunks
    chunker = MedicalChunker(max_chars=600, min_chars=50)
    storage = ChunkStorage("data/processed/chunks")
    
    # Process the structured document
    document_text = create_structured_medical_document()
    doc_id = "structured_medical_note"
    
    print(f"📄 Processing structured medical document...")
    print(f"📊 Document length: {len(document_text)} characters")
    
    # Generate chunks
    chunks = chunker.chunk_text(document_text, doc_id, page=1)
    
    # Save chunks
    output_file = storage.save_chunks(chunks)
    
    print(f"✅ Created {len(chunks)} chunks")
    print(f"💾 Saved to: {output_file}")
    
    # Analyze results
    print(f"\n📈 Detailed Chunk Analysis:")
    print("-" * 35)
    
    sections_found = {}
    total_words = 0
    total_chars = 0
    
    for i, chunk in enumerate(chunks, 1):
        total_words += chunk.word_count
        total_chars += chunk.char_count
        
        if chunk.section:
            sections_found[chunk.section] = sections_found.get(chunk.section, 0) + 1
        
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Section: {chunk.section or 'Unknown'}")
        print(f"  Size: {chunk.char_count} chars, {chunk.word_count} words")
        print(f"  Position: {chunk.start_char}-{chunk.end_char}")
        
        # Show first line of content for identification
        first_line = chunk.text.split('\n')[0].strip()
        print(f"  Content: {first_line[:60]}{'...' if len(first_line) > 60 else ''}")
    
    # Section summary
    print(f"\n📋 Medical Sections Detected:")
    print("-" * 30)
    
    if sections_found:
        for section, count in sections_found.items():
            print(f"  • {section}: {count} chunk(s)")
    else:
        print("  No medical sections detected in chunks")
    
    # Statistics
    print(f"\n📊 Processing Statistics:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Total words: {total_words:,}")
    print(f"  Average chunk size: {total_chars // len(chunks)} chars")
    print(f"  Sections with headers: {len(sections_found)}")
    
    # Verify JSONL format
    print(f"\n🔍 JSONL File Verification:")
    print("-" * 25)
    
    # Read back the first few lines to verify format
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
    
    print(f"  Lines in JSONL file: {len(lines)}")
    print(f"  Matches chunk count: {len(lines) == len(chunks)}")
    
    # Show sample JSONL structure
    if lines:
        import json
        sample_data = json.loads(lines[0])
        print(f"  Sample JSONL keys: {list(sample_data.keys())}")
        print(f"  Metadata included: {'metadata' in sample_data}")
    
    print(f"\n✅ Enhanced chunking test completed successfully!")
    
    return chunks

if __name__ == "__main__":
    try:
        chunks = test_enhanced_chunking()
        print(f"\n🎉 Medical chunking system is fully operational!")
        print(f"📁 Chunks available in data/processed/chunks/ directory")
    except Exception as e:
        print(f"\n❌ Error in enhanced chunking test: {e}")
        import traceback
        traceback.print_exc()