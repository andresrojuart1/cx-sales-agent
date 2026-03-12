"""User Lookup — Search contractors and check product eligibility."""

import streamlit as st

st.set_page_config(page_title="User Lookup", page_icon=":mag:", layout="wide")

from datetime import datetime, timezone
import re

from data.redshift import get_contractor_profile, search_contractors
from data.supabase_client import check_opportunity_lock, save_lead
from eligibility.engine import count_eligible, get_user_eligibility
from eligibility.products import PRODUCTS
from shared import render_sidebar

render_sidebar()

st.markdown(
    """
    <section class="ontop-hero">
        <span class="ontop-eyebrow">User Lookup</span>
        <h2>Find a contractor, validate eligibility, and turn intent into a qualified lead.</h2>
        <p>Search by CR code, email, or name to review profile signals and product opportunities in one workflow.</p>
    </section>
    """,
    unsafe_allow_html=True,
)


def parse_supabase_timestamp(raw_value: str) -> datetime:
    """Normalize Supabase timestamps for Python 3.9's stricter parser."""
    normalized = re.sub(r"\.(\d{1,5})([+-]\d{2}:\d{2})$", lambda m: f".{m.group(1).ljust(6, '0')}{m.group(2)}", raw_value)
    return datetime.fromisoformat(normalized)

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Search</p>
        <h3 class="ontop-section-title">Locate a contractor</h3>
        <p>Start with a CR code for the fastest match, or search by email or full name.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

search_term = st.text_input(
    "Search by CR Code, email, or name",
    placeholder="e.g. CR034116 or john@example.com",
)

if not search_term:
    st.info("Enter a CR code, email, or name to look up a contractor.")
    st.stop()

# Direct CR code lookup (starts with "CR")
if search_term.upper().startswith("CR"):
    profile = get_contractor_profile(search_term.upper())
    if profile:
        selected_cr = profile["cod_contractor"]
    else:
        st.error(f"No contractor found for **{search_term.upper()}**")
        st.stop()
else:
    # Search by email or name
    with st.spinner("Searching..."):
        results = search_contractors(search_term)

    if results.empty:
        st.error(f"No contractors found matching **{search_term}**")
        st.stop()

    if len(results) == 1:
        selected_cr = results.iloc[0]["cod_contractor"]
        profile = get_contractor_profile(selected_cr)
    else:
        st.subheader("Search Results")
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True,
            column_config={
                "cod_contractor": "CR Code",
                "full_name": "Name",
                "des_email": "Email",
                "des_residence_country": "Country",
            },
        )
        selected_cr = st.selectbox(
            "Select a contractor",
            options=results["cod_contractor"].tolist(),
            format_func=lambda cr: f"{cr} — {results.loc[results['cod_contractor'] == cr, 'full_name'].values[0]}",
        )
        profile = get_contractor_profile(selected_cr)

if not profile:
    st.error("Could not load contractor profile.")
    st.stop()

# ---------------------------------------------------------------------------
# Profile Card
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    f"""
    <div class="ontop-subtle-card">
        <p class="ontop-kicker">Contractor Profile</p>
        <h3 class="ontop-section-title">{profile.get('full_name', 'N/A')}</h3>
        <p>Reference profile details before you pitch products or create a lead.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Identity</p>
            <h3>{profile.get('full_name', 'N/A')}</h3>
            <p><strong>CR Code</strong><br><code>{profile['cod_contractor']}</code></p>
            <p><strong>Email</strong><br>{profile.get('des_email') or 'N/A'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Location</p>
            <h3>{profile.get('des_residence_country') or 'N/A'}</h3>
            <p><strong>Country</strong><br>{profile.get('des_residence_country') or 'N/A'}</p>
            <p><strong>City</strong><br>{profile.get('des_residence_city') or 'N/A'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    wallet_status = profile.get("des_wallet_status") or "N/A"
    balance = profile.get("amt_wallet_balance")
    balance_text = f"${balance:,.2f}" if balance is not None else "N/A"
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Wallet</p>
            <h3>{wallet_status}</h3>
            <p><strong>Status</strong><br>{wallet_status}</p>
            <p><strong>Balance</strong><br>{balance_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Eligibility Cards
# ---------------------------------------------------------------------------

st.divider()

user_email = profile.get("des_email")
eligibility = get_user_eligibility(selected_cr, user_email)
num_eligible = count_eligible(selected_cr, eligibility)

st.markdown(
    f"""
    <div class="ontop-inline-stat">
        <span class="ontop-kicker">Eligibility Summary</span>
        <strong>{num_eligible} product{'s' if num_eligible != 1 else ''} available</strong>
        Review each product card below, confirm the lock state, and capture the opportunity if available.
    </div>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(len(PRODUCTS))

for col, (key, product) in zip(cols, PRODUCTS.items()):
    result = eligibility.get(key)
    if not result:
        continue

    with col:
        if result.status == "ELIGIBLE":
            st.success(f"**{product.name}**")
            st.caption(product.description)
            st.markdown(f"*{product.pitch}*")

            lead_key = f"lead_{selected_cr}_{key}"
            if st.session_state.get(lead_key):
                st.info("Lead submitted!")
            else:
                lock = check_opportunity_lock(selected_cr, key)
                if lock:
                    if lock["agent_email"] == st.session_state["agent_email"]:
                        st.info("You already have an active lead for this product.")
                    else:
                        created = parse_supabase_timestamp(lock["created_at"])
                        days_left = 60 - (datetime.now(timezone.utc) - created).days
                        st.warning(
                            f"Locked by **{lock['agent_name']}** — "
                            f"available in ~{max(days_left, 1)} days"
                        )
                else:
                    with st.expander("Mark as Lead"):
                        notes = st.text_area(
                            "Notes (optional)",
                            key=f"notes_{selected_cr}_{key}",
                            placeholder="Any context about the interaction...",
                        )
                        if st.button("Submit Lead", key=f"btn_{selected_cr}_{key}", type="primary"):
                            save_lead(
                                cr_code=selected_cr,
                                product=key,
                                agent_name=st.session_state["agent_name"],
                                notes=notes,
                                agent_email=st.session_state["agent_email"],
                            )
                            st.session_state[lead_key] = True
                            st.rerun()

        elif result.status == "ALREADY_USING":
            st.markdown(
                f"""<div style="padding:1rem;border-radius:0.5rem;background-color:#374151;color:#9ca3af;">
                <strong>{product.name}</strong><br>
                <small>Already using this product</small></div>""",
                unsafe_allow_html=True,
            )

        elif result.status == "NOT_ELIGIBLE":
            st.error(f"**{product.name}**")
            st.caption(result.reason)
