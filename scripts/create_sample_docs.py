#!/usr/bin/env python3
"""
Create sample PDF documents for testing the extraction pipeline
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from pathlib import Path

def create_sample_protocol_pdf(output_path: str):
    """Create a sample clinical protocol PDF with text and tables"""
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Clinical Study Protocol", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Protocol information
    protocol_info = """
    <b>Protocol Number:</b> ClinChat-001<br/>
    <b>Study Title:</b> Efficacy and Safety of Novel Treatment in Patients with Chronic Condition<br/>
    <b>Principal Investigator:</b> Dr. Jane Smith, MD, PhD<br/>
    <b>Study Phase:</b> Phase II<br/>
    <b>Study Design:</b> Randomized, Double-blind, Placebo-controlled
    """
    
    story.append(Paragraph(protocol_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Objectives section
    objectives = Paragraph("Study Objectives", styles['Heading1'])
    story.append(objectives)
    story.append(Spacer(1, 12))
    
    objectives_text = """
    <b>Primary Objective:</b> To evaluate the efficacy of the investigational treatment 
    compared to placebo in reducing disease symptoms as measured by the Clinical 
    Assessment Scale (CAS) at 12 weeks.
    
    <b>Secondary Objectives:</b>
    • To assess the safety and tolerability of the investigational treatment
    • To evaluate quality of life improvements using standardized questionnaires
    • To analyze biomarker changes throughout the study period
    """
    
    story.append(Paragraph(objectives_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Patient demographics table
    demographics_title = Paragraph("Patient Demographics", styles['Heading1'])
    story.append(demographics_title)
    story.append(Spacer(1, 12))
    
    demographics_data = [
        ['Characteristic', 'Treatment Group', 'Placebo Group', 'Total'],
        ['Number of patients', '50', '50', '100'],
        ['Age (mean ± SD)', '45.2 ± 12.8', '46.1 ± 11.9', '45.7 ± 12.3'],
        ['Gender (Male/Female)', '25/25', '23/27', '48/52'],
        ['Weight (kg)', '72.5 ± 15.2', '71.8 ± 14.6', '72.2 ± 14.9'],
        ['Disease duration (years)', '3.2 ± 1.8', '3.0 ± 1.6', '3.1 ± 1.7']
    ]
    
    demographics_table = Table(demographics_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1*inch])
    demographics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(demographics_table)
    story.append(Spacer(1, 20))
    
    # Dosing schedule table
    dosing_title = Paragraph("Dosing Schedule", styles['Heading1'])
    story.append(dosing_title)
    story.append(Spacer(1, 12))
    
    dosing_data = [
        ['Visit', 'Day', 'Dose (mg)', 'Frequency', 'Route'],
        ['Screening', '-14 to -1', '0', 'N/A', 'N/A'],
        ['Baseline', '0', '10', 'Once daily', 'Oral'],
        ['Week 2', '14', '20', 'Once daily', 'Oral'],
        ['Week 4', '28', '30', 'Once daily', 'Oral'],
        ['Week 8', '56', '30', 'Once daily', 'Oral'],
        ['Week 12', '84', '30', 'Once daily', 'Oral'],
        ['Follow-up', '112', '0', 'N/A', 'N/A']
    ]
    
    dosing_table = Table(dosing_data, colWidths=[1.2*inch, 1*inch, 1*inch, 1.2*inch, 1*inch])
    dosing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(dosing_table)
    story.append(Spacer(1, 20))
    
    # Statistical analysis section
    stats_title = Paragraph("Statistical Analysis Plan", styles['Heading1'])
    story.append(stats_title)
    story.append(Spacer(1, 12))
    
    stats_text = """
    The primary efficacy endpoint will be analyzed using a mixed-effects model for 
    repeated measures (MMRM) with treatment group, visit, and treatment-by-visit 
    interaction as fixed effects, and patient as a random effect. The baseline 
    CAS score will be included as a covariate.
    
    Sample size calculation: With 50 patients per group, the study has 80% power 
    to detect a difference of 3.5 points on the CAS scale (standard deviation = 6.2) 
    using a two-sided t-test with α = 0.05.
    
    Safety analysis will be performed on all randomized patients who received at 
    least one dose of study medication. Adverse events will be summarized by system 
    organ class and preferred term.
    """
    
    story.append(Paragraph(stats_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Created sample protocol PDF: {output_path}")

def create_sample_text_pdf(output_path: str):
    """Create a simple text-heavy PDF"""
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Patient Case Report")
    
    # Content
    c.setFont("Helvetica", 12)
    y_pos = height - 100
    
    content = [
        "Patient ID: ClinChat-001-001",
        "Date of Birth: January 15, 1978",
        "Gender: Female",
        "Height: 165 cm",
        "Weight: 68 kg",
        "",
        "Chief Complaint:",
        "The patient presents with a 3-month history of progressive fatigue,",
        "joint pain, and occasional fever. Symptoms began gradually and have",
        "worsened over the past month, significantly impacting daily activities.",
        "",
        "Medical History:",
        "- Hypertension (diagnosed 2015, well-controlled with medication)",
        "- No known drug allergies", 
        "- Non-smoker, occasional social alcohol use",
        "",
        "Physical Examination:",
        "Vital Signs: BP 128/82 mmHg, HR 88 bpm, Temp 37.2°C",
        "General: Alert, oriented, appears mildly fatigued",
        "HEENT: Normal examination",
        "Cardiovascular: Regular rate and rhythm, no murmurs",
        "Pulmonary: Clear to auscultation bilaterally",
        "Abdomen: Soft, non-tender, no organomegaly",
        "Extremities: Mild joint swelling in hands and knees",
        "",
        "Assessment and Plan:",
        "Based on the clinical presentation and examination findings,",
        "the differential diagnosis includes autoimmune conditions.",
        "Recommended laboratory studies include complete blood count,",
        "comprehensive metabolic panel, inflammatory markers (ESR, CRP),",
        "and autoimmune markers (ANA, RF, anti-CCP).",
        "",
        "Follow-up appointment scheduled in 2 weeks to review results",
        "and adjust treatment plan accordingly."
    ]
    
    for line in content:
        c.drawString(50, y_pos, line)
        y_pos -= 20
        
        # Start new page if needed
        if y_pos < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_pos = height - 50
    
    c.save()
    print(f"✅ Created sample text PDF: {output_path}")

def main():
    """Create sample PDF files for testing"""
    
    # Ensure raw data directory exists
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎯 Creating sample PDF documents for testing...")
    
    # Create different types of PDFs
    try:
        create_sample_protocol_pdf(str(raw_dir / "protocol.pdf"))
    except Exception as e:
        print(f"❌ Error creating protocol PDF: {e}")
        print("Note: ReportLab library may not be installed")
    
    try:
        create_sample_text_pdf(str(raw_dir / "patient_report.pdf"))
    except Exception as e:
        print(f"❌ Error creating patient report PDF: {e}")
    
    # Create a simple text file that can be converted to PDF
    simple_text_content = """
Clinical Trial Data Summary

Study: ClinChat-RAG-001
Date: October 19, 2025

Enrollment Summary:
Total Enrolled: 150 patients
Completed: 142 patients  
Discontinued: 8 patients

Primary Endpoint Results:
Treatment Group: 65.2% response rate
Placebo Group: 32.1% response rate
P-value: < 0.001

Adverse Events:
Mild: 23 events
Moderate: 7 events
Severe: 2 events

Conclusion:
The investigational treatment demonstrated significant 
efficacy compared to placebo with an acceptable safety profile.
"""
    
    # Save as text file (can be used for testing if PDF creation fails)
    text_file = raw_dir / "clinical_summary.txt"
    with open(text_file, 'w') as f:
        f.write(simple_text_content)
    
    print(f"✅ Created sample text file: {text_file}")
    print(f"📁 Sample files saved to: {raw_dir}")
    print("\nReady for document processing pipeline testing!")

if __name__ == "__main__":
    main()