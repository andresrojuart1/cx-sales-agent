# PII Table Migration: Removing `internal.lkp_contractor_pii`

> **Date**: 2026-02-15
> **Reason**: The Redshift user `jdaza` does not have `SELECT` permission on `internal.lkp_contractor_pii`. All other required tables are accessible.

---

## What is `lkp_contractor_pii`?

A lookup table in the `internal` schema that maps **hashed contractor codes** to **real contractor codes** and PII data.

| Column | Type | Purpose |
|---|---|---|
| `hash_cod_contractor` | varchar | The hashed/obfuscated contractor code stored in `wallet_transaction.cod_contractor` |
| `cod_contractor` | varchar | The real CR code (e.g. `CR034116`) |
| `des_email` | varchar | The contractor's email |
| `full_name` | varchar | The contractor's full name |

### Why it exists

The `wallet_transaction` table stores contractor identifiers in the `cod_contractor` column, but these can be either:
1. **Real CR codes** (e.g. `CR034116`) — directly usable
2. **Hashed/obfuscated codes** — need the PII table to resolve back to real CR codes

The PII table bridges this gap. Without it, some transaction rows might have unresolvable contractor codes.

---

## How it was used (BEFORE)

Every transaction query joined the PII table with this pattern:

```sql
-- Join
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = wt.cod_contractor

-- Resolution
CASE
    WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
    ELSE c.cod_contractor  -- fallback to contractor table
END AS cod_contractor
```

**Logic**: If the PII table can resolve `wt.cod_contractor` (the hash) into a real CR code, use that. Otherwise, fall back to the `process_data.contractor` table (joined via `wt.id_contractor`).

### Affected queries

| Query | PII Join | Fallback |
|---|---|---|
| **Quick transactions** | `pi.hash_cod_contractor = wt.cod_contractor` | `c.cod_contractor` via `c.id_contractor = wt.id_contractor` |
| **Future Fund transactions** | `pi.hash_cod_contractor = wt.cod_contractor` | `wt.cod_contractor` directly (no contractor join in original) |
| **Tapi transactions** | `pi.hash_cod_contractor = wt.cod_contractor` | `c.cod_contractor` via `c.id_contractor = wt.id_contractor` |
| **E-Sim transactions** | `pi.hash_cod_contractor = wt.cod_contractor` | `wt.cod_contractor` directly (no contractor join in original) |
| **Tapi segment** | `pi.hash_cod_contractor = c.cod_contractor` | `c.cod_contractor` directly |
| **Reserve audience** | `pi.hash_cod_contractor = c.cod_contractor` | `c.cod_contractor` directly |

---

## What changes (AFTER)

Remove all `internal.lkp_contractor_pii` joins. Resolve contractor codes through `process_data.contractor` instead.

### New resolution strategy per query

#### 1. Quick transactions

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj
    ON msgj.wallet_transaction_id = wt.id_transaction
LEFT JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
LEFT JOIN raw_data.raw_ops_top_up_upload msg
    ON msg.id = msgj.ops_top_up_upload_id
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = wt.cod_contractor
WHERE (msg.message ILIKE 'Quick%' OR wt.des_transaction_type ILIKE 'Quick%')
   OR wt.id_transaction IN ('1989950', ...)
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj
    ON msgj.wallet_transaction_id = wt.id_transaction
JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
LEFT JOIN raw_data.raw_ops_top_up_upload msg
    ON msg.id = msgj.ops_top_up_upload_id
WHERE (msg.message ILIKE 'Quick%' OR wt.des_transaction_type ILIKE 'Quick%')
   OR wt.id_transaction IN ('1989950', ...)
```

**Change**: Removed PII join. Changed contractor join from `LEFT JOIN` to `JOIN` (INNER) — if there's no matching contractor, we can't resolve the code anyway. Uses `c.cod_contractor` directly.

---

#### 2. Future Fund transactions

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE wt.cod_contractor
    END AS cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj ...
LEFT JOIN raw_data.raw_ops_top_up_upload msg ...
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = wt.cod_contractor
WHERE BTRIM(msg.message) ILIKE 'future%'
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj ...
LEFT JOIN raw_data.raw_ops_top_up_upload msg ...
JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
WHERE BTRIM(msg.message) ILIKE 'future%'
```

**Change**: Removed PII join. Added contractor join (was missing in original — the original fell back to `wt.cod_contractor` which could be hashed). Now resolves via contractor table.

---

#### 3. Tapi transactions

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = wt.cod_contractor
WHERE wt.des_transaction_type = 'UTILITIES_PAYMENT'
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.wallet_transaction wt
JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
WHERE wt.des_transaction_type = 'UTILITIES_PAYMENT'
```

**Change**: Removed PII join. Changed contractor join to INNER. Direct `c.cod_contractor`.

---

#### 4. E-Sim transactions

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE wt.cod_contractor
    END AS cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj ...
LEFT JOIN raw_data.raw_ops_top_up_upload msg ...
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = wt.cod_contractor
WHERE msg.message IN ('E-sim', 'E-sim Debit', 'Esim Refund', 'Esim Return', 'Esim Debit')
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.wallet_transaction wt
LEFT JOIN raw_data.raw_ops_top_up_history msgj ...
LEFT JOIN raw_data.raw_ops_top_up_upload msg ...
JOIN process_data.contractor c
    ON c.id_contractor = wt.id_contractor
WHERE msg.message IN ('E-sim', 'E-sim Debit', 'Esim Refund', 'Esim Return', 'Esim Debit')
```

**Change**: Removed PII join. Added contractor join (was missing). Direct `c.cod_contractor`.

---

#### 5. Tapi segment

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor
FROM process_data.contractor c
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = c.cod_contractor
LEFT JOIN process_data.contract c2
    ON c2.id_contractor = c.id_contractor
WHERE c.cod_residence_country IN ('COL','MEX','ARG','PER','CHL')
  AND c2.des_state IN ('ACTIVE')
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.contractor c
JOIN process_data.contract c2
    ON c2.id_contractor = c.id_contractor
WHERE c.cod_residence_country IN ('COL','MEX','ARG','PER','CHL')
  AND c2.des_state IN ('ACTIVE')
```

**Change**: Removed PII join. The contractor table already has the real `cod_contractor` — the PII lookup was redundant here (it was resolving `c.cod_contractor` against itself essentially). No data loss.

---

#### 6. Reserve audience

**BEFORE:**
```sql
SELECT DISTINCT
    CASE
        WHEN pi.cod_contractor IS NOT NULL THEN pi.cod_contractor
        ELSE c.cod_contractor
    END AS cod_contractor
FROM process_data.plan_subscription ps
LEFT JOIN process_data.contractor c
    ON c.id_contractor = ps.id_contractor
LEFT JOIN internal.lkp_contractor_pii pi
    ON pi.hash_cod_contractor = c.cod_contractor
WHERE ps.is_enabled = true AND cod_plan = 'RESERVE'
```

**AFTER:**
```sql
SELECT DISTINCT c.cod_contractor
FROM process_data.plan_subscription ps
JOIN process_data.contractor c
    ON c.id_contractor = ps.id_contractor
WHERE ps.is_enabled = true AND cod_plan = 'RESERVE'
```

**Change**: Removed PII join. Same as Tapi segment — the PII lookup was resolving the contractor table's own `cod_contractor`, which is redundant. No data loss.

---

## Risk Assessment

### No risk (safe changes)
- **Tapi segment** and **Reserve audience**: The PII table was joining on `c.cod_contractor` from the contractor table itself. Since the contractor table already has real CR codes, the PII join was doing nothing useful. **Zero data difference expected.**
- **Quick transactions** and **Tapi transactions**: Already had a contractor join via `c.id_contractor = wt.id_contractor`. The PII table was only a secondary resolution path. Changing from `LEFT JOIN` to `JOIN` on contractor means we only lose rows where `wt.id_contractor` has no matching contractor — these would be orphaned transactions with no known user (can't use them for eligibility anyway).

### Low risk (minor potential difference)
- **Future Fund transactions** and **E-Sim transactions**: The original queries did NOT join the contractor table — they fell back to `wt.cod_contractor` directly (which could be hashed). We now add a contractor join. This means:
  - If `wt.cod_contractor` was a **real CR code** → no difference (contractor table has the same code)
  - If `wt.cod_contractor` was a **hashed code** AND `wt.id_contractor` links to the contractor table → we now correctly resolve it (improvement)
  - If `wt.cod_contractor` was a **hashed code** AND `wt.id_contractor` is NULL → we lose this row (transaction can't be attributed to anyone)

### Validation plan
After applying the changes, compare row counts from the new queries against the Excel snapshot counts:

| Query | Excel Count | Expected Match |
|---|---|---|
| Quick transactions (distinct CR codes) | ~unique from 2,615 rows | Close match |
| Future Fund transactions (distinct CR codes) | ~unique from 1,448 rows | Close match |
| Tapi transactions (distinct CR codes) | ~unique from 5,911 rows | Close match |
| E-Sim transactions (distinct CR codes) | ~unique from 21 rows | Exact or close |
| Tapi segment | ~11,358 | Exact match expected |
| Reserve audience | ~742 | Exact match expected |

---

## Summary

| Query | Change Type | Risk | Expected Data Impact |
|---|---|---|---|
| Quick transactions | Remove PII, use existing contractor join | None | Same results |
| Future Fund transactions | Remove PII, add contractor join | Low | May lose rows with NULL id_contractor |
| Tapi transactions | Remove PII, use existing contractor join | None | Same results |
| E-Sim transactions | Remove PII, add contractor join | Low | May lose rows with NULL id_contractor |
| Tapi segment | Remove PII (was redundant) | None | Identical results |
| Reserve audience | Remove PII (was redundant) | None | Identical results |
