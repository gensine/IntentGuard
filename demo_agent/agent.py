import httpx
from typing import Dict, Any, List

class ShoppingAgent:
    """
    Simulates an autonomous AI shopping / travel booking agent.
    Demonstrates how real-world agent frameworks (LangChain, AutoGen, LlamaIndex)
    integrate with the IntentGuard payment verification layer.
    """
    def __init__(self, firewall_url: str = "http://127.0.0.1:8000"):
        self.firewall_url = firewall_url
        self.client = httpx.Client(base_url=firewall_url, timeout=10.0)

    def attempt_payment(
        self,
        request_id: str,
        intent_id: str,
        payee: str,
        amount: float,
        description: str,
        context_sources: List[str]
    ) -> Dict[str, Any]:
        """
        Agent attempts to pay. By architectural design, the agent CANNOT access
        the UPI rail directly. It must query the firewall.
        """
        payload = {
            "request_id": request_id,
            "intent_id": intent_id,
            "payee": payee,
            "amount": amount,
            "currency": "INR",
            "description": description,
            "raw_context_sources": context_sources
        }
        res = self.client.post("/payments/verify", json=payload)
        return res.json()
