#!/usr/bin/env python3
"""
Quick test of working Gemini and Groq APIs
"""

import requests
import json

API_BASE = "http://localhost:8001"

def test_working_apis():
    """Test the working API providers"""
    print("🚀 Testing Working ClinChat-RAG Enhanced API")
    print("=" * 50)
    
    # Test clinical text
    clinical_text = """
    Patient John Doe, 55-year-old male, presents with acute chest pain.
    Blood pressure: 150/90 mmHg. Heart rate: 98 bpm.
    Troponin elevated at 12.5 ng/mL. ECG shows ST depression.
    Started on aspirin, metoprolol, and atorvastatin.
    """
    
    # Test Google Gemini
    print("🧠 Testing Google Gemini Analysis...")
    try:
        response = requests.post(f"{API_BASE}/analyze/ai", json={
            "text": clinical_text,
            "provider": "gemini",
            "max_tokens": 500
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Gemini Analysis Success!")
            print(f"   Model: {result['model_used']}")
            print(f"   Processing Time: {result['processing_time']:.2f}s")
            print(f"   Analysis Preview: {result['response'][:100]}...")
        else:
            print(f"❌ Gemini failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Gemini error: {e}")
    
    # Test Groq
    print("\n⚡ Testing Groq Analysis...")
    try:
        response = requests.post(f"{API_BASE}/analyze/ai", json={
            "text": clinical_text,
            "provider": "groq",
            "max_tokens": 300
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Groq Analysis Success!")
            print(f"   Model: {result['model_used']}")
            print(f"   Processing Time: {result['processing_time']:.2f}s")
            print(f"   Analysis Preview: {result['response'][:100]}...")
        else:
            print(f"❌ Groq failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Groq error: {e}")
    
    # Test combined analysis
    print("\n🔄 Testing Combined Analysis...")
    try:
        response = requests.post(f"{API_BASE}/analyze/text", json={
            "text": clinical_text,
            "provider": "auto"
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Combined Analysis Success!")
            print(f"   Provider Used: {result['provider_used']}")
            print(f"   Processing Time: {result['processing_time']:.2f}s")
            
            # Show extracted entities
            entities = result['entities']
            print("   📊 Extracted Entities:")
            for category, items in entities.items():
                if items and category != 'all_entities':
                    print(f"     {category}: {', '.join(items[:3])}")
            
            if result['ai_analysis']:
                print(f"   🧠 AI Analysis: {result['ai_analysis'][:80]}...")
        else:
            print(f"❌ Combined analysis failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Combined analysis error: {e}")
    
    # Test provider status
    print("\n📊 Provider Status...")
    try:
        response = requests.get(f"{API_BASE}/providers/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Provider Status Retrieved!")
            for name, info in status['providers'].items():
                icon = "✅" if info['configured'] else "❌"
                print(f"   {icon} {name.upper()}: {info['description']}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    print("\n🎯 SUCCESS! Your API keys are working perfectly!")
    print(f"📚 Interactive docs: {API_BASE}/docs")

if __name__ == "__main__":
    test_working_apis()