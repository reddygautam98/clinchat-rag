# 🏥 ClinChat-RAG API Reference

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Clinical Query APIs](#clinical-query-apis)
- [Medical Information APIs](#medical-information-apis)
- [Drug Interaction APIs](#drug-interaction-apis)
- [Patient Safety APIs](#patient-safety-apis)
- [Administrative APIs](#administrative-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Medical Compliance](#medical-compliance)

## 🎯 Overview

The ClinChat-RAG API provides secure, HIPAA-compliant endpoints for clinical decision support, medical information retrieval, and healthcare workflow integration. All endpoints require proper authentication and follow medical data protection standards.

**Base URL**: `https://api.clinchat-rag.com/v1`  
**API Version**: `v1.0.0`  
**Medical Compliance**: HIPAA, FDA Guidelines  
**Security**: OAuth 2.0, JWT Tokens, TLS 1.3

## 🔐 Authentication

### OAuth 2.0 Flow

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=your_client_id&
client_secret=your_client_secret&
scope=clinical:read clinical:write medical:query
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "clinical:read clinical:write medical:query",
  "medical_license_verified": true
}
```

### Using API Tokens

Include the Bearer token in all API requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
X-Medical-Context: clinical_decision_support
```

## 🩺 Clinical Query APIs

### Ask Clinical Question

**Endpoint**: `POST /clinical/query`  
**Purpose**: Get evidence-based answers to clinical questions  
**Medical Use**: Clinical decision support, medical education

```http
POST /clinical/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "question": "What are the contraindications for metformin?",
  "context": {
    "specialty": "endocrinology",
    "patient_age": 65,
    "medical_history": ["diabetes_type_2", "ckd_stage_3"],
    "urgency": "routine"
  },
  "preferences": {
    "include_guidelines": true,
    "include_drug_interactions": true,
    "evidence_level": "high_quality_only",
    "response_format": "structured"
  }
}
```

**Response:**
```json
{
  "response": {
    "answer": "Metformin is contraindicated in patients with severe renal impairment (eGFR <30 mL/min/1.73m²), acute or chronic metabolic acidosis, and diabetic ketoacidosis.",
    "clinical_summary": "Based on current ADA/EASD guidelines and FDA prescribing information.",
    "contraindications": [
      {
        "condition": "Severe renal impairment",
        "criteria": "eGFR <30 mL/min/1.73m²",
        "rationale": "Risk of lactic acidosis due to reduced metformin clearance",
        "evidence_level": "A"
      }
    ],
    "confidence_score": 0.95,
    "last_updated": "2024-10-15T10:30:00Z"
  },
  "sources": [
    {
      "title": "Standards of Medical Care in Diabetes—2024",
      "authors": ["American Diabetes Association"],
      "journal": "Diabetes Care",
      "year": 2024,
      "doi": "10.2337/dc24-S009",
      "relevance_score": 0.92,
      "evidence_level": "A"
    }
  ],
  "metadata": {
    "query_id": "cq_20241020_123456",
    "processing_time_ms": 1250,
    "medical_specialty": "endocrinology",
    "compliance_verified": true,
    "audit_logged": true
  }
}
```

### Clinical Guidelines Search

**Endpoint**: `GET /clinical/guidelines`  
**Purpose**: Search current clinical practice guidelines

```http
GET /clinical/guidelines?condition=hypertension&specialty=cardiology&year=2024
Authorization: Bearer {token}
```

**Response:**
```json
{
  "guidelines": [
    {
      "id": "aha_hypertension_2024",
      "title": "2024 AHA/ACC Guideline for Management of Hypertension",
      "organization": "American Heart Association",
      "publication_date": "2024-03-15",
      "summary": "Updated recommendations for hypertension diagnosis and management",
      "key_recommendations": [
        {
          "recommendation": "BP target <130/80 mmHg for most adults",
          "strength": "Strong",
          "evidence_quality": "High"
        }
      ],
      "url": "https://ahajournals.org/hypertension/guidelines/2024"
    }
  ],
  "total_count": 5,
  "search_metadata": {
    "query_terms": ["hypertension", "cardiology"],
    "filters_applied": ["year:2024", "specialty:cardiology"],
    "search_time_ms": 450
  }
}
```

## 💊 Drug Interaction APIs

### Check Drug Interactions

**Endpoint**: `POST /drugs/interactions/check`  
**Purpose**: Analyze potential drug interactions  
**Medical Use**: Medication safety, clinical pharmacy

```http
POST /drugs/interactions/check
Authorization: Bearer {token}
Content-Type: application/json

{
  "medications": [
    {
      "name": "warfarin",
      "dosage": "5mg",
      "frequency": "daily",
      "route": "oral"
    },
    {
      "name": "ciprofloxacin", 
      "dosage": "500mg",
      "frequency": "twice_daily",
      "route": "oral"
    }
  ],
  "patient_context": {
    "age": 72,
    "weight_kg": 68,
    "renal_function": "normal",
    "liver_function": "mild_impairment"
  }
}
```

**Response:**
```json
{
  "interactions": [
    {
      "drug_1": "warfarin",
      "drug_2": "ciprofloxacin",
      "severity": "major",
      "clinical_significance": "high",
      "mechanism": "CYP1A2 and CYP3A4 inhibition by ciprofloxacin increases warfarin levels",
      "clinical_effect": "Increased anticoagulation effect and bleeding risk",
      "onset": "rapid (1-3 days)",
      "management": {
        "recommendations": [
          "Monitor INR closely (daily for first week)",
          "Consider warfarin dose reduction (25-50%)",
          "Alternative antibiotic if possible"
        ],
        "monitoring_frequency": "daily_inr_x7_days"
      },
      "references": [
        {
          "pmid": "12345678",
          "title": "Warfarin-ciprofloxacin interaction",
          "journal": "Clin Pharmacol Ther"
        }
      ]
    }
  ],
  "overall_risk_assessment": {
    "risk_level": "high",
    "requires_monitoring": true,
    "contraindicated": false,
    "alternative_suggested": true
  },
  "metadata": {
    "interaction_check_id": "ic_20241020_789123",
    "database_version": "2024.10.15",
    "last_updated": "2024-10-15T08:00:00Z"
  }
}
```

### Drug Information Lookup

**Endpoint**: `GET /drugs/{drug_name}/info`  
**Purpose**: Comprehensive drug information retrieval

```http
GET /drugs/metformin/info?include=contraindications,interactions,monitoring
Authorization: Bearer {token}
```

**Response:**
```json
{
  "drug_info": {
    "generic_name": "metformin",
    "brand_names": ["Glucophage", "Fortamet", "Glumetza"],
    "drug_class": "biguanide",
    "therapeutic_category": "antidiabetic",
    "mechanism_of_action": "Decreases hepatic glucose production and improves insulin sensitivity",
    "indications": [
      {
        "indication": "Type 2 diabetes mellitus",
        "fda_approved": true,
        "guideline_recommended": true
      }
    ],
    "contraindications": [
      {
        "condition": "Severe renal impairment",
        "criteria": "eGFR <30 mL/min/1.73m²",
        "absolute": true
      }
    ],
    "monitoring_parameters": [
      {
        "parameter": "Renal function",
        "frequency": "annually",
        "critical_values": "eGFR <45 requires dose adjustment"
      }
    ],
    "black_box_warnings": [],
    "pregnancy_category": "B"
  }
}
```

## ⚕️ Patient Safety APIs

### Allergy Interaction Check

**Endpoint**: `POST /safety/allergy-check`  
**Purpose**: Check medications against patient allergies

```http
POST /safety/allergy-check
Authorization: Bearer {token}
Content-Type: application/json

{
  "medication": {
    "name": "amoxicillin",
    "class": "beta_lactam_antibiotic"
  },
  "patient_allergies": [
    {
      "allergen": "penicillin",
      "reaction_type": "anaphylaxis",
      "severity": "severe",
      "verified": true
    }
  ]
}
```

**Response:**
```json
{
  "safety_assessment": {
    "contraindicated": true,
    "risk_level": "high",
    "cross_reactivity": {
      "present": true,
      "mechanism": "Beta-lactam ring structure similarity",
      "cross_reaction_probability": 0.85
    },
    "recommendations": {
      "action": "avoid_medication",
      "alternatives": [
        {
          "medication": "azithromycin",
          "safety_profile": "safe_alternative",
          "efficacy": "equivalent"
        }
      ]
    }
  }
}
```

### Dosage Calculation

**Endpoint**: `POST /safety/dosage-calculation`  
**Purpose**: Calculate appropriate medication dosages

```http
POST /safety/dosage-calculation
Authorization: Bearer {token}
Content-Type: application/json

{
  "medication": "vancomycin",
  "indication": "severe_infection",
  "patient": {
    "age": 45,
    "weight_kg": 70,
    "height_cm": 175,
    "creatinine_mg_dl": 1.2,
    "gender": "male"
  },
  "target_level": "trough_15_20"
}
```

## 📊 Administrative APIs

### System Health Check

**Endpoint**: `GET /health`  
**Purpose**: Monitor system status and medical service availability

```http
GET /health
Authorization: Bearer {token}
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-10-20T14:30:00Z",
  "services": {
    "clinical_nlp": {
      "status": "operational",
      "response_time_ms": 145,
      "accuracy_score": 0.97
    },
    "drug_database": {
      "status": "operational",
      "last_updated": "2024-10-15T08:00:00Z",
      "version": "2024.10.15"
    },
    "medical_guidelines": {
      "status": "operational",
      "guidelines_count": 1247,
      "last_sync": "2024-10-19T12:00:00Z"
    }
  },
  "compliance_status": {
    "hipaa_compliant": true,
    "audit_logging": "active",
    "data_encryption": "aes_256_active"
  }
}
```

### Audit Log Query

**Endpoint**: `GET /audit/logs`  
**Purpose**: Retrieve clinical activity audit trails

```http
GET /audit/logs?start_date=2024-10-01&end_date=2024-10-20&user_id=clinician_123
Authorization: Bearer {token}
X-Audit-Context: compliance_review
```

## ⚠️ Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "MEDICAL_VALIDATION_ERROR",
    "message": "Clinical query requires valid medical context",
    "details": {
      "field": "patient_context",
      "requirement": "Patient age and medical history required for drug safety assessment"
    },
    "medical_impact": "moderate",
    "suggested_action": "Provide complete patient context for accurate clinical assessment"
  },
  "request_id": "req_20241020_456789",
  "timestamp": "2024-10-20T14:30:00Z"
}
```

### Error Codes

| Code | Description | Medical Significance |
|------|-------------|---------------------|
| `INSUFFICIENT_MEDICAL_CONTEXT` | Missing patient information | May affect clinical accuracy |
| `DRUG_INTERACTION_WARNING` | Potential medication interaction | Patient safety concern |
| `CONTRAINDICATION_DETECTED` | Medication contraindicated | Critical safety alert |
| `MEDICAL_LICENSE_REQUIRED` | Valid medical license needed | Compliance requirement |
| `HIPAA_VIOLATION_DETECTED` | PHI in request | Privacy violation |

## 🚦 Rate Limiting

### Clinical APIs
- **Standard Users**: 1000 requests/hour
- **Licensed Clinicians**: 5000 requests/hour  
- **Enterprise**: 50,000 requests/hour
- **Emergency Access**: Unlimited (with justification)

### Rate Limit Headers

```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4789
X-RateLimit-Reset: 1634567890
X-RateLimit-Medical-Priority: standard
```

## 🛡️ Medical Compliance

### HIPAA Compliance
- All requests are logged for audit purposes
- PHI is automatically detected and rejected
- Access is restricted to licensed healthcare professionals
- Data is encrypted in transit and at rest

### Medical Disclaimers
- All responses include appropriate clinical disclaimers
- System is for decision support only, not diagnosis
- Healthcare professionals must validate all recommendations
- Emergency situations require immediate medical attention

### Clinical Validation
- Medical accuracy is continuously monitored
- Responses are validated against current guidelines
- System includes confidence scores and evidence levels
- Regular updates from authoritative medical sources

---

## 📞 API Support

### Technical Support
- **Email**: api-support@clinchat-rag.com
- **Documentation**: https://docs.clinchat-rag.com
- **Status Page**: https://status.clinchat-rag.com

### Medical Support
- **Medical Director**: medical-director@clinchat-rag.com
- **Clinical Validation**: clinical-team@clinchat-rag.com
- **Emergency Contact**: +1-800-MEDICAL (24/7)

### Security Issues
- **Security Team**: security@clinchat-rag.com
- **HIPAA Compliance**: compliance@clinchat-rag.com
- **Vulnerability Reports**: security-reports@clinchat-rag.com

---

**⚠️ Medical Disclaimer**: This API provides clinical decision support tools. All medical decisions should be made by qualified healthcare professionals. This system is not a substitute for professional medical judgment.