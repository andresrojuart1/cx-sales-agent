"""Dashboard — Performance overview and team stats."""

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide")

from data.conversion import run_conversion_check
from data.supabase_client import expire_stale_leads, get_leads
from eligibility.products import PRODUCT_NAMES
from shared import render_sidebar

render_sidebar()


ONTOp_COLORS = ["#261C94", "#E35276", "#7C73F7", "#F38BA3", "#B8B8C8"]


def open_shell(shell_class: str):
    st.markdown(f'<div class="{shell_class}">', unsafe_allow_html=True)


def close_shell():
    st.markdown("</div>", unsafe_allow_html=True)


def base_chart(data: pd.DataFrame) -> alt.Chart:
    return alt.Chart(data)


def style_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure(background="transparent")
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#B8B8C8",
            titleColor="#FFFFFF",
            gridColor="#2A2A3E",
            domainColor="#2A2A3E",
            tickColor="#2A2A3E",
        )
        .configure_legend(
            labelColor="#B8B8C8",
            titleColor="#FFFFFF",
        )
    )


def render_table(df: pd.DataFrame):
    st.markdown(
        df.to_html(index=False, classes="ontop-html-table", border=0, escape=False),
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="ontop-hero">
        <span class="ontop-eyebrow">Dashboard</span>
        <h2>Monitor conversion, ownership, and product performance across the sales workflow.</h2>
        <p>Use this view to understand team activity, spot bottlenecks, and trigger conversion checks when needed.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

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

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Time Window</p>
        <h3 class="ontop-section-title">Choose the analysis period</h3>
        <p>The charts and metrics below update based on the selected timeframe.</p>
    </div>
    """,
    unsafe_allow_html=True,
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

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Product Performance</p>
        <h3 class="ontop-section-title">Leads by product</h3>
        <p>Compare total lead volume and conversion outcomes across the portfolio.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

product_chart = (
    base_chart(product_stats)
    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("total:Q", title="Total Leads"),
        color=alt.Color(
            "product_name:N",
            scale=alt.Scale(range=ONTOp_COLORS),
            legend=None,
        ),
        tooltip=["product_name:N", "total:Q", "converted:Q", "conversion_rate:Q"],
    )
    .properties(height=320)
)

product_labels = (
    base_chart(product_stats)
    .mark_text(dy=-10, color="#FFFFFF", fontSize=12, fontWeight="bold")
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("total:Q", title="Total Leads"),
        text=alt.Text("total:Q"),
    )
)

open_shell("ontop-chart-shell")
st.altair_chart(
    style_chart(alt.layer(product_chart, product_labels)),
    use_container_width=True,
)
close_shell()

open_shell("ontop-table-shell")
render_table(
    product_stats.rename(
        columns={
            "product_name": "Product",
            "total": "Total Leads",
            "converted": "Converted",
            "conversion_rate": "Conversion %",
        }
    ).fillna("")
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Leads by agent
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Ownership</p>
        <h3 class="ontop-section-title">Leads by agent</h3>
        <p>See who is generating the most opportunities and how often those leads convert.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

open_shell("ontop-table-shell")
render_table(
    agent_stats.rename(
        columns={
            "agent_name": "Agent",
            "total": "Total Leads",
            "converted": "Converted",
            "conversion_rate": "Conversion %",
        }
    ).fillna("")
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Leads over time
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Trend</p>
        <h3 class="ontop-section-title">Leads over time</h3>
        <p>Track daily lead creation to spot surges, slowdowns, or campaign impact.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

daily = df.groupby("date").size().reset_index(name="leads")

trend_chart = (
    base_chart(daily)
    .mark_line(strokeWidth=3, color="#E35276", point=alt.OverlayMarkDef(color="#261C94", size=70))
    .encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("leads:Q", title="Leads"),
        tooltip=["date:T", "leads:Q"],
    )
    .properties(height=320)
)

trend_labels = (
    base_chart(daily)
    .mark_text(dy=-12, color="#FFFFFF", fontSize=11)
    .encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("leads:Q", title="Leads"),
        text=alt.Text("leads:Q"),
    )
)

open_shell("ontop-chart-shell")
st.altair_chart(
    style_chart(alt.layer(trend_chart, trend_labels)),
    use_container_width=True,
)
close_shell()

# ---------------------------------------------------------------------------
# Status breakdown
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Status Mix</p>
        <h3 class="ontop-section-title">Status breakdown</h3>
        <p>Understand how the current pipeline is distributed across active and terminal states.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_df = df["status"].value_counts().reset_index()
status_df.columns = ["Status", "Count"]

status_chart = (
    base_chart(status_df)
    .mark_arc(innerRadius=70, outerRadius=120)
    .encode(
        theta=alt.Theta("Count:Q"),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=["Qualified", "Contacted", "Converted", "Rejected", "Expired"],
                range=["#7C73F7", "#B8B8C8", "#E35276", "#6B6B7E", "#261C94"],
            ),
        ),
        tooltip=["Status:N", "Count:Q"],
    )
    .properties(height=320)
)

status_labels = (
    base_chart(status_df)
    .mark_text(radius=145, color="#FFFFFF", fontSize=12, fontWeight="bold")
    .encode(
        theta=alt.Theta("Count:Q"),
        text=alt.Text("Count:Q"),
    )
)

open_shell("ontop-chart-shell")
st.altair_chart(
    style_chart(alt.layer(status_chart, status_labels)),
    use_container_width=True,
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Agent leads explorer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Explorer</p>
        <h3 class="ontop-section-title">Agent leads</h3>
        <p>Drill into a single owner to inspect lead quality, status, and recent output.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

agent_names = sorted(df["agent_name"].unique().tolist())
selected_agent = st.selectbox(
    "Select Agent",
    options=["All Agents"] + agent_names,
)

agent_df = df if selected_agent == "All Agents" else df[df["agent_name"] == selected_agent]

a_total = len(agent_df)
a_converted = len(agent_df[agent_df["status"] == "Converted"])
a_active = len(agent_df[agent_df["status"].isin(["Qualified", "Contacted"])])
a_rate = (a_converted / a_total * 100) if a_total > 0 else 0

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Total", a_total)
mc2.metric("Active", a_active)
mc3.metric("Converted", a_converted)
mc4.metric("Conversion Rate", f"{a_rate:.1f}%")

agent_display = agent_df[["cr_code", "product_name", "agent_name", "status", "notes", "date"]].rename(
    columns={
        "cr_code": "CR Code",
        "product_name": "Product",
        "agent_name": "Agent",
        "status": "Status",
        "notes": "Notes",
        "date": "Date",
    }
)
open_shell("ontop-table-shell")
render_table(agent_display.fillna(""))
close_shell()
