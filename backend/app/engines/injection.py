import re
from typing import List, Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(the\s+)?previous",
    r"system\s*:\s*pay",
    r"new\s+instruction\s*:",
    r"pay\s+(this\s+)?upi",
    r"override\s+(intent|limit|payment)",
    r"emergency\s+transfer",
    r"send\s+(money|funds|inr|rs\.?)\s+(to|now)",
    r"<!--.*ignore.*-->",
    r"urgent\s+security\s+update\s+fee"
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def detect_prompt_injection(context_sources: List[str]) -> Tuple[bool, float, List[str]]:
    """
    Examines context traces provided by the AI agent (e.g., text extracted from web pages).
    Identifies if an untrusted payload attempted to hijack the agent's payment behavior.
    """
    flags = []
    max_risk = 0.0

    for source in context_sources:
        for pattern in COMPILED_PATTERNS:
            match = pattern.search(source)
            if match:
                matched_phrase = match.group(0)
                flags.append(f"Prompt injection detected in untrusted content: '{matched_phrase}'")
                max_risk = max(max_risk, 0.85)

    is_injected = len(flags) > 0
    return is_injected, max_risk, flags
