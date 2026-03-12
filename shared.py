"""Shared components used across all pages."""

import streamlit as st

ALLOWED_DOMAIN = "getontop.com"
LEAD_ADMIN_FALLBACK_EMAILS = {
    "mrojas@getontop.com",
    "acaballero@getontop.com",
    "flociccero@getontop.com",
}


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

            [data-testid="stSidebarNav"] {
                display: none;
            }

            [data-testid="stSidebarNavSeparator"] {
                display: none;
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

            div[data-testid="stExpander"] {
                margin-top: 0.85rem;
                overflow: hidden;
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
                padding: 0.8rem 0.95rem;
                border-radius: 18px;
                border: 1px solid var(--border-color);
                background: linear-gradient(180deg, rgba(26, 26, 36, 0.92), rgba(6, 6, 9, 0.92));
                margin-bottom: 0.85rem;
            }

            .ontop-profile-summary {
                padding: 0.8rem 0.95rem;
                margin-bottom: 0.55rem;
            }

            .ontop-subtle-card h3,
            .ontop-subtle-card p {
                margin: 0;
            }

            .ontop-section-title {
                margin-top: 0.15rem;
                margin-bottom: 0.55rem;
            }

            .ontop-kicker {
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.76rem;
                font-weight: 700;
            }

            .ontop-profile-card {
                padding: 0.95rem 1rem;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.95), rgba(6, 6, 9, 0.95));
                min-height: 0;
            }

            .ontop-panel-card {
                padding: 0.95rem 1rem;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.95), rgba(6, 6, 9, 0.95));
            }

            .ontop-tight-columns {
                gap: 0.75rem;
            }

            .ontop-profile-meta {
                margin-top: 0.3rem;
                color: var(--text-secondary);
                font-size: 0.92rem;
            }

            .ontop-profile-value {
                margin-top: 0.8rem;
            }

            .ontop-profile-label {
                display: block;
                color: var(--text-muted);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                margin-bottom: 0.22rem;
            }

            .ontop-profile-strong {
                color: #FFFFFF;
                font-size: 1.4rem;
                font-weight: 700;
                line-height: 1.1;
            }

            .ontop-profile-text {
                color: var(--text-primary);
                font-size: 0.95rem;
                line-height: 1.25;
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

            .ontop-mini-stats {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.75rem;
                margin: 0.65rem 0 0.35rem;
            }

            .ontop-mini-stat {
                padding: 0.85rem 0.95rem;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.95), rgba(6, 6, 9, 0.95));
            }

            .ontop-mini-stat-purple {
                background:
                    radial-gradient(circle at top right, rgba(124, 115, 247, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(27, 24, 57, 0.96), rgba(10, 10, 22, 0.96));
                border-color: rgba(124, 115, 247, 0.22);
            }

            .ontop-mini-stat-green {
                background:
                    radial-gradient(circle at top right, rgba(34, 197, 94, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(12, 40, 26, 0.96), rgba(6, 18, 11, 0.96));
                border-color: rgba(34, 197, 94, 0.22);
            }

            .ontop-mini-stat-coral {
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(40, 15, 25, 0.96), rgba(16, 7, 12, 0.96));
                border-color: rgba(227, 82, 118, 0.22);
            }

            .ontop-mini-stat-amber {
                background:
                    radial-gradient(circle at top right, rgba(245, 158, 11, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(45, 27, 9, 0.96), rgba(18, 11, 5, 0.96));
                border-color: rgba(245, 158, 11, 0.22);
            }

            .ontop-mini-stat-red {
                background:
                    radial-gradient(circle at top right, rgba(239, 68, 68, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(45, 14, 14, 0.96), rgba(20, 7, 7, 0.96));
                border-color: rgba(239, 68, 68, 0.22);
            }

            .ontop-mini-stat span {
                display: block;
                color: var(--text-muted);
                font-size: 0.78rem;
                margin-bottom: 0.3rem;
            }

            .ontop-mini-stat strong {
                display: block;
                color: #FFFFFF;
                font-size: 1.9rem;
                line-height: 1;
            }

            .ontop-compact-note {
                color: var(--text-secondary);
                font-size: 0.92rem;
                margin: 0.35rem 0 0.85rem;
            }

            .ontop-table-shell,
            .ontop-chart-shell {
                padding: 0;
                border-radius: 20px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(38, 28, 148, 0.12), transparent 28%),
                    linear-gradient(180deg, rgba(6, 6, 9, 0.96), rgba(26, 26, 36, 0.92));
                margin-bottom: 1rem;
                overflow: hidden;
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

            .ontop-status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.22rem 0.55rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0.03em;
                white-space: nowrap;
            }

            .ontop-status-badge::before {
                content: "";
                width: 0.45rem;
                height: 0.45rem;
                border-radius: 999px;
                background: currentColor;
                opacity: 0.9;
            }

            .ontop-status-green {
                background: rgba(34, 197, 94, 0.12);
                color: #7ee2a8;
                border: 1px solid rgba(34, 197, 94, 0.3);
            }

            .ontop-status-purple {
                background: rgba(124, 115, 247, 0.14);
                color: #b5afff;
                border: 1px solid rgba(124, 115, 247, 0.32);
            }

            .ontop-status-coral {
                background: rgba(227, 82, 118, 0.14);
                color: #ff9ab0;
                border: 1px solid rgba(227, 82, 118, 0.32);
            }

            .ontop-status-gray {
                background: rgba(184, 184, 200, 0.12);
                color: #d5d5df;
                border: 1px solid rgba(184, 184, 200, 0.24);
            }

            .ontop-status-amber {
                background: rgba(245, 158, 11, 0.12);
                color: #f8c56a;
                border: 1px solid rgba(245, 158, 11, 0.28);
            }

            .ontop-feedback-card {
                padding: 0.85rem 1rem;
                border-radius: 16px;
                border: 1px solid var(--border-color);
                background: rgba(6, 6, 9, 0.9);
                margin: 0.7rem 0 0.8rem;
            }

            .ontop-feedback-card strong,
            .ontop-feedback-card span {
                color: #FFFFFF;
            }

            .ontop-feedback-card p {
                margin: 0.35rem 0 0;
                color: var(--text-secondary);
                font-size: 0.9rem;
            }

            .ontop-toolbar {
                display: flex;
                align-items: end;
                justify-content: space-between;
                gap: 1rem;
                padding: 0.85rem 1rem;
                border: 1px solid var(--border-color);
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(26, 26, 36, 0.92), rgba(6, 6, 9, 0.92));
                margin-bottom: 0.75rem;
            }

            .ontop-toolbar-copy h3 {
                margin: 0;
            }

            .ontop-toolbar-copy p {
                margin: 0.25rem 0 0;
                color: var(--text-secondary);
            }

            .ontop-section-head {
                margin: 0.25rem 0 0.75rem;
            }

            .ontop-section-head h3 {
                margin: 0;
            }

            .ontop-section-head p {
                margin: 0.25rem 0 0;
                color: var(--text-secondary);
            }

            .ontop-product-grid {
                display: grid;
                grid-template-columns: repeat(5, minmax(0, 1fr));
                gap: 1rem;
                align-items: stretch;
            }

            .ontop-product-card {
                display: flex;
                flex-direction: column;
                gap: 0.8rem;
                padding: 1rem;
                min-height: 100%;
                border-radius: 22px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.96), rgba(6, 6, 9, 0.96));
            }

            .ontop-product-card-green {
                background:
                    radial-gradient(circle at top right, rgba(34, 197, 94, 0.18), transparent 35%),
                    linear-gradient(180deg, rgba(12, 40, 26, 0.96), rgba(6, 18, 11, 0.96));
                border-color: rgba(34, 197, 94, 0.24);
            }

            .ontop-product-card-purple {
                background:
                    radial-gradient(circle at top right, rgba(124, 115, 247, 0.16), transparent 35%),
                    linear-gradient(180deg, rgba(27, 24, 57, 0.96), rgba(10, 10, 22, 0.96));
                border-color: rgba(124, 115, 247, 0.24);
            }

            .ontop-product-card-coral {
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.12), transparent 35%),
                    linear-gradient(180deg, rgba(32, 16, 24, 0.96), rgba(9, 8, 12, 0.96));
            }

            .ontop-product-card h3 {
                margin: 0;
                font-size: 1.1rem;
            }

            .ontop-product-card p {
                margin: 0;
            }

            .ontop-product-desc {
                color: var(--text-muted);
                font-size: 0.88rem;
            }

            .ontop-product-pitch {
                color: #f2f2f7;
                font-size: 0.98rem;
                line-height: 1.45;
                min-height: 5.2rem;
            }

            .ontop-product-footer {
                margin-top: auto;
            }

            .ontop-product-state {
                padding-top: 0.2rem;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            }

            .ontop-product-state p {
                color: var(--text-secondary);
                font-size: 0.95rem;
                line-height: 1.45;
            }

            .ontop-control-strip {
                padding: 0.85rem 1rem;
                border-radius: 22px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.10), transparent 35%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.95), rgba(6, 6, 9, 0.95));
                margin-bottom: 0.8rem;
            }

            .ontop-sidebar-brand {
                padding: 0.15rem 0 0.95rem;
            }

            .ontop-sidebar-brand h1 {
                margin: 0;
                font-size: 2rem;
                line-height: 1;
            }

            .ontop-sidebar-brand p {
                margin: 0.45rem 0 0;
                color: var(--text-muted);
                font-size: 0.88rem;
            }

            .ontop-sidebar-section-label {
                margin: 1rem 0 0.45rem;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.72rem;
                font-weight: 700;
            }

            .ontop-sidebar-user {
                padding: 1rem;
                border-radius: 18px;
                border: 1px solid var(--border-color);
                background:
                    radial-gradient(circle at top right, rgba(227, 82, 118, 0.14), transparent 36%),
                    linear-gradient(180deg, rgba(26, 26, 36, 0.96), rgba(6, 6, 9, 0.96));
                margin-top: 1rem;
                margin-bottom: 0.75rem;
            }

            .ontop-sidebar-user strong {
                display: block;
                color: #FFFFFF;
                font-size: 1.05rem;
                margin-bottom: 0.35rem;
            }

            .ontop-sidebar-user span {
                color: var(--text-secondary);
                font-size: 0.9rem;
                word-break: break-word;
            }

            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
                width: 100%;
                display: flex;
                align-items: center;
                min-height: 2.9rem;
                padding: 0.7rem 0.9rem;
                margin-bottom: 0.35rem;
                border-radius: 16px;
                border: 1px solid transparent;
                background: rgba(255, 255, 255, 0.02);
                color: #FFFFFF;
                text-decoration: none;
                transition: border-color 120ms ease, background 120ms ease;
            }

            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
                border-color: rgba(124, 115, 247, 0.35);
                background: rgba(255, 255, 255, 0.05);
            }

            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
                border-color: rgba(124, 115, 247, 0.45);
                background: linear-gradient(135deg, rgba(38, 28, 148, 0.46), rgba(227, 82, 118, 0.26));
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
            }

            @media (max-width: 1200px) {
                .ontop-product-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }

            @media (max-width: 700px) {
                .ontop-product-grid {
                    grid-template-columns: 1fr;
                }

                .ontop-mini-stats {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_lead_admin_emails() -> set[str]:
    """Return the set of emails allowed to delete leads."""
    auth_cfg = st.secrets.get("auth", {})
    raw_value = auth_cfg.get("lead_admin_emails", [])

    if isinstance(raw_value, str):
        configured = {email.strip().lower() for email in raw_value.split(",") if email.strip()}
        return configured or LEAD_ADMIN_FALLBACK_EMAILS
    if isinstance(raw_value, list):
        configured = {str(email).strip().lower() for email in raw_value if str(email).strip()}
        return configured or LEAD_ADMIN_FALLBACK_EMAILS
    return LEAD_ADMIN_FALLBACK_EMAILS


def can_delete_leads() -> bool:
    """Check if the current signed-in user can delete leads."""
    agent_email = st.session_state.get("agent_email", "") or getattr(st.user, "email", "")
    return agent_email.lower() in get_lead_admin_emails()


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
        st.markdown(
            """
            <div class="ontop-sidebar-brand">
                <h1>CX Sales Agent</h1>
                <p>Lead qualification workspace</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="ontop-sidebar-section-label">Workspace</div>', unsafe_allow_html=True)
        st.page_link("pages/1_User_Lookup.py", label="User Lookup")
        st.page_link("pages/2_My_Leads.py", label="My Leads")
        st.page_link("pages/3_Dashboard.py", label="Dashboard")

        st.markdown('<div class="ontop-sidebar-section-label">Utilities</div>', unsafe_allow_html=True)

        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared — data will reload on next query.")

        st.caption("Data is cached for 1 hour. Use refresh to reload the latest data.")

        st.markdown(
            f"""
            <div class="ontop-sidebar-user">
                <strong>{st.session_state['agent_name']}</strong>
                <span>{st.session_state['agent_email']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign out", use_container_width=True):
            st.logout()
