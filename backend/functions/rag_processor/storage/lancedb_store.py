"""
LanceDB Cloud Vector Store for Expense Document RAG

Production-ready vector storage using LanceDB Cloud with:
- Remote cloud database connections with API key authentication
- Optimized schema for expense document chunks and metadata
- High-throughput batch operations for document indexing
- Semantic search with embedding-based similarity matching
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

try:
    import lancedb
    import pyarrow as pa
    import pandas as pd
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.warning(f"RAG dependencies not installed: {e}")
    lancedb = None
    pa = None
    pd = None
    SentenceTransformer = None

from config import Config

logger = logging.getLogger(__name__)

class ExpenseDocumentVectorStore:
    """
    LanceDB-based vector store for document chunks and embeddings
    """
    
    def __init__(self, 
                 db_uri: str = None,
                 api_key: str = None,
                 region: str = None,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 table_name: str = None):
        """
        Initialize the Expense Document Vector Store
        
        Args:
            db_uri: LanceDB Cloud URI (db://database-name) or local path
            api_key: LanceDB Cloud API key (sk_...)
            region: LanceDB Cloud region (us-east-1, us-west-2, etc.)
            embedding_model: SentenceTransformer model for embeddings
            table_name: Name of the expense documents table
        """
        if not lancedb or not pd:
            raise ImportError("LanceDB dependencies not installed. Run: pip install lancedb sentence-transformers pandas")
        
        # Use configuration-based setup
        lance_config = Config.get_lancedb_config()
        
        self.db_uri = db_uri or lance_config['uri']
        self.api_key = api_key or lance_config['api_key'] 
        self.region = region or lance_config['region']
        self.table_name = table_name or lance_config['table_name']
        self.embedding_model_name = embedding_model
        
        # Validate cloud connection parameters
        self.is_cloud = self.db_uri.startswith('db://')
        self.is_local = Config.is_local_development()
        
        if self.is_cloud and not self.is_local and not self.api_key:
            raise ValueError("LanceDB Cloud requires API key. Set LANCEDB_API_KEY environment variable.")
        
        # Initialize connection
        self._initialize_connection()
        
        # Initialize components
        self.db = None
        self.table = None
        self.embedding_model = None
        
        self._initialize_components()
    
    def _initialize_connection(self):
        """Initialize LanceDB connection (local or cloud)"""
        try:
            if self.is_cloud:
                logger.info(f"Connecting to LanceDB Cloud: {self.db_uri} in region {self.region}")
            else:
                logger.info(f"Using local LanceDB at {self.db_uri}")
                # Ensure local directory exists
                os.makedirs(self.db_uri, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to initialize LanceDB connection: {str(e)}")
            raise
    
    def _initialize_components(self):
        """Initialize LanceDB and embedding model with retry logic"""
        import time
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Initialize LanceDB connection with proper parameters
                if self.is_cloud:
                    self.db = lancedb.connect(
                        uri=self.db_uri,
                        api_key=self.api_key,
                        region=self.region
                    )
                    logger.info(f"Connected to LanceDB Cloud: {self.db_uri}")
                else:
                    self.db = lancedb.connect(self.db_uri)
                    logger.info(f"Connected to local LanceDB: {self.db_uri}")
                
                # Initialize embedding model
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
                
                # Initialize or get existing table with proper schema
                self._initialize_expense_table()
                
                # If we reach here, initialization was successful
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to initialize RAG Vector Store (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize RAG Vector Store after {max_retries} attempts: {str(e)}")
                    raise
    
    def _initialize_expense_table(self):
        """Initialize or connect to expense documents table"""
        try:
            # Check if table exists
            table_names = list(self.db.table_names())
            
            if self.table_name in table_names:
                self.table = self.db.open_table(self.table_name)
                logger.info(f"Connected to existing expense table: {self.table_name}")
            else:
                # Create table with sample data to establish schema
                sample_data = pd.DataFrame({
                    'chunk_id': ['sample_chunk'],
                    'business_id': ['sample_business'],
                    'document_id': ['sample_document'],
                    'content': ['Sample expense document content'],
                    'vector': [[0.0] * 384],  # MiniLM-L6-v2 dimensions
                    'expense_amount': [0.0],
                    'expense_category': [''],
                    'expense_merchant': [''],
                    'expense_date': [''],
                    'document_type': ['expense'],
                    'drive_url': [''],
                    'chunk_index': [0],
                    'created_at': [datetime.now().isoformat()],
                    'metadata_json': ['{}']
                })
                
                # Create table with sample data, then delete the sample
                self.table = self.db.create_table(self.table_name, sample_data)
                self.table.delete("chunk_id = 'sample_chunk'")
                logger.info(f"Created new expense table: {self.table_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize table: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add document chunks to the vector store
        
        Args:
            documents: List of document dictionaries with required fields
            
        Returns:
            List of document IDs that were added
        """
        try:
            if not documents:
                return []
            
            # Prepare data for insertion
            data_to_insert = []
            document_ids = []
            
            for doc in documents:
                # Generate embedding for content
                content = doc.get('content', '')
                if not content.strip():
                    logger.warning(f"Skipping document with empty content: {doc.get('id')}")
                    continue
                
                vector = self.embedding_model.encode(content).tolist()
                
                # Prepare metadata as JSON string
                metadata = {
                    'document_type': doc.get('document_type'),
                    'date': doc.get('date'),
                    'chunk_index': doc.get('chunk_index', 0),
                    'page_number': doc.get('page_number'),
                    'category': doc.get('category'),
                    'merchant': doc.get('merchant'),
                    'amount': doc.get('amount'),
                    'file_path': doc.get('file_path'),
                    'chunk_type': doc.get('chunk_type', 'text'),
                    'source_section': doc.get('source_section')
                }
                
                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                current_time = datetime.now()
                
                # Extract expense-specific fields with defaults
                expense_amount = doc.get('amount', 0.0)
                expense_category = doc.get('category', '')
                expense_merchant = doc.get('merchant', '')
                expense_date = doc.get('date', '')
                document_type = doc.get('document_type', 'expense')
                drive_url = doc.get('drive_url', '')
                chunk_index = doc.get('chunk_index', 0)
                
                data_to_insert.append({
                    'chunk_id': doc['id'],
                    'business_id': doc['business_id'],
                    'document_id': doc['document_id'],
                    'content': content,
                    'vector': vector,
                    'expense_amount': float(expense_amount) if expense_amount else 0.0,
                    'expense_category': str(expense_category),
                    'expense_merchant': str(expense_merchant),
                    'expense_date': str(expense_date),
                    'document_type': str(document_type),
                    'drive_url': str(drive_url),
                    'chunk_index': int(chunk_index),
                    'created_at': current_time.isoformat(),
                    'metadata_json': json.dumps(metadata)
                })
                
                document_ids.append(doc['id'])
            
            if data_to_insert:
                # Convert to DataFrame and add to LanceDB table
                df = pd.DataFrame(data_to_insert)
                self.table.add(df)
                
                logger.info(f"Added {len(data_to_insert)} document chunks to vector store")
            
            return document_ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def search(self, 
               query: str,
               business_id: str,
               limit: int = 10,
               filters: Dict[str, Any] = None,
               similarity_threshold: float = 0.01) -> List[Dict[str, Any]]:
        """
        Perform semantic search on document chunks
        
        Args:
            query: Search query text
            business_id: Business ID to filter results
            limit: Maximum number of results
            filters: Additional metadata filters
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of matching document chunks with scores
        """
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Build base search
            search_builder = self.table.search(query_vector)
            
            # Apply business filter
            where_clause = f"business_id = '{business_id}'"
            logger.debug(f"Searching with where clause: {where_clause}")
            
            # Apply additional filters using structured fields
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        if key == 'category':
                            where_clause += f" AND expense_category = '{value}'"
                        elif key == 'merchant':
                            where_clause += f" AND expense_merchant LIKE '%{value}%'"
                        elif key == 'document_type':
                            where_clause += f" AND document_type = '{value}'"
                        elif key == 'amount_filter' and isinstance(value, dict):
                            operator = value.get('operator', '=')
                            amount = value.get('value', 0)
                            where_clause += f" AND expense_amount {operator} {amount}"
                        else:
                            # Fall back to metadata JSON search for other filters
                            if isinstance(value, str):
                                where_clause += f" AND metadata_json LIKE '%\"{key}\": \"{value}\"%'"
                            else:
                                where_clause += f" AND metadata_json LIKE '%\"{key}\": {value}%'"
            
            # Execute search
            # For cloud LanceDB, we need to use to_list() instead of to_arrow()
            if self.is_cloud:
                results_list = (search_builder
                               .where(where_clause)
                               .limit(limit)
                               .to_list())
                logger.debug(f"Cloud search returned {len(results_list)} results")
                # Convert to DataFrame for consistent processing
                import pandas as pd
                results = pd.DataFrame(results_list)
            else:
                results = (search_builder
                          .where(where_clause)
                          .limit(limit)
                          .to_arrow()
                          .to_pandas())
            
            logger.debug(f"DataFrame has {len(results)} rows")
            
            # Process results
            search_results = []
            logger.debug(f"Processing {len(results)} rows from DataFrame")
            for i, (_, row) in enumerate(results.iterrows()):
                # Parse metadata JSON
                try:
                    metadata = json.loads(row['metadata_json'])
                except json.JSONDecodeError:
                    metadata = {}
                
                # Calculate similarity score (LanceDB returns cosine distance, convert to similarity)
                # Cosine distance ranges from 0 to 2, where 0 is identical and 2 is opposite
                # Convert to similarity score: similarity = 1 - (distance / 2)
                distance = row.get('_distance', 1.0)
                similarity = max(0.0, 1.0 - (distance / 2.0))  # Convert to 0-1 range
                
                # Include results above similarity threshold
                if similarity >= similarity_threshold:
                    search_results.append({
                        'id': row['chunk_id'],
                        'document_id': row['document_id'],
                        'business_id': row['business_id'],
                        'content': row['content'],
                        'metadata': metadata,
                        'similarity_score': similarity,
                        'score': similarity,
                        'created_at': row['created_at']
                    })
                    logger.debug(f"Added result: similarity={similarity:.4f}, content={row['content'][:50]}...")
                else:
                    logger.debug(f"Filtered out result: similarity={similarity:.4f} < threshold={similarity_threshold}")
            
            logger.info(f"Found {len(search_results)} results for query: {query[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            return []
    
    def hybrid_search(self,
                     query: str,
                     business_id: str,
                     limit: int = 10,
                     filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and full-text search
        
        Args:
            query: Search query text
            business_id: Business ID to filter results
            limit: Maximum number of results
            filters: Additional metadata filters
            
        Returns:
            List of matching document chunks with combined scores
        """
        try:
            # For now, use semantic search as base
            # TODO: Implement full-text search integration when LanceDB adds FTS support
            semantic_results = self.search(
                query=query,
                business_id=business_id,
                limit=limit * 2,  # Get more results for reranking
                filters=filters,
                similarity_threshold=0.5  # Lower threshold for hybrid
            )
            
            # Simple keyword boost for now
            # TODO: Replace with proper FTS when available
            query_terms = query.lower().split()
            
            for result in semantic_results:
                content_lower = result['content'].lower()
                keyword_matches = sum(1 for term in query_terms if term in content_lower)
                keyword_score = keyword_matches / len(query_terms) if query_terms else 0
                
                # Combine semantic and keyword scores
                result['hybrid_score'] = (result['similarity_score'] * 0.7 + keyword_score * 0.3)
            
            # Sort by hybrid score and return top results
            hybrid_results = sorted(semantic_results, key=lambda x: x['hybrid_score'], reverse=True)
            return hybrid_results[:limit]
            
        except Exception as e:
            logger.error(f"Error performing hybrid search: {str(e)}")
            return []
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document
        
        Args:
            document_id: Document ID to retrieve chunks for
            
        Returns:
            List of document chunks
        """
        try:
            results = (self.table
                      .search()
                      .where(f"document_id = '{document_id}'")
                      .to_arrow()
                      .to_pandas())
            
            chunks = []
            for _, row in results.iterrows():
                try:
                    metadata = json.loads(row['metadata_json'])
                except json.JSONDecodeError:
                    metadata = {}
                
                chunks.append({
                    'id': row['chunk_id'],
                    'content': row['content'],
                    'metadata': metadata,
                    'created_at': row['created_at']
                })
            
            # Sort by chunk_index if available
            chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.delete(f"document_id = '{document_id}'")
            logger.info(f"Deleted chunks for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            return False
    
    def get_stats(self, business_id: str = None) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Args:
            business_id: Optional business ID to filter stats
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get total count
            if business_id:
                results = (self.table
                          .search()
                          .where(f"business_id = '{business_id}'")
                          .to_arrow()
                          .to_pandas())
            else:
                results = self.table.to_arrow().to_pandas()
            
            total_chunks = len(results)
            unique_documents = results['document_id'].nunique() if total_chunks > 0 else 0
            unique_businesses = results['business_id'].nunique() if total_chunks > 0 else 0
            
            stats = {
                'total_chunks': total_chunks,
                'unique_documents': unique_documents,
                'unique_businesses': unique_businesses,
                'database_uri': self.db_uri,
                'table_name': self.table_name,
                'embedding_model': self.embedding_model_name
            }
            
            if business_id:
                stats['business_id'] = business_id
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the vector store
        
        Returns:
            Health status information
        """
        try:
            # Test basic operations
            test_passed = True
            error_message = None
            
            # Check database connection
            if not self.db:
                test_passed = False
                error_message = "Database not connected"
            
            # Check table availability (LanceTable objects have custom __bool__ that may return False for empty tables)
            elif self.table is None:
                test_passed = False
                error_message = "Table not available"
            
            # Check embedding model
            elif not self.embedding_model:
                test_passed = False
                error_message = "Embedding model not loaded"
            
            # Perform simple test
            else:
                try:
                    test_vector = self.embedding_model.encode("test").tolist()
                    if len(test_vector) != 384:
                        test_passed = False
                        error_message = f"Unexpected embedding dimension: {len(test_vector)}"
                except Exception as e:
                    test_passed = False
                    error_message = f"Embedding test failed: {str(e)}"
            
            # Simple stats without complex queries
            simple_stats = {
                'database_uri': self.db_uri,
                'table_name': self.table_name,
                'embedding_model': self.embedding_model_name,
                'is_cloud': self.is_cloud
            }
            
            return {
                'status': 'healthy' if test_passed else 'unhealthy',
                'error': error_message,
                'database_uri': self.db_uri,
                'table_name': self.table_name,
                'embedding_model': self.embedding_model_name,
                'is_cloud': self.is_cloud,
                'stats': simple_stats
            }
            
        except Exception as e:
            logger.error(f"Health check exception: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_uri': self.db_uri,
                'table_name': self.table_name
            }
            
