import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from config import Config
import logging
from datetime import datetime
from typing import Optional, Dict, Any
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
                        action_type: str, action_data: Dict[str, Any]) -> str:
        """Record an AI action (message, folder creation, spreadsheet update, etc.)"""
        try:
            action_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('actions').document()

            action_data.update({
                'action_id': action_ref.id,
                'action_type': action_type,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'completed',
                'business_id': business_id,
                'user_id': user_id
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

    def get_or_create_business_folder(self, user_id: str, business_id: str) -> str:
        """Get or create the root business folder in Drive"""
        try:
            # Check if business folder ID exists in Firestore
            business = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id).get()
            
            if business.exists:
                drive_folder_id = business.to_dict().get('drive_folder_id')
                if drive_folder_id:
                    try:
                        # Verify folder exists in Drive
                        self.drive_service.files().get(fileId=drive_folder_id).execute()
                        return drive_folder_id
                    except Exception as e:
                        logger.warning(f"Business Drive folder {drive_folder_id} not found, will recreate")
            
            # Create new business folder in Drive
            folder_metadata = {
                'name': f"Business_Expenses_{business_id}",
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            drive_folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            drive_folder_id = drive_folder.get('id')
            
            # Update business document with Drive folder ID
            self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .update({'drive_folder_id': drive_folder_id})
            
            return drive_folder_id
            
        except Exception as e:
            logger.error(f"Error in get_or_create_business_folder: {str(e)}")
            raise

    def get_folder_by_name(self, parent_folder_id: str, folder_name: str) -> Optional[Dict[str, Any]]:
        """Check if folder exists in Drive by name and parent."""
        try:
            query = f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)'
            ).execute()
            
            files = results.get('files', [])
            return files[0] if files else None
            
        except Exception as e:
            logger.error(f"Error checking folder existence: {str(e)}")
            return None

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

    def record_expense(self, user_id: str, business_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record an expense transaction"""
        try:
            expense_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('expenses').document()
                
            expense_data.update({
                'expense_id': expense_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id
            })
                
            # Record expense creation action
            action_id = self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='create_expense',
                action_data=expense_data
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

    def get_or_create_monthly_spreadsheet(self, user_id: str, business_id: str, 
                                    folder_id: str, firestore_folder_id: str,
                                    date: datetime) -> Dict[str, Any]:
        """Get or create monthly expense spreadsheet in the specified folder."""
        try:
            month_year = date.strftime('%B_%Y')
            spreadsheet_name = f"Expenses_{month_year}"
            
            # Check existing spreadsheets in Firestore
            spreadsheets = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets')\
                .where('month_year', '==', month_year)\
                .where('folder_id', '==', firestore_folder_id)\
                .limit(1)\
                .stream()
            
            for spreadsheet in spreadsheets:
                spreadsheet_data = spreadsheet.to_dict()
                drive_spreadsheet_id = spreadsheet_data.get('drive_spreadsheet_id')
                
                try:
                    # Verify spreadsheet exists in Drive
                    drive_file = self.drive_service.files().get(
                        fileId=drive_spreadsheet_id,
                        fields='id, webViewLink'
                    ).execute()
                    
                    spreadsheet_data['id'] = spreadsheet.id
                    spreadsheet_data['url'] = drive_file.get('webViewLink')
                    return spreadsheet_data
                    
                except Exception as e:
                    logger.warning(f"Drive spreadsheet {drive_spreadsheet_id} not found, will recreate")
            
            # Create new spreadsheet
            spreadsheet_metadata = {
                'name': spreadsheet_name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [folder_id]
            }
            
            drive_spreadsheet = self.drive_service.files().create(
                body=spreadsheet_metadata,
                fields='id, webViewLink'
            ).execute()
            
            drive_spreadsheet_id = drive_spreadsheet.get('id')
            spreadsheet_url = drive_spreadsheet.get('webViewLink')
            
            # Initialize spreadsheet with headers and formatting
            sheets_service = build('sheets', 'v4', credentials=self.drive_credentials)
            
            # Instead of creating a new worksheet, rename and use Sheet1
            rename_request = {
                'requests': [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': 0,  # Sheet1's ID is always 0
                            'title': date.strftime('%B %Y')
                        },
                        'fields': 'title'
                    }
                }]
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=drive_spreadsheet_id,
                body=rename_request
            ).execute()
            
            # Add headers to Sheet1
            headers = [
                ['Transaction started (UTC)', 'Transaction completed (UTC)', 'Transaction ID', 'Transaction status', 
                 'Transaction type', 'Transaction description', 'Payer', 'Card number', 'Expense split #','Orig currency','Orig amount (Orig currency)']
            ]
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=drive_spreadsheet_id,
                range=f"'{date.strftime('%B %Y')}'!A1:K1",  # Updated range to use renamed Sheet1
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
            # Format headers
            format_requests = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,  # Sheet1's ID is always 0
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                                    'textFormat': {'bold': True},
                                    'horizontalAlignment': 'CENTER'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                        }
                    }
                ]
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=drive_spreadsheet_id,
                body=format_requests
            ).execute()
            
            # Store in Firestore
            spreadsheet_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document()
            
            spreadsheet_data = {
                'name': spreadsheet_name,
                'month_year': month_year,
                'drive_spreadsheet_id': drive_spreadsheet_id,
                'folder_id': firestore_folder_id,  # Store Firestore folder ID
                'url': spreadsheet_url,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            }
            
            # Record action
            action_id = self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='create_spreadsheet',
                action_data={
                    'spreadsheet_name': spreadsheet_name,
                    'drive_spreadsheet_id': drive_spreadsheet_id,
                    'folder_id': firestore_folder_id,
                    'url': spreadsheet_url
                }
            )
            
            spreadsheet_data['action_id'] = action_id
            spreadsheet_data['id'] = spreadsheet_ref.id
            
            spreadsheet_ref.set(spreadsheet_data)
            
            return spreadsheet_data
            
        except Exception as e:
            logger.error(f"Error in get_or_create_monthly_spreadsheet: {str(e)}")
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
            
            # Get the current month-year worksheet name
            transaction_date = datetime.strptime(expense_data['date'], '%Y-%m-%d')
            month_year = transaction_date.strftime('%B %Y')
            
            # Convert date to UTC timestamp
            try:
                transaction_started = datetime.strptime(
                    f"{expense_data['date']} {expense_data.get('time', '00:00:00')}", 
                    '%Y-%m-%d %H:%M:%S'
                ).strftime('%Y-%m-%d %H:%M:%S UTC')
                transaction_completed = datetime.strptime(
                    f"{expense_data['date']} {expense_data.get('time', '23:59:59')}", 
                    '%Y-%m-%d %H:%M:%S'
                ).strftime('%Y-%m-%d %H:%M:%S UTC')
            except Exception as e:
                logger.warning(f"Error parsing transaction time: {e}, using default timestamps")
                transaction_started = f"{expense_data['date']} 00:00:00 UTC"
                transaction_completed = f"{expense_data['date']} 23:59:59 UTC"

            # Get existing transactions
            sheets_service = build('sheets', 'v4', credentials=self.drive_credentials)
            
            # Prepare new row data
            new_row = [
                transaction_started,                    # Transaction started (UTC)
                transaction_completed,                  # Transaction completed (UTC)
                expense_data.get('transaction_id', ''), # Transaction ID
                'Completed',                           # Transaction status
                expense_data.get('transaction_type', 'Expense'), # Transaction type
                expense_data.get('description', ''),    # Transaction description
                expense_data.get('payer', 'Self'),      # Payer
                expense_data.get('payment_method', ''), # Card number/payment method
                '1',                                    # Expense split #
                expense_data.get('orig_currency', 'GBP'), # Original currency
                expense_data.get('orig_amount', expense_data.get('amount', 0)) # Original amount
            ]

            # Append the new row with regular (non-bold) formatting
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=drive_spreadsheet_id,
                range=f"'{month_year}'!A:K",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [new_row]}
            ).execute()

            # Get the row number where data was inserted
            updated_range = result.get('updates', {}).get('updatedRange', '')
            match = re.search(r'!A(\d+)', updated_range)
            if match:
                row_number = int(match.group(1))
                
                # Apply regular (non-bold) formatting to the new row
                format_request = {
                    'requests': [{
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': row_number - 1,
                                'endRowIndex': row_number,
                                'startColumnIndex': 0,
                                'endColumnIndex': 11
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'textFormat': {'bold': False},
                                    'horizontalAlignment': 'LEFT'
                                }
                            },
                            'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
                        }
                    }]
                }
                
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=drive_spreadsheet_id,
                    body=format_request
                ).execute()

            return {
                'spreadsheet_url': spreadsheet_data.get('url'),
                'update_id': expense_data.get('action_id'),
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error updating expense spreadsheet: {str(e)}")
            raise