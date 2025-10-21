#!/usr/bin/env python3
"""
ClinChat-RAG Local API
FastAPI application with local-only features
No external AI dependencies required
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import spacy
from pathlib import Path
import logging
import os
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ClinChat-RAG Local API",
    description="Clinical Document AI Assistant - Local Features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models
nlp_sm = None
nlp_md = None
clinical_data = {}

# Pydantic models
class ClinicalText(BaseModel):
    text: str = Field(..., description="Clinical text to analyze")
    model_type: str = Field("medium", description="spaCy model to use (small/medium)")

class EntityResponse(BaseModel):
    entities: List[Dict[str, Any]]
    clinical_entities: Dict[str, List[str]]
    summary: Dict[str, Any]

class DatasetInfo(BaseModel):
    name: str
    records: int
    size_bytes: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models and load data on startup"""
    global nlp_sm, nlp_md, clinical_data
    
    logger.info("🚀 Starting ClinChat-RAG Local API...")
    
    try:
        # Load spaCy models
        logger.info("📦 Loading spaCy models...")
        nlp_sm = spacy.load("en_core_web_sm")
        nlp_md = spacy.load("en_core_web_md")
        logger.info("✅ spaCy models loaded successfully")
        
        # Load clinical datasets
        logger.info("📊 Loading clinical datasets...")
        load_clinical_datasets()
        logger.info("✅ Clinical datasets loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise e

def load_clinical_datasets():
    """Load clinical datasets into memory"""
    global clinical_data
    
    data_dir = Path("data/raw")
    
    # Load lab data
    lab_file = data_dir / "lab_data_chemistry_panel_5k.csv"
    if lab_file.exists():
        clinical_data["lab_data"] = pd.read_csv(lab_file)
        logger.info(f"📊 Loaded {len(clinical_data['lab_data'])} lab records")
    
    # Load adverse events data
    ae_file = data_dir / "ae_data_safety_database_5k.csv"
    if ae_file.exists():
        clinical_data["ae_data"] = pd.read_csv(ae_file)
        logger.info(f"⚠️ Loaded {len(clinical_data['ae_data'])} adverse event records")

def get_nlp_model(model_type: str = "medium"):
    """Get spaCy model based on type"""
    if model_type == "small":
        return nlp_sm
    else:
        return nlp_md

def extract_clinical_entities(text: str, nlp_model) -> Dict[str, List[str]]:
    """Extract clinical-specific entities"""
    doc = nlp_model(text)
    
    clinical_entities = {
        "medications": [],
        "conditions": [],
        "measurements": [],
        "procedures": [],
        "body_parts": [],
        "dates": [],
        "numbers": [],
        "organizations": [],
        "locations": []
    }
    
    # Clinical term patterns
    medication_indicators = ["mg", "mcg", "daily", "bid", "tid", "qid", "prn"]
    condition_indicators = ["diabetes", "hypertension", "carcinoma", "infarction", "syndrome", "disease"]
    measurement_indicators = ["mmhg", "bpm", "ng/ml", "%", "cm", "lbs", "kg"]
    
    for ent in doc.ents:
        text_lower = ent.text.lower()
        
        # Categorize entities
        if ent.label_ in ["DATE", "TIME"]:
            clinical_entities["dates"].append(ent.text)
        elif ent.label_ in ["CARDINAL", "QUANTITY", "PERCENT"]:
            clinical_entities["numbers"].append(ent.text)
        elif ent.label_ in ["ORG"]:
            clinical_entities["organizations"].append(ent.text)
        elif ent.label_ in ["GPE", "LOC"]:
            clinical_entities["locations"].append(ent.text)
        elif any(med in text_lower for med in medication_indicators):
            clinical_entities["medications"].append(ent.text)
        elif any(cond in text_lower for cond in condition_indicators):
            clinical_entities["conditions"].append(ent.text)
        elif any(meas in text_lower for meas in measurement_indicators):
            clinical_entities["measurements"].append(ent.text)
    
    # Look for specific medication names
    medication_names = ["aspirin", "metoprolol", "atorvastatin", "cisplatin", "insulin", "warfarin"]
    tokens = [token.text.lower() for token in doc]
    
    for med in medication_names:
        if med in tokens:
            clinical_entities["medications"].append(med.title())
    
    # Remove duplicates
    for category in clinical_entities:
        clinical_entities[category] = list(set(clinical_entities[category]))
    
    return clinical_entities

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "ClinChat-RAG Local API",
        "status": "running",
        "version": "1.0.0",
        "features": "local-only",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    components = {
        "spacy_small": "✅ loaded" if nlp_sm else "❌ not loaded",
        "spacy_medium": "✅ loaded" if nlp_md else "❌ not loaded",
        "lab_data": "✅ loaded" if "lab_data" in clinical_data else "❌ not loaded",
        "ae_data": "✅ loaded" if "ae_data" in clinical_data else "❌ not loaded"
    }
    
    all_healthy = all("✅" in status for status in components.values())
    
    return HealthCheck(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        components=components
    )

@app.post("/analyze/text", response_model=EntityResponse)
async def analyze_clinical_text(request: ClinicalText):
    """Analyze clinical text and extract entities"""
    try:
        nlp_model = get_nlp_model(request.model_type)
        if not nlp_model:
            raise HTTPException(status_code=500, detail="spaCy model not available")
        
        # Process text
        doc = nlp_model(request.text)
        
        # Extract standard entities
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "description": spacy.explain(ent.label_),
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0  # spaCy doesn't provide confidence scores
            })
        
        # Extract clinical entities
        clinical_entities = extract_clinical_entities(request.text, nlp_model)
        
        # Create summary
        summary = {
            "total_entities": len(entities),
            "clinical_categories": len([cat for cat, items in clinical_entities.items() if items]),
            "text_length": len(request.text),
            "sentence_count": len(list(doc.sents)),
            "token_count": len([token for token in doc if not token.is_space]),
            "model_used": request.model_type
        }
        
        return EntityResponse(
            entities=entities,
            clinical_entities=clinical_entities,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datasets", response_model=List[DatasetInfo])
async def get_datasets():
    """Get information about loaded datasets"""
    datasets = []
    
    for dataset_name, df in clinical_data.items():
        if df is not None:
            # Get sample data (first 3 records)
            sample_data = df.head(3).to_dict('records')
            
            # Clean sample data for JSON serialization
            for record in sample_data:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        record[key] = str(value)
            
            datasets.append(DatasetInfo(
                name=dataset_name,
                records=len(df),
                size_bytes=df.memory_usage(deep=True).sum(),
                columns=df.columns.tolist(),
                sample_data=sample_data
            ))
    
    return datasets

@app.get("/datasets/{dataset_name}/summary")
async def get_dataset_summary(dataset_name: str):
    """Get summary statistics for a dataset"""
    if dataset_name not in clinical_data:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = clinical_data[dataset_name]
    
    summary = {
        "name": dataset_name,
        "total_records": len(df),
        "columns": len(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        "column_info": {},
        "sample_values": {}
    }
    
    # Analyze each column
    for col in df.columns:
        col_info = {
            "dtype": str(df[col].dtype),
            "non_null_count": df[col].count(),
            "null_count": df[col].isnull().sum(),
            "unique_values": df[col].nunique()
        }
        
        # Add statistics for numeric columns
        if df[col].dtype in ['int64', 'float64']:
            col_info.update({
                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                "std": float(df[col].std()) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None
            })
        
        summary["column_info"][col] = col_info
        
        # Sample values (first 3 unique non-null values)
        sample_values = df[col].dropna().unique()[:3].tolist()
        summary["sample_values"][col] = [str(val) for val in sample_values]
    
    return summary

@app.get("/datasets/{dataset_name}/search")
async def search_dataset(dataset_name: str, query: str, limit: int = 10):
    """Search dataset for records containing query terms"""
    if dataset_name not in clinical_data:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = clinical_data[dataset_name]
    
    # Simple text search across all string columns
    mask = pd.Series([False] * len(df))
    
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            mask |= df[col].astype(str).str.contains(query, case=False, na=False)
    
    results = df[mask].head(limit)
    
    # Convert to JSON-serializable format
    records = results.to_dict('records')
    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, (pd.Timestamp, datetime)):
                record[key] = str(value)
    
    return {
        "query": query,
        "dataset": dataset_name,
        "total_matches": mask.sum(),
        "returned_records": len(records),
        "records": records
    }

@app.get("/clinical/adverse-events/summary")
async def get_ae_summary():
    """Get adverse events summary statistics"""
    if "ae_data" not in clinical_data:
        raise HTTPException(status_code=404, detail="Adverse events data not loaded")
    
    df = clinical_data["ae_data"]
    
    summary = {
        "total_events": len(df),
        "unique_patients": df['patient_id'].nunique() if 'patient_id' in df.columns else None,
        "unique_ae_terms": df['ae_term'].nunique() if 'ae_term' in df.columns else None,
        "severity_distribution": {},
        "serious_events": {},
        "top_ae_terms": {}
    }
    
    # Severity distribution
    if 'ctcae_grade' in df.columns:
        severity_dist = df['ctcae_grade'].value_counts().to_dict()
        summary["severity_distribution"] = {str(k): int(v) for k, v in severity_dist.items()}
    
    # Serious events
    if 'serious' in df.columns:
        serious_counts = df['serious'].value_counts().to_dict()
        summary["serious_events"] = {str(k): int(v) for k, v in serious_counts.items()}
    
    # Top AE terms
    if 'ae_term' in df.columns:
        top_terms = df['ae_term'].value_counts().head(10).to_dict()
        summary["top_ae_terms"] = {str(k): int(v) for k, v in top_terms.items()}
    
    return summary

@app.get("/clinical/lab-data/summary")
async def get_lab_summary():
    """Get laboratory data summary statistics"""
    if "lab_data" not in clinical_data:
        raise HTTPException(status_code=404, detail="Laboratory data not loaded")
    
    df = clinical_data["lab_data"]
    
    summary = {
        "total_results": len(df),
        "unique_patients": df['patient_id'].nunique() if 'patient_id' in df.columns else None,
        "unique_tests": df['test_name'].nunique() if 'test_name' in df.columns else None,
        "result_distribution": {},
        "abnormal_rate": None,
        "top_tests": {}
    }
    
    # Result distribution
    if 'result_interpretation' in df.columns:
        result_dist = df['result_interpretation'].value_counts().to_dict()
        summary["result_distribution"] = {str(k): int(v) for k, v in result_dist.items()}
        
        # Calculate abnormal rate
        total_results = len(df)
        abnormal_results = len(df[df['result_interpretation'] != 'Normal'])
        summary["abnormal_rate"] = round(abnormal_results / total_results * 100, 2)
    
    # Top tests
    if 'test_name' in df.columns:
        top_tests = df['test_name'].value_counts().head(10).to_dict()
        summary["top_tests"] = {str(k): int(v) for k, v in top_tests.items()}
    
    return summary

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print("🚀 Starting ClinChat-RAG Local API Server...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )