import requests
import logging
import json
from datetime import datetime
from PIL import Image
import base64
import io
from config import Config
from typing import Optional, Dict, Any, Tuple, List
from config import Config
import pdf2image

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """Initialize AIService with API configuration"""
        self.api_url = Config.AI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "HTTP-Referer": Config.SITE_URL,
            "X-Title": "ExpenseBot",
            "Content-Type": "application/json"
        }
        self.model = "google/gemini-pro-1.5"

    def _encode_image(self, image_content: bytes, mime_type: str) -> str:
        """Encode image content to base64"""
        return f"data:{mime_type};base64,{base64.b64encode(image_content).decode('utf-8')}"

    def _encode_file(self, file_content: bytes, mime_type: str) -> str:
        """Encode file content to base64"""
        return base64.b64encode(file_content).decode('utf-8')

    def _make_request(self, messages: list) -> dict:
        """Make API request to OpenRouter"""
        try:
            payload = {
                "model": self.model,
                "messages": messages
            }
            logger.debug(f"Making request to OpenRouter with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                url=self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.debug(f"Received response from OpenRouter: {json.dumps(response_data, indent=2)}")
            
            # OpenRouter response format is different, let's normalize it
            if 'choices' not in response_data and 'choices' in response_data.get('response', {}):
                response_data = response_data['response']
                
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            raise

    def process_media(self, media_content: bytes, mime_type: str, message: str = "") -> Tuple[bool, dict, str]:
        """Process different types of media content"""
        logger.info(f"Processing media of type: {mime_type}")
        
        try:
            # Check file size (OpenRouter has a 20MB limit)
            content_size = len(media_content) / (1024 * 1024)  # Size in MB
            if content_size > 20:
                logger.warning(f"File too large: {content_size}MB")
                return False, {}, "Sorry, the file is too large. Please send a smaller file (under 20MB)."

            if mime_type.startswith('image/'):
                try:
                    image = Image.open(io.BytesIO(media_content))
                    image.verify()
                    logger.info(f"Successfully loaded image: {image.format} {image.size}")
                    return self.process_receipt_image(media_content, mime_type, message)
                except Exception as e:
                    logger.error(f"Failed to load image: {str(e)}")
                    return False, {}, "Sorry, the image appears to be corrupted. Please try again."
                
            elif mime_type == 'application/pdf':
                logger.info("Processing PDF document")
                return self.process_document(media_content, mime_type, message)
                
            else:
                logger.warning(f"Unsupported mime type: {mime_type}")
                return False, {}, f"Sorry, I can't process files of type {mime_type}. Please send a PDF or image file."

        except Exception as e:
            logger.error(f"Error processing media: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that file. Please try again."

    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from response text that might be wrapped in markdown code blocks"""
        try:
            # Try to find JSON within markdown code blocks
            if "```json" in text:
                # Extract content between ```json and ```
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end != -1:
                    return text[start:end].strip()
            
            # If no markdown blocks, try to find JSON between curly braces
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return text[start:end]
            
            return text
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {str(e)}")
            return text

    def process_receipt_image(self, image_content: bytes, mime_type: str, message: str = "") -> Tuple[bool, dict, str]:
        """Process receipt images"""
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

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": self._encode_image(image_content, mime_type)
                        }
                    }
                ]
            }]

            response = self._make_request(messages)
            
            if 'choices' in response and len(response['choices']) > 0:
                result_text = response['choices'][0]['message']['content']
                logger.debug(f"Raw response text: {result_text}")
                
                # Extract JSON from response
                json_text = self._extract_json_from_response(result_text)
                logger.debug(f"Extracted JSON text: {json_text}")
                
                try:
                    transaction_data = json.loads(json_text)
                    if self.is_valid_transaction(transaction_data):
                        logger.info("Successfully extracted transaction data")
                        return True, transaction_data, "Receipt processed successfully"
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                    logger.error(f"Failed to parse JSON: {json_text}")
            
            logger.warning("Invalid transaction data received")
            return False, {}, "Could not extract transaction details. Please send a clearer image."

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing the receipt. Please try again."

    def _convert_pdf_to_images(self, pdf_content: bytes) -> List[Image.Image]:
        """Convert PDF content to list of PIL Images"""
        try:
            # Convert PDF bytes to images
            images = pdf2image.convert_from_bytes(
                pdf_content,
                dpi=200,  # Adjust DPI as needed
                fmt='jpeg',
                single_file=True  # Only process first page for receipts/invoices
            )
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to image: {str(e)}")
            raise

    def process_document(self, file_content: bytes, mime_type: str, message: str = "") -> Tuple[bool, dict, str]:
        """Process PDF documents by converting to images first"""
        try:
            logger.info("Processing PDF document")
            
            # Convert PDF to images
            try:
                images = self._convert_pdf_to_images(file_content)
                if not images:
                    return False, {}, "Could not extract any images from the PDF. Please try sending an image directly."
                
                # Process first page only for now
                first_page = images[0]
                logger.info(f"Processing first page of PDF: {first_page.size}")
                
                # Convert PIL Image to bytes
                img_byte_arr = io.BytesIO()
                first_page.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                
                # Process as image
                return self.process_receipt_image(img_byte_arr, 'image/jpeg', message)
                
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}")
                return False, {}, "Sorry, I had trouble processing the PDF. Please try sending an image instead."
            
        except Exception as e:
            logger.error(f"Error in process_document: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that document. Please try again or send an image."

    def is_valid_transaction(self, transaction_data: dict) -> bool:
        """Check if the transaction data contains all required fields with valid values."""
        try:
            if isinstance(transaction_data.get('amount'), str):
                transaction_data['amount'] = float(transaction_data['amount'])
            if isinstance(transaction_data.get('orig_amount'), str):
                transaction_data['orig_amount'] = float(transaction_data.get('orig_amount', 0))

            required_fields = {
                'amount': lambda x: isinstance(x, (int, float)) and x >= 0,
                'description': lambda x: isinstance(x, str) and len(x.strip()) > 0,
                'transaction_date': lambda x: isinstance(x, str) and len(x) == 10,
                'transaction_type': lambda x: x in ['Expense', 'Income', 'Transfer'],
                'currency': lambda x: isinstance(x, str) and x in ['USD', 'EUR', 'GBP'],
                'category': lambda x: isinstance(x, str) and len(x.strip()) > 0,
                'payment_method': lambda x: isinstance(x, str) and len(x.strip()) > 0
            }

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

    def extract_transaction(self, message: str) -> Tuple[bool, dict, str]:
        """Extract transaction details from message"""
        try:
            today = datetime.now()
            check_messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"""Analyze if this message contains expense/transaction information. 
                    Today's date is {today.strftime('%Y-%m-%d')}. 
                    Consider keywords like spent, paid, bought, purchased, cost, etc. 
                    Message: {message} 
                    Respond with just 'YES' or 'NO'."""
                }]
            }]
            
            logger.debug("Making initial check request")
            check_response = self._make_request(check_messages)
            
            if 'choices' not in check_response:
                logger.error(f"Unexpected response format: {json.dumps(check_response, indent=2)}")
                return False, {}, "Sorry, I encountered an error. Please try again."
            
            response_text = check_response['choices'][0]['message']['content']
            logger.debug(f"Check response text: {response_text}")
            
            is_transaction = 'YES' in response_text.upper()
            if not is_transaction:
                return False, {}, "This doesn't seem to be a transaction. Please provide details of what was purchased."

            extract_messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"""Extract transaction details from this message. 
                    Today's date is {today.strftime('%Y-%m-%d')}.
                    
                    Return a JSON object with these fields:
                    {{
                        "transaction_date": "YYYY-MM-DD",
                        "amount": numeric value (no currency symbols),
                        "currency": "GBP" (or other currency code),
                        "description": detailed description,
                        "transaction_type": "Expense",
                        "category": specific category,
                        "payment_method": payment method used,
                        "merchant": store/vendor name
                    }}
                    
                    Message to analyze: {message}"""
                }]
            }]
            
            logger.debug("Making extraction request")
            response = self._make_request(extract_messages)
            
            if 'choices' not in response:
                logger.error(f"Unexpected extraction response format: {json.dumps(response, indent=2)}")
                return False, {}, "Sorry, I encountered an error. Please try again."
            
            result_text = response['choices'][0]['message']['content']
            logger.debug(f"Raw result text: {result_text}")
            
            # Extract JSON from response
            json_text = self._extract_json_from_response(result_text)
            logger.debug(f"Extracted JSON text: {json_text}")
            
            transaction_data = json.loads(json_text)
            
            if self.is_valid_transaction(transaction_data):
                return True, transaction_data, "Transaction extracted successfully"
            
            return False, {}, "Could not extract all transaction details. Please include amount and what was purchased."
            
        except Exception as e:
            logger.error(f"Error extracting transaction: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that. Please try again."

    def process_csv(self, text_content: str, message: str = "") -> Tuple[bool, dict, str]:
        """Process CSV content."""
        try:
            logger.info("Processing CSV content")
            prompt = f"""Extract any expense or transaction information from this CSV content. Additional context: {message} Return a JSON object with transaction details if found. """
            messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt + "\n\n" + text_content
                }]
            }]
            response = self._make_request(messages)
            result_text = response['choices'][0]['message']['content']
            logger.debug(f"Received response: {result_text}")
            try:
                transaction_data = json.loads(result_text)
                if self.is_valid_transaction(transaction_data):
                    return True, transaction_data, "CSV processed successfully"
            except json.JSONDecodeError:
                pass
            return False, {}, "No clear transaction details found in CSV content"
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}", exc_info=True)
            return False, {}, "Sorry, I had trouble processing that CSV content"

    def analyze_content(self, content: bytes, mime_type: str, prompt: str, response_schema: Optional[Dict[str, Any]] = None) -> str:
        """Analyze content with specific prompt and optional response schema"""
        try:
            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]

            if mime_type.startswith('image/'):
                messages[0]['content'].append({
                    "type": "image_url",
                    "image_url": {
                        "url": self._encode_image(content, mime_type)
                    }
                })
            else:
                messages[0]['content'].append({
                    "type": "file_url",
                    "file_url": {
                        "url": f"data:{mime_type};base64,{self._encode_file(content, mime_type)}"
                    }
                })

            response = self._make_request(messages)
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            raise

    def _detect_document_type(self, file_content: bytes, mime_type: str) -> Tuple[str, str]:
        """Detect document type (receipt or invoice) and extract date"""
        try:
            image_content = file_content
            
            # Convert PDF to image if needed
            if mime_type == 'application/pdf':
                logger.debug("Converting PDF to image for document type detection")
                try:
                    # Convert first page of PDF to image
                    images = pdf2image.convert_from_bytes(
                        file_content,
                        dpi=200,
                        fmt='jpeg',
                        first_page=1,
                        last_page=1
                    )
                    if not images:
                        logger.error("Failed to convert PDF to image")
                        return "receipt", datetime.now().strftime('%Y-%m-%d')
                    
                    # Convert PIL Image to bytes
                    img_byte_arr = io.BytesIO()
                    images[0].save(img_byte_arr, format='JPEG')
                    image_content = img_byte_arr.getvalue()
                    mime_type = 'image/jpeg'
                    
                    logger.debug("Successfully converted PDF to image")
                    
                except Exception as e:
                    logger.error(f"Error converting PDF to image: {str(e)}")
                    return "receipt", datetime.now().strftime('%Y-%m-%d')

            prompt = """Analyze this document and determine its type and date.
            Return a JSON object with EXACTLY these fields:
            {
                "document_type": "receipt" or "invoice",
                "date": "YYYY-MM-DD" (date shown on document),
                "confidence": number between 0 and 1
            }

            Important:
            - Look for dates in the document
            - For receipts, look for point-of-sale dates
            - For invoices, look for invoice date or due date
            - If multiple dates found, use the earliest one
            - If no date found, return today's date
            - document_type must be either "receipt" or "invoice"
            - If unsure about type, use visual clues:
              * Receipts usually have items with prices listed
              * Invoices usually have payment terms, invoice numbers, company details
            """

            messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": self._encode_image(image_content, mime_type)
                        }
                    }
                ]
            }]

            response = self._make_request(messages)
            result_text = self._extract_json_from_response(response['choices'][0]['message']['content'])
            result = json.loads(result_text)
            
            logger.info(f"Document type detection result: {result}")
            
            # Validate date format
            try:
                datetime.strptime(result['date'], '%Y-%m-%d')
            except (ValueError, KeyError):
                logger.warning("Invalid date format in response, using current date")
                result['date'] = datetime.now().strftime('%Y-%m-%d')

            return result['document_type'], result['date']

        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            return "receipt", datetime.now().strftime('%Y-%m-%d')  # Default fallback
