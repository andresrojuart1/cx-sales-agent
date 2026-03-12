"""Redirect the root app entry to the main workspace page."""

import streamlit as st

st.set_page_config(
    page_title="CX Sales Agent",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.switch_page("pages/1_User_Lookup.py")
