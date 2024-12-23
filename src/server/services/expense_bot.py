import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import io
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
from models.schemas import Transaction, TransactionType, Currency

logger = logging.getLogger(__name__)

class ExpenseBot:
    def __init__(self, firebase_service, gemini_service):
        self.firebase = firebase_service
        self.gemini = gemini_service
        
    