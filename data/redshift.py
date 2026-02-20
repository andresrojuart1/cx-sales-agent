"""Redshift connection and cached query functions."""

import pandas as pd
import psycopg2
import streamlit as st


def get_connection():
    """Create a new Redshift connection from st.secrets."""
    cfg = st.secrets["redshift"]
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


def _query_to_df(sql: str) -> pd.DataFrame:
    """Execute a query and return results as a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df


# ---------------------------------------------------------------------------
# Contractor profile (uncached — per-user, on-demand)
# ---------------------------------------------------------------------------

def get_contractor_profile(cr_code: str) -> dict | None:
    """Look up a single contractor by CR code. Returns dict or None."""
    sql = """
        SELECT
            cod_contractor,
            full_name,
            first_name,
            last_name,
            des_email,
            des_phone,
            des_residence_country,
            des_residence_city,
            des_wallet_status,
            amt_wallet_balance,
            has_active_contract,
            is_active_contractor,
            amt_monthly_compensation_usd,
            des_contractor_type,
            dat_creation
        FROM process_data.contractor
        WHERE cod_contractor = %s
        LIMIT 1
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, (cr_code,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [desc[0] for desc in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def search_contractors(search_term: str, limit: int = 20) -> pd.DataFrame:
    """Search contractors by CR code, email, or name. Returns top matches."""
    sql = """
        SELECT
            cod_contractor,
            full_name,
            des_email,
            des_residence_country
        FROM process_data.contractor
        WHERE cod_contractor ILIKE %s
           OR des_email ILIKE %s
           OR full_name ILIKE %s
        LIMIT %s
    """
    pattern = f"%{search_term}%"
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=(pattern, pattern, pattern, limit))
    finally:
        conn.close()
    return df


# ---------------------------------------------------------------------------
# Transaction sets (cached — return distinct cod_contractor sets)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Loading Quick transactions...")
def get_quick_transactions() -> set:
    """Distinct cod_contractor values with Quick transactions."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.wallet_transaction wt
        LEFT JOIN raw_data.raw_ops_top_up_history msgj
            ON msgj.wallet_transaction_id = wt.id_transaction
        JOIN process_data.contractor c
            ON c.id_contractor = wt.id_contractor
        LEFT JOIN raw_data.raw_ops_top_up_upload msg
            ON msg.id = msgj.ops_top_up_upload_id
        WHERE
            (
                msg.message ILIKE 'Quick%%' OR
                wt.des_transaction_type ILIKE 'Quick%%'
            )
            OR wt.id_transaction IN (
                '1989950', '1989951', '1989952', '2004982', '2004981',
                '1989953', '2004980', '1989954', '2003004', '2012763',
                '2012768', '2012771', '2012764', '2012775', '2012767',
                '2012769', '2012765', '2012773', '2012776', '2012770',
                '2012772', '2012778', '2012766', '2025755', '2025754',
                '2012777'
            )
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


@st.cache_data(ttl=3600, show_spinner="Loading Future Fund transactions...")
def get_future_fund_transactions() -> set:
    """Distinct cod_contractor values with Future Fund transactions."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.wallet_transaction wt
        LEFT JOIN raw_data.raw_ops_top_up_history msgj
            ON msgj.wallet_transaction_id = wt.id_transaction
        LEFT JOIN raw_data.raw_ops_top_up_upload msg
            ON msg.id = msgj.ops_top_up_upload_id
        JOIN process_data.contractor c
            ON c.id_contractor = wt.id_contractor
        WHERE BTRIM(msg.message) ILIKE 'future%%'
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


@st.cache_data(ttl=3600, show_spinner="Loading Tapi transactions...")
def get_tapi_transactions() -> set:
    """Distinct cod_contractor values with Tapi transactions."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.wallet_transaction wt
        JOIN process_data.contractor c
            ON c.id_contractor = wt.id_contractor
        WHERE wt.des_transaction_type = 'UTILITIES_PAYMENT'
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


@st.cache_data(ttl=3600, show_spinner="Loading E-Sim transactions...")
def get_esim_transactions() -> set:
    """Distinct cod_contractor values with E-Sim transactions."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.wallet_transaction wt
        LEFT JOIN raw_data.raw_ops_top_up_history msgj
            ON msgj.wallet_transaction_id = wt.id_transaction
        LEFT JOIN raw_data.raw_ops_top_up_upload msg
            ON msg.id = msgj.ops_top_up_upload_id
        JOIN process_data.contractor c
            ON c.id_contractor = wt.id_contractor
        WHERE msg.message IS NOT NULL
          AND msg.message IN (
                'E-sim', 'E-sim Debit', 'Esim Refund',
                'Esim Return', 'Esim Debit'
          )
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


# ---------------------------------------------------------------------------
# Audience sets (cached — from Redshift)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Loading Tapi segment...")
def get_tapi_segment() -> set:
    """Distinct cod_contractor values eligible for Tapi."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.contractor c
        JOIN process_data.contract c2
            ON c2.id_contractor = c.id_contractor
        WHERE c.cod_residence_country IN ('COL','MEX','ARG','PER','CHL')
          AND c2.des_state IN ('ACTIVE')
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


@st.cache_data(ttl=3600, show_spinner="Loading Reserve audience...")
def get_reserve_audience() -> set:
    """Distinct cod_contractor values eligible for Reserve (pre-filtered)."""
    sql = """
        SELECT DISTINCT c.cod_contractor
        FROM process_data.plan_subscription ps
        JOIN process_data.contractor c
            ON c.id_contractor = ps.id_contractor
        WHERE ps.is_enabled = true
          AND cod_plan = 'RESERVE'
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())


@st.cache_data(ttl=3600, show_spinner="Loading active contractors...")
def get_all_active_contractors() -> set:
    """All active cod_contractor values (E-Sim audience = everyone)."""
    sql = """
        SELECT cod_contractor
        FROM process_data.contractor
        WHERE is_active_contractor = 1
    """
    df = _query_to_df(sql)
    return set(df["cod_contractor"].dropna())
