"""CX Sales Agent Tool — Main entry point."""

import streamlit as st

from shared import render_sidebar

st.set_page_config(
    page_title="CX Sales Agent",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

# --- Main page ---
st.header("Welcome to the CX Sales Agent Tool")

st.markdown(f"Logged in as: **{st.session_state['agent_name']}**")

st.markdown("""
Use the sidebar to navigate between pages:

- **User Lookup** — Search for a contractor, see product eligibility, and mark qualified leads.
- **My Leads** — View and manage your submitted leads.
- **Dashboard** — Performance overview and team stats.
""")
