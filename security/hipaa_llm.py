"""
HIPAA-Compliant LLM Solutions for ClinChat-RAG
Implements secure LLM hosting and PHI-safe API endpoints
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import requests
import asyncio

# For on-premises hosting
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class LLMConfig:
    """Configuration for HIPAA-compliant LLM setup"""
    provider: str  # "on_premises", "azure_openai", "aws_bedrock", "google_vertex"
    
    # Model settings
    model_name: str
    model_path: Optional[str] = None  # For on-premises models
    
    # API settings
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    deployment_id: Optional[str] = None  # For Azure OpenAI
    
    # Security settings
    phi_filtering_enabled: bool = True
    audit_logging_enabled: bool = True
    data_residency_region: str = "us-east-1"
    
    # Performance settings
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout_seconds: int = 30
    
    # HIPAA compliance
    baa_signed: bool = False  # Business Associate Agreement
    hipaa_compliant_endpoint: bool = False
    phi_masking_enabled: bool = True

class PHIMaskingLevel(Enum):
    """Levels of PHI masking for different use cases"""
    NONE = "none"  # No masking (only for BAA-covered endpoints)
    BASIC = "basic"  # Mask obvious PHI (SSN, phone, etc.)
    AGGRESSIVE = "aggressive"  # Mask all potential PHI
    SYNTHETIC = "synthetic"  # Replace with synthetic data

class ComplianceStatus(Enum):
    """Compliance status for LLM endpoints"""
    HIPAA_COMPLIANT = "hipaa_compliant"
    BAA_REQUIRED = "baa_required"
    NOT_COMPLIANT = "not_compliant"
    ON_PREMISES = "on_premises"

@dataclass
class PHIDetectionResult:
    """Result of PHI detection scan"""
    phi_detected: bool
    phi_types: List[str]  # Types of PHI found
    confidence_scores: Dict[str, float]
    masked_content: str
    risk_level: str  # "low", "medium", "high", "critical"

class PHIScanner:
    """Advanced PHI detection and masking system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced PHI patterns
        self.phi_patterns = {
            "ssn": [
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
                r'\b\d{9}\b'
            ],
            "phone": [
                r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b',
                r'\(\d{3}\)\s?\d{3}[-\.\s]?\d{4}'
            ],
            "email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            "medical_record": [
                r'\bMRN\s*:?\s*\d+\b',
                r'\bMedical Record\s*:?\s*\d+\b',
                r'\bPatient ID\s*:?\s*\d+\b'
            ],
            "date_of_birth": [
                r'\bDOB\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
                r'\bDate of Birth\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
            ],
            "address": [
                r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b'
            ],
            "insurance": [
                r'\bInsurance\s*:?\s*\d+\b',
                r'\bPolicy\s*:?\s*\d+\b'
            ]
        }
        
        # Medical context patterns that might contain PHI
        self.medical_contexts = [
            "patient", "diagnosis", "prescription", "treatment", "surgery",
            "admission", "discharge", "allergic", "medication", "dose"
        ]
    
    def scan_content(self, content: str, masking_level: PHIMaskingLevel = PHIMaskingLevel.BASIC) -> PHIDetectionResult:
        """Scan content for PHI and apply masking"""
        import re
        
        phi_found = {}
        confidence_scores = {}
        masked_content = content
        
        # Scan for each PHI type
        for phi_type, patterns in self.phi_patterns.items():
            matches = []
            max_confidence = 0.0
            
            for pattern in patterns:
                pattern_matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in pattern_matches:
                    matches.append(match)
                    # Higher confidence for exact matches
                    confidence = 0.9 if match.group() else 0.7
                    max_confidence = max(max_confidence, confidence)
            
            if matches:
                phi_found[phi_type] = [match.group() for match in matches]
                confidence_scores[phi_type] = max_confidence
                
                # Apply masking based on level
                if masking_level != PHIMaskingLevel.NONE:
                    for match in matches:
                        masked_content = self._mask_phi(masked_content, match, phi_type, masking_level)
        
        # Check for medical context that might indicate PHI
        medical_context_score = self._assess_medical_context(content)
        if medical_context_score > 0.7:
            confidence_scores["medical_context"] = medical_context_score
        
        # Determine overall risk level
        risk_level = self._calculate_risk_level(phi_found, confidence_scores, medical_context_score)
        
        return PHIDetectionResult(
            phi_detected=len(phi_found) > 0,
            phi_types=list(phi_found.keys()),
            confidence_scores=confidence_scores,
            masked_content=masked_content,
            risk_level=risk_level
        )
    
    def _mask_phi(self, content: str, match, phi_type: str, masking_level: PHIMaskingLevel) -> str:
        """Apply PHI masking based on level"""
        original = match.group()
        
        if masking_level == PHIMaskingLevel.BASIC:
            if phi_type == "ssn":
                masked = f"***-**-{original[-4:]}"
            elif phi_type == "phone":
                masked = f"***-***-{original[-4:]}"
            elif phi_type == "email":
                parts = original.split('@')
                masked = f"***@{parts[1]}" if len(parts) > 1 else "***@***.com"
            else:
                masked = "***"
        
        elif masking_level == PHIMaskingLevel.AGGRESSIVE:
            masked = "[REDACTED]"
        
        elif masking_level == PHIMaskingLevel.SYNTHETIC:
            masked = self._generate_synthetic_replacement(phi_type)
        
        else:
            masked = original
        
        return content.replace(original, masked)
    
    def _generate_synthetic_replacement(self, phi_type: str) -> str:
        """Generate synthetic replacement data"""
        import random
        
        if phi_type == "ssn":
            return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        elif phi_type == "phone":
            return f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        elif phi_type == "email":
            return "example@example.com"
        elif phi_type == "medical_record":
            return f"MRN: {random.randint(100000,999999)}"
        else:
            return "[SYNTHETIC_DATA]"
    
    def _assess_medical_context(self, content: str) -> float:
        """Assess likelihood of medical context containing PHI"""
        content_lower = content.lower()
        context_matches = sum(1 for context in self.medical_contexts if context in content_lower)
        return min(context_matches / len(self.medical_contexts), 1.0)
    
    def _calculate_risk_level(self, phi_found: Dict, confidence_scores: Dict, medical_context_score: float) -> str:
        """Calculate overall PHI risk level"""
        if not phi_found and medical_context_score < 0.3:
            return "low"
        
        high_risk_phi = ["ssn", "medical_record", "date_of_birth"]
        if any(phi_type in phi_found for phi_type in high_risk_phi):
            return "critical"
        
        if len(phi_found) > 3 or medical_context_score > 0.8:
            return "high"
        elif len(phi_found) > 0 or medical_context_score > 0.5:
            return "medium"
        else:
            return "low"

class OnPremisesLLM:
    """On-premises LLM hosting for maximum security"""
    
    def __init__(self, config: LLMConfig):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not installed for on-premises hosting")
        
        self.config = config
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.phi_scanner = PHIScanner()
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """Initialize on-premises model"""
        try:
            self.logger.info(f"Loading on-premises model: {self.config.model_name}")
            
            # Load tokenizer and model
            if self.config.model_path:
                # Load from local path
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_path)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_path,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            else:
                # Load from HuggingFace Hub
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.logger.info("On-premises model initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize on-premises model: {e}")
            return False
    
    async def generate_response(self, prompt: str, user_id: str, 
                              session_id: str) -> Dict[str, Any]:
        """Generate response with PHI protection"""
        try:
            start_time = time.time()
            
            # Scan input for PHI
            phi_scan = self.phi_scanner.scan_content(
                prompt, 
                PHIMaskingLevel.AGGRESSIVE if self.config.phi_masking_enabled else PHIMaskingLevel.NONE
            )
            
            if phi_scan.phi_detected and phi_scan.risk_level in ["high", "critical"]:
                return {
                    "response": "I cannot process requests containing protected health information (PHI). Please remove any personal identifiers and try again.",
                    "phi_detected": True,
                    "risk_level": phi_scan.risk_level,
                    "processing_time": time.time() - start_time
                }
            
            # Use masked prompt for generation
            safe_prompt = phi_scan.masked_content
            
            # Generate response
            generated = self.pipeline(
                safe_prompt,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                num_return_sequences=1,
                truncation=True
            )
            
            response_text = generated[0]['generated_text']
            
            # Remove the original prompt from response
            if response_text.startswith(safe_prompt):
                response_text = response_text[len(safe_prompt):].strip()
            
            # Scan output for PHI
            output_scan = self.phi_scanner.scan_content(response_text, PHIMaskingLevel.BASIC)
            
            # Log for audit
            if self.config.audit_logging_enabled:
                self._log_llm_usage(user_id, session_id, phi_scan, output_scan, time.time() - start_time)
            
            return {
                "response": output_scan.masked_content,
                "phi_detected": phi_scan.phi_detected,
                "risk_level": phi_scan.risk_level,
                "processing_time": time.time() - start_time,
                "model": self.config.model_name,
                "compliance_status": ComplianceStatus.ON_PREMISES.value
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            return {
                "error": "Failed to generate response",
                "details": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _log_llm_usage(self, user_id: str, session_id: str, input_scan: PHIDetectionResult, 
                      output_scan: PHIDetectionResult, processing_time: float):
        """Log LLM usage for audit purposes"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "model": self.config.model_name,
            "input_phi_detected": input_scan.phi_detected,
            "input_risk_level": input_scan.risk_level,
            "output_phi_detected": output_scan.phi_detected,
            "processing_time": processing_time,
            "compliance_status": ComplianceStatus.ON_PREMISES.value
        }
        
        self.logger.info(f"LLM_AUDIT: {json.dumps(audit_entry)}")

class AzureOpenAISecure:
    """HIPAA-compliant Azure OpenAI implementation"""
    
    def __init__(self, config: LLMConfig):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed for Azure OpenAI")
        
        self.config = config
        self.phi_scanner = PHIScanner()
        self.logger = logging.getLogger(__name__)
        
        # Configure OpenAI for Azure
        openai.api_type = "azure"
        openai.api_base = config.api_endpoint
        openai.api_version = "2023-12-01-preview"
        openai.api_key = config.api_key
    
    async def generate_response(self, prompt: str, user_id: str, 
                              session_id: str) -> Dict[str, Any]:
        """Generate response using Azure OpenAI with PHI protection"""
        try:
            start_time = time.time()
            
            # Verify BAA is signed for PHI processing
            if not self.config.baa_signed:
                phi_scan = self.phi_scanner.scan_content(prompt, PHIMaskingLevel.AGGRESSIVE)
                if phi_scan.phi_detected:
                    return {
                        "error": "PHI detected but no BAA signed with Azure OpenAI",
                        "phi_detected": True,
                        "compliance_status": ComplianceStatus.BAA_REQUIRED.value
                    }
            else:
                # Light scanning if BAA is signed
                phi_scan = self.phi_scanner.scan_content(prompt, PHIMaskingLevel.BASIC)
            
            # Generate response
            response = await openai.ChatCompletion.acreate(
                engine=self.config.deployment_id,
                messages=[
                    {"role": "system", "content": "You are a medical AI assistant. Always include appropriate medical disclaimers."},
                    {"role": "user", "content": phi_scan.masked_content}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout_seconds
            )
            
            response_text = response.choices[0].message.content
            
            # Scan output
            output_scan = self.phi_scanner.scan_content(response_text, PHIMaskingLevel.BASIC)
            
            # Log for audit
            if self.config.audit_logging_enabled:
                self._log_azure_usage(user_id, session_id, phi_scan, output_scan, time.time() - start_time)
            
            return {
                "response": output_scan.masked_content,
                "phi_detected": phi_scan.phi_detected,
                "risk_level": phi_scan.risk_level,
                "processing_time": time.time() - start_time,
                "model": self.config.deployment_id,
                "compliance_status": ComplianceStatus.HIPAA_COMPLIANT.value if self.config.baa_signed else ComplianceStatus.BAA_REQUIRED.value
            }
            
        except Exception as e:
            self.logger.error(f"Azure OpenAI request failed: {e}")
            return {
                "error": "Failed to generate response via Azure OpenAI",
                "details": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _log_azure_usage(self, user_id: str, session_id: str, input_scan: PHIDetectionResult,
                        output_scan: PHIDetectionResult, processing_time: float):
        """Log Azure OpenAI usage for audit"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "azure_openai",
            "user_id": user_id,
            "session_id": session_id,
            "deployment_id": self.config.deployment_id,
            "baa_signed": self.config.baa_signed,
            "input_phi_detected": input_scan.phi_detected,
            "input_risk_level": input_scan.risk_level,
            "output_phi_detected": output_scan.phi_detected,
            "processing_time": processing_time
        }
        
        self.logger.info(f"AZURE_LLM_AUDIT: {json.dumps(audit_entry)}")

class ComplianceLLMManager:
    """Manager for HIPAA-compliant LLM operations"""
    
    def __init__(self):
        self.llm_providers = {}
        self.phi_scanner = PHIScanner()
        self.logger = logging.getLogger(__name__)
    
    def register_llm(self, name: str, config: LLMConfig) -> bool:
        """Register an LLM provider"""
        try:
            if config.provider == "on_premises":
                provider = OnPremisesLLM(config)
                if provider.initialize():
                    self.llm_providers[name] = provider
                    return True
            
            elif config.provider == "azure_openai":
                provider = AzureOpenAISecure(config)
                self.llm_providers[name] = provider
                return True
            
            else:
                self.logger.error(f"Unsupported LLM provider: {config.provider}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to register LLM {name}: {e}")
            return False
        
        return False
    
    async def get_response(self, prompt: str, user_id: str, session_id: str,
                          preferred_provider: str = None) -> Dict[str, Any]:
        """Get response from most appropriate LLM provider"""
        # Quick PHI scan to determine best provider
        phi_scan = self.phi_scanner.scan_content(prompt, PHIMaskingLevel.NONE)
        
        # Select provider based on PHI content and availability
        if phi_scan.risk_level in ["high", "critical"]:
            # Use on-premises for high-risk PHI
            provider_priority = ["on_premises", "azure_openai_baa"]
        else:
            # Use any compliant provider
            provider_priority = [preferred_provider] if preferred_provider else list(self.llm_providers.keys())
        
        for provider_name in provider_priority:
            if provider_name in self.llm_providers:
                try:
                    provider = self.llm_providers[provider_name]
                    response = await provider.generate_response(prompt, user_id, session_id)
                    response["provider_used"] = provider_name
                    return response
                except Exception as e:
                    self.logger.warning(f"Provider {provider_name} failed: {e}")
                    continue
        
        return {
            "error": "No compliant LLM providers available",
            "phi_risk_level": phi_scan.risk_level
        }
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status for all registered providers"""
        status = {
            "total_providers": len(self.llm_providers),
            "providers": {}
        }
        
        for name, provider in self.llm_providers.items():
            if hasattr(provider, 'config'):
                config = provider.config
                status["providers"][name] = {
                    "provider_type": config.provider,
                    "model": config.model_name,
                    "baa_signed": getattr(config, 'baa_signed', False),
                    "hipaa_compliant": getattr(config, 'hipaa_compliant_endpoint', False),
                    "phi_masking_enabled": config.phi_masking_enabled,
                    "compliance_status": self._get_provider_compliance_status(config)
                }
        
        return status
    
    def _get_provider_compliance_status(self, config: LLMConfig) -> str:
        """Determine compliance status for a provider"""
        if config.provider == "on_premises":
            return ComplianceStatus.ON_PREMISES.value
        elif config.baa_signed and config.hipaa_compliant_endpoint:
            return ComplianceStatus.HIPAA_COMPLIANT.value
        elif config.baa_signed:
            return ComplianceStatus.BAA_REQUIRED.value
        else:
            return ComplianceStatus.NOT_COMPLIANT.value

# Configuration examples
ON_PREMISES_CONFIG = LLMConfig(
    provider="on_premises",
    model_name="microsoft/DialoGPT-medium",
    model_path="/opt/clinchat/models/medical-llm",
    phi_filtering_enabled=True,
    audit_logging_enabled=True,
    phi_masking_enabled=True,
    max_tokens=500,
    temperature=0.1
)

AZURE_OPENAI_CONFIG = LLMConfig(
    provider="azure_openai",
    model_name="gpt-35-turbo",
    api_endpoint="https://your-resource.openai.azure.com/",
    deployment_id="gpt-35-turbo-deployment",
    baa_signed=True,
    hipaa_compliant_endpoint=True,
    phi_filtering_enabled=True,
    audit_logging_enabled=True,
    phi_masking_enabled=True
)

# Global manager instance
compliance_llm_manager = ComplianceLLMManager()

# Export main components
__all__ = [
    'ComplianceLLMManager',
    'LLMConfig',
    'PHIScanner',
    'OnPremisesLLM',
    'AzureOpenAISecure',
    'PHIMaskingLevel',
    'ComplianceStatus',
    'ON_PREMISES_CONFIG',
    'AZURE_OPENAI_CONFIG',
    'compliance_llm_manager'
]