import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from config import Config
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# Google Sheets and Drive setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # Write service account key to a temporary file
    import tempfile
    import json
    
    service_account_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    json.dump(json.loads(Config.SERVICE_ACCOUNT_KEY), service_account_file)
    service_account_file.close()
    
    # Update your credentials initialization
    creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_file.name, scope)
    
except Exception as e:
    logger.error(f"Failed to initialize credentials: {str(e)}")
    raise

sheets_client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)



logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        """Initialize Firebase and set up development/production environment"""
        try:
            if Config.IS_DEVELOPMENT:
                os.environ["FIRESTORE_EMULATOR_HOST"] = Config.FIREBASE_FIRESTORE_EMULATOR_HOST
                os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = Config.FIREBASE_AUTH_EMULATOR_HOST
                os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = Config.FIREBASE_STORAGE_EMULATOR_HOST
                logger.info("Using Firebase emulators")
                # Set storage emulator host for development
                self.storage_host = f"http://{Config.FIREBASE_STORAGE_EMULATOR_HOST}"
                self.is_emulated = True
            else:
                self.storage_host = "https://storage.googleapis.com"
                self.is_emulated = False

            if not len(firebase_admin._apps):
                cred = credentials.Certificate(json.loads(Config.FIREBASE_SERVICE_ACCOUNT_KEY))
                firebase_admin.initialize_app(cred, {
                    'storageBucket': Config.FIREBASE_STORAGE_BUCKET
                })
                logger.info(f"Firebase initialized in {'development' if Config.IS_DEVELOPMENT else 'production'} mode")

            self.db = firestore.client()
            self.auth = auth
            self.bucket = storage.bucket()

            # Add Google Drive setup with renamed credentials variable
            self.drive_credentials = service_account.Credentials.from_service_account_info(
                json.loads(Config.SERVICE_ACCOUNT_KEY),
                scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            )
            self.drive_service = build('drive', 'v3', credentials=self.drive_credentials)

           

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number from Firebase Auth and then Firestore
        
        Args:
            phone_number: Phone number in E.164 format (e.g. +1234567890)
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            # First get user from Firebase Auth by phone
            auth_user = self.auth.get_user_by_phone_number(phone_number)
            if not auth_user:
                logger.info(f"No auth user found for phone: {phone_number}")
                return None
                
            # Get the Firebase Auth UID
            uid = auth_user.uid
            # Now get user data from Firestore using the auth UID
            user_ref = self.db.collection('users').document(uid)
            user = user_ref.get()

            if user.exists:
                return {
                    'id': user.id,  # This will be the auth UID
                    **user.to_dict()
                }
                
            logger.info(f"No Firestore user found for uid: {uid}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by phone: {str(e)}")
            return None

    def get_active_business(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get first business for user or create default"""
        try:
            # Query for first business
            businesses = self.db.collection('users').document(user_id)\
                .collection('businesses')\
                .limit(1)\
                .stream()

            # Get first business
            for business in businesses:
                return {
                    'id': business.id,
                    **business.to_dict()
                }

            # No business found, create default
            business_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document()

            business_data = {
                'id': business_ref.id,
                'name': 'Default Business',
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'type': 'small_business'
            }
            
            business_ref.set(business_data)
            logger.info(f"Created default business for user {user_id}: {business_ref.id}")
            
            return {
                'id': business_ref.id,
                **business_data
            }

        except Exception as e:
            logger.error(f"Error getting/creating business: {str(e)}")
            return None

    def record_ai_action(self, user_id: str, business_id: str, 
                        action_type: str, action_data: Dict[str, Any],
                        related_id: str = None) -> str:
        """Record an AI/System action with improved tracking
        
        Action Types:
        - message_received: New message from user
        - message_sent: Response sent to user
        - folder_created: New folder created
        - spreadsheet_created: New spreadsheet created
        - spreadsheet_updated: Spreadsheet updated
        - transaction_recorded: New transaction recorded
        - transaction_duplicate: Duplicate transaction detected
        - media_processed: Media file processed
        """
        try:
            action_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('actions').document()

            timestamp = datetime.now()
            
            base_data = {
                'action_id': action_ref.id,
                'action_type': action_type,
                'status': 'completed',
                'created_at': firestore.SERVER_TIMESTAMP,
                'timestamp': timestamp.isoformat(),
                'business_id': business_id,
                'user_id': user_id,
                'related_id': related_id,  # ID of related resource (folder_id, spreadsheet_id, etc.)
            }

            # Add action-specific data
            action_data.update(base_data)

            # Add additional context based on action type
            if action_type == 'message_received':
                action_data.update({
                    'platform': action_data.get('platform', 'whatsapp'),
                    'message_type': action_data.get('type', 'text')
                })
            elif action_type == 'folder_created':
                action_data.update({
                    'folder_type': action_data.get('type'),
                    'drive_folder_id': action_data.get('drive_folder_id'),
                    'folder_url': action_data.get('url')
                })
            elif action_type == 'spreadsheet_created':
                action_data.update({
                    'drive_spreadsheet_id': action_data.get('drive_spreadsheet_id'),
                    'spreadsheet_url': action_data.get('url'),
                    'month': action_data.get('month'),
                    'year': action_data.get('year')
                })
            elif action_type == 'transaction_recorded':
                action_data.update({
                    'transaction_id': action_data.get('transaction_id'),
                    'amount': action_data.get('amount'),
                    'category': action_data.get('category'),
                    'merchant': action_data.get('merchant'),
                    'spreadsheet_id': action_data.get('spreadsheet_id')
                })

            action_ref.set(action_data)
            logger.info(f"Recorded action {action_type} for business {business_id}")
            return action_ref.id

        except Exception as e:
            logger.error(f"Error recording action: {str(e)}")
            raise

    def store_business_folder(self, user_id: str, business_id: str, 
                            folder_data: Dict[str, Any], action_id: str = None) -> str:
        """Store folder metadata under business"""
        try:
            folder_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders').document()

            folder_data.update({
                'folder_id': folder_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id,
                'action_id': action_id  # Link to the action that created it
            })

            folder_ref.set(folder_data)
            logger.info(f"Created folder in business {business_id}: {folder_ref.id}")
            return folder_ref.id

        except Exception as e:
            logger.error(f"Error storing folder: {str(e)}")
            raise

    def store_business_spreadsheet(self, user_id: str, business_id: str, 
                                 spreadsheet_data: Dict[str, Any], action_id: str = None) -> str:
        """Store spreadsheet metadata under business"""
        try:
            spreadsheet_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document()

            spreadsheet_data.update({
                'spreadsheet_id': spreadsheet_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id,
                'action_id': action_id  # Link to the action that created it
            })

            spreadsheet_ref.set(spreadsheet_data)
            logger.info(f"Created spreadsheet in business {business_id}: {spreadsheet_ref.id}")
            return spreadsheet_ref.id

        except Exception as e:
            logger.error(f"Error storing spreadsheet: {str(e)}")
            raise

    def record_spreadsheet_update(self, user_id: str, business_id: str, 
                                spreadsheet_id: str, update_data: Dict[str, Any],
                                action_id: str = None) -> str:
        """Record a spreadsheet update action"""
        try:
            update_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document(spreadsheet_id)\
                .collection('updates').document()

            update_data.update({
                'update_id': update_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'business_id': business_id,
                'spreadsheet_id': spreadsheet_id,
                'action_id': action_id  # Link to the action that triggered the update
            })

            update_ref.set(update_data)
            logger.info(f"Recorded spreadsheet update: {update_ref.id}")
            return update_ref.id

        except Exception as e:
            logger.error(f"Error recording spreadsheet update: {str(e)}")
            raise 

    def store_folder_metadata(self, user_id: str, business_id: str, folder_data: Dict[str, Any]) -> str:
        """Store folder metadata in Firestore"""
        try:
            folder_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders').document()

            folder_data.update({
                'folder_id': folder_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id
            })

            folder_ref.set(folder_data)
            logger.info(f"Stored folder metadata: {folder_ref.id}")
            return folder_ref.id

        except Exception as e:
            logger.error(f"Error storing folder metadata: {str(e)}")
            raise

    def get_or_create_business_folder(self, user_id: str, business_id: str) -> Dict[str, Any]:
        """Get or create the root business folder in Drive and Firestore"""
        try:
            # First check Firestore for existing folder
            folders = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', 'business_root')\
                .limit(1)\
                .stream()

            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                # Verify folder still exists in Drive
                try:
                    folder = self.drive_service.files().get(
                        fileId=folder_data['drive_folder_id'],
                        fields='id, name, webViewLink'
                    ).execute()
                    return {
                        'id': folder_data['folder_id'],
                        'drive_id': folder_data['drive_folder_id'],
                        'name': folder['name'],
                        'url': folder['webViewLink'],
                        'type': 'business_root'
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create new business folder in Drive
            folder_metadata = {
                'name': f"Business-{business_id}",
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            drive_folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Record folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'business_root',
                    'name': drive_folder.get('name'),
                    'drive_folder_id': drive_folder.get('id'),
                    'url': drive_folder.get('webViewLink')
                },
                related_id=drive_folder.get('id')
            )
            
            # Set permissions
            self._set_permissions(drive_folder.get('id'), user_id)
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder.get('name'),
                'drive_folder_id': drive_folder.get('id'),
                'url': drive_folder.get('webViewLink'),
                'type': 'business_root'
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder.get('id'),
                'name': drive_folder.get('name'),
                'url': drive_folder.get('webViewLink'),
                'type': 'business_root'
            }
                
        except Exception as e:
            logger.error(f"Error in get_or_create_business_folder: {str(e)}")
            raise

    def get_or_create_transactions_folder(self, user_id: str, business_id: str, 
                                        business_folder_id: str) -> Dict[str, Any]:
        """Get or create Transactions folder within business folder"""
        try:
            # First check Firestore for existing folder
            folders = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', 'transactions')\
                .where('parent_folder_id', '==', business_folder_id)\
                .limit(1)\
                .stream()

            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                # Verify folder still exists in Drive
                try:
                    folder = self.drive_service.files().get(
                        fileId=folder_data['drive_folder_id'],
                        fields='id, name, webViewLink'
                    ).execute()
                    return {
                        'id': folder_data['folder_id'],
                        'drive_id': folder_data['drive_folder_id'],
                        'name': folder['name'],
                        'url': folder['webViewLink'],
                        'type': 'transactions'
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create Transactions folder
            folder_metadata = {
                'name': 'Transactions',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [business_folder_id]
            }
            
            drive_folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Record transactions folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'transactions_folder',
                    'name': drive_folder.get('name'),
                    'drive_folder_id': drive_folder.get('id'),
                    'url': drive_folder.get('webViewLink'),
                    'parent_folder_id': business_folder_id
                },
                related_id=drive_folder.get('id')
            )
            
            # Set permissions
            self._set_permissions(drive_folder.get('id'), user_id)
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder.get('name'),
                'drive_folder_id': drive_folder.get('id'),
                'url': drive_folder.get('webViewLink'),
                'type': 'transactions',
                'parent_folder_id': business_folder_id
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder.get('id'),
                'name': drive_folder.get('name'),
                'url': drive_folder.get('webViewLink'),
                'type': 'transactions'
            }
                
        except Exception as e:
            logger.error(f"Error in get_or_create_transactions_folder: {str(e)}")
            raise

    def get_or_create_year_folder(self, user_id: str, business_id: str, 
                                 transactions_folder_id: str) -> Dict[str, Any]:
        """Get or create year folder within Transactions folder"""
        try:
            # First check Firestore for existing folder
            year = datetime.now().strftime('%Y')  # Use current year if not specified
            
            folders = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', 'year')\
                .where('year', '==', year)\
                .where('parent_folder_id', '==', transactions_folder_id)\
                .limit(1)\
                .stream()

            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                # Verify folder still exists in Drive
                try:
                    folder = self.drive_service.files().get(
                        fileId=folder_data['drive_folder_id'],
                        fields='id, name, webViewLink'
                    ).execute()
                    return {
                        'id': folder_data['folder_id'],
                        'drive_id': folder_data['drive_folder_id'],
                        'name': folder['name'],
                        'url': folder['webViewLink'],
                        'type': 'year',
                        'year': year
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create year folder
            folder_metadata = {
                'name': year,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [transactions_folder_id]
            }
            
            drive_folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Record year folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'year_folder',
                    'name': drive_folder.get('name'),
                    'drive_folder_id': drive_folder.get('id'),
                    'url': drive_folder.get('webViewLink'),
                    'parent_folder_id': transactions_folder_id,
                    'year': year
                },
                related_id=drive_folder.get('id')
            )
            
            # Set permissions
            self._set_permissions(drive_folder.get('id'), user_id)
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder.get('name'),
                'drive_folder_id': drive_folder.get('id'),
                'url': drive_folder.get('webViewLink'),
                'type': 'year',
                'year': year,
                'parent_folder_id': transactions_folder_id
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder.get('id'),
                'name': drive_folder.get('name'),
                'url': drive_folder.get('webViewLink'),
                'type': 'year',
                'year': year
            }
                
        except Exception as e:
            logger.error(f"Error in get_or_create_year_folder: {str(e)}")
            raise

    def get_or_create_monthly_spreadsheet(self, user_id: str, business_id: str, 
                                        year_folder_id: str, date: datetime) -> Dict[str, Any]:
        """Get or create monthly expense spreadsheet in the year folder."""
        try:
            month_name = date.strftime('%B')
            year = date.strftime('%Y')
            spreadsheet_name = f"{month_name}.xlsx"
            sheet_name = f"{month_name} {year}"
            
            # First check Firestore for existing spreadsheet
            spreadsheets = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets')\
                .where('month', '==', month_name)\
                .where('year', '==', year)\
                .where('parent_folder_id', '==', year_folder_id)\
                .limit(1)\
                .stream()

            spreadsheet_docs = list(spreadsheets)
            if spreadsheet_docs:
                spreadsheet_data = spreadsheet_docs[0].to_dict()
                spreadsheet_data['spreadsheet_id'] = spreadsheet_docs[0].id  # Add document ID
                # Verify spreadsheet still exists in Drive
                try:
                    spreadsheet = self.drive_service.files().get(
                        fileId=spreadsheet_data['drive_spreadsheet_id'],
                        fields='id, name, webViewLink'
                    ).execute()
                    return spreadsheet_data
                except Exception as e:
                    logger.warning(f"Drive spreadsheet not found, will recreate: {str(e)}")

            # Create new spreadsheet
            spreadsheet_metadata = {
                'name': spreadsheet_name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [year_folder_id]
            }
            
            drive_spreadsheet = self.drive_service.files().create(
                body=spreadsheet_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Record spreadsheet creation
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='spreadsheet_created',
                action_data={
                    'drive_spreadsheet_id': drive_spreadsheet.get('id'),
                    'url': drive_spreadsheet.get('webViewLink'),
                    'month': date.strftime('%B'),
                    'year': date.strftime('%Y'),
                    'parent_folder_id': year_folder_id
                },
                related_id=drive_spreadsheet.get('id')
            )
            
            # Set permissions
            self._set_permissions(drive_spreadsheet.get('id'), user_id)
            
            # Initialize spreadsheet with headers
            self._initialize_expense_spreadsheet(
                drive_spreadsheet.get('id'), 
                month_name,
                year
            )
            
            # Create Firestore document
            spreadsheet_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document()
            
            spreadsheet_data = {
                'name': drive_spreadsheet.get('name'),
                'drive_spreadsheet_id': drive_spreadsheet.get('id'),
                'url': drive_spreadsheet.get('webViewLink'),
                'type': 'expense_spreadsheet',
                'month': month_name,
                'year': year,
                'sheet_name': sheet_name,
                'parent_folder_id': year_folder_id,
                'spreadsheet_id': spreadsheet_ref.id,  # Add document ID
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            spreadsheet_ref.set(spreadsheet_data)
            
            return spreadsheet_data
                
        except Exception as e:
            logger.error(f"Error in get_or_create_monthly_spreadsheet: {str(e)}")
            raise

    def _initialize_expense_spreadsheet(self, spreadsheet_id: str, month_name: str, year: str):
        """Initialize a new expense spreadsheet with headers and formatting"""
        try:
            sheets_service = build('sheets', 'v4', credentials=self.drive_credentials)
            sheet_name = f"{month_name} {year}"
            
            logger.info(f"Initializing spreadsheet {spreadsheet_id} with sheet name: {sheet_name}")

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
            
            # Define headers with essential fields only
            headers = [[
                'Date',             # A
                'Description',      # B
                'Amount',           # C
                'Category',         # D
                'Payment Method',   # E
                'Status',          # F
                'Transaction ID',   # G - This will now store the Firestore transaction ID
                'Merchant',        # H - Ensure merchant column is present
                'Original Currency', # I
                'Original Amount',  # J
                'Exchange Rate',    # K
                'Timestamp',       # L
                'Created At'       # M
            ]]
            
            # Update headers
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1:M1",
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            # Format headers - make them bold with gray background
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': 13  # A through M
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
                    # Freeze the header row
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

    def record_expense(self, user_id: str, business_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record an expense transaction"""
        try:
            expense_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('transactions').document()
                
            expense_data.update({
                'expense_id': expense_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id
            })
                
            # Record transaction action
            action_id = self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='transaction_recorded',
                action_data={
                    'transaction_id': expense_ref.id,
                    'amount': expense_data.get('amount'),
                    'description': expense_data.get('description'),
                    'category': expense_data.get('category'),
                    'merchant': expense_data.get('merchant'),
                    'spreadsheet_id': expense_data.get('spreadsheet_id')
                },
                related_id=expense_ref.id
            )
                
            expense_data['action_id'] = action_id
            expense_ref.set(expense_data)
                
            return {
                'id': expense_ref.id,
                **expense_data
            }
                
        except Exception as e:
            logger.error(f"Error recording expense: {str(e)}")
            raise

    def get_user_registration_url(self) -> str:
        """Get the URL where users can register"""
        # This should be configured somewhere in your application
        return "https://expensebot.xyz"

    def get_spreadsheet_history(self, user_id: str, business_id: str, 
                              spreadsheet_id: str) -> list:
        """Get history of updates for a specific spreadsheet"""
        try:
            updates = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document(spreadsheet_id)\
                .collection('updates')\
                .order_by('createdAt', direction=firestore.Query.DESCENDING)\
                .stream()
                
            return [{
                'id': update.id,
                **update.to_dict()
            } for update in updates]
                
        except Exception as e:
            logger.error(f"Error getting spreadsheet history: {str(e)}")
            return []

    def get_or_create_monthly_folder(self, user_id: str, business_id: str, date: datetime) -> Dict[str, Any]:
        """Get or create a folder for the specific month and year."""
        try:
            folder_name = f"Expenses_{date.strftime('%B_%Y')}"
            
            # Get business folder ID first
            business_folder_id = self.get_or_create_business_folder(user_id, business_id)
            
            # Check if folder exists in Drive first
            existing_drive_folder = self.get_folder_by_name(business_folder_id, folder_name)
            
            if existing_drive_folder:
                # Check if we have it in Firestore
                folders = self.db.collection('users').document(user_id)\
                    .collection('businesses').document(business_id)\
                    .collection('folders')\
                    .where('drive_folder_id', '==', existing_drive_folder['id'])\
                    .limit(1)\
                    .stream()
                
                folder_docs = list(folders)
                if folder_docs:
                    folder_doc = folder_docs[0]
                    folder_data = folder_doc.to_dict()
                    folder_data['id'] = folder_doc.id  # Add Firestore ID
                    
                    # Get or create spreadsheet
                    spreadsheet = self.get_or_create_monthly_spreadsheet(
                        user_id=user_id,
                        business_id=business_id,
                        folder_id=folder_data['drive_folder_id'],
                        firestore_folder_id=folder_doc.id,
                        date=date
                    )
                    folder_data['spreadsheet'] = spreadsheet
                    
                    return folder_data
                
                # If not in Firestore, create the record
                drive_folder_id = existing_drive_folder['id']
                folder_url = existing_drive_folder['webViewLink']
            
            else:
                # Create new folder in Drive
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [business_folder_id]
                }
                
                drive_folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id, webViewLink'
                ).execute()
                
                drive_folder_id = drive_folder.get('id')
                folder_url = drive_folder.get('webViewLink')
                
                # Share folder with user
                user = self.db.collection('users').document(user_id).get()
                if not user.exists:
                    raise ValueError(f"User {user_id} not found")
                user_email = user.to_dict().get('email')
                if user_email:
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': user_email
                    }
                    self.drive_service.permissions().create(
                        fileId=drive_folder_id,
                        body=permission,
                        sendNotificationEmail=False
                    ).execute()
            
            # Create/Update Firestore record
            folder_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('folders').document()
            
            folder_data = {
                'name': folder_name,
                'month_year': date.strftime('%B_%Y'),
                'drive_folder_id': drive_folder_id,
                'folder_url': folder_url,
                'status': 'active',
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            # Record action
            action_id = self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='create_folder',
                action_data={
                    'folder_name': folder_name,
                    'drive_folder_id': drive_folder_id,
                    'folder_url': folder_url,
                    'firestore_folder_id': folder_ref.id
                }
            )
            
            folder_data['action_id'] = action_id
            folder_ref.set(folder_data)
            
            # Get or create spreadsheet
            spreadsheet = self.get_or_create_monthly_spreadsheet(
                user_id=user_id,
                business_id=business_id,
                folder_id=drive_folder_id,
                firestore_folder_id=folder_ref.id,
                date=date
            )
            
            folder_data['id'] = folder_ref.id
            folder_data['spreadsheet'] = spreadsheet
            
            return folder_data
            
        except Exception as e:
            logger.error(f"Error in get_or_create_monthly_folder: {str(e)}")
            raise

    def update_expense_spreadsheet(self, user_id: str, business_id: str, 
                                 spreadsheet_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update expense spreadsheet with new transaction."""
        try:
            # Get spreadsheet data from Firestore
            spreadsheet = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document(spreadsheet_id).get()
            
            if not spreadsheet.exists:
                raise ValueError(f"Spreadsheet {spreadsheet_id} not found")
            
            spreadsheet_data = spreadsheet.to_dict()
            drive_spreadsheet_id = spreadsheet_data.get('drive_spreadsheet_id')
            sheet_name = spreadsheet_data.get('sheet_name')
            
            if not sheet_name or not drive_spreadsheet_id:
                raise ValueError("Invalid spreadsheet data")

            sheets_service = build('sheets', 'v4', credentials=self.drive_credentials)

            # Format amount as number
            try:
                amount = float(expense_data['amount'])
            except (TypeError, ValueError):
                amount = 0.0

            # Prepare new row data
            new_row = [
                expense_data['date'],                    # Date
                expense_data['description'],             # Description
                amount,                                  # Amount
                expense_data['category'],                # Category
                expense_data['payment_method'],          # Payment Method
                expense_data.get('status', 'Completed'), # Status
                expense_data.get('transaction_id', ''),  # Transaction ID (Firestore ID)
                expense_data.get('merchant', 'N/A'),     # Merchant
                expense_data.get('orig_currency', 'GBP'), # Original Currency
                expense_data.get('orig_amount', amount),  # Original Amount
                expense_data.get('exchange_rate', 1.0),   # Exchange Rate
                expense_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),  # Timestamp
                expense_data.get('createdAt', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))   # Created At
            ]

            # Append the new row
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=drive_spreadsheet_id,
                range=f"{sheet_name}!A:M",  # Updated to include all columns
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': [new_row]}
            ).execute()

            # Format the new row
            if 'updates' in result:
                updated_range = result.get('updates', {}).get('updatedRange', '')
                match = re.search(r'!A(\d+)', updated_range)
                if match:
                    row_number = int(match.group(1))
                    format_request = {
                        'requests': [
                            # Format amount as currency
                            {
                                'repeatCell': {
                                    'range': {
                                        'sheetId': 0,
                                        'startRowIndex': row_number - 1,
                                        'endRowIndex': row_number,
                                        'startColumnIndex': 2,  # Amount column (C)
                                        'endColumnIndex': 3
                                    },
                                    'cell': {
                                        'userEnteredFormat': {
                                            'numberFormat': {
                                                'type': 'CURRENCY',
                                                'pattern': '"£"#,##0.00'
                                            }
                                        }
                                    },
                                    'fields': 'userEnteredFormat.numberFormat'
                                }
                            },
                            # Explicitly set non-bold for the entire row
                            {
                                'repeatCell': {
                                    'range': {
                                        'sheetId': 0,
                                        'startRowIndex': row_number - 1,
                                        'endRowIndex': row_number,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 13  # A through M
                                    },
                                    'cell': {
                                        'userEnteredFormat': {
                                            'textFormat': {
                                                'bold': False
                                            }
                                        }
                                    },
                                    'fields': 'userEnteredFormat.textFormat'
                                }
                            }
                        ]
                    }

                    sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=drive_spreadsheet_id,
                        body=format_request
                    ).execute()

            # Record update in Firestore
            update_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document(spreadsheet_id)\
                .collection('updates').document()

            update_data = {
                'update_id': update_ref.id,
                'transaction_id': expense_data.get('transaction_id'),
                'transaction_date': expense_data['date'],
                'amount': amount,
                'description': expense_data['description'],
                'merchant': expense_data.get('merchant', 'N/A'),
                'row_number': row_number if 'row_number' in locals() else None,
                'createdAt': firestore.SERVER_TIMESTAMP
            }
            
            update_ref.set(update_data)

            return {
                'spreadsheet_url': spreadsheet_data.get('url'),
                'update_id': update_ref.id,
                'status': 'completed',
                'row_number': row_number if 'row_number' in locals() else None
            }

        except Exception as e:
            logger.error(f"Error updating expense spreadsheet: {str(e)}")
            raise

    def store_message(self, user_id: str, business_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a WhatsApp message interaction"""
        try:
            # Create message reference under the business
            message_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('messages').document()
            
            message_data.update({
                'message_id': message_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'delivered'
            })
            
            # If there's media content, handle storage based on environment
            if message_data.get('media_content'):
                media_path = f"businesses/{business_id}/messages/{message_ref.id}/media"
                
                if self.is_emulated:
                    # Handle storage emulator
                    try:
                        # Store media content reference for emulator
                        media_url = f"{self.storage_host}/{Config.FIREBASE_STORAGE_BUCKET}/{media_path}"
                        
                        # In development, we might want to just store the content length
                        # or hash instead of actually uploading
                        media_data = message_data['media_content']
                        content_length = len(media_data) if isinstance(media_data, bytes) else len(str(media_data))
                        
                        message_data.update({
                            'media_url': media_url,
                            'media_path': media_path,
                            'media_size': content_length,
                            'media_type': message_data.get('media_type', 'application/octet-stream'),
                            'environment': 'development'
                        })
                        
                        logger.info(f"Emulator: Stored media reference at {media_url}")
                        
                    except Exception as e:
                        logger.warning(f"Emulator: Failed to handle media: {str(e)}")
                        # Continue without media in development
                        message_data['media_error'] = str(e)
                else:
                    # Production storage handling
                    media_blob = self.bucket.blob(media_path)
                    media_blob.upload_from_string(
                        message_data['media_content'],
                        content_type=message_data.get('media_type', 'application/octet-stream')
                    )
                    
                    # Generate a signed URL that expires in 7 days
                    media_url = media_blob.generate_signed_url(
                        version="v4",
                        expiration=datetime.timedelta(days=7),
                        method="GET"
                    )
                    
                    message_data.update({
                        'media_url': media_url,
                        'media_path': media_path,
                        'environment': 'production'
                    })
                
                # Remove the raw content from the stored data
                del message_data['media_content']
            
            message_ref.set(message_data)
            
            return {
                'id': message_ref.id,
                **message_data
            }
            
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise

    def get_message_history(self, user_id: str, business_id: str, 
                           limit: int = 50, start_after: str = None) -> List[Dict[str, Any]]:
        """Get message history for a business with pagination"""
        try:
            query = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('messages')\
                .order_by('createdAt', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            if start_after:
                # Get the last document for pagination
                last_doc = self.db.collection('users').document(user_id)\
                    .collection('businesses').document(business_id)\
                    .collection('messages').document(start_after).get()
                if last_doc.exists:
                    query = query.start_after(last_doc)
            
            messages = query.stream()
            
            return [{
                'id': msg.id,
                **msg.to_dict()
            } for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting message history: {str(e)}")
            return []

    def get_message_by_id(self, user_id: str, business_id: str, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID"""
        try:
            message = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('messages').document(message_id).get()
            
            if message.exists:
                return {
                    'id': message.id,
                    **message.to_dict()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting message: {str(e)}")
            return None

    

    def _set_permissions(self, file_id: str, user_id: str):
        """Set permissions for a Drive file/folder for both user and service account"""
        try:
            # Get user email from Firestore
            user = self.db.collection('users').document(user_id).get()
            if not user.exists:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user.to_dict().get('email')
            if not user_email:
                raise ValueError(f"No email found for user {user_id}")

            # Get service account email
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']

            logger.info(f"Setting permissions for file {file_id}")
            logger.info(f"User email: {user_email}")
            logger.info(f"Service account email: {service_account_email}")

            try:
                # First give the user editor access
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
                
                logger.info(f"Set writer permission for user: {user_email}")

                # Then make service account the owner
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
                    sendNotificationEmail=True  # Required for ownership transfer
                ).execute()
                
                logger.info(f"Set owner permission for service account: {service_account_email}")

                # Verify permissions
                permissions = self.drive_service.permissions().list(
                    fileId=file_id,
                    fields='permissions(id,emailAddress,role,type)'
                ).execute()

                logger.info("Current permissions:")
                for permission in permissions.get('permissions', []):
                    logger.info(f"- {permission.get('emailAddress')}: {permission.get('role')}")

            except Exception as e:
                logger.error(f"Error setting individual permission: {str(e)}")
                
                # Try alternative permission method
                try:
                    logger.info("Trying alternative permission method...")
                    
                    # Make file accessible to anyone with the link (as backup)
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
                    
                    logger.info("Set backup anyone-with-link permission")
                    
                except Exception as backup_error:
                    logger.error(f"Backup permission method also failed: {str(backup_error)}")
                    raise backup_error

        except Exception as e:
            logger.error(f"Error in _set_permissions: {str(e)}")
            raise

    def check_duplicate_transaction(self, user_id: str, business_id: str, 
                                  transaction_data: Dict[str, Any]) -> bool:
        """
        Check if a similar transaction already exists based on date, amount, and description.
        Returns True if duplicate found, False otherwise.
        """
        try:
            # Get transactions from the same date with same amount
            transactions = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('transactions')\
                .where('date', '==', transaction_data['date'])\
                .where('amount', '==', float(transaction_data['amount']))\
                .stream()

            # Check for similar descriptions
            for transaction in transactions:
                tx_data = transaction.to_dict()
                # Use string similarity to compare descriptions
                if self._are_descriptions_similar(
                    tx_data.get('description', '').lower(),
                    transaction_data.get('description', '').lower()
                ):
                    logger.warning(f"Duplicate transaction found: {tx_data}")
                    return True

            # Also check in spreadsheet for the current month
            if 'spreadsheet_id' in transaction_data:
                spreadsheet = self.db.collection('users').document(user_id)\
                    .collection('businesses').document(business_id)\
                    .collection('spreadsheets').document(transaction_data['spreadsheet_id']).get()
                
                if spreadsheet.exists:
                    spreadsheet_data = spreadsheet.to_dict()
                    drive_spreadsheet_id = spreadsheet_data.get('drive_spreadsheet_id')
                    sheet_name = spreadsheet_data.get('sheet_name')

                    if drive_spreadsheet_id and sheet_name:
                        sheets_service = build('sheets', 'v4', credentials=self.drive_credentials)
                        result = sheets_service.spreadsheets().values().get(
                            spreadsheetId=drive_spreadsheet_id,
                            range=f"{sheet_name}!A:C"  # Get date, description, amount
                        ).execute()

                        values = result.get('values', [])[1:]  # Skip header row
                        for row in values:
                            if len(row) >= 3:
                                if (row[0] == transaction_data['date'] and 
                                    self._are_descriptions_similar(row[1].lower(), transaction_data['description'].lower()) and
                                    abs(float(row[2]) - float(transaction_data['amount'])) < 0.01):  # Handle floating point comparison
                                    logger.warning(f"Duplicate transaction found in spreadsheet: {row}")
                                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking for duplicate transaction: {str(e)}")
            return False

    def _are_descriptions_similar(self, desc1: str, desc2: str) -> bool:
        """
        Compare two descriptions to determine if they are similar enough to be considered duplicates.
        """
        # Remove common variations
        desc1 = desc1.replace('ltd', '').replace('limited', '').strip()
        desc2 = desc2.replace('ltd', '').replace('limited', '').strip()
        
        # If either description is contained within the other
        if desc1 in desc2 or desc2 in desc1:
            return True
        
        # Calculate word overlap
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        # If more than 70% words match, consider it similar
        return overlap / total > 0.7 if total > 0 else False