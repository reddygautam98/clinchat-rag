#!/usr/bin/env python3
"""
Anthropic Claude Configuration Test Script
Test the Fusion AI technology setup for ClinChat-RAG system.
"""

import os
from dotenv import load_dotenv
import anthropic
import sys

def test_anthropic_config():
    """Test Anthropic Claude configuration and connectivity."""
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 Testing Fusion AI Technology (Anthropic Claude)")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key.startswith('your_'):
        print("❌ ANTHROPIC_API_KEY: Not configured")
        print("⚠️  Please set your Anthropic API key in the .env file")
        return False
    else:
        # Mask the API key for security
        masked_key = api_key[:7] + "..." + api_key[-4:]
        print(f"✅ ANTHROPIC_API_KEY: {masked_key}")
    
    # Check other settings
    model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    max_tokens = os.getenv('ANTHROPIC_MAX_TOKENS', '4000')
    temperature = os.getenv('ANTHROPIC_TEMPERATURE', '0.1')
    provider = os.getenv('LLM_PROVIDER', 'anthropic')
    
    print(f"✅ LLM_PROVIDER: {provider}")
    print(f"✅ ANTHROPIC_MODEL: {model}")
    print(f"✅ ANTHROPIC_MAX_TOKENS: {max_tokens}")
    print(f"✅ ANTHROPIC_TEMPERATURE: {temperature}")
    
    # Test connection
    print("\n🔗 Testing Anthropic Claude Connection...")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test basic chat completion
        print("📝 Testing Basic AI Response...")
        response = client.messages.create(
            model=model,
            max_tokens=int(max_tokens),
            temperature=float(temperature),
            messages=[
                {"role": "user", "content": "Hello! This is a test for the ClinChat-RAG system. Please respond briefly."}
            ]
        )
        
        basic_response = response.content[0].text
        print(f"✅ Basic Response: {basic_response}")
        
        # Test clinical document analysis
        print("🏥 Testing Clinical Document Analysis...")
        clinical_test = client.messages.create(
            model=model,
            max_tokens=500,
            temperature=0.1,
            system="You are a specialized clinical document AI assistant with expertise in pharmaceutical research, clinical trials, and regulatory compliance. You help analyze clinical documents, protocols, and research data.",
            messages=[
                {"role": "user", "content": "What are the key components that must be included in a clinical trial protocol according to ICH-GCP guidelines?"}
            ]
        )
        
        clinical_response = clinical_test.content[0].text
        print(f"✅ Clinical Analysis: {clinical_response[:200]}...")
        
        # Test document processing capability
        print("📋 Testing Document Processing...")
        doc_test = client.messages.create(
            model=model,
            max_tokens=300,
            temperature=0.1,
            system="You are analyzing clinical documents. Provide structured, precise responses for regulatory compliance.",
            messages=[
                {"role": "user", "content": "Given this sample adverse event data: 'Patient reported headache (Grade 2, possibly related to study drug, resolved after 3 days)', extract the key safety information in a structured format."}
            ]
        )
        
        doc_response = doc_test.content[0].text
        print(f"✅ Document Processing: {doc_response[:150]}...")
        
        # Test reasoning capability
        print("🧠 Testing Advanced Reasoning...")
        reasoning_test = client.messages.create(
            model=model,
            max_tokens=400,
            temperature=0.1,
            system="You are a clinical research AI that helps with complex analysis and decision-making in pharmaceutical development.",
            messages=[
                {"role": "user", "content": "If a Phase II oncology trial shows 30% response rate with 95% CI [18%-45%] in 50 patients, what are the key considerations for proceeding to Phase III?"}
            ]
        )
        
        reasoning_response = reasoning_test.content[0].text
        print(f"✅ Advanced Reasoning: {reasoning_response[:150]}...")
        
        print("\n🎉 Fusion AI Technology Test: PASSED")
        print("Your ClinChat-RAG system is ready with Claude!")
        return True
        
    except Exception as e:
        print(f"❌ Connection Test Failed: {str(e)}")
        print("\nTroubleshooting Tips:")
        print("1. Verify your Anthropic API key is correct")
        print("2. Check your internet connection")
        print("3. Ensure you have sufficient API credits")
        print("4. Confirm the model name is correct")
        return False

def show_fusion_ai_benefits():
    """Show the benefits of using Fusion AI (Claude) for clinical applications."""
    print("\n💡 Fusion AI Technology Benefits:")
    print("━" * 60)
    print("• 🎯 Superior reasoning for complex clinical scenarios")
    print("• 📚 Excellent at analyzing long clinical documents")
    print("• 🔬 Strong performance on scientific and medical content")
    print("• ⚡ Fast response times for real-time analysis")
    print("• 🛡️ Built-in safety measures for healthcare applications")
    print("• 📊 Excellent at structured data extraction")
    print("• 🔍 Advanced pattern recognition in clinical data")
    print("• 💬 Natural conversation flow for user interactions")

def show_clinical_use_cases():
    """Show specific clinical use cases for Fusion AI."""
    print("\n🏥 Clinical Use Cases:")
    print("━" * 60)
    print("• Protocol Analysis: Extract inclusion/exclusion criteria")
    print("• Safety Monitoring: Analyze adverse event patterns")  
    print("• Regulatory Review: Check compliance requirements")
    print("• Data Extraction: Structure unstructured clinical data")
    print("• Literature Review: Summarize research findings")
    print("• Risk Assessment: Evaluate clinical trial risks")
    print("• Statistical Analysis: Interpret clinical results")
    print("• Regulatory Submissions: Prepare documentation")

if __name__ == "__main__":
    print("🚀 ClinChat-RAG Fusion AI Technology Test")
    print("=" * 60)
    
    success = test_anthropic_config()
    
    if success:
        show_fusion_ai_benefits()
        show_clinical_use_cases()
        print("\n✅ Fusion AI Technology is ready for ClinChat-RAG!")
        print("🎯 Your system now uses Claude's advanced capabilities for clinical document analysis.")
        sys.exit(0)
    else:
        print("\n❌ Fusion AI configuration test failed. Please check your setup.")
        sys.exit(1)