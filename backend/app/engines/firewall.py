from datetime import datetime, timezone
from typing import List, Dict, Optional
from app.models.schemas import StructuredIntent, PaymentRequest, DecisionOutput, DecisionEnum, PolicySettings
from app.engines.merchant import evaluate_merchant
from app.engines.injection import detect_prompt_injection

class PaymentFirewallEngine:
    """
    Core Payment Intent Firewall engine.
    Applies Tier 1 (Deterministic Hard Blocks) and Tier 2 (Weighted Risk Analysis).
    """
    def __init__(self):
        self.request_history: List[PaymentRequest] = []

    def evaluate(self, intent: StructuredIntent, req: PaymentRequest, policy: PolicySettings) -> DecisionOutput:
        reasons: List[str] = []
        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------
        # TIER 1: DETERMINISTIC HARD RULES (Instant Block)
        # -------------------------------------------------------------
        # 1. Kill Switch / Revocation Check
        if intent.is_revoked:
            return DecisionOutput(
                request_id=req.request_id,
                decision=DecisionEnum.BLOCK,
                risk_score=1.0,
                reasons=["Agent authorization was revoked by user emergency kill-switch."],
                user_message="BLOCKED: The kill switch was triggered for this intent. All payment actions are frozen.",
                timestamp=now
            )

        # 2. Time Window Expiry Check
        valid_until = intent.valid_until if intent.valid_until.tzinfo else intent.valid_until.replace(tzinfo=timezone.utc)
        if now > valid_until:
            return DecisionOutput(
                request_id=req.request_id,
                decision=DecisionEnum.BLOCK,
                risk_score=1.0,
                reasons=[f"Intent expired at {valid_until.strftime('%H:%M:%S UTC')}."],
                user_message="BLOCKED: The authorized time window for this task has expired.",
                timestamp=now
            )

        # 3. Blocklisted Payee Check
        if req.payee.lower() in [p.lower() for p in policy.blocked_payees]:
            return DecisionOutput(
                request_id=req.request_id,
                decision=DecisionEnum.BLOCK,
                risk_score=1.0,
                reasons=[f"Payee '{req.payee}' is globally blacklisted as high-risk."],
                user_message=f"BLOCKED: Payee '{req.payee}' is flagged as fraudulent in global registry.",
                timestamp=now
            )

        # 4. Severe Budget Exceedance (> 15% above user's approved limit)
        hard_limit = intent.max_amount * 1.15
        if req.amount > hard_limit:
            return DecisionOutput(
                request_id=req.request_id,
                decision=DecisionEnum.BLOCK,
                risk_score=0.98,
                reasons=[f"Requested amount ₹{req.amount:,.2f} severely exceeds approved limit ₹{intent.max_amount:,.2f}."],
                user_message=f"BLOCKED: The agent tried to pay ₹{req.amount:,.2f}, which exceeds your approved budget of ₹{intent.max_amount:,.2f}.",
                timestamp=now
            )

        # -------------------------------------------------------------
        # TIER 2: SOFT RISK EVALUATION (Weighted Scoring)
        # -------------------------------------------------------------
        risk_score = 0.0

        # Factor A: Prompt Injection & Context Source Tagging
        is_injected, inject_risk, inject_reasons = detect_prompt_injection(req.raw_context_sources)
        if is_injected:
            risk_score += inject_risk
            reasons.extend(inject_reasons)

        # Factor B: Merchant Reputation & Lookalike Check
        merchant_risk, merchant_reason, merchant_info = evaluate_merchant(req.payee)
        if merchant_risk > 0:
            risk_score += merchant_risk
            if merchant_reason:
                reasons.append(merchant_reason)

        # Factor C: Whitelist Verification
        allowed_normalized = [p.lower() for p in intent.allowed_payees]
        if req.payee.lower() not in allowed_normalized:
            if not merchant_info or not merchant_info.is_verified:
                risk_score += 0.40
                reasons.append(f"Payee '{req.payee}' is not in your allowed merchant list.")
            else:
                risk_score += 0.10
                reasons.append(f"Payee '{req.payee}' is verified, but not explicitly whitelisted in intent.")

        # Factor D: Minor Budget Margin (1% to 15% overage)
        if req.amount > intent.max_amount:
            risk_score += 0.30
            reasons.append(f"Requested amount ₹{req.amount:,.2f} is slightly above base limit ₹{intent.max_amount:,.2f}.")

        # Factor E: Runaway Loop / Duplicate Detection (same payee and amount in recent requests)
        recent_matches = [
            r for r in self.request_history[-5:]
            if r.payee == req.payee and r.amount == req.amount and r.intent_id == req.intent_id
        ]
        if recent_matches:
            risk_score += 0.60
            reasons.append("Runaway loop detected: Agent is repeatedly attempting identical payments.")

        # Record into history
        self.request_history.append(req)

        # Clamp risk score
        risk_score = min(max(risk_score, 0.0), 1.0)
        risk_score = round(risk_score, 2)

        # -------------------------------------------------------------
        # DECISION THRESHOLDS
        # -------------------------------------------------------------
        if risk_score > policy.ask_user_threshold:
            decision = DecisionEnum.BLOCK
            primary_reason = reasons[0] if reasons else "High cumulative risk detected"
            user_msg = f"BLOCKED: {primary_reason}."
        elif risk_score >= policy.auto_approve_threshold:
            decision = DecisionEnum.ASK_USER
            primary_reason = reasons[0] if reasons else "Borderline parameters"
            user_msg = f"CONFIRMATION REQUIRED: {primary_reason}. Would you like to authorize ₹{req.amount:,.2f} to {req.payee}?"
        else:
            decision = DecisionEnum.APPROVE
            user_msg = f"APPROVED: Verified payment of ₹{req.amount:,.2f} to {req.payee} matches your authorized intent."

        return DecisionOutput(
            request_id=req.request_id,
            decision=decision,
            risk_score=risk_score,
            reasons=reasons if reasons else ["Request matches authorized intent parameters perfectly."],
            user_message=user_msg,
            timestamp=now
        )

firewall_engine = PaymentFirewallEngine()
