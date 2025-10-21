#!/usr/bin/env python3
"""
ClinChat-RAG Enhanced API with Google Gemini & Groq Integration
FastAPI application with multiple AI provider support
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import spacy
from pathlib import Path
import logging
import os
import asyncio
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

# AI Provider imports (with error handling)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Gemini not available. Install with: pip install google-generativeai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: Groq not available. Install with: pip install groq")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ClinChat-RAG Enhanced API",
    description="Clinical Document AI Assistant with Google Gemini & Groq Integration",
    version="2.0.0",
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
gemini_model = None
groq_client = None

# Pydantic models
class ClinicalText(BaseModel):
    text: str = Field(..., description="Clinical text to analyze")
    provider: Optional[str] = Field("local", description="AI provider: local, gemini, or groq")
    max_tokens: Optional[int] = Field(2000, description="Maximum tokens for AI response")

class EntityResponse(BaseModel):
    text: str
    entities: Dict[str, List[str]]
    provider_used: str
    processing_time: float
    ai_analysis: Optional[str] = None

class DatasetInfo(BaseModel):
    name: str
    description: str
    records: int
    size_mb: float
    last_updated: str

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    providers: Dict[str, bool]
    models_loaded: Dict[str, bool]

class AIResponse(BaseModel):
    provider: str
    response: str
    processing_time: float
    model_used: str

# AI Provider Configuration
def configure_ai_providers():
    """Configure AI providers based on available API keys"""
    global gemini_model, groq_client
    
    # Configure Google Gemini
    if GEMINI_AVAILABLE:
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and api_key != 'your_google_gemini_api_key_here':
            try:
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("✅ Google Gemini configured successfully")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini: {e}")
    
    # Configure Groq
    if GROQ_AVAILABLE:
        api_key = os.getenv('GROQ_API_KEY')
        if api_key and api_key != 'your_groq_api_key_here':
            try:
                groq_client = Groq(api_key=api_key)
                logger.info("✅ Groq Cloud configured successfully")
            except Exception as e:
                logger.error(f"❌ Failed to configure Groq: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models and load data on startup"""
    global nlp_sm, nlp_md
    
    logger.info("🚀 Starting ClinChat-RAG Enhanced API...")
    
    # Configure AI providers
    configure_ai_providers()
    
    # Load spaCy models
    try:
        nlp_sm = spacy.load("en_core_web_sm")
        nlp_md = spacy.load("en_core_web_md")
        logger.info("✅ spaCy models loaded successfully")
    except OSError as e:
        logger.error(f"❌ Failed to load spaCy models: {e}")
        logger.error("Install with: python -m spacy download en_core_web_sm en_core_web_md")
    
    # Load clinical datasets
    load_clinical_datasets()
    
    logger.info("✨ API initialization complete!")

def load_clinical_datasets():
    """Load clinical datasets into memory"""
    global clinical_data
    
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    # Load adverse events data
    ae_file = data_dir / "adverse_events_clinical.csv"
    if ae_file.exists():
        clinical_data['adverse_events'] = pd.read_csv(ae_file)
        logger.info(f"✅ Loaded {len(clinical_data['adverse_events'])} adverse events")
    
    # Load lab data
    lab_file = data_dir / "lab_results_clinical.csv"
    if lab_file.exists():
        clinical_data['lab_results'] = pd.read_csv(lab_file)
        logger.info(f"✅ Loaded {len(clinical_data['lab_results'])} lab results")

def get_nlp_model(model_type: str = "medium"):
    """Get spaCy model based on type"""
    if model_type == "small" and nlp_sm:
        return nlp_sm
    elif model_type == "medium" and nlp_md:
        return nlp_md
    return None

def extract_clinical_entities(text: str, nlp_model) -> Dict[str, List[str]]:
    """Extract clinical-specific entities"""
    if not nlp_model:
        return {"error": ["spaCy model not available"]}
    
    doc = nlp_model(text)
    
    entities = {
        "persons": [],
        "organizations": [],
        "medical_conditions": [],
        "medications": [],
        "body_parts": [],
        "lab_values": [],
        "dates": [],
        "all_entities": []
    }
    
    # Extract named entities
    for ent in doc.ents:
        entities["all_entities"].append(f"{ent.text} ({ent.label_})")
        
        if ent.label_ in ["PERSON"]:
            entities["persons"].append(ent.text)
        elif ent.label_ in ["ORG"]:
            entities["organizations"].append(ent.text)
        elif ent.label_ in ["DATE", "TIME"]:
            entities["dates"].append(ent.text)
    
    # Extract medical terms using pattern matching
    medical_keywords = {
        "conditions": ["diabetes", "hypertension", "pneumonia", "infection", "fever", "pain", "inflammation"],
        "medications": ["aspirin", "ibuprofen", "penicillin", "insulin", "metformin"],
        "body_parts": ["heart", "lung", "liver", "kidney", "brain", "chest", "abdomen"]
    }
    
    text_lower = text.lower()
    for category, keywords in medical_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                if category == "conditions":
                    entities["medical_conditions"].append(keyword)
                elif category == "medications":
                    entities["medications"].append(keyword)
                elif category == "body_parts":
                    entities["body_parts"].append(keyword)
    
    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities

async def analyze_with_gemini(text: str, analysis_type: str = "clinical") -> Optional[str]:
    """Analyze text with Google Gemini"""
    if not gemini_model:
        return None
    
    try:
        if analysis_type == "clinical":
            prompt = f"""
            Analyze this clinical text and provide a structured summary:
            
            Text: {text}
            
            Please provide:
            1. Key medical findings
            2. Potential diagnoses or conditions mentioned
            3. Treatment recommendations if any
            4. Important clinical observations
            
            Keep the response concise and clinical.
            """
        else:
            prompt = f"Analyze this text: {text}"
        
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return None

async def analyze_with_groq(text: str, analysis_type: str = "clinical") -> Optional[str]:
    """Analyze text with Groq Cloud"""
    if not groq_client:
        return None
    
    try:
        if analysis_type == "clinical":
            system_prompt = "You are a medical AI assistant. Analyze clinical text and provide structured, professional medical summaries."
            user_prompt = f"Analyze this clinical text and extract key medical information: {text}"
        else:
            system_prompt = "You are a helpful AI assistant."
            user_prompt = f"Analyze this text: {text}"
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-70b-versatile",
            max_tokens=2000,
            temperature=0.1
        )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq analysis failed: {e}")
        return None

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "ClinChat-RAG Enhanced API",
        "version": "2.0.0",
        "description": "Clinical Document AI Assistant with Google Gemini & Groq",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    providers = {
        "gemini": gemini_model is not None,
        "groq": groq_client is not None,
        "spacy": nlp_sm is not None and nlp_md is not None
    }
    
    models_loaded = {
        "spacy_small": nlp_sm is not None,
        "spacy_medium": nlp_md is not None,
        "datasets": len(clinical_data) > 0
    }
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="2.0.0",
        providers=providers,
        models_loaded=models_loaded
    )

@app.post("/analyze/text", response_model=EntityResponse)
async def analyze_clinical_text(request: ClinicalText):
    """Analyze clinical text with multiple AI providers"""
    start_time = datetime.utcnow()
    
    # Get spaCy model for entity extraction
    nlp_model = get_nlp_model("medium")
    entities = extract_clinical_entities(request.text, nlp_model)
    
    # AI Analysis based on provider
    ai_analysis = None
    provider_used = request.provider
    
    if request.provider == "gemini" and gemini_model:
        ai_analysis = await analyze_with_gemini(request.text)
        provider_used = "gemini"
    elif request.provider == "groq" and groq_client:
        ai_analysis = await analyze_with_groq(request.text)
        provider_used = "groq"
    elif request.provider == "auto":
        # Try providers in order of preference
        if gemini_model:
            ai_analysis = await analyze_with_gemini(request.text)
            provider_used = "gemini"
        elif groq_client:
            ai_analysis = await analyze_with_groq(request.text)
            provider_used = "groq"
        else:
            provider_used = "local"
    else:
        provider_used = "local"
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    return EntityResponse(
        text=request.text,
        entities=entities,
        provider_used=provider_used,
        processing_time=processing_time,
        ai_analysis=ai_analysis
    )

@app.post("/analyze/ai", response_model=AIResponse)
async def ai_analysis_only(request: ClinicalText):
    """Get AI analysis without entity extraction"""
    start_time = datetime.utcnow()
    
    response_text = "No AI provider available"
    model_used = "none"
    provider = request.provider
    
    if request.provider == "gemini" and gemini_model:
        response_text = await analyze_with_gemini(request.text) or "Analysis failed"
        model_used = "gemini-1.5-pro"
        provider = "gemini"
    elif request.provider == "groq" and groq_client:
        response_text = await analyze_with_groq(request.text) or "Analysis failed"
        model_used = "llama-3.1-70b-versatile"
        provider = "groq"
    elif request.provider == "auto":
        if gemini_model:
            response_text = await analyze_with_gemini(request.text) or "Analysis failed"
            model_used = "gemini-1.5-pro"
            provider = "gemini"
        elif groq_client:
            response_text = await analyze_with_groq(request.text) or "Analysis failed"
            model_used = "llama-3.1-70b-versatile"
            provider = "groq"
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    
    return AIResponse(
        provider=provider,
        response=response_text,
        processing_time=processing_time,
        model_used=model_used
    )

@app.get("/providers/status")
async def get_provider_status():
    """Get status of all AI providers"""
    return {
        "providers": {
            "gemini": {
                "available": GEMINI_AVAILABLE,
                "configured": gemini_model is not None,
                "model": "gemini-1.5-pro",
                "description": "Google Gemini Pro - Advanced reasoning and analysis"
            },
            "groq": {
                "available": GROQ_AVAILABLE,
                "configured": groq_client is not None,
                "model": "llama-3.1-70b-versatile",
                "description": "Groq Cloud - High-speed inference"
            },
            "spacy": {
                "available": True,
                "configured": nlp_sm is not None and nlp_md is not None,
                "models": ["en_core_web_sm", "en_core_web_md"],
                "description": "Local clinical NLP processing"
            }
        },
        "recommended_setup": {
            "gemini_api_key": "https://makersuite.google.com/app/apikey",
            "groq_api_key": "https://console.groq.com/"
        }
    }

@app.get("/datasets", response_model=List[DatasetInfo])
async def get_datasets():
    """Get information about loaded datasets"""
    datasets = []
    
    for name, df in clinical_data.items():
        if isinstance(df, pd.DataFrame):
            datasets.append(DatasetInfo(
                name=name,
                description=f"Clinical {name.replace('_', ' ')} dataset",
                records=len(df),
                size_mb=round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                last_updated=datetime.utcnow().isoformat()
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
        "columns": list(df.columns),
        "column_types": df.dtypes.to_dict(),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "sample_data": df.head(3).to_dict(orient="records")
    }
    
    # Add specific summaries based on dataset type
    if dataset_name == "adverse_events":
        if 'severity' in df.columns:
            severity_counts = df['severity'].value_counts().to_dict()
            summary["severity_distribution"] = severity_counts
        
        if 'event_type' in df.columns:
            event_counts = df['event_type'].value_counts().head(10).to_dict()
            summary["top_event_types"] = event_counts
    
    elif dataset_name == "lab_results":
        if 'test_name' in df.columns:
            test_counts = df['test_name'].value_counts().head(10).to_dict()
            summary["top_tests"] = test_counts
        
        if 'result_interpretation' in df.columns:
            normal_count = len(df[df['result_interpretation'] == 'Normal'])
            abnormal_count = len(df[df['result_interpretation'] != 'Normal'])
            summary["result_distribution"] = {
                "normal": normal_count,
                "abnormal": abnormal_count,
                "abnormal_rate": round(abnormal_count / len(df) * 100, 2)
            }
    
    return summary

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("ENHANCED_API_PORT", 8001))  # Use different port for enhanced API
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    print("🚀 Starting ClinChat-RAG Enhanced API Server...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print("🤖 AI Providers: Google Gemini + Groq Cloud + Local spaCy")
    
    uvicorn.run(
        "enhanced_main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )