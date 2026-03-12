"""My Leads — View and manage leads submitted by the current agent."""

from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="My Leads", page_icon=":clipboard:", layout="wide")

from data.supabase_client import get_leads, update_lead_status
from eligibility.products import PRODUCT_KEYS, PRODUCT_NAMES
from shared import render_sidebar

render_sidebar()


def open_table_shell():
    st.markdown('<div class="ontop-table-shell">', unsafe_allow_html=True)


def close_shell():
    st.markdown("</div>", unsafe_allow_html=True)


def render_table(df: pd.DataFrame):
    st.markdown(
        df.to_html(index=False, classes="ontop-html-table", border=0, escape=False),
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> str:
    tones = {
        "Qualified": "green",
        "Contacted": "purple",
        "Converted": "coral",
        "Rejected": "gray",
        "Expired": "amber",
    }
    tone = tones.get(status, "gray")
    return f'<span class="ontop-status-badge ontop-status-{tone}">{status}</span>'


def format_cr_code(cr_code: str) -> str:
    return f"<strong>{cr_code}</strong>"


def format_notes(notes: str) -> str:
    if not notes:
        return '<span style="color:#6B6B7E;">No notes</span>'
    compact = " ".join(str(notes).split())
    if len(compact) <= 72:
        return compact
    short = compact[:69].rstrip()
    return f'<span title="{compact}">{short}...</span>'


def format_date_cell(raw_value: str) -> str:
    created_at = pd.to_datetime(raw_value, utc=True)
    age_days = (datetime.now(timezone.utc) - created_at.to_pydatetime()).days
    age_text = "Today" if age_days <= 0 else f"{age_days}d ago"
    return (
        f"{created_at.strftime('%Y-%m-%d %H:%M')}"
        f"<br><span style='color:#6B6B7E;font-size:0.78rem;'>{age_text}</span>"
    )


def reset_filters():
    st.session_state["my_leads_product_filter"] = "All"
    st.session_state["my_leads_status_filter"] = "All"
    st.session_state["my_leads_start_date"] = date.today() - timedelta(days=30)
    st.session_state["my_leads_end_date"] = date.today()
    st.session_state["my_leads_search_filter"] = ""

st.markdown(
    """
    <section class="ontop-hero">
        <span class="ontop-eyebrow">My Leads</span>
        <h2>Track your active pipeline and update lead outcomes without losing context.</h2>
        <p>Filter by product, status, and time period to review the opportunities currently assigned to you.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

agent_name = st.session_state["agent_name"]
agent_email = st.session_state["agent_email"]

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

col1, col2, col3, col4, col5 = st.columns([1.1, 1.1, 1.05, 1.35, 0.7], vertical_alignment="bottom")

with col1:
    product_filter = st.selectbox(
        "Product",
        options=["All"] + PRODUCT_KEYS,
        format_func=lambda x: "All Products" if x == "All" else PRODUCT_NAMES.get(x, x),
        key="my_leads_product_filter",
    )

with col2:
    status_filter = st.selectbox(
        "Status",
        options=["All", "Qualified", "Contacted", "Converted", "Rejected", "Expired"],
        key="my_leads_status_filter",
    )

with col3:
    start_date = st.date_input(
        "Start Date",
        value=st.session_state.get("my_leads_start_date", date.today() - timedelta(days=30)),
        key="my_leads_start_date",
    )

with col4:
    end_date = st.date_input(
        "End Date",
        value=st.session_state.get("my_leads_end_date", date.today()),
        key="my_leads_end_date",
    )

with col5:
    search_filter = st.text_input(
        "Find lead",
        placeholder="CR code, note, or product",
        key="my_leads_search_filter",
    )

filter_action_col, filter_button_col = st.columns([4.4, 0.8], vertical_alignment="bottom")
with filter_button_col:
    if st.button("Clear", use_container_width=True):
        reset_filters()
        st.rerun()

if start_date > end_date:
    st.warning("Start Date cannot be later than End Date.")
    st.stop()

# ---------------------------------------------------------------------------
# Fetch leads
# ---------------------------------------------------------------------------

leads = get_leads(
    agent_name=agent_name,
    agent_email=agent_email,
    product=product_filter if product_filter != "All" else None,
    status=status_filter if status_filter != "All" else None,
)

if not leads:
    st.info("No leads found for the selected filters.")
    st.stop()

df = pd.DataFrame(leads)
base_df = df.copy()
df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
base_df["created_at"] = pd.to_datetime(base_df["created_at"], utc=True)

start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
date_mask = (df["created_at"] >= start_ts.tz_localize("UTC")) & (df["created_at"] <= end_ts.tz_localize("UTC"))
base_date_mask = (base_df["created_at"] >= start_ts.tz_localize("UTC")) & (base_df["created_at"] <= end_ts.tz_localize("UTC"))
df = df[date_mask].copy()
base_df = base_df[base_date_mask].copy()

# Display-friendly columns
df["product_name"] = df["product"].map(PRODUCT_NAMES)
base_df["product_name"] = base_df["product"].map(PRODUCT_NAMES)

if search_filter:
    search_mask = (
        df["cr_code"].fillna("").str.contains(search_filter, case=False, na=False)
        | df["product_name"].fillna("").str.contains(search_filter, case=False, na=False)
        | df["notes"].fillna("").str.contains(search_filter, case=False, na=False)
    )
    df = df[search_mask].copy()

if df.empty:
    st.info("No leads match the current filters and search term.")
    st.stop()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

active_count = len(base_df[base_df["status"].isin(["Qualified", "Contacted"])])
closed_count = len(base_df[base_df["status"].isin(["Converted", "Rejected", "Expired"])])
recent_converted = len(
    base_df[
        (base_df["status"] == "Converted")
        & (pd.to_datetime(base_df["created_at"], utc=True) >= (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)))
    ]
)
needs_follow_up = len(
    base_df[
        (base_df["status"].isin(["Qualified", "Contacted"]))
        & (pd.to_datetime(base_df["created_at"], utc=True) < (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=14)))
    ]
)

st.markdown(
    f"""
    <div class="ontop-mini-stats">
        <div class="ontop-mini-stat ontop-mini-stat-purple">
            <span>Open</span>
            <strong>{active_count}</strong>
        </div>
        <div class="ontop-mini-stat">
            <span>Need Follow-up</span>
            <strong>{needs_follow_up}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-green">
            <span>Converted (30d)</span>
            <strong>{recent_converted}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"Closed leads available: {closed_count}. Use filters or search to narrow the list further.")

# ---------------------------------------------------------------------------
# Leads table
# ---------------------------------------------------------------------------

lead_options = {
    f"{row['cr_code']} — {PRODUCT_NAMES.get(row['product'], row['product'])} ({row['status']})": row["id"]
    for _, row in df.iterrows()
}

st.markdown(
    """
    <div class="ontop-toolbar">
        <div class="ontop-toolbar-copy">
            <h3>Lead Details</h3>
            <p>Review notes and status, then update a selected lead.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if lead_options:
    action_c1, action_c2, action_c3 = st.columns([2.6, 1.2, 0.8], vertical_alignment="bottom")
    with action_c1:
        selected_label = st.selectbox(
            "Lead",
            options=list(lead_options.keys()),
            label_visibility="collapsed",
        )
    with action_c2:
        new_status = st.selectbox(
            "Status",
            options=["Qualified", "Contacted", "Converted", "Rejected", "Expired"],
            label_visibility="collapsed",
        )
    with action_c3:
        update_clicked = st.button("Update", type="primary", use_container_width=True)
else:
    update_clicked = False

display_df = pd.DataFrame(
    {
        "CR Code": df["cr_code"].map(format_cr_code),
        "Product": df["product_name"],
        "Status": df["status"].map(render_status_badge),
        "Notes": df["notes"].map(format_notes),
        "Date": df["created_at"].map(format_date_cell),
    }
)

open_table_shell()
render_table(display_df.fillna(""))
close_shell()

if lead_options and update_clicked:
    lead_id = lead_options[selected_label]
    update_lead_status(lead_id, new_status)
    st.session_state["leads_feedback"] = f"Lead updated to {new_status}."
    st.rerun()

if st.session_state.get("leads_feedback"):
    st.toast(st.session_state.pop("leads_feedback"))
