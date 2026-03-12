"""My Leads — View and manage leads submitted by the current agent."""

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

col1, col2, col3 = st.columns(3)

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Filters</p>
        <h3 class="ontop-section-title">Refine your pipeline view</h3>
        <p>Narrow the list to focus on the products and time ranges that need action.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with col1:
    product_filter = st.selectbox(
        "Product",
        options=["All"] + PRODUCT_KEYS,
        format_func=lambda x: "All Products" if x == "All" else PRODUCT_NAMES.get(x, x),
    )

with col2:
    status_filter = st.selectbox(
        "Status",
        options=["All", "Qualified", "Contacted", "Converted", "Rejected", "Expired"],
    )

with col3:
    days_filter = st.selectbox(
        "Time Period",
        options=[7, 30, 90, 365],
        format_func=lambda d: f"Last {d} days",
        index=1,
    )

# ---------------------------------------------------------------------------
# Fetch leads
# ---------------------------------------------------------------------------

leads = get_leads(
    agent_name=agent_name,
    agent_email=agent_email,
    product=product_filter if product_filter != "All" else None,
    status=status_filter if status_filter != "All" else None,
    days=days_filter,
)

if not leads:
    st.info("No leads found for the selected filters.")
    st.stop()

df = pd.DataFrame(leads)

# Display-friendly columns
df["product_name"] = df["product"].map(PRODUCT_NAMES)
df["created"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Summary</p>
        <h3 class="ontop-section-title">Lead volume and status mix</h3>
        <p>Use the metrics below to understand your current workload and recent movement.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.metric("Total Leads", len(df))

status_counts = df["status"].value_counts()
scols = st.columns(5)
for i, status in enumerate(["Qualified", "Contacted", "Converted", "Rejected", "Expired"]):
    with scols[i]:
        st.metric(status, status_counts.get(status, 0))

st.divider()

# ---------------------------------------------------------------------------
# Leads table
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Lead Details</p>
        <h3 class="ontop-section-title">Review every lead in the current result set</h3>
        <p>Check notes and current status before making updates.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

display_df = df[["cr_code", "product_name", "status", "notes", "created"]].rename(
    columns={
        "cr_code": "CR Code",
        "product_name": "Product",
        "status": "Status",
        "notes": "Notes",
        "created": "Date",
    }
)

open_table_shell()
render_table(display_df.fillna(""))
close_shell()

# ---------------------------------------------------------------------------
# Status update
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Update Workflow</p>
        <h3 class="ontop-section-title">Change the status of an existing lead</h3>
        <p>Select the lead to update and apply the new outcome.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

lead_options = {
    f"{row['cr_code']} — {PRODUCT_NAMES.get(row['product'], row['product'])} ({row['status']})": row["id"]
    for _, row in df.iterrows()
}

if lead_options:
    selected_label = st.selectbox("Select a lead", options=list(lead_options.keys()))
    new_status = st.selectbox(
        "New status",
        options=["Qualified", "Contacted", "Converted", "Rejected", "Expired"],
    )
    if st.button("Update Status", type="primary"):
        lead_id = lead_options[selected_label]
        update_lead_status(lead_id, new_status)
        st.success(f"Updated to **{new_status}**")
        st.rerun()
