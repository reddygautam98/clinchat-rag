#!/usr/bin/env python3
"""
Script to list available models for Google Gemini and Groq
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq

load_dotenv()

def list_gemini_models():
    """List available Google Gemini models"""
    print("🔮 Available Google Gemini Models:")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("   ❌ No GOOGLE_API_KEY found")
        return
    
    try:
        genai.configure(api_key=api_key)
        
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f"   ✅ {model.name}")
    except Exception as e:
        print(f"   ❌ Error listing Gemini models: {e}")

def test_groq_models():
    """Test common Groq model names"""
    print("\n⚡ Testing Common Groq Models:")
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("   ❌ No GROQ_API_KEY found")
        return
    
    # Common Groq models (as of late 2024)
    models_to_test = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile", 
        "mixtral-8x7b-32768",
        "gemma-7b-it",
        "llama3-groq-70b-8192-tool-use-preview",
        "llama3-70b-8192",
        "llama3-8b-8192"
    ]
    
    client = Groq(api_key=api_key)
    
    for model_name in models_to_test:
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=model_name,
                max_tokens=5
            )
            print(f"   ✅ {model_name} - Working!")
            break  # Found a working model
        except Exception as e:
            if "model_decommissioned" in str(e) or "not_found" in str(e):
                print(f"   ❌ {model_name} - Decommissioned/Not Found")
            else:
                print(f"   ⚠️  {model_name} - Error: {str(e)[:60]}...")

def main():
    print("🚀 Discovering Available AI Models")
    print("=" * 50)
    
    list_gemini_models()
    test_groq_models()
    
    print("\n" + "=" * 50)
    print("💡 Use the working models in your .env file!")

if __name__ == "__main__":
    main()