"""Shared components used across all pages."""

import streamlit as st

ALLOWED_DOMAIN = "getontop.com"


def apply_global_theme():
    """Inject a shared Ontop-inspired theme across the app."""
    st.markdown(
        """
        <style>
            :root {
                --ontop-purple: #261C94;
                --ontop-coral: #E35276;
                --bg-primary: #000000;
                --bg-card: #060609;
                --bg-input: #1A1A24;
                --text-primary: #FFFFFF;
                --text-secondary: #B8B8C8;
                --text-muted: #6B6B7E;
                --border-color: #2A2A3E;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(38, 28, 148, 0.35), transparent 32%),
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.20), transparent 28%),
                    linear-gradient(180deg, #050507 0%, #000000 100%);
                color: var(--text-primary);
            }

            [data-testid="stHeader"] {
                background: rgba(0, 0, 0, 0);
            }

            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(38, 28, 148, 0.18), rgba(6, 6, 9, 0.94) 26%),
                    #060609;
                border-right: 1px solid var(--border-color);
            }

            [data-testid="stSidebar"] * {
                color: var(--text-primary);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            h1, h2, h3 {
                color: var(--text-primary);
                letter-spacing: -0.02em;
            }

            p, li, label, .stMarkdown, .stCaption {
                color: var(--text-secondary);
            }

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox [data-baseweb="select"] > div,
            .stMultiSelect [data-baseweb="select"] > div {
                background: var(--bg-input);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                border-radius: 14px;
            }

            .stButton > button,
            .stDownloadButton > button {
                background: linear-gradient(135deg, var(--ontop-purple), var(--ontop-coral));
                color: var(--text-primary);
                border: 0;
                border-radius: 999px;
                font-weight: 600;
                box-shadow: 0 10px 24px rgba(38, 28, 148, 0.28);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                filter: brightness(1.06);
            }

            .stDataFrame, div[data-testid="stMetric"], div[data-testid="stExpander"] {
                background: rgba(6, 6, 9, 0.82);
                border: 1px solid var(--border-color);
                border-radius: 18px;
            }

            div[data-testid="stMetric"] {
                padding: 1rem;
            }

            .stAlert {
                border-radius: 16px;
                border: 1px solid var(--border-color);
            }

            .ontop-hero {
                padding: 1.5rem 1.75rem;
                margin-bottom: 1.5rem;
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.25), transparent 35%),
                    linear-gradient(135deg, rgba(38, 28, 148, 0.92), rgba(6, 6, 9, 0.94));
                box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
            }

            .ontop-hero h1,
            .ontop-hero h2,
            .ontop-hero p {
                color: #FFFFFF;
                margin: 0;
            }

            .ontop-eyebrow {
                display: inline-block;
                margin-bottom: 0.7rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.10);
                color: #FFFFFF;
                font-size: 0.78rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            .ontop-subtle-card {
                padding: 1rem 1.1rem;
                border-radius: 18px;
                border: 1px solid var(--border-color);
                background: linear-gradient(180deg, rgba(26, 26, 36, 0.92), rgba(6, 6, 9, 0.92));
                margin-bottom: 1rem;
            }

            .ontop-subtle-card h3,
            .ontop-subtle-card p {
                margin: 0;
            }

            .ontop-section-title {
                margin-top: 0.2rem;
                margin-bottom: 0.9rem;
            }

            .ontop-kicker {
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.76rem;
                font-weight: 700;
            }

            .ontop-profile-card {
                padding: 1.15rem;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.95), rgba(6, 6, 9, 0.95));
                min-height: 160px;
            }

            .ontop-profile-card code {
                background: rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 0.2rem 0.45rem;
                color: #FFFFFF;
            }

            .ontop-inline-stat {
                padding: 0.9rem 1rem;
                border-radius: 18px;
                border: 1px solid var(--border-color);
                background: rgba(6, 6, 9, 0.85);
                margin-bottom: 1rem;
            }

            .ontop-inline-stat strong {
                display: block;
                color: #FFFFFF;
                font-size: 1.05rem;
                margin-bottom: 0.15rem;
            }

            .ontop-table-shell,
            .ontop-chart-shell {
                padding: 0.8rem;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(38, 28, 148, 0.12), transparent 28%),
                    linear-gradient(180deg, rgba(6, 6, 9, 0.96), rgba(26, 26, 36, 0.92));
                margin-bottom: 1rem;
            }

            .ontop-chart-shell [data-testid="stVegaLiteChart"],
            .ontop-chart-shell [data-testid="stArrowVegaLiteChart"] {
                background: transparent;
            }

            .ontop-html-table {
                width: 100%;
                border-collapse: collapse;
                overflow: hidden;
                border-radius: 16px;
                font-size: 0.94rem;
            }

            .ontop-html-table th {
                background: #12121a;
                color: #ffffff;
                text-align: left;
                padding: 0.55rem 0.7rem;
                border-bottom: 1px solid var(--border-color);
                font-size: 0.84rem;
                line-height: 1.2;
            }

            .ontop-html-table td {
                background: #060609;
                color: #b8b8c8;
                padding: 0.48rem 0.7rem;
                border-bottom: 1px solid rgba(42, 42, 62, 0.7);
                vertical-align: top;
                font-size: 0.88rem;
                line-height: 1.2;
            }

            .ontop-html-table tr:hover td {
                background: #101018;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def require_auth():
    """Centralized authentication guard.

    - If not logged in, show sign-in prompt and stop.
    - If email is missing, fail closed.
    - If email domain is not allowed, deny access.
    - If authorized, populate session state with agent identity.
    """
    if not st.user.is_logged_in:
        st.header("CX Sales Agent")
        st.info("Please sign in with your Google Workspace account to continue.")
        if st.button("Sign in with Google"):
            st.login("google")
        st.stop()

    email = st.user.email
    if not email:
        st.error("Unable to verify your identity. No email address received.")
        if st.button("Sign out"):
            st.logout()
        st.stop()

    if not email.endswith(f"@{ALLOWED_DOMAIN}"):
        st.error(f"Access restricted to @{ALLOWED_DOMAIN} accounts.")
        st.markdown(f"Signed in as: **{email}**")
        if st.button("Sign out"):
            st.logout()
        st.stop()

    # Set identity in session state
    st.session_state["agent_name"] = st.user.name or email.split("@")[0]
    st.session_state["agent_email"] = email


def render_sidebar():
    """Render the common sidebar with auth guard, identity display, and cache controls."""
    require_auth()
    apply_global_theme()

    with st.sidebar:
        st.title("CX Sales Agent")
        st.divider()

        st.markdown(f"**{st.session_state['agent_name']}**")
        st.caption(st.session_state["agent_email"])

        if st.button("Sign out", use_container_width=True):
            st.logout()

        st.divider()

        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared — data will reload on next query.")

        st.caption("Data is cached for 1 hour. Click above to force a refresh.")
