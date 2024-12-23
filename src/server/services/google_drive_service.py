import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

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
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_file.name, scope)
            self.sheets_client = gspread.authorize(self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            raise

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a folder in Google Drive"""
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