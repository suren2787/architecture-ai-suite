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
        Supports loading indices created with LangChain for backward compatibility.
        
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
        
        # Load metadata with LangChain compatibility
        metadata_file = os.path.join(folder_path, 'index.pkl')
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file not found at: {metadata_file}")
        
        # Create stub classes for LangChain objects we need to unpickle
        class InMemoryDocstore:
            """Stub for langchain_community.docstore.in_memory.InMemoryDocstore"""
            def __init__(self, _dict=None):
                self._dict = _dict or {}
            
            def __setstate__(self, state):
                self.__dict__.update(state)
        
        class LangChainDocument:
            """Stub for LangChain Document with proper unpickling support"""
            def __init__(self, page_content="", metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}
            
            def __setstate__(self, state):
                # Handle unpickling
                self.__dict__.update(state)
            
            def __getstate__(self):
                return self.__dict__
        
        # Create a custom unpickler that can handle LangChain objects
        class LangChainCompatibleUnpickler(pickle.Unpickler):
            def find_class(self, module, name):
                # Map LangChain Document to our stub class
                if 'langchain' in module and name == 'Document':
                    return LangChainDocument
                # Handle InMemoryDocstore
                if 'langchain' in module and 'InMemoryDocstore' in name:
                    return InMemoryDocstore
                # For other LangChain classes, try standard pickle
                if 'langchain' in module:
                    try:
                        return super().find_class(module, name)
                    except (ImportError, AttributeError):
                        print(f"⚠️  Using stub for unknown LangChain class: {module}.{name}")
                        # Return a simple class that can be unpickled
                        return type(name, (), {})
                return super().find_class(module, name)
        
        with open(metadata_file, 'rb') as f:
            metadata = LangChainCompatibleUnpickler(f).load()
        
        # Handle different metadata formats
        # LangChain format: (docstore, index_to_docstore_id)
        # Our format: {'docstore': ..., 'index_to_docstore_id': ...}
        if isinstance(metadata, tuple) and len(metadata) == 2:
            # LangChain format
            docstore_obj, index_to_docstore_id = metadata
        elif isinstance(metadata, dict):
            # Our format
            docstore_obj = metadata.get('docstore', {})
            index_to_docstore_id = metadata.get('index_to_docstore_id', {})
        else:
            raise ValueError(f"Unknown metadata format: {type(metadata)}")
        
        # Handle different docstore formats
        if hasattr(docstore_obj, '_dict'):
            # LangChain InMemoryDocstore - the _dict maps UUIDs to Documents
            # But index_to_docstore_id maps indices to UUIDs
            docstore_dict = docstore_obj._dict
            
            # Rebuild docstore to map indices directly to documents
            docstore = {}
            for idx, uuid in index_to_docstore_id.items():
                if uuid in docstore_dict:
                    docstore[idx] = docstore_dict[uuid]
        elif isinstance(docstore_obj, dict):
            # Already a dict
            docstore = docstore_obj
        else:
            # Try to convert to dict
            docstore = dict(docstore_obj) if docstore_obj else {}
        
        # Convert LangChain documents to our Document class if needed
        from text_utils import Document as OurDocument
        converted_docstore = {}
        for key, value in docstore.items():
            # Check if this is a document-like object
            is_document = (
                hasattr(value, 'page_content') or
                (hasattr(value, '__dict__') and isinstance(value.__dict__.get('__dict__'), dict) and 'page_content' in value.__dict__.get('__dict__', {})) or
                (hasattr(value, '__dict__') and 'page_content' in value.__dict__)
            )
            
            if is_document:
                # This looks like a document, ensure it's our Document class
                if not isinstance(value, OurDocument):
                    # Try different ways to extract page_content and metadata
                    page_content = None
                    metadata = None
                    
                    # Method 1: Direct attributes
                    if hasattr(value, 'page_content'):
                        page_content = value.page_content
                        metadata = getattr(value, 'metadata', {})
                    # Method 2: __dict__ containing page_content directly
                    elif hasattr(value, '__dict__') and 'page_content' in value.__dict__:
                        page_content = value.__dict__['page_content']
                        metadata = value.__dict__.get('metadata', {})
                    # Method 3: Pydantic model with nested __dict__
                    elif hasattr(value, '__dict__') and isinstance(value.__dict__.get('__dict__'), dict):
                        inner_dict = value.__dict__['__dict__']
                        page_content = inner_dict.get('page_content', '')
                        metadata = inner_dict.get('metadata', {})
                    
                    if page_content is not None:
                        converted_docstore[key] = OurDocument(
                            page_content=page_content,
                            metadata=metadata
                        )
                    else:
                        # Fallback: keep original if we can't extract content
                        converted_docstore[key] = value
                else:
                    converted_docstore[key] = value
            else:
                converted_docstore[key] = value
        
        # For LangChain indices, index_to_docstore_id maps to UUIDs, but we've already
        # remapped to use indices directly, so reset it
        if isinstance(metadata, tuple):
            # Create simple index mapping for our format
            index_to_docstore_id = {i: i for i in range(len(converted_docstore))}
        
        print(f"✅ Loaded FAISS index from {folder_path} ({index.ntotal} vectors)")
        if len(docstore) != len(converted_docstore):
            print(f"   Converted {len(docstore)} -> {len(converted_docstore)} documents")
        
        return cls(
            embeddings_provider=embeddings_provider,
            index=index,
            docstore=converted_docstore,
            index_to_docstore_id=index_to_docstore_id
        )
