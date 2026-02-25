"""My Leads — View and manage leads submitted by the current agent."""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="My Leads", page_icon=":clipboard:", layout="wide")

from data.supabase_client import get_leads, update_lead_status
from eligibility.products import PRODUCT_KEYS, PRODUCT_NAMES
from shared import render_sidebar

render_sidebar()

st.header("My Leads")

agent_name = st.session_state["agent_name"]
agent_email = st.session_state["agent_email"]

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

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

st.subheader("Lead Details")

display_df = df[["cr_code", "product_name", "status", "notes", "created"]].rename(
    columns={
        "cr_code": "CR Code",
        "product_name": "Product",
        "status": "Status",
        "notes": "Notes",
        "created": "Date",
    }
)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Status update
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Update Lead Status")

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
