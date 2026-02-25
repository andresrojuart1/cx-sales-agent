"""Supabase connection for audiences, risk matrix, and lead storage."""

from datetime import datetime, timedelta, timezone

import streamlit as st
from supabase import create_client


def get_client():
    """Create a Supabase client from st.secrets."""
    cfg = st.secrets["supabase"]
    return create_client(cfg["url"], cfg["key"])


# ---------------------------------------------------------------------------
# Audience data (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Loading Quick audience...")
def get_quick_audience() -> set:
    """All CR_Code values from the quick_audience table."""
    client = get_client()
    result = client.table("quick_audience").select("CR_Code").execute()
    return {row["CR_Code"] for row in result.data if row["CR_Code"]}


@st.cache_data(ttl=3600, show_spinner="Loading Future Fund audience...")
def get_ff_audience() -> set:
    """All CR_Code values from the ff_audience table."""
    client = get_client()
    result = client.table("ff_audience").select("CR_Code").execute()
    return {row["CR_Code"] for row in result.data if row["CR_Code"]}


@st.cache_data(ttl=3600, show_spinner="Loading risk matrix...")
def get_risk_matrix_rejected() -> set:
    """All des_email values where decision is 'Not approved'."""
    client = get_client()
    result = (
        client.table("risk_matrix")
        .select("des_email")
        .eq("decision", "Not approved")
        .execute()
    )
    return {row["des_email"].lower() for row in result.data if row["des_email"]}


# ---------------------------------------------------------------------------
# Lead operations (not cached)
# ---------------------------------------------------------------------------

_CX_LEADS_TABLE = "cx_leads"


def save_lead(
    cr_code: str,
    product: str,
    agent_name: str,
    notes: str = "",
    agent_email: str = "",
) -> dict:
    """Insert a new qualified lead. Returns the inserted row."""
    client = get_client()
    row = {
        "cr_code": cr_code,
        "product": product,
        "agent_name": agent_name,
        "agent_email": agent_email,
        "notes": notes,
        "status": "Qualified",
    }
    result = client.table(_CX_LEADS_TABLE).insert(row).execute()
    return result.data[0] if result.data else {}


_LOCK_WINDOW_DAYS = 60


def check_opportunity_lock(cr_code: str, product: str) -> dict | None:
    """Check if an active lead locks this cr_code+product (60-day window).

    Returns the blocking lead dict if locked, or None if the opportunity is
    available.  Active means status in ('Qualified', 'Contacted').
    """
    client = get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_LOCK_WINDOW_DAYS)).isoformat()
    result = (
        client.table(_CX_LEADS_TABLE)
        .select("id, agent_name, agent_email, status, created_at")
        .eq("cr_code", cr_code)
        .eq("product", product)
        .in_("status", ["Qualified", "Contacted"])
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def expire_stale_leads() -> int:
    """Set status='Expired' on active leads older than the lock window.

    Returns the number of leads expired.
    """
    client = get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_LOCK_WINDOW_DAYS)).isoformat()
    result = (
        client.table(_CX_LEADS_TABLE)
        .update({"status": "Expired"})
        .in_("status", ["Qualified", "Contacted"])
        .lt("created_at", cutoff)
        .execute()
    )
    return len(result.data)


def get_leads(
    agent_name: str | None = None,
    agent_email: str | None = None,
    product: str | None = None,
    status: str | None = None,
    days: int | None = None,
) -> list[dict]:
    """Fetch leads with optional filters. Returns list of dicts."""
    client = get_client()
    query = client.table(_CX_LEADS_TABLE).select("*").order("created_at", desc=True)

    if agent_email:
        # Match by email (new leads) OR by name (legacy leads without email)
        query = query.or_(f"agent_email.eq.{agent_email},agent_name.eq.{agent_name}")
    elif agent_name:
        query = query.eq("agent_name", agent_name)
    if product:
        query = query.eq("product", product)
    if status:
        query = query.eq("status", status)
    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = query.gte("created_at", cutoff)

    result = query.execute()
    return result.data


def update_lead_status(lead_id: str, new_status: str) -> dict:
    """Update the status of an existing lead."""
    client = get_client()
    result = (
        client.table(_CX_LEADS_TABLE)
        .update({"status": new_status})
        .eq("id", lead_id)
        .execute()
    )
    return result.data[0] if result.data else {}
