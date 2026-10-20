from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import uuid

from app.models.schemas import (
    StructuredIntent,
    IntentCreateRequest,
    PaymentRequest,
    DecisionOutput,
    DecisionEnum,
    ApprovalActionRequest,
    PolicySettings,
    MerchantInfo
)
from app.core.signer import signer
from app.core.audit import audit_log
from app.core.mock_upi import mock_upi
from app.engines.firewall import firewall_engine
from app.engines.merchant import KNOWN_MERCHANTS

app = FastAPI(
    title="IntentGuard Firewall API",
    description="Safety and Intent Verification Layer for Agentic Payments (DRUNIX Hackathon 2026)",
    version="1.0.0"
)

# Enable CORS for local web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for hackathon runtime
intents_db: Dict[str, StructuredIntent] = {}
pending_requests_db: Dict[str, Dict[str, Any]] = {}
policy_settings = PolicySettings()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "IntentGuard Payment Firewall",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/intents", response_model=StructuredIntent)
def create_intent(req: IntentCreateRequest):
    """
    Creates a new structured user intent and cryptographically signs it with Ed25519.
    """
    intent_id = f"int_{uuid.uuid4().hex[:6]}"
    now = datetime.now(timezone.utc)
    
    intent = StructuredIntent(
        intent_id=intent_id,
        user_id="usr_default",
        task=req.task,
        category=req.category,
        max_amount=req.max_amount,
        currency="INR",
        allowed_payees=req.allowed_payees,
        quantity=1,
        valid_from=now,
        valid_until=now + timedelta(minutes=req.valid_minutes),
        is_revoked=False,
        is_confirmed=True
    )
    
    # Cryptographically sign the intent
    signature = signer.sign_intent(intent.model_dump())
    intent.signature = signature
    
    # Save to store
    intents_db[intent_id] = intent
    
    # Log to tamper-evident audit trail
    audit_log.log_event("INTENT_CREATED", {
        "intent_id": intent.intent_id,
        "task": intent.task,
        "max_amount": intent.max_amount,
        "signature": signature
    })
    
    return intent

@app.get("/intents/{intent_id}", response_model=StructuredIntent)
def get_intent(intent_id: str):
    if intent_id not in intents_db:
        raise HTTPException(status_code=404, detail="Intent not found")
    return intents_db[intent_id]

@app.get("/intents", response_model=List[StructuredIntent])
def list_intents():
    return list(intents_db.values())

@app.post("/intents/{intent_id}/revoke")
def revoke_intent(intent_id: str):
    """
    Instant Emergency Kill Switch: Revokes intent authority.
    Any future payment attempts using this intent ID are blocked with risk 1.0.
    """
    if intent_id not in intents_db:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    intents_db[intent_id].is_revoked = True
    audit_log.log_event("KILL_SWITCH_TRIGGERED", {
        "intent_id": intent_id,
        "action": "REVOKED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "SUCCESS", "message": f"Intent {intent_id} has been revoked.", "is_revoked": True}

@app.post("/payments/verify", response_model=DecisionOutput)
def verify_payment_request(req: PaymentRequest):
    """
    Main Firewall Gate: The AI agent MUST call this endpoint before initiating any payment.
    Runs cryptographic validation, Hard Rules, and Risk Engine.
    """
    intent = intents_db.get(req.intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail=f"No active intent found with ID '{req.intent_id}'")

    # 1. Cryptographic Signature Verification
    if not signer.verify_intent(intent.model_dump(), intent.signature):
        audit_log.log_event("SIGNATURE_VERIFICATION_FAILED", {"intent_id": req.intent_id, "request_id": req.request_id})
        raise HTTPException(status_code=403, detail="CRITICAL: Intent cryptographic signature is invalid or tampered!")

    # 2. Evaluate with Firewall Engine
    decision = firewall_engine.evaluate(intent, req, policy_settings)

    # 3. If Approved, route directly to the Mock UPI rail
    if decision.decision == DecisionEnum.APPROVE:
        cleared_txn = mock_upi.execute_payment(req.payee, req.amount, req.description)
        decision.payment_reference = cleared_txn["txn_id"]

    # 4. If Ask User, stage request for human-in-the-loop one-tap confirmation
    elif decision.decision == DecisionEnum.ASK_USER:
        pending_requests_db[req.request_id] = {
            "request": req.model_dump(),
            "decision": decision.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    # 5. Log decision to audit trail
    audit_log.log_event("PAYMENT_EVALUATED", {
        "request_id": req.request_id,
        "intent_id": req.intent_id,
        "payee": req.payee,
        "amount": req.amount,
        "decision": decision.decision.value,
        "risk_score": decision.risk_score,
        "reasons": decision.reasons,
        "payment_ref": decision.payment_reference
    })

    return decision

@app.get("/payments/pending")
def list_pending_approvals():
    """Returns all payments currently in 'ASK_USER' awaiting manual review."""
    return list(pending_requests_db.values())

@app.post("/payments/{request_id}/approve", response_model=DecisionOutput)
def approve_pending_payment(request_id: str, action: ApprovalActionRequest):
    """
    Human-in-the-loop manual confirmation for borderline payments.
    """
    if request_id not in pending_requests_db:
        raise HTTPException(status_code=404, detail="Pending payment request not found or already resolved.")

    pending_data = pending_requests_db.pop(request_id)
    req = PaymentRequest(**pending_data["request"])

    now = datetime.now(timezone.utc)
    if action.user_action.upper() == "APPROVE":
        cleared = mock_upi.execute_payment(req.payee, req.amount, req.description)
        decision = DecisionOutput(
            request_id=req.request_id,
            decision=DecisionEnum.APPROVE,
            risk_score=0.10,
            reasons=[f"Manually approved by user: {action.reason}"],
            user_message=f"Manual user override: Authorized ₹{req.amount:,.2f} payment to {req.payee}.",
            payment_reference=cleared["txn_id"],
            timestamp=now
        )
        audit_log.log_event("USER_MANUAL_APPROVAL", {"request_id": request_id, "action": "APPROVED", "txn_id": cleared["txn_id"]})
    else:
        decision = DecisionOutput(
            request_id=req.request_id,
            decision=DecisionEnum.BLOCK,
            risk_score=1.0,
            reasons=[f"Rejected by user during human-in-the-loop check: {action.reason}"],
            user_message=f"User rejected payment of ₹{req.amount:,.2f} to {req.payee}.",
            timestamp=now
        )
        audit_log.log_event("USER_MANUAL_REJECTION", {"request_id": request_id, "action": "REJECTED"})

    return decision

@app.get("/audit")
def get_audit_trail():
    """
    Returns the complete hash-chained audit log and its real-time cryptographic verification status.
    """
    is_valid, validation_msg = audit_log.verify_integrity()
    return {
        "is_chain_valid": is_valid,
        "verification_message": validation_msg,
        "total_blocks": len(audit_log.chain),
        "chain": audit_log.get_trail()
    }

@app.get("/merchants")
def get_verified_merchants():
    """Returns the verified merchant registry."""
    return list(KNOWN_MERCHANTS.values())

@app.get("/policies", response_model=PolicySettings)
def get_policies():
    return policy_settings

@app.put("/policies", response_model=PolicySettings)
def update_policies(new_policy: PolicySettings):
    global policy_settings
    policy_settings = new_policy
    audit_log.log_event("POLICY_UPDATED", new_policy.model_dump())
    return policy_settings
