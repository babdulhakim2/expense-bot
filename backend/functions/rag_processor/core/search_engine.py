"""
RAG Search Service - Main API Interface

Provides high-level search capabilities that orchestrate vector search, ColBERT retrieval,
query enhancement, and result post-processing.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from storage.lancedb_store import ExpenseDocumentVectorStore
from core.document_indexer import ExpenseDocumentIndexer

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Structured search result"""
    content: str
    document_id: str
    chunk_id: str
    score: float
    metadata: Dict[str, Any]
    retrieval_method: str
    business_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'content': self.content,
            'document_id': self.document_id,
            'chunk_id': self.chunk_id,
            'score': self.score,
            'metadata': self.metadata,
            'retrieval_method': self.retrieval_method,
            'business_id': self.business_id
        }

@dataclass
class SearchResponse:
    """Complete search response with metadata"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    search_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'results': [result.to_dict() for result in self.results],
            'total_results': self.total_results,
            'processing_time': self.processing_time,
            'search_metadata': self.search_metadata
        }


class QueryEnhancer:
    """Enhances search queries for better retrieval"""
    
    def __init__(self):
        """Initialize query enhancer"""
        self.expense_keywords = {
            'amount': ['total', 'cost', 'price', 'sum', 'charge', 'fee'],
            'vendor': ['merchant', 'company', 'business', 'store', 'supplier'],
            'date': ['when', 'date', 'time', 'day', 'month', 'year'],
            'category': ['type', 'category', 'kind', 'classification'],
            'payment': ['paid', 'payment', 'transaction', 'purchase', 'buy']
        }
        
        # Common financial brands and their context
        self.brand_expansions = {
            'revolut': 'revolut card payment transaction bank',
            'paypal': 'paypal payment transaction online',
            'stripe': 'stripe payment processing charge',
            'amazon': 'amazon purchase order shopping',
            'uber': 'uber ride transport taxi',
            'starbucks': 'starbucks coffee cafe purchase',
            'walmart': 'walmart store shopping purchase',
            'target': 'target store shopping retail'
        }
        
        self.query_patterns = [
            (r'\$(\d+(?:\.\d{2})?)', r'amount \1 dollars'),  # $50.00 -> amount 50.00 dollars
            (r'(\d+(?:\.\d{2})?)\s*dollars?', r'amount \1'),  # 50 dollars -> amount 50
            (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'date \1'),  # 12/25/2023 -> date 12/25/2023
            (r'how much', 'amount cost total'),
            (r'who paid', 'vendor merchant company'),
            (r'what for', 'category description purpose')
        ]
    
    def enhance_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        Enhance query for better retrieval
        
        Args:
            query: Original search query
            context: Additional context for enhancement
            
        Returns:
            Enhanced query string
        """
        try:
            enhanced = query.lower().strip()
            
            # Check if query is a single word that might be a brand
            words = enhanced.split()
            if len(words) == 1:
                single_word = words[0]
                # Check for brand expansions
                if single_word in self.brand_expansions:
                    enhanced = self.brand_expansions[single_word]
                    logger.debug(f"Expanded brand query: '{single_word}' -> '{enhanced}'")
            
            # Apply pattern transformations
            for pattern, replacement in self.query_patterns:
                enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
            
            # Add context-specific keywords
            if context:
                business_id = context.get('business_id')
                date_range = context.get('date_range')
                document_type = context.get('document_type')
                
                if date_range:
                    enhanced += f" date {date_range}"
                
                if document_type:
                    enhanced += f" {document_type}"
            
            # Expand keywords
            words = enhanced.split()
            expanded_words = []
            
            for word in words:
                expanded_words.append(word)
                
                # Add synonyms for expense-related terms
                for category, synonyms in self.expense_keywords.items():
                    if word in synonyms:
                        expanded_words.extend([s for s in synonyms if s != word])
                        break
            
            enhanced = ' '.join(expanded_words)
            
            logger.debug(f"Enhanced query: '{query}' -> '{enhanced}'")
            return enhanced
            
        except Exception as e:
            logger.warning(f"Query enhancement failed: {str(e)}")
            return query
    
    def extract_filters(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract filters from query
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (cleaned_query, filters)
        """
        filters = {}
        cleaned_query = query
        
        try:
            # Extract amount filters
            amount_matches = re.findall(r'amount\s*([><=]+)\s*(\d+(?:\.\d{2})?)', query, re.IGNORECASE)
            for operator, amount in amount_matches:
                filters['amount_filter'] = {'operator': operator, 'value': float(amount)}
                cleaned_query = re.sub(rf'amount\s*{re.escape(operator)}\s*{re.escape(amount)}', '', cleaned_query, flags=re.IGNORECASE)
            
            # Extract date filters
            date_matches = re.findall(r'(?:after|before|on)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', query, re.IGNORECASE)
            if date_matches:
                filters['date_filter'] = date_matches[0]
                for match in date_matches:
                    cleaned_query = re.sub(rf'(?:after|before|on)\s*{re.escape(match)}', '', cleaned_query, flags=re.IGNORECASE)
            
            # Extract category filters
            category_matches = re.findall(r'category[:\s]+([^\s,]+)', query, re.IGNORECASE)
            if category_matches:
                filters['category'] = category_matches[0]
                for match in category_matches:
                    cleaned_query = re.sub(rf'category[:\s]+{re.escape(match)}', '', cleaned_query, flags=re.IGNORECASE)
            
            # Clean up extra whitespace
            cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
            
            return cleaned_query, filters
            
        except Exception as e:
            logger.warning(f"Filter extraction failed: {str(e)}")
            return query, {}


class ResultPostProcessor:
    """Post-processes search results for better presentation"""
    
    def __init__(self):
        """Initialize result post-processor"""
        self.highlight_patterns = [
            r'\$\d+(?:\.\d{2})?',  # Dollar amounts
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Dates
            r'total|amount|sum|cost|price',  # Amount keywords
            r'invoice|receipt|bill|statement'  # Document types
        ]
    
    def process_results(self, 
                       results: List[Dict[str, Any]], 
                       query: str,
                       max_results: int = 10) -> List[SearchResult]:
        """
        Post-process search results
        
        Args:
            results: Raw search results
            query: Original search query
            max_results: Maximum number of results to return
            
        Returns:
            List of processed SearchResult objects
        """
        try:
            processed_results = []
            
            for result in results[:max_results]:
                # Extract required fields
                content = result.get('content', '')
                document_id = result.get('document_id', '')
                chunk_id = result.get('id', result.get('chunk_id', ''))
                score = result.get('score', result.get('similarity_score', result.get('hybrid_score', 0.0)))
                metadata = result.get('metadata', {})
                retrieval_method = result.get('retrieval_method', 'unknown')
                business_id = result.get('business_id', '')
                
                # Enhance content with highlights
                highlighted_content = self._highlight_content(content, query)
                
                # Create SearchResult object
                search_result = SearchResult(
                    content=highlighted_content,
                    document_id=document_id,
                    chunk_id=chunk_id,
                    score=float(score),
                    metadata=metadata,
                    retrieval_method=retrieval_method,
                    business_id=business_id
                )
                
                processed_results.append(search_result)
            
            # Sort by score (descending)
            processed_results.sort(key=lambda x: x.score, reverse=True)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error post-processing results: {str(e)}")
            return []
    
    def _highlight_content(self, content: str, query: str) -> str:
        """Add highlights to content based on query terms"""
        try:
            highlighted = content
            query_terms = query.lower().split()
            
            # Highlight query terms
            for term in query_terms:
                if len(term) > 2:  # Skip very short terms
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    highlighted = pattern.sub(f'**{term}**', highlighted)
            
            # Highlight important patterns
            for pattern in self.highlight_patterns:
                highlighted = re.sub(
                    f'({pattern})', 
                    r'**\1**', 
                    highlighted, 
                    flags=re.IGNORECASE
                )
            
            return highlighted
            
        except Exception as e:
            logger.warning(f"Content highlighting failed: {str(e)}")
            return content
    
    def deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity"""
        try:
            deduplicated = []
            seen_content = set()
            
            for result in results:
                # Create a normalized version of content for comparison
                normalized = re.sub(r'\s+', ' ', result.content.lower().strip())
                
                # Check for exact duplicates
                if normalized in seen_content:
                    continue
                
                # Check for near-duplicates (>90% similarity)
                is_duplicate = False
                for seen in seen_content:
                    if self._calculate_similarity(normalized, seen) > 0.9:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    deduplicated.append(result)
                    seen_content.add(normalized)
            
            return deduplicated
            
        except Exception as e:
            logger.warning(f"Deduplication failed: {str(e)}")
            return results
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        try:
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            if not words1 and not words2:
                return 1.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0


class ExpenseDocumentSearchEngine:
    """
    Main RAG search service that orchestrates all components
    """
    
    def __init__(self,
                 vector_store: ExpenseDocumentVectorStore = None,
                 document_indexer: ExpenseDocumentIndexer = None,
                 enable_query_enhancement: bool = True,
                 enable_result_postprocessing: bool = True):
        """
        Initialize Expense Document Search Engine
        
        Args:
            vector_store: Vector store instance for embeddings
            document_indexer: Document indexer for processing new documents
            enable_query_enhancement: Whether to enhance search queries
            enable_result_postprocessing: Whether to post-process results
        """
        # Initialize components
        self.vector_store = vector_store or ExpenseDocumentVectorStore()
        self.document_indexer = document_indexer or ExpenseDocumentIndexer(
            vector_store=self.vector_store
        )
        
        # Set reference for caching completed jobs
        self.document_indexer._search_engine_ref = self
        
        # Initialize enhancement components
        self.query_enhancer = QueryEnhancer() if enable_query_enhancement else None
        self.result_processor = ResultPostProcessor() if enable_result_postprocessing else None
        
        # Configuration
        self.config = {
            'default_limit': 10,
            'max_limit': 50,
            'similarity_threshold': 0.3,
            'enable_deduplication': True
        }
        
        # Document cache for avoiding reprocessing
        self.document_cache = {}  # document_hash -> job_info
        self.cache_ttl = 3600  # 1 hour cache TTL
        
        logger.info("Initialized RAGSearchService")
    
    def search(self,
               query: str,
               business_id: str,
               limit: int = 10,
               search_method: str = 'auto',
               filters: Dict[str, Any] = None,
               enhance_query: bool = True) -> SearchResponse:
        """
        Perform comprehensive search across indexed documents
        
        Args:
            query: Search query string
            business_id: Business ID to filter results
            limit: Maximum number of results to return
            search_method: Search method ('vector', 'colbert', 'hybrid', 'auto')
            filters: Additional filters to apply
            enhance_query: Whether to enhance the query
            
        Returns:
            SearchResponse with results and metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Searching: '{query}' for business {business_id}")
            
            # Validate inputs
            if not query.strip():
                return SearchResponse(
                    query=query,
                    results=[],
                    total_results=0,
                    processing_time=0.0,
                    search_metadata={'error': 'Empty query'}
                )
            
            limit = min(limit, self.config['max_limit'])
            original_query = query
            
            # Query enhancement
            enhanced_query = query
            extracted_filters = filters or {}
            
            if enhance_query and self.query_enhancer:
                enhanced_query = self.query_enhancer.enhance_query(
                    query, 
                    context={'business_id': business_id}
                )
                
                # Extract filters from query
                cleaned_query, query_filters = self.query_enhancer.extract_filters(enhanced_query)
                enhanced_query = cleaned_query
                extracted_filters.update(query_filters)
            
            # Perform vector search (simplified)
            raw_results = self.vector_store.search(
                query=enhanced_query,
                business_id=business_id,
                limit=limit * 2,  # Get more for post-processing
                filters=extracted_filters,
                similarity_threshold=self.config['similarity_threshold']
            )
            
            # Post-process results
            processed_results = []
            if self.result_processor:
                processed_results = self.result_processor.process_results(
                    raw_results, 
                    original_query, 
                    max_results=limit * 2
                )
                
                # Deduplicate if enabled
                if self.config['enable_deduplication']:
                    processed_results = self.result_processor.deduplicate_results(processed_results)
            else:
                # Basic processing without enhancement
                for result in raw_results:
                    processed_results.append(SearchResult(
                        content=result.get('content', ''),
                        document_id=result.get('document_id', ''),
                        chunk_id=result.get('id', result.get('chunk_id', '')),
                        score=result.get('score', result.get('similarity_score', 0.0)),
                        metadata=result.get('metadata', {}),
                        retrieval_method='vector',
                        business_id=business_id
                    ))
            
            # Limit final results
            final_results = processed_results[:limit]
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create search metadata
            search_metadata = {
                'original_query': original_query,
                'enhanced_query': enhanced_query if enhance_query else None,
                'search_method': 'vector',
                'filters_applied': extracted_filters,
                'total_raw_results': len(raw_results),
                'post_processing_enabled': self.result_processor is not None,
                'deduplication_enabled': self.config['enable_deduplication']
            }
            
            response = SearchResponse(
                query=original_query,
                results=final_results,
                total_results=len(final_results),
                processing_time=processing_time,
                search_metadata=search_metadata
            )
            
            logger.info(f"Search completed: {len(final_results)} results in {processing_time:.3f}s")
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Search failed: {str(e)}")
            
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                processing_time=processing_time,
                search_metadata={'error': str(e)}
            )
    
    def add_document(self,
                    file_path: str,
                    business_id: str,
                    metadata: Dict[str, Any] = None) -> str:
        """
        Add document to the index
        
        Args:
            file_path: Path to document file
            business_id: Business ID for context
            metadata: Additional metadata
            
        Returns:
            Job ID for tracking indexing progress
        """
        return self.document_indexer.add_document(
            file_path=file_path,
            business_id=business_id,
            metadata=metadata
        )
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        chunks = self.vector_store.get_document_chunks(document_id)
        return [chunk for chunk in chunks]
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document and its chunks from vector store"""
        return self.vector_store.delete_document(document_id)
    
    def check_document_cache(self, document_hash: str, business_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if document was already processed recently
        
        Args:
            document_hash: SHA256 hash of document content
            business_id: Business ID for context
            
        Returns:
            Cached job info if found and still valid, None otherwise
        """
        try:
            cache_key = f"{business_id}:{document_hash}"
            
            if cache_key in self.document_cache:
                cached_job = self.document_cache[cache_key]
                cached_time = datetime.fromisoformat(cached_job['cached_at'])
                
                # Check if cache is still valid
                if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                    logger.info(f"Cache hit for document hash {document_hash[:8]}")
                    return cached_job
                else:
                    # Remove expired cache
                    del self.document_cache[cache_key]
                    logger.debug(f"Expired cache removed for hash {document_hash[:8]}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Error checking document cache: {str(e)}")
            return None
    
    def cache_document_result(self, document_hash: str, business_id: str, job_result: Dict[str, Any]):
        """
        Cache document processing result
        
        Args:
            document_hash: SHA256 hash of document content
            business_id: Business ID for context
            job_result: Job processing result to cache
        """
        try:
            cache_key = f"{business_id}:{document_hash}"
            
            cached_data = {
                'job_id': job_result.get('job_id'),
                'document_id': job_result.get('document_id'),
                'chunks_created': job_result.get('chunks_created', 0),
                'processing_time': job_result.get('processing_time', 0),
                'cached_at': datetime.now().isoformat(),
                'document_hash': document_hash
            }
            
            self.document_cache[cache_key] = cached_data
            logger.info(f"Cached document result for hash {document_hash[:8]}")
            
            # Clean up old cache entries (keep only last 100)
            if len(self.document_cache) > 100:
                oldest_keys = sorted(
                    self.document_cache.keys(),
                    key=lambda k: self.document_cache[k]['cached_at']
                )[:10]  # Remove oldest 10
                
                for key in oldest_keys:
                    del self.document_cache[key]
                
                logger.debug(f"Cleaned up {len(oldest_keys)} old cache entries")
            
        except Exception as e:
            logger.warning(f"Error caching document result: {str(e)}")
    
    def estimate_processing_time(self, file_size_bytes: int, file_extension: str) -> Dict[str, Any]:
        """
        Estimate processing time based on file size and type
        
        Args:
            file_size_bytes: File size in bytes
            file_extension: File extension (e.g., '.pdf', '.jpg')
            
        Returns:
            Dictionary with time estimates
        """
        try:
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Base processing times (in seconds) per MB
            base_times = {
                '.pdf': 2.0,      # PDFs take longer due to text extraction
                '.docx': 1.5,     # Word docs are moderate
                '.txt': 0.5,      # Text files are fastest
                '.jpg': 3.0,      # Images need OCR
                '.jpeg': 3.0,
                '.png': 3.0,
                '.tiff': 4.0,     # TIFF can be large and complex
                '.bmp': 2.5
            }
            
            # Get base time per MB for file type
            base_time_per_mb = base_times.get(file_extension.lower(), 2.0)
            
            # Calculate estimates
            parsing_time = max(1, file_size_mb * base_time_per_mb * 0.3)
            chunking_time = max(1, file_size_mb * 0.5)  
            embedding_time = max(2, file_size_mb * 1.0)  # Vector embedding is slow
            indexing_time = max(1, file_size_mb * 0.2)
            
            total_estimate = parsing_time + chunking_time + embedding_time + indexing_time
            
            # Add buffer for AI API calls and queue wait time
            total_with_buffer = total_estimate * 1.3 + 5  # 30% buffer + 5s base
            
            return {
                'total_seconds': int(total_with_buffer),
                'total_minutes': round(total_with_buffer / 60, 1),
                'breakdown': {
                    'parsing': int(parsing_time),
                    'chunking': int(chunking_time), 
                    'embedding': int(embedding_time),
                    'indexing': int(indexing_time),
                    'buffer': int(total_with_buffer - total_estimate)
                },
                'file_size_mb': round(file_size_mb, 2),
                'file_type': file_extension
            }
            
        except Exception as e:
            logger.warning(f"Error estimating processing time: {str(e)}")
            return {
                'total_seconds': 30,
                'total_minutes': 0.5,
                'breakdown': {'error': 'estimation_failed'},
                'file_size_mb': round(file_size_bytes / (1024*1024), 2),
                'file_type': file_extension
            }
    
    def get_stats(self, business_id: str = None) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            'vector_store': self.vector_store.get_stats(business_id),
            'document_indexer': self.document_indexer.get_queue_status(),
            'search_methods_available': ['vector'],
            'document_cache': {
                'entries': len(self.document_cache),
                'ttl_seconds': self.cache_ttl
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            status = 'healthy'
            component_health = {}
            
            # Check vector store
            vector_health = self.vector_store.health_check()
            component_health['vector_store'] = vector_health
            if vector_health['status'] != 'healthy':
                status = 'warning'
            
            
            # Check document indexer
            indexer_health = self.document_indexer.health_check()
            component_health['document_indexer'] = indexer_health
            if indexer_health['status'] != 'healthy':
                status = 'warning'
            
            # Perform search test
            try:
                test_response = self.search(
                    query="test search",
                    business_id="test_business",
                    limit=1
                )
                component_health['search_test'] = {
                    'status': 'healthy',
                    'processing_time': test_response.processing_time
                }
            except Exception as e:
                component_health['search_test'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                status = 'unhealthy'
            
            return {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'components': component_health,
                'config': self.config,
                'capabilities': {
                    'query_enhancement': self.query_enhancer is not None,
                    'result_postprocessing': self.result_processor is not None,
                    'vector_search': True,
                    'document_caching': True
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }