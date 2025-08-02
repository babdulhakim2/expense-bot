"""
Document access routes for authenticated Google Drive documents
"""
import logging
from flask import Blueprint, request, jsonify, Response, send_file
from services.google_drive_service import GoogleDriveService
from functools import wraps
import io
import mimetypes

logger = logging.getLogger(__name__)

documents_bp = Blueprint('documents', __name__, url_prefix='/api')

@documents_bp.route('/documents/view', methods=['GET'])
def view_document():
    """
    View a Google Drive document using service account authentication
    
    Query parameters:
        - url: Google Drive URL
        - file_id: Alternative to URL - direct file ID
    """
    try:
        # Get file identifier from request
        drive_url = request.args.get('url')
        file_id = request.args.get('file_id')
        
        if not drive_url and not file_id:
            return jsonify({'error': 'Either url or file_id parameter is required'}), 400
        
        # Initialize Google Drive service
        drive_service = GoogleDriveService()
        
        # Extract file ID from URL if needed
        if drive_url and not file_id:
            file_id = drive_service.extract_file_id_from_url(drive_url)
        
        if not file_id:
            return jsonify({'error': 'Could not extract file ID from URL'}), 400
        
        # Get file metadata first
        file_metadata = drive_service.drive_service.files().get(
            fileId=file_id, 
            fields='id, name, mimeType, size'
        ).execute()
        
        file_name = file_metadata.get('name', 'document')
        mime_type = file_metadata.get('mimeType', 'application/octet-stream')
        file_size = file_metadata.get('size')
        
        logger.info(f"Serving document: {file_name} ({mime_type})")
        
        # Download file content
        file_content = drive_service.download_file(file_id)
        
        # Create response with proper headers
        response = Response(
            file_content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="{file_name}"',
                'Content-Length': str(len(file_content)),
                'Cache-Control': 'private, max-age=3600'  # Cache for 1 hour
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving document: {str(e)}")
        return jsonify({'error': 'Failed to access document'}), 500

@documents_bp.route('/documents/info', methods=['GET'])
def document_info():
    """
    Get document metadata without downloading the full file
    
    Query parameters:
        - url: Google Drive URL
        - file_id: Alternative to URL - direct file ID
    """
    try:
        # Get file identifier from request
        drive_url = request.args.get('url')
        file_id = request.args.get('file_id')
        
        if not drive_url and not file_id:
            return jsonify({'error': 'Either url or file_id parameter is required'}), 400
        
        # Initialize Google Drive service
        drive_service = GoogleDriveService()
        
        # Extract file ID from URL if needed
        if drive_url and not file_id:
            file_id = drive_service.extract_file_id_from_url(drive_url)
        
        if not file_id:
            return jsonify({'error': 'Could not extract file ID from URL'}), 400
        
        # Get file metadata
        file_metadata = drive_service.drive_service.files().get(
            fileId=file_id, 
            fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
        ).execute()
        
        return jsonify({
            'id': file_metadata.get('id'),
            'name': file_metadata.get('name'),
            'mimeType': file_metadata.get('mimeType'),
            'size': file_metadata.get('size'),
            'createdTime': file_metadata.get('createdTime'),
            'modifiedTime': file_metadata.get('modifiedTime'),
            'webViewLink': file_metadata.get('webViewLink'),
            'downloadUrl': f'/api/documents/view?file_id={file_id}'
        })
        
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        return jsonify({'error': 'Failed to get document info'}), 500