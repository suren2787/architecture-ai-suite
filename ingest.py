import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def ingest_documents():
    """
    Load Markdown files from /docs folder, split into chunks, create embeddings,
    and save to FAISS index.
    """
    # Path to docs folder
    docs_path = os.path.join(os.path.dirname(__file__), 'docs')
    
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"Docs folder not found at: {docs_path}")
    
    print(f"Loading Markdown files from: {docs_path}")
    
    # Load all Markdown files from the docs folder
    # Use TextLoader to avoid requiring the unstructured package
    loader = DirectoryLoader(
        docs_path,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'},
        show_progress=True
    )
    documents = loader.load()
    
    print(f"Loaded {len(documents)} documents")
    
    # Split documents into chunks
    # 1000 characters with 200 character overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    
    # Initialize embeddings using HuggingFace model (runs locally)
    print("Initializing embeddings model (this may take a moment on first run)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Create FAISS vectorstore
    print("Creating FAISS vectorstore...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Save the vectorstore to local folder
    index_path = os.path.join(os.path.dirname(__file__), 'faiss_index')
    print(f"Saving FAISS index to: {index_path}")
    vectorstore.save_local(index_path)
    
    print(f"✅ Successfully created FAISS index with {len(chunks)} chunks")
    print(f"Index saved to: {index_path}")
    
    return vectorstore


if __name__ == "__main__":
    try:
        ingest_documents()
    except Exception as e:
        print(f"Error during ingestion: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
