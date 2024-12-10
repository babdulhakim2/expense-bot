import google.generativeai as genai
from models.schemas import Transaction
import logging
import json
from datetime import datetime
from PIL import Image
import time
import io
from config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GOOGLE_GENERATIVE_AI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config=Config.GEMINI_GENERATION_CONFIG
        )

    def wait_for_file_processing(self, file):
        """Wait for uploaded file to be processed by Gemini."""
        logger.info(f"Waiting for file {file.name} to be processed...")
        while True:
            file = genai.get_file(file.name)
            if file.state.name == "ACTIVE":
                logger.info(f"File {file.name} is ready")
                return True
            elif file.state.name == "PROCESSING":
                logger.debug("Still processing...")
                time.sleep(2)
            else:
                logger.error(f"File processing failed: {file.state.name}")
                return False

    def process_media(self, media_content: bytes, mime_type: str, message: str = "") -> tuple[bool, dict, str]:
        """Process different types of media content."""
        logger.info(f"Processing media of type: {mime_type}")
        
        try:
            # Handle different mime types
            if mime_type.startswith('image/'):
                # Add error handling for image loading
                try:
                    image = Image.open(io.BytesIO(media_content))
                    image.load()  # This will verify the image is complete
                    logger.info(f"Successfully loaded image: {image.format} {image.size}")
                    return self.process_receipt_image(image, message)
                except Exception as e:
                    logger.error(f"Failed to load image: {str(e)}")
                    return False, {}, "Sorry, the image appears to be corrupted. Please try sending it again."
                
            elif mime_type == 'application/pdf':
                # Upload PDF to Gemini
                file = genai.upload_file(io.BytesIO(media_content), mime_type=mime_type)
                if not self.wait_for_file_processing(file):
                    return False, {}, "Failed to process PDF file"
                    
                return self.process_document(file, message)
                
            elif mime_type == 'text/csv':
                # Process CSV content
                text_content = media_content.decode('utf-8')
                return self.process_csv(text_content, message)
                
            else:
                logger.warning(f"Unsupported mime type: {mime_type}")
                return False, {}, f"Sorry, I can't process files of type {mime_type}"

        except Exception as e:
            logger.error(f"Error processing media: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that file. Please try again."

    def process_receipt_image(self, image: Image.Image, message: str = "") -> tuple[bool, dict, str]:
        """Process receipt images."""
        try:
            logger.info("Processing receipt image")
            today = datetime.now()
            
            prompt = f"""Analyze this receipt image and extract transaction details.
            Today's date is {today.strftime('%Y-%m-%d')}.
            Additional context: {message}

            Return a JSON object with EXACTLY these fields:
            {{
                "transaction_date": "{today.strftime('%Y-%m-%d')}" (or date from receipt),
                "amount": numeric value (no currency symbols),
                "currency": "GBP" (or currency shown on receipt),
                "description": detailed items purchased,
                "transaction_type": "Expense",
                "category": category based on items/merchant,
                "payment_method": payment method from receipt or "Card",
                "merchant": store/vendor name,
                "transaction_id": receipt number if visible
            }}

            Important:
            - Amount must be a number (not a string)
            - Date must be YYYY-MM-DD format
            - If currency is not GBP, provide the original amount
            """

            logger.debug(f"Sending prompt to Gemini: {prompt}")
            result = self.model.generate_content(
                [prompt, image],
                generation_config={"response_mime_type": "application/json"}
            )
            
            logger.debug(f"Received response: {result.text}")
            transaction_data = json.loads(result.text)
            
            if self.is_valid_transaction(transaction_data):
                logger.info("Successfully extracted transaction data")
                return True, transaction_data, "Receipt processed successfully"
            else:
                logger.warning("Invalid transaction data received")
                return False, {}, "Could not extract transaction details. Please send a clearer image."

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing the receipt. Please try again."

    def process_document(self, file, message: str = "") -> tuple[bool, dict, str]:
        """Process PDF documents."""
        try:
            logger.info("Processing PDF document")
            
            prompt = f"""Extract any expense or transaction information from this document.
            Additional context: {message}

            Return a JSON object with transaction details if found.
            """
            
            result = self.model.generate_content([prompt, file])
            logger.debug(f"Received response: {result.text}")
            
            # Try to parse as transaction or return error
            try:
                transaction_data = json.loads(result.text)
                if self.is_valid_transaction(transaction_data):
                    return True, transaction_data, "Document processed successfully"
            except json.JSONDecodeError:
                pass
                
            return False, {}, "No clear transaction details found in document"
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that document"

    def is_valid_transaction(self, transaction_data: dict) -> bool:
        """Check if the transaction data contains all required fields with valid values."""
        try:
            # Convert string amounts to float if needed
            if isinstance(transaction_data.get('amount'), str):
                transaction_data['amount'] = float(transaction_data['amount'])
            if isinstance(transaction_data.get('orig_amount'), str):
                transaction_data['orig_amount'] = float(transaction_data.get('orig_amount', 0))
            
            # Ensure all required fields exist with correct types
            required_fields = {
                'amount': lambda x: isinstance(x, (int, float)) and x >= 0,
                'description': lambda x: isinstance(x, str) and len(x.strip()) > 0,
                'transaction_date': lambda x: isinstance(x, str) and len(x) == 10,  # YYYY-MM-DD
                'transaction_type': lambda x: x in ['Expense', 'Income', 'Transfer'],
                'currency': lambda x: isinstance(x, str) and x in ['USD', 'EUR', 'GBP'],
                'category': lambda x: isinstance(x, str) and len(x.strip()) > 0,
                'payment_method': lambda x: isinstance(x, str) and len(x.strip()) > 0
            }

            # Add default values for missing optional fields
            defaults = {
                'orig_currency': transaction_data.get('currency', 'GBP'),
                'orig_amount': transaction_data.get('amount', 0.0),
                'merchant': 'Unknown',
                'exchange_rate': 1.0 if transaction_data.get('currency') == 'GBP' else None
            }
            
            for field, value in defaults.items():
                if field not in transaction_data:
                    transaction_data[field] = value

            valid = all(
                field in transaction_data and validator(transaction_data[field])
                for field, validator in required_fields.items()
            )
            
            if valid:
                logger.info(f"Valid transaction data: {transaction_data}")
            else:
                logger.warning(f"Invalid transaction data: {transaction_data}")
                
            return valid

        except Exception as e:
            logger.error(f"Error validating transaction: {str(e)}")
            return False

    def extract_transaction(self, message: str) -> tuple[bool, dict, str]:
        """Extract transaction details from message."""
        try:
            # First, check if this is a transaction message
            today = datetime.now()
            check_prompt = f"""Analyze if this message contains expense/transaction information.
            Today's date is {today.strftime('%Y-%m-%d')}.
            Consider keywords like spent, paid, bought, purchased, cost, etc.
            
            Message: {message}
            
            Respond with just 'YES' or 'NO'.
            """

            check_result = self.model.generate_content(check_prompt)
            is_transaction = 'YES' in check_result.text.upper()

            if not is_transaction:
                return False, {}, "This doesn't seem to be a transaction. Please provide a screenshot of a receipt or invoice."

            # Extract transaction details
            extract_prompt = f"""Extract transaction details from this message.
            Today's date is {today.strftime('%Y-%m-%d')}. Use this as default if no date mentioned.

            Important notes:
            1. For currency conversion:
               - Identify the original transaction currency (e.g., USD, EUR, GBP)
               - If amount is in a different currency than GBP, provide both amounts
               - Use current exchange rates if needed
            
            2. For transaction ID:
               - If receipt/document contains a reference number, use it
               - Otherwise, leave it empty and system will generate one

            Return a JSON object with EXACTLY these fields:
            {{
                "transaction_date": "YYYY-MM-DD",
                "amount": numeric value in GBP,
                "orig_currency": original currency code,
                "orig_amount": original amount if different from GBP amount,
                "description": detailed description of purchase,
                "transaction_type": "Expense",
                "category": specific category (Food, Transport, Shopping, etc.),
                "payment_method": payment method used,
                "transaction_id": receipt reference if available,
                "merchant": store/vendor name if available,
                "exchange_rate": rate used for conversion if applicable
            }}

            Example for direct GBP transaction:
            {{
                "transaction_date": "2024-03-14",
                "amount": 25.50,
                "orig_currency": "GBP",
                "orig_amount": 25.50,
                "description": "Lunch at Subway - Footlong Sub & Drink",
                "transaction_type": "Expense",
                "category": "Food & Dining",
                "payment_method": "Credit Card",
                "transaction_id": "",
                "merchant": "Subway Oxford Street",
                "exchange_rate": null
            }}

            Example for USD transaction:
            {{
                "transaction_date": "2024-03-14",
                "amount": 20.15,
                "orig_currency": "USD",
                "orig_amount": 25.50,
                "description": "Amazon.com - USB Cable",
                "transaction_type": "Expense",
                "category": "Electronics",
                "payment_method": "Credit Card",
                "transaction_id": "AMZ-123456",
                "merchant": "Amazon.com",
                "exchange_rate": 0.79
            }}

            Message to analyze: {message}
            """

            result = self.model.generate_content(
                extract_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent output
                    response_mime_type="application/json",
                    response_schema=Transaction
                )
            )
            
            logger.debug(f"Gemini response: {result.text}")
            transaction_data = json.loads(result.text)
            
            if self.is_valid_transaction(transaction_data):
                # Add transaction ID if not provided
                if not transaction_data.get('transaction_id'):
                    transaction_data['transaction_id'] = f"TXN_{today.strftime('%Y%m%d%H%M%S')}"
                
                # Ensure currency handling is correct
                if transaction_data['orig_currency'] != 'GBP':
                    logger.info(f"Currency conversion: {transaction_data['orig_currency']} to GBP")
                    logger.info(f"Original amount: {transaction_data['orig_amount']}, GBP amount: {transaction_data['amount']}")
                
                return True, transaction_data, "Transaction extracted successfully"
            else:
                return False, {}, "Could not extract all transaction details. Please include amount and what was purchased."

        except Exception as e:
            logger.error(f"Error extracting transaction: {e}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that. Please try again with the amount and description."

    def process_csv(self, text_content: str, message: str = "") -> tuple[bool, dict, str]:
        """Process CSV content."""
        try:
            logger.info("Processing CSV content")
            
            prompt = f"""Extract any expense or transaction information from this CSV content.
            Additional context: {message}

            Return a JSON object with transaction details if found.
            """
            
            result = self.model.generate_content([prompt, text_content])
            logger.debug(f"Received response: {result.text}")
            
            # Try to parse as transaction or return error
            try:
                transaction_data = json.loads(result.text)
                if self.is_valid_transaction(transaction_data):
                    return True, transaction_data, "CSV processed successfully"
            except json.JSONDecodeError:
                pass
                
            return False, {}, "No clear transaction details found in CSV content"
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that CSV content"