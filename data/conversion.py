"""Automatic conversion detection — match active leads against Redshift transactions."""

from data.redshift import (
    get_esim_transactions,
    get_future_fund_transactions,
    get_quick_transactions,
    get_reserve_audience,
    get_tapi_transactions,
)
from data.supabase_client import get_leads, update_lead_status

PRODUCT_TXN_FETCHERS: dict[str, callable] = {
    "quick": get_quick_transactions,
    "future_fund": get_future_fund_transactions,
    "tapi": get_tapi_transactions,
    "esim": get_esim_transactions,
}


def run_conversion_check() -> list[dict]:
    """Compare active leads against transaction data and auto-convert matches.

    For most products a lead is converted when the user's cr_code appears in
    the product's transaction set.  For *reserve* the logic is inverted: a user
    converts (enrolls) when they *leave* the reserve audience.

    Returns the list of leads that were newly marked as Converted.
    """
    all_leads = get_leads()
    active_leads = [l for l in all_leads if l["status"] in ("Qualified", "Contacted")]

    if not active_leads:
        return []

    txn_cache: dict[str, set] = {
        product: fetcher() for product, fetcher in PRODUCT_TXN_FETCHERS.items()
    }

    reserve_audience = get_reserve_audience()

    converted: list[dict] = []
    for lead in active_leads:
        product = lead["product"]
        cr_code = lead["cr_code"]

        if product == "reserve":
            # User enrolled → they disappear from the "eligible + not enrolled" audience
            if cr_code not in reserve_audience:
                update_lead_status(lead["id"], "Converted")
                converted.append(lead)
        else:
            txn_set = txn_cache.get(product)
            if txn_set and cr_code in txn_set:
                update_lead_status(lead["id"], "Converted")
                converted.append(lead)

    return converted
