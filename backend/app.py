import os
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests
from dotenv import load_dotenv
import weave
import datetime
import logging
from datetime import datetime
from services.ai_service import AIService
from config import Config
from google.cloud import secretmanager
import wandb
from services.firebase_service import FirebaseService
from twilio.rest import Client



# Set up logging configuration at the top of the file after imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Import and register blueprints
from routes.tasks import tasks_bp
app.register_blueprint(tasks_bp)

# Initialize services with config
gemini_service = AIService()  # Primary service now

# Dictionary to maintain chat history per user
chat_sessions = {}



# Initialize Firebase service
firebase_service = FirebaseService()

# Initialize Twilio client
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify if the server is running.
    """
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()}), 200






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
            registration_url = 'https://expensebot.xyz'
            msg.body(
                "👋 Welcome to ExpenseBot!\n\n"
                "It looks like you haven't registered yet. "
                f"Please create an account and register your Phone Number at:\n{registration_url}\n\n"
                "Once registered, you can start tracking your expenses using Whatsapp!"
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
            business_id=business['id'],
            message_data={
                **incoming_message,
                'user_id': user['id'],
                'business_id': business['id']
            }
        )

        # Record message received action
        firebase_service.record_ai_action(
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
                        business_id=business['id'],
                        message_data={
                            **stored_message,
                            'media_content': media_response.content,
                            'media_type': media_type
                        }
                    )

                # Use only Gemini for processing
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
            # Use only Gemini for text processing
            is_transaction, transaction, response = gemini_service.extract_transaction(incoming_msg)
            logger.info(f"Transaction data: {transaction}")
        if not is_transaction:
            msg.body(response)
            # Store AI response
            firebase_service.store_message(
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
        transaction_year = transaction_date.strftime('%Y')

        # Get or create folder structure
        business_folder = firebase_service.get_or_create_business_folder(
            business_id=business['id']
        )

        transactions_folder = firebase_service.get_or_create_transactions_folder(
            business_id=business['id'],
            business_folder_id=business_folder['drive_id']
        )

        year_folder = firebase_service.get_or_create_year_folder(
            business_id=business['id'],
            transaction_year=transaction_year,
            transactions_folder_id=transactions_folder['drive_id']
        )

        # Get or create monthly spreadsheet
        spreadsheet = firebase_service.get_or_create_monthly_spreadsheet(
            business_id=business['id'],
            year_folder_id=year_folder['drive_id'],
            date=transaction_date
        )

        # NOW check for duplicates after we have the spreadsheet
        if firebase_service.check_duplicate_transaction(
            business_id=business['id'],
            transaction_data={
                'date': transaction['transaction_date'],
                'amount': transaction['amount'],
                'description': transaction['description'],
                'spreadsheet_id': spreadsheet['spreadsheet_id']
            }
        ):
            duplicate_msg = "⚠️ This transaction appears to be a duplicate. If this is a different transaction, please add more details to the description."
            
            # Send message directly via Twilio instead of using MessagingResponse
            twilio_client.messages.create(
                from_=f'whatsapp:{Config.TWILIO_PHONE_NUMBER}',
                body=duplicate_msg,
                to=user_id  # user_id already contains the whatsapp: prefix
            )
            
            # Store the duplicate warning message
            firebase_service.store_message(
                business_id=business['id'],
                message_data={
                    'direction': 'outbound',
                    'content': duplicate_msg,
                    'type': 'duplicate_warning',
                    'related_message_id': stored_message['id'],
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Record the duplicate detection action
            firebase_service.record_ai_action(
                business_id=business['id'],
                action_type='transaction_duplicate',
                action_data={
                    'original_message': incoming_msg,
                    'duplicate_details': {
                        'date': transaction['transaction_date'],
                        'amount': transaction['amount'],
                        'description': transaction['description']
                    }
                }
            )
            
            return str(MessagingResponse())  # Return empty response since we sent message directly

        # Record the expense
        expense = firebase_service.record_expense(
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

        # Store the document if we have media
        if num_media > 0:
            try:
                logger.info("Starting document storage process...")
                
                # Get business folder first
                business_folder = firebase_service.get_or_create_business_folder(
                    business_id=business['id']
                )
                logger.debug(f"Got business folder: {business_folder['id']}")
                
                # Detect document type
                logger.debug(f"Detecting document type for media type: {media_type}")
                document_type, document_date = gemini_service._detect_document_type(
                    media_response.content,
                    media_type
                )
                logger.info(f"Detected document type: {document_type}, date: {document_date}")

                # Store document with metadata
                logger.debug("Preparing to store document...")
                stored_document = firebase_service.store_document(
                    business_id=business['id'],
                    document_type=document_type,
                    file_content=media_response.content,
                    mime_type=media_type,
                    date=document_date,
                    metadata={
                        'expense_id': expense['id'],
                        'transaction_date': transaction['transaction_date'],
                        'amount': transaction['amount'],
                        'description': transaction['description'],
                        'category': transaction['category'],
                        'merchant': transaction.get('merchant', 'N/A'),
                        'business_folder_id': business_folder['drive_id']
                    }
                )
                logger.info(f"Document stored successfully: {stored_document['url']}")

                # Add document info to response
                response_text += f"\n\n📄 Document stored as {document_type}\n"
                response_text += f"📂 View at: {stored_document['url']}"

                # Record document storage action
                logger.debug("Recording document storage action...")
                firebase_service.record_ai_action(
                    business_id=business['id'],
                    action_type='document_stored',
                    action_data={
                        'document_type': document_type,
                        'document_url': stored_document['url'],
                        'expense_id': expense['id'],
                        'mime_type': media_type
                    },
                    related_id=expense['id']
                )
                logger.info("Document storage process completed successfully")

            except Exception as e:
                logger.error(f"Error storing document: {str(e)}", exc_info=True)
                # Log the full traceback for debugging
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                response_text += "\n\n⚠️ Transaction recorded but couldn't store the document."

        # Continue with existing code for sending response
        twilio_client.messages.create(
            from_=f'whatsapp:{Config.TWILIO_PHONE_NUMBER}',
            body=response_text,
            to=user_id
        )

        # Return empty response since we sent message directly
        return str(MessagingResponse())
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        error_msg = "Sorry, something went wrong. Please try again."
        
        # Store error message if we have user context
        if 'user' in locals() and 'business' in locals():
            firebase_service.store_message(
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

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get business_id from request
        business_id = request.form.get('businessId')
        if not business_id:
            return jsonify({'error': 'Business ID is required'}), 400

        # Get the file content and MIME type
        file_content = file.read()
        mime_type = file.content_type

        # Get business folder
        business_folder = firebase_service.get_or_create_business_folder(
            business_id=business_id
        )
        logger.debug(f"Got business folder: {business_folder['id']}")

        # Use Gemini to detect document type and extract transaction data
        is_transaction, transaction, ai_response = gemini_service.process_media(
            file_content,
            mime_type,
            ""  # No additional message for uploaded files
        )

        # Detect document type
        document_type, document_date = gemini_service._detect_document_type(
            file_content,
            mime_type
        )
        logger.info(f"Detected document type: {document_type}, date: {document_date}")

        # If it's a valid transaction, process it
        if is_transaction:
            # Get transaction date
            transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d')
            transaction_year = transaction_date.strftime('%Y')

            # Create folder structure
            transactions_folder = firebase_service.get_or_create_transactions_folder(
                business_id=business_id,
                business_folder_id=business_folder['drive_id']
            )

            year_folder = firebase_service.get_or_create_year_folder(
                business_id=business_id,
                transaction_year=transaction_year,
                transactions_folder_id=transactions_folder['drive_id']
            )

            # Get or create monthly spreadsheet
            spreadsheet = firebase_service.get_or_create_monthly_spreadsheet(
                business_id=business_id,
                year_folder_id=year_folder['drive_id'],
                date=transaction_date
            )

            # Record the expense
            expense = firebase_service.record_expense(
                business_id=business_id,
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

            # Update spreadsheet
            firebase_service.update_expense_spreadsheet(
                business_id=business_id,
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

        # Store the document
        stored_document = firebase_service.store_document(
            business_id=business_id,
            document_type=document_type,
            file_content=file_content,
            mime_type=mime_type,
            date=document_date,
            metadata={
                'expense_id': expense['id'] if is_transaction else None,
                'transaction_date': transaction['transaction_date'] if is_transaction else document_date,
                'amount': transaction.get('amount') if is_transaction else None,
                'description': transaction.get('description') if is_transaction else None,
                'category': transaction.get('category') if is_transaction else None,
                'merchant': transaction.get('merchant', 'N/A') if is_transaction else None,
                'business_folder_id': business_folder['drive_id']
            }
        )

        # Record document storage action
        firebase_service.record_ai_action(
            business_id=business_id,
            action_type='document_stored',
            action_data={
                'document_type': document_type,
                'document_url': stored_document['url'],
                'expense_id': expense['id'] if is_transaction else None,
                'mime_type': mime_type,
                'is_transaction': is_transaction
            },
            related_id=expense['id'] if is_transaction else None
        )

        # Prepare response
        response_data = {
            'success': True,
            'document': {
                'url': stored_document['url'],
                'type': document_type,
                'date': document_date
            }
        }

        if is_transaction:
            response_data['transaction'] = {
                'id': expense['id'],
                'date': transaction['transaction_date'],
                'amount': transaction['amount'],
                'description': transaction['description'],
                'category': transaction['category'],
                'payment_method': transaction['payment_method'],
                'merchant': transaction.get('merchant', 'N/A')
            }

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)