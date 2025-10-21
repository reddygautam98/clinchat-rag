#!/usr/bin/env python3
"""
Comprehensive Chunking Demo for ClinChat-RAG
===========================================

Demonstrates chunking with multiple medical documents and metadata preservation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from nlp.chunker import MedicalChunker, ChunkStorage, process_document

def create_comprehensive_medical_document():
    """Create a longer medical document to test chunking"""
    return """
    COMPREHENSIVE MEDICAL RECORD
    ===========================
    
    Patient Name: [PATIENT_001] 
    Medical Record Number: [MRN_7654]
    Date of Service: [DATE_2023]
    
    CHIEF COMPLAINT:
    72 year old female presents with progressive shortness of breath and chest pain 
    over the past 3 weeks. Patient reports difficulty climbing stairs and performing
    daily activities. Pain is described as sharp, intermittent, and located in the
    left chest area.
    
    HISTORY OF PRESENT ILLNESS:
    The patient is a 72-year-old female with a past medical history significant for 
    hypertension, diabetes mellitus type 2, and coronary artery disease who presents
    with a 3-week history of progressive dyspnea on exertion and intermittent chest pain.
    
    The dyspnea initially occurred only with significant exertion such as climbing
    two flights of stairs, but has progressed to occurring with minimal exertion
    such as walking across the room. The patient denies orthopnea or paroxysmal
    nocturnal dyspnea but reports increased fatigue and decreased exercise tolerance.
    
    The chest pain is described as sharp, non-radiating, and located in the left
    anterior chest. It occurs intermittently throughout the day and is not clearly
    related to exertion. The pain is rated 4-6/10 in intensity and is not relieved
    by rest or nitroglycerin. The patient denies palpitations, syncope, or presyncope.
    
    PAST MEDICAL HISTORY:
    1. Hypertension - diagnosed 2015, well controlled on ACE inhibitor
    2. Type 2 Diabetes Mellitus - diagnosed 2018, controlled with metformin
    3. Coronary Artery Disease - diagnosed 2020 after abnormal stress test
       - Cardiac catheterization showed 70% LAD stenosis
       - Treated with drug-eluting stent placement
    4. Hyperlipidemia - managed with statin therapy
    5. Osteoarthritis - bilateral knees, managed conservatively
    6. History of breast cancer - diagnosed 2010, treated with lumpectomy and radiation
       - Currently in remission, last oncology visit 6 months ago
    
    MEDICATIONS:
    1. Lisinopril 10mg daily - for hypertension
    2. Metformin 1000mg twice daily - for diabetes
    3. Atorvastatin 40mg at bedtime - for hyperlipidemia  
    4. Aspirin 81mg daily - for cardioprotection
    5. Clopidogrel 75mg daily - antiplatelet therapy
    6. Metoprolol 50mg twice daily - for rate control and cardioprotection
    7. Acetaminophen 650mg as needed for arthritis pain
    8. Calcium carbonate 500mg twice daily with meals
    9. Vitamin D3 2000 IU daily
    
    ALLERGIES:
    - Penicillin: rash and hives (documented 1995)
    - Sulfa drugs: gastrointestinal upset
    - No known food allergies
    
    SOCIAL HISTORY:
    The patient is a retired school teacher who lives alone in a two-story home.
    She has two adult children who live nearby and provide support. She quit smoking
    15 years ago after a 20 pack-year history. She denies current alcohol use but
    reports occasional wine with dinner (1-2 glasses per week). She denies illicit
    drug use. Her diet consists mainly of home-cooked meals with attention to 
    diabetic restrictions.
    
    FAMILY HISTORY:
    - Father: died at age 78 from myocardial infarction
    - Mother: died at age 85 from stroke, had history of hypertension
    - Sister: alive, age 70, history of breast cancer
    - Brother: alive, age 68, history of diabetes and hypertension
    - No family history of sudden cardiac death or inherited cardiac conditions
    
    REVIEW OF SYSTEMS:
    Constitutional: Denies fever, chills, night sweats, or unintentional weight loss
    Cardiovascular: Positive for dyspnea and chest pain as described above
    Respiratory: Denies cough, wheezing, or hemoptysis
    Gastrointestinal: Denies nausea, vomiting, abdominal pain, or changes in bowel habits
    Genitourinary: Denies dysuria, frequency, or hematuria
    Musculoskeletal: Reports chronic knee pain consistent with known osteoarthritis
    Neurological: Denies headache, dizziness, weakness, or numbness
    Psychiatric: Denies depression, anxiety, or sleep disturbances
    
    PHYSICAL EXAMINATION:
    VITAL SIGNS:
    - Blood Pressure: 142/88 mmHg (elevated)
    - Heart Rate: 88 beats per minute, regular
    - Respiratory Rate: 22 breaths per minute (mildly elevated)
    - Temperature: 98.2°F (36.8°C)
    - Oxygen Saturation: 94% on room air (decreased)
    - Weight: 165 lbs (75 kg)
    - Height: 5'4" (163 cm)
    - BMI: 28.3 kg/m² (overweight)
    
    GENERAL APPEARANCE:
    Alert, cooperative, well-appearing female in no acute distress. Appears stated age.
    Mild dyspnea noted when speaking in full sentences.
    
    CARDIOVASCULAR:
    Regular rate and rhythm. S1 and S2 present. No murmurs, rubs, or gallops appreciated.
    Point of maximal impulse not displaced. No jugular venous distension at 45 degrees.
    No peripheral edema noted in bilateral lower extremities.
    
    PULMONARY:
    Inspection reveals mild increased work of breathing. Bilateral breath sounds present
    with fine crackles noted at bilateral lung bases. No wheezes or rhonchi appreciated.
    No use of accessory muscles of respiration.
    
    LABORATORY RESULTS:
    Complete Blood Count:
    - White Blood Cells: 7.2 K/μL (normal)
    - Hemoglobin: 11.8 g/dL (low normal)
    - Hematocrit: 35.2% (low normal)
    - Platelets: 285 K/μL (normal)
    
    Comprehensive Metabolic Panel:
    - Sodium: 138 mEq/L (normal)
    - Potassium: 4.1 mEq/L (normal)
    - Chloride: 102 mEq/L (normal)
    - CO2: 24 mEq/L (normal)
    - Blood Urea Nitrogen: 22 mg/dL (slightly elevated)
    - Creatinine: 1.1 mg/dL (normal)
    - Glucose: 145 mg/dL (elevated)
    - eGFR: >60 mL/min/1.73m² (normal)
    
    Cardiac Biomarkers:
    - Troponin I: 0.02 ng/mL (normal, < 0.04)
    - BNP: 850 pg/mL (significantly elevated, normal < 100)
    - CK-MB: 2.1 ng/mL (normal)
    
    IMAGING STUDIES:
    Chest X-Ray:
    - Mild cardiomegaly noted
    - Bilateral lower lobe infiltrates consistent with pulmonary edema
    - No pneumothorax or pleural effusions
    - Stable appearance compared to prior study from 6 months ago
    
    Echocardiogram:
    - Left ventricular ejection fraction: 35% (reduced)
    - Moderate left ventricular systolic dysfunction
    - Mild mitral regurgitation
    - Normal right heart function
    - No pericardial effusion
    
    ASSESSMENT AND PLAN:
    
    1. HEART FAILURE WITH REDUCED EJECTION FRACTION (HFrEF)
       - New diagnosis based on symptoms, elevated BNP, and reduced LVEF on echo
       - Likely related to progression of coronary artery disease
       - Initiate guideline-directed medical therapy:
         * Continue current ACE inhibitor (Lisinopril)
         * Add loop diuretic: Furosemide 40mg daily
         * Consider beta-blocker optimization
       - Dietary sodium restriction (<2g daily)
       - Daily weights monitoring
       - Follow-up in cardiology clinic within 2 weeks
    
    2. CORONARY ARTERY DISEASE
       - Stable, continue current antiplatelet therapy
       - Continue statin for secondary prevention
       - Consider repeat cardiac catheterization given new heart failure
       - Optimize medical management
    
    3. DIABETES MELLITUS TYPE 2
       - Glucose slightly elevated, likely related to stress
       - Continue current metformin regimen
       - Monitor glucose closely with medication changes
       - Diabetes education reinforcement
    
    4. HYPERTENSION
       - Currently elevated, may be related to heart failure
       - Continue current ACE inhibitor
       - Monitor closely with diuretic initiation
       - Target BP <130/80 mmHg per guidelines
    
    DISCHARGE PLANNING:
    - Patient education regarding heart failure symptoms
    - Instructions for daily weight monitoring
    - Dietary consultation for sodium restriction
    - Home health services for medication management
    - Cardiology follow-up scheduled for [DATE_FOLLOWUP]
    - Primary care follow-up in 1 week
    
    PROGNOSIS:
    The patient has newly diagnosed heart failure with reduced ejection fraction.
    With appropriate medical management and lifestyle modifications, the prognosis
    can be improved. Patient will require close monitoring and medication optimization.
    """

def run_chunking_demo():
    """Demonstrate comprehensive chunking with multiple documents"""
    
    print("🔧 ClinChat-RAG Comprehensive Chunking Demo")
    print("=" * 50)
    
    # Create test documents
    documents = {
        "comprehensive_record": create_comprehensive_medical_document(),
        "emergency_note": """
        EMERGENCY DEPARTMENT NOTE
        ========================
        
        CHIEF COMPLAINT:
        Acute chest pain with radiation to left arm
        
        HISTORY OF PRESENT ILLNESS:
        65 year old male presents with sudden onset severe chest pain while mowing lawn.
        Pain described as crushing, 9/10 severity, associated with diaphoresis and nausea.
        
        ASSESSMENT:
        Acute ST-elevation myocardial infarction
        
        PLAN:
        Emergent cardiac catheterization
        """,
        "discharge_summary": """
        DISCHARGE SUMMARY
        =================
        
        HOSPITAL COURSE:
        Patient admitted for management of acute coronary syndrome.
        Underwent successful percutaneous coronary intervention.
        
        DISCHARGE MEDICATIONS:
        - Aspirin 81mg daily
        - Clopidogrel 75mg daily
        - Metoprolol 50mg BID
        
        FOLLOW-UP:
        Cardiology clinic in 1 week
        """
    }
    
    # Initialize chunker with different settings
    chunker = MedicalChunker(max_chars=800, min_chars=100)  # Smaller chunks for demo
    storage = ChunkStorage("data/processed/chunks")
    
    all_results = {}
    
    # Process each document
    for doc_id, content in documents.items():
        print(f"\n📄 Processing: {doc_id}")
        print("-" * 40)
        
        # Generate chunks
        chunks = chunker.chunk_text(content, doc_id)
        all_results[doc_id] = chunks
        
        # Save to JSONL
        output_file = storage.save_chunks(chunks)
        
        print(f"✅ Created {len(chunks)} chunks")
        print(f"💾 Saved to: {output_file}")
        
        # Show chunk details
        total_chars = sum(c.char_count for c in chunks)
        sections_found = set(c.section for c in chunks if c.section)
        
        print(f"📊 Total characters: {total_chars}")
        print(f"📋 Sections detected: {len(sections_found)}")
        if sections_found:
            print(f"   Sections: {', '.join(sections_found)}")
    
    # Generate summary report
    print(f"\n📈 CHUNKING SUMMARY REPORT")
    print("=" * 40)
    
    total_chunks = sum(len(chunks) for chunks in all_results.values())
    total_chars = sum(
        sum(c.char_count for c in chunks) 
        for chunks in all_results.values()
    )
    
    print(f"Documents processed: {len(all_results)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Total characters processed: {total_chars:,}")
    print(f"Average chunk size: {total_chars // total_chunks if total_chunks > 0 else 0} chars")
    
    # Section analysis
    all_sections = set()
    for chunks in all_results.values():
        for chunk in chunks:
            if chunk.section:
                all_sections.add(chunk.section)
    
    print(f"Medical sections detected: {len(all_sections)}")
    if all_sections:
        print("Sections found:")
        for section in sorted(all_sections):
            print(f"   • {section}")
    
    # Show sample chunks
    print(f"\n📄 Sample Chunk Details:")
    print("-" * 30)
    
    sample_chunks = []
    for doc_id, chunks in all_results.items():
        if chunks:
            sample_chunks.append((doc_id, chunks[0]))
    
    for doc_id, chunk in sample_chunks[:3]:  # Show first 3
        print(f"\nDocument: {doc_id}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Section: {chunk.section or 'Unknown'}")
        print(f"Size: {chunk.char_count} chars, {chunk.word_count} words")
        print(f"Position: {chunk.start_char}-{chunk.end_char}")
        preview = chunk.text[:150].replace('\n', ' ')
        print(f"Preview: {preview}{'...' if len(chunk.text) > 150 else ''}")
    
    # Verify JSONL files
    print(f"\n📁 Generated Files:")
    print("-" * 20)
    
    chunks_dir = Path("data/processed/chunks")
    jsonl_files = list(chunks_dir.glob("*.jsonl"))
    
    for file_path in jsonl_files:
        size_kb = file_path.stat().st_size / 1024
        print(f"📄 {file_path.name} ({size_kb:.1f} KB)")
    
    print(f"\n✅ Chunking demo completed successfully!")
    print(f"📁 All chunks saved to: {chunks_dir}")
    
    return all_results

if __name__ == "__main__":
    try:
        results = run_chunking_demo()
        print(f"\n🏆 ClinChat-RAG Chunking System: OPERATIONAL")
    except Exception as e:
        print(f"\n❌ Error in chunking demo: {e}")
        import traceback
        traceback.print_exc()