import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional, Dict, Any
from googleapiclient.http import MediaIoBaseUpload
import io
import httplib2
import socket
import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class CustomHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')  # Less strict SSL
        kwargs['ssl_context'] = context
        return super(CustomHTTPAdapter, self).init_poolmanager(*args, **kwargs)

class GoogleDriveService:
    def __init__(self):
        """Initialize Google Drive and Sheets service"""
        try:
            # Google Sheets and Drive setup
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            # Write service account key to a temporary file
            import tempfile
            service_account_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            json.dump(json.loads(Config.SERVICE_ACCOUNT_KEY), service_account_file)
            service_account_file.close()
            
            # Initialize credentials
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                service_account_file.name, 
                scope
            )
            
            # Create authorized http object
            authorized_http = self.creds.authorize(httplib2.Http(timeout=30))
            
            # Initialize services
            self.drive_service = build(
                'drive', 
                'v3', 
                http=authorized_http
            )
            
            self.sheets_client = gspread.authorize(self.creds)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            raise

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a folder in Google Drive"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                
                drive_folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id, name, webViewLink'
                ).execute()
                
                return {
                    'id': drive_folder.get('id'),
                    'name': drive_folder.get('name'),
                    'url': drive_folder.get('webViewLink')
                }
                
            except ssl.SSLError as e:
                retry_count += 1
                logger.warning(f"SSL Error (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count == max_retries:
                    raise
                continue
                
            except Exception as e:
                logger.error(f"Error creating folder: {str(e)}")
                raise

    def create_spreadsheet(self, name: str, parent_folder_id: str) -> Dict[str, Any]:
        """Create a new spreadsheet in Google Drive"""
        try:
            spreadsheet_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [parent_folder_id]
            }
            
            drive_spreadsheet = self.drive_service.files().create(
                body=spreadsheet_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'id': drive_spreadsheet.get('id'),
                'name': drive_spreadsheet.get('name'),
                'url': drive_spreadsheet.get('webViewLink')
            }
            
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {str(e)}")
            raise

    def set_permissions(self, file_id: str, user_email: str, service_account_email: str):
        """Set permissions for a Drive file/folder"""
        try:
            # Give user editor access
            user_permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': user_email
            }
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body=user_permission,
                sendNotificationEmail=False
            ).execute()
            
            # Make service account the owner
            owner_permission = {
                'type': 'user',
                'role': 'owner',
                'emailAddress': service_account_email,
                'transferOwnership': True
            }
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body=owner_permission,
                transferOwnership=True,
                sendNotificationEmail=True
            ).execute()
            
        except Exception as e:
            logger.error(f"Error setting permissions: {str(e)}")
            # Try alternative permission method
            try:
                anyone_permission = {
                    'type': 'anyone',
                    'role': 'writer',
                    'allowFileDiscovery': False
                }
                
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body=anyone_permission,
                    sendNotificationEmail=False
                ).execute()
                
            except Exception as backup_error:
                logger.error(f"Backup permission method failed: {str(backup_error)}")
                raise backup_error

    def initialize_expense_spreadsheet(self, spreadsheet_id: str, month_name: str, year: str):
        """Initialize a new expense spreadsheet with headers and formatting"""
        try:
            sheets_service = build('sheets', 'v4', credentials=self.creds)
            sheet_name = f"{month_name} {year}"
            
            # Rename default sheet
            rename_request = {
                'requests': [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': 0,
                            'title': sheet_name
                        },
                        'fields': 'title'
                    }
                }]
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=rename_request
            ).execute()
            
            # Define and update headers
            headers = [[
                'Date', 'Description', 'Amount', 'Category', 'Payment Method',
                'Status', 'Transaction ID', 'Merchant', 'Original Currency',
                'Original Amount', 'Exchange Rate', 'Timestamp', 'Created At'
            ]]
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:M1",
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            # Format headers
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': 13
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                                    'textFormat': {'bold': True},
                                    'horizontalAlignment': 'CENTER',
                                    'verticalAlignment': 'MIDDLE'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
                        }
                    },
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': 0,
                                'gridProperties': {
                                    'frozenRowCount': 1
                                }
                            },
                            'fields': 'gridProperties.frozenRowCount'
                        }
                    }
                ]
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=format_request
            ).execute()
            
        except Exception as e:
            logger.error(f"Error initializing spreadsheet: {str(e)}")
            raise

    def update_spreadsheet(self, spreadsheet_id: str, sheet_name: str, 
                          values: list) -> Dict[str, Any]:
        """Update spreadsheet with new values"""
        try:
            sheets_service = build('sheets', 'v4', credentials=self.creds)
            
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:M",
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': [values]}
            ).execute()
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating spreadsheet: {str(e)}")
            raise

    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata from Drive"""
        try:
            return self.drive_service.files().get(
                fileId=file_id,
                fields='id, name, webViewLink'
            ).execute()
            
        except Exception as e:
            logger.error(f"Error getting file: {str(e)}")
            raise 

    def file_exists(self, file_id: str) -> bool:
        """Check if a file/folder exists in Drive"""
        try:
            self.drive_service.files().get(
                fileId=file_id,
                fields='id'
            ).execute()
            return True
        except Exception:
            return False 

    def upload_file(self, file_content: bytes, file_name: str, 
                    mime_type: str, parent_folder_id: str) -> Dict[str, Any]:
        """Upload file to Google Drive"""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'url': file.get('webViewLink')
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise 

    def download_file(self, file_id: str) -> bytes:
        """Download file content from Google Drive"""
        try:
            # Get file metadata first to check if it exists
            file_metadata = self.drive_service.files().get(fileId=file_id, fields='id, name, mimeType').execute()
            logger.debug(f"Downloading file: {file_metadata.get('name')} ({file_metadata.get('mimeType')})")
            
            # Download the file content
            request = self.drive_service.files().get_media(fileId=file_id)
            file_content = request.execute()
            
            logger.info(f"Successfully downloaded file {file_id}, size: {len(file_content)} bytes")
            return file_content
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            raise

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
                raise ValueError(f"Cannot extract file ID from URL: {drive_url}")
            
            logger.debug(f"Extracted file ID {file_id} from URL {drive_url}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error extracting file ID from URL {drive_url}: {str(e)}")
            raise