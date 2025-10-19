# Sample Clinical Dataset Documentation

## Overview

This directory contains sample clinical documents for testing and development of the ClinChat-RAG system. These files represent the types of documents commonly found in clinical trials and pharmaceutical research.

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

### 3. Laboratory Data (CSV)
**File Pattern**: `lab_data_*.csv`
**Purpose**: Structured laboratory test results from clinical trials.

**Sample File**: `lab_data_chemistry_panel.csv`
**Columns Include**:
- patient_id
- visit_date
- test_name
- test_value
- reference_range
- units
- abnormal_flag
- lab_comments

**Use Cases for RAG**:
- Query specific lab values
- Identify abnormal results
- Track lab trends over time
- Compare against reference ranges

### 4. Adverse Events Data (CSV)
**File Pattern**: `ae_data_*.csv`
**Purpose**: Structured adverse event reporting data.

**Sample File**: `ae_data_safety_database.csv`
**Columns Include**:
- patient_id
- ae_term
- severity_grade
- relationship_to_drug
- start_date
- end_date
- serious_flag
- outcome

**Use Cases for RAG**:
- Query adverse event patterns
- Assess drug safety profiles
- Identify serious adverse events
- Analyze causality relationships

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

## File Validation

Each sample file includes:
- **Checksum**: SHA-256 hash for integrity verification
- **Metadata**: File size, creation date, document type
- **Schema**: For structured data (CSV), includes column definitions
- **Validation**: Data quality checks and compliance verification

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