from typing import Dict, Optional, Tuple
from app.models.schemas import MerchantInfo

# Known verified merchants in the national registry
KNOWN_MERCHANTS: Dict[str, MerchantInfo] = {
    "irctc@upi": MerchantInfo(vpa="irctc@upi", name="IRCTC Official", category="transport.rail", is_verified=True, complaint_count=0, trust_score=0.99),
    "swiggy@icici": MerchantInfo(vpa="swiggy@icici", name="Swiggy Delivery", category="food.delivery", is_verified=True, complaint_count=1, trust_score=0.96),
    "amazon@apl": MerchantInfo(vpa="amazon@apl", name="Amazon India", category="ecommerce.retail", is_verified=True, complaint_count=2, trust_score=0.97),
    "zomato@hdfc": MerchantInfo(vpa="zomato@hdfc", name="Zomato India", category="food.delivery", is_verified=True, complaint_count=0, trust_score=0.98),
    "uber@axisbank": MerchantInfo(vpa="uber@axisbank", name="Uber Rides", category="transport.cab", is_verified=True, complaint_count=1, trust_score=0.95),
    "makemytrip@icici": MerchantInfo(vpa="makemytrip@icici", name="MakeMyTrip Travels", category="travel.flight", is_verified=True, complaint_count=0, trust_score=0.98),
}

def string_similarity(s1: str, s2: str) -> float:
    """Calculate character-level similarity between two merchant handles."""
    s1, s2 = s1.lower().split("@")[0], s2.lower().split("@")[0]
    if s1 == s2:
        return 1.0
    
    # Calculate simple bigram overlap Dice coefficient
    pairs1 = {s1[i:i+2] for i in range(len(s1)-1)}
    pairs2 = {s2[i:i+2] for i in range(len(s2)-1)}
    
    if not pairs1 or not pairs2:
        return 0.0
    intersection = len(pairs1 & pairs2)
    return (2.0 * intersection) / (len(pairs1) + len(pairs2))

def evaluate_merchant(vpa: str) -> Tuple[float, Optional[str], Optional[MerchantInfo]]:
    """
    Evaluates merchant trust and lookalike risk.
    Returns: (risk_penalty, warning_reason, merchant_info)
    """
    vpa_lower = vpa.lower().strip()
    
    # Exact verified match
    if vpa_lower in KNOWN_MERCHANTS:
        info = KNOWN_MERCHANTS[vpa_lower]
        return 0.0, None, info

    # Lookalike check against known brands (e.g. 'irctc-booking@upi' or 'irctcc@upi' vs 'irctc@upi')
    handle = vpa_lower.split("@")[0]
    for known_vpa, info in KNOWN_MERCHANTS.items():
        known_handle = known_vpa.split("@")[0]
        sim = string_similarity(vpa_lower, known_vpa)
        # Check either high bigram similarity or brand name embedded in unfamiliar handle
        if (0.40 <= sim < 1.0) or (len(known_handle) >= 4 and (known_handle in handle or handle in known_handle)):
            return 0.75, f"Lookalike/Typosquatting alert: Payee '{vpa}' suspiciously imitates verified brand '{info.name}' ({known_vpa})", None

    # Completely unverified newly seen merchant
    return 0.35, f"Payee '{vpa}' is not on the verified merchant registry", None
