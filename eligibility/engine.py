"""Core eligibility logic — determines which products a user can be offered."""

from dataclasses import dataclass

from data.redshift import (
    get_all_active_contractors,
    get_esim_transactions,
    get_future_fund_transactions,
    get_quick_transactions,
    get_reserve_audience,
    get_tapi_segment,
    get_tapi_transactions,
)
from data.supabase_client import get_ff_audience, get_quick_audience, get_risk_matrix_rejected
from eligibility.products import PRODUCT_KEYS


@dataclass
class EligibilityResult:
    status: str  # "ELIGIBLE", "ALREADY_USING", "NOT_ELIGIBLE"
    reason: str  # Human-readable explanation


def get_user_eligibility(cr_code: str, user_email: str | None = None) -> dict[str, EligibilityResult]:
    """
    Return eligibility status for every product given a contractor code.

    Args:
        cr_code: The contractor's CR code (e.g. "CR034116").
        user_email: The contractor's email (needed for Quick risk matrix check).

    Returns:
        Dict mapping product key -> EligibilityResult.
    """
    results = {}

    # --- Quick ---
    quick_audience = get_quick_audience()
    quick_txns = get_quick_transactions()

    if cr_code in quick_txns:
        results["quick"] = EligibilityResult("ALREADY_USING", "Already has Quick transactions")
    elif cr_code not in quick_audience:
        results["quick"] = EligibilityResult("NOT_ELIGIBLE", "Not in Quick audience")
    else:
        # Check risk matrix via email
        if user_email:
            rejected_emails = get_risk_matrix_rejected()
            if user_email.lower() in rejected_emails:
                results["quick"] = EligibilityResult("NOT_ELIGIBLE", "Risk matrix: Not approved")
            else:
                results["quick"] = EligibilityResult("ELIGIBLE", "In audience, approved by risk matrix")
        else:
            results["quick"] = EligibilityResult("ELIGIBLE", "In audience (no email for risk check)")

    # --- Future Fund ---
    ff_audience = get_ff_audience()
    ff_txns = get_future_fund_transactions()

    if cr_code in ff_txns:
        results["future_fund"] = EligibilityResult("ALREADY_USING", "Already has Future Fund transactions")
    elif cr_code not in ff_audience:
        results["future_fund"] = EligibilityResult("NOT_ELIGIBLE", "Not in Future Fund audience")
    else:
        results["future_fund"] = EligibilityResult("ELIGIBLE", "In audience, no existing transactions")

    # --- Tapi ---
    tapi_segment = get_tapi_segment()
    tapi_txns = get_tapi_transactions()

    if cr_code in tapi_txns:
        results["tapi"] = EligibilityResult("ALREADY_USING", "Already has Tapi transactions")
    elif cr_code not in tapi_segment:
        results["tapi"] = EligibilityResult("NOT_ELIGIBLE", "Not in Tapi segment")
    else:
        results["tapi"] = EligibilityResult("ELIGIBLE", "In segment, no existing transactions")

    # --- E-Sim ---
    active_contractors = get_all_active_contractors()
    esim_txns = get_esim_transactions()

    if cr_code in esim_txns:
        results["esim"] = EligibilityResult("ALREADY_USING", "Already has e-Sim transactions")
    elif cr_code not in active_contractors:
        results["esim"] = EligibilityResult("NOT_ELIGIBLE", "Not an active contractor")
    else:
        results["esim"] = EligibilityResult("ELIGIBLE", "Active contractor, no existing e-Sim")

    # --- Reserve ---
    reserve_aud = get_reserve_audience()

    if cr_code in reserve_aud:
        results["reserve"] = EligibilityResult("ELIGIBLE", "Eligible for Reserve, not yet enrolled")
    else:
        results["reserve"] = EligibilityResult("NOT_ELIGIBLE", "Not in Reserve audience or already enrolled")

    return results


def count_eligible(cr_code: str, eligibility: dict[str, EligibilityResult]) -> int:
    """Count how many products the user is eligible for."""
    return sum(1 for r in eligibility.values() if r.status == "ELIGIBLE")
