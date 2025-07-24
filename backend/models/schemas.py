from typing_extensions import TypedDict, Optional
from typing import Union, Literal
import enum

class Currency(str, enum.Enum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"
    # Add more currencies as needed

class TransactionType(str, enum.Enum):
    EXPENSE = "Expense"
    INCOME = "Income"
    TRANSFER = "Transfer"

class DocumentType(str, enum.Enum):
    RECEIPT = "Receipt"
    INVOICE = "Invoice"

class Transaction(TypedDict):
    transaction_date: str  # Format: YYYY-MM-DD
    timestamp: str  # Format: YYYY-MM-DD HH:mm:ss, extracted from transaction or derived from date
    amount: float  # Amount in GBP
    orig_currency: Currency
    orig_amount: float  # Original amount in original currency
    description: str
    transaction_type: TransactionType
    category: str
    payment_method: str
    transaction_id: Optional[str]  # Optional, will be generated if empty
    merchant: str
    exchange_rate: Optional[float]
    business_name: Optional[str]
    status: Optional[str]  # For tracking transaction status


