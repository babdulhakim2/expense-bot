import os
from flask import Flask, request, jsonify
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
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from services.plaid_service import PlaidService
from flask_cors import CORS

load_dotenv()  # take environment variables from .env.


# Set up logging configuration at the top of the file after imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# CORS(app, resources={
#     r"/api/*": {
#         "origins": ["http://localhost:3000"],
#         "methods": ["POST", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Accept"]
#     }
# })

# Initialize services with config
gemma2_service = Gemma2Service()  # Primary service
gemini_service = GeminiService()  # Fallback service
plaid_service = PlaidService()

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
        
        # Store incoming message immediately
        incoming_message = {
            'direction': 'inbound',
            'phone_number': phone_number,
            'content': incoming_msg,
            'type': 'text' if num_media == 0 else 'media',
            'platform': 'whatsapp',
            'timestamp': datetime.now().isoformat()
        }
        
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
        # TODO Use AI to get business context
        if not business:
            msg.body("Sorry, there was an error accessing your business account. Please try again later.")
            return str(resp)

        # Store the incoming message with user context
        stored_message = firebase_service.store_message(
            user_id=user['id'],
            business_id=business['id'],
            message_data={
                **incoming_message,
                'user_id': user['id'],
                'business_id': business['id']
            }
        )

        # Record message received action
        firebase_service.record_ai_action(
            user_id=user['id'],
            business_id=business['id'],
            action_type='message_received',
            action_data=incoming_message
        )

        if num_media > 0:
            # Process media message
            try:
                media_url = request.values.get('MediaUrl0')
                media_type = request.values.get('MediaContentType0')
                
                logger.info(f"Processing media: {media_type} from {media_url}")
                
                # Download media content
                media_response = requests.get(media_url)
                if media_response.status_code == 200:
                    # Store media content in Firebase Storage
                    firebase_service.store_message(
                        user_id=user['id'],
                        business_id=business['id'],
                        message_data={
                            **stored_message,
                            'media_content': media_response.content,
                            'media_type': media_type
                        }
                    )

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
                logger.info(f"Transaction data: {transaction}")
        if not is_transaction:
            msg.body(response)
            # Store AI response
            firebase_service.store_message(
                user_id=user['id'],
                business_id=business['id'],
                message_data={
                    'direction': 'outbound',
                    'content': response,
                    'type': 'ai_response',
                    'related_message_id': stored_message['id'],
                    'timestamp': datetime.now().isoformat()
                }
            )
            return str(resp)

        # Get transaction date
        transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d')

        # Get or create folder structure
        business_folder = firebase_service.get_or_create_business_folder(
            user_id=user['id'],
            business_id=business['id']
        )

        transactions_folder = firebase_service.get_or_create_transactions_folder(
            user_id=user['id'],
            business_id=business['id'],
            business_folder_id=business_folder['drive_id']
        )

        year_folder = firebase_service.get_or_create_year_folder(
            user_id=user['id'],
            business_id=business['id'],
            transactions_folder_id=transactions_folder['drive_id']
        )

        # Get or create monthly spreadsheet
        spreadsheet = firebase_service.get_or_create_monthly_spreadsheet(
            user_id=user['id'],
            business_id=business['id'],
            year_folder_id=year_folder['drive_id'],
            date=transaction_date
        )

        # NOW check for duplicates after we have the spreadsheet
        if firebase_service.check_duplicate_transaction(
            user_id=user['id'],
            business_id=business['id'],
            transaction_data={
                'date': transaction['transaction_date'],
                'amount': transaction['amount'],
                'description': transaction['description'],
                'spreadsheet_id': spreadsheet['spreadsheet_id']
            }
        ):
            msg.body("⚠️ This transaction appears to be a duplicate. If this is a different transaction, please add more details to the description.")
            return str(resp)

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
                'spreadsheet_id': spreadsheet['spreadsheet_id']
            }
        )

        # Update the spreadsheet with the new expense
        firebase_service.update_expense_spreadsheet(
            user_id=user['id'],
            business_id=business['id'],
            spreadsheet_id=spreadsheet['spreadsheet_id'],
            expense_data={
                'date': transaction['transaction_date'],
                'description': transaction['description'],
                'amount': transaction['amount'],
                'category': transaction['category'],
                'payment_method': transaction['payment_method'],
                'status': 'Completed',
                'transaction_id': expense['id'],
                'merchant': transaction.get('merchant', 'N/A'),
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
            f"🏷️ {transaction.get('merchant', 'N/A')}\n\n"
            f"📊 View your expenses at:\n"
            f"https://expensebot.xyz/dashboard\n\n"
        )

        # Add folder URLs
        response_text += (
            f"📂 Business folder:\n{business_folder['url']}\n\n"
            f"📂 Transactions folder:\n{transactions_folder['url']}\n\n"
            f"📂 Year folder:\n{year_folder['url']}\n\n"
        )

        # Add spreadsheet URL - use the direct URL from spreadsheet data
        if spreadsheet.get('url'):  # Changed from spreadsheet.get('spreadsheet', {}).get('url')
            response_text += (
                f"📊 View spreadsheet at:\n"
                f"{spreadsheet['url']}\n\n"
            )

        # Store the final response message
        firebase_service.store_message(
            user_id=user['id'],
            business_id=business['id'],
            message_data={
                'direction': 'outbound',
                'content': response_text,
                'type': 'transaction_confirmation',
                'related_message_id': stored_message['id'],
                'transaction_data': transaction,
                'expense_id': expense['id'],
                'business_folder_id': business_folder['id'],
                'transactions_folder_id': transactions_folder['id'],
                'year_folder_id': year_folder['id'],
                'spreadsheet_id': spreadsheet.get('spreadsheet', {}).get('id'),
                'timestamp': datetime.now().isoformat()
            }
        )

        # Record message sent action
        firebase_service.record_ai_action(
            user_id=user['id'],
            business_id=business['id'],
            action_type='message_sent',
            action_data={
                'content': response_text,
                'type': 'transaction_confirmation',
                'transaction_id': expense['id'],
                'platform': 'whatsapp'
            },
            related_id=expense['id']
        )

        msg.body(response_text)
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        error_msg = "Sorry, something went wrong. Please try again."
        
        # Store error message if we have user context
        if 'user' in locals() and 'business' in locals():
            firebase_service.store_message(
                user_id=user['id'],
                business_id=business['id'],
                message_data={
                    'direction': 'outbound',
                    'content': error_msg,
                    'type': 'error',
                    'error_details': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        msg = MessagingResponse().message()
        msg.body(error_msg)
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

@app.route('/api/banking/plaid/create_link_token', methods=['POST', 'OPTIONS'])
def create_link_token():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        logger.info("Received create_link_token request")
        logger.info(f"Headers: {dict(request.headers)}")
        
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_id = data.get('user_id')
        if not user_id:
            logger.error("User ID is required")
            return jsonify({"error": "User ID is required"}), 400
            
        logger.info(f"Creating link token for user {user_id}")
        token_data = plaid_service.create_link_token(user_id)
        logger.info(f"Created link token: {token_data}")
        
        return jsonify(token_data)
        
    except Exception as e:
        logger.error(f"Error creating link token: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/banking/plaid/exchange_token', methods=['POST', 'OPTIONS'])
def exchange_token():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        logger.info("Received exchange_token request")
        logger.info(f"Headers: {dict(request.headers)}")
        
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        public_token = data.get('public_token')
        user_id = data.get('user_id')
        business_id = data.get('business_id')
        
        if not all([public_token, user_id, business_id]):
            return jsonify({"error": "Missing required parameters"}), 400
            
        try:
            # Exchange public token for access token
            plaid_data = plaid_service.exchange_public_token(public_token)
            logger.info("Exchanged public token for access token")
            
            # Get accounts
            accounts = plaid_service.get_accounts(plaid_data['access_token'])
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            # Store in Firebase
            connection_id = firebase_service.store_bank_connection(
                user_id=user_id,
                business_id=business_id,
                plaid_data={
                    'access_token': plaid_data['access_token'],
                    'item_id': plaid_data['item_id']
                },
                accounts=accounts
            )
            
            logger.info(f"Stored bank connection with ID: {connection_id}")
            
            # Return connection details
            return jsonify({
                "connection_id": connection_id,
                "bank_name": accounts[0].get('name', 'Connected Bank'),
                "account_count": len(accounts),
                "status": "success",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
        except plaid.ApiException as e:
            logger.error(f"Plaid API error: {str(e)}")
            return jsonify({"error": str(e)}), 400
            
    except Exception as e:
        logger.error(f"Error exchanging token: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/banking/plaid/sync', methods=['POST'])
async def sync_transactions():
    try:
        data = await request.get_json()
        connection_id = data.get('connection_id')
        
        if not connection_id:
            return jsonify({"error": "Connection ID is required"}), 400
            
        # Get connection details from Firebase
        connection = await firebase_service.get_bank_connection(connection_id)
        if not connection:
            return jsonify({"error": "Connection not found"}), 404
            
        # Get transactions from Plaid
        start_date = datetime.now() - timedelta(days=30)  # Last 30 days
        transactions = await plaid_service.get_transactions(
            connection['access_token'],
            start_date
        )
        
        # Store transactions in Firebase
        await firebase_service.store_transactions(
            user_id=connection['user_id'],
            business_id=connection['business_id'],
            transactions=transactions
        )
        
        return jsonify({
            "status": "success",
            "transaction_count": len(transactions),
            "sync_time": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing transactions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9004))
    app.run(host='0.0.0.0', port=port, debug=True)