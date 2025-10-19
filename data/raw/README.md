# Sample Clinical Dataset Documentation

## Overview

This directory contains comprehensive sample clinical datasets for testing and development of the ClinChat-RAG system. These files represent the types of documents commonly found in clinical trials and pharmaceutical research, now expanded to **5,000 rows each** for realistic performance testing.

## Dataset Summary

- **📊 Total Records**: 10,000+ clinical data points
- **🧪 Lab Chemistry**: 5,000 rows across 16 different lab tests
- **⚠️ Adverse Events**: 5,000 rows with comprehensive safety data
- **👥 Patients**: 1,000+ synthetic patient records
- **📅 Time Span**: 12 months of clinical data (2024)

## Document Types & Use Cases

### 1. Clinical Trial Protocol (PDF)
**File Pattern**: `protocol_*.pdf`
**Purpose**: Clinical trial protocol documents define the objectives, design, methodology, statistical considerations, and organization of a trial.

**Sample File**: `protocol_phase_ii_oncology_sample.pdf`
**Content Includes**:
- Study objectives and endpoints
- Patient inclusion/exclusion criteria
- Treatment schedules and dosing
- Safety monitoring procedures
- Statistical analysis plans
- Regulatory compliance requirements

**Use Cases for RAG**:
- Query inclusion/exclusion criteria
- Lookup dosing schedules
- Find safety monitoring requirements
- Extract endpoint definitions

### 2. Clinical Study Report (CSR) PDF
**File Pattern**: `csr_*.pdf`
**Purpose**: Comprehensive report of clinical trial results submitted to regulatory authorities.

**Sample File**: `csr_cardiovascular_study_sample.pdf`
**Content Includes**:
- Study summary and conclusions
- Patient demographics and baseline characteristics
- Efficacy results and statistical analysis
- Safety data and adverse events
- Protocol deviations
- Regulatory compliance documentation

**Use Cases for RAG**:
- Query efficacy outcomes
- Lookup safety data
- Find statistical significance
- Extract patient demographics

### 3. Laboratory Data (CSV) - **5,000 Records**
**File Pattern**: `lab_data_*.csv`
**Purpose**: Structured laboratory test results from clinical trials.

**Sample Files**: 
- `lab_data_chemistry_panel_5k.csv` - **5,000 rows** (primary dataset)
- `lab_data_chemistry_panel.csv` - 30 rows (small sample)

**Comprehensive Lab Panel (16 Tests)**:
- **Hematology**: Hemoglobin, WBC Count, Platelet Count
- **Chemistry**: Creatinine, ALT, AST, Bilirubin, Alkaline Phosphatase
- **Metabolic**: Glucose, BUN, Sodium, Potassium, Chloride, CO2
- **Protein**: Albumin, Total Protein

**Data Features**:
- **312+ patients** with 1-3 visits each
- **Realistic abnormal values** (~15% abnormality rate)
- **Clinical comments** based on result interpretation
- **Reference ranges** for all tests
- **Temporal patterns** across multiple visits

**Use Cases for RAG**:
- Query specific lab values and trends
- Identify abnormal results and patterns
- Track patient lab evolution over time
- Compare against reference ranges
- Detect potential drug-lab interactions
- Generate safety reports and summaries

### 4. Adverse Events Data (CSV) - **5,000 Records**
**File Pattern**: `ae_data_*.csv`
**Purpose**: Structured adverse event reporting data for safety analysis.

**Sample Files**: 
- `ae_data_safety_database_5k.csv` - **5,000 rows** (primary dataset)
- `ae_data_safety_database.csv` - 15 rows (small sample)

**Comprehensive AE Data (11 Fields)**:
- **Core Fields**: patient_id, ae_term, severity_grade, relationship_to_drug
- **Temporal**: start_date, end_date, outcome
- **Clinical**: serious_flag, action_taken
- **Context**: concomitant_meds, medical_history

**Rich Clinical Context**:
- **50+ unique AE terms** (MedDRA-style terminology)
- **CTCAE severity grading** (Grades 1-5)
- **Causality assessment** (5-point scale)
- **Clinical actions** based on severity
- **Medical history** and concomitant medications
- **Realistic outcomes** and temporal patterns

**Use Cases for RAG**:
- Query adverse event patterns and frequencies
- Assess drug safety profiles and risk factors
- Identify serious adverse events and outcomes
- Analyze causality relationships and dose modifications
- Generate safety summaries and signal detection
- Track AE resolution patterns and medical actions
- Correlate with patient medical history and concomitant medications

### 5. Regulatory Submission Documents (PDF)
**File Pattern**: `regulatory_*.pdf`
**Purpose**: Documents submitted to regulatory agencies (FDA, EMA, etc.).

**Sample File**: `regulatory_nda_section_2_sample.pdf`
**Content Includes**:
- Quality module documentation
- Non-clinical study reports
- Clinical study summaries
- Risk management plans
- Product labeling

**Use Cases for RAG**:
- Query regulatory requirements
- Find submission timelines
- Extract quality specifications
- Review approval conditions

## Data Privacy & Compliance

### Synthetic Data Only
All sample files in this directory contain **SYNTHETIC DATA ONLY**. No real patient data, proprietary clinical information, or confidential business information is included.

### PHI Considerations
- All patient identifiers are synthetic
- Dates are fictional or anonymized
- Geographic locations are generalized
- No real patient health information is included

### Data Generation Sources
- **Text Content**: Generated using privacy-conscious AI models
- **Numerical Data**: Programmatically generated with realistic distributions
- **Medical Terms**: Based on public medical vocabularies (MedDRA, SNOMED CT)
- **Regulatory Content**: Based on publicly available guidance documents

## Dataset Statistics

### Lab Chemistry Panel (5,000 rows)
- **File Size**: ~597KB
- **Patients**: 312 unique patients
- **Time Span**: 365 days (2024)
- **Tests per Patient**: 16 lab tests
- **Abnormal Rate**: ~15% (realistic clinical distribution)
- **Visit Pattern**: 1-3 visits per patient

### Adverse Events (5,000 rows)
- **File Size**: ~649KB
- **Patients**: 1,000 unique patients
- **AE Terms**: 50+ different adverse events
- **Severity Distribution**: Weighted toward lower grades (1-2)
- **Serious Events**: ~8% (realistic safety profile)
- **Temporal Coverage**: Full year with resolution tracking

## File Validation

Each sample file includes:
- **Checksum**: SHA-256 hash for integrity verification
- **Metadata**: File size, creation date, document type
- **Schema**: For structured data (CSV), includes column definitions
- **Validation**: Data quality checks and compliance verification
- **Generator Script**: `generate_clinical_data.py` for reproducibility

## Usage Instructions

### For Development
1. Use these files to test document ingestion pipelines
2. Validate NLP processing accuracy
3. Test embedding generation and retrieval
4. Develop and refine search algorithms

### For Testing
1. Automated testing of document parsing
2. Validation of PHI detection algorithms
3. Testing of access controls and audit logging
4. Performance benchmarking with realistic data volumes

### For Demonstrations
1. Safe demonstration of system capabilities
2. Training materials for end users
3. Proof of concept presentations
4. Regulatory review discussions

## Adding New Sample Documents

When adding new sample documents:

1. **Ensure Synthetic Nature**: Verify no real PHI or confidential data
2. **Document Metadata**: Update this README with file descriptions
3. **Validate Format**: Ensure files match expected schemas
4. **Test Compatibility**: Verify files work with ingestion pipelines
5. **Update Checksums**: Generate and record file integrity hashes

## Security Notes

- These files are safe for development and testing environments
- Do not use in production without proper data governance review
- Regular security scanning should be performed on all sample data
- Access to this directory should still follow principle of least privilege

## Compliance Validation

All sample documents have been validated for:
- ✅ No real PHI content
- ✅ No proprietary information
- ✅ Compliance with synthetic data guidelines
- ✅ Appropriate medical terminology usage
- ✅ Realistic but fictional content structure

## Contact

For questions about sample data or to request additional document types, contact the development team or refer to the project documentation in `docs/`.