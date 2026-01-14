"""
Text processing utilities to replace LangChain dependencies.
"""

import os
from typing import List, Dict, Any


class Document:
    """Simple document class to replace langchain_core.documents.Document"""
    
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"Document(page_content='{self.page_content[:50]}...', metadata={self.metadata})"


class TextSplitter:
    """
    Text splitter that recursively splits text into chunks.
    Replaces langchain_text_splitters.RecursiveCharacterTextSplitter
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive splitting."""
        chunks = []
        
        def _split_text_recursive(text: str, separators: List[str]) -> List[str]:
            """Recursively split text using different separators."""
            if not separators:
                # No more separators, return chunks based on size
                return self._split_by_size(text)
            
            separator = separators[0]
            remaining_separators = separators[1:]
            
            if separator == "":
                # Empty separator means split by character
                return self._split_by_size(text)
            
            # Split by current separator
            splits = text.split(separator)
            
            # Process each split
            good_splits = []
            for split in splits:
                if len(split) <= self.chunk_size:
                    good_splits.append(split)
                else:
                    # Split is too large, try next separator
                    good_splits.extend(_split_text_recursive(split, remaining_separators))
            
            return good_splits
        
        # Get initial splits
        splits = _split_text_recursive(text, self.separators)
        
        # Merge splits with overlap
        chunks = self._merge_splits(splits)
        
        return chunks
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by size when no separator works."""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks
    
    def _merge_splits(self, splits: List[str]) -> List[str]:
        """Merge small splits and add overlap between chunks."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split)
            
            # If adding this split would exceed chunk_size
            if current_length + split_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = self._join_chunks(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                # Keep last few items for overlap
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                current_chunk = [overlap_text, split] if overlap_text and split else [split]
                current_length = len(overlap_text) + split_length
            else:
                current_chunk.append(split)
                current_length += split_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = self._join_chunks(current_chunk)
            chunks.append(chunk_text)
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _join_chunks(self, chunks: List[str]) -> str:
        """Helper to join chunks with appropriate separator."""
        return " ".join(chunks) if " " in self.separators else "".join(chunks)
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks."""
        chunks = []
        
        for doc in documents:
            text_chunks = self.split_text(doc.page_content)
            
            for chunk_text in text_chunks:
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata=doc.metadata.copy()
                )
                chunks.append(chunk_doc)
        
        return chunks


def load_text_file(file_path: str, encoding: str = 'utf-8') -> str:
    """Load text from a file."""
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def load_documents_from_directory(
    directory: str,
    glob_pattern: str = "**/*.md",
    encoding: str = 'utf-8'
) -> List[Document]:
    """
    Load documents from a directory.
    Replaces langchain_community.document_loaders.DirectoryLoader
    """
    import glob as glob_module
    
    documents = []
    
    # Find all matching files
    pattern = os.path.join(directory, glob_pattern)
    files = glob_module.glob(pattern, recursive=True)
    
    print(f"Found {len(files)} files matching pattern: {glob_pattern}")
    
    for file_path in files:
        try:
            content = load_text_file(file_path, encoding=encoding)
            doc = Document(
                page_content=content,
                metadata={
                    "source": file_path,
                    "filename": os.path.basename(file_path)
                }
            )
            documents.append(doc)
            print(f"  Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  Error loading {file_path}: {e}")
    
    return documents
