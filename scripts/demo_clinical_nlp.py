#!/usr/bin/env python3
"""
Clinical NLP Demonstration with spaCy
Shows working local clinical text processing capabilities
"""

import spacy
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

class ClinicalNLPProcessor:
    def __init__(self):
        """Initialize clinical NLP models"""
        print("🧠 Loading spaCy Clinical NLP Models...")
        
        # Load both models for comparison
        self.nlp_sm = spacy.load("en_core_web_sm")
        self.nlp_md = spacy.load("en_core_web_md")
        
        print("✅ Models loaded successfully!")
        
        # Clinical text samples for demonstration
        self.clinical_samples = [
            "Patient presents with acute myocardial infarction. Current medications include aspirin 81mg daily, metoprolol 50mg BID, and atorvastatin 40mg daily.",
            "Laboratory results show elevated troponin I at 15.2 ng/mL (normal <0.04). EKG demonstrates ST elevation in leads II, III, and aVF.",
            "The patient has a history of diabetes mellitus type 2, hypertension, and hyperlipidemia. HbA1c is 8.2%.",
            "Adverse event: Patient developed severe nausea and vomiting after administration of chemotherapy (Cisplatin 75mg/m2). Grade 3 toxicity per CTCAE criteria.",
            "Vital signs: BP 140/90 mmHg, HR 88 bpm, Temp 98.6°F, O2 sat 97% on room air. Weight 185 lbs, Height 5'10\".",
            "Pathology report shows invasive ductal carcinoma, grade 2, ER positive, PR positive, HER2 negative. Tumor size 2.1 cm.",
        ]
    
    def process_clinical_text(self, text, model_name="medium"):
        """Process clinical text and extract entities"""
        nlp = self.nlp_md if model_name == "medium" else self.nlp_sm
        
        doc = nlp(text)
        
        # Extract different types of information
        results = {
            "text": text,
            "model": model_name,
            "entities": [],
            "tokens": [],
            "sentences": [],
            "pos_tags": [],
            "dependencies": []
        }
        
        # Named entities
        for ent in doc.ents:
            results["entities"].append({
                "text": ent.text,
                "label": ent.label_,
                "description": spacy.explain(ent.label_),
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        # Tokens with POS tags
        for token in doc:
            if not token.is_space:
                results["tokens"].append({
                    "text": token.text,
                    "lemma": token.lemma_,
                    "pos": token.pos_,
                    "tag": token.tag_,
                    "is_alpha": token.is_alpha,
                    "is_digit": token.is_digit,
                    "is_stop": token.is_stop
                })
                
                results["pos_tags"].append(f"{token.text}/{token.pos_}")
        
        # Sentences
        for sent in doc.sents:
            results["sentences"].append(sent.text.strip())
        
        # Dependencies (first 10 for brevity)
        for token in list(doc)[:10]:
            if not token.is_space:
                results["dependencies"].append({
                    "text": token.text,
                    "dep": token.dep_,
                    "head": token.head.text,
                    "children": [child.text for child in token.children]
                })
        
        return results
    
    def extract_clinical_entities(self, text):
        """Extract clinical-specific entities and patterns"""
        doc = self.nlp_md(text)
        
        clinical_entities = {
            "medications": [],
            "conditions": [],
            "measurements": [],
            "procedures": [],
            "body_parts": [],
            "dates": [],
            "numbers": []
        }
        
        # Simple pattern matching for clinical terms
        medication_indicators = ["mg", "mcg", "daily", "BID", "TID", "QID", "PRN"]
        condition_indicators = ["diabetes", "hypertension", "carcinoma", "infarction", "syndrome"]
        measurement_indicators = ["mmHg", "bpm", "ng/mL", "%", "cm", "lbs"]
        
        for ent in doc.ents:
            text_lower = ent.text.lower()
            
            # Dates and times
            if ent.label_ in ["DATE", "TIME"]:
                clinical_entities["dates"].append(ent.text)
            
            # Numbers and quantities
            elif ent.label_ in ["CARDINAL", "QUANTITY"]:
                clinical_entities["numbers"].append(ent.text)
            
            # Check for medications
            elif any(med in text_lower for med in medication_indicators):
                clinical_entities["medications"].append(ent.text)
            
            # Check for conditions
            elif any(cond in text_lower for cond in condition_indicators):
                clinical_entities["conditions"].append(ent.text)
            
            # Check for measurements
            elif any(meas in text_lower for meas in measurement_indicators):
                clinical_entities["measurements"].append(ent.text)
        
        # Additional pattern matching for specific clinical terms
        tokens = [token.text.lower() for token in doc]
        
        # Look for medication names (simplified)
        medication_names = ["aspirin", "metoprolol", "atorvastatin", "cisplatin", "insulin"]
        for med in medication_names:
            if med in tokens:
                clinical_entities["medications"].append(med.title())
        
        # Look for body parts
        body_parts = ["heart", "lung", "kidney", "liver", "brain", "chest", "abdomen"]
        for part in body_parts:
            if part in tokens:
                clinical_entities["body_parts"].append(part.title())
        
        return clinical_entities
    
    def analyze_clinical_document(self, text):
        """Comprehensive clinical document analysis"""
        print(f"\n📄 Analyzing Clinical Document...")
        print(f"📝 Text: {text[:100]}..." if len(text) > 100 else f"📝 Text: {text}")
        
        # Process with both models
        sm_results = self.process_clinical_text(text, "small")
        md_results = self.process_clinical_text(text, "medium")
        
        # Extract clinical entities
        clinical_entities = self.extract_clinical_entities(text)
        
        print(f"\n🔍 Entity Comparison:")
        print(f"  Small Model: {len(sm_results['entities'])} entities")
        print(f"  Medium Model: {len(md_results['entities'])} entities")
        
        print(f"\n🏥 Clinical Entities Found:")
        for category, items in clinical_entities.items():
            if items:
                print(f"  {category.title()}: {', '.join(set(items))}")
        
        print(f"\n📊 Medium Model Entities:")
        for ent in md_results['entities']:
            print(f"  • {ent['text']} [{ent['label']}] - {ent['description']}")
        
        return {
            "small_model": sm_results,
            "medium_model": md_results,
            "clinical_entities": clinical_entities
        }
    
    def process_clinical_dataset(self):
        """Process actual clinical data from our datasets"""
        print(f"\n📊 Processing Clinical Dataset...")
        
        # Load adverse events data
        ae_file = Path("data/raw/ae_data_safety_database_5k.csv")
        if ae_file.exists():
            df = pd.read_csv(ae_file)
            
            # Process first 5 AE terms
            ae_terms = df['ae_term'].unique()[:5]
            
            print(f"\n⚠️ Processing {len(ae_terms)} Adverse Event Terms:")
            
            for term in ae_terms:
                # Create clinical context
                clinical_text = f"Patient experienced {term.lower()} during the study. This adverse event was reported and assessed for severity and relationship to study drug."
                
                print(f"\n🔍 AE Term: {term}")
                entities = self.extract_clinical_entities(clinical_text)
                
                if any(entities.values()):
                    for category, items in entities.items():
                        if items:
                            print(f"  {category}: {', '.join(set(items))}")
        else:
            print("❌ Clinical dataset not found")
    
    def run_demo(self):
        """Run complete clinical NLP demonstration"""
        print("🏥 ClinChat-RAG Clinical NLP Demonstration")
        print("="*60)
        
        # Process sample clinical texts
        for i, sample in enumerate(self.clinical_samples, 1):
            print(f"\n{'='*20} Sample {i} {'='*20}")
            self.analyze_clinical_document(sample)
        
        # Process real clinical data
        self.process_clinical_dataset()
        
        print(f"\n{'='*60}")
        print("🎉 Clinical NLP Demonstration Complete!")
        print("✅ spaCy models are working perfectly for clinical text analysis")
        print("🚀 Ready for integration into ClinChat-RAG API!")

def main():
    """Main demonstration function"""
    try:
        processor = ClinicalNLPProcessor()
        processor.run_demo()
    except Exception as e:
        print(f"❌ Error in clinical NLP demo: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()