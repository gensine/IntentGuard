from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DecisionEnum(str, Enum):
    APPROVE = "APPROVE"
    ASK_USER = "ASK_USER"
    BLOCK = "BLOCK"

class StructuredIntent(BaseModel):
    intent_id: str
    user_id: str = "usr_default"
    task: str
    category: str = "general"
    max_amount: float
    currency: str = "INR"
    allowed_payees: List[str] = []
    quantity: int = 1
    valid_from: datetime
    valid_until: datetime
    signature: Optional[str] = None
    is_revoked: bool = False
    is_confirmed: bool = True

class IntentCreateRequest(BaseModel):
    task: str
    max_amount: float
    category: str = "transport.rail"
    allowed_payees: List[str] = ["irctc@upi", "swiggy@icici", "amazon@apl", "zomato@hdfc"]
    valid_minutes: int = 30

class PaymentRequest(BaseModel):
    request_id: str
    intent_id: str
    payee: str
    amount: float
    currency: str = "INR"
    description: str
    agent_trace_ref: Optional[str] = None
    raw_context_sources: List[str] = []  # Context traces (e.g., scraped web text, user instructions)

class DecisionOutput(BaseModel):
    request_id: str
    decision: DecisionEnum
    risk_score: float
    reasons: List[str]
    user_message: str
    payment_reference: Optional[str] = None
    timestamp: datetime

class ApprovalActionRequest(BaseModel):
    user_action: str  # "APPROVE" or "REJECT"
    reason: Optional[str] = "User manual confirmation"

class PolicySettings(BaseModel):
    daily_cap: float = 10000.0
    auto_approve_threshold: float = 0.30
    ask_user_threshold: float = 0.70
    blocked_categories: List[str] = ["gambling", "crypto_unregulated"]
    blocked_payees: List[str] = ["fraudster@upi", "darkweb@paytm"]

class MerchantInfo(BaseModel):
    vpa: str
    name: str
    category: str
    is_verified: bool
    complaint_count: int = 0
    trust_score: float = 1.0
