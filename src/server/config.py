import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini Configuration
    GEMINI_MODEL = "gemini-1.5-flash"
    GEMINI_API_KEY = os.environ["GOOGLE_GENERATIVE_AI_API_KEY"]
    GEMINI_GENERATION_CONFIG = {
        "temperature": 0.1,  # Lower for more consistent output
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    # Database Configuration
    DATABASE_NAME = "expenses.db"

    # Google Drive/Sheets Configuration
    GOOGLE_SERVICE_ACCOUNT_KEY = os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"] 