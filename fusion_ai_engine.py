#!/usr/bin/env python3
"""
Fusion AI Engine for ClinChat-RAG
Intelligent combination of Google Gemini and Groq Cloud for optimal clinical analysis
With unified database integration for both APIs
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import os
from dotenv import load_dotenv

# AI Provider imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Database integration
try:
    from database.operations import (
        log_fusion_conversation, AnalyticsManager,
        get_db_context, ConversationManager, ProviderResponseManager
    )
    from database.models import (
        ProviderType, AnalysisType as DBAnalysisType, 
        UrgencyLevel, FusionStrategy
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Database integration not available")

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of clinical analysis"""
    QUICK_TRIAGE = "quick_triage"
    DETAILED_ANALYSIS = "detailed_analysis"
    EMERGENCY_ASSESSMENT = "emergency_assessment"
    DIAGNOSTIC_REASONING = "diagnostic_reasoning"
    TREATMENT_PLANNING = "treatment_planning"
    RESEARCH_ANALYSIS = "research_analysis"

class ProviderCapability(Enum):
    """AI Provider capabilities"""
    SPEED = "speed"
    REASONING = "reasoning"
    ACCURACY = "accuracy"
    COST_EFFICIENCY = "cost_efficiency"

@dataclass
class AnalysisResult:
    """Result from AI analysis"""
    provider: str
    model: str
    response: str
    processing_time: float
    confidence_score: float
    analysis_type: AnalysisType
    tokens_used: int

@dataclass
class FusionResult:
    """Combined result from Fusion AI"""
    primary_result: AnalysisResult
    secondary_result: Optional[AnalysisResult]
    consensus_analysis: str
    confidence_score: float
    total_processing_time: float
    fusion_strategy: str
    recommendations: List[str]

class FusionAIEngine:
    """Fusion AI Engine that intelligently combines multiple AI providers"""
    
    def __init__(self):
        """Initialize the Fusion AI Engine"""
        self.gemini_model = None
        self.groq_client = None
        self._initialize_providers()
        
        # Provider performance profiles
        self.provider_profiles = {
            "gemini": {
                ProviderCapability.REASONING: 0.95,
                ProviderCapability.ACCURACY: 0.92,
                ProviderCapability.SPEED: 0.60,
                ProviderCapability.COST_EFFICIENCY: 0.85
            },
            "groq": {
                ProviderCapability.REASONING: 0.80,
                ProviderCapability.ACCURACY: 0.85,
                ProviderCapability.SPEED: 0.95,
                ProviderCapability.COST_EFFICIENCY: 0.90
            }
        }
    
    def _initialize_providers(self):
        """Initialize AI providers"""
        # Initialize Google Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key and not api_key.startswith('your_'):
                try:
                    genai.configure(api_key=api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                    logger.info("✅ Fusion AI: Google Gemini initialized")
                except Exception as e:
                    logger.error(f"❌ Fusion AI: Gemini initialization failed: {e}")
        
        # Initialize Groq
        if GROQ_AVAILABLE:
            api_key = os.getenv('GROQ_API_KEY')
            if api_key and not api_key.startswith('your_'):
                try:
                    self.groq_client = Groq(api_key=api_key)
                    logger.info("✅ Fusion AI: Groq Cloud initialized")
                except Exception as e:
                    logger.error(f"❌ Fusion AI: Groq initialization failed: {e}")
    
    def get_optimal_strategy(self, analysis_type: AnalysisType, text_length: int, urgency: str = "normal") -> str:
        """Determine optimal Fusion AI strategy based on requirements"""
        
        # Emergency cases - prioritize speed
        if urgency == "emergency" or analysis_type == AnalysisType.EMERGENCY_ASSESSMENT:
            return "speed_first"
        
        # Complex diagnostic reasoning - prioritize accuracy
        if analysis_type in [AnalysisType.DIAGNOSTIC_REASONING, AnalysisType.RESEARCH_ANALYSIS]:
            return "accuracy_first"
        
        # Quick triage - use fastest provider
        if analysis_type == AnalysisType.QUICK_TRIAGE:
            return "groq_only"
        
        # Long documents - use parallel processing
        if text_length > 1000:
            return "parallel_consensus"
        
        # Default - balanced approach
        return "gemini_primary"
    
    async def analyze_with_gemini(self, text: str, analysis_type: AnalysisType) -> Optional[AnalysisResult]:
        """Analyze text with Google Gemini"""
        if not self.gemini_model:
            return None
        
        start_time = time.time()
        
        try:
            # Create specialized prompt based on analysis type
            prompt = self._create_specialized_prompt(text, analysis_type, "gemini")
            
            response = self.gemini_model.generate_content(prompt)
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                provider="gemini",
                model="gemini-2.0-flash",
                response=response.text.strip(),
                processing_time=processing_time,
                confidence_score=0.92,  # High confidence for Gemini reasoning
                analysis_type=analysis_type,
                tokens_used=len(response.text.split()) * 1.3  # Estimate
            )
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return None
    
    async def analyze_with_groq(self, text: str, analysis_type: AnalysisType) -> Optional[AnalysisResult]:
        """Analyze text with Groq Cloud"""
        if not self.groq_client:
            return None
        
        start_time = time.time()
        
        try:
            # Create specialized prompt based on analysis type
            prompt = self._create_specialized_prompt(text, analysis_type, "groq")
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert clinical AI assistant specializing in medical analysis."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                max_tokens=2000,
                temperature=0.1
            )
            
            processing_time = time.time() - start_time
            response_text = chat_completion.choices[0].message.content.strip()
            
            return AnalysisResult(
                provider="groq",
                model="llama-3.1-8b-instant",
                response=response_text,
                processing_time=processing_time,
                confidence_score=0.85,  # Good confidence for Groq speed
                analysis_type=analysis_type,
                tokens_used=chat_completion.usage.total_tokens if hasattr(chat_completion, 'usage') else len(response_text.split())
            )
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return None
    
    def _create_specialized_prompt(self, text: str, analysis_type: AnalysisType, provider: str) -> str:
        """Create specialized prompts based on analysis type and provider strengths"""
        
        base_clinical_context = f"""
        Clinical Text: {text}
        
        Analysis Type: {analysis_type.value}
        """
        
        if analysis_type == AnalysisType.QUICK_TRIAGE:
            if provider == "groq":  # Groq optimized for speed
                return f"""
                {base_clinical_context}
                
                Provide a RAPID clinical triage assessment:
                1. Urgency level (Low/Medium/High/Critical)
                2. Primary concern (1-2 sentences)
                3. Immediate actions needed
                4. Red flags if any
                
                Keep response concise and actionable.
                """
            else:  # Gemini
                return f"""
                {base_clinical_context}
                
                Perform clinical triage with detailed reasoning:
                1. Risk stratification with rationale
                2. Differential diagnosis considerations
                3. Recommended diagnostic workup
                4. Disposition planning
                """
        
        elif analysis_type == AnalysisType.DIAGNOSTIC_REASONING:
            if provider == "gemini":  # Gemini optimized for complex reasoning
                return f"""
                {base_clinical_context}
                
                Provide comprehensive diagnostic reasoning:
                1. Systematic symptom analysis
                2. Differential diagnosis with probability ranking
                3. Supporting and contradicting evidence
                4. Recommended diagnostic tests with rationale
                5. Clinical decision-making process
                6. Risk factors and prognosis considerations
                
                Use clinical reasoning frameworks and evidence-based medicine.
                """
            else:  # Groq
                return f"""
                {base_clinical_context}
                
                Generate structured diagnostic analysis:
                1. Top 3 differential diagnoses
                2. Key clinical features supporting each
                3. Next diagnostic steps
                4. Risk stratification
                """
        
        elif analysis_type == AnalysisType.TREATMENT_PLANNING:
            return f"""
            {base_clinical_context}
            
            Develop evidence-based treatment plan:
            1. Primary treatment recommendations
            2. Alternative approaches
            3. Contraindications and precautions
            4. Monitoring parameters
            5. Patient education points
            6. Follow-up timeline
            """
        
        elif analysis_type == AnalysisType.EMERGENCY_ASSESSMENT:
            return f"""
            {base_clinical_context}
            
            URGENT: Emergency clinical assessment required:
            1. Immediate life threats (ABC assessment)
            2. Critical interventions needed NOW
            3. Emergency diagnostic priorities
            4. Stabilization measures
            5. Disposition (ED, ICU, ward, home)
            
            Focus on time-sensitive, life-saving interventions.
            """
        
        else:  # Default detailed analysis
            return f"""
            {base_clinical_context}
            
            Provide comprehensive clinical analysis:
            1. Clinical summary and key findings
            2. Assessment and diagnostic considerations
            3. Treatment recommendations
            4. Prognosis and risk factors
            5. Patient counseling points
            """
    
    async def fusion_analyze(
        self, 
        text: str, 
        analysis_type: AnalysisType = AnalysisType.DETAILED_ANALYSIS,
        urgency: str = "normal"
    ) -> FusionResult:
        """Perform Fusion AI analysis using optimal strategy"""
        
        strategy = self.get_optimal_strategy(analysis_type, len(text), urgency)
        logger.info(f"🔮 Fusion AI Strategy: {strategy}")
        
        start_time = time.time()
        
        if strategy == "speed_first":
            # Groq first for speed, Gemini for validation
            primary_result = await self.analyze_with_groq(text, analysis_type)
            secondary_result = None
            
            # If Groq is fast enough, get Gemini validation
            if primary_result and primary_result.processing_time < 2.0:
                secondary_result = await self.analyze_with_gemini(text, analysis_type)
            
        elif strategy == "accuracy_first":
            # Gemini first for accuracy, Groq for speed comparison
            primary_result = await self.analyze_with_gemini(text, analysis_type)
            secondary_result = await self.analyze_with_groq(text, analysis_type)
            
        elif strategy == "groq_only":
            # Fast triage with Groq only
            primary_result = await self.analyze_with_groq(text, analysis_type)
            secondary_result = None
            
        elif strategy == "parallel_consensus":
            # Run both providers in parallel for consensus
            results = await asyncio.gather(
                self.analyze_with_gemini(text, analysis_type),
                self.analyze_with_groq(text, analysis_type),
                return_exceptions=True
            )
            
            gemini_result, groq_result = results
            primary_result = gemini_result if isinstance(gemini_result, AnalysisResult) else None
            secondary_result = groq_result if isinstance(groq_result, AnalysisResult) else None
            
        else:  # gemini_primary (default)
            # Gemini as primary, Groq as fast backup
            primary_result = await self.analyze_with_gemini(text, analysis_type)
            if not primary_result:
                primary_result = await self.analyze_with_groq(text, analysis_type)
                secondary_result = None
            else:
                # Quick Groq analysis for comparison
                secondary_result = await self.analyze_with_groq(text, analysis_type)
        
        total_time = time.time() - start_time
        
        # Generate consensus analysis and recommendations
        consensus_analysis, confidence, recommendations = self._generate_consensus(
            primary_result, secondary_result, strategy, analysis_type
        )
        
        # Log to database if available
        if DATABASE_AVAILABLE:
            try:
                self._log_fusion_conversation(
                    input_text=text,
                    final_analysis=consensus_analysis,
                    confidence_score=confidence,
                    processing_time_total=total_time,
                    fusion_strategy=strategy,
                    primary_result=primary_result,
                    secondary_result=secondary_result,
                    analysis_type=analysis_type,
                    urgency=urgency
                )
            except Exception as e:
                logger.warning(f"Failed to log to database: {e}")
        
        return FusionResult(
            primary_result=primary_result,
            secondary_result=secondary_result,
            consensus_analysis=consensus_analysis,
            confidence_score=confidence,
            total_processing_time=total_time,
            fusion_strategy=strategy,
            recommendations=recommendations
        )
    
    def _generate_consensus(
        self, 
        primary: Optional[AnalysisResult], 
        secondary: Optional[AnalysisResult],
        strategy: str,
        analysis_type: AnalysisType
    ) -> Tuple[str, float, List[str]]:
        """Generate consensus analysis from multiple AI results"""
        
        if not primary:
            return "Analysis failed - no providers available", 0.0, ["Check API configuration"]
        
        if not secondary:
            # Single provider result
            return primary.response, primary.confidence_score, [
                f"Single provider analysis using {primary.provider}",
                f"Processing time: {primary.processing_time:.2f}s",
                f"Model: {primary.model}"
            ]
        
        # Dual provider consensus
        consensus_parts = []
        
        # Add provider comparison
        speed_winner = "Groq" if secondary.processing_time < primary.processing_time else "Gemini"
        consensus_parts.append(f"**🚀 FUSION AI ANALYSIS ({strategy.upper()})**")
        consensus_parts.append(f"Primary: {primary.provider} | Secondary: {secondary.provider}")
        consensus_parts.append(f"Speed Leader: {speed_winner} ({min(primary.processing_time, secondary.processing_time):.2f}s)")
        
        # Combine insights
        consensus_parts.append("\n**📋 CLINICAL ANALYSIS:**")
        consensus_parts.append(primary.response)
        
        if len(secondary.response) > 100:  # Add secondary insights if substantial
            consensus_parts.append(f"\n**⚡ RAPID VALIDATION ({secondary.provider}):**")
            consensus_parts.append(secondary.response[:300] + "..." if len(secondary.response) > 300 else secondary.response)
        
        # Calculate weighted confidence
        weight_primary = 0.7 if primary.provider == "gemini" else 0.6
        weight_secondary = 1.0 - weight_primary
        combined_confidence = (primary.confidence_score * weight_primary + 
                             secondary.confidence_score * weight_secondary)
        
        recommendations = [
            f"Fusion Strategy: {strategy}",
            f"Primary Analysis: {primary.provider} ({primary.processing_time:.2f}s)",
            f"Validation: {secondary.provider} ({secondary.processing_time:.2f}s)",
            f"Combined Confidence: {combined_confidence:.1%}",
            f"Total Tokens: {primary.tokens_used + secondary.tokens_used}"
        ]
        
        # Add strategy-specific recommendations
        if strategy == "parallel_consensus":
            recommendations.append("✅ Dual-provider consensus achieved")
        elif strategy == "speed_first":
            recommendations.append("⚡ Optimized for emergency response time")
        elif strategy == "accuracy_first":
            recommendations.append("🎯 Optimized for diagnostic accuracy")
        
        consensus_text = "\n".join(consensus_parts)
        
        return consensus_text, combined_confidence, recommendations
    
    def _log_fusion_conversation(
        self,
        input_text: str,
        final_analysis: str,
        confidence_score: float,
        processing_time_total: float,
        fusion_strategy: str,
        primary_result: Optional[AnalysisResult],
        secondary_result: Optional[AnalysisResult],
        analysis_type: AnalysisType,
        urgency: str = "normal"
    ) -> None:
        """Log fusion AI conversation to database"""
        try:
            # Convert analysis type to database enum
            db_analysis_type_map = {
                AnalysisType.QUICK_TRIAGE: DBAnalysisType.QUICK_TRIAGE,
                AnalysisType.EMERGENCY_ASSESSMENT: DBAnalysisType.EMERGENCY_ASSESSMENT,
                AnalysisType.DIAGNOSTIC_REASONING: DBAnalysisType.DIAGNOSTIC_REASONING,
                AnalysisType.TREATMENT_PLANNING: DBAnalysisType.TREATMENT_PLANNING,
                AnalysisType.DETAILED_ANALYSIS: DBAnalysisType.DETAILED_ANALYSIS,
                AnalysisType.RESEARCH_ANALYSIS: DBAnalysisType.GENERAL
            }
            
            # Convert urgency to database enum
            urgency_map = {
                "emergency": UrgencyLevel.EMERGENCY,
                "urgent": UrgencyLevel.URGENT,
                "normal": UrgencyLevel.NORMAL,
                "routine": UrgencyLevel.ROUTINE
            }
            
            # Convert fusion strategy
            strategy_map = {
                "speed_first": FusionStrategy.SPEED_FIRST,
                "accuracy_first": FusionStrategy.ACCURACY_FIRST,
                "parallel_consensus": FusionStrategy.PARALLEL_CONSENSUS
            }
            
            # Prepare provider responses for database
            gemini_response = None
            groq_response = None
            primary_provider_type = None
            
            if primary_result:
                if primary_result.provider == "gemini":
                    primary_provider_type = ProviderType.GOOGLE_GEMINI
                    gemini_response = {
                        "model_name": primary_result.model,
                        "request_payload": {"text": input_text, "analysis_type": analysis_type.value},
                        "response_text": primary_result.response,
                        "processing_time": primary_result.processing_time,
                        "success": True,
                        "tokens_input": getattr(primary_result, 'tokens_input', None),
                        "tokens_output": getattr(primary_result, 'tokens_output', None),
                        "response_metadata": {"confidence": primary_result.confidence_score}
                    }
                elif primary_result.provider == "groq":
                    primary_provider_type = ProviderType.GROQ
                    groq_response = {
                        "model_name": primary_result.model,
                        "request_payload": {"text": input_text, "analysis_type": analysis_type.value},
                        "response_text": primary_result.response,
                        "processing_time": primary_result.processing_time,
                        "success": True,
                        "tokens_input": getattr(primary_result, 'tokens_input', None),
                        "tokens_output": getattr(primary_result, 'tokens_output', None),
                        "response_metadata": {"confidence": primary_result.confidence_score}
                    }
            
            if secondary_result:
                if secondary_result.provider == "gemini" and not gemini_response:
                    gemini_response = {
                        "model_name": secondary_result.model,
                        "request_payload": {"text": input_text, "analysis_type": analysis_type.value},
                        "response_text": secondary_result.response,
                        "processing_time": secondary_result.processing_time,
                        "success": True,
                        "tokens_input": getattr(secondary_result, 'tokens_input', None),
                        "tokens_output": getattr(secondary_result, 'tokens_output', None),
                        "response_metadata": {"confidence": secondary_result.confidence_score}
                    }
                elif secondary_result.provider == "groq" and not groq_response:
                    groq_response = {
                        "model_name": secondary_result.model,
                        "request_payload": {"text": input_text, "analysis_type": analysis_type.value},
                        "response_text": secondary_result.response,
                        "processing_time": secondary_result.processing_time,
                        "success": True,
                        "tokens_input": getattr(secondary_result, 'tokens_input', None),
                        "tokens_output": getattr(secondary_result, 'tokens_output', None),
                        "response_metadata": {"confidence": secondary_result.confidence_score}
                    }
            
            # Log to database
            conversation_id = log_fusion_conversation(
                input_text=input_text,
                final_analysis=final_analysis,
                confidence_score=confidence_score,
                processing_time_total=processing_time_total,
                fusion_strategy=strategy_map.get(fusion_strategy, FusionStrategy.SPEED_FIRST),
                primary_provider=primary_provider_type or ProviderType.FUSION,
                gemini_response=gemini_response,
                groq_response=groq_response,
                analysis_type=db_analysis_type_map.get(analysis_type, DBAnalysisType.GENERAL),
                urgency_level=urgency_map.get(urgency, UrgencyLevel.NORMAL)
            )
            
            logger.info(f"📝 Fusion conversation logged to database: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to log fusion conversation to database: {e}")

# Convenience functions for easy integration
async def quick_triage(text: str) -> FusionResult:
    """Quick clinical triage using Fusion AI"""
    engine = FusionAIEngine()
    return await engine.fusion_analyze(text, AnalysisType.QUICK_TRIAGE, urgency="normal")

async def emergency_assessment(text: str) -> FusionResult:
    """Emergency clinical assessment using Fusion AI"""
    engine = FusionAIEngine()
    return await engine.fusion_analyze(text, AnalysisType.EMERGENCY_ASSESSMENT, urgency="emergency")

async def diagnostic_reasoning(text: str) -> FusionResult:
    """Detailed diagnostic reasoning using Fusion AI"""
    engine = FusionAIEngine()
    return await engine.fusion_analyze(text, AnalysisType.DIAGNOSTIC_REASONING)

async def treatment_planning(text: str) -> FusionResult:
    """Treatment planning using Fusion AI"""
    engine = FusionAIEngine()
    return await engine.fusion_analyze(text, AnalysisType.TREATMENT_PLANNING)

# Main execution for testing
async def main():
    """Test Fusion AI capabilities"""
    print("🚀 Testing Fusion AI Engine")
    print("=" * 50)
    
    # Test case
    clinical_text = """
    Patient: 67-year-old male with history of hypertension and diabetes
    Chief Complaint: Severe chest pain for 2 hours, radiating to left arm
    Vitals: BP 180/100, HR 110, O2Sat 92% on room air
    Physical: Diaphoretic, anxious, S3 gallop heard
    ECG: ST elevations in leads II, III, aVF
    Labs: Troponin I elevated at 15.2 ng/mL (normal <0.04)
    """
    
    # Test different analysis types
    test_cases = [
        (AnalysisType.QUICK_TRIAGE, "normal"),
        (AnalysisType.EMERGENCY_ASSESSMENT, "emergency"),
        (AnalysisType.DIAGNOSTIC_REASONING, "normal")
    ]
    
    engine = FusionAIEngine()
    
    for analysis_type, urgency in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {analysis_type.value} (Urgency: {urgency})")
        print(f"{'='*60}")
        
        result = await engine.fusion_analyze(clinical_text, analysis_type, urgency)
        
        print(f"Strategy Used: {result.fusion_strategy}")
        print(f"Total Time: {result.total_processing_time:.2f}s")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"\nAnalysis:\n{result.consensus_analysis[:500]}...")
        print(f"\nRecommendations:")
        for rec in result.recommendations:
            print(f"  • {rec}")

if __name__ == "__main__":
    asyncio.run(main())