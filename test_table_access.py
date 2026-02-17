"""Test SELECT access to every table the app needs."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    host=os.environ["REDSHIFT_HOST"],
    port=os.environ["REDSHIFT_PORT"],
    dbname=os.environ["REDSHIFT_DBNAME"],
    user=os.environ["REDSHIFT_USER"],
    password=os.environ["REDSHIFT_PASSWORD"],
)
cur = conn.cursor()

tables = [
    "process_data.wallet_transaction",
    "process_data.contractor",
    "process_data.contract",
    "process_data.plan_subscription",
    "raw_data.raw_ops_top_up_history",
    "raw_data.raw_ops_top_up_upload",
    "internal.lkp_contractor_pii",
]

for table in tables:
    try:
        cur.execute(f"SELECT 1 FROM {table} LIMIT 1")
        cur.fetchone()
        print(f"  OK    {table}")
    except Exception as e:
        conn.rollback()
        msg = str(e).strip().split("\n")[0]
        print(f"  FAIL  {table} -- {msg}")

cur.close()
conn.close()
