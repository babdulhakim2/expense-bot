import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
from dotenv import load_dotenv
import weave
import datetime
import logging
from datetime import datetime
from services.gemma2_service import Gemma2Service
from services.gemini_service import GeminiService
from config import Config
from google.cloud import secretmanager
import wandb
from services.firebase_service import FirebaseService

load_dotenv()  # take environment variables from .env.


# Set up logging configuration at the top of the file after imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize services with config
gemma2_service = Gemma2Service()  # Primary service
gemini_service = GeminiService()  # Fallback service

# Dictionary to maintain chat history per user
chat_sessions = {}



# Initialize Firebase service
firebase_service = FirebaseService()

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

        # Check if user exists
        print(f"Checking if user exists: {phone_number}")
        user = firebase_service.get_user_by_phone(phone_number)
        if not user:
            registration_url = firebase_service.get_user_registration_url()
            msg.body(
                "👋 Welcome to ExpenseBot!\n\n"
                "It looks like you haven't registered yet. "
                f"Please create an account at:\n{registration_url}\n\n"
                "Once registered, you can start tracking your expenses!"
            )
            return str(resp)

        # Get or create active business for user
        business = firebase_service.get_active_business(user['id'])
        if not business:
            msg.body("Sorry, there was an error accessing your business account. Please try again later.")
            return str(resp)

        if num_media > 0:
            # Process media message
            try:
                media_url = request.values.get('MediaUrl0')
                media_type = request.values.get('MediaContentType0')
                
                logger.info(f"Processing media: {media_type} from {media_url}")
                
                # Download media content
                media_response = requests.get(media_url)
                if media_response.status_code != 200:
                    logger.error(f"Failed to download media: {media_response.status_code}")
                    msg.body("Sorry, I couldn't download the file. Please try again.")
                    return str(resp)
                    
                # Try Gemma first
                try:
                    is_transaction, transaction, response = gemma2_service.process_media(
                        media_response.content,
                        media_type,
                        incoming_msg
                    )
                except Exception as e:
                    logger.error(f"Gemma media processing failed: {str(e)}")
                    is_transaction = False
                    response = str(e)
                
                # Fall back to Gemini if Gemma fails
                if not is_transaction:
                    logger.info("Gemma processing failed, falling back to Gemini")
                    is_transaction, transaction, response = gemini_service.process_media(
                        media_response.content,
                        media_type,
                        incoming_msg
                    )
                    
            except Exception as e:
                logger.error(f"Error processing media: {str(e)}", exc_info=True)
                msg.body("Sorry, I had trouble processing your image. Please try again.")
                return str(resp)
        
        else:
            # Try Gemma first for text processing
            try:
                is_transaction, transaction, response = gemma2_service.extract_transaction(incoming_msg)
            except Exception as e:
                logger.error(f"Gemma text processing failed: {str(e)}")
                is_transaction = False
            
            # Fall back to Gemini if Gemma fails
            if not is_transaction:
                logger.info("Gemma text processing failed, falling back to Gemini")
                is_transaction, transaction, response = gemini_service.extract_transaction(incoming_msg)
        
        if not is_transaction:
            msg.body(response)
            return str(resp)

        # Get or create monthly folder
        transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d')
        monthly_folder = firebase_service.get_or_create_monthly_folder(
            user_id=user['id'],
            business_id=business['id'],
            date=transaction_date
        )

        # Record the expense
        expense = firebase_service.record_expense(
            user_id=user['id'],
            business_id=business['id'],
            expense_data={
                'date': transaction['transaction_date'],
                'amount': transaction['amount'],
                'description': transaction['description'],
                'category': transaction['category'],
                'payment_method': transaction['payment_method'],
                'merchant': transaction.get('merchant', 'N/A'),
                'orig_currency': transaction.get('orig_currency', 'GBP'),
                'orig_amount': transaction.get('orig_amount', transaction['amount']),
                'exchange_rate': transaction.get('exchange_rate', 1.0),
                'folder_id': monthly_folder['id']
            }
        )

        # Update the spreadsheet with the new expense
        if monthly_folder.get('spreadsheet'):
            firebase_service.update_expense_spreadsheet(
                user_id=user['id'],
                business_id=business['id'],
                spreadsheet_id=monthly_folder['spreadsheet']['id'],
                expense_data={
                    'date': transaction['transaction_date'],
                    'description': transaction['description'],
                    'amount': transaction['amount'],
                    'category': transaction['category'],
                    'payment_method': transaction['payment_method'],
                    'status': 'Completed',
                    'action_id': expense['action_id'],
                    'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )

        # Format success response
        response_text = (
            f"✅ Transaction recorded!\n\n"
            f"🆔 {expense['id']}\n"
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
            f"📊 View your expenses at:\n"
            f"https://expensebot.xyz/dashboard"
        )
        
        if monthly_folder.get('folder_url'):
            response_text += (
                f"📂 View folder at:\n"
                f"{monthly_folder['folder_url']}\n\n"
            )
        
        if monthly_folder.get('spreadsheet', {}).get('url'):
            response_text += (
                f"📊 View spreadsheet at:\n"
                f"{monthly_folder['spreadsheet']['url']}\n\n"
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