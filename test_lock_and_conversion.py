"""Test the opportunity-lock and auto-conversion functions.

Run:  python test_lock_and_conversion.py

Requires a .env with SUPABASE_URL, SUPABASE_KEY, and Redshift credentials.
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

TABLE = "cx_leads"
client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

LOCK_WINDOW_DAYS = 60


# ── 1. Test check_opportunity_lock ──────────────────────────────────────────

def check_opportunity_lock(cr_code: str, product: str) -> dict | None:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=LOCK_WINDOW_DAYS)).isoformat()
    result = (
        client.table(TABLE)
        .select("id, agent_name, agent_email, status, created_at")
        .eq("cr_code", cr_code)
        .eq("product", product)
        .in_("status", ["Qualified", "Contacted"])
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


print("=" * 60)
print("1. Testing check_opportunity_lock()")
print("=" * 60)

# Grab a recent active lead to test with
sample = (
    client.table(TABLE)
    .select("cr_code, product, agent_name, agent_email, status, created_at")
    .in_("status", ["Qualified", "Contacted"])
    .order("created_at", desc=True)
    .limit(1)
    .execute()
)

if sample.data:
    row = sample.data[0]
    print(f"  Sample active lead: {row['cr_code']} / {row['product']} "
          f"by {row['agent_name']} ({row['status']}, {row['created_at'][:10]})")

    lock = check_opportunity_lock(row["cr_code"], row["product"])
    if lock:
        print(f"  Lock check result: LOCKED by {lock['agent_name']} "
              f"(email: {lock['agent_email']})")
        created = datetime.fromisoformat(lock["created_at"])
        days_left = LOCK_WINDOW_DAYS - (datetime.now(timezone.utc) - created).days
        print(f"  Days remaining: ~{max(days_left, 0)}")
    else:
        print("  Lock check result: AVAILABLE (no active lock)")

    # Test with a fake cr_code that shouldn't be locked
    fake_lock = check_opportunity_lock("CR000000", "quick")
    print(f"\n  Fake CR000000/quick lock: {'LOCKED' if fake_lock else 'AVAILABLE (correct)'}")
else:
    print("  No active leads found — nothing to test lock against.")
    print("  Try creating a lead first via the app, then re-run.")


# ── 2. Test expire_stale_leads (dry run) ────────────────────────────────────

print("\n" + "=" * 60)
print("2. Testing expire_stale_leads (DRY RUN — read only)")
print("=" * 60)

cutoff = (datetime.now(timezone.utc) - timedelta(days=LOCK_WINDOW_DAYS)).isoformat()
stale = (
    client.table(TABLE)
    .select("id, cr_code, product, agent_name, status, created_at")
    .in_("status", ["Qualified", "Contacted"])
    .lt("created_at", cutoff)
    .execute()
)
print(f"  Leads that WOULD be expired: {len(stale.data)}")
for row in stale.data[:5]:
    print(f"    {row['cr_code']} / {row['product']} — {row['agent_name']} "
          f"({row['status']}, {row['created_at'][:10]})")
if len(stale.data) > 5:
    print(f"    ... and {len(stale.data) - 5} more")


# ── 3. Test conversion check (dry run) ─────────────────────────────────────

print("\n" + "=" * 60)
print("3. Testing conversion check (DRY RUN — read only)")
print("=" * 60)

try:
    import psycopg2
    import pandas as pd

    conn = psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=os.environ["REDSHIFT_PORT"],
        dbname=os.environ["REDSHIFT_DBNAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )

    def query_set(sql):
        df = pd.read_sql_query(sql, conn)
        return set(df.iloc[:, 0].dropna())

    print("  Loading transaction sets from Redshift...")
    txn_sets = {
        "quick": query_set("""
            SELECT DISTINCT c.cod_contractor
            FROM process_data.wallet_transaction wt
            LEFT JOIN raw_data.raw_ops_top_up_history msgj ON msgj.wallet_transaction_id = wt.id_transaction
            JOIN process_data.contractor c ON c.id_contractor = wt.id_contractor
            LEFT JOIN raw_data.raw_ops_top_up_upload msg ON msg.id = msgj.ops_top_up_upload_id
            WHERE (msg.message ILIKE 'Quick%%' OR wt.des_transaction_type ILIKE 'Quick%%')
                OR wt.id_transaction IN ('1989950','1989951','1989952','2004982','2004981',
                    '1989953','2004980','1989954','2003004','2012763','2012768','2012771',
                    '2012764','2012775','2012767','2012769','2012765','2012773','2012776',
                    '2012770','2012772','2012778','2012766','2025755','2025754','2012777')
        """),
        "future_fund": query_set("""
            SELECT DISTINCT c.cod_contractor
            FROM process_data.wallet_transaction wt
            LEFT JOIN raw_data.raw_ops_top_up_history msgj ON msgj.wallet_transaction_id = wt.id_transaction
            LEFT JOIN raw_data.raw_ops_top_up_upload msg ON msg.id = msgj.ops_top_up_upload_id
            JOIN process_data.contractor c ON c.id_contractor = wt.id_contractor
            WHERE BTRIM(msg.message) ILIKE 'future%%'
        """),
        "tapi": query_set("""
            SELECT DISTINCT c.cod_contractor
            FROM process_data.wallet_transaction wt
            JOIN process_data.contractor c ON c.id_contractor = wt.id_contractor
            WHERE wt.des_transaction_type = 'UTILITIES_PAYMENT'
        """),
        "esim": query_set("""
            SELECT DISTINCT c.cod_contractor
            FROM process_data.wallet_transaction wt
            LEFT JOIN raw_data.raw_ops_top_up_history msgj ON msgj.wallet_transaction_id = wt.id_transaction
            LEFT JOIN raw_data.raw_ops_top_up_upload msg ON msg.id = msgj.ops_top_up_upload_id
            JOIN process_data.contractor c ON c.id_contractor = wt.id_contractor
            WHERE msg.message IS NOT NULL
              AND msg.message IN ('E-sim','E-sim Debit','Esim Refund','Esim Return','Esim Debit')
        """),
    }

    for product, s in txn_sets.items():
        print(f"    {product}: {len(s)} contractors with transactions")

    conn.close()

    # Get active leads and check for matches
    active = (
        client.table(TABLE)
        .select("id, cr_code, product, agent_name, status")
        .in_("status", ["Qualified", "Contacted"])
        .execute()
    )

    would_convert = []
    for lead in active.data:
        txn_set = txn_sets.get(lead["product"])
        if txn_set and lead["cr_code"] in txn_set:
            would_convert.append(lead)

    print(f"\n  Active leads checked: {len(active.data)}")
    print(f"  Leads that WOULD be auto-converted: {len(would_convert)}")
    for lead in would_convert[:10]:
        print(f"    {lead['cr_code']} / {lead['product']} — {lead['agent_name']}")
    if len(would_convert) > 10:
        print(f"    ... and {len(would_convert) - 10} more")

except Exception as e:
    print(f"  Redshift connection failed: {e}")
    print("  Skipping conversion check test.")


print("\n" + "=" * 60)
print("All tests complete (no data was modified).")
print("=" * 60)
