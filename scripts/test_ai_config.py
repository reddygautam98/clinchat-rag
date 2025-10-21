#!/usr/bin/env python3
"""
Quick AI Configuration Test
Verify Fusion AI setup is working properly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_anthropic_connection():
    """Test Anthropic API connection"""
    try:
        from anthropic import Anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found")
            return False
            
        client = Anthropic(api_key=api_key)
        
        # Test with a simple message
        message = client.messages.create(
            model="claude-3-5-sonnet-20250101",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'ClinChat-RAG AI is working!' if you can read this."}
            ]
        )
        
        response = message.content[0].text
        print(f"✅ Anthropic Claude: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic connection failed: {e}")
        return False

def test_openai_embeddings():
    """Test OpenAI embeddings"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
            
        client = OpenAI(api_key=api_key)
        
        # Test embeddings
        response = client.embeddings.create(
            input="Test clinical document embeddings",
            model="text-embedding-ada-002"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ OpenAI Embeddings: Generated {len(embedding)}-dimensional vector")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI embeddings failed: {e}")
        return False

def test_spacy_models():
    """Test spaCy models are working"""
    try:
        import spacy
        
        # Test small model
        nlp_sm = spacy.load("en_core_web_sm")
        doc_sm = nlp_sm("The patient shows signs of acute myocardial infarction.")
        entities_sm = [(ent.text, ent.label_) for ent in doc_sm.ents]
        print(f"✅ spaCy Small: Found {len(entities_sm)} entities")
        
        # Test medium model
        nlp_md = spacy.load("en_core_web_md")
        doc_md = nlp_md("Patient has diabetes mellitus type 2.")
        entities_md = [(ent.text, ent.label_) for ent in doc_md.ents]
        print(f"✅ spaCy Medium: Found {len(entities_md)} entities")
        
        return True
        
    except Exception as e:
        print(f"❌ spaCy models failed: {e}")
        return False

def main():
    """Run all AI configuration tests"""
    print("🧪 Testing ClinChat-RAG AI Configuration")
    print("="*50)
    
    tests = [
        ("Anthropic Claude API", test_anthropic_connection),
        ("OpenAI Embeddings API", test_openai_embeddings), 
        ("spaCy NLP Models", test_spacy_models)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Testing {test_name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL AI COMPONENTS WORKING!")
        print("✅ Ready for clinical document processing!")
    else:
        print("⚠️  Some AI components need attention")
    
    return passed == total

if __name__ == "__main__":
    main()