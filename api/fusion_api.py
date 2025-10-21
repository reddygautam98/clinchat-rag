#!/usr/bin/env python3
"""
ClinChat-RAG Enhanced API with Fusion AI Technology
Intelligent combination of Google Gemini and Groq Cloud for optimal clinical analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import spacy
from pathlib import Path
import logging
import os
import asyncio
from datetime import datetime
import uvicorn
from dotenv import load_dotenv
import sys

# Add fusion AI engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Fusion AI Engine
try:
    from fusion_ai_engine import FusionAIEngine, AnalysisType, FusionResult
    FUSION_AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fusion AI engine not available: {e}")
    FUSION_AI_AVAILABLE = False

# Database integration
try:
    from database.connection import init_database, get_database_health, get_db_context
    from database.operations import (
        ConversationManager, ProviderResponseManager, AnalyticsManager,
        ClinicalDocumentManager, AuditManager
    )
    from database.models import (
        ProviderType, AnalysisType as DBAnalysisType, 
        UrgencyLevel, FusionStrategy
    )
    DATABASE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Database integration not available: {e}")
    DATABASE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ClinChat-RAG Fusion AI API",
    description="Clinical Document AI Assistant with Fusion AI Technology",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
nlp_sm = None
nlp_md = None
clinical_data = {}
fusion_engine = None

# Pydantic models
class ClinicalText(BaseModel):
    text: str = Field(..., description="Clinical text to analyze")
    analysis_type: Optional[str] = Field("detailed_analysis", description="Analysis type: quick_triage, emergency_assessment, diagnostic_reasoning, treatment_planning, detailed_analysis")
    urgency: Optional[str] = Field("normal", description="Urgency level: normal, urgent, emergency")
    include_entities: Optional[bool] = Field(True, description="Include spaCy entity extraction")

class FusionAnalysisResponse(BaseModel):
    text: str
    analysis_type: str
    urgency: str
    fusion_strategy: str
    primary_provider: str
    secondary_provider: Optional[str]
    consensus_analysis: str
    confidence_score: float
    processing_time: float
    entities: Optional[Dict[str, List[str]]] = None
    recommendations: List[str]
    provider_details: Dict[str, Dict]

class QuickResponse(BaseModel):
    provider: str
    analysis: str
    processing_time: float
    urgency_level: str
    immediate_actions: List[str]

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    fusion_ai_enabled: bool
    providers_available: Dict[str, bool]
    models_loaded: Dict[str, bool]

# Initialize Fusion AI Engine
async def initialize_fusion_ai():
    """Initialize the Fusion AI Engine"""
    global fusion_engine
    if FUSION_AI_AVAILABLE:
        fusion_engine = FusionAIEngine()
        logger.info("🔮 Fusion AI Engine initialized")
    else:
        logger.warning("⚠️ Fusion AI Engine not available")

@app.on_event("startup")
async def startup_event():
    """Initialize models and load data on startup"""
    global nlp_sm, nlp_md
    
    logger.info("🚀 Starting ClinChat-RAG Fusion AI API...")
    
    # Initialize Fusion AI
    await initialize_fusion_ai()
    
    # Load spaCy models
    try:
        nlp_sm = spacy.load("en_core_web_sm")
        nlp_md = spacy.load("en_core_web_md")
        logger.info("✅ spaCy models loaded successfully")
    except OSError as e:
        logger.error(f"❌ Failed to load spaCy models: {e}")
    
    # Load clinical datasets
    load_clinical_datasets()
    
    logger.info("✨ Fusion AI API initialization complete!")

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

def extract_clinical_entities(text: str) -> Dict[str, List[str]]:
    """Extract clinical entities using spaCy"""
    if not nlp_md:
        return {"error": ["spaCy models not available"]}
    
    doc = nlp_md(text)
    
    entities = {
        "persons": [],
        "organizations": [],
        "medical_conditions": [],
        "medications": [],
        "body_parts": [],
        "dates": [],
        "quantities": [],
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
        elif ent.label_ in ["QUANTITY", "CARDINAL"]:
            entities["quantities"].append(ent.text)
    
    # Extract medical terms using pattern matching
    medical_keywords = {
        "conditions": ["diabetes", "hypertension", "pneumonia", "infection", "fever", "pain", "inflammation", 
                      "myocardial infarction", "stroke", "sepsis", "pneumonia", "COPD"],
        "medications": ["aspirin", "ibuprofen", "penicillin", "insulin", "metformin", "atorvastatin", 
                       "lisinopril", "amlodipine", "warfarin", "heparin"],
        "body_parts": ["heart", "lung", "liver", "kidney", "brain", "chest", "abdomen", "extremities"]
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

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "ClinChat-RAG Fusion AI API",
        "version": "3.0.0",
        "description": "Clinical Document AI Assistant with Fusion AI Technology",
        "fusion_ai": "Google Gemini + Groq Cloud Intelligence",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint with Fusion AI and Database status"""
    providers_available = {
        "fusion_ai": fusion_engine is not None,
        "gemini": fusion_engine and fusion_engine.gemini_model is not None,
        "groq": fusion_engine and fusion_engine.groq_client is not None,
        "spacy": nlp_sm is not None and nlp_md is not None,
        "database": DATABASE_AVAILABLE
    }
    
    models_loaded = {
        "spacy_small": nlp_sm is not None,
        "spacy_medium": nlp_md is not None,
        "clinical_datasets": len(clinical_data) > 0,
        "fusion_engine": fusion_engine is not None,
        "database_models": DATABASE_AVAILABLE
    }
    
    # Get database health if available
    database_health = None
    if DATABASE_AVAILABLE:
        try:
            database_health = get_database_health()
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            database_health = {"status": "unhealthy", "error": str(e)}
    
    health_response = HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="3.0.0",
        fusion_ai_enabled=FUSION_AI_AVAILABLE,
        providers_available=providers_available,
        models_loaded=models_loaded
    )
    
    # Add database health to response
    if database_health:
        health_response.__dict__["database_health"] = database_health
    
    return health_response

@app.post("/fusion/analyze", response_model=FusionAnalysisResponse)
async def fusion_analyze(request: ClinicalText):
    """Perform Fusion AI analysis of clinical text"""
    if not fusion_engine:
        raise HTTPException(status_code=503, detail="Fusion AI Engine not available")
    
    # Map string analysis type to enum
    analysis_type_mapping = {
        "quick_triage": AnalysisType.QUICK_TRIAGE,
        "emergency_assessment": AnalysisType.EMERGENCY_ASSESSMENT,
        "diagnostic_reasoning": AnalysisType.DIAGNOSTIC_REASONING,
        "treatment_planning": AnalysisType.TREATMENT_PLANNING,
        "detailed_analysis": AnalysisType.DETAILED_ANALYSIS,
        "research_analysis": AnalysisType.RESEARCH_ANALYSIS
    }
    
    analysis_type = analysis_type_mapping.get(request.analysis_type, AnalysisType.DETAILED_ANALYSIS)
    
    try:
        # Perform Fusion AI analysis
        result = await fusion_engine.fusion_analyze(
            text=request.text,
            analysis_type=analysis_type,
            urgency=request.urgency
        )
        
        # Extract entities if requested
        entities = None
        if request.include_entities:
            entities = extract_clinical_entities(request.text)
        
        # Build provider details
        provider_details = {}
        if result.primary_result:
            provider_details["primary"] = {
                "provider": result.primary_result.provider,
                "model": result.primary_result.model,
                "processing_time": result.primary_result.processing_time,
                "confidence": result.primary_result.confidence_score,
                "tokens_used": result.primary_result.tokens_used
            }
        
        if result.secondary_result:
            provider_details["secondary"] = {
                "provider": result.secondary_result.provider,
                "model": result.secondary_result.model,
                "processing_time": result.secondary_result.processing_time,
                "confidence": result.secondary_result.confidence_score,
                "tokens_used": result.secondary_result.tokens_used
            }
        
        return FusionAnalysisResponse(
            text=request.text,
            analysis_type=request.analysis_type,
            urgency=request.urgency,
            fusion_strategy=result.fusion_strategy,
            primary_provider=result.primary_result.provider if result.primary_result else "none",
            secondary_provider=result.secondary_result.provider if result.secondary_result else None,
            consensus_analysis=result.consensus_analysis,
            confidence_score=result.confidence_score,
            processing_time=result.total_processing_time,
            entities=entities,
            recommendations=result.recommendations,
            provider_details=provider_details
        )
        
    except Exception as e:
        logger.error(f"Fusion AI analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/fusion/quick-triage", response_model=QuickResponse)
async def quick_triage(request: ClinicalText):
    """Rapid clinical triage using Fusion AI"""
    if not fusion_engine:
        raise HTTPException(status_code=503, detail="Fusion AI Engine not available")
    
    try:
        result = await fusion_engine.fusion_analyze(
            text=request.text,
            analysis_type=AnalysisType.QUICK_TRIAGE,
            urgency="normal"
        )
        
        # Extract urgency and actions from response
        analysis_lines = result.consensus_analysis.split('\n')
        urgency_level = "Medium"
        immediate_actions = ["Clinical assessment needed"]
        
        # Parse urgency level and actions from AI response
        for line in analysis_lines:
            if "urgency" in line.lower() or "priority" in line.lower():
                if "high" in line.lower() or "critical" in line.lower():
                    urgency_level = "High"
                elif "low" in line.lower():
                    urgency_level = "Low"
            elif "action" in line.lower() or "immediate" in line.lower():
                if len(line.strip()) > 10:
                    immediate_actions = [line.strip()]
        
        return QuickResponse(
            provider=result.primary_result.provider if result.primary_result else "fusion",
            analysis=result.consensus_analysis,
            processing_time=result.total_processing_time,
            urgency_level=urgency_level,
            immediate_actions=immediate_actions
        )
        
    except Exception as e:
        logger.error(f"Quick triage failed: {e}")
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")

@app.post("/fusion/emergency", response_model=FusionAnalysisResponse)
async def emergency_assessment(request: ClinicalText):
    """Emergency clinical assessment using Fusion AI"""
    if not fusion_engine:
        raise HTTPException(status_code=503, detail="Fusion AI Engine not available")
    
    # Force emergency analysis
    request.analysis_type = "emergency_assessment"
    request.urgency = "emergency"
    
    return await fusion_analyze(request)

@app.get("/fusion/capabilities")
async def get_fusion_capabilities():
    """Get Fusion AI capabilities and strategies"""
    if not fusion_engine:
        return {"error": "Fusion AI Engine not available"}
    
    return {
        "fusion_ai_version": "3.0.0",
        "providers": {
            "gemini": {
                "model": "gemini-2.0-flash",
                "capabilities": ["advanced_reasoning", "complex_diagnostics", "research_analysis"],
                "optimal_for": ["diagnostic_reasoning", "treatment_planning", "detailed_analysis"]
            },
            "groq": {
                "model": "llama-3.1-8b-instant",
                "capabilities": ["high_speed", "real_time_processing", "rapid_triage"],
                "optimal_for": ["quick_triage", "emergency_assessment", "fast_screening"]
            }
        },
        "analysis_types": [
            "quick_triage",
            "emergency_assessment", 
            "diagnostic_reasoning",
            "treatment_planning",
            "detailed_analysis",
            "research_analysis"
        ],
        "fusion_strategies": [
            "speed_first",
            "accuracy_first",
            "groq_only",
            "parallel_consensus",
            "gemini_primary"
        ],
        "urgency_levels": ["normal", "urgent", "emergency"]
    }

@app.get("/datasets")
async def get_datasets():
    """Get information about loaded clinical datasets"""
    datasets = []
    
    for name, df in clinical_data.items():
        if isinstance(df, pd.DataFrame):
            datasets.append({
                "name": name,
                "description": f"Clinical {name.replace('_', ' ')} dataset",
                "records": len(df),
                "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                "last_updated": datetime.utcnow().isoformat()
            })
    
    return {"datasets": datasets, "total_datasets": len(datasets)}

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("FUSION_API_PORT", 8002))
    reload = False  # Disable reload for fusion AI
    
    print("🚀 Starting ClinChat-RAG Fusion AI API Server...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print("🔮 Fusion AI: Google Gemini + Groq Cloud Intelligence")
    
    uvicorn.run(
        "fusion_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )