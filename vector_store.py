"""
FAISS vector store wrapper without LangChain dependencies.
Uses faiss-cpu and pickle for storing/loading embeddings.
"""

import os
import pickle
import numpy as np
from typing import List, Tuple, Dict, Any

try:
    import faiss
except ImportError:
    raise ImportError("Install faiss-cpu: pip install faiss-cpu")

from text_utils import Document


class FAISSVectorStore:
    """
    FAISS vector store that replaces langchain_community.vectorstores.FAISS
    """
    
    def __init__(self, embeddings_provider, index=None, docstore=None, index_to_docstore_id=None):
        """
        Initialize FAISS vector store.
        
        Args:
            embeddings_provider: Embeddings provider with embed_query and embed_documents methods
            index: FAISS index (optional, will be created if not provided)
            docstore: Document store (optional)
            index_to_docstore_id: Mapping from index to docstore ID (optional)
        """
        self.embeddings = embeddings_provider
        self.index = index
        self.docstore = docstore or {}
        self.index_to_docstore_id = index_to_docstore_id or {}
    
    @classmethod
    def from_documents(cls, documents: List[Document], embeddings_provider):
        """
        Create FAISS index from documents.
        
        Args:
            documents: List of Document objects
            embeddings_provider: Embeddings provider instance
            
        Returns:
            FAISSVectorStore: Initialized vector store
        """
        # Extract texts and metadatas
        texts = [doc.page_content for doc in documents]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings_list = embeddings_provider.embed_documents(texts)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings_list).astype('float32')
        
        # Get dimension
        dimension = embeddings_array.shape[1]
        
        # Create FAISS index (using L2 distance)
        index = faiss.IndexFlatL2(dimension)
        
        # Add vectors to index
        index.add(embeddings_array)
        
        # Create docstore
        docstore = {i: documents[i] for i in range(len(documents))}
        index_to_docstore_id = {i: i for i in range(len(documents))}
        
        print(f"✅ Created FAISS index with {len(documents)} documents (dimension: {dimension})")
        
        return cls(
            embeddings_provider=embeddings_provider,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id
        )
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to existing index.
        
        Args:
            documents: List of Document objects to add
        """
        if not documents:
            return
        
        # Extract texts
        texts = [doc.page_content for doc in documents]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} new documents...")
        embeddings_list = self.embeddings.embed_documents(texts)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings_list).astype('float32')
        
        # Get current count
        current_count = self.index.ntotal
        
        # Add vectors to index
        self.index.add(embeddings_array)
        
        # Update docstore
        for i, doc in enumerate(documents):
            doc_id = current_count + i
            self.docstore[doc_id] = doc
            self.index_to_docstore_id[doc_id] = doc_id
        
        print(f"✅ Added {len(documents)} documents to index (total: {self.index.ntotal})")
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Search for similar documents and return with scores.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS index
        distances, indices = self.index.search(query_vector, k)
        
        # Get documents and scores
        results = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx < 0 or idx >= len(self.docstore):
                continue
            
            doc_id = self.index_to_docstore_id.get(idx, idx)
            doc = self.docstore.get(doc_id)
            
            if doc:
                results.append((doc, float(distance)))
        
        return results
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of Document objects
        """
        results_with_scores = self.similarity_search_with_score(query, k)
        return [doc for doc, score in results_with_scores]
    
    def save_local(self, folder_path: str):
        """
        Save FAISS index and metadata to local folder.
        
        Args:
            folder_path: Path to save the index
        """
        os.makedirs(folder_path, exist_ok=True)
        
        # Save FAISS index
        index_file = os.path.join(folder_path, 'index.faiss')
        faiss.write_index(self.index, index_file)
        
        # Save docstore and metadata
        metadata = {
            'docstore': self.docstore,
            'index_to_docstore_id': self.index_to_docstore_id
        }
        metadata_file = os.path.join(folder_path, 'index.pkl')
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✅ Saved FAISS index to {folder_path}")
    
    @classmethod
    def load_local(cls, folder_path: str, embeddings_provider, allow_dangerous_deserialization: bool = False):
        """
        Load FAISS index from local folder.
        
        Args:
            folder_path: Path to load the index from
            embeddings_provider: Embeddings provider instance
            allow_dangerous_deserialization: Allow loading pickled data (required for compatibility)
            
        Returns:
            FAISSVectorStore: Loaded vector store
        """
        if not allow_dangerous_deserialization:
            raise ValueError(
                "Loading pickled data requires allow_dangerous_deserialization=True. "
                "Only load data from trusted sources."
            )
        
        # Load FAISS index
        index_file = os.path.join(folder_path, 'index.faiss')
        if not os.path.exists(index_file):
            raise FileNotFoundError(f"FAISS index not found at: {index_file}")
        
        index = faiss.read_index(index_file)
        
        # Load metadata
        metadata_file = os.path.join(folder_path, 'index.pkl')
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file not found at: {metadata_file}")
        
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        docstore = metadata.get('docstore', {})
        index_to_docstore_id = metadata.get('index_to_docstore_id', {})
        
        print(f"✅ Loaded FAISS index from {folder_path} ({index.ntotal} vectors)")
        
        return cls(
            embeddings_provider=embeddings_provider,
            index=index,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id
        )
