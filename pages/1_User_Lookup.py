"""User Lookup — Search contractors and check product eligibility."""

import streamlit as st

st.set_page_config(page_title="User Lookup", page_icon=":mag:", layout="wide")

from datetime import datetime, timezone
import re

from data.redshift import get_contractor_profile, search_contractors
from data import supabase_client
from eligibility.engine import count_eligible, get_user_eligibility
from eligibility.products import PRODUCTS
from shared import render_sidebar

check_opportunity_lock = supabase_client.check_opportunity_lock
save_lead = supabase_client.save_lead
get_recent_lead = getattr(supabase_client, "get_recent_lead", lambda *_args, **_kwargs: None)

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


def render_feedback_card(title: str, body: str, tone: str):
    st.markdown(
        f"""
        <div class="ontop-feedback-card">
            <span class="ontop-status-badge ontop-status-{tone}">{title}</span>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, tone: str):
    return f'<span class="ontop-status-badge ontop-status-{tone}">{label}</span>'

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

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
col0, col1, col2, col3 = st.columns(4)

with col0:
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Contractor Profile</p>
            <div class="ontop-profile-value">
                <div class="ontop-profile-strong">{profile.get('full_name', 'N/A')}</div>
            </div>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">Summary</span>
                <div class="ontop-profile-text">
                    {profile.get('cod_contractor', 'N/A')}<br>
                    {profile.get('des_residence_country') or 'No country'}<br>
                    {profile.get('des_wallet_status') or 'No wallet status'}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col1:
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Identity</p>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">CR Code</span>
                <div class="ontop-profile-text"><code>{profile['cod_contractor']}</code></div>
            </div>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">Email</span>
                <div class="ontop-profile-text">{profile.get('des_email') or 'N/A'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Location</p>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">Country</span>
                <div class="ontop-profile-strong">{profile.get('des_residence_country') or 'N/A'}</div>
            </div>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">City</span>
                <div class="ontop-profile-text">{profile.get('des_residence_city') or 'N/A'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    wallet_status = profile.get("des_wallet_status") or "N/A"
    balance = profile.get("amt_wallet_balance")
    balance_text = f"${balance:,.2f}" if balance is not None else "N/A"
    wallet_tone = "green" if wallet_status.upper() == "ACTIVATED" else "gray"
    st.markdown(
        f"""
        <div class="ontop-profile-card">
            <p class="ontop-kicker">Wallet</p>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">Status</span>
                <span class="ontop-status-badge ontop-status-{wallet_tone}">{wallet_status}</span>
            </div>
            <div class="ontop-profile-value">
                <span class="ontop-profile-label">Balance</span>
                <div class="ontop-profile-strong">{balance_text}</div>
            </div>
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

cols = st.columns(len(PRODUCTS))

for col, (key, product) in zip(cols, PRODUCTS.items()):
    result = eligibility.get(key)
    if not result:
        continue

    status_html = ""
    feedback_title = ""
    feedback_body = ""
    feedback_tone = "gray"
    card_class = "ontop-product-card-coral"
    lead_key = f"lead_{selected_cr}_{key}"
    lock = None
    recent_lead = None

    if result.status == "ELIGIBLE":
        status_html = render_status_badge("Eligible", "green")
        feedback_tone = "green"
        feedback_title = "Opportunity open"
        feedback_body = "No active lock found. Add context below and create the lead when ready."
        card_class = "ontop-product-card-green"
        if st.session_state.get(lead_key):
            feedback_title = "Lead submitted"
            feedback_body = "This opportunity is now in your pipeline and will show up in My Leads."
        else:
            recent_lead = get_recent_lead(selected_cr, key)
            if recent_lead and recent_lead["status"] == "Converted":
                status_html = render_status_badge("Converted", "purple")
                feedback_tone = "purple"
                feedback_title = "Recently converted"
                feedback_body = f"Converted by {recent_lead['agent_name']}. This opportunity should remain closed."
                card_class = "ontop-product-card-purple"
            else:
                lock = check_opportunity_lock(selected_cr, key)
            if lock:
                created = parse_supabase_timestamp(lock["created_at"])
                days_left = max(60 - (datetime.now(timezone.utc) - created).days, 1)
                if lock["agent_email"] == st.session_state["agent_email"]:
                    status_html = render_status_badge("Assigned", "purple")
                    feedback_tone = "purple"
                    feedback_title = "Already assigned to you"
                    feedback_body = (
                        f"You already have an active lead for this product. "
                        f"It stays reserved for about {days_left} more day(s) unless you update it sooner in My Leads."
                    )
                    card_class = "ontop-product-card-purple"
                else:
                    status_html = render_status_badge("Taken", "amber")
                    feedback_tone = "amber"
                    feedback_title = "Opportunity locked"
                    feedback_body = f"Locked by {lock['agent_name']}. It should open again in about {days_left} day(s)."
    elif result.status == "ALREADY_USING":
        status_html = render_status_badge("Already using", "gray")
        feedback_tone = "gray"
        feedback_title = "Already active"
        feedback_body = result.reason
    else:
        status_html = render_status_badge("Not eligible", "coral")
        feedback_tone = "coral"
        feedback_title = "Currently unavailable"
        feedback_body = result.reason

    with col:
        st.markdown(
            f"""
            <div class="ontop-product-card {card_class}">
                <div>
                    <h3>{product.name}</h3>
                    <p class="ontop-product-desc">{product.description}</p>
                </div>
                <div>{status_html}</div>
                <p class="ontop-product-pitch"><em>{product.pitch}</em></p>
                <div class="ontop-product-footer ontop-product-state">
                    <p><strong>{feedback_title}</strong></p>
                    <p>{feedback_body}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if (
            result.status == "ELIGIBLE"
            and not st.session_state.get(lead_key)
            and not lock
            and not (recent_lead and recent_lead["status"] == "Converted")
        ):
            with st.expander(f"Mark {product.name} as Lead"):
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
                    st.session_state["lookup_feedback"] = f"{product.name} lead created for {selected_cr}."
                    st.rerun()

if st.session_state.get("lookup_feedback"):
    st.toast(st.session_state.pop("lookup_feedback"))
