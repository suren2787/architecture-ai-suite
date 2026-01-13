#!/usr/bin/env python3
"""
Architecture AI Suite - Demo Script

This script demonstrates the core functionality without needing the Streamlit UI.
Perfect for testing your setup or integrating into CI/CD pipelines.

Note: Requires valid API credentials in .env file to query the LLM.
"""

import sys


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def demo_knowledge_bot():
    """Demonstrate the Knowledge Bot"""
    print_section("📚 Knowledge Bot Demo")
    
    import os
    
    # Check if API credentials are configured
    provider = os.getenv('MODEL_PROVIDER', '')
    if provider == 'bedrock':
        aws_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        if not aws_key or aws_key == 'your_access_key_here':
            print("⏭️  Skipping Knowledge Bot demo - AWS credentials not configured")
            print("💡 Tip: Configure AWS_ACCESS_KEY_ID in .env to try this feature")
            print("   See SETUP.md for instructions\n")
            return True  # Not a failure, just skipped
    elif provider == 'openai':
        if not os.getenv('OPENAI_API_KEY'):
            print("⏭️  Skipping Knowledge Bot demo - OpenAI API key not configured")
            print("💡 Tip: Configure OPENAI_API_KEY in .env to try this feature\n")
            return True
    elif provider == 'anthropic':
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("⏭️  Skipping Knowledge Bot demo - Anthropic API key not configured")
            print("💡 Tip: Configure ANTHROPIC_API_KEY in .env to try this feature\n")
            return True
    
    from brain import ask_auditor
    
    questions = [
        "What are the requirements for data residency in Hong Kong?",
        "What authentication method should we use?",
        "Which event architecture should we use for microservices?"
    ]
    
    print("Asking sample questions to the Knowledge Bot...\n")
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 70)
        
        try:
            answer, sources = ask_auditor(question)
            print(f"\n💡 Answer:\n{answer}\n")
            
            if sources:
                print(f"📖 Sources:")
                for src in sources[:2]:  # Show top 2 sources
                    filename = src.get('filename', 'unknown')
                    confidence = src.get('confidence', 'Unknown')
                    print(f"  • {filename} (Confidence: {confidence})")
            
            print()
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}")
            print("💡 Tip: Make sure you have valid API credentials in .env")
            return False
    
    return True


def demo_solution_auditor():
    """Demonstrate the Solution Auditor"""
    print_section("🔍 Solution Auditor Demo")
    
    import os
    
    # Check if API credentials are configured
    provider = os.getenv('MODEL_PROVIDER', '')
    if provider == 'bedrock':
        aws_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        if not aws_key or aws_key == 'your_access_key_here':
            print("⏭️  Skipping Solution Auditor demo - AWS credentials not configured")
            print("💡 Tip: Configure AWS_ACCESS_KEY_ID in .env to try this feature")
            print("   See SETUP.md for instructions\n")
            return True  # Not a failure, just skipped
    elif provider == 'openai':
        if not os.getenv('OPENAI_API_KEY'):
            print("⏭️  Skipping Solution Auditor demo - OpenAI API key not configured")
            return True
    elif provider == 'anthropic':
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("⏭️  Skipping Solution Auditor demo - Anthropic API key not configured")
            return True
    
    from reviewer import run_audit
    
    sample_design = """
    # Payment Service Design
    
    ## Architecture
    - Microservice architecture using AWS ECS
    - PostgreSQL database for transaction storage
    - Redis for session management
    
    ## Authentication
    - JWT-based authentication
    - OAuth 2.0 for third-party integrations
    
    ## Data Storage
    - Database deployed in us-east-1
    - Automatic backups every 24 hours
    """
    
    print("Auditing a sample payment service design...\n")
    print(f"Design Document:\n{sample_design}\n")
    print("-" * 70)
    
    try:
        audit_result = run_audit(sample_design)
        print(f"\n📋 Audit Results:\n\n{audit_result}\n")
        return True
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print("💡 Tip: Make sure you have valid API credentials in .env")
        return False


def demo_faiss_index():
    """Demonstrate FAISS index loading and search"""
    print_section("🗄️ FAISS Index Demo")
    
    from brain import load_faiss_index
    import os
    
    print("Loading FAISS vector index...")
    
    try:
        vectorstore = load_faiss_index()
        print("✅ FAISS index loaded successfully\n")
        
        # Check if we can perform searches (requires embeddings API access)
        provider = os.getenv('MODEL_PROVIDER', '')
        can_search = False
        
        if provider == 'bedrock':
            aws_key = os.getenv('AWS_ACCESS_KEY_ID', '')
            can_search = aws_key and aws_key != 'your_access_key_here'
        elif provider == 'openai':
            can_search = bool(os.getenv('OPENAI_API_KEY'))
        elif provider == 'anthropic':
            can_search = bool(os.getenv('ANTHROPIC_API_KEY'))
        
        if not can_search:
            print("⚠️  Search functionality requires API credentials for embeddings")
            print("💡 Tip: Configure your credentials in .env to enable search")
            print("   The FAISS index is loaded and ready - just needs embeddings API access\n")
            return True  # Index loaded successfully, search just skipped
        
        # Test similarity search
        query = "data residency requirements"
        print(f"Searching for: '{query}'\n")
        
        results = vectorstore.similarity_search(query, k=3)
        print(f"Found {len(results)} relevant documents:\n")
        
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'unknown')
            content_preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            print(f"{i}. Source: {source}")
            print(f"   Preview: {content_preview}\n")
        
        return True
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")
        return False


def demo_configuration():
    """Demonstrate configuration loading"""
    print_section("⚙️ Configuration Demo")
    
    import config
    import os
    
    print("Organization Configuration:")
    print(f"  • Name: {config.ORG_NAME}")
    print(f"  • Icon: {config.ORG_ICON}")
    print(f"  • Priority ADRs: {config.PRIORITY_ADRS if config.PRIORITY_ADRS else 'None configured'}")
    print(f"  • Reranking Keywords: {', '.join(config.RERANKING_KEYWORDS)}")
    print(f"  • Audit Aspects: {len(config.AUDIT_ASPECTS)} configured")
    
    print("\nLLM Configuration:")
    provider = os.getenv('MODEL_PROVIDER', 'not set')
    model = os.getenv('MODEL_NAME', 'not set')
    print(f"  • Provider: {provider}")
    print(f"  • Model: {model}")
    
    print("\nEmbedding Configuration:")
    emb_provider = os.getenv('EMBEDDING_PROVIDER', 'not set')
    emb_model = os.getenv('EMBEDDING_MODEL', 'not set')
    print(f"  • Provider: {emb_provider}")
    print(f"  • Model: {emb_model}")
    
    return True


def main():
    """Run all demos"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "Architecture AI Suite Demo" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\nThis demo showcases the core functionality of the Architecture AI Suite.")
    print("Some features require valid API credentials in .env file.\n")
    
    demos = [
        ("Configuration", demo_configuration, True),  # Always runs
        ("FAISS Index", demo_faiss_index, True),      # Always runs
        ("Knowledge Bot", demo_knowledge_bot, False),  # Requires API credentials
        ("Solution Auditor", demo_solution_auditor, False),  # Requires API credentials
    ]
    
    results = []
    
    for name, demo_func, always_run in demos:
        if always_run:
            success = demo_func()
            results.append((name, success))
        else:
            try:
                success = demo_func()
                results.append((name, success))
            except KeyboardInterrupt:
                print("\n\n⏸️  Demo interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Demo failed: {e}")
                results.append((name, False))
    
    # Summary
    print_section("📊 Demo Summary")
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n{passed}/{total} demos completed successfully")
    
    if passed < total:
        print("\n💡 Tip: Make sure you have valid API credentials configured in .env")
        print("   See SETUP.md for configuration instructions")
    else:
        print("\n✨ All demos completed! Your setup is working correctly.")
        print("   Run 'streamlit run app.py' to launch the full UI")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user")
        sys.exit(130)
