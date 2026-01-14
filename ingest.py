import os
from text_utils import Document, TextSplitter, load_documents_from_directory
from vector_store import FAISSVectorStore
import confluence_sync
from embeddings import get_embeddings

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
    documents = load_documents_from_directory(
        directory=docs_path,
        glob_pattern="**/*.md",
        encoding='utf-8'
    )
    
    print(f"Loaded {len(documents)} documents")
    
    # Split documents into chunks
    # 1000 characters with 200 character overlap
    text_splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")
    
    # Initialize embeddings using configured provider
    print("Initializing embeddings model...")
    embeddings = get_embeddings()
    
    # Create FAISS vectorstore
    print("Creating FAISS vectorstore...")
    vectorstore = FAISSVectorStore.from_documents(chunks, embeddings)
    
    # Save the vectorstore to local folder
    index_path = os.path.join(os.path.dirname(__file__), 'faiss_index')
    print(f"Saving FAISS index to: {index_path}")
    vectorstore.save_local(index_path)
    
    print(f"✅ Successfully created FAISS index with {len(chunks)} chunks")
    print(f"Index saved to: {index_path}")
    
    return vectorstore


def ingest_from_confluence(space_key=None, labels=None, merge_with_existing=True):
    """
    Fetch pages from Confluence and add them to FAISS index.
    
    Args:
        space_key (str): Confluence space key. If None, uses config value
        labels (list): List of labels to filter pages. If None, uses config value
        merge_with_existing (bool): If True, merge with existing index. If False, replace it.
        
    Returns:
        tuple: (success, message, num_pages)
    """
    # Fetch pages from Confluence
    print("Fetching pages from Confluence...")
    success, pages, error_msg = confluence_sync.fetch_space_pages(space_key, labels)
    
    if not success:
        return False, f"❌ Failed to fetch Confluence pages: {error_msg}", 0
    
    if not pages:
        return False, "⚠️ No pages found matching the criteria", 0
    
    print(f"✅ Fetched {len(pages)} pages from Confluence")
    
    # Convert Confluence pages to documents
    documents = []
    for page in pages:
        doc = Document(
            page_content=page['content'],
            metadata={
                'source': f"confluence:{page['title']}",
                'title': page['title'],
                'confluence_id': page['id'],
                'version': page['version']
            }
        )
        documents.append(doc)
    
    # Split documents into chunks
    text_splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    
    print("Splitting Confluence pages into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks from Confluence pages")
    
    # Initialize embeddings using configured provider
    print("Initializing embeddings model...")
    embeddings = get_embeddings()
    
    index_path = os.path.join(os.path.dirname(__file__), 'faiss_index')
    
    # Merge with existing or create new
    if merge_with_existing and os.path.exists(os.path.join(index_path, 'index.faiss')):
        print("Loading existing FAISS index...")
        try:
            existing_vectorstore = FAISSVectorStore.load_local(
                index_path, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("Merging Confluence pages with existing index...")
            existing_vectorstore.add_documents(chunks)
            vectorstore = existing_vectorstore
            print(f"✅ Merged {len(chunks)} Confluence chunks with existing index")
        except Exception as e:
            print(f"⚠️ Could not load existing index: {e}. Creating new index...")
            vectorstore = FAISSVectorStore.from_documents(chunks, embeddings)
    else:
        print("Creating new FAISS index from Confluence pages...")
        vectorstore = FAISSVectorStore.from_documents(chunks, embeddings)
    
    # Save the updated vectorstore
    print(f"Saving FAISS index to: {index_path}")
    vectorstore.save_local(index_path)
    
    success_msg = f"✅ Successfully synced {len(pages)} pages ({len(chunks)} chunks) from Confluence"
    print(success_msg)
    
    return True, success_msg, len(pages)


if __name__ == "__main__":
    try:
        ingest_documents()
    except Exception as e:
        print(f"Error during ingestion: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
