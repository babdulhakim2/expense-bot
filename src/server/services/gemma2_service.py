import logging
import json
from datetime import datetime
from PIL import Image
import io
import base64
import requests
from config import Config

logger = logging.getLogger(__name__)

class Gemma2Service:
    def __init__(self):
        self.api_key = Config.GOOGLE_GENERATIVE_AI_API_KEY
        self.api_endpoint = "https://paligema.expensebot.xyz/v1/predict"  # Replace with actual Gemma API endpoint
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def encode_image(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def process_receipt_image(self, image: Image.Image, message: str = "") -> tuple[bool, dict, str]:
        """Process receipt images using Gemma API."""
        try:
            logger.info("Processing receipt image with Gemma")
            today = datetime.now()
            
            # Convert image to base64
            base64_image = self.encode_image(image)
            
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
            }}"""

            # Prepare the request payload
            payload = {
                "prompt": prompt,
                "image": base64_image,
                "temperature": 0.1,
                "response_format": "json"
            }

            # Make API request
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return False, {}, "Failed to process receipt with Gemma API"

            transaction_data = response.json()
            
            if self.is_valid_transaction(transaction_data):
                logger.info("Successfully extracted transaction data")
                return True, transaction_data, "Receipt processed successfully"
            else:
                logger.warning("Invalid transaction data received")
                return False, {}, "Could not extract transaction details. Please send a clearer image."

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing the receipt. Please try again."

    def is_valid_transaction(self, transaction_data: dict) -> bool:
        """Check if the transaction data contains all required fields with valid values."""
        try:
            # Convert string amounts to float if needed
            if isinstance(transaction_data.get('amount'), str):
                transaction_data['amount'] = float(transaction_data['amount'])
            
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
                'merchant': 'Unknown',
                'transaction_id': f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
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
        """Extract transaction details from text message."""
        try:
            logger.info("Processing text message with Gemma")
            today = datetime.now()
            
            prompt = f"""Extract transaction details from this message.
            Today's date is {today.strftime('%Y-%m-%d')}.
            Message: {message}

            Return a JSON object with EXACTLY these fields:
            {{
                "transaction_date": "{today.strftime('%Y-%m-%d')}" (or date from message),
                "amount": numeric value (no currency symbols),
                "currency": "GBP" (or currency mentioned),
                "description": what was purchased/paid for,
                "transaction_type": "Expense",
                "category": category based on description,
                "payment_method": payment method if mentioned or "Card",
                "merchant": vendor name if mentioned
            }}"""

            # Prepare the request payload
            payload = {
                "prompt": prompt,
                "temperature": 0.1,
                "response_format": "json"
            }

            # Make API request
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return False, {}, "Failed to process message with Gemma API"

            transaction_data = response.json()
            
            if self.is_valid_transaction(transaction_data):
                logger.info("Successfully extracted transaction data")
                return True, transaction_data, "Transaction processed successfully"
            else:
                logger.warning("Invalid transaction data received")
                return False, {}, "Could not extract transaction details from message."

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing your message. Please try again."

    def process_media(self, media_content: bytes, media_type: str, message: str = "") -> tuple[bool, dict, str]:
        """Process media content using Gemma API."""
        try:
            logger.info("Processing media with Gemma")
            
            # Convert media content to PIL Image
            try:
                image = Image.open(io.BytesIO(media_content))
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            except Exception as e:
                logger.error(f"Failed to process image: {str(e)}")
                return False, {}, "Could not process the image. Please try again."

            # Use existing process_receipt_image method
            return self.process_receipt_image(image, message)

        except Exception as e:
            logger.error(f"Error in process_media: {str(e)}", exc_info=True)
            return False, {}, "Failed to process media content"
