"""
Test script for Table-Aware Numeric Reasoning
Tests the enhanced RAG system with table processing capabilities
"""

import sys
import requests
import json
from pathlib import Path

def test_table_aware_rag():
    """Test the table-aware numeric reasoning functionality"""
    
    print("🧪 Testing Table-Aware Numeric Reasoning")
    print("=" * 50)
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("\n🔬 Test 1: Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            health_data = response.json()
            print(f"Status: {health_data.get('status')}")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure it's running on localhost:8000")
        return
    
    # Test 2: Numeric query detection
    print("\n🔬 Test 2: Numeric Queries")
    
    numeric_queries = [
        "What is the average glucose level?",
        "Show me the cholesterol values",
        "What are the lab results?",
        "Calculate the mean HDL levels",
        "What is the minimum hemoglobin value?",
        "How many lab tests were performed?"
    ]
    
    for query in numeric_queries:
        print(f"\nTesting query: '{query}'")
        
        try:
            response = requests.post(
                f"{base_url}/ask",
                json={
                    "question": query,
                    "max_sources": 3,
                    "include_scores": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response received")
                print(f"Answer: {result['answer'][:200]}...")
                print(f"Sources: {len(result['sources'])}")
                print(f"Confidence: {result['confidence']}")
                
                # Check if it's a computed result
                if "Computed from table data" in result.get('confidence', ''):
                    print("🎯 Table processing detected!")
                elif "Retrieved from medical documents" in result.get('confidence', ''):
                    print("📄 Regular text processing used")
                
            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 3: Non-numeric queries (should use regular processing)
    print("\n🔬 Test 3: Non-Numeric Queries")
    
    text_queries = [
        "What is the patient's diagnosis?",
        "Tell me about the treatment plan",
        "What medications were prescribed?"
    ]
    
    for query in text_queries:
        print(f"\nTesting query: '{query}'")
        
        try:
            response = requests.post(
                f"{base_url}/ask",
                json={
                    "question": query,
                    "max_sources": 3,
                    "include_scores": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response received")
                print(f"Answer: {result['answer'][:200]}...")
                print(f"Confidence: {result['confidence']}")
                
            else:
                print(f"❌ Query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 4: Search endpoint
    print("\n🔬 Test 4: Document Search")
    
    try:
        response = requests.get(
            f"{base_url}/search",
            params={"query": "glucose levels", "k": 3}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search successful")
            print(f"Found {results['total_found']} documents")
            
            for i, result in enumerate(results['results'][:2]):
                print(f"\nResult {i+1}:")
                print(f"  Doc ID: {result['doc_id']}")
                print(f"  Content: {result['content'][:100]}...")
                print(f"  Score: {result['similarity_score']:.3f}")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Table-aware testing completed!")
    print("\nSummary:")
    print("- Numeric queries should show 'Computed from table data'")
    print("- Text queries should show 'Retrieved from medical documents'")
    print("- API should handle both types seamlessly")

if __name__ == "__main__":
    test_table_aware_rag()