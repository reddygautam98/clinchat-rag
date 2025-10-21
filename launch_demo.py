"""
ClinChat-RAG Demo Launcher
Quick script to start both the FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import signal
import os

def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def start_fastapi_server():
    """Start the FastAPI server in the background"""
    print("🚀 Starting FastAPI server...")
    
    # Get the Python path from virtual environment
    venv_path = Path(__file__).parent.parent / ".venv" / "Scripts"
    uvicorn_path = venv_path / "uvicorn.exe"
    
    if not uvicorn_path.exists():
        print("❌ uvicorn not found. Please install with: pip install uvicorn")
        return None
    
    # Check if port 8000 is available
    if not check_port_available(8000):
        print("⚠️ Port 8000 is busy. Trying port 8001...")
        port = 8001
        if not check_port_available(8001):
            print("❌ Both ports 8000 and 8001 are busy. Please stop other services.")
            return None
    else:
        port = 8000
    
    # Start the server
    cmd = [
        str(uvicorn_path),
        "api.app:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Wait for server to start
        print(f"⏳ Waiting for FastAPI server to start on port {port}...")
        time.sleep(5)
        
        # Test if server is responding
        import requests
        try:
            response = requests.get(f"http://127.0.0.1:{port}/", timeout=5)
            if response.status_code == 200:
                print(f"✅ FastAPI server running at http://127.0.0.1:{port}")
                return process, port
        except:
            pass
        
        print("❌ FastAPI server failed to start properly")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {e}")
        return None

def start_streamlit_app(api_port=8000):
    """Start the Streamlit application"""
    print("🎨 Starting Streamlit app...")
    
    # Get the Python path from virtual environment  
    venv_path = Path(__file__).parent.parent / ".venv" / "Scripts"
    python_path = venv_path / "python.exe"
    
    if not python_path.exists():
        print("❌ Python not found in virtual environment")
        return None
    
    # Update the API URL in the app if using different port
    if api_port != 8000:
        print(f"📝 Using API port {api_port}")
    
    # Start Streamlit
    cmd = [
        str(python_path),
        "-m", "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port", "8501",
        "--server.headless", "false"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent
        )
        
        print("⏳ Starting Streamlit (this may take a moment)...")
        time.sleep(3)
        
        # Open browser
        streamlit_url = "http://localhost:8501"
        print(f"🌐 Opening browser to {streamlit_url}")
        webbrowser.open(streamlit_url)
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return None

def main():
    """Main launcher function"""
    print("🏥 ClinChat-RAG Demo Launcher")
    print("=" * 40)
    
    processes = []
    
    try:
        # Start FastAPI server
        fastapi_result = start_fastapi_server()
        if fastapi_result:
            fastapi_process, api_port = fastapi_result
            processes.append(fastapi_process)
            
            # Start Streamlit app
            streamlit_process = start_streamlit_app(api_port)
            if streamlit_process:
                processes.append(streamlit_process)
                
                print("\n🎉 Both services are running!")
                print(f"📡 FastAPI API: http://127.0.0.1:{api_port}")
                print("🎨 Streamlit UI: http://localhost:8501")
                print("\n💡 Use Ctrl+C to stop both services")
                
                # Wait for user interrupt
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping services...")
            else:
                print("❌ Failed to start Streamlit app")
        else:
            print("❌ Failed to start FastAPI server")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    
    finally:
        # Clean up processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main()