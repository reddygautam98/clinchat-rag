#!/usr/bin/env python3
"""
Test ClinChat-RAG Local API
Demonstrates working features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health Check Success:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🔍 Testing Root Endpoint...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ Root Endpoint Success:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Root Endpoint Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root Endpoint Error: {e}")
        return False

def test_clinical_text_analysis():
    """Test clinical text analysis"""
    print("\n🔍 Testing Clinical Text Analysis...")
    
    clinical_text = "Patient presents with acute myocardial infarction. Current medications include aspirin 81mg daily and metoprolol 50mg BID. Troponin I is elevated at 15.2 ng/mL."
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze/text",
            json={
                "text": clinical_text,
                "model_type": "medium"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Clinical Text Analysis Success:")
            print(f"📝 Text: {clinical_text}")
            print(f"📊 Summary: {result['summary']}")
            print("🏥 Clinical Entities Found:")
            for category, items in result['clinical_entities'].items():
                if items:
                    print(f"  {category}: {', '.join(items)}")
            print("🔍 All Entities:")
            for entity in result['entities']:
                print(f"  • {entity['text']} [{entity['label']}] - {entity['description']}")
            return True
        else:
            print(f"❌ Clinical Text Analysis Failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Clinical Text Analysis Error: {e}")
        return False

def test_datasets():
    """Test datasets endpoint"""
    print("\n🔍 Testing Datasets...")
    try:
        response = requests.get(f"{BASE_URL}/datasets")
        if response.status_code == 200:
            datasets = response.json()
            print("✅ Datasets Success:")
            for dataset in datasets:
                print(f"📊 Dataset: {dataset['name']}")
                print(f"  Records: {dataset['records']:,}")
                print(f"  Columns: {len(dataset['columns'])}")
                print(f"  Size: {dataset['size_bytes']:,} bytes")
            return True
        else:
            print(f"❌ Datasets Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Datasets Error: {e}")
        return False

def test_ae_summary():
    """Test adverse events summary"""
    print("\n🔍 Testing Adverse Events Summary...")
    try:
        response = requests.get(f"{BASE_URL}/clinical/adverse-events/summary")
        if response.status_code == 200:
            summary = response.json()
            print("✅ Adverse Events Summary Success:")
            print(f"📊 Total Events: {summary['total_events']:,}")
            print(f"👥 Unique Patients: {summary['unique_patients']:,}")
            print(f"⚠️ Unique AE Terms: {summary['unique_ae_terms']:,}")
            
            if summary['severity_distribution']:
                print("🎯 Severity Distribution:")
                for grade, count in summary['severity_distribution'].items():
                    print(f"  Grade {grade}: {count:,}")
            
            if summary['top_ae_terms']:
                print("📋 Top Adverse Events:")
                for term, count in list(summary['top_ae_terms'].items())[:5]:
                    print(f"  {term}: {count}")
            
            return True
        else:
            print(f"❌ AE Summary Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AE Summary Error: {e}")
        return False

def test_lab_summary():
    """Test lab data summary"""
    print("\n🔍 Testing Lab Data Summary...")
    try:
        response = requests.get(f"{BASE_URL}/clinical/lab-data/summary")
        if response.status_code == 200:
            summary = response.json()
            print("✅ Lab Data Summary Success:")
            print(f"📊 Total Results: {summary['total_results']:,}")
            print(f"👥 Unique Patients: {summary['unique_patients']:,}")
            print(f"🧪 Unique Tests: {summary['unique_tests']:,}")
            print(f"⚠️ Abnormal Rate: {summary['abnormal_rate']}%")
            
            if summary['result_distribution']:
                print("🎯 Result Distribution:")
                for result, count in summary['result_distribution'].items():
                    print(f"  {result}: {count:,}")
            
            if summary['top_tests']:
                print("🔬 Top Lab Tests:")
                for test, count in list(summary['top_tests'].items())[:5]:
                    print(f"  {test}: {count}")
            
            return True
        else:
            print(f"❌ Lab Summary Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lab Summary Error: {e}")
        return False

def test_search():
    """Test dataset search"""
    print("\n🔍 Testing Dataset Search...")
    try:
        response = requests.get(f"{BASE_URL}/datasets/ae_data/search?query=nausea&limit=3")
        if response.status_code == 200:
            result = response.json()
            print("✅ Dataset Search Success:")
            print(f"🔍 Query: {result['query']}")
            print(f"📊 Total Matches: {result['total_matches']}")
            print(f"📄 Returned Records: {result['returned_records']}")
            
            if result['records']:
                print("📋 Sample Records:")
                for i, record in enumerate(result['records'][:2], 1):
                    print(f"  Record {i}:")
                    for key, value in record.items():
                        if value and str(value).strip():
                            print(f"    {key}: {value}")
            
            return True
        else:
            print(f"❌ Search Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 ClinChat-RAG Local API Testing")
    print("="*50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_check),
        ("Clinical Text Analysis", test_clinical_text_analysis),
        ("Datasets Overview", test_datasets),
        ("Adverse Events Summary", test_ae_summary),
        ("Lab Data Summary", test_lab_summary),
        ("Dataset Search", test_search)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ ClinChat-RAG Local API is fully functional!")
    else:
        print("⚠️ Some tests failed - check server status")
    
    print(f"\n🌐 Access the API:")
    print(f"  • Interactive docs: http://localhost:8000/docs")
    print(f"  • Alternative docs: http://localhost:8000/redoc")
    print(f"  • API root: http://localhost:8000")

if __name__ == "__main__":
    main()