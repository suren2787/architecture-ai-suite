#!/usr/bin/env python3
"""
Validation script for Architecture AI Suite setup.

This script checks that all components are properly configured and working.
Run this after completing the setup instructions in SETUP.md.
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_status(check_name, passed, message=""):
    """Print check status with emoji"""
    icon = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    print(f"{icon} {check_name}: {status}")
    if message:
        print(f"   → {message}")
    return passed


def check_python_version():
    """Check Python version >= 3.8"""
    print_header("Checking Python Version")
    version = sys.version_info
    passed = version >= (3, 8)
    print_status(
        "Python Version",
        passed,
        f"Python {version.major}.{version.minor}.{version.micro} {'(OK)' if passed else '(Need 3.8+)'}"
    )
    return passed


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        'streamlit',
        'langchain',
        'langchain_community',
        'langchain_aws',
        'faiss',
        'boto3',
        'dotenv',
        'requests',
        'bs4'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'faiss':
                __import__('faiss')
            elif package == 'dotenv':
                __import__('dotenv')
            elif package == 'bs4':
                __import__('bs4')
            else:
                __import__(package)
            print_status(f"Package '{package}'", True, "Installed")
        except ImportError:
            missing.append(package)
            print_status(f"Package '{package}'", False, "Not installed")
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True


def check_config_files():
    """Check if configuration files exist"""
    print_header("Checking Configuration Files")
    
    checks = []
    
    # Check .env
    env_exists = os.path.exists('.env')
    checks.append(print_status(".env file", env_exists, 
                               "Found" if env_exists else "Missing - copy from .env.example"))
    
    # Check config.env
    config_env_exists = os.path.exists('config.env')
    checks.append(print_status("config.env file", config_env_exists,
                               "Found" if config_env_exists else "Missing - copy from config.env.example"))
    
    return all(checks)


def check_environment_vars():
    """Check if key environment variables are set"""
    print_header("Checking Environment Variables")
    
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv('config.env')
    
    checks = []
    
    # Check LLM provider
    provider = os.getenv('MODEL_PROVIDER', '')
    checks.append(print_status("MODEL_PROVIDER", bool(provider), provider or "Not set"))
    
    # Check model name
    model = os.getenv('MODEL_NAME', '')
    checks.append(print_status("MODEL_NAME", bool(model), model or "Not set"))
    
    # Provider-specific checks
    if provider == 'bedrock':
        aws_key = os.getenv('AWS_ACCESS_KEY_ID', '')
        is_configured = aws_key and aws_key != 'your_access_key_here'
        checks.append(print_status("AWS Credentials", is_configured,
                                  "Configured" if is_configured else "Using placeholder - update .env"))
    elif provider == 'openai':
        openai_key = os.getenv('OPENAI_API_KEY', '')
        is_configured = bool(openai_key)
        checks.append(print_status("OpenAI API Key", is_configured,
                                  "Configured" if is_configured else "Missing"))
    elif provider == 'anthropic':
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        is_configured = bool(anthropic_key)
        checks.append(print_status("Anthropic API Key", is_configured,
                                  "Configured" if is_configured else "Missing"))
    
    # Check embedding provider
    emb_provider = os.getenv('EMBEDDING_PROVIDER', '')
    checks.append(print_status("EMBEDDING_PROVIDER", bool(emb_provider),
                              emb_provider or "Not set (will use default)"))
    
    return all(checks)


def check_organization_config():
    """Check organization configuration"""
    print_header("Checking Organization Configuration")
    
    try:
        import config
        
        checks = []
        checks.append(print_status("Organization Name", True, config.ORG_NAME))
        checks.append(print_status("Organization Icon", True, config.ORG_ICON))
        checks.append(print_status("Audit Aspects", len(config.AUDIT_ASPECTS) > 0,
                                  f"{len(config.AUDIT_ASPECTS)} aspects configured"))
        checks.append(print_status("Reranking Keywords", len(config.RERANKING_KEYWORDS) > 0,
                                  f"{len(config.RERANKING_KEYWORDS)} keywords configured"))
        
        if config.PRIORITY_ADRS:
            checks.append(print_status("Priority ADRs", True,
                                      f"{len(config.PRIORITY_ADRS)} ADRs: {', '.join(config.PRIORITY_ADRS)}"))
        else:
            checks.append(print_status("Priority ADRs", True, "None configured (optional)"))
        
        return all(checks)
    except Exception as e:
        print_status("Config module", False, str(e))
        return False


def check_documents():
    """Check if documents exist in docs/ folder"""
    print_header("Checking Knowledge Base Documents")
    
    docs_path = Path('docs')
    if not docs_path.exists():
        print_status("docs/ folder", False, "Not found")
        return False
    
    md_files = list(docs_path.glob('**/*.md'))
    
    if not md_files:
        print_status("Markdown files", False, "No .md files found in docs/")
        return False
    
    print_status("Markdown files", True, f"Found {len(md_files)} document(s)")
    for md_file in md_files[:5]:  # Show first 5
        print(f"   • {md_file.name}")
    if len(md_files) > 5:
        print(f"   ... and {len(md_files) - 5} more")
    
    return True


def check_faiss_index():
    """Check if FAISS index exists"""
    print_header("Checking FAISS Vector Index")
    
    index_path = Path('faiss_index')
    
    if not index_path.exists():
        print_status("faiss_index/ folder", False, "Not found - run 'python ingest.py'")
        return False
    
    index_file = index_path / 'index.faiss'
    pkl_file = index_path / 'index.pkl'
    
    if not index_file.exists() or not pkl_file.exists():
        print_status("FAISS index files", False, "Incomplete - run 'python ingest.py'")
        return False
    
    print_status("FAISS index files", True, "Found index.faiss and index.pkl")
    
    # Try to load the index
    try:
        from brain import load_faiss_index
        vectorstore = load_faiss_index()
        print_status("Load FAISS index", True, "Successfully loaded")
        return True
    except Exception as e:
        print_status("Load FAISS index", False, str(e))
        return False


def check_modules():
    """Check if all Python modules can be imported"""
    print_header("Checking Python Modules")
    
    modules = [
        ('app', 'Streamlit UI'),
        ('brain', 'RAG Engine'),
        ('reviewer', 'Solution Auditor'),
        ('ingest', 'Document Ingestion'),
        ('embeddings', 'Embeddings'),
        ('config', 'Configuration'),
        ('confluence', 'Confluence Integration'),
        ('confluence_sync', 'Confluence Sync')
    ]
    
    checks = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            checks.append(print_status(f"{module_name}.py", True, description))
        except Exception as e:
            checks.append(print_status(f"{module_name}.py", False, str(e)))
    
    return all(checks)


def run_all_checks():
    """Run all validation checks"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Architecture AI Suite Validator" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = []
    
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Config Files", check_config_files()))
    results.append(("Environment Variables", check_environment_vars()))
    results.append(("Organization Config", check_organization_config()))
    results.append(("Documents", check_documents()))
    results.append(("FAISS Index", check_faiss_index()))
    results.append(("Python Modules", check_modules()))
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {check_name}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print(f"🎉 All checks passed! ({passed}/{total})")
        print("=" * 70)
        print("\n✨ Your setup is complete! Run: streamlit run app.py")
        return 0
    else:
        print(f"⚠️  {total - passed} check(s) failed ({passed}/{total} passed)")
        print("=" * 70)
        print("\n📖 See SETUP.md for detailed setup instructions")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_checks())
