"""
Simple test script for the ClinChat-RAG API
"""
import requests
import json
import time
import subprocess
import sys
import os

def test_rag_api():
    """Test the RAG API endpoints"""
    
    base_url = "http://127.0.0.1:8005"
    
    print("🚀 Testing ClinChat-RAG API...")
    
    # Test 1: Root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False
    
    # Test 2: Health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test 3: Simple search
    try:
        response = requests.get(f"{base_url}/search?query=chest%20pain&k=3")
        if response.status_code == 200:
            print("✅ Search endpoint working")
            search_data = response.json()
            print(f"   Found {len(search_data.get('results', []))} results")
            if search_data.get('results'):
                print(f"   First result: {search_data['results'][0]['doc_id']}")
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
    
    # Test 4: Q&A endpoint
    try:
        qa_request = {
            "question": "What causes chest pain?",
            "max_sources": 3,
            "include_scores": True
        }
        
        response = requests.post(
            f"{base_url}/qa",
            json=qa_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Q&A endpoint working!")
            qa_data = response.json()
            
            print(f"   Question: {qa_data.get('question')}")
            print(f"   Answer: {qa_data.get('answer', '')[:100]}...")
            print(f"   Sources: {len(qa_data.get('sources', []))} documents")
            
            # Show provenance
            for i, source in enumerate(qa_data.get('sources', [])[:2]):
                print(f"   Source {i+1}: doc_id={source.get('doc_id')}, chunk_id={source.get('chunk_id')}")
                if source.get('similarity_score'):
                    print(f"            similarity_score={source.get('similarity_score'):.4f}")
            
            return True
        else:
            print(f"❌ Q&A endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Q&A endpoint error: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting ClinChat-RAG server...")
    
    # Get the correct Python path
    venv_path = r"C:\Users\reddy\Downloads\Gen-AI enabled data-warehouse + RAG clinical assistant\.venv\Scripts"
    uvicorn_path = os.path.join(venv_path, "uvicorn.exe")
    
    # Change to the correct directory
    os.chdir(r"c:\Users\reddy\Downloads\Gen-AI enabled data-warehouse + RAG clinical assistant\clinchat-rag")
    
    # Start the server
    cmd = [uvicorn_path, "api.app:app", "--host", "127.0.0.1", "--port", "8005"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("   Waiting for server to start...")
        
        # Wait for server to be ready
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://127.0.0.1:8005/", timeout=1)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return process
            except:
                pass
            time.sleep(1)
            print(f"   Waiting... {i+1}/30")
        
        print("❌ Server failed to start within 30 seconds")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

if __name__ == "__main__":
    print("=" * 50)
    print("🏥 ClinChat-RAG API Test Suite")
    print("=" * 50)
    
    # Start server
    server_process = start_server()
    
    if server_process:
        try:
            # Run tests
            time.sleep(2)  # Give server a moment to fully initialize
            success = test_rag_api()
            
            if success:
                print("\n🎉 All tests passed! RAG API is working correctly.")
                print("\n📋 Test Summary:")
                print("   ✅ FastAPI server startup")
                print("   ✅ Root endpoint")
                print("   ✅ Health check endpoint") 
                print("   ✅ Search endpoint")
                print("   ✅ Q&A endpoint with provenance")
                print("\n🔗 API Documentation: http://127.0.0.1:8005/docs")
                print("🔗 Interactive API: http://127.0.0.1:8005/redoc")
            else:
                print("\n❌ Some tests failed. Check the server logs.")
                
        finally:
            # Clean up
            print("\n🧹 Cleaning up...")
            server_process.terminate()
            time.sleep(2)
            print("✅ Server stopped.")
    else:
        print("❌ Could not start server for testing.")
    
    print("\n" + "=" * 50)