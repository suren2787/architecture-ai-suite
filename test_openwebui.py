#!/usr/bin/env python3
"""
OpenWebUI Configuration Test Script

This script helps validate your OpenWebUI configuration before running the main application.
It tests both LLM and embeddings connectivity.

Usage:
    python test_openwebui.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_llm_connection():
    """Test OpenWebUI LLM connection"""
    print_header("Testing OpenWebUI LLM Connection")
    
    # Check environment variables
    api_key = os.getenv('OPENWEBUI_API_KEY')
    base_url = os.getenv('OPENWEBUI_BASE_URL')
    model_name = os.getenv('MODEL_NAME', 'deepseek-r1')
    
    if not api_key:
        print("❌ OPENWEBUI_API_KEY not set in .env file")
        return False
    
    if not base_url:
        print("❌ OPENWEBUI_BASE_URL not set in .env file")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    print(f"✓ Base URL: {base_url}")
    print(f"✓ Model: {model_name}")
    
    # Test the connection
    try:
        print("\nTesting LLM inference...")
        from brain import invoke_llm
        
        test_prompt = "Say 'Hello, OpenWebUI is working!' and nothing else."
        response = invoke_llm(test_prompt, max_tokens=50)
        
        print(f"✅ LLM Response: {response[:100]}")
        print("\n✅ OpenWebUI LLM connection is working!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you've run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify OPENWEBUI_BASE_URL is correct (should end with /api/v1)")
        print("  2. Check OPENWEBUI_API_KEY is valid")
        print("  3. Ensure the model is available in your OpenWebUI instance")
        print("  4. Test connectivity: curl -H 'Authorization: Bearer YOUR_KEY' YOUR_BASE_URL/models")
        return False

def test_embeddings_connection():
    """Test OpenWebUI embeddings connection"""
    print_header("Testing OpenWebUI Embeddings Connection")
    
    embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'bedrock').lower()
    
    if embedding_provider != 'openwebui':
        print(f"ℹ️  EMBEDDING_PROVIDER is set to '{embedding_provider}' (not openwebui)")
        print("   Skipping OpenWebUI embeddings test")
        return True
    
    api_key = os.getenv('OPENWEBUI_API_KEY')
    base_url = os.getenv('OPENWEBUI_BASE_URL')
    model_name = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    
    if not api_key or not base_url:
        print("❌ OPENWEBUI_API_KEY or OPENWEBUI_BASE_URL not set")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    print(f"✓ Base URL: {base_url}")
    print(f"✓ Embedding Model: {model_name}")
    
    try:
        print("\nTesting embeddings generation...")
        from embeddings import test_embeddings
        
        success, message, dimension = test_embeddings()
        
        if success:
            print(f"✅ Embedding dimension: {dimension}")
            print("\n✅ OpenWebUI embeddings connection is working!")
            return True
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify the embedding model is available in OpenWebUI")
        print("  2. Check if OpenWebUI supports embeddings endpoint")
        print("  3. Consider using 'huggingface' provider for local embeddings")
        return False

def check_configuration():
    """Check basic configuration"""
    print_header("Checking Configuration")
    
    model_provider = os.getenv('MODEL_PROVIDER', 'bedrock').lower()
    
    if model_provider != 'openwebui':
        print(f"⚠️  Warning: MODEL_PROVIDER is set to '{model_provider}'")
        print("   This test script is for OpenWebUI configuration")
        print("   To test OpenWebUI, set MODEL_PROVIDER=openwebui in your .env file")
        return False
    
    print("✓ MODEL_PROVIDER is set to 'openwebui'")
    
    required_vars = ['OPENWEBUI_API_KEY', 'OPENWEBUI_BASE_URL', 'MODEL_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease add these to your .env file")
        return False
    
    print("✓ All required environment variables are set")
    return True

def main():
    """Main test function"""
    print("\n🧪 OpenWebUI Configuration Test")
    print("This script will test your OpenWebUI setup\n")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("\nTo create one:")
        print("  1. Copy .env.openwebui.example to .env")
        print("  2. Update with your OpenWebUI credentials")
        print("  3. Run this test again")
        sys.exit(1)
    
    # Check configuration
    if not check_configuration():
        print("\n❌ Configuration check failed")
        print("\nNext steps:")
        print("  1. Review your .env file")
        print("  2. Set MODEL_PROVIDER=openwebui")
        print("  3. Add OPENWEBUI_API_KEY and OPENWEBUI_BASE_URL")
        sys.exit(1)
    
    # Test LLM
    llm_success = test_llm_connection()
    
    # Test embeddings
    embeddings_success = test_embeddings_connection()
    
    # Summary
    print_header("Test Summary")
    
    if llm_success and embeddings_success:
        print("✅ All tests passed!")
        print("\nYou're ready to run the application:")
        print("  streamlit run app.py")
    elif llm_success:
        print("✅ LLM tests passed")
        print("⚠️  Embeddings tests had issues (check configuration)")
        print("\nYou can still run the app, but embeddings might not work correctly")
    else:
        print("❌ Tests failed")
        print("\nPlease review the errors above and fix the configuration")
        sys.exit(1)

if __name__ == "__main__":
    main()
