#!/usr/bin/env python3
"""
ClinChat-RAG UI Launch Script
Starts both the API server and UI development server
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import threading
import os

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting ClinChat-RAG API server...")
    
    # Change to the main directory
    main_dir = Path(__file__).parent.parent
    os.chdir(main_dir)
    
    try:
        # Start the API server
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--port", "8000", "--host", "0.0.0.0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ API server starting on http://localhost:8000")
        return api_process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_ui_server():
    """Start the UI development server"""
    print("🎨 Starting UI development server...")
    
    # Change to UI directory
    ui_dir = Path(__file__).parent
    os.chdir(ui_dir)
    
    try:
        # Try different ports in case of conflicts
        ports = [9000, 8080, 3000, 5000, 8888]
        
        for port in ports:
            try:
                ui_process = subprocess.Popen([
                    sys.executable, "-m", "http.server", str(port)
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Give it a moment to start
                time.sleep(1)
                
                # Check if it's still running (didn't fail immediately)
                if ui_process.poll() is None:
                    print(f"✅ UI server starting on http://localhost:{port}")
                    return ui_process, port
                else:
                    ui_process.terminate()
                    
            except Exception:
                continue
                
        print("❌ Failed to start UI server on any available port")
        return None, None
        
    except Exception as e:
        print(f"❌ Failed to start UI server: {e}")
        return None, None

def main():
    """Main launch function"""
    print("🏥 ClinChat-RAG System Launcher")
    print("=" * 50)
    
    # Start servers
    api_process = start_api_server()
    time.sleep(2)  # Give API server time to start
    
    ui_process, ui_port = start_ui_server()
    
    if not api_process or not ui_process:
        print("\n❌ Failed to start one or more services")
        if api_process:
            api_process.terminate()
        if ui_process:
            ui_process.terminate()
        return 1
    
    print("\n🎉 All services started successfully!")
    print(f"📊 API: http://localhost:8000")
    print(f"🌐 UI:  http://localhost:{ui_port}")
    print("\n📝 Opening UI in your default browser...")
    
    # Open browser after a short delay
    threading.Timer(3.0, lambda: webbrowser.open(f"http://localhost:{ui_port}")).start()
    
    print("\n💡 Usage Instructions:")
    print("1. The UI should open in your browser automatically")
    print("2. Enter medical questions in the text area")
    print("3. Choose search mode (hybrid recommended)")
    print("4. Review answers and supporting sources")
    print("\n⚠️  Press Ctrl+C to stop all services")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process.poll() is not None:
                print("\n❌ API server stopped unexpectedly")
                break
                
            if ui_process.poll() is not None:
                print("\n❌ UI server stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        if api_process:
            print("Stopping API server...")
            api_process.terminate()
            api_process.wait()
            
        if ui_process:
            print("Stopping UI server...")
            ui_process.terminate()
            ui_process.wait()
            
        print("✅ All services stopped successfully")
        return 0

if __name__ == "__main__":
    sys.exit(main())