import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from config import Config
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from .google_drive_service import GoogleDriveService
from google.cloud.firestore import AsyncClient

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
        """Initialize Firebase and Google Drive services"""
        try:
            if Config.IS_DEVELOPMENT:
                os.environ["FIRESTORE_EMULATOR_HOST"] = Config.FIREBASE_FIRESTORE_EMULATOR_HOST
                os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = Config.FIREBASE_AUTH_EMULATOR_HOST
                os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = Config.FIREBASE_STORAGE_EMULATOR_HOST
                logger.info("Using Firebase emulators")
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

            # Initialize both sync and async clients
            self.db = firestore.client()  # Sync client
            # self.db_async = AsyncClient()  # Async client
            self.auth = auth
            self.bucket = storage.bucket()

            # Add Google Drive setup
            self.drive_credentials = service_account.Credentials.from_service_account_info(
                json.loads(Config.SERVICE_ACCOUNT_KEY),
                scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
            )
            self.drive_service = build('drive', 'v3', credentials=self.drive_credentials)

            # Initialize Google Drive service
            self.drive_service = GoogleDriveService()

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
            user = user_ref.get()  # This returns a DocumentSnapshot, not a coroutine

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
                    folder = self.drive_service.get_file(folder_data['drive_folder_id'])
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
            drive_folder = self.drive_service.create_folder(
                folder_name=f"Business-{business_id}"
            )
            
            # Record folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'business_root',
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id'],
                    'url': drive_folder['url']
                },
                related_id=drive_folder['id']
            )
            
            # Get user email for permissions
            user = self.db.collection('users').document(user_id).get()
            if not user.exists:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user.to_dict().get('email')
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']
            
            # Set permissions
            self.drive_service.set_permissions(
                drive_folder['id'],
                user_email,
                service_account_email
            )
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': 'business_root'
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
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
                    folder = self.drive_service.get_file(folder_data['drive_folder_id'])
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
            drive_folder = self.drive_service.create_folder(
                folder_name='Transactions',
                parent_id=business_folder_id
            )
            
            # Record transactions folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'transactions_folder',
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id'],
                    'url': drive_folder['url'],
                    'parent_folder_id': business_folder_id
                },
                related_id=drive_folder['id']
            )
            
            # Get user email for permissions
            user = self.db.collection('users').document(user_id).get()
            if not user.exists:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user.to_dict().get('email')
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']
            
            # Set permissions
            self.drive_service.set_permissions(
                drive_folder['id'],
                user_email,
                service_account_email
            )
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': 'transactions',
                'parent_folder_id': business_folder_id
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
                'type': 'transactions'
            }
                
        except Exception as e:
            logger.error(f"Error in get_or_create_transactions_folder: {str(e)}")
            raise

    def get_or_create_year_folder(self, user_id: str, business_id: str, 
                                 transactions_folder_id: str) -> Dict[str, Any]:
        """Get or create year folder within Transactions folder"""
        try:
            year = datetime.now().strftime('%Y')
            
            # First check Firestore for existing folder
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
                    folder = self.drive_service.get_file(folder_data['drive_folder_id'])
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
            drive_folder = self.drive_service.create_folder(
                folder_name=year,
                parent_id=transactions_folder_id
            )
            
            # Record year folder creation action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'year_folder',
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id'],
                    'url': drive_folder['url'],
                    'parent_folder_id': transactions_folder_id,
                    'year': year
                },
                related_id=drive_folder['id']
            )
            
            # Get user email for permissions
            user = self.db.collection('users').document(user_id).get()
            if not user.exists:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user.to_dict().get('email')
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']
            
            # Set permissions
            self.drive_service.set_permissions(
                drive_folder['id'],
                user_email,
                service_account_email
            )
            
            # Store in Firestore
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': 'year',
                'year': year,
                'parent_folder_id': transactions_folder_id
            }
            
            folder_id = self.store_folder_metadata(user_id, business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
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
                spreadsheet_data['spreadsheet_id'] = spreadsheet_docs[0].id
                # Verify spreadsheet still exists in Drive
                try:
                    spreadsheet = self.drive_service.get_file(spreadsheet_data['drive_spreadsheet_id'])
                    return spreadsheet_data
                except Exception as e:
                    logger.warning(f"Drive spreadsheet not found, will recreate: {str(e)}")

            # Create new spreadsheet
            drive_spreadsheet = self.drive_service.create_spreadsheet(
                name=spreadsheet_name,
                parent_folder_id=year_folder_id
            )
            
            # Initialize the spreadsheet
            self.drive_service.initialize_expense_spreadsheet(
                drive_spreadsheet['id'],
                month_name,
                year
            )
            
            # Record spreadsheet creation
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='spreadsheet_created',
                action_data={
                    'drive_spreadsheet_id': drive_spreadsheet['id'],
                    'url': drive_spreadsheet['url'],
                    'month': month_name,
                    'year': year,
                    'parent_folder_id': year_folder_id
                },
                related_id=drive_spreadsheet['id']
            )
            
            # Get user email for permissions
            user = self.db.collection('users').document(user_id).get()
            if not user.exists:
                raise ValueError(f"User {user_id} not found")
            
            user_email = user.to_dict().get('email')
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']
            
            # Set permissions
            self.drive_service.set_permissions(
                drive_spreadsheet['id'],
                user_email,
                service_account_email
            )
            
            # Create Firestore document
            spreadsheet_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('spreadsheets').document()
            
            spreadsheet_data = {
                'name': drive_spreadsheet['name'],
                'drive_spreadsheet_id': drive_spreadsheet['id'],
                'url': drive_spreadsheet['url'],
                'type': 'expense_spreadsheet',
                'month': month_name,
                'year': year,
                'sheet_name': sheet_name,
                'parent_folder_id': year_folder_id,
                'spreadsheet_id': spreadsheet_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            spreadsheet_ref.set(spreadsheet_data)
            
            return spreadsheet_data
                
        except Exception as e:
            logger.error(f"Error in get_or_create_monthly_spreadsheet: {str(e)}")
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

    def store_bank_connection(self, user_id: str, business_id: str, plaid_data: Dict, accounts: List[Dict]) -> str:
        """Store bank connection details in Firestore"""
        try:
            logger.info(f"Storing bank connection for user {user_id}")
            connection_ref = self.db.collection('bank_connections').document()
            
            # Create connection data
            connection_data = {
                'user_id': user_id,
                'business_id': business_id,
                'plaid_item_id': plaid_data['item_id'],
                'access_token': plaid_data['access_token'],
                'accounts': accounts,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Store in Firestore
            connection_ref.set(connection_data)
            logger.info(f"Stored bank connection with ID: {connection_ref.id}")
            
            # Record the action
            self.record_ai_action(
                user_id=user_id,
                business_id=business_id,
                action_type='bank_connection_created',
                action_data={
                    'provider': 'plaid',
                    'num_accounts': len(accounts),
                    'connection_id': connection_ref.id
                }
            )
            
            return connection_ref.id
            
        except Exception as e:
            logger.error(f"Error storing bank connection: {str(e)}")
            raise

    def get_bank_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get bank connection details"""
        try:
            connection_ref = self.db.collection('bank_connections').document(connection_id)
            connection = connection_ref.get()
            
            if not connection.exists:
                return None
            
            return connection.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting bank connection: {str(e)}")
            return None

    def get_bank_connections(self, business_id: str) -> List[Dict[str, Any]]:
        """Get all bank connections for a business"""
        try:
            connections_ref = self.db.collection('bank_connections')\
                .where('business_id', '==', business_id)
            
            connections = []
            for doc in connections_ref.stream():
                connection_data = doc.to_dict()
                connections.append({
                    'id': doc.id,
                    'bankName': connection_data.get('provider_name', 'Connected Bank'),
                    'status': connection_data.get('status', 'active'),
                    'lastSync': connection_data.get('last_sync'),
                    'accountCount': len(connection_data.get('accounts', [])),
                    'createdAt': connection_data.get('created_at'),
                    'updatedAt': connection_data.get('updated_at')
                })
            
            logger.info(f"Found {len(connections)} bank connections for business {business_id}")
            return connections
            
        except Exception as e:
            logger.error(f"Error getting bank connections: {str(e)}")
            raise

    def store_transactions(self, user_id: str, business_id: str, transactions: List[Dict[str, Any]]) -> None:
        """Store bank transactions"""
        try:
            batch = self.db.batch()
            
            for transaction in transactions:
                transaction_ref = self.db.collection('transactions').document()
                transaction_data = {
                    'user_id': user_id,
                    'business_id': business_id,
                    'plaid_transaction_id': transaction['id'],
                    'amount': transaction['amount'],
                    'date': transaction['date'],
                    'description': transaction['description'],
                    'category': transaction.get('category', 'Uncategorized'),
                    'merchant': transaction.get('merchant', 'Unknown'),
                    'status': 'pending' if transaction.get('pending', False) else 'completed',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                batch.set(transaction_ref, transaction_data)
            
            batch.commit()
            logger.info(f"Stored {len(transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Error storing transactions: {str(e)}")
            raise

    async def get_bank_connection(
        self, 
        user_id: str, 
        business_id: str, 
        connection_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get bank connection details"""
        try:
            connection_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('bank_connections').document(connection_id)
                
            connection = await connection_ref.get()
            
            if not connection.exists:
                return None
            
            connection_data = connection.to_dict()
            
            # Decrypt sensitive data
            connection_data['access_token'] = self._decrypt_sensitive_data(
                connection_data['access_token']
            )
            connection_data['refresh_token'] = self._decrypt_sensitive_data(
                connection_data['refresh_token']
            )
            
            return connection_data
            
        except Exception as e:
            logger.error(f"Error getting bank connection: {str(e)}")
            return None

    async def update_bank_tokens(
        self, 
        user_id: str, 
        business_id: str,
        connection_id: str,
        tokens: Dict[str, Any]
    ) -> None:
        """Update bank connection tokens"""
        try:
            connection_ref = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('bank_connections').document(connection_id)
                
            await connection_ref.update({
                'access_token': self._encrypt_sensitive_data(tokens['access_token']),
                'refresh_token': self._encrypt_sensitive_data(tokens['refresh_token']),
                'expires_at': datetime.now() + timedelta(seconds=tokens['expires_in']),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            
        except Exception as e:
            logger.error(f"Error updating bank tokens: {str(e)}")
            raise

    async def is_transaction_synced(
        self, 
        user_id: str, 
        business_id: str,
        bank_transaction_id: str
    ) -> bool:
        """Check if a bank transaction has already been synced"""
        try:
            transactions = self.db.collection('users').document(user_id)\
                .collection('businesses').document(business_id)\
                .collection('transactions')\
                .where('bank_transaction_id', '==', bank_transaction_id)\
                .limit(1)\
                .stream()
                
            return len(list(transactions)) > 0
                
        except Exception as e:
            logger.error(f"Error checking transaction sync status: {str(e)}")
            return False

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storing"""
        # TODO: Implement proper encryption
        # For now, just return the data as-is
        return data

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        # TODO: Implement proper decryption
        # For now, just return the data as-is
        return encrypted_data

    async def get_bank_connections(self, business_id: str) -> List[Dict[str, Any]]:
        """Get all bank connections for a business"""
        try:
            # Update the collection path to match the structure
            connections_ref = self.db.collection('businesses').document(business_id)\
                .collection('bank_connections')
            
            connections = []
            async for doc in connections_ref.stream():
                connection_data = doc.to_dict()
                # Format the connection data for frontend
                connections.append({
                    'id': doc.id,
                    'bankName': connection_data.get('provider_name', 'Unknown Bank'),
                    'status': connection_data.get('status', 'inactive'),
                    'lastSync': connection_data.get('last_sync'),
                    'accountCount': len(connection_data.get('accounts', [])),
                    'createdAt': connection_data.get('created_at'),
                    'updatedAt': connection_data.get('updated_at')
                })
            
            logger.info(f"Found {len(connections)} bank connections for business {business_id}")
            return connections
            
        except Exception as e:
            logger.error(f"Error getting bank connections: {str(e)}")
            raise

    async def get_connection_by_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get connection details by account ID"""
        try:
            connections = self.db.collection_group('bank_connections')\
                .where('accounts', 'array_contains', {'id': account_id})\
                .limit(1)
            
            async for doc in connections.stream():
                business_id = doc.reference.parent.parent.id
                return {
                    'id': doc.id,
                    'business_id': business_id,
                    **doc.to_dict()
                }
            return None
        except Exception as e:
            logger.error(f"Error getting connection by account: {str(e)}")
            raise

    async def update_connection_sync_time(self, business_id: str, connection_id: str):
        """Update last sync time for a connection"""
        try:
            connection_ref = self.db.collection('businesses').document(business_id)\
                .collection('bank_connections').document(connection_id)
            
            await connection_ref.update({
                'last_sync': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Error updating connection sync time: {str(e)}")
            raise

    async def update_connection_status(self, business_id: str, connection_id: str, status: str):
        """Update connection status"""
        try:
            connection_ref = self.db.collection('businesses').document(business_id)\
                .collection('bank_connections').document(connection_id)
            
            await connection_ref.update({
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.error(f"Error updating connection status: {str(e)}")
            raise

    async def delete_auth_state(self, state: str) -> None:
        """Delete used OAuth state"""
        try:
            await self.db.collection('auth_states').document(state).delete()
            logger.info(f"Deleted auth state: {state}")
        except Exception as e:
            logger.error(f"Error deleting auth state: {str(e)}")
            # Don't raise here as this is cleanup

    def get_user_registration_url(self) -> str:
        """Get the URL for user registration"""
        try:
            # Get the base URL from config
            base_url = Config.FRONTEND_URL or 'http://localhost:3000'
            
            # Create a registration URL with a unique token
            registration_url = f"{base_url}"
            
            logger.info(f"Generated registration URL: {registration_url}")
            return registration_url
            
        except Exception as e:
            logger.error(f"Error generating registration URL: {str(e)}")
            # Return a default URL if there's an error
            return "https://expensebot.xyz"