"""Dashboard — Performance overview and team stats."""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide")

from data.conversion import run_conversion_check
from data.supabase_client import delete_lead, expire_stale_leads, get_leads
from eligibility.products import PRODUCT_ESTIMATED_MRR, PRODUCT_NAMES
from shared import can_delete_leads, render_sidebar

render_sidebar()
is_lead_admin = can_delete_leads()


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

# Fetch all leads first so the top filter can drive the whole dashboard.
all_leads = get_leads()

if not all_leads:
    st.info("No leads recorded yet.")
    st.stop()

all_df = pd.DataFrame(all_leads)
all_df["product_name"] = all_df["product"].map(PRODUCT_NAMES)
all_df["estimated_mrr"] = all_df["product"].map(PRODUCT_ESTIMATED_MRR).fillna(0.0)
all_df["created_at"] = pd.to_datetime(all_df["created_at"])
all_df["date"] = all_df["created_at"].dt.date

agent_filter_options = ["All Agents"] + sorted(all_df["agent_name"].dropna().unique().tolist())

toolbar_col1, toolbar_col2, toolbar_col3, toolbar_col4 = st.columns([1.05, 1.05, 1.2, 1.0], vertical_alignment="bottom")
with toolbar_col1:
    start_date = st.date_input(
        "Start Date",
        value=st.session_state.get("dashboard_start_date", date.today() - timedelta(days=30)),
        key="dashboard_start_date",
    )
with toolbar_col2:
    end_date = st.date_input(
        "End Date",
        value=st.session_state.get("dashboard_end_date", date.today()),
        key="dashboard_end_date",
    )
with toolbar_col3:
    selected_agent = st.selectbox(
        "Agent",
        options=agent_filter_options,
    )
with toolbar_col4:
    if st.button("Check Conversions", type="secondary", use_container_width=True):
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

if start_date > end_date:
    st.warning("Start Date cannot be later than End Date.")
    st.stop()

start_ts = pd.Timestamp(start_date).tz_localize("UTC")
end_ts = (pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)).tz_localize("UTC")
df = all_df[(all_df["created_at"] >= start_ts) & (all_df["created_at"] <= end_ts)].copy()
if selected_agent != "All Agents":
    df = df[df["agent_name"] == selected_agent].copy()

if df.empty:
    st.info("No leads match the selected agent and date range.")
    st.stop()

converted_df = df[df["status"] == "Converted"].copy()
df["converted_mrr"] = df.apply(
    lambda row: row["estimated_mrr"] if row["status"] == "Converted" else 0.0,
    axis=1,
)

# ---------------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------------

total = len(df)
converted = len(df[df["status"] == "Converted"])
expired = len(df[df["status"] == "Expired"])
active = len(df[df["status"].isin(["Qualified", "Contacted"])])
conversion_rate = (converted / total * 100) if total > 0 else 0
estimated_mrr = float(converted_df["estimated_mrr"].sum())

st.markdown(
    f"""
    <div class="ontop-mini-stats" style="grid-template-columns: repeat(6, minmax(0, 1fr));">
        <div class="ontop-mini-stat">
            <span>Total Leads</span>
            <strong>{total}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-purple">
            <span>Open</span>
            <strong>{active}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-green">
            <span>Converted</span>
            <strong>{converted}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-red">
            <span>Expired</span>
            <strong>{expired}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-amber">
            <span>Conversion Rate</span>
            <strong>{conversion_rate:.1f}%</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-coral">
            <span>Estimated MRR</span>
            <strong>${estimated_mrr:,.1f}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Leads by product
# ---------------------------------------------------------------------------

st.markdown('<div class="ontop-section-head"><h3>Leads by Product</h3><p>Compare volume and conversion by product.</p></div>', unsafe_allow_html=True)

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
product_stats["conversion_rate_label"] = product_stats["conversion_rate"].map(lambda value: f"{value:.1f}%")
product_stats["estimated_mrr"] = (
    converted_df.groupby("product_name")["estimated_mrr"].sum().reindex(product_stats["product_name"]).fillna(0).values
)
product_stats["estimated_mrr_label"] = product_stats["estimated_mrr"].map(lambda value: f"${value:,.1f}")

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
        y=alt.Y("total:Q", title=None, axis=None),
        text=alt.Text("total:Q"),
    )
)

product_rate_line = (
    base_chart(product_stats)
    .mark_line(color="#F59E0B", strokeWidth=3, point=alt.OverlayMarkDef(color="#F59E0B", size=90))
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(
            "conversion_rate:Q",
            title=None,
            axis=alt.Axis(orient="right", format=".0f", labelExpr="datum.label + '%'", tickCount=4),
            scale=alt.Scale(domain=[0, max(15, float(product_stats["conversion_rate"].max()) + 2)]),
        ),
        tooltip=[
            "product_name:N",
            "total:Q",
            "converted:Q",
            alt.Tooltip("conversion_rate:Q", title="Conversion %", format=".1f"),
        ],
    )
)

product_rate_labels = (
    base_chart(product_stats)
    .mark_text(dy=-12, color="#FCD34D", fontSize=11, fontWeight="bold")
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(
            "conversion_rate:Q",
            title=None,
            axis=None,
            scale=alt.Scale(domain=[0, max(15, float(product_stats["conversion_rate"].max()) + 2)]),
        ),
        text=alt.Text("conversion_rate_label:N"),
    )
)

best_product = product_stats.loc[product_stats["conversion_rate"].idxmax()] if not product_stats.empty else None
if best_product is not None:
    legend_col1, legend_col2 = st.columns([4, 1.2], vertical_alignment="center")
    with legend_col1:
        st.caption(
            f"Best conversion rate: {best_product['product_name']} ({best_product['conversion_rate']:.1f}%)."
        )
    with legend_col2:
        st.markdown(
            """
            <div style="display:flex;justify-content:flex-end;align-items:center;gap:0.45rem;margin-top:0.1rem;">
                <span style="display:inline-block;width:0.9rem;height:0.18rem;background:#F59E0B;border-radius:999px;"></span>
                <span style="color:#FCD34D;font-size:0.88rem;font-weight:600;">Conversion Rate</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

open_shell("ontop-chart-shell")
st.altair_chart(
    style_chart(alt.layer(product_chart, product_labels, product_rate_line, product_rate_labels).resolve_scale(y="independent")),
    use_container_width=True,
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Estimated MRR by product
# ---------------------------------------------------------------------------

st.markdown('<div class="ontop-section-head"><h3>Estimated MRR by Product</h3><p>Track recurring value generated by converted leads.</p></div>', unsafe_allow_html=True)

mrr_chart = (
    base_chart(product_stats)
    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("estimated_mrr:Q", title="Estimated MRR (USD)"),
        color=alt.Color(
            "product_name:N",
            scale=alt.Scale(range=ONTOp_COLORS),
            legend=None,
        ),
        tooltip=[
            "product_name:N",
            alt.Tooltip("estimated_mrr:Q", title="Estimated MRR", format=",.1f"),
            "total:Q",
            "converted:Q",
        ],
    )
    .properties(height=280)
)

mrr_labels = (
    base_chart(product_stats)
    .mark_text(dy=-10, color="#FFFFFF", fontSize=12, fontWeight="bold")
    .encode(
        x=alt.X("product_name:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("estimated_mrr:Q", title=None, axis=None),
        text=alt.Text("estimated_mrr_label:N"),
    )
)

top_mrr_product = product_stats.loc[product_stats["estimated_mrr"].idxmax()] if not product_stats.empty else None
if top_mrr_product is not None:
    st.caption(
        f"Highest projected MRR: {top_mrr_product['product_name']} (${top_mrr_product['estimated_mrr']:,.1f})."
    )

open_shell("ontop-chart-shell")
st.altair_chart(
    style_chart(alt.layer(mrr_chart, mrr_labels)),
    use_container_width=True,
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Leads by agent
# ---------------------------------------------------------------------------

st.markdown('<div class="ontop-section-head"><h3>Leads by Agent</h3><p>See who is generating the most opportunities and how often they convert.</p></div>', unsafe_allow_html=True)

agent_stats = (
    df.groupby("agent_name")
    .agg(
        total=("id", "count"),
        converted=("status", lambda s: (s == "Converted").sum()),
        mrr=("converted_mrr", "sum"),
    )
    .reset_index()
    .sort_values("total", ascending=False)
)
agent_stats["conversion_rate"] = (
    agent_stats["converted"] / agent_stats["total"] * 100
).round(1)
agent_stats["conversion_rate_label"] = agent_stats["conversion_rate"].map(lambda value: f"{value:.1f}%")
agent_stats["mrr_label"] = agent_stats["mrr"].map(lambda value: f"${value:,.1f}")

open_shell("ontop-table-shell")
render_table(
    agent_stats.rename(
        columns={
            "agent_name": "Agent",
            "total": "Total Leads",
            "converted": "Converted",
            "mrr_label": "MRR Estimated",
            "conversion_rate_label": "Conversion %",
        }
    )[["Agent", "Total Leads", "Converted", "MRR Estimated", "Conversion %"]].fillna("")
)
close_shell()

st.divider()

# ---------------------------------------------------------------------------
# Leads over time
# ---------------------------------------------------------------------------

st.markdown('<div class="ontop-section-head"><h3>Leads Over Time</h3><p>Track daily lead creation to spot surges and slowdowns.</p></div>', unsafe_allow_html=True)

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
# Agent leads explorer
# ---------------------------------------------------------------------------

st.markdown('<div class="ontop-section-head"><h3>Agent Leads</h3><p>Inspect the lead list for the current dashboard filter.</p></div>', unsafe_allow_html=True)

agent_df = df.copy()

a_total = len(agent_df)
a_converted = len(agent_df[agent_df["status"] == "Converted"])
a_active = len(agent_df[agent_df["status"].isin(["Qualified", "Contacted"])])
a_rate = (a_converted / a_total * 100) if a_total > 0 else 0

st.markdown(
    f"""
    <div class="ontop-mini-stats" style="grid-template-columns: repeat(4, minmax(0, 1fr));">
        <div class="ontop-mini-stat">
            <span>Total</span>
            <strong>{a_total}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-purple">
            <span>Open</span>
            <strong>{a_active}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-green">
            <span>Converted</span>
            <strong>{a_converted}</strong>
        </div>
        <div class="ontop-mini-stat ontop-mini-stat-amber">
            <span>Conversion Rate</span>
            <strong>{a_rate:.1f}%</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

agent_display = agent_df[["cr_code", "product_name", "agent_name", "status", "converted_mrr", "notes", "date"]].rename(
    columns={
        "cr_code": "CR Code",
        "product_name": "Product",
        "agent_name": "Agent",
        "status": "Status",
        "converted_mrr": "MRR",
        "notes": "Notes",
        "date": "Date",
    }
)
agent_display["MRR"] = agent_display["MRR"].map(lambda value: f"${value:,.1f}" if value else "—")
if is_lead_admin and not agent_df.empty:
    selected_dashboard_delete_ids = set(st.session_state.get("dashboard_delete_ids", []))
    delete_df = agent_df[["id", "cr_code", "product_name", "agent_name", "status", "converted_mrr", "notes", "date"]].rename(
        columns={
            "id": "Lead ID",
            "cr_code": "CR Code",
            "product_name": "Product",
            "agent_name": "Agent",
            "status": "Status",
            "converted_mrr": "MRR",
            "notes": "Notes",
            "date": "Date",
        }
    ).copy()
    delete_df["MRR"] = delete_df["MRR"].map(lambda value: f"${value:,.1f}" if value else "—")
    delete_df.insert(0, "Delete", delete_df["Lead ID"].isin(selected_dashboard_delete_ids))

    open_shell("ontop-table-shell")
    edited_delete_df = st.data_editor(
        delete_df,
        use_container_width=True,
        hide_index=True,
        disabled=["Lead ID", "CR Code", "Product", "Agent", "Status", "MRR", "Notes", "Date"],
        column_config={
            "Delete": st.column_config.CheckboxColumn(
                "Delete",
                help="Select lead(s) to remove",
                default=False,
            ),
            "Lead ID": st.column_config.TextColumn("Lead ID", width="small"),
        },
        key="dashboard_delete_editor",
    )
    close_shell()

    selected_delete_ids = edited_delete_df.loc[edited_delete_df["Delete"], "Lead ID"].tolist()
    st.session_state["dashboard_delete_ids"] = selected_delete_ids

    admin_col1, admin_col2 = st.columns([3, 2])
    with admin_col1:
        confirm_dashboard_delete = st.checkbox(
            f"I understand this will permanently delete {len(selected_delete_ids)} selected lead(s).",
            key="dashboard_delete_confirm",
        )
    with admin_col2:
        if st.button("Delete Selected Leads", type="secondary", key="dashboard_delete_btn", use_container_width=True):
            if not selected_delete_ids:
                st.warning("Select at least one lead to delete.")
            elif not confirm_dashboard_delete:
                st.warning("Confirm deletion before removing leads.")
            else:
                for lead_id in selected_delete_ids:
                    delete_lead(lead_id)
                st.session_state["dashboard_delete_ids"] = []
                st.success(f"Deleted {len(selected_delete_ids)} lead(s).")
                st.rerun()
else:
    open_shell("ontop-table-shell")
    render_table(agent_display.fillna(""))
    close_shell()
