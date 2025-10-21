#!/usr/bin/env python3
# Simple status check script for ClinChat-RAG

import os
import sys
from pathlib import Path

def main():
    print("ClinChat-RAG Status Check")
    print("=" * 40)
    
    # Check working directory
    cwd = Path.cwd()
    print(f"Working Directory: {cwd}")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("ENV: .env file found")
        try:
            with open(env_path) as f:
                content = f.read()
                has_gemini = "GOOGLE_API_KEY" in content
                has_groq = "GROQ_API_KEY" in content
                print(f"ENV: Gemini API key configured: {has_gemini}")
                print(f"ENV: Groq API key configured: {has_groq}")
        except Exception as e:
            print(f"ENV: Error reading .env: {e}")
    else:
        print("ENV: .env file not found")
    
    # Check database
    db_path = Path("data/clinchat_fusion.db")
    if db_path.exists():
        print(f"DB: Database exists: {db_path}")
        print(f"DB: Size: {db_path.stat().st_size} bytes")
    else:
        print("DB: Database not found")
        # Create data directory if it doesn't exist
        Path("data").mkdir(exist_ok=True)
        print("DB: Created data directory")
    
    # Check key files
    key_files = [
        "api/fusion_api.py",
        "database/connection.py",
        "fusion_ai_engine.py"
    ]
    
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"FILE: {file_path} - OK")
        else:
            print(f"FILE: {file_path} - MISSING")
    
    print("=" * 40)
    print("Status check complete")

if __name__ == "__main__":
    main()