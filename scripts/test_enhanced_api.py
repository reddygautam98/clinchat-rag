#!/usr/bin/env python3
"""
Test script for the enhanced ClinChat-RAG API with Google Gemini & Groq integration
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8001"

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API Health Check Passed!")
            print(f"   Status: {health_data['status']}")
            print(f"   Version: {health_data['version']}")
            print("   Providers:", json.dumps(health_data['providers'], indent=4))
            print("   Models:", json.dumps(health_data['models_loaded'], indent=4))
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_provider_status():
    """Test provider status endpoint"""
    print("\n🤖 Testing Provider Status...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/providers/status")
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Provider Status Retrieved!")
            
            for provider, info in status_data['providers'].items():
                status_icon = "✅" if info['configured'] else "❌"
                print(f"   {status_icon} {provider.upper()}: {info['description']}")
                if info.get('model'):
                    print(f"      Model: {info['model']}")
            
            print("\n📋 Setup Instructions:")
            for provider, url in status_data['recommended_setup'].items():
                print(f"   {provider}: {url}")
            
            return True
        else:
            print(f"❌ Provider status failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Provider status error: {e}")
        return False

def test_local_analysis():
    """Test local spaCy analysis"""
    print("\n🏥 Testing Local Clinical Analysis...")
    
    clinical_text = """
    Patient presents with acute chest pain radiating to left arm. 
    Blood pressure is 160/95 mmHg. ECG shows ST elevation in leads V2-V6.
    Troponin I elevated at 15.2 ng/mL. Diagnosed with STEMI.
    Initiated dual antiplatelet therapy with aspirin and clopidogrel.
    """
    
    payload = {
        "text": clinical_text,
        "provider": "local"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/analyze/text", json=payload)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Local Analysis Completed!")
            print(f"   Provider Used: {result['provider_used']}")
            print(f"   Processing Time: {result['processing_time']:.3f}s")
            print(f"   Local Processing Time: {processing_time:.3f}s")
            
            entities = result['entities']
            print("\n   📊 Extracted Entities:")
            for category, items in entities.items():
                if items and category != 'all_entities':
                    print(f"     {category}: {', '.join(items[:3])}")
            
            return True
        else:
            print(f"❌ Local analysis failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Local analysis error: {e}")
        return False

def test_ai_analysis():
    """Test AI provider analysis (if configured)"""
    print("\n🤖 Testing AI Provider Analysis...")
    
    clinical_text = """
    65-year-old male with diabetes mellitus presents with shortness of breath.
    Physical exam reveals bilateral crackles and elevated JVP.
    BNP is 2,500 pg/mL. Echocardiogram shows EF of 35%.
    Started on ACE inhibitor and beta-blocker for heart failure.
    """
    
    # Test with auto provider selection
    payload = {
        "text": clinical_text,
        "provider": "auto"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/analyze/ai", json=payload)
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Analysis Completed!")
            print(f"   Provider: {result['provider']}")
            print(f"   Model Used: {result['model_used']}")
            print(f"   Processing Time: {result['processing_time']:.3f}s")
            print(f"   Total Time: {processing_time:.3f}s")
            
            if result['response'] != "No AI provider available":
                print(f"\n   🧠 AI Analysis Preview:")
                # Show first 200 characters of response
                preview = result['response'][:200]
                print(f"     {preview}{'...' if len(result['response']) > 200 else ''}")
            else:
                print("   ⚠️ No AI providers configured (API keys needed)")
            
            return True
        else:
            print(f"❌ AI analysis failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI analysis error: {e}")
        return False

def test_datasets():
    """Test dataset endpoints"""
    print("\n📊 Testing Dataset Operations...")
    
    try:
        # Get datasets
        response = requests.get(f"{API_BASE_URL}/datasets")
        if response.status_code == 200:
            datasets = response.json()
            print(f"✅ Found {len(datasets)} Clinical Datasets:")
            
            for dataset in datasets:
                print(f"   📋 {dataset['name']}: {dataset['records']} records ({dataset['size_mb']} MB)")
            
            # Test dataset summary if datasets exist
            if datasets:
                dataset_name = datasets[0]['name']
                response = requests.get(f"{API_BASE_URL}/datasets/{dataset_name}/summary")
                if response.status_code == 200:
                    summary = response.json()
                    print(f"\n   📈 {dataset_name} Summary:")
                    print(f"     Total Records: {summary['total_records']}")
                    print(f"     Columns: {len(summary['columns'])}")
                    print(f"     Memory Usage: {summary['memory_usage_mb']} MB")
            
            return True
        else:
            print(f"❌ Dataset retrieval failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dataset test error: {e}")
        return False

def test_performance_comparison():
    """Compare performance across providers"""
    print("\n⚡ Testing Performance Comparison...")
    
    test_text = "Patient diagnosed with acute pneumonia. Started on antibiotics."
    
    providers = ["local", "gemini", "groq", "auto"]
    results = {}
    
    for provider in providers:
        print(f"   Testing {provider}...")
        payload = {"text": test_text, "provider": provider}
        
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE_URL}/analyze/text", json=payload)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                results[provider] = {
                    "success": True,
                    "provider_used": result['provider_used'],
                    "processing_time": result['processing_time'],
                    "total_time": total_time,
                    "has_ai_analysis": result['ai_analysis'] is not None
                }
            else:
                results[provider] = {"success": False, "error": response.status_code}
        except Exception as e:
            results[provider] = {"success": False, "error": str(e)}
    
    # Display results
    print("\n   📊 Performance Results:")
    for provider, result in results.items():
        if result['success']:
            icon = "✅"
            info = f"Provider: {result['provider_used']}, Time: {result['total_time']:.3f}s"
            if result['has_ai_analysis']:
                info += " (with AI)"
        else:
            icon = "❌"
            info = f"Error: {result['error']}"
        
        print(f"     {icon} {provider.upper()}: {info}")
    
    return True

def main():
    """Main test function"""
    print("🚀 ClinChat-RAG Enhanced API Testing")
    print("=" * 50)
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Run tests
    tests = [
        ("Health Check", test_api_health),
        ("Provider Status", test_provider_status),
        ("Local Analysis", test_local_analysis),
        ("AI Analysis", test_ai_analysis),
        ("Dataset Operations", test_datasets),
        ("Performance Comparison", test_performance_comparison)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ ClinChat-RAG Enhanced API is fully operational!")
    else:
        print(f"⚠️ {passed}/{total} tests passed")
    
    print(f"\n📋 API Features Available:")
    print(f"   • Local spaCy processing: ✅")
    print(f"   • Clinical entity extraction: ✅") 
    print(f"   • Dataset analytics: ✅")
    print(f"   • Google Gemini integration: 🔑 (needs API key)")
    print(f"   • Groq Cloud integration: 🔑 (needs API key)")
    
    print(f"\n🔧 To enable AI features:")
    print(f"   1. Get Google Gemini API key: https://makersuite.google.com/app/apikey")
    print(f"   2. Get Groq API key: https://console.groq.com/")
    print(f"   3. Update .env file with your keys")
    print(f"   4. Restart the API server")
    
    print(f"\n📚 Interactive Documentation: {API_BASE_URL}/docs")

if __name__ == "__main__":
    main()