import aiohttp
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from config import Config
import urllib.parse

logger = logging.getLogger(__name__)

class TrueLayerService:
    def __init__(self):
        """Initialize TrueLayer service"""
        self.client_id = Config.TRUELAYER_CLIENT_ID
        self.client_secret = Config.TRUELAYER_CLIENT_SECRET
        self.redirect_uri = Config.TRUELAYER_REDIRECT_URI
        self.auth_url = "https://auth.truelayer.com"
        self.api_url = "https://api.truelayer.com"
        
        # Add debug logging
        logger.info(f"TrueLayer Service initialized with redirect_uri: {self.redirect_uri}")
        
    async def get_auth_url(self, state: str) -> str:
        """Get OAuth authorization URL"""
        try:
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "scope": "info accounts balance cards transactions",
                "redirect_uri": self.redirect_uri,
                "state": state,
                "providers": "uk-ob-all uk-oauth-all",
            }
            
            # Debug log the parameters (excluding sensitive data)
            logger.debug(f"Auth URL params: {params}")
            
            query_string = urllib.parse.urlencode(params)
            auth_url = f"{self.auth_url}/?{query_string}"
            
            # Debug log the generated URL
            logger.debug(f"Generated auth URL: {auth_url}")
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {str(e)}")
            raise

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            logger.info("Exchanging auth code for tokens")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.auth_url}/connect/token",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json"
                    },
                    data={
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.redirect_uri
                    }
                ) as response:
                    data = await response.json()
                    logger.debug(f"Token exchange response: {data}")
                    
                    if response.status != 200:
                        logger.error(f"Token exchange failed: {data}")
                        raise Exception(f"Failed to exchange code: {data}")
                    
                    # Validate required fields
                    required_fields = ['access_token', 'expires_in']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        logger.error(f"Missing required fields in token response: {missing_fields}")
                        raise Exception(f"Invalid token response: missing {', '.join(missing_fields)}")
                    
                    logger.info("Successfully exchanged code for tokens")
                    return {
                        "access_token": data["access_token"],
                        "refresh_token": data.get("refresh_token"),
                        "expires_in": data["expires_in"]
                    }
                    
        except Exception as e:
            logger.error(f"Error exchanging code: {str(e)}")
            raise

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.auth_url}/connect/token",
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token
                    }
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Token refresh failed: {error_data}")
                        
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise

    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's bank accounts"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/data/v1/accounts",
                    headers={"Authorization": f"Bearer {access_token}"}
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Failed to get accounts: {error_data}")
                        
                    data = await response.json()
                    return data.get("results", [])
                    
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise

    async def get_transactions(
        self,
        access_token: str,
        account_id: str,
        from_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for an account"""
        try:
            if not from_date:
                from_date = datetime.now() - timedelta(days=90)
                
            params = {
                "from": from_date.strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/data/v1/accounts/{account_id}/transactions",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Failed to get transactions: {error_data}")
                        
                    data = await response.json()
                    return data.get("results", [])
                    
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            raise 