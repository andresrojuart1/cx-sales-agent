"""Shared components used across all pages."""

import streamlit as st


def render_sidebar():
    """Render the common sidebar with agent name and cache controls."""
    with st.sidebar:
        st.title("CX Sales Agent")
        st.divider()

        st.text_input(
            "Your Name",
            key="agent_name",
            placeholder="Enter your name...",
        )

        st.divider()

        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared — data will reload on next query.")

        st.caption("Data is cached for 1 hour. Click above to force a refresh.")
