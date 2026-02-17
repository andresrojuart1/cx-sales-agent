"""Quick test: verify connections to Supabase and Redshift."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
print("Testing Supabase...")
try:
    from supabase import create_client

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    result = client.table("risk_matrix").select("id, des_email, decision").limit(3).execute()
    print(f"  Connected. risk_matrix rows returned: {len(result.data)}")
    for row in result.data:
        print(f"    {row}")
except Exception as e:
    print(f"  FAILED: {e}")

print()

# --- Redshift ---
print("Testing Redshift...")
try:
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=os.environ["REDSHIFT_PORT"],
        dbname=os.environ["REDSHIFT_DBNAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    count = cur.fetchone()[0]
    print(f"  Connected. Public tables found: {count}")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10")
    tables = [row[0] for row in cur.fetchall()]
    print(f"  Sample tables: {tables}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"  FAILED: {e}")

print("\nDone.")
