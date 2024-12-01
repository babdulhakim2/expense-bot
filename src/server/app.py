import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv
import weave
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import logging
import sqlite3
from datetime import datetime, timezone
from googleapiclient.discovery import build
from services.gemini_service import GeminiService
from config import Config
from google.cloud import secretmanager
import wandb
from googleapiclient.errors import HttpError
import firebase_admin
from firebase_admin import credentials, firestore
import json

load_dotenv()  # take environment variables from .env.

# Initialize wandb with API key before using weave
# wandb.login(key=os.getenv('WANDB_API_KEY'))

# # Then initialize weave
# weave.init(project_name="expense-bot")

# Set up logging configuration at the top of the file after imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize services with config
gemini_service = GeminiService()  # No need to pass API key, it uses config

# Dictionary to maintain chat history per user
chat_sessions = {}

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

# Initialize Firebase Admin SDK
firebase_creds = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_KEY)
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)

db = firestore.client()

# Add these after the existing imports
def get_or_create_user_folder(phone_number):
    try:
        user_ref = db.collection('users').document(phone_number)
        user = user_ref.get()
        
        if user.exists:
            folder_id = user.to_dict().get('folder_id')
            user_email = user.to_dict().get('email')
            logger.info(f"Found existing folder for {phone_number}: {folder_id}")
            
            try:
                permissions = drive_service.permissions().list(
                    fileId=folder_id,
                    fields="permissions(emailAddress)"
                ).execute().get('permissions', [])
            except HttpError as e:
                if e.resp.status == 404:
                    logger.warning(f"Folder {folder_id} not found. Recreating folder.")
                    
                    # Recreate folder in Google Drive
                    folder_metadata = {
                        'name': f'Expenses_{phone_number}',
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = drive_service.files().create(
                        body=folder_metadata,
                        fields='id'
                    ).execute()
                    folder_id = folder.get('id')
                    
                    # Share the new folder
                    permission = {
                        'type': 'user',
                        'role': 'writer',
                        'emailAddress': user_email
                    }
                    drive_service.permissions().create(
                        fileId=folder_id,
                        body=permission,
                        sendNotificationEmail=False
                    ).execute()
                    
                    # Update Firestore with new folder_id
                    user_ref.update({
                        'folder_id': folder_id
                    })
                    
                    logger.info(f"Recreated and shared folder for {phone_number}: {folder_id}")
                    return folder_id
                else:
                    logger.error(f"Failed to list permissions for folder {folder_id}: {str(e)}")
                    raise e
            
            if not any(p.get('emailAddress') == user_email for p in permissions):
                logger.info(f"Sharing folder with {user_email}")
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': user_email
                }
                drive_service.permissions().create(
                    fileId=folder_id,
                    body=permission,
                    sendNotificationEmail=False
                ).execute()
            
            return folder_id
        
        # Create new folder in Google Drive
        folder_metadata = {
            'name': f'Expenses_{phone_number}',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        folder_id = folder.get('id')
        
        # Share the new folder
        user_email = user.to_dict().get('email') if user.exists else os.environ.get('DEFAULT_USER_EMAIL')
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': user_email
        }
        drive_service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=False
        ).execute()
        
        # Store user info in Firestore
        user_ref.set({
            'folder_id': folder_id,
            'created_at': firestore.SERVER_TIMESTAMP,
            'email': user_email
        })
        
        logger.info(f"Created and shared new folder for {phone_number}: {folder_id}")
        return folder_id

    except HttpError as e:
        logger.error(f"Failed to manage folder due to API error: {str(e)}")
        raise e
    
    except Exception as e:
        logger.error(f"Failed to manage user folder: {str(e)}")
        raise e

def get_or_create_spreadsheet(phone_number):
    try:
        folder_id = get_or_create_user_folder(phone_number)
        try:
            spreadsheet = sheets_client.open(f'Expenses_{phone_number}')
        except gspread.SpreadsheetNotFound:
            spreadsheet = sheets_client.create(f'Expenses_{phone_number}')
            # Move to user's folder
            file_id = spreadsheet.id
            # Get the file's current parents
            file = drive_service.files().get(
                fileId=file_id,
                fields='parents'
            ).execute()
            previous_parents = ",".join(file.get('parents', []))
            # Move the file to the new folder
            drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
        
        # Share with user's email
        email = "abdulhakim.gafai@gmail.com"
        permissions = spreadsheet.list_permissions()
        if not any(p.get('emailAddress') == email for p in permissions):
            spreadsheet.share(email, perm_type='user', role='writer', notify=False)
        
        return spreadsheet
    except Exception as e:
        logger.error(f"Error in get_or_create_spreadsheet: {str(e)}")
        raise e

def get_or_create_worksheet(spreadsheet, worksheet_name):
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="20")
        # Initialize headers with new columns
        headers = [
            'Transaction started (UTC)',
            'Transaction completed (UTC)',
            'Transaction ID',
            'Transaction status',
            'Transaction type',
            'Transaction description',
            'Payer',
            'Card number',
            'Expense split #',
            'Orig currency',
            'Orig amount (Orig currency)'
        ]
        worksheet.append_row(headers)
    return worksheet

def update_expense_sheet(date, amount, item, phone_number):
    try:
        spreadsheet = get_or_create_spreadsheet(phone_number)
        worksheet_name = date.strftime('%B %Y')
        worksheet = get_or_create_worksheet(spreadsheet, worksheet_name)
        
        # Generate transaction ID
        transaction_id = f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Prepare row data with all fields
        row_data = [
            datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),  # Transaction started
            datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),  # Transaction completed
            transaction_id,                                            # Transaction ID
            'Completed',                                              # Transaction status
            'Expense',                                                # Transaction type
            item,                                                     # Transaction description
            'N/A',                                                    # Payer
            'N/A',                                                    # Card number
            '1',                                                      # Expense split
            'USD',                                                    # Original currency
            amount                                                    # Original amount
        ]
        
        worksheet.append_row(row_data)
        
        # Get spreadsheet URL
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        logger.info(f"Expense added to spreadsheet: {spreadsheet_url}")
        
        return spreadsheet_url, transaction_id
        
    except Exception as e:
        logger.error(f"Error updating expense sheet: {str(e)}")
        raise e

def parse_expense_text(text):
    # For simplicity, let's assume the text contains date, amount, and item in a known format
    # You can adjust the parsing logic as needed

    # Mock parsing for demonstration purposes
    # Example text: "Expense: Lunch; Amount: 15.50; Date: 2024-11-08"
    date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', text)
    amount_match = re.search(r'Amount:\s*(\d+(\.\d{2})?)', text)
    item_match = re.search(r'Expense:\s*(.+?);', text)

    if date_match and amount_match and item_match:
        date_str = date_match.group(1)
        amount_str = amount_match.group(1)
        item = item_match.group(1)
    else:
        # If parsing fails, return some default values or raise an error
        date_str = datetime.now().strftime('%Y-%m-%d')
        amount_str = '0.00'
        item = 'Unknown Expense'

    return datetime.strptime(date_str, '%Y-%m-%d'), float(amount_str), item

def get_folder_url(phone_number):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('SELECT folder_id FROM users WHERE phone_number = ?', (phone_number,))
        result = c.fetchone()
        
        if result:
            folder_id = result[0]
            folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
            return folder_url
        return None
    except Exception as e:
        logger.error(f"Error getting folder URL: {str(e)}")
        return None
    finally:
        conn.close()

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    try:
        user_id = request.values.get('From')
        incoming_msg = request.values.get('Body', '').strip()
        num_media = int(request.values.get('NumMedia', 0))
        
        # Extract phone number
        phone_number = user_id.replace('whatsapp:', '')
        logger.info(f"Received message from {phone_number}: {incoming_msg}")
        
        resp = MessagingResponse()
        msg = resp.message()

        if num_media > 0:
            # Process media message
            media_url = request.values.get('MediaUrl0')
            media_type = request.values.get('MediaContentType0')
            
            logger.info(f"Processing media: {media_type} from {media_url}")
            
            # Download media content
            media_response = requests.get(media_url)
            if media_response.status_code != 200:
                logger.error(f"Failed to download media: {media_response.status_code}")
                msg.body("Sorry, I couldn't download the file. Please try again.")
                return str(resp)
                
            # Process the media
            is_transaction, transaction, response = gemini_service.process_media(
                media_response.content,
                media_type,
                incoming_msg
            )
            
        else:
            # Process text message
            is_transaction, transaction, response = gemini_service.extract_transaction(incoming_msg)
        
        if not is_transaction:
            msg.body(response)
            return str(resp)
            
        # Retrieve user email from Firestore
        user_doc = db.collection('users').document(phone_number).get()
        if user_doc.exists:
            user_email = user_doc.to_dict().get('email')
        else:
            user_email = os.environ.get('DEFAULT_USER_EMAIL')  # Fallback email
        
        # Update spreadsheet with transaction
        spreadsheet_url, transaction_id = update_expense_sheet(
            datetime.strptime(transaction['transaction_date'], '%Y-%m-%d'),
            transaction['amount'],
            transaction['description'],
            phone_number
        )
        
        folder_url = get_folder_url(phone_number)
        
        # Format success response with currency information
        response_text = (
            f"✅ Transaction recorded!\n\n"
            f"🆔 {transaction_id}\n"
            f"📝 {transaction['description']}\n"
        )

        # Add currency information
        if transaction['orig_currency'] != 'GBP':
            response_text += (
                f"💰 Original: {transaction['orig_currency']} {transaction['orig_amount']:.2f}\n"
                f"💱 GBP Amount: £{transaction['amount']:.2f}\n"
                f"📈 Rate: {transaction['exchange_rate']:.4f}\n"
            )
        else:
            response_text += f"💰 Amount: £{transaction['amount']:.2f}\n"

        response_text += (
            f"📅 {transaction['transaction_date']}\n"
            f"🏷️ {transaction['category']}\n"
            f"💳 {transaction['payment_method']}\n"
            f"🏪 {transaction.get('merchant', 'N/A')}\n\n"
            f"📊 View spreadsheet: {spreadsheet_url}\n"
            f"📁 View folder: {folder_url}"
        )
        
        msg.body(response_text)
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        msg = MessagingResponse().message()
        msg.body("Sorry, something went wrong. Please try again.")
        return str(msg)

wandb_enabled = False  # Global flag

def init_wandb():
    global wandb_enabled
    try:
        wandb_key = Config.WANDB_API_KEY
       

        if not wandb_key:
            logger.warning("WANDB_API_KEY not found, W&B features will be disabled")
            return False
        
        # Clean the API key
        wandb_key = wandb_key.strip().strip('"\'').strip()
        
        if len(wandb_key) != 40:
            logger.error(f"Invalid API key length: {len(wandb_key)}. Expected 40 characters.")
            return False
        
        wandb.login(key=wandb_key)
        weave.init(project_name="expense-bot")
        os.environ["WANDB_CONFIG_DIR"] = "/tmp"
        # wandb_enabled = True
        logger.info("Successfully initialized Weights & Biases")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Weights & Biases: {str(e)}")
        return False

# Call this during app startup
init_wandb()

def access_secret_version(project_id, secret_id):
    """
    Access the secret version.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        raise

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=9004, debug=True)
    port = int(os.environ.get('PORT', 9004))
    app.run(host='0.0.0.0', port=port)