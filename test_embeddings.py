"""
Test script for embeddings and FAISS integration
"""

from embeddings import get_embeddings, test_embeddings
from text_utils import Document
from vector_store import FAISSVectorStore

def test_faiss_creation():
    """Test creating a FAISS index with configured embeddings"""
    print("\n" + "="*60)
    print("Testing FAISS Index Creation with Configured Embeddings")
    print("="*60 + "\n")
    
    try:
        # Get embeddings
        embeddings = get_embeddings()
        
        # Create sample documents
        docs = [
            Document(page_content="AWS Bedrock provides embeddings via Amazon Titan.", metadata={"source": "test1"}),
            Document(page_content="FAISS is a vector similarity search library.", metadata={"source": "test2"}),
            Document(page_content="Architecture standards ensure compliance.", metadata={"source": "test3"}),
        ]
        
        print(f"Creating FAISS index with {len(docs)} test documents...")
        
        # Create FAISS vectorstore
        vectorstore = FAISSVectorStore.from_documents(docs, embeddings)
        
        print("✅ FAISS index created successfully!\n")
        
        # Test similarity search
        query = "What is FAISS?"
        print(f"Testing similarity search with query: '{query}'")
        results = vectorstore.similarity_search(query, k=2)
        
        print(f"\n📊 Top {len(results)} results:")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.page_content[:60]}...")
        
        print("\n✅ All tests passed! Embeddings and FAISS integration working.\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test embeddings first
    success, message, dimension = test_embeddings()
    
    if success:
        # Test FAISS creation
        test_faiss_creation()
    else:
        print("\n⚠️ Skipping FAISS test due to embeddings failure")
