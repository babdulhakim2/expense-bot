"""
RAG Processor Cloud Function

Standalone cloud function for processing expense documents and providing
semantic search capabilities. Handles document indexing, vector storage,
and search operations independently from the main backend.
"""

import os
import json
import logging
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import functions_framework
from flask import Request

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import RAG components
from core.search_engine import ExpenseDocumentSearchEngine
from core.document_indexer import ExpenseDocumentIndexer
from storage.lancedb_store import ExpenseDocumentVectorStore

# Global instances (initialized on first request)
search_engine = None
document_indexer = None

def get_search_engine():
    """Get or initialize the search engine"""
    global search_engine
    if search_engine is None:
        logger.info("Initializing RAG search engine...")
        search_engine = ExpenseDocumentSearchEngine()
        logger.info("RAG search engine initialized")
    return search_engine

def get_document_indexer():
    """Get or initialize the document indexer"""
    global document_indexer
    if document_indexer is None:
        logger.info("Initializing document indexer...")
        document_indexer = ExpenseDocumentIndexer()
        logger.info("Document indexer initialized")
    return document_indexer

@functions_framework.http
def rag_processor(request: Request):
    """
    Main HTTP entry point for RAG processing
    
    Endpoints:
    - POST /index - Index a document from Google Drive
    - POST /search - Search indexed documents
    - GET /health - Health check
    - GET /stats - Get system statistics
    """
    
    # Enable CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Add CORS headers to all responses
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Route to appropriate handler based on path and method
        path = request.path.strip('/')
        method = request.method
        
        if method == 'GET' and path == 'health':
            return handle_health_check(request, headers)
        elif method == 'GET' and path == 'stats':
            return handle_stats(request, headers)
        elif method == 'POST' and path == 'index':
            return handle_index_document(request, headers)
        elif method == 'POST' and path == 'search':
            return handle_search(request, headers)
        else:
            # Default endpoint info
            response_data = {
                'service': 'RAG Processor',
                'version': '1.0.0',
                'endpoints': {
                    'GET /health': 'Health check',
                    'GET /stats': 'System statistics',
                    'POST /index': 'Index a document',
                    'POST /search': 'Search documents'
                }
            }
            return (json.dumps(response_data), 200, headers)
            
    except Exception as e:
        logger.error(f"Unhandled error in RAG processor: {str(e)}")
        response_data = {
            'error': 'Internal server error',
            'message': str(e)
        }
        return (json.dumps(response_data), 500, headers)

def handle_health_check(request: Request, headers: Dict[str, str]):
    """Handle health check requests"""
    try:
        # Check all components
        engine = get_search_engine()
        indexer = get_document_indexer()
        
        engine_health = engine.health_check()
        indexer_health = indexer.health_check()
        
        overall_status = 'healthy'
        if engine_health['status'] != 'healthy' or indexer_health['status'] != 'healthy':
            overall_status = 'unhealthy'
        
        response_data = {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': {
                'search_engine': engine_health,
                'document_indexer': indexer_health
            }
        }
        return (json.dumps(response_data), 200, headers)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        response_data = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        return (json.dumps(response_data), 500, headers)

def handle_stats(request: Request, headers: Dict[str, str]):
    """Handle statistics requests"""
    try:
        business_id = request.args.get('business_id')
        
        engine = get_search_engine()
        stats = engine.get_stats(business_id)
        
        response_data = {
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
        return (json.dumps(response_data), 200, headers)
        
    except Exception as e:
        logger.error(f"Stats request failed: {str(e)}")
        response_data = {
            'error': 'Failed to get statistics',
            'message': str(e)
        }
        return (json.dumps(response_data), 500, headers)

def handle_index_document(request: Request, headers: Dict[str, str]):
    """Handle document indexing requests"""
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Required fields
        required_fields = ['business_id', 'document_id', 'drive_url']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            response_data = {
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }
            return (json.dumps(response_data), 400, headers)
        
        business_id = data['business_id']
        document_id = data['document_id']
        drive_url = data['drive_url']
        metadata = data.get('metadata', {})
        
        # Add drive_url to metadata
        metadata['drive_url'] = drive_url
        metadata['indexed_at'] = datetime.now().isoformat()
        
        logger.info(f"Indexing document {document_id} for business {business_id}")
        
        # Generate a job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Import the drive downloader
            from utils.drive_downloader import DriveDownloader
            
            # Download file from Google Drive
            downloader = DriveDownloader()
            logger.info(f"Downloading file from Google Drive: {drive_url}")
            file_content, mime_type = downloader.download_file(drive_url)
            logger.info(f"Downloaded file: {len(file_content)} bytes, type: {mime_type}")
            
            # Get the document indexer and process the file
            indexer = get_document_indexer()
            
            # Create a temporary file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Add mime_type to metadata
                metadata['mime_type'] = mime_type
                metadata['file_size'] = len(file_content)
                
                # Process the document
                job_id_returned = indexer.add_document(
                    file_path=temp_path,
                    business_id=business_id,
                    document_id=document_id,
                    metadata=metadata
                )
                
                # Process the job immediately
                result = indexer.process_next_job()
                if not result:
                    result = {'chunks_created': 0, 'processing_time': 0}
                
                logger.info(f"Document indexed successfully: {result}")
                
                response_data = {
                    'job_id': job_id,
                    'status': 'completed',
                    'message': 'Document indexed successfully',
                    'document_id': document_id,
                    'business_id': business_id,
                    'chunks_created': result.get('chunks_created', 0),
                    'processing_time': result.get('processing_time', 0),
                    'timestamp': datetime.now().isoformat()
                }
                return (json.dumps(response_data), 200, headers)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            response_data = {
                'job_id': job_id,
                'status': 'failed',
                'message': f'Document processing failed: {str(e)}',
                'document_id': document_id,
                'business_id': business_id,
                'timestamp': datetime.now().isoformat()
            }
            return (json.dumps(response_data), 500, headers)
        
    except Exception as e:
        logger.error(f"Document indexing failed: {str(e)}")
        response_data = {
            'error': 'Document indexing failed',
            'message': str(e)
        }
        return (json.dumps(response_data), 500, headers)

def handle_search(request: Request, headers: Dict[str, str]):
    """Handle search requests"""
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Required fields
        if not data.get('query') or not data.get('business_id'):
            response_data = {
                'error': 'Missing required fields',
                'required': ['query', 'business_id']
            }
            return (json.dumps(response_data), 400, headers)
        
        query = data['query']
        business_id = data['business_id']
        limit = int(data.get('limit', 10))
        search_method = data.get('search_method', 'auto')
        filters = data.get('filters', {})
        enhance_query = data.get('enhance_query', True)
        
        logger.info(f"Searching: '{query}' for business {business_id}")
        
        # Perform search
        engine = get_search_engine()
        search_response = engine.search(
            query=query,
            business_id=business_id,
            limit=limit,
            search_method=search_method,
            filters=filters,
            enhance_query=enhance_query
        )
        
        # Convert to JSON-serializable format
        response_data = search_response.to_dict()
        
        logger.info(f"Search completed: {len(search_response.results)} results in {search_response.processing_time:.3f}s")
        
        return (json.dumps(response_data), 200, headers)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        response_data = {
            'error': 'Search failed',
            'message': str(e)
        }
        return (json.dumps(response_data), 500, headers)

# For local testing
if __name__ == '__main__':
    import sys
    
    # Simple local testing
    print("RAG Processor Cloud Function - Local Testing")
    print("=" * 50)
    
    try:
        # Test initialization
        print("1. Testing component initialization...")
        engine = get_search_engine()
        indexer = get_document_indexer()
        print("✅ Components initialized successfully")
        
        # Test health check
        print("2. Testing health check...")
        health = engine.health_check()
        print(f"✅ Health check: {health['status']}")
        
        # Test search
        print("3. Testing search...")
        search_response = engine.search(
            query="coffee receipt",
            business_id="test_business",
            limit=5
        )
        print(f"✅ Search test: {search_response.total_results} results in {search_response.processing_time:.3f}s")
        
        print("🎉 All local tests passed!")
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)