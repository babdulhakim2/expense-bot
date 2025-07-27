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
from .google_drive_service import GoogleDriveService
import mimetypes
import ssl

# Set up logger
logger = logging.getLogger(__name__)

# Google Sheets and Drive setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    # Write service account key to a temporary file
    import tempfile
    import json
    
    # Check if we're in Cloud Functions with mounted secrets
    if os.environ.get('FUNCTION_NAME') and not Config.SERVICE_ACCOUNT_KEY:
        logger.info("Running in Cloud Function, skipping Google Sheets/Drive setup")
        creds = None
    else:
        service_account_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        json.dump(json.loads(Config.SERVICE_ACCOUNT_KEY), service_account_file)
        service_account_file.close()
        
        # Update your credentials initialization
        creds = ServiceAccountCredentials.from_json_keyfile_name(service_account_file.name, scope)
    
except Exception as e:
    logger.error(f"Failed to initialize credentials: {str(e)}")
    creds = None

sheets_client = gspread.authorize(creds) if creds else None
drive_service = build('drive', 'v3', credentials=creds) if creds else None

class FirebaseService:
    def __init__(self):
        """Initialize Firebase and Google Drive services"""
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

            # Initialize Google Drive service
            self.drive_service = GoogleDriveService()

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise

    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number from Firestore
        
        Args:
            phone_number: Phone number in E.164 format (e.g. +1234567890)
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            # Query users collection for phone number
            users = self.db.collection('users')\
                .where('phoneNumber', '==', phone_number)\
                .limit(1)\
                .stream()
            
            # Get the first user document from the stream
            user_docs = list(users)
            if user_docs:
                user_doc = user_docs[0]  # Get first document
                return {
                    'id': user_doc.id,
                    **user_doc.to_dict()
                }
                
            logger.info(f"No user found for phone_number: {phone_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by phone: {str(e)}")
            return None

    def get_active_business(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get first business where user is owner or create default"""
        try:
            # Query businesses where user is owner
            businesses = self.db.collection('businesses')\
                .where('userId', '==', user_id)\
                .limit(1)\
                .stream()

            # Get first business
            business_docs = list(businesses)
            if business_docs:
                business_doc = business_docs[0]
                return {
                    'id': business_doc.id,
                    **business_doc.to_dict()
                }

            # No business found, create default
            business_ref = self.db.collection('businesses').document()
            
            business_data = {
                'id': business_ref.id,
                'name': 'Default Business',
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'type': 'small_business',
                'userId': user_id
            }
            
            business_ref.set(business_data)
            logger.info(f"Created default business with owner {user_id}: {business_ref.id}")
            
            return {
                'id': business_ref.id,
                **business_data
            }

        except Exception as e:
            logger.error(f"Error getting/creating business: {str(e)}")
            return None

    def record_ai_action(self, business_id: str, 
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
            action_ref = self.db.collection('businesses').document(business_id)\
                .collection('actions').document()

            timestamp = datetime.now()
            
            base_data = {
                'action_id': action_ref.id,
                'action_type': action_type,
                'status': 'completed',
                'created_at': firestore.SERVER_TIMESTAMP,
                'timestamp': timestamp.isoformat(),
                'business_id': business_id,
                'related_id': related_id
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

    def store_business_folder(self, business_id: str, 
                            folder_data: Dict[str, Any], action_id: str = None) -> str:
        """Store folder metadata under business"""
        try:
            folder_ref = self.db.collection('businesses').document(business_id)\
                .collection('folders').document()

            folder_data.update({
                'folder_id': folder_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id,
                'action_id': action_id
            })

            folder_ref.set(folder_data)
            logger.info(f"Created folder in business {business_id}: {folder_ref.id}")
            return folder_ref.id

        except Exception as e:
            logger.error(f"Error storing folder: {str(e)}")
            raise

    def store_business_spreadsheet(self, business_id: str, 
                                 spreadsheet_data: Dict[str, Any], action_id: str = None) -> str:
        """Store spreadsheet metadata under business"""
        try:
            spreadsheet_ref = self.db.collection('businesses').document(business_id)\
                .collection('spreadsheets').document()

            spreadsheet_data.update({
                'spreadsheet_id': spreadsheet_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'business_id': business_id,
                'action_id': action_id
            })

            spreadsheet_ref.set(spreadsheet_data)
            logger.info(f"Created spreadsheet in business {business_id}: {spreadsheet_ref.id}")
            return spreadsheet_ref.id

        except Exception as e:
            logger.error(f"Error storing spreadsheet: {str(e)}")
            raise

    def record_spreadsheet_update(self, business_id: str, 
                                spreadsheet_id: str, update_data: Dict[str, Any],
                                action_id: str = None) -> str:
        """Record a spreadsheet update action"""
        try:
            update_ref = self.db.collection('businesses').document(business_id)\
                .collection('spreadsheets').document(spreadsheet_id)\
                .collection('updates').document()

            update_data.update({
                'update_id': update_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'business_id': business_id,
                'spreadsheet_id': spreadsheet_id,
                'action_id': action_id
            })

            update_ref.set(update_data)
            logger.info(f"Recorded spreadsheet update: {update_ref.id}")
            return update_ref.id

        except Exception as e:
            logger.error(f"Error recording spreadsheet update: {str(e)}")
            raise 

    def store_folder_metadata(self, business_id: str, folder_data: Dict[str, Any]) -> str:
        """Store folder metadata in Firestore"""
        try:
            folder_ref = self.db.collection('businesses').document(business_id)\
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

    def get_or_create_business_folder(self, business_id: str) -> Dict[str, Any]:
        """Get or create the root business folder in Drive and Firestore"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # First check Firestore for existing folder
                folders = self.db.collection('businesses').document(business_id)\
                    .collection('folders')\
                    .where('type', '==', 'business_root')\
                    .limit(1)\
                    .stream()

                folder_docs = list(folders)
                if folder_docs:
                    folder_data = folder_docs[0].to_dict()
                    folder_id = folder_docs[0].id
                    
                    # Verify folder still exists in Drive
                    try:
                        drive_folder = self.drive_service.get_file(folder_data['drive_folder_id'])
                        return {
                            'id': folder_id,
                            'drive_id': folder_data['drive_folder_id'],
                            'name': drive_folder['name'],
                            'url': drive_folder['webViewLink'],
                            'type': 'business_root'
                        }
                    except Exception as e:
                        logger.warning(f"Drive folder not found, will recreate: {str(e)}")
                        # Don't raise here - continue to create new folder
                
                # Get business details for folder name
                business = self.db.collection('businesses').document(business_id).get()
                if not business.exists:
                    raise ValueError(f"Business {business_id} not found")
                
                business_data = business.to_dict()
                business_name = business_data.get('name', f'Business-{business_id}')
                owner_email = business_data.get('ownerEmail')
                
                if not owner_email:
                    raise ValueError(f"Owner email not found for business {business_id}")

                # Create new "Expense Bot Root" folder first
                try:
                    root_folder = self.drive_service.create_folder(
                        folder_name=Config.GOOGLE_DRIVE_BASE_PATH
                    )
                except ssl.SSLError as e:
                    retry_count += 1
                    logger.warning(f"SSL Error creating root folder (attempt {retry_count}/{max_retries}): {str(e)}")
                    if retry_count == max_retries:
                        raise
                    continue

                # Create business folder inside "Expense Bot Root"
                try:
                    drive_folder = self.drive_service.create_folder(
                        folder_name=business_name,
                        parent_id=root_folder['id']
                    )
                except ssl.SSLError as e:
                    retry_count += 1
                    logger.warning(f"SSL Error creating business folder (attempt {retry_count}/{max_retries}): {str(e)}")
                    if retry_count == max_retries:
                        raise
                    continue
                
                # Record folder creation action
                action_id = self.record_ai_action(
                    business_id=business_id,
                    action_type='folder_created',
                    action_data={
                        'type': 'business_root',
                        'name': drive_folder['name'],
                        'drive_folder_id': drive_folder['id'],
                        'url': drive_folder['url'],
                        'root_folder_id': root_folder['id']
                    },
                    related_id=drive_folder['id']
                )

                # Set permissions for both folders
                service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
                service_account_email = service_account['client_email']
                
                # Set permissions for root folder
                self.drive_service.set_permissions(
                    root_folder['id'],
                    owner_email,
                    service_account_email
                )
                
                # Set permissions for business folder
                self.drive_service.set_permissions(
                    drive_folder['id'],
                    owner_email,
                    service_account_email
                )
                
                # Store in Firestore
                folder_data = {
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id'],
                    'url': drive_folder['url'],
                    'type': 'business_root',
                    'business_id': business_id,
                    'action_id': action_id,
                    'root_folder_id': root_folder['id'],
                    'root_folder_name': 'Expense Bot Root'
                }
                
                folder_id = self.store_folder_metadata(business_id, folder_data)
                
                return {
                    'id': folder_id,
                    'drive_id': drive_folder['id'],
                    'name': drive_folder['name'],
                    'url': drive_folder['url'],
                    'type': 'business_root',
                    'root_folder_id': root_folder['id']
                }
                
            except Exception as e:
                logger.error(f"Error in get_or_create_business_folder: {str(e)}")
                raise

    def get_or_create_transactions_folder(self, business_id: str, 
                                        business_folder_id: str) -> Dict[str, Any]:
        """Get or create Transactions folder within business folder"""
        try:
            # First check Firestore for existing folder
            folders = self.db.collection('businesses').document(business_id)\
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
   
            user_email = self.get_owner_email(business_id)
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
            
            folder_id = self.store_folder_metadata( business_id, folder_data)
            
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

    def get_owner_email(self, business_id: str) -> Optional[str]:
        """Get the owner email for a business"""
        try:
            business = self.db.collection('businesses').document(business_id).get()
            if business.exists:
                return business.to_dict().get('ownerEmail')
            return None
        except Exception as e:
            logger.error(f"Error getting owner email: {str(e)}")
            return None


    def get_or_create_year_folder(self, business_id: str,  transaction_year: str,
                                 transactions_folder_id: str) -> Dict[str, Any]:
        """Get or create year folder within Transactions folder"""
        try:
            
            # First check Firestore for existing folder
            folders = self.db.collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', 'year')\
                .where('year', '==', transaction_year)\
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
                        'year': transaction_year
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create year folder
            drive_folder = self.drive_service.create_folder(
                folder_name=transaction_year,
                parent_id=transactions_folder_id
            )
            
            # Record year folder creation action
            self.record_ai_action(
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': 'year_folder',
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id'],
                    'url': drive_folder['url'],
                    'parent_folder_id': transactions_folder_id,
                    'year': transaction_year
                },
                related_id=drive_folder['id']
            )
            
           
            
            user_email = self.get_owner_email(business_id)
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
                'year': transaction_year,
                'parent_folder_id': transactions_folder_id
            }
            
            folder_id = self.store_folder_metadata( business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
                'type': 'year',
                'year': transaction_year
            }
                
        except Exception as e:
            logger.error(f"Error in get_or_create_year_folder: {str(e)}")
            raise

    def get_or_create_monthly_spreadsheet(self, business_id: str, 
                                        year_folder_id: str, date: datetime) -> Dict[str, Any]:
        """Get or create monthly expense spreadsheet in the year folder."""
        try:
            month_name = date.strftime('%B')
            year = date.strftime('%Y')
            spreadsheet_name = f"{month_name}.xlsx"
            sheet_name = f"{month_name} {year}"
            
            # First check Firestore for existing spreadsheet
            spreadsheets = self.db.collection('businesses').document(business_id)\
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
            
            user_email = self.get_owner_email(business_id)
            service_account = json.loads(Config.SERVICE_ACCOUNT_KEY)
            service_account_email = service_account['client_email']
            
            # Set permissions
            self.drive_service.set_permissions(
                drive_spreadsheet['id'],
                user_email,
                service_account_email
            )
            
            # Create Firestore document
            spreadsheet_ref = self.db.collection('businesses').document(business_id)\
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

    
    def record_expense(self, business_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record an expense transaction"""
        try:
            expense_ref = self.db.collection('businesses').document(business_id)\
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

    
    def update_expense_spreadsheet(self, business_id: str, 
                                 spreadsheet_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update expense spreadsheet with new transaction."""
        try:
            # Get spreadsheet data from Firestore
            spreadsheet = self.db.collection('businesses').document(business_id)\
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
            update_ref = self.db.collection('businesses').document(business_id)\
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

    def store_message(self, business_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a WhatsApp message interaction"""
        try:
            # Create message reference under the business
            message_ref = self.db.collection('businesses').document(business_id)\
                .collection('messages').document()
            
            message_data.update({
                'message_id': message_ref.id,
                'createdAt': firestore.SERVER_TIMESTAMP,
                'status': 'delivered'
            })
            
            # If there's media content, handle storage based on environment
            # if message_data.get('media_content'):
            #     media_path = f"businesses/{business_id}/messages/{message_ref.id}/media"
                
            #     if self.is_emulated:
            #         # Handle storage emulator
            #         try:
            #             # Store media content reference for emulator
            #             media_url = f"{self.storage_host}/{Config.FIREBASE_STORAGE_BUCKET}/{media_path}"
                        
            #             # In development, we might want to just store the content length
            #             # or hash instead of actually uploading
            #             media_data = message_data['media_content']
            #             content_length = len(media_data) if isinstance(media_data, bytes) else len(str(media_data))
                        
            #             message_data.update({
            #                 'media_url': media_url,
            #                 'media_path': media_path,
            #                 'media_size': content_length,
            #                 'media_type': message_data.get('media_type', 'application/octet-stream'),
            #                 'environment': 'development'
            #             })
                        
            #             logger.info(f"Emulator: Stored media reference at {media_url}")
                        
            #         except Exception as e:
            #             logger.warning(f"Emulator: Failed to handle media: {str(e)}")
            #             # Continue without media in development
            #             message_data['media_error'] = str(e)
            #     else:
            #         # Production storage handling
            #         media_blob = self.bucket.blob(media_path)
            #         media_blob.upload_from_string(
            #             message_data['media_content'],
            #             content_type=message_data.get('media_type', 'application/octet-stream')
            #         )
                    
            #         # Generate a signed URL that expires in 7 days
            #         media_url = media_blob.generate_signed_url(
            #             version="v4",
            #             expiration=datetime.timedelta(days=7),
            #             method="GET"
            #         )
                    
            #         message_data.update({
            #             'media_url': media_url,
            #             'media_path': media_path,
            #             'environment': 'production'
            #         })
                
            #     # Remove the raw content from the stored data
            #     del message_data['media_content']
            
            message_ref.set(message_data)
            
            return {
                'id': message_ref.id,
                **message_data
            }
            
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise

    

    def check_duplicate_transaction(self, business_id: str, 
                                  transaction_data: Dict[str, Any]) -> bool:
        """
        Check if a similar transaction already exists based on date, amount, and description.
        Returns True if duplicate found, False otherwise.
        """
        try:
            # Get transactions from the same date with same amount
            transactions = self.db.collection('businesses').document(business_id)\
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
                spreadsheet = self.db.collection('businesses').document(business_id)\
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

    def get_or_create_documents_folder(self, business_id: str, 
                                     document_type: str,
                                     business_folder_id: str) -> Dict[str, Any]:
        """Get or create documents (receipts/invoices) folder"""
        try:
            # Check for existing folder
            folders = self.db.collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', f'{document_type}_root')\
                .limit(1)\
                .stream()
            
            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                folder_id = folder_docs[0].id
                
                # Verify folder still exists in Drive
                try:
                    drive_folder = self.drive_service.get_file(folder_data['drive_folder_id'])
                    return {
                        'id': folder_id,
                        'drive_id': folder_data['drive_folder_id'],
                        'name': drive_folder['name'],
                        'url': drive_folder['webViewLink'],
                        'type': f'{document_type}_root'
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create new folder
            folder_name = f"{document_type.title()}s"  # "Receipts" or "Invoices"
            drive_folder = self.drive_service.create_folder(
                folder_name=folder_name,
                parent_id=business_folder_id
            )
            
            # Record folder creation
            action_id = self.record_ai_action(
                business_id=business_id,
                action_type='folder_created',
                action_data={
                    'type': f'{document_type}_root',
                    'name': drive_folder['name'],
                    'drive_folder_id': drive_folder['id']
                }
            )
            
            # Store metadata
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': f'{document_type}_root',
                'business_id': business_id,
                'action_id': action_id
            }
            
            folder_id = self.store_folder_metadata(business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
                'type': f'{document_type}_root'
            }
            
        except Exception as e:
            logger.error(f"Error in get_or_create_documents_folder: {str(e)}")
            raise

    def get_or_create_document_year_folder(self, business_id: str, 
                                         document_type: str,
                                         year: str,
                                         parent_folder_id: str) -> Dict[str, Any]:
        """Get or create year folder for documents"""
        try:
            # Check for existing folder
            folders = self.db.collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', f'{document_type}_year')\
                .where('year', '==', year)\
                .limit(1)\
                .stream()
            
            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                folder_id = folder_docs[0].id
                
                # Verify folder still exists in Drive
                try:
                    drive_folder = self.drive_service.get_file(folder_data['drive_folder_id'])
                    return {
                        'id': folder_id,
                        'drive_id': folder_data['drive_folder_id'],
                        'name': drive_folder['name'],
                        'url': drive_folder['webViewLink'],
                        'type': f'{document_type}_year'
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create new folder
            folder_name = str(year)
            drive_folder = self.drive_service.create_folder(
                folder_name=folder_name,
                parent_id=parent_folder_id
            )
            
            # Store metadata
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': f'{document_type}_year',
                'year': year,
                'business_id': business_id
            }
            
            folder_id = self.store_folder_metadata(business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
                'type': f'{document_type}_year'
            }
            
        except Exception as e:
            logger.error(f"Error in get_or_create_document_year_folder: {str(e)}")
            raise

    def get_or_create_document_month_folder(self, business_id: str,
                                          document_type: str,
                                          year: str,
                                          month: str,
                                          year_folder_id: str) -> Dict[str, Any]:
        """Get or create month folder for documents"""
        try:
            # Check for existing folder
            folders = self.db.collection('businesses').document(business_id)\
                .collection('folders')\
                .where('type', '==', f'{document_type}_month')\
                .where('year', '==', year)\
                .where('month', '==', month)\
                .limit(1)\
                .stream()
            
            folder_docs = list(folders)
            if folder_docs:
                folder_data = folder_docs[0].to_dict()
                folder_id = folder_docs[0].id
                
                # Verify folder still exists in Drive
                try:
                    drive_folder = self.drive_service.get_file(folder_data['drive_folder_id'])
                    return {
                        'id': folder_id,
                        'drive_id': folder_data['drive_folder_id'],
                        'name': drive_folder['name'],
                        'url': drive_folder['webViewLink'],
                        'type': f'{document_type}_month'
                    }
                except Exception as e:
                    logger.warning(f"Drive folder not found, will recreate: {str(e)}")

            # Create new folder
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            month_num = int(month)
            folder_name = month_names[month_num - 1]
            
            drive_folder = self.drive_service.create_folder(
                folder_name=folder_name,
                parent_id=year_folder_id
            )
            
            # Store metadata
            folder_data = {
                'name': drive_folder['name'],
                'drive_folder_id': drive_folder['id'],
                'url': drive_folder['url'],
                'type': f'{document_type}_month',
                'year': year,
                'month': month,
                'business_id': business_id
            }
            
            folder_id = self.store_folder_metadata(business_id, folder_data)
            
            return {
                'id': folder_id,
                'drive_id': drive_folder['id'],
                'name': drive_folder['name'],
                'url': drive_folder['url'],
                'type': f'{document_type}_month'
            }
            
        except Exception as e:
            logger.error(f"Error in get_or_create_document_month_folder: {str(e)}")
            raise

    def store_document(self, business_id: str,
                      document_type: str,
                      file_content: bytes,
                      mime_type: str,
                      date: str,
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store document in appropriate folder structure"""
        try:
            year = date[:4]
            month = date[5:7]
            business_folder_id = metadata.get('business_folder_id')
            
            if not business_folder_id:
                raise ValueError("business_folder_id is required in metadata")
            
            # Get or create folder structure
            documents_folder = self.get_or_create_documents_folder(
                business_id=business_id,
                document_type=document_type,
                business_folder_id=business_folder_id
            )
            
            year_folder = self.get_or_create_document_year_folder(
                business_id=business_id,
                document_type=document_type,
                year=year,
                parent_folder_id=documents_folder['drive_id']
            )
            
            month_folder = self.get_or_create_document_month_folder(
                business_id=business_id,
                document_type=document_type,
                year=year,
                month=month,
                year_folder_id=year_folder['drive_id']
            )
            
            # Upload file
            file_name = f"{date}_{metadata.get('merchant', 'unknown')}_{document_type}"
            file_extension = mimetypes.guess_extension(mime_type) or '.pdf'
            
            drive_file = self.drive_service.upload_file(
                file_content=file_content,
                file_name=f"{file_name}{file_extension}",
                mime_type=mime_type,
                parent_folder_id=month_folder['drive_id']
            )
            
            return drive_file
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise