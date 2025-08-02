"""
Simplified RAG API Endpoints

Provides minimal REST API endpoints for RAG functionality by calling
the RAG Processor Cloud Function.
"""

import logging
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import tempfile
import hashlib
import json

from services.rag_client import get_rag_client, init_rag_client
from config import Config

logger = logging.getLogger(__name__)

# Create blueprint
rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')

def init_rag_service():
    """Initialize RAG client with proper configuration"""
    try:
        # Initialize RAG client
        rag_function_url = os.getenv('RAG_FUNCTION_URL')
        if rag_function_url:
            init_rag_client(rag_function_url)
            logger.info("RAG client initialized successfully")
        else:
            logger.warning("RAG_FUNCTION_URL not set. RAG functionality will be limited.")
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        raise

# Initialize RAG client on startup
init_rag_service()

@rag_bp.route('/search', methods=['POST'])
def search_documents():
    """
    Search documents using RAG
    
    Expected JSON payload:
    {
        "query": "search query string",
        "business_id": "business_id",
        "limit": 10,
        "filters": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        query = data.get('query', '').strip()
        business_id = data.get('business_id', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        if not business_id:
            return jsonify({'error': 'Business ID is required'}), 400
        
        # Optional parameters
        limit = min(data.get('limit', 10), 50)  # Cap at 50
        filters = data.get('filters', {})
        enhance_query = data.get('enhance_query', True)
        
        # Perform search using RAG client
        rag_client = get_rag_client()
        response = rag_client.search(
            query=query,
            business_id=business_id,
            limit=limit,
            filters=filters,
            enhance_query=enhance_query
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    Upload and index a document
    
    Form data:
    - file: Document file to upload
    - business_id: Business ID for context
    - metadata: Optional JSON metadata
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get business ID
        business_id = request.form.get('business_id', '').strip()
        if not business_id:
            return jsonify({'error': 'Business ID is required'}), 400
        
        # Validate file size (20MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = 20 * 1024 * 1024  # 20MB
        if file_size > max_size:
            return jsonify({
                'error': f'File too large. Maximum size is {max_size // (1024*1024)}MB'
            }), 400
        
        # Get optional metadata
        metadata = {'file_size': file_size, 'original_filename': file.filename}
        metadata_json = request.form.get('metadata')
        if metadata_json:
            try:
                additional_metadata = json.loads(metadata_json)
                metadata.update(additional_metadata)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid metadata JSON'}), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1]
        
        # Generate document hash
        file_content = file.read()
        file.seek(0)  # Reset for processing
        
        document_hash = hashlib.sha256(file_content).hexdigest()
        document_id = f"doc_{document_hash[:16]}"
        
        metadata['document_hash'] = document_hash
        metadata['upload_timestamp'] = datetime.now().isoformat()
        
        logger.info("Uploading to Google Drive...")
        
        # TODO: Upload file to Google Drive
        # For now, we'll create a placeholder drive_url
        drive_url = f"https://drive.google.com/file/d/{document_id}/view"
        
        # Call RAG cloud function to index the document
        rag_client = get_rag_client()
        
        try:
            response = rag_client.index_document(
                business_id=business_id,
                document_id=document_id,
                drive_url=drive_url,
                metadata=metadata
            )
            
            # Add processing time estimate
            time_estimate = rag_client.estimate_processing_time(file_size, file_ext)
            response['estimated_processing_time'] = time_estimate
            response['filename'] = filename
            response['file_size_mb'] = round(file_size / (1024*1024), 2)
            
            logger.info(f"Document submitted to RAG processor: {response.get('job_id')}")
            return jsonify(response), 202  # 202 Accepted for async processing
            
        except Exception as e:
            logger.error(f"Failed to submit document to RAG processor: {str(e)}")
            return jsonify({
                'error': 'RAG indexing service unavailable',
                'message': str(e)
            }), 503
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get RAG statistics"""
    try:
        business_id = request.args.get('business_id')
        rag_client = get_rag_client()
        stats = rag_client.get_stats(business_id)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@rag_bp.route('/health', methods=['GET'])
def health_check():
    """Check RAG service health"""
    try:
        rag_client = get_rag_client()
        health = rag_client.health_check()
        
        # Return appropriate HTTP status based on health
        status_code = 200
        if health.get('status') == 'unhealthy':
            status_code = 503
        elif health.get('status') == 'disabled':
            status_code = 503
        
        return jsonify(health), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# Error handlers
@rag_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@rag_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@rag_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500