from math import exp

# Small category weight modifiers
CATEGORY_WEIGHTS = {
    "supplier": 1.00,
    "distributor": 0.97,
    "dealer": 0.95,
    "gold": 1.05,
    "silver": 1.02,
}

def compute_score(on_time_delivery_rate: float,
                  complaint_count: int,
                  missing_documents: bool,
                  compliance_score: float,
                  category: str) -> float:
    """
    Deterministic scoring function that returns a float in [0, 100].
    - on_time_delivery_rate and compliance_score are percentages (0-100).
    - complaint_count reduces score with diminishing returns.
    - missing_documents applies a fixed penalty.
    - category adjusts the final score slightly.
    """

    # baseline
    baseline = 30.0

    # on-time delivery contributes up to +40 points
    on_time_contrib = (on_time_delivery_rate / 100.0) * 40.0

    # compliance contributes up to +25 points
    compliance_contrib = (compliance_score / 100.0) * 25.0

    # complaints penalty: saturating penalty with diminishing returns (max 20)
    complaints_penalty = min(20.0, 5.0 * (1 - exp(-complaint_count / 5.0)))

    # missing documents penalty
    missing_penalty = 15.0 if missing_documents else 0.0

    raw_score = baseline + on_time_contrib + compliance_contrib - complaints_penalty - missing_penalty

    weight = CATEGORY_WEIGHTS.get(category.lower(), 1.0)
    adjusted = raw_score * weight

    final = max(0.0, min(100.0, round(adjusted, 2)))
    return final
