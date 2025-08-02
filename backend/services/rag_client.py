"""
RAG Client Service

Client for calling the RAG Processor Cloud Function.
Handles document indexing and search operations via HTTP requests.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests

from config import Config

logger = logging.getLogger(__name__)

class RAGClient:
    """Client for RAG Processor Cloud Function"""
    
    def __init__(self, rag_function_url: str = None):
        """
        Initialize RAG client
        
        Args:
            rag_function_url: URL of the RAG processor cloud function
        """
        self.rag_function_url = rag_function_url or os.getenv('RAG_FUNCTION_URL')
        
        if not self.rag_function_url:
            logger.warning("RAG_FUNCTION_URL not configured. RAG functionality will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"RAG Client initialized with URL: {self.rag_function_url}")
        
        # Request timeout settings
        self.timeout = 60  # 60 seconds for most operations
        self.search_timeout = 10  # 10 seconds for search operations
        
    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None, timeout: int = None) -> Dict:
        """
        Make HTTP request to RAG function
        
        Args:
            endpoint: API endpoint (e.g., 'search', 'index')
            method: HTTP method
            data: Request data
            timeout: Request timeout
            
        Returns:
            Response data as dictionary
        """
        if not self.enabled:
            raise Exception("RAG Client is not enabled. Check RAG_FUNCTION_URL configuration.")
        
        url = f"{self.rag_function_url.rstrip('/')}/{endpoint.lstrip('/')}"
        timeout = timeout or self.timeout
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, params=data or {})
            else:
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"RAG function request timed out: {url}")
            raise Exception(f"RAG function request timed out after {timeout}s")
        except requests.exceptions.RequestException as e:
            logger.error(f"RAG function request failed: {url} - {str(e)}")
            raise Exception(f"RAG function request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from RAG function: {str(e)}")
            raise Exception("Invalid response from RAG function")
    
    def health_check(self) -> Dict[str, Any]:
        """Check RAG function health"""
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'RAG function URL not configured'
            }
        
        try:
            return self._make_request('health', timeout=5)
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_stats(self, business_id: str = None) -> Dict[str, Any]:
        """Get RAG system statistics"""
        params = {}
        if business_id:
            params['business_id'] = business_id
        
        return self._make_request('stats', data=params)
    
    def index_document(self, 
                      business_id: str,
                      document_id: str,
                      drive_url: str,
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Index a document in the RAG system
        
        Args:
            business_id: Business ID
            document_id: Unique document identifier
            drive_url: Google Drive URL for the document
            metadata: Additional document metadata
            
        Returns:
            Indexing job information
        """
        data = {
            'business_id': business_id,
            'document_id': document_id,
            'drive_url': drive_url,
            'metadata': metadata or {}
        }
        
        return self._make_request('index', method='POST', data=data)
    
    def search(self,
               query: str,
               business_id: str,
               limit: int = 10,
               search_method: str = 'auto',
               filters: Dict[str, Any] = None,
               enhance_query: bool = True) -> Dict[str, Any]:
        """
        Search documents using RAG
        
        Args:
            query: Search query
            business_id: Business ID to filter results
            limit: Maximum number of results
            search_method: Search method ('vector', 'hybrid', 'auto')
            filters: Additional filters
            enhance_query: Whether to enhance the query
            
        Returns:
            Search results
        """
        data = {
            'query': query,
            'business_id': business_id,
            'limit': limit,
            'search_method': search_method,
            'filters': filters or {},
            'enhance_query': enhance_query
        }
        
        return self._make_request('search', method='POST', data=data, timeout=self.search_timeout)
    
    def estimate_processing_time(self, file_size_bytes: int, file_extension: str) -> Dict[str, Any]:
        """
        Estimate document processing time
        
        Args:
            file_size_bytes: File size in bytes
            file_extension: File extension
            
        Returns:
            Time estimation
        """
        # Simple client-side estimation since this doesn't need the cloud function
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Base processing times (in seconds) per MB
        base_times = {
            '.pdf': 2.0,
            '.docx': 1.5,
            '.txt': 0.5,
            '.jpg': 3.0,
            '.jpeg': 3.0,
            '.png': 3.0,
            '.tiff': 4.0,
            '.bmp': 2.5
        }
        
        base_time_per_mb = base_times.get(file_extension.lower(), 2.0)
        total_estimate = max(5, file_size_mb * base_time_per_mb * 1.5)  # 50% buffer
        
        return {
            'total_seconds': int(total_estimate),
            'total_minutes': round(total_estimate / 60, 1),
            'file_size_mb': round(file_size_mb, 2),
            'file_type': file_extension
        }

# Global RAG client instance
rag_client = None

def get_rag_client() -> RAGClient:
    """Get or create RAG client instance"""
    global rag_client
    if rag_client is None:
        rag_client = RAGClient()
    return rag_client

def init_rag_client(rag_function_url: str = None):
    """Initialize RAG client with specific URL"""
    global rag_client
    rag_client = RAGClient(rag_function_url)
    return rag_client