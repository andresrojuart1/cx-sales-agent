"""Validate rewritten Redshift queries against Excel snapshot counts."""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

EXPECTED = {
    "Quick transactions": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
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
        """,
        "expected_approx": 2615,
        "note": "~unique CRs from 2,615 rows (may be fewer distinct)",
    },
    "Future Fund transactions": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
            FROM process_data.wallet_transaction wt
            LEFT JOIN raw_data.raw_ops_top_up_history msgj
                ON msgj.wallet_transaction_id = wt.id_transaction
            LEFT JOIN raw_data.raw_ops_top_up_upload msg
                ON msg.id = msgj.ops_top_up_upload_id
            JOIN process_data.contractor c
                ON c.id_contractor = wt.id_contractor
            WHERE BTRIM(msg.message) ILIKE 'future%%'
        """,
        "expected_approx": 1448,
        "note": "~unique CRs from 1,448 rows (may be fewer distinct)",
    },
    "Tapi transactions": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
            FROM process_data.wallet_transaction wt
            JOIN process_data.contractor c
                ON c.id_contractor = wt.id_contractor
            WHERE wt.des_transaction_type = 'UTILITIES_PAYMENT'
        """,
        "expected_approx": 5911,
        "note": "~unique CRs from 5,911 rows (may be fewer distinct)",
    },
    "E-Sim transactions": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
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
        """,
        "expected_approx": 21,
        "note": "~unique CRs from 21 rows",
    },
    "Tapi segment": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
            FROM process_data.contractor c
            JOIN process_data.contract c2
                ON c2.id_contractor = c.id_contractor
            WHERE c.cod_residence_country IN ('COL','MEX','ARG','PER','CHL')
              AND c2.des_state IN ('ACTIVE')
        """,
        "expected_approx": 11358,
        "note": "~11,358",
    },
    "Reserve audience": {
        "sql": """
            SELECT COUNT(DISTINCT c.cod_contractor) AS cnt
            FROM process_data.plan_subscription ps
            JOIN process_data.contractor c
                ON c.id_contractor = ps.id_contractor
            WHERE ps.is_enabled = true
              AND cod_plan = 'RESERVE'
        """,
        "expected_approx": 742,
        "note": "~742",
    },
}

THRESHOLD = 0.05


def main():
    conn = psycopg2.connect(
        host=os.environ["REDSHIFT_HOST"],
        port=os.environ["REDSHIFT_PORT"],
        dbname=os.environ["REDSHIFT_DBNAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )
    cur = conn.cursor()

    all_ok = True
    print("=" * 72)
    print("VALIDATION: Rewritten queries vs Excel snapshot counts")
    print("=" * 72)

    for name, info in EXPECTED.items():
        try:
            cur.execute(info["sql"])
            actual = cur.fetchone()[0]
            expected = info["expected_approx"]
            diff_pct = abs(actual - expected) / max(expected, 1)
            flag = "FLAG" if diff_pct > THRESHOLD else "OK"
            if flag == "FLAG":
                all_ok = False
            print(
                f"\n{name}:\n"
                f"  Live count:     {actual:>8,}\n"
                f"  Excel snapshot: {expected:>8,}  ({info['note']})\n"
                f"  Diff:           {diff_pct:>7.1%}  [{flag}]"
            )
        except Exception as e:
            all_ok = False
            print(f"\n{name}:\n  ERROR: {e}")
            conn.rollback()

    cur.close()
    conn.close()

    print("\n" + "=" * 72)
    if all_ok:
        print("RESULT: All queries within 5% threshold. Migration looks good.")
    else:
        print("RESULT: Some queries flagged — review diffs above.")
    print("=" * 72)


if __name__ == "__main__":
    main()
