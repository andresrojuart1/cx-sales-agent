"""Dashboard — Performance overview and team stats."""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide")

from data.conversion import run_conversion_check
from data.supabase_client import expire_stale_leads, get_leads
from eligibility.products import PRODUCT_NAMES
from shared import render_sidebar

render_sidebar()

st.header("Dashboard")

# ---------------------------------------------------------------------------
# Conversion & expiration check
# ---------------------------------------------------------------------------

if st.button("Check Conversions", type="secondary"):
    with st.spinner("Matching leads against transactions..."):
        converted = run_conversion_check()
        expired = expire_stale_leads()
    if converted:
        st.success(f"Auto-converted {len(converted)} lead(s)!")
    if expired:
        st.info(f"Expired {expired} stale lead(s) (>60 days, not converted)")
    if not converted and not expired:
        st.info("No new conversions or expirations detected.")
    st.rerun()

# ---------------------------------------------------------------------------
# Time period selector
# ---------------------------------------------------------------------------

days = st.selectbox(
    "Time Period",
    options=[7, 30, 90, 365],
    format_func=lambda d: f"Last {d} days",
    index=1,
)

# Fetch all leads (no agent filter = team-wide)
all_leads = get_leads(days=days)

if not all_leads:
    st.info("No leads recorded yet.")
    st.stop()

df = pd.DataFrame(all_leads)
df["product_name"] = df["product"].map(PRODUCT_NAMES)
df["created_at"] = pd.to_datetime(df["created_at"])
df["date"] = df["created_at"].dt.date

# ---------------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------------

total = len(df)
converted = len(df[df["status"] == "Converted"])
expired = len(df[df["status"] == "Expired"])
active = len(df[df["status"].isin(["Qualified", "Contacted"])])
conversion_rate = (converted / total * 100) if total > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Leads", total)
col2.metric("Active", active)
col3.metric("Converted", converted)
col4.metric("Conversion Rate", f"{conversion_rate:.1f}%")
col5.metric("Expired", expired)

st.divider()

# ---------------------------------------------------------------------------
# Leads by product
# ---------------------------------------------------------------------------

st.subheader("Leads by Product")

product_stats = (
    df.groupby("product_name")
    .agg(
        total=("id", "count"),
        converted=("status", lambda s: (s == "Converted").sum()),
    )
    .reset_index()
)
product_stats["conversion_rate"] = (
    product_stats["converted"] / product_stats["total"] * 100
).round(1)

st.bar_chart(product_stats.set_index("product_name")["total"])

st.dataframe(
    product_stats.rename(
        columns={
            "product_name": "Product",
            "total": "Total Leads",
            "converted": "Converted",
            "conversion_rate": "Conversion %",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Leads by agent
# ---------------------------------------------------------------------------

st.subheader("Leads by Agent")

agent_stats = (
    df.groupby("agent_name")
    .agg(
        total=("id", "count"),
        converted=("status", lambda s: (s == "Converted").sum()),
    )
    .reset_index()
    .sort_values("total", ascending=False)
)
agent_stats["conversion_rate"] = (
    agent_stats["converted"] / agent_stats["total"] * 100
).round(1)

st.dataframe(
    agent_stats.rename(
        columns={
            "agent_name": "Agent",
            "total": "Total Leads",
            "converted": "Converted",
            "conversion_rate": "Conversion %",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Leads over time
# ---------------------------------------------------------------------------

st.subheader("Leads Over Time")

daily = df.groupby("date").size().reset_index(name="leads")
daily = daily.set_index("date")

st.line_chart(daily["leads"])

# ---------------------------------------------------------------------------
# Status breakdown
# ---------------------------------------------------------------------------

st.subheader("Status Breakdown")

status_df = df["status"].value_counts().reset_index()
status_df.columns = ["Status", "Count"]

st.bar_chart(status_df.set_index("Status")["Count"])
