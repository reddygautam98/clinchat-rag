#!/usr/bin/env python3
"""
Adverse Events Dataset Demo
Demonstrate powerful queries and analysis on the 5000-row AE dataset.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def load_ae_data():
    """Load the adverse events dataset."""
    file_path = 'data/raw/ae_data_safety_database_5k.csv'
    df = pd.read_csv(file_path)
    
    # Convert dates
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    
    # Calculate duration for resolved events
    resolved_mask = df['end_date'].notna()
    df.loc[resolved_mask, 'duration_days'] = (df.loc[resolved_mask, 'end_date'] - 
                                              df.loc[resolved_mask, 'start_date']).dt.days
    
    return df

def demo_safety_queries(df):
    """Demonstrate key safety analysis queries."""
    print("🔍 Clinical Safety Analysis Demonstrations")
    print("=" * 60)
    
    # Query 1: Serious Drug-Related Events
    print("\n1️⃣ SERIOUS DRUG-RELATED ADVERSE EVENTS")
    print("-" * 40)
    serious_related = df[
        (df['serious_flag'] == 'Y') & 
        (df['relationship_to_drug'].isin(['Probably Related', 'Definitely Related']))
    ]
    
    top_serious = serious_related['ae_term'].value_counts().head(10)
    print("Top 10 Serious Drug-Related Events:")
    for ae, count in top_serious.items():
        percentage = (count / len(serious_related)) * 100
        print(f"  • {ae}: {count} events ({percentage:.1f}%)")
    
    # Query 2: Fatal Events Analysis
    print("\n2️⃣ FATAL ADVERSE EVENTS ANALYSIS")
    print("-" * 40)
    fatal_events = df[df['outcome'] == 'Fatal']
    print(f"Total Fatal Events: {len(fatal_events)} ({len(fatal_events)/len(df)*100:.1f}%)")
    
    fatal_by_relationship = fatal_events['relationship_to_drug'].value_counts()
    print("\nFatal Events by Drug Relationship:")
    for rel, count in fatal_by_relationship.items():
        percentage = (count / len(fatal_events)) * 100
        print(f"  • {rel}: {count} events ({percentage:.1f}%)")
    
    # Query 3: Grade 4+ Events (Life-threatening)
    print("\n3️⃣ LIFE-THREATENING EVENTS (Grade 4+)")
    print("-" * 40)
    severe_events = df[df['severity_grade'] >= 4]
    print(f"Total Grade 4+ Events: {len(severe_events)} ({len(severe_events)/len(df)*100:.1f}%)")
    
    severe_by_action = severe_events['action_taken'].value_counts().head(5)
    print("\nMost Common Actions for Grade 4+ Events:")
    for action, count in severe_by_action.items():
        print(f"  • {action}: {count} events")

def demo_drug_interaction_analysis(df):
    """Analyze potential drug-drug interactions."""
    print("\n💊 DRUG-DRUG INTERACTION ANALYSIS")
    print("=" * 60)
    
    # Find patients on multiple medications with drug-related AEs
    multi_med_patients = df[
        (df['concomitant_meds'] != 'None') & 
        (df['concomitant_meds'].str.contains(',')) &
        (df['relationship_to_drug'].isin(['Possibly Related', 'Probably Related', 'Definitely Related']))
    ]
    
    print(f"Patients with multiple medications and drug-related AEs: {len(multi_med_patients)}")
    
    # Analyze common medication combinations with AEs
    print("\n🔍 High-Risk Medication Combinations:")
    
    # Extract individual medications
    all_meds = []
    for meds in multi_med_patients['concomitant_meds']:
        if pd.notna(meds) and meds != 'None':
            med_list = [med.strip() for med in meds.split(',')]
            all_meds.extend(med_list)
    
    med_counts = Counter(all_meds).most_common(10)
    for med, count in med_counts:
        ae_with_med = df[df['concomitant_meds'].str.contains(med, na=False)]
        avg_severity = ae_with_med['severity_grade'].mean()
        print(f"  • {med}: {count} AE cases, avg severity {avg_severity:.1f}")

def demo_temporal_analysis(df):
    """Analyze temporal patterns in adverse events."""
    print("\n📅 TEMPORAL PATTERN ANALYSIS")
    print("=" * 60)
    
    # Monthly AE frequency
    df['month'] = df['start_date'].dt.to_period('M')
    monthly_counts = df['month'].value_counts().sort_index()
    
    print("Monthly Adverse Event Frequency:")
    for month, count in monthly_counts.items():
        print(f"  • {month}: {count} events")
    
    # Seasonal patterns
    df['season'] = df['start_date'].dt.month.map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Fall', 10: 'Fall', 11: 'Fall'
    })
    
    seasonal_severity = df.groupby('season')['severity_grade'].mean().sort_values(ascending=False)
    print(f"\nAverage Severity by Season:")
    for season, severity in seasonal_severity.items():
        print(f"  • {season}: {severity:.2f}")

def demo_resolution_analysis(df):
    """Analyze resolution patterns and duration."""
    print("\n⏱️ RESOLUTION PATTERN ANALYSIS")
    print("=" * 60)
    
    # Resolution by severity
    resolution_by_severity = df.groupby('severity_grade')['outcome'].value_counts()
    
    print("Resolution Patterns by Severity Grade:")
    for grade in sorted(df['severity_grade'].unique()):
        print(f"\nGrade {grade}:")
        grade_outcomes = resolution_by_severity[grade]
        total_grade = df[df['severity_grade'] == grade].shape[0]
        
        for outcome, count in grade_outcomes.items():
            percentage = (count / total_grade) * 100
            print(f"  • {outcome}: {count} ({percentage:.1f}%)")
    
    # Duration analysis for resolved events
    resolved_events = df[df['duration_days'].notna()]
    if len(resolved_events) > 0:
        print(f"\nResolution Duration Statistics:")
        print(f"  • Median duration: {resolved_events['duration_days'].median():.1f} days")
        print(f"  • Average duration: {resolved_events['duration_days'].mean():.1f} days")
        print(f"  • Quick resolution (<7 days): {(resolved_events['duration_days'] < 7).sum()} events")
        print(f"  • Prolonged (>30 days): {(resolved_events['duration_days'] > 30).sum()} events")

def demo_risk_factor_analysis(df):
    """Analyze risk factors from medical history."""
    print("\n🏥 MEDICAL HISTORY RISK FACTOR ANALYSIS")
    print("=" * 60)
    
    # Find patients with specific conditions
    conditions = ['Diabetes mellitus', 'Hypertension', 'GERD', 'Asthma', 'Depression']
    
    for condition in conditions:
        condition_patients = df[df['medical_history'].str.contains(condition, na=False)]
        
        if len(condition_patients) > 0:
            avg_severity = condition_patients['severity_grade'].mean()
            serious_rate = (condition_patients['serious_flag'] == 'Y').mean() * 100
            
            print(f"\n{condition} Patients:")
            print(f"  • Total AE events: {len(condition_patients)}")
            print(f"  • Average severity: {avg_severity:.2f}")
            print(f"  • Serious event rate: {serious_rate:.1f}%")
            
            # Most common AEs in this population
            top_aes = condition_patients['ae_term'].value_counts().head(3)
            print(f"  • Top AEs: {', '.join(top_aes.index.tolist())}")

def demo_regulatory_reporting(df):
    """Generate regulatory reporting summaries."""
    print("\n📋 REGULATORY REPORTING SUMMARY")
    print("=" * 60)
    
    # Expedited reporting criteria (Serious + Drug-related)
    expedited = df[
        (df['serious_flag'] == 'Y') & 
        (df['relationship_to_drug'].isin(['Possibly Related', 'Probably Related', 'Definitely Related']))
    ]
    
    print(f"Expedited Reporting Cases: {len(expedited)}")
    print(f"Percentage of total AEs: {len(expedited)/len(df)*100:.1f}%")
    
    # Fatal cases requiring immediate reporting
    fatal_drug_related = df[
        (df['outcome'] == 'Fatal') & 
        (df['relationship_to_drug'].isin(['Possibly Related', 'Probably Related', 'Definitely Related']))
    ]
    
    print(f"\nImmediate Fatal Reports Required: {len(fatal_drug_related)}")
    
    if len(fatal_drug_related) > 0:
        print("Fatal Drug-Related Events:")
        for _, event in fatal_drug_related.head(5).iterrows():
            print(f"  • {event['ae_term']} (Grade {event['severity_grade']}, {event['relationship_to_drug']})")

def demo_rag_queries(df):
    """Demonstrate RAG-style natural language queries."""
    print("\n🤖 RAG QUERY DEMONSTRATIONS")
    print("=" * 60)
    
    queries_and_results = [
        {
            "query": "Show me liver-related adverse events",
            "filter": df['ae_term'].str.contains('ALT|AST|liver|hepat', case=False, na=False),
            "description": "Hepatic adverse events"
        },
        {
            "query": "What are the most serious cardiovascular events?", 
            "filter": (df['ae_term'].str.contains('Chest Pain|Palpitations|Hypertension|Hypotension', case=False, na=False)) & 
                     (df['severity_grade'] >= 3),
            "description": "Grade 3+ cardiovascular events"
        },
        {
            "query": "Find adverse events that led to treatment discontinuation",
            "filter": df['action_taken'].str.contains('discontinuation|discontinuation', case=False, na=False),
            "description": "Events causing treatment discontinuation"
        },
        {
            "query": "Show patterns in injection site reactions",
            "filter": df['ae_term'].str.contains('Injection Site', case=False, na=False),
            "description": "Injection site adverse events"
        }
    ]
    
    for i, query_info in enumerate(queries_and_results, 1):
        print(f"\n{i}️⃣ Query: '{query_info['query']}'")
        print(f"   Results: {query_info['description']}")
        
        filtered_data = df[query_info['filter']]
        if len(filtered_data) > 0:
            print(f"   Found: {len(filtered_data)} events")
            print(f"   Avg Severity: {filtered_data['severity_grade'].mean():.1f}")
            print(f"   Serious Rate: {(filtered_data['serious_flag'] == 'Y').mean()*100:.1f}%")
            
            top_terms = filtered_data['ae_term'].value_counts().head(3)
            print(f"   Top Terms: {', '.join(top_terms.index.tolist())}")
        else:
            print("   No matching events found")

def main():
    """Run the complete adverse events demonstration."""
    print("🏥 ClinChat-RAG Adverse Events Dataset Demo")
    print("=" * 60)
    print("Demonstrating powerful clinical safety analysis on 5,000 AE records")
    
    try:
        # Load data
        df = load_ae_data()
        print(f"✅ Loaded {len(df):,} adverse events from {df['patient_id'].nunique():,} patients")
        
        # Run demonstrations
        demo_safety_queries(df)
        demo_drug_interaction_analysis(df)
        demo_temporal_analysis(df)
        demo_resolution_analysis(df)  
        demo_risk_factor_analysis(df)
        demo_regulatory_reporting(df)
        demo_rag_queries(df)
        
        print(f"\n🎉 Demonstration Complete!")
        print(f"Your 5,000-row AE dataset enables sophisticated clinical safety analysis")
        print(f"Perfect for training and testing your Fusion AI RAG system! 🚀")
        
    except FileNotFoundError:
        print("❌ Error: Adverse events dataset not found.")
        print("   Please run: python generate_clinical_data.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()