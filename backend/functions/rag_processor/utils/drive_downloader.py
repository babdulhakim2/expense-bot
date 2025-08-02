"""
Google Drive downloader for RAG processor using service account authentication
"""
import logging
import os
import json
import tempfile
from typing import Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class DriveDownloader:
    """Google Drive file downloader with service account authentication"""
    
    def __init__(self):
        self.drive_service = None
        self._init_drive_service()
    
    def _init_drive_service(self):
        """Initialize Google Drive service with service account credentials"""
        try:
            # Get service account key from environment
            service_account_key = os.getenv('SERVICE_ACCOUNT_KEY')
            if not service_account_key:
                logger.warning("SERVICE_ACCOUNT_KEY not found in environment, falling back to public access")
                return
            
            # Parse the service account key
            try:
                service_account_info = json.loads(service_account_key)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid SERVICE_ACCOUNT_KEY JSON: {e}")
                return
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Build the Drive service
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive service initialized with service account")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            self.drive_service = None
    
    def extract_file_id_from_url(self, drive_url: str) -> str:
        """Extract file ID from Google Drive URL"""
        try:
            # Handle different Drive URL formats:
            # https://drive.google.com/file/d/FILE_ID/view
            # https://drive.google.com/open?id=FILE_ID
            # https://drive.google.com/file/d/FILE_ID/edit
            
            if '/file/d/' in drive_url:
                # Format: https://drive.google.com/file/d/FILE_ID/view
                file_id = drive_url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in drive_url:
                # Format: https://drive.google.com/open?id=FILE_ID
                file_id = drive_url.split('id=')[1].split('&')[0]
            else:
                # Try regex as fallback
                match = re.search(r'([a-zA-Z0-9_-]{28,})', drive_url)
                if match:
                    file_id = match.group(1)
                else:
                    raise ValueError(f"Cannot extract file ID from URL: {drive_url}")
            
            logger.debug(f"Extracted file ID {file_id} from URL {drive_url}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error extracting file ID from URL {drive_url}: {str(e)}")
            raise
    
    def download_file(self, drive_url: str) -> Tuple[bytes, str]:
        """
        Download file from Google Drive URL using authenticated API
        
        Returns:
            Tuple[bytes, str]: (file_content, mime_type)
        """
        try:
            file_id = self.extract_file_id_from_url(drive_url)
            logger.info(f"Downloading file from Drive: {file_id}")
            
            if self.drive_service:
                # Use authenticated Google Drive API
                return self._download_with_api(file_id)
            else:
                # Fallback to public download
                return self._download_public(file_id, drive_url)
                
        except Exception as e:
            logger.error(f"Error downloading file from {drive_url}: {str(e)}")
            raise
    
    def _download_with_api(self, file_id: str) -> Tuple[bytes, str]:
        """Download file using authenticated Google Drive API"""
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(
                fileId=file_id, 
                fields='id,name,mimeType,size'
            ).execute()
            
            mime_type = file_metadata.get('mimeType', 'application/octet-stream')
            file_name = file_metadata.get('name', 'unknown')
            file_size = file_metadata.get('size', 'unknown')
            
            logger.info(f"File metadata: {file_name}, {mime_type}, {file_size} bytes")
            
            # Download file content
            request = self.drive_service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            logger.info(f"Successfully downloaded file {file_id} via API, size: {len(file_content)} bytes")
            return file_content, mime_type
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id} via API: {str(e)}")
            raise
    
    def _download_public(self, file_id: str, drive_url: str) -> Tuple[bytes, str]:
        """Fallback to public download method"""
        import requests
        import re
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Use Google Drive's direct download URL
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        
        logger.warning(f"Falling back to public download for file {file_id}")
        
        # First request to get the download confirmation page (for large files)
        response = session.get(download_url, stream=True)
        response.raise_for_status()
        
        # Check if we need to confirm the download (for large files)
        if 'download_warning' in response.text or 'virus-scan-warning' in response.text:
            # Extract the confirmation token
            confirm_token = None
            for line in response.text.splitlines():
                if 'confirm=' in line:
                    match = re.search(r'confirm=([a-zA-Z0-9_-]+)', line)
                    if match:
                        confirm_token = match.group(1)
                        break
            
            if confirm_token:
                # Make the confirmed download request
                confirmed_url = f"{download_url}&confirm={confirm_token}"
                response = session.get(confirmed_url, stream=True)
                response.raise_for_status()
        
        # Get the file content
        file_content = response.content
        
        # Try to determine MIME type from headers
        mime_type = response.headers.get('content-type', 'application/octet-stream')
        
        logger.info(f"Successfully downloaded file {file_id} via public method, size: {len(file_content)} bytes")
        return file_content, mime_type

    def is_public_file(self, drive_url: str) -> bool:
        """Check if the Drive file is publicly accessible"""
        try:
            file_id = self.extract_file_id_from_url(drive_url)
            test_url = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            response = self.session.head(test_url)
            return response.status_code in [200, 302]  # 302 for redirect to actual download
            
        except Exception as e:
            logger.warning(f"Could not check file accessibility: {str(e)}")
            return False