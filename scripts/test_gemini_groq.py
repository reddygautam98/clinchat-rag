#!/usr/bin/env python3
"""
Test script for Google Gemini and Groq Cloud integration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai  # type: ignore
from groq import Groq  # type: ignore

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_google_gemini():
    """Test Google Gemini API connection"""
    print("🔮 Testing Google Gemini API...")
    
    # Configure Gemini
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key or api_key == 'your_google_gemini_api_key_here':
        print("❌ Google Gemini API key not configured")
        print("   Please get your API key from: https://makersuite.google.com/app/apikey")
        print("   And set GOOGLE_API_KEY in your .env file")
        return False
    
    try:
        genai.configure(api_key=api_key)
        
        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("What is the capital of France? Answer in one word.")
        
        print("✅ Google Gemini API working!")
        print("   Model: gemini-2.0-flash")
        print(f"   Test response: {response.text.strip()}")  # type: ignore
        return True
        
    except Exception as e:
        print(f"❌ Google Gemini API error: {str(e)}")
        return False

def test_groq_cloud():
    """Test Groq Cloud API connection"""
    print("\n⚡ Testing Groq Cloud API...")
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key or api_key == 'your_groq_api_key_here':
        print("❌ Groq API key not configured")
        print("   Please get your API key from: https://console.groq.com/")
        print("   And set GROQ_API_KEY in your .env file")
        return False
    
    try:
        client = Groq(api_key=api_key)
        
        # Test with a simple prompt
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "What is 2+2? Answer with just the number.",
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=10,
            temperature=0.1
        )
        
        print("✅ Groq Cloud API working!")
        print("   Model: llama-3.1-8b-instant")
        print(f"   Test response: {chat_completion.choices[0].message.content.strip()}")  # type: ignore
        return True
        
    except Exception as e:
        print(f"❌ Groq Cloud API error: {str(e)}")
        return False

def test_clinical_use_case():
    """Test both APIs with a clinical use case"""
    print("\n🏥 Testing Clinical Use Case...")
    
    clinical_text = """
    Patient presents with chest pain, shortness of breath, and elevated troponin levels.
    ECG shows ST-elevation in leads II, III, and aVF. 
    Diagnosis: Acute inferior wall myocardial infarction.
    Treatment: Emergency cardiac catheterization recommended.
    """
    
    # Test with Google Gemini
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key and api_key != 'your_google_gemini_api_key_here':
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            Analyze this clinical note and extract key medical entities:
            {clinical_text}
            
            Provide a structured summary with:
            1. Chief complaints
            2. Key findings
            3. Diagnosis
            4. Treatment plan
            """
            
            response = model.generate_content(prompt)
            print("✅ Google Gemini Clinical Analysis:")
            print(f"   {response.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Gemini clinical test failed: {str(e)}")
    
    # Test with Groq
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key and groq_key != 'your_groq_api_key_here':
        try:
            client = Groq(api_key=groq_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI assistant. Analyze clinical notes and provide structured summaries."
                    },
                    {
                        "role": "user",
                        "content": f"Extract the diagnosis from this clinical note: {clinical_text}"
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=200,
                temperature=0.1
            )
            
            print("✅ Groq Clinical Analysis:")
            print(f"   {chat_completion.choices[0].message.content.strip()}")
            
        except Exception as e:
            print(f"❌ Groq clinical test failed: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Testing Google Gemini & Groq Cloud Integration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Test individual APIs
    gemini_works = test_google_gemini()
    groq_works = test_groq_cloud()
    
    # Test clinical use case if both work
    if gemini_works or groq_works:
        test_clinical_use_case()
    
    print("\n" + "=" * 50)
    print("🎯 API Configuration Summary:")
    print(f"   Google Gemini: {'✅ Ready' if gemini_works else '❌ Needs Setup'}")
    print(f"   Groq Cloud: {'✅ Ready' if groq_works else '❌ Needs Setup'}")
    
    if not gemini_works and not groq_works:
        print("\n📝 Next Steps:")
        print("1. Get Google Gemini API key: https://makersuite.google.com/app/apikey")
        print("2. Get Groq API key: https://console.groq.com/")
        print("3. Update your .env file with the API keys")
        print("4. Run this script again to test")
    elif gemini_works and groq_works:
        print("\n🎉 Both APIs are working! Your clinical AI system is ready!")
        print("   You can now use both Google Gemini and Groq for different use cases:")
        print("   - Gemini: Advanced reasoning and analysis")
        print("   - Groq: High-speed inference and real-time responses")

if __name__ == "__main__":
    main()