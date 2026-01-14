"""
Model-Agnostic Embeddings Module

Supports multiple embedding providers:
- AWS Bedrock (amazon.titan-embed-text-v2:0)
- OpenAI (text-embedding-3-small)
- HuggingFace (sentence-transformers/all-MiniLM-L6-v2)
- OpenWebUI (Corporate proxy with OpenAI-compatible API)

Uses OpenAI library directly instead of LangChain.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class EmbeddingsProvider:
    """Base class for embeddings providers"""
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text"""
        raise NotImplementedError
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        raise NotImplementedError


def get_embeddings() -> EmbeddingsProvider:
    """
    Get embeddings model based on EMBEDDING_PROVIDER environment variable.
    
    Returns:
        EmbeddingsProvider: Embeddings provider instance
        
    Raises:
        ValueError: If provider is unsupported or configuration is missing
    """
    provider = os.getenv('EMBEDDING_PROVIDER', 'bedrock').lower()
    model_name = os.getenv('EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
    
    if provider == 'bedrock':
        return _get_bedrock_embeddings(model_name)
    elif provider == 'openai':
        return _get_openai_embeddings(model_name)
    elif provider == 'huggingface':
        return _get_huggingface_embeddings(model_name)
    elif provider == 'openwebui':
        return _get_openwebui_embeddings(model_name)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}. Use 'bedrock', 'openai', 'huggingface', or 'openwebui'")


class BedrockEmbeddings(EmbeddingsProvider):
    """AWS Bedrock embeddings provider"""
    
    def __init__(self, model_name: str, region: str = 'us-east-1'):
        try:
            import boto3
        except ImportError:
            raise ImportError("Install boto3: pip install boto3")
        
        self.model_name = model_name
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query"""
        import json
        
        body = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=self.model_name,
            body=body,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        return response_body.get('embedding', [])
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        return [self.embed_query(text) for text in texts]


def _get_bedrock_embeddings(model_name):
    """Get AWS Bedrock embeddings"""
    region = os.getenv('AWS_REGION', 'us-east-1')
    embeddings = BedrockEmbeddings(model_name=model_name, region=region)
    print(f"✅ Using AWS Bedrock embeddings: {model_name}")
    return embeddings


class OpenAIEmbeddings(EmbeddingsProvider):
    """OpenAI embeddings provider using openai library directly"""
    
    def __init__(self, model: str, api_key: str, base_url: str = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query"""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        # OpenAI API supports batch embeddings
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [data.embedding for data in response.data]


def _get_openai_embeddings(model_name):
    """Get OpenAI embeddings"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env")
    
    embeddings = OpenAIEmbeddings(model=model_name, api_key=api_key)
    print(f"✅ Using OpenAI embeddings: {model_name}")
    return embeddings


class HuggingFaceEmbeddings(EmbeddingsProvider):
    """HuggingFace embeddings provider (local)"""
    
    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Install sentence-transformers: pip install sentence-transformers")
        
        self.model = SentenceTransformer(model_name)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query"""
        return self.model.encode(text).tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]


def _get_huggingface_embeddings(model_name):
    """Get HuggingFace embeddings (local)"""
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    print(f"✅ Using HuggingFace embeddings: {model_name}")
    return embeddings


def _get_openwebui_embeddings(model_name):
    """
    Get OpenWebUI embeddings via OpenAI-compatible API.
    
    OpenWebUI is commonly used as a corporate proxy when direct access
    to cloud embedding services is restricted by network policies.
    
    Args:
        model_name (str): Embedding model name configured in OpenWebUI
        
    Returns:
        OpenAIEmbeddings: Configured for OpenWebUI endpoint
    """
    base_url = os.getenv('OPENWEBUI_BASE_URL')
    api_key = os.getenv('OPENWEBUI_API_KEY', 'sk-dummy')
    
    if not base_url:
        raise ValueError(
            "OPENWEBUI_BASE_URL not set in environment variables. "
            "Example: http://your-openwebui-instance:8080/api/v1"
        )
    
    # OpenWebUI provides OpenAI-compatible embeddings endpoint
    embeddings = OpenAIEmbeddings(model=model_name, api_key=api_key, base_url=base_url)
    print(f"✅ Using OpenWebUI embeddings: {model_name} (via {base_url})")
    return embeddings


def get_embedding_info():
    """
    Get current embedding configuration info for display.
    
    Returns:
        dict: Provider and model information
    """
    provider = os.getenv('EMBEDDING_PROVIDER', 'bedrock').upper()
    model_name = os.getenv('EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
    
    # Format model name for display
    if 'titan' in model_name.lower():
        display_name = "Amazon Titan v2"
    elif 'cohere' in model_name.lower():
        display_name = "Cohere Embed"
    elif 'text-embedding-3' in model_name.lower():
        display_name = "OpenAI Embedding-3"
    elif 'all-MiniLM' in model_name:
        display_name = "MiniLM-L6-v2 (Local)"
    else:
        display_name = model_name.split('/')[-1] if '/' in model_name else model_name
    
    return {
        'provider': provider,
        'model': display_name,
        'raw_model': model_name
    }


def test_embeddings():
    """
    Test the configured embeddings provider.
    
    Returns:
        tuple: (success: bool, message: str, dimension: int)
    """
    try:
        print("Testing embeddings configuration...")
        embeddings = get_embeddings()
        
        # Test with a sample text
        test_text = "This is a test sentence for embeddings."
        print(f"Generating embedding for: '{test_text}'")
        
        # Generate embedding
        vector = embeddings.embed_query(test_text)
        
        # Check vector dimension
        dimension = len(vector)
        
        provider = os.getenv('EMBEDDING_PROVIDER', 'bedrock')
        model = os.getenv('EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
        
        success_msg = f"✅ {provider.upper()} embeddings working!\n   Model: {model}\n   Dimension: {dimension}"
        print(success_msg)
        
        return True, success_msg, dimension
        
    except Exception as e:
        error_msg = f"❌ Embeddings test failed: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, error_msg, 0


if __name__ == "__main__":
    # Run test when executed directly
    test_embeddings()
