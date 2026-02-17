"""Supabase connection for audiences, risk matrix, and lead storage."""

import os
from datetime import datetime, timedelta, timezone

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_client():
    """Create a Supabase client from env vars."""
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


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


def check_duplicate_lead(cr_code: str, product: str, window_days: int = 30) -> bool:
    """Return True if a lead already exists for this user+product within the window."""
    client = get_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    result = (
        client.table(_CX_LEADS_TABLE)
        .select("id")
        .eq("cr_code", cr_code)
        .eq("product", product)
        .gte("created_at", cutoff)
        .limit(1)
        .execute()
    )
    return len(result.data) > 0


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
