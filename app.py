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

st.markdown(
    f"""
    <section class="ontop-hero">
        <span class="ontop-eyebrow">CX Sales Agent</span>
        <h1>Revenue workflows, lead qualification, and eligibility in one place.</h1>
        <p>Signed in as {st.session_state['agent_name']}. Use the workspace to identify qualified users, capture leads, and track team performance.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Lookup", "Contractors", "Search by CR, name, or email")
    st.caption("Review profile data and product eligibility before creating a lead.")

with col2:
    st.metric("Pipeline", "My Leads", "Own and update lead status")
    st.caption("Track qualified opportunities and move them through the workflow.")

with col3:
    st.metric("Visibility", "Dashboard", "Team-wide performance")
    st.caption("Monitor conversion, activity, and product performance across agents.")

st.divider()
st.subheader("Workspace")
st.markdown(
    """
    - **User Lookup**: Search a contractor, inspect profile details, and identify eligible products.
    - **My Leads**: Review your pipeline, filter by product or status, and update outcomes.
    - **Dashboard**: Check team metrics, conversion trends, and activity by product or agent.
    """
)
