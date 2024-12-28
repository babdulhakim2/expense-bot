import hmac
import hashlib
import logging
from typing import Dict, Any
from .firebase_service import FirebaseService

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.firebase_service = FirebaseService()

    def verify_signature(self, body: bytes, signature: str, webhook_secret: str) -> bool:
        """Verify TrueLayer webhook signature"""
        try:
            expected_sig = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False

    async def handle_new_transaction(self, data: Dict[str, Any]):
        """Handle new transaction webhook"""
        try:
            transaction = data.get('transaction', {})
            account_id = transaction.get('account_id')
            
            # Get connection details from account_id
            connection = await self.firebase_service.get_connection_by_account(account_id)
            if not connection:
                raise ValueError(f"No connection found for account {account_id}")

            # Format transaction data
            transaction_data = {
                'id': transaction.get('transaction_id'),
                'amount': transaction.get('amount'),
                'currency': transaction.get('currency'),
                'description': transaction.get('description'),
                'timestamp': transaction.get('timestamp'),
                'status': transaction.get('status'),
                'merchant': transaction.get('merchant', {}).get('name'),
                'category': transaction.get('category')
            }

            # Store transaction
            await self.firebase_service.store_transaction(
                business_id=connection['business_id'],
                transaction_data=transaction_data
            )

            # Update last sync time
            await self.firebase_service.update_connection_sync_time(
                business_id=connection['business_id'],
                connection_id=connection['id']
            )

        except Exception as e:
            logger.error(f"Error handling new transaction: {str(e)}")
            raise

    async def handle_modified_transaction(self, data: Dict[str, Any]):
        """Handle modified transaction webhook"""
        # Similar to handle_new_transaction but update existing transaction
        pass

    async def handle_data_sync(self, data: Dict[str, Any]):
        """Handle data sync webhook"""
        try:
            sync_type = data.get('sync_type')
            account_id = data.get('account_id')
            
            connection = await self.firebase_service.get_connection_by_account(account_id)
            if not connection:
                raise ValueError(f"No connection found for account {account_id}")

            await self.firebase_service.update_connection_sync_time(
                business_id=connection['business_id'],
                connection_id=connection['id']
            )

        except Exception as e:
            logger.error(f"Error handling data sync: {str(e)}")
            raise

    async def handle_connection_status(self, data: Dict[str, Any]):
        """Handle connection status webhook"""
        try:
            status = data.get('status')
            account_id = data.get('account_id')
            
            connection = await self.firebase_service.get_connection_by_account(account_id)
            if not connection:
                raise ValueError(f"No connection found for account {account_id}")

            await self.firebase_service.update_connection_status(
                business_id=connection['business_id'],
                connection_id=connection['id'],
                status=status
            )

        except Exception as e:
            logger.error(f"Error handling connection status: {str(e)}")
            raise 