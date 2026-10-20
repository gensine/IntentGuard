import json
from cryptography.hazmat.primitives.asymmetric import ed25519
from typing import Dict, Any

class IntentSigner:
    """
    Cryptographic signer for User Intents using Ed25519.
    Guarantees non-repudiation and prevents the AI agent from tampering with
    critical authorization parameters (max_amount, valid_until, allowed_payees).
    """
    def __init__(self):
        # Generate persistent in-process keypair for the firewall
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def _canonical_bytes(self, intent_dict: Dict[str, Any]) -> bytes:
        # Strip mutable / metadata keys before computing signature
        canonical_dict = {
            k: v for k, v in intent_dict.items()
            if k not in ("signature", "is_revoked", "is_confirmed")
        }
        return json.dumps(canonical_dict, sort_keys=True, default=str).encode("utf-8")

    def sign_intent(self, intent_dict: Dict[str, Any]) -> str:
        payload = self._canonical_bytes(intent_dict)
        signature = self.private_key.sign(payload)
        return signature.hex()

    def verify_intent(self, intent_dict: Dict[str, Any], sig_hex: str) -> bool:
        if not sig_hex:
            return False
        payload = self._canonical_bytes(intent_dict)
        try:
            self.public_key.verify(bytes.fromhex(sig_hex), payload)
            return True
        except Exception:
            return False

# Global singleton signer instance
signer = IntentSigner()
