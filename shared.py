"""Shared components used across all pages."""

import streamlit as st

ALLOWED_DOMAIN = "getontop.com"


def require_auth():
    """Centralized authentication guard.

    - If not logged in, show sign-in prompt and stop.
    - If email is missing, fail closed.
    - If email domain is not allowed, deny access.
    - If authorized, populate session state with agent identity.
    """
    # DEBUG — remove after login is working
    with st.expander("DEBUG: st.user"):
        st.json({
            "is_logged_in": st.user.is_logged_in,
            "email": getattr(st.user, "email", "N/A"),
            "name": getattr(st.user, "name", "N/A"),
        })

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
