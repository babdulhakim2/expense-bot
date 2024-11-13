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

load_dotenv()  # take environment variables from .env.

weave.init(project_name="expense-bot")

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

# Authenticate with Google APIs
creds = ServiceAccountCredentials.from_json_keyfile_name(Config.GOOGLE_SERVICE_ACCOUNT_KEY, scope)
sheets_client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

# Add these after the existing imports
def init_database():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            folder_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_or_create_user_folder(phone_number):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute('SELECT folder_id FROM users WHERE phone_number = ?', (phone_number,))
        result = c.fetchone()
        
        if result:
            folder_id = result[0]
            logger.info(f"Found existing folder for {phone_number}: {folder_id}")
            
            # Check and share folder if not already shared
            email = os.environ.get('MY_EMAIL')
            permissions = drive_service.permissions().list(
                fileId=folder_id,
                fields="permissions(emailAddress)"
            ).execute().get('permissions', [])
            
            if not any(p.get('emailAddress') == email for p in permissions):
                logger.info(f"Sharing folder with {email}")
                permission = {
                    'type': 'user',
                    'role': 'writer',
                    'emailAddress': email
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
        email = os.environ.get('MY_EMAIL')
        logger.info(f"Sharing new folder with {email}")
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        drive_service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=False
        ).execute()
        
        # Store user info
        c.execute('''
            INSERT INTO users (phone_number, folder_id) 
            VALUES (?, ?)
        ''', (phone_number, folder_id))
        conn.commit()
        
        logger.info(f"Created new folder for {phone_number}: {folder_id}")
        return folder_id
        
    except Exception as e:
        logger.error(f"Error managing user folder: {str(e)}")
        raise e
    finally:
        conn.close()

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
        
        # Remove chat sessions since we're using stateless requests
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


if __name__ == '__main__':
    init_database()  # Initialize SQLite database
    app.run(host='0.0.0.0', port=9004, debug=True)
