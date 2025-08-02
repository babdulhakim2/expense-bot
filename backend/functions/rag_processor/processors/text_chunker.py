"""
Advanced Chunking Strategies for RAG

Implements various document chunking methods optimized for different document types
and retrieval scenarios.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    logging.warning(f"Chunking dependencies not installed: {e}")
    SentenceTransformer = None
    np = None

# For type hints when dependencies are missing
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING or np is None:
    import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ChunkMetadata:
    """Metadata for a document chunk"""
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_type: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    semantic_density: Optional[float] = None
    estimated_tokens: Optional[int] = None

@dataclass
class Chunk:
    """Document chunk with content and metadata"""
    content: str
    metadata: ChunkMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary format"""
        return {
            'content': self.content,
            'metadata': {
                'chunk_id': self.metadata.chunk_id,
                'document_id': self.metadata.document_id,
                'chunk_index': self.metadata.chunk_index,
                'chunk_type': self.metadata.chunk_type,
                'start_char': self.metadata.start_char,
                'end_char': self.metadata.end_char,
                'page_number': self.metadata.page_number,
                'section_title': self.metadata.section_title,
                'parent_chunk_id': self.metadata.parent_chunk_id,
                'semantic_density': self.metadata.semantic_density,
                'estimated_tokens': self.metadata.estimated_tokens
            }
        }

class ChunkingStrategy:
    """Base class for chunking strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def chunk_document(self, 
                      text: str, 
                      document_id: str,
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Chunk a document into smaller pieces
        
        Args:
            text: Document text content
            document_id: Unique document identifier
            metadata: Additional document metadata
            
        Returns:
            List of document chunks
        """
        raise NotImplementedError("Subclasses must implement chunk_document")
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int, content: str) -> str:
        """Generate unique chunk ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{document_id}_chunk_{chunk_index}_{content_hash}"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple estimation: ~4 characters per token on average
        return max(1, len(text) // 4)


class FixedSizeChunking(ChunkingStrategy):
    """Fixed-size chunking with overlap"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 overlap: int = 200,
                 preserve_sentences: bool = True):
        """
        Initialize fixed-size chunking
        
        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
            preserve_sentences: Whether to preserve sentence boundaries
        """
        super().__init__("fixed_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_sentences = preserve_sentences
    
    def chunk_document(self, 
                      text: str, 
                      document_id: str,
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Chunk document using fixed-size strategy"""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))
            
            # Try to preserve sentence boundaries
            if self.preserve_sentences and end < len(text):
                # Look for sentence endings within a reasonable distance
                search_start = max(start + self.chunk_size - 100, start + self.chunk_size // 2)
                search_text = text[search_start:end + 100]
                
                sentence_endings = []
                for match in re.finditer(r'[.!?]\s+', search_text):
                    sentence_endings.append(search_start + match.end())
                
                if sentence_endings:
                    # Choose the sentence ending closest to target size
                    target_pos = start + self.chunk_size
                    best_end = min(sentence_endings, key=lambda x: abs(x - target_pos))
                    end = min(best_end, len(text))
            
            # Extract chunk content
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._generate_chunk_id(document_id, chunk_index, chunk_content),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    chunk_type="fixed_size",
                    start_char=start,
                    end_char=end,
                    estimated_tokens=self._estimate_tokens(chunk_content)
                )
                
                chunks.append(Chunk(content=chunk_content, metadata=chunk_metadata))
                chunk_index += 1
            
            # Move to next chunk with overlap
            start = max(start + self.chunk_size - self.overlap, end)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks


class SemanticChunking(ChunkingStrategy):
    """Semantic chunking based on sentence embeddings"""
    
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 max_chunk_size: int = 1500,
                 min_chunk_size: int = 100,
                 similarity_threshold: float = 0.7):
        """
        Initialize semantic chunking
        
        Args:
            embedding_model: SentenceTransformer model name
            max_chunk_size: Maximum chunk size in characters
            min_chunk_size: Minimum chunk size in characters
            similarity_threshold: Similarity threshold for grouping sentences
        """
        super().__init__("semantic")
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.similarity_threshold = similarity_threshold
        
        if SentenceTransformer:
            self.embedding_model = SentenceTransformer(embedding_model)
        else:
            self.embedding_model = None
            logger.warning("SentenceTransformer not available, falling back to paragraph chunking")
    
    def chunk_document(self, 
                      text: str, 
                      document_id: str,
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Chunk document using semantic similarity"""
        if not text.strip():
            return []
        
        if not self.embedding_model:
            # Fallback to paragraph-based chunking
            return self._fallback_paragraph_chunking(text, document_id, metadata)
        
        try:
            # Split into sentences
            sentences = self._split_into_sentences(text)
            
            if len(sentences) <= 1:
                # Single sentence or empty, return as-is
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._generate_chunk_id(document_id, 0, text),
                    document_id=document_id,
                    chunk_index=0,
                    chunk_type="semantic_single",
                    start_char=0,
                    end_char=len(text),
                    estimated_tokens=self._estimate_tokens(text)
                )
                return [Chunk(content=text.strip(), metadata=chunk_metadata)]
            
            # Generate embeddings for sentences
            embeddings = self.embedding_model.encode(sentences)
            
            # Group sentences based on semantic similarity
            chunks = self._group_sentences_semantically(
                sentences, embeddings, document_id
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {str(e)}")
            # Fallback to paragraph chunking
            return self._fallback_paragraph_chunking(text, document_id, metadata)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could be improved with NLTK/spaCy
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _group_sentences_semantically(self, 
                                    sentences: List[str], 
                                    embeddings: np.ndarray,
                                    document_id: str) -> List[Chunk]:
        """Group sentences based on semantic similarity"""
        if not sentences:
            return []
        
        chunks = []
        current_chunk_sentences = [sentences[0]]
        current_chunk_embeddings = [embeddings[0]]
        chunk_index = 0
        start_char = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity with current chunk
            current_chunk_avg = np.mean(current_chunk_embeddings, axis=0)
            similarity = np.dot(current_chunk_avg, embeddings[i]) / (
                np.linalg.norm(current_chunk_avg) * np.linalg.norm(embeddings[i])
            )
            
            # Check if we should start a new chunk
            current_chunk_text = ' '.join(current_chunk_sentences)
            should_split = (
                similarity < self.similarity_threshold or
                len(current_chunk_text + ' ' + sentences[i]) > self.max_chunk_size
            )
            
            if should_split and len(current_chunk_text) >= self.min_chunk_size:
                # Create chunk from current sentences
                chunk_content = current_chunk_text.strip()
                end_char = start_char + len(chunk_content)
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._generate_chunk_id(document_id, chunk_index, chunk_content),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    chunk_type="semantic",
                    start_char=start_char,
                    end_char=end_char,
                    semantic_density=float(similarity),
                    estimated_tokens=self._estimate_tokens(chunk_content)
                )
                
                chunks.append(Chunk(content=chunk_content, metadata=chunk_metadata))
                
                # Start new chunk
                current_chunk_sentences = [sentences[i]]
                current_chunk_embeddings = [embeddings[i]]
                chunk_index += 1
                start_char = end_char + 1
            else:
                # Add to current chunk
                current_chunk_sentences.append(sentences[i])
                current_chunk_embeddings.append(embeddings[i])
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_content = ' '.join(current_chunk_sentences).strip()
            end_char = start_char + len(chunk_content)
            
            chunk_metadata = ChunkMetadata(
                chunk_id=self._generate_chunk_id(document_id, chunk_index, chunk_content),
                document_id=document_id,
                chunk_index=chunk_index,
                chunk_type="semantic",
                start_char=start_char,
                end_char=end_char,
                estimated_tokens=self._estimate_tokens(chunk_content)
            )
            
            chunks.append(Chunk(content=chunk_content, metadata=chunk_metadata))
        
        return chunks
    
    def _fallback_paragraph_chunking(self, 
                                   text: str, 
                                   document_id: str,
                                   metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Fallback to paragraph-based chunking"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        chunk_index = 0
        current_chunk = ""
        start_char = 0
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) > self.max_chunk_size and current_chunk:
                # Create chunk
                chunk_content = current_chunk.strip()
                end_char = start_char + len(chunk_content)
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=self._generate_chunk_id(document_id, chunk_index, chunk_content),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    chunk_type="paragraph_fallback",
                    start_char=start_char,
                    end_char=end_char,
                    estimated_tokens=self._estimate_tokens(chunk_content)
                )
                
                chunks.append(Chunk(content=chunk_content, metadata=chunk_metadata))
                
                current_chunk = paragraph
                chunk_index += 1
                start_char = end_char + 2  # Account for paragraph separation
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunk_content = current_chunk.strip()
            end_char = start_char + len(chunk_content)
            
            chunk_metadata = ChunkMetadata(
                chunk_id=self._generate_chunk_id(document_id, chunk_index, chunk_content),
                document_id=document_id,
                chunk_index=chunk_index,
                chunk_type="paragraph_fallback",
                start_char=start_char,
                end_char=end_char,
                estimated_tokens=self._estimate_tokens(chunk_content)
            )
            
            chunks.append(Chunk(content=chunk_content, metadata=chunk_metadata))
        
        return chunks


class HierarchicalChunking(ChunkingStrategy):
    """Hierarchical chunking with parent-child relationships"""
    
    def __init__(self, 
                 large_chunk_size: int = 2000,
                 small_chunk_size: int = 500,
                 overlap: int = 100):
        """
        Initialize hierarchical chunking
        
        Args:
            large_chunk_size: Size of parent chunks
            small_chunk_size: Size of child chunks
            overlap: Overlap between chunks
        """
        super().__init__("hierarchical")
        self.large_chunk_size = large_chunk_size
        self.small_chunk_size = small_chunk_size
        self.overlap = overlap
    
    def chunk_document(self, 
                      text: str, 
                      document_id: str,
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Chunk document hierarchically"""
        if not text.strip():
            return []
        
        all_chunks = []
        
        # Create large parent chunks
        parent_chunker = FixedSizeChunking(
            chunk_size=self.large_chunk_size,
            overlap=self.overlap,
            preserve_sentences=True
        )
        parent_chunks = parent_chunker.chunk_document(text, document_id, metadata)
        
        # Create smaller child chunks for each parent
        child_chunker = FixedSizeChunking(
            chunk_size=self.small_chunk_size,
            overlap=self.overlap // 2,
            preserve_sentences=True
        )
        
        for parent_chunk in parent_chunks:
            # Add parent chunk
            parent_chunk.metadata.chunk_type = "hierarchical_parent"
            all_chunks.append(parent_chunk)
            
            # Create child chunks
            child_chunks = child_chunker.chunk_document(
                parent_chunk.content, 
                document_id, 
                metadata
            )
            
            for child_chunk in child_chunks:
                # Update child metadata
                child_chunk.metadata.chunk_type = "hierarchical_child"
                child_chunk.metadata.parent_chunk_id = parent_chunk.metadata.chunk_id
                child_chunk.metadata.chunk_id = self._generate_chunk_id(
                    document_id, 
                    len(all_chunks), 
                    child_chunk.content
                )
                all_chunks.append(child_chunk)
        
        return all_chunks


class ExpenseDocumentChunking(ChunkingStrategy):
    """Specialized chunking for expense documents"""
    
    def __init__(self):
        """Initialize expense document chunking"""
        super().__init__("expense_document")
        self.section_patterns = {
            'header': r'(?i)(invoice|receipt|bill|statement).*?(\n|$)',
            'vendor': r'(?i)(vendor|merchant|company|business).*?(\n|$)',
            'amount': r'(?i)(total|amount|sum|price|cost).*?(\$|USD|\d+\.\d{2})',
            'date': r'(?i)(date|issued|transaction).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'items': r'(?i)(item|description|product|service).*?(?=\n(?:total|amount|tax)|$)',
            'tax': r'(?i)(tax|vat|gst).*?(\$|USD|\d+\.\d{2})',
            'footer': r'(?i)(thank you|visit again|policy|terms).*?$'
        }
    
    def chunk_document(self, 
                      text: str, 
                      document_id: str,
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """Chunk expense document by sections"""
        if not text.strip():
            return []
        
        chunks = []
        chunk_index = 0
        processed_positions = set()
        
        # Try to identify and chunk by sections
        for section_name, pattern in self.section_patterns.items():
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                start, end = match.span()
                
                # Avoid overlapping chunks
                if any(pos in processed_positions for pos in range(start, end)):
                    continue
                
                section_text = text[start:end].strip()
                if section_text and len(section_text) > 10:  # Minimum content threshold
                    chunk_metadata = ChunkMetadata(
                        chunk_id=self._generate_chunk_id(document_id, chunk_index, section_text),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        chunk_type="expense_section",
                        start_char=start,
                        end_char=end,
                        section_title=section_name,
                        estimated_tokens=self._estimate_tokens(section_text)
                    )
                    
                    chunks.append(Chunk(content=section_text, metadata=chunk_metadata))
                    chunk_index += 1
                    
                    # Mark positions as processed
                    processed_positions.update(range(start, end))
        
        # Handle remaining unprocessed text
        remaining_text = ""
        last_end = 0
        
        for start in sorted(processed_positions):
            if start > last_end:
                remaining_text += text[last_end:start]
            last_end = max(last_end, start + 1)
        
        if last_end < len(text):
            remaining_text += text[last_end:]
        
        # Chunk remaining text using fixed-size strategy
        if remaining_text.strip():
            fixed_chunker = FixedSizeChunking(chunk_size=500, overlap=50)
            remaining_chunks = fixed_chunker.chunk_document(
                remaining_text, document_id, metadata
            )
            
            for chunk in remaining_chunks:
                chunk.metadata.chunk_type = "expense_general"
                chunk.metadata.chunk_index = chunk_index
                chunk.metadata.chunk_id = self._generate_chunk_id(
                    document_id, chunk_index, chunk.content
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks


class SemanticTextChunker:
    """Orchestrates different chunking strategies based on document type"""
    
    def __init__(self):
        """Initialize chunking orchestrator"""
        self.strategies = {
            'expense_document': ExpenseDocumentChunking(),
            'financial_statement': SemanticChunking(max_chunk_size=1000),
            'contract': HierarchicalChunking(large_chunk_size=1500, small_chunk_size=400),
            'report': SemanticChunking(max_chunk_size=1200),
            'general_document': FixedSizeChunking(chunk_size=800, overlap=100)
        }
        
        # Default strategy
        self.default_strategy = FixedSizeChunking(chunk_size=1000, overlap=200)
    
    def chunk_document(self, 
                      text: str,
                      document_id: str,
                      document_type: str = 'general_document',
                      metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Chunk document using appropriate strategy
        
        Args:
            text: Document text content
            document_id: Unique document identifier
            document_type: Type of document (determines chunking strategy)
            metadata: Additional document metadata
            
        Returns:
            List of document chunks
        """
        try:
            # Select chunking strategy
            strategy = self.strategies.get(document_type, self.default_strategy)
            
            logger.info(f"Chunking document {document_id} using {strategy.name} strategy")
            
            # Perform chunking
            chunks = strategy.chunk_document(text, document_id, metadata)
            
            # Add common metadata to all chunks
            for chunk in chunks:
                if metadata:
                    for key, value in metadata.items():
                        if not hasattr(chunk.metadata, key):
                            setattr(chunk.metadata, key, value)
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document {document_id}: {str(e)}")
            # Fallback to default strategy
            return self.default_strategy.chunk_document(text, document_id, metadata)
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available chunking strategies"""
        return list(self.strategies.keys())
    
    def add_strategy(self, document_type: str, strategy: ChunkingStrategy):
        """Add or update a chunking strategy"""
        self.strategies[document_type] = strategy
        logger.info(f"Added/updated chunking strategy for {document_type}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on chunking orchestrator"""
        try:
            status = 'healthy'
            strategy_status = {}
            
            # Test each strategy with sample text
            sample_text = "This is a sample document for testing chunking strategies. It contains multiple sentences to verify that the chunking works correctly."
            
            for doc_type, strategy in self.strategies.items():
                try:
                    chunks = strategy.chunk_document(sample_text, "test_doc")
                    strategy_status[doc_type] = {
                        'status': 'healthy',
                        'chunks_created': len(chunks),
                        'strategy_name': strategy.name
                    }
                except Exception as e:
                    strategy_status[doc_type] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'strategy_name': strategy.name
                    }
                    status = 'warning'
            
            return {
                'status': status,
                'total_strategies': len(self.strategies),
                'strategy_status': strategy_status,
                'semantic_chunking_available': SentenceTransformer is not None
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }