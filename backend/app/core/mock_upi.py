import uuid
import time
from typing import Dict, Any

class MockUPIRail:
    """
    Simulates an NPCI/UPI PSP payment gateway sandbox.
    Only callable when IntentGuard issues an APPROVE decision.
    """
    def execute_payment(self, payee: str, amount: float, description: str) -> Dict[str, Any]:
        txn_id = f"UPI{int(time.time())}{uuid.uuid4().hex[:6].upper()}"
        rrn = f"NPCI{uuid.uuid4().hex[:12].upper()}"
        return {
            "status": "SUCCESS",
            "txn_id": txn_id,
            "rrn": rrn,
            "payee": payee,
            "amount": amount,
            "currency": "INR",
            "message": "Payment cleared via NPCI Sandbox Rail",
            "cleared_at": time.time()
        }

mock_upi = MockUPIRail()
