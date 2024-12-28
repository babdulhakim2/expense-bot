import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
from .plaid_service import PlaidService
from .firebase_service import FirebaseService

logger = logging.getLogger(__name__)

class BankSyncService:
    def __init__(self):
        """Initialize bank sync service"""
        self.firebase_service = FirebaseService()
        self.plaid_service = PlaidService()
        logger.info("Bank Sync Service initialized")

    async def sync_transactions(
        self,
        user_id: str,
        business_id: str,
        connection_id: str,
        from_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync transactions for a bank connection"""
        try:
            # Get connection details
            connection = await self.firebase_service.get_bank_connection(
                user_id=user_id,
                business_id=business_id,
                connection_id=connection_id
            )
            
            if not connection:
                raise Exception("Bank connection not found")

            # Get transactions from Plaid
            transactions = await self.plaid_service.get_transactions(
                access_token=connection['access_token'],
                start_date=from_date or (datetime.now() - timedelta(days=30))
            )
            
            # Process each transaction
            all_transactions = []
            for transaction in transactions:
                if not await self.firebase_service.is_transaction_synced(
                    user_id=user_id,
                    business_id=business_id,
                    bank_transaction_id=transaction['id']
                ):
                    # Store transaction
                    stored_tx = await self.firebase_service.store_transaction(
                        user_id=user_id,
                        business_id=business_id,
                        transaction_data=transaction
                    )
                    all_transactions.append(stored_tx)
            
            # Update last sync time
            await self.firebase_service.update_connection_sync_time(
                business_id=business_id,
                connection_id=connection_id
            )
            
            return {
                "synced_transactions": len(all_transactions),
                "transactions": all_transactions
            }
            
        except Exception as e:
            logger.error(f"Error syncing transactions: {str(e)}")
            raise 