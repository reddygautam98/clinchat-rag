#!/usr/bin/env python3
"""
ClinChat-RAG Simple API Launcher
Starts the Fusion AI API with proper environment configuration
"""

import sys
import os
from pathlib import Path

def main():
    """Launch the ClinChat-RAG API server"""
    
    # Set up the Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Starting ClinChat-RAG Fusion AI Server...")
    print(f"Project Root: {project_root}")
    
    # Verify API keys
    gemini_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not gemini_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return 1
        
    if not groq_key:
        print("ERROR: GROQ_API_KEY not found in environment")
        return 1
    
    print("✓ API keys configured")
    
    # Try to import the API
    try:
        from api.fusion_api import app
        print("✓ API module loaded successfully")
    except ImportError as e:
        print(f"ERROR: Failed to import API: {e}")
        return 1
    
    # Start the server
    try:
        import uvicorn
        print("Starting server on http://localhost:8002...")
        print("Press Ctrl+C to stop")
        
        uvicorn.run(
            "api.fusion_api:app",
            host="0.0.0.0",
            port=8002,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())