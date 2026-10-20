import hashlib
import json
import time
from typing import List, Dict, Any, Tuple

class AuditBlock:
    def __init__(self, index: int, timestamp: float, event_type: str, payload: Dict[str, Any], prev_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.event_type = event_type
        self.payload = payload
        self.prev_hash = prev_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        data = f"{self.index}:{self.timestamp}:{self.event_type}:{json.dumps(self.payload, sort_keys=True, default=str)}:{self.prev_hash}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

class AuditChain:
    """
    Append-only, tamper-evident hash-chained audit trail.
    Every intent, payment evaluation, and policy change is permanently anchored.
    """
    def __init__(self):
        self.chain: List[AuditBlock] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = AuditBlock(
            index=0,
            timestamp=time.time(),
            event_type="GENESIS",
            payload={"message": "IntentGuard Security Audit Trail Initialized (Citi & NPCI DRUNIX)"},
            prev_hash="0" * 64,
        )
        self.chain.append(genesis)

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        prev = self.chain[-1]
        block = AuditBlock(
            index=len(self.chain),
            timestamp=time.time(),
            event_type=event_type,
            payload=payload,
            prev_hash=prev.hash,
        )
        self.chain.append(block)
        return block.to_dict()

    def verify_integrity(self) -> Tuple[bool, str]:
        """Validates that no block has been altered and that all prev_hashes match."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.prev_hash != prev.hash:
                return False, f"Broken chain link at block {curr.index}: prev_hash mismatch"
            if curr.hash != curr.compute_hash():
                return False, f"Tampered data detected at block {curr.index}: invalid hash"
        return True, "Chain integrity verified (100% valid)"

    def get_trail(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.chain]

audit_log = AuditChain()
