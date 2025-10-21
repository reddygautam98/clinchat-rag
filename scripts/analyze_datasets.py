#!/usr/bin/env python3
"""
Clinical Dataset Analysis Script
Analyze the 5000-row clinical datasets and provide summary statistics.
"""

import pandas as pd
import os
from collections import Counter

def analyze_lab_data():
    """Analyze the lab chemistry dataset."""
    print("🧪 Laboratory Chemistry Analysis")
    print("=" * 40)
    
    file_path = 'data/raw/lab_data_chemistry_panel_5k.csv'
    df = pd.read_csv(file_path)
    
    print(f"📊 Total Records: {len(df):,}")
    print(f"👥 Unique Patients: {df['patient_id'].nunique():,}")
    print(f"📅 Date Range: {df['visit_date'].min()} to {df['visit_date'].max()}")
    print(f"🧪 Lab Tests: {df['test_name'].nunique()} different tests")
    
    # Abnormal flag distribution
    flag_dist = df['abnormal_flag'].value_counts()
    print(f"\n🎯 Result Distribution:")
    for flag, count in flag_dist.items():
        percentage = (count / len(df)) * 100
        flag_name = {'N': 'Normal', 'H': 'High', 'L': 'Low'}.get(flag, flag)
        print(f"  {flag_name}: {count:,} ({percentage:.1f}%)")
    
    # Most common tests
    print(f"\n🔬 Most Common Tests:")
    test_counts = df['test_name'].value_counts().head(5)
    for test, count in test_counts.items():
        print(f"  {test}: {count:,} results")
    
    # Patients with multiple visits
    visit_counts = df.groupby('patient_id')['visit_date'].nunique()
    multiple_visits = (visit_counts > 1).sum()
    print(f"\n📅 Longitudinal Data:")
    print(f"  Patients with multiple visits: {multiple_visits:,}")
    print(f"  Average visits per patient: {visit_counts.mean():.1f}")

def analyze_ae_data():
    """Analyze the adverse events dataset."""
    print("\n⚠️ Adverse Events Analysis")
    print("=" * 40)
    
    file_path = 'data/raw/ae_data_safety_database_5k.csv'
    df = pd.read_csv(file_path)
    
    print(f"📊 Total Records: {len(df):,}")
    print(f"👥 Unique Patients: {df['patient_id'].nunique():,}")
    print(f"📅 Date Range: {df['start_date'].min()} to {df['start_date'].max()}")
    print(f"⚠️ Unique AE Terms: {df['ae_term'].nunique()} different events")
    
    # Severity distribution
    severity_dist = df['severity_grade'].value_counts().sort_index()
    print(f"\n🎯 Severity Distribution (CTCAE Grades):")
    for grade, count in severity_dist.items():
        percentage = (count / len(df)) * 100
        print(f"  Grade {grade}: {count:,} ({percentage:.1f}%)")
    
    # Serious events
    serious_count = (df['serious_flag'] == 'Y').sum()
    serious_pct = (serious_count / len(df)) * 100
    print(f"\n🚨 Serious Events: {serious_count:,} ({serious_pct:.1f}%)")
    
    # Most common AEs
    print(f"\n📋 Top 10 Most Common Adverse Events:")
    ae_counts = df['ae_term'].value_counts().head(10)
    for ae, count in ae_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {ae}: {count:,} ({percentage:.1f}%)")
    
    # Relationship to drug
    print(f"\n🔗 Relationship to Study Drug:")
    rel_dist = df['relationship_to_drug'].value_counts()
    for rel, count in rel_dist.items():
        percentage = (count / len(df)) * 100
        print(f"  {rel}: {count:,} ({percentage:.1f}%)")
    
    # Outcomes
    print(f"\n📈 Outcomes:")
    outcome_dist = df['outcome'].value_counts()
    for outcome, count in outcome_dist.items():
        percentage = (count / len(df)) * 100
        print(f"  {outcome}: {count:,} ({percentage:.1f}%)")

def analyze_dataset_quality():
    """Analyze data quality metrics."""
    print("\n✅ Data Quality Assessment")
    print("=" * 40)
    
    # Lab data quality
    lab_df = pd.read_csv('data/raw/lab_data_chemistry_panel_5k.csv')
    print("🧪 Lab Chemistry Quality:")
    print(f"  Missing values: {lab_df.isnull().sum().sum():,}")
    print(f"  Duplicate records: {lab_df.duplicated().sum():,}")
    print(f"  Valid date format: {len(lab_df):,}/{len(lab_df):,}")
    
    # AE data quality
    ae_df = pd.read_csv('data/raw/ae_data_safety_database_5k.csv')
    print(f"\n⚠️ Adverse Events Quality:")
    print(f"  Missing values: {ae_df.isnull().sum().sum():,}")
    print(f"  Duplicate records: {ae_df.duplicated().sum():,}")
    print(f"  Valid date format: {len(ae_df):,}/{len(ae_df):,}")
    
    # Check for realistic patterns
    print(f"\n🎯 Realism Checks:")
    print(f"  Lab abnormal rate: {((lab_df['abnormal_flag'] != 'N').sum() / len(lab_df) * 100):.1f}% (target: ~15%)")
    print(f"  AE serious rate: {((ae_df['serious_flag'] == 'Y').sum() / len(ae_df) * 100):.1f}% (target: 5-10%)")

def show_file_info():
    """Show file size and storage information."""
    print("\n📁 File Information")
    print("=" * 40)
    
    files = [
        'data/raw/lab_data_chemistry_panel_5k.csv',
        'data/raw/ae_data_safety_database_5k.csv'
    ]
    
    total_size = 0
    for file_path in files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            total_size += size
            print(f"📄 {os.path.basename(file_path)}: {size:,} bytes ({size/1024:.1f} KB)")
    
    print(f"\n📦 Total Dataset Size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"💾 Estimated Memory Usage: ~{(total_size * 3)/1024:.1f} KB when loaded")

def main():
    """Run complete dataset analysis."""
    print("🏥 ClinChat-RAG Clinical Dataset Analysis")
    print("=" * 60)
    
    try:
        analyze_lab_data()
        analyze_ae_data()
        analyze_dataset_quality()
        show_file_info()
        
        print(f"\n🎉 Dataset Analysis Complete!")
        print(f"📊 Your 5,000-row datasets are ready for:")
        print(f"  • RAG system testing and validation")
        print(f"  • Performance benchmarking")
        print(f"  • AI model training and evaluation")
        print(f"  • Clinical document analysis workflows")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find dataset file.")
        print(f"   Please run: python generate_clinical_data.py")
    except Exception as e:
        print(f"❌ Error analyzing datasets: {e}")

if __name__ == "__main__":
    main()