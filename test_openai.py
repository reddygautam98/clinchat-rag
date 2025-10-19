#!/usr/bin/env python3
"""
OpenAI Configuration Test Script
Run this to verify your OpenAI API key and connectivity for ClinChat-RAG.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
import sys

def test_openai_config():
    """Test OpenAI configuration and connectivity."""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Checking OpenAI Configuration...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key.startswith('your_'):
        print("❌ OPENAI_API_KEY: Not configured")
        print("⚠️  Please set your OpenAI API key in the .env file")
        return False
    else:
        # Mask the API key for security
        masked_key = api_key[:7] + "..." + api_key[-4:]
        print(f"✅ OPENAI_API_KEY: {masked_key}")
    
    # Check other settings
    model = os.getenv('OPENAI_MODEL', 'gpt-4-1106-preview')
    embedding_model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-ada-002')
    max_tokens = os.getenv('OPENAI_MAX_TOKENS', '2000')
    temperature = os.getenv('OPENAI_TEMPERATURE', '0.1')
    
    print(f"✅ OPENAI_MODEL: {model}")
    print(f"✅ OPENAI_EMBEDDING_MODEL: {embedding_model}")
    print(f"✅ OPENAI_MAX_TOKENS: {max_tokens}")
    print(f"✅ OPENAI_TEMPERATURE: {temperature}")
    
    # Test connection
    print(f"\n🔗 Testing OpenAI Connection...")
    try:
        client = OpenAI(api_key=api_key)
        
        # Test chat completion
        print("📝 Testing Chat Completion...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hello! This is a test message for ClinChat-RAG system. Please respond briefly."}
            ],
            max_tokens=int(max_tokens),
            temperature=float(temperature)
        )
        
        chat_response = response.choices[0].message.content
        print(f"✅ Chat Response: {chat_response}")
        
        # Test embedding
        print("📊 Testing Embeddings...")
        embedding_response = client.embeddings.create(
            model=embedding_model,
            input="Test embedding for clinical document analysis in ClinChat-RAG"
        )
        
        embedding_vector = embedding_response.data[0].embedding
        print(f"✅ Embedding Generated: {len(embedding_vector)} dimensions")
        
        # Test with clinical-like content
        print("🏥 Testing Clinical Content Processing...")
        clinical_test = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a clinical document AI assistant."},
                {"role": "user", "content": "What are the key components of a clinical trial protocol?"}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        clinical_response = clinical_test.choices[0].message.content
        print(f"✅ Clinical AI Response: {clinical_response[:100]}...")
        
        print(f"\n🎉 OpenAI Configuration Test: PASSED")
        print(f"Your ClinChat-RAG system is ready to use OpenAI!")
        return True
        
    except Exception as e:
        print(f"❌ Connection Test Failed: {str(e)}")
        print(f"\nTroubleshooting Tips:")
        print(f"1. Verify your OpenAI API key is correct and has credits")
        print(f"2. Check your internet connection")
        print(f"3. Ensure the API key has access to GPT-4 (if using GPT-4)")
        print(f"4. Try using gpt-3.5-turbo if GPT-4 access is limited")
        return False

def show_usage_tips():
    """Show tips for using OpenAI with clinical applications."""
    print(f"\n💡 Clinical Use Tips:")
    print(f"━" * 50)
    print(f"• Use temperature=0.1 for consistent clinical responses")
    print(f"• Set appropriate max_tokens to control response length")
    print(f"• Consider using gpt-4 for complex clinical reasoning")
    print(f"• Use text-embedding-ada-002 for document embeddings")
    print(f"• Monitor API usage and costs in OpenAI dashboard")
    print(f"• Implement proper error handling for production use")

if __name__ == "__main__":
    print("ClinChat-RAG OpenAI Configuration Test")
    print("=" * 50)
    
    success = test_openai_config()
    
    if success:
        show_usage_tips()
        print(f"\n✅ All tests passed! Your OpenAI setup is ready for ClinChat-RAG.")
        sys.exit(0)
    else:
        print(f"\n❌ Configuration test failed. Please check your OpenAI setup.")
        sys.exit(1)