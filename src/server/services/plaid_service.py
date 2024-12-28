import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.accounts_get_request_options import AccountsGetRequestOptions
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

class PlaidService:
    def __init__(self):
        """Initialize Plaid client"""
        try:
            # Log configuration details for debugging
            logger.info(f"Initializing Plaid service with:")
            logger.info(f"Client ID: {Config.PLAID_CLIENT_ID}")
            logger.info(f"Environment: {Config.PLAID_ENV}")
            
            configuration = plaid.Configuration(
                host=plaid.Environment.Sandbox,
                api_key={
                    'clientId': Config.PLAID_CLIENT_ID,
                    'secret': Config.PLAID_SECRET,
                }
            )
            
            self.client = plaid_api.PlaidApi(plaid.ApiClient(configuration))
            logger.info("Plaid service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Plaid service: {str(e)}")
            raise

    def create_link_token(self, user_id: str) -> Dict[str, Any]:
        """Create a Link token for initializing Plaid Link"""
        try:
            logger.info(f"Creating link token for user {user_id}")
            
            request = LinkTokenCreateRequest(
                products=[Products('transactions')],
                client_name="ExpenseBot",
                country_codes=[CountryCode('GB')],
                language='en',
                user=LinkTokenCreateRequestUser(
                    client_user_id=user_id
                )
            )
            
            # Make the request
            response = self.client.link_token_create(request)
            logger.info("Link token created successfully")
            
            return {
                'link_token': response['link_token'],
                'expiration': response['expiration']
            }
            
        except Exception as e:
            logger.error(f"Error creating link token: {str(e)}")
            raise

    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token"""
        try:
            logger.info("Exchanging public token")
            exchange_request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            response = self.client.item_public_token_exchange(exchange_request)
            logger.info("Public token exchanged successfully")
            
            return {
                'access_token': response['access_token'],
                'item_id': response['item_id']
            }
            
        except Exception as e:
            logger.error(f"Error exchanging public token: {str(e)}")
            raise

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accounts associated with an access token"""
        try:
            logger.info("Getting accounts")
            
            # Create the request object without options
            request = AccountsGetRequest(
                access_token=access_token
            )
            
            response = self.client.accounts_get(request)
            accounts = response['accounts']
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            return [{
                'id': account['account_id'],
                'name': account['name'],
                'type': account['type'],
                'subtype': account['subtype'],
                'mask': account.get('mask'),
                'current_balance': account.get('balances', {}).get('current'),
                'currency': account.get('balances', {}).get('iso_currency_code')
            } for account in accounts]
            
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise

    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for an access token"""
        try:
            if not end_date:
                end_date = datetime.now()
                
            response = self.client.transactions_get(
                access_token,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            transactions = response['transactions']
            logger.info(f"Retrieved {len(transactions)} transactions")
            
            return [{
                'id': tx['transaction_id'],
                'account_id': tx['account_id'],
                'date': tx['date'],
                'amount': tx['amount'],
                'currency': tx['iso_currency_code'],
                'description': tx['name'],
                'merchant': tx.get('merchant_name'),
                'category': tx.get('category', ['Uncategorized'])[0],
                'pending': tx['pending']
            } for tx in transactions]
            
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            raise 