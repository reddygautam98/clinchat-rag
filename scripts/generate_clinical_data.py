#!/usr/bin/env python3
"""
Clinical Dataset Generator
Generate large synthetic clinical datasets (5000 rows each) for ClinChat-RAG testing.
"""

import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, 'data', 'raw')

class ClinicalDataGenerator:
    def __init__(self):
        # Lab test configurations
        self.lab_tests = {
            'Hemoglobin': {'range': (8.0, 18.0), 'normal': (12.0, 15.0), 'unit': 'g/dL'},
            'White Blood Cell Count': {'range': (2.0, 15.0), 'normal': (4.5, 11.0), 'unit': '10^3/µL'},
            'Platelet Count': {'range': (50, 600), 'normal': (150, 450), 'unit': '10^3/µL'},
            'Creatinine': {'range': (0.3, 3.0), 'normal': (0.6, 1.2), 'unit': 'mg/dL'},
            'ALT': {'range': (5, 200), 'normal': (7, 56), 'unit': 'U/L'},
            'AST': {'range': (8, 180), 'normal': (10, 40), 'unit': 'U/L'},
            'Bilirubin Total': {'range': (0.1, 5.0), 'normal': (0.3, 1.2), 'unit': 'mg/dL'},
            'Alkaline Phosphatase': {'range': (30, 300), 'normal': (44, 147), 'unit': 'U/L'},
            'Glucose': {'range': (40, 400), 'normal': (70, 100), 'unit': 'mg/dL'},
            'BUN': {'range': (5, 80), 'normal': (8, 20), 'unit': 'mg/dL'},
            'Sodium': {'range': (125, 150), 'normal': (136, 145), 'unit': 'mmol/L'},
            'Potassium': {'range': (2.5, 6.0), 'normal': (3.5, 5.1), 'unit': 'mmol/L'},
            'Chloride': {'range': (90, 115), 'normal': (98, 107), 'unit': 'mmol/L'},
            'CO2': {'range': (15, 35), 'normal': (22, 29), 'unit': 'mmol/L'},
            'Albumin': {'range': (2.0, 5.5), 'normal': (3.5, 5.0), 'unit': 'g/dL'},
            'Protein Total': {'range': (4.0, 9.0), 'normal': (6.0, 8.3), 'unit': 'g/dL'},
        }
        
        # Adverse event terms (MedDRA-like)
        self.ae_terms = [
            'Headache', 'Nausea', 'Fatigue', 'Diarrhea', 'Vomiting', 'Dizziness',
            'Rash', 'Cough', 'Insomnia', 'Decreased Appetite', 'Constipation',
            'Abdominal Pain', 'Back Pain', 'Joint Pain', 'Muscle Pain', 'Fever',
            'Chills', 'Sweating', 'Dry Mouth', 'Blurred Vision', 'Tinnitus',
            'Shortness of Breath', 'Chest Pain', 'Palpitations', 'Hypertension',
            'Hypotension', 'Peripheral Edema', 'Weight Loss', 'Weight Gain',
            'Anxiety', 'Depression', 'Confusion', 'Memory Impairment',
            'Elevated ALT', 'Elevated AST', 'Elevated Creatinine', 'Anemia',
            'Thrombocytopenia', 'Neutropenia', 'Hyperglycemia', 'Hypoglycemia',
            'Dehydration', 'Electrolyte Imbalance', 'Injection Site Reaction',
            'Allergic Reaction', 'Skin Irritation', 'Pruritus', 'Urticaria',
            'Dyspepsia', 'Gastritis', 'Upper Respiratory Infection', 'UTI',
            'Syncope', 'Falls', 'Bruising', 'Petechiae', 'Epistaxis'
        ]
        
        # Severity grades (CTCAE)
        self.severities = [1, 1, 1, 2, 2, 3, 4, 5]  # Weighted toward lower grades
        
        # Relationship to drug
        self.relationships = [
            'Unrelated', 'Unlikely Related', 'Possibly Related', 
            'Probably Related', 'Definitely Related'
        ]
        
        # Outcomes
        self.outcomes = [
            'Resolved', 'Resolved with sequelae', 'Recovering', 
            'Not recovered', 'Fatal', 'Unknown'
        ]

    def generate_patient_id(self, index: int) -> str:
        """Generate synthetic patient ID."""
        return f"SYNTH{index:04d}"

    def generate_lab_value(self, test_name: str, abnormal_prob: float = 0.15) -> Dict[str, Any]:
        """Generate a realistic lab value with controlled abnormal probability."""
        test_config = self.lab_tests[test_name]
        
        if random.random() < abnormal_prob:
            # Generate abnormal value
            if random.random() < 0.5:
                # Low abnormal
                value = random.uniform(test_config['range'][0], test_config['normal'][0])
                flag = 'L'
            else:
                # High abnormal
                value = random.uniform(test_config['normal'][1], test_config['range'][1])
                flag = 'H'
        else:
            # Generate normal value
            value = random.uniform(test_config['normal'][0], test_config['normal'][1])
            flag = 'N'
        
        # Round based on typical precision
        if test_name in ['Platelet Count', 'White Blood Cell Count']:
            value = round(value, 1)
        elif test_name in ['ALT', 'AST', 'Alkaline Phosphatase', 'Glucose', 'BUN']:
            value = int(round(value))
        else:
            value = round(value, 2)
        
        return {
            'value': value,
            'flag': flag,
            'unit': test_config['unit'],
            'reference_range': f"{test_config['normal'][0]}-{test_config['normal'][1]}"
        }

    def generate_lab_data(self, num_rows: int = 5000) -> None:
        """Generate comprehensive lab chemistry dataset."""
        print(f"Generating {num_rows} rows of lab chemistry data...")
        
        filename = os.path.join(data_dir, 'lab_data_chemistry_panel_5k.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['patient_id', 'visit_date', 'test_name', 'test_value', 
                         'reference_range', 'units', 'abnormal_flag', 'lab_comments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Generate data for multiple patients over time
            num_patients = num_rows // len(self.lab_tests)  # ~312 patients
            base_date = datetime(2024, 1, 1)
            
            for patient_num in range(1, num_patients + 1):
                patient_id = self.generate_patient_id(patient_num)
                
                # Each patient has multiple visits (1-3 visits)
                num_visits = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
                
                for visit in range(num_visits):
                    # Generate visit date
                    days_offset = random.randint(0, 365) + (visit * random.randint(30, 90))
                    visit_date = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')
                    
                    # Generate all lab tests for this visit
                    for test_name in self.lab_tests.keys():
                        lab_result = self.generate_lab_value(test_name)
                        
                        # Generate appropriate comment
                        comments = self.generate_lab_comment(lab_result['flag'], test_name)
                        
                        writer.writerow({
                            'patient_id': patient_id,
                            'visit_date': visit_date,
                            'test_name': test_name,
                            'test_value': lab_result['value'],
                            'reference_range': lab_result['reference_range'],
                            'units': lab_result['unit'],
                            'abnormal_flag': lab_result['flag'],
                            'lab_comments': comments
                        })
        
        print(f"✅ Lab chemistry data saved to: {filename}")

    def generate_lab_comment(self, flag: str, test_name: str) -> str:
        """Generate appropriate lab comments based on results."""
        if flag == 'N':
            comments = ['Within normal limits', 'Normal range', '', 'No significant findings']
        elif flag == 'L':
            if test_name == 'Hemoglobin':
                comments = ['Mild anemia', 'Below normal range', 'Consider iron studies']
            elif test_name in ['ALT', 'AST']:
                comments = ['Below normal', 'Low normal']
            else:
                comments = ['Below normal range', 'Low', 'Consider clinical correlation']
        else:  # flag == 'H'
            if test_name in ['ALT', 'AST']:
                comments = ['Elevated liver enzyme', 'Above normal range', 'Monitor liver function']
            elif test_name == 'Creatinine':
                comments = ['Elevated', 'Possible kidney dysfunction', 'Recheck recommended']
            elif test_name == 'Glucose':
                comments = ['Elevated glucose', 'Hyperglycemia', 'Consider diabetes workup']
            else:
                comments = ['Above normal range', 'Elevated', 'Clinical correlation advised']
        
        return random.choice(comments)

    def generate_ae_data(self, num_rows: int = 5000) -> None:
        """Generate comprehensive adverse events dataset."""
        print(f"Generating {num_rows} rows of adverse events data...")
        
        filename = os.path.join(data_dir, 'ae_data_safety_database_5k.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['patient_id', 'ae_term', 'severity_grade', 'relationship_to_drug',
                         'start_date', 'end_date', 'serious_flag', 'outcome', 'action_taken',
                         'concomitant_meds', 'medical_history']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            base_date = datetime(2024, 1, 1)
            
            for row in range(num_rows):
                patient_id = self.generate_patient_id(random.randint(1, 1000))
                ae_term = random.choice(self.ae_terms)
                severity = random.choice(self.severities)
                relationship = random.choice(self.relationships)
                
                # Generate start date
                start_offset = random.randint(0, 365)
                start_date = (base_date + timedelta(days=start_offset)).strftime('%Y-%m-%d')
                
                # Generate end date (if resolved)
                outcome = self.generate_outcome(severity)
                if outcome in ['Resolved', 'Resolved with sequelae', 'Fatal']:
                    duration = self.generate_duration(ae_term, severity)
                    end_date = (base_date + timedelta(days=start_offset + duration)).strftime('%Y-%m-%d')
                else:
                    end_date = 'Ongoing' if outcome in ['Recovering', 'Not recovered'] else ''
                
                # Determine if serious
                serious_flag = 'Y' if severity >= 4 or outcome == 'Fatal' or ae_term in [
                    'Chest Pain', 'Shortness of Breath', 'Syncope', 'Elevated ALT', 'Elevated AST'
                ] else ('Y' if random.random() < 0.05 else 'N')
                
                # Generate additional fields
                action_taken = self.generate_action_taken(severity, relationship)
                concomitant_meds = self.generate_concomitant_meds()
                medical_history = self.generate_medical_history()
                
                writer.writerow({
                    'patient_id': patient_id,
                    'ae_term': ae_term,
                    'severity_grade': severity,
                    'relationship_to_drug': relationship,
                    'start_date': start_date,
                    'end_date': end_date,
                    'serious_flag': serious_flag,
                    'outcome': outcome,
                    'action_taken': action_taken,
                    'concomitant_meds': concomitant_meds,
                    'medical_history': medical_history
                })
        
        print(f"✅ Adverse events data saved to: {filename}")

    def generate_outcome(self, severity: int) -> str:
        """Generate outcome based on severity."""
        if severity == 5:
            return 'Fatal'
        elif severity == 4:
            return random.choices(['Resolved', 'Resolved with sequelae', 'Not recovered'],
                                weights=[0.3, 0.4, 0.3])[0]
        elif severity == 3:
            return random.choices(['Resolved', 'Resolved with sequelae', 'Recovering'],
                                weights=[0.6, 0.2, 0.2])[0]
        else:
            return random.choices(['Resolved', 'Recovering'], weights=[0.8, 0.2])[0]

    def generate_duration(self, ae_term: str, severity: int) -> int:
        """Generate realistic duration for AE resolution."""
        base_duration = {
            'Headache': 1, 'Nausea': 2, 'Fatigue': 7, 'Diarrhea': 3,
            'Rash': 10, 'Elevated ALT': 30, 'Elevated AST': 30
        }
        
        duration = base_duration.get(ae_term, 5)  # Default 5 days
        duration *= severity  # More severe = longer duration
        duration += random.randint(-2, 5)  # Add variability
        
        return max(1, duration)  # Minimum 1 day

    def generate_action_taken(self, severity: int, relationship: str) -> str:
        """Generate action taken based on severity and relationship."""
        actions = {
            1: ['None', 'Symptomatic treatment', 'Monitor'],
            2: ['Symptomatic treatment', 'Monitor', 'Dose modification'],
            3: ['Dose modification', 'Treatment interruption', 'Concomitant medication'],
            4: ['Treatment discontinuation', 'Hospitalization', 'Intensive treatment'],
            5: ['Treatment discontinuation', 'Intensive care', 'Emergency treatment']
        }
        
        if relationship in ['Probably Related', 'Definitely Related']:
            if severity >= 3:
                return random.choice(['Dose reduction', 'Treatment interruption', 'Drug discontinuation'])
        
        return random.choice(actions.get(severity, ['Monitor']))

    def generate_concomitant_meds(self) -> str:
        """Generate realistic concomitant medications."""
        meds = [
            'Acetaminophen', 'Ibuprofen', 'Aspirin', 'Metformin', 'Lisinopril',
            'Atorvastatin', 'Omeprazole', 'Levothyroxine', 'Amlodipine', 'Metoprolol',
            'Losartan', 'Simvastatin', 'Hydrochlorothiazide', 'Gabapentin',
            'Sertraline', 'Escitalopram', 'Montelukast', 'Fluticasone'
        ]
        
        if random.random() < 0.3:  # 30% chance of no concomitant meds
            return 'None'
        
        num_meds = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        selected_meds = random.sample(meds, num_meds)
        return ', '.join(selected_meds)

    def generate_medical_history(self) -> str:
        """Generate realistic medical history."""
        conditions = [
            'Hypertension', 'Diabetes mellitus', 'Hyperlipidemia', 'Osteoarthritis',
            'GERD', 'Anxiety', 'Depression', 'Asthma', 'Hypothyroidism',
            'Migraine', 'Fibromyalgia', 'Sleep apnea', 'Allergic rhinitis'
        ]
        
        if random.random() < 0.2:  # 20% chance of no significant history
            return 'No significant medical history'
        
        num_conditions = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        selected_conditions = random.sample(conditions, num_conditions)
        return ', '.join(selected_conditions)

def main():
    """Generate all clinical datasets."""
    print("🏥 Clinical Dataset Generator")
    print("=" * 50)
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    generator = ClinicalDataGenerator()
    
    # Generate lab data
    generator.generate_lab_data(5000)
    
    # Generate adverse events data
    generator.generate_ae_data(5000)
    
    print(f"\n✅ All datasets generated successfully!")
    print(f"📁 Location: {data_dir}")
    print(f"📊 Total rows: 10,000 (5,000 per dataset)")
    print(f"🎯 Ready for ClinChat-RAG testing and development!")

if __name__ == "__main__":
    main()