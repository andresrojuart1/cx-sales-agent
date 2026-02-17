# CX Sales Agent Tool — Implementation Workflow

> **Project**: Sales Tool for Customer Experience Agents
> **Objective**: Enable CX agents to identify eligible users, offer add-on products, and track qualified leads for commission.
> **Generated**: 2026-02-15
> **Updated**: 2026-02-15 — Live data architecture (Redshift + Supabase from Day 1)

---

## Executive Summary

Build an internal web application that CX agents use during support interactions. When a user contacts support, the agent looks up their identifier (`cod_contractor` / CR Code) and instantly sees which products the user is **eligible** for but **not yet using**. The agent can then pitch the product, record the interaction, and mark the user as a qualified lead.

---

## Data Landscape

### Live Data Sources (Production Architecture)

The tool reads **live** from two databases — no Excel intermediary.

#### Redshift (Primary — Transaction & User Data)
SQL queries available in `queries.sql`. Key schemas: `process_data`, `raw_data`, `internal`.

| What | Source | Key Columns | Status |
|---|---|---|---|
| All active contractors | `process_data.contractor` | cod_contractor, full_name, des_email, des_residence_country, + many more | **READY** — DDL in queries.sql |
| Quick transactions | `process_data.wallet_transaction` + joins | cod_contractor, amt_transaction, message | **READY** — query in queries.sql |
| Future Fund transactions | `process_data.wallet_transaction` + joins | cod_contractor, amt_transaction, message | **READY** — query in queries.sql |
| Tapi transactions | `process_data.wallet_transaction` + joins | cod_contractor, des_transaction_type | **READY** — query in queries.sql |
| Tapi segment (audience) | `process_data.contractor` + `process_data.contract` | cod_contractor, des_email, full_name, country (COL/MEX/ARG/PER/CHL + active contract) | **READY** — query in queries.sql |
| E-Sim transactions | `process_data.wallet_transaction` + joins | cod_contractor, message | **READY** — query in queries.sql |
| Reserve audience | `process_data.plan_subscription` + joins | cod_contractor (is_enabled=true, cod_plan='RESERVE') | **READY** — query in queries.sql |

#### Supabase (Audiences + Risk Matrix + Lead Storage)

| What | Table | Key | Status |
|---|---|---|---|
| Quick audience | `quick_audience` | CR_Code (PK), external_id, company_email, client_requester, name_requester, CL_Code | **READY** — uploaded from Excel |
| Future Fund audience | `ff_audience` | CR_Code (PK), external_id, name_requester, company_email, uid | **READY** — uploaded from Excel |
| Risk Matrix | `risk_matrix` | des_email, decision ('Approved' / 'Not approved') | **READY** |
| Quick contract events | `quick_contract_events` | contract_token, worker_email, final_status | **EXISTS** |
| Loan fee tiers | `loan_fee_tiers` | min_amount, max_amount, installments, fixed_fee | **EXISTS** |
| Leads | `cx_leads` (new) | To be created — stores qualified leads | **PENDING** |
| Agents | `cx_agents` (new) | To be created — agent profiles | **PENDING** |

### Key Identifier
- **`cod_contractor`** (CR Code, e.g. `CR034116`) is the universal user identifier across all data sources.

### Excel Reference (for validation only)
The file `New iniciatives - Wallet.xlsx` contains snapshot exports from these same queries. Used only to validate that our live queries return consistent data during development.

---

## Eligibility Logic per Product

### 1. Quick (Earned Wage Advance)
```
Eligible = Quick Audience (Supabase: quick_audience)
         − Users with Quick transactions (Redshift)
         − Users rejected by Risk Matrix (Supabase: risk_matrix, joined via email)
```
- **Audience source**: Supabase `quick_audience` table (uploaded from Excel, ~7,733 rows)
- **Exclusion 1**: Any `CR_Code` with existing Quick transactions (Redshift)
- **Exclusion 2**: Any user whose email matches `risk_matrix.des_email` WHERE `decision = 'Not approved'`

### 2. Future Fund (Investment Product)
```
Eligible = Future Fund Audience (Supabase: ff_audience)
         − Users with Future Fund transactions (Redshift)
```
- **Audience source**: Supabase `ff_audience` table (uploaded from Excel, ~18,996 rows)
- **Exclusion**: Any `CR_Code` with existing Future Fund transactions (Redshift)

### 3. Tapi (Bill Pay Service)
```
Eligible = Tapi Segment (Redshift)
         − Users with Tapi transactions (Redshift)
```
- **Audience source**: Redshift segment query
- **Exclusion**: Any `cod_contractor` with existing Tapi (UTILITIES_PAYMENT) transactions

### 4. E-Sim
```
Eligible = All Active Contractors (Redshift `contractor` table)
         − Users with E-Sim transactions (Redshift)
```
- **Audience source**: Redshift `contractor` table — every active contractor is eligible
- **Exclusion**: Any `cod_contractor` with existing E-Sim transactions

### 5. Reserve (Visa Debit Card Benefits)
```
Eligible = Reserve Audience (Redshift)
         (already filtered — only includes eligible + not-yet-enrolled)
```
- **Audience source**: Redshift Reserve audience query — pre-filtered to eligible, non-enrolled users
- **No additional exclusions needed** — the query handles it

---

## Architecture Decision

### Recommended: Python + Streamlit (Internal Tool)

**Why Streamlit:**
- Fast to build for internal tools (CX agents only, not public-facing)
- Native Python data processing with pandas (matches your data stack)
- Easy to deploy (Streamlit Cloud, or internal server)
- Built-in session state for agent workflow
- Low maintenance burden
- Native secrets management via `st.secrets` (`.streamlit/secrets.toml`) + env vars

**Alternative considered:** React + FastAPI — more scalable but overkill for an internal CX tool with <20 agents.

### Data Pipeline (Live from Day 1)
```
Redshift (transactions, audiences, contractors)
        ↓
   pandas in-memory (with st.cache_data TTL for performance)
        ↓
   Eligibility Engine
        ↓
   Streamlit UI ←→ Supabase (risk matrix reads, lead writes)
```

### Secrets & Configuration
```
.streamlit/secrets.toml (local dev, gitignored)
├── [redshift]
│   ├── host, port, dbname, user, password
├── [supabase]
│   ├── url, key (service role key)
```
In production: set as environment variables — Streamlit reads `st.secrets` from env vars automatically on Streamlit Cloud, or use `python-dotenv` + `os.environ` for self-hosted.

---

## Phase 1: Live Data Connections & Eligibility Engine
**Duration**: 3–4 days | **Priority**: Critical

### Tasks

#### 1.1 — Project Setup ✅ DONE
- [x] uv virtual environment created, dependencies installed (`requirements.txt`)
- [x] `.env` configured with Redshift + Supabase credentials
- [x] Redshift connection tested via `psycopg2-binary` — working
- [x] Supabase connection tested via `supabase` SDK (REST API) — working
- [x] `test_connections.py` validates both connections

#### 1.2 — Redshift Data Layer ✅ DONE (queries ready)
- [x] All Redshift SQL queries provided in `queries.sql`:
  - Quick transactions (wallet_transaction + joins, message LIKE 'Quick%')
  - Future Fund transactions (wallet_transaction + joins, message LIKE 'future%')
  - Tapi transactions (wallet_transaction, des_transaction_type = 'UTILITIES_PAYMENT')
  - Tapi segment (contractor + contract, countries COL/MEX/ARG/PER/CHL, active)
  - E-Sim transactions (wallet_transaction + joins, specific E-sim messages)
  - Reserve audience (plan_subscription, is_enabled=true, cod_plan='RESERVE')
  - Contractor table DDL (full schema with 60+ columns)
- [ ] Implement `data/redshift.py` with cached query functions
- [ ] Validate query results against Excel row counts

#### 1.3 — Supabase Data Layer ✅ DONE (tables ready)
- [x] `quick_audience` table uploaded to Supabase (~7,733 rows, PK: CR_Code)
- [x] `ff_audience` table uploaded to Supabase (~18,996 rows, PK: CR_Code)
- [x] `risk_matrix` table exists (des_email, decision: 'Approved' / 'Not approved')
- [x] Schema documented in `supabase-schema.sql`
- [ ] Implement `data/supabase_client.py` with audience + risk matrix fetch functions

#### 1.4 — Eligibility Engine
- [ ] Build per-product eligibility functions:
  - `get_quick_eligible() → set[cr_code]` (audience − transactions − risk rejected)
  - `get_future_fund_eligible() → set[cr_code]` (audience − transactions)
  - `get_tapi_eligible() → set[cr_code]` (segment − transactions)
  - `get_esim_eligible() → set[cr_code]` (all active contractors − transactions)
  - `get_reserve_eligible() → set[cr_code]` (reserve audience, pre-filtered)
- [ ] Build unified lookup: `get_user_eligibility(cr_code) → dict[product: EligibilityStatus]`
  - Status: `ELIGIBLE` | `ALREADY_USING` | `NOT_ELIGIBLE` (with reason)
- [ ] Build user profile enrichment: `get_user_profile(cr_code) → UserProfile`
  - Pull name, email, company, country from `contractor` table

#### 1.5 — Data Validation
- [ ] Count eligible users per product after all exclusions (sanity check vs Excel counts)
- [ ] Flag duplicate CR codes within audience queries
- [ ] Log data quality report

### Exit Criteria
- [ ] Live Redshift + Supabase connections working
- [ ] `get_user_eligibility("CR034116")` returns correct product eligibility dict
- [ ] Query results match Excel snapshot counts (within tolerance)
- [ ] Risk matrix correctly excludes users from Quick
- [ ] All 5 products have working eligibility functions

---

## Phase 2: Agent-Facing UI
**Duration**: 3–4 days | **Priority**: Critical

### Tasks

#### 2.1 — User Lookup Interface
- [ ] Search bar: agent enters CR Code, email, or name
- [ ] Fuzzy matching on name/email for partial searches
- [ ] Display user profile card:
  - Name, email, company, country
  - CR Code, External ID
  - Account status

#### 2.2 — Eligibility Dashboard
- [ ] Product eligibility cards (one per product)
  - Green = Eligible (can offer)
  - Gray = Already using (no action)
  - Red = Not eligible (risk/exclusion)
- [ ] For each eligible product, show:
  - Product name and one-line description
  - Key selling points / talk track
  - "Mark as Lead" button

#### 2.3 — Lead Capture Flow
- [ ] "Mark as Lead" action:
  - Captures: cr_code, product, agent_id, timestamp, notes (optional)
  - Confirmation dialog before submission
- [ ] Lead stored directly in Supabase (`cx_leads` table)
- [ ] Prevent duplicate leads (same user + same product within X days)

#### 2.4 — Agent Session
- [ ] Agent login (simple — name/ID selection or SSO later)
- [ ] Session tracking: which users the agent looked up
- [ ] Quick stats: leads generated today, this week

### Exit Criteria
- [ ] Agent can search user by CR code and see eligibility in < 2 seconds
- [ ] Agent can mark a lead and see it saved
- [ ] Duplicate lead prevention works

---

## Phase 3: Lead Management & Commission Tracking
**Duration**: 2–3 days | **Priority**: High

### Tasks

#### 3.1 — Lead Pipeline View
- [ ] Table of all leads with filters:
  - By product, by agent, by date range, by status
- [ ] Lead statuses: `Qualified → Contacted → Converted → Rejected`
- [ ] Bulk status update capability

#### 3.2 — Conversion Tracking
- [ ] Match leads against new transactions (did the user start using the product?)
- [ ] Auto-update lead status when a new transaction appears for that user+product
- [ ] Conversion attribution: link conversion to the agent who generated the lead

#### 3.3 — Commission Dashboard
- [ ] Per-agent view:
  - Total leads generated
  - Conversion rate
  - Pending commissions
- [ ] Admin view:
  - All agents' performance
  - Product-level conversion rates
  - Commission payout summary

### Exit Criteria
- [ ] Leads flow from Qualified → Converted automatically when transactions appear
- [ ] Commission report is exportable (CSV)
- [ ] Agent can see their own performance

---

## Phase 4: Deployment & Polish
**Duration**: 2–3 days | **Priority**: Medium

### Tasks

#### 4.1 — Deployment
- [ ] Deploy on Streamlit Cloud (or internal Docker host)
- [ ] Configure production secrets (env vars for Redshift + Supabase)
- [ ] Access control: only CX team can access (Streamlit auth or password)
- [ ] Monitoring: error logging, usage analytics

#### 4.2 — Performance Tuning
- [ ] Optimize Redshift queries (indexes, query plans)
- [ ] Tune cache TTL per data type (audiences = longer, transactions = shorter)
- [ ] Add data staleness indicator ("Data last refreshed: X minutes ago")
- [ ] Connection pooling for concurrent agent sessions

#### 4.3 — Talk Tracks & Product Content
- [ ] Add configurable talk tracks per product (markdown content)
- [ ] FAQ section per product for agent reference
- [ ] Objection handling suggestions

#### 4.4 — Operational Readiness
- [ ] Agent onboarding guide / training doc
- [ ] Error handling: graceful degradation if Redshift is slow/down
- [ ] Data quality alerts (if eligible counts drop below expected thresholds)

### Exit Criteria
- [ ] Deployed and accessible to CX team
- [ ] Handles concurrent agent sessions without degradation
- [ ] Agents trained and using the tool

---

## Open Questions (Need Answers Before Building)

| # | Question | Status | Impacts |
|---|---|---|---|
| 1 | ~~**E-Sim audience**~~ | **RESOLVED** — All active contractors from Redshift `contractor` table | Phase 1 |
| 2 | ~~**Reserve enrollment**~~ | **RESOLVED** — Reserve audience query is pre-filtered (eligible + not enrolled) | Phase 1 |
| 3 | ~~**Risk Matrix schema**~~ | **RESOLVED** — `risk_matrix` table: `des_email` + `decision` ('Approved' / 'Not approved') | Phase 1 |
| 4 | ~~**Supabase credentials**~~ | **RESOLVED** — env vars in `.env`, connection tested | Phase 1 |
| 5 | ~~**Redshift credentials**~~ | **RESOLVED** — env vars in `.env`, connection tested | Phase 1 |
| 6 | ~~**Redshift SQL queries**~~ | **RESOLVED** — all queries provided in `queries.sql` | Phase 1 |
| 7 | **Commission structure**: Flat fee per lead? Percentage of transaction? Per product? | OPEN | Phase 3 |
| 8 | **Agent list**: How many agents? Do they have existing IDs/logins? | OPEN | Phase 2 |
| 9 | **Duplicate lead window**: How many days before the same user+product can be re-submitted as a lead? | OPEN | Phase 2 |

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **UI** | Streamlit | Fast internal tool development, Python-native |
| **Data Processing** | pandas + numpy | Vectorized operations on eligibility data |
| **Transaction & User Data** | Amazon Redshift (live queries) | Source of truth for contractors, transactions, audiences |
| **Risk Matrix + Leads DB** | Supabase (PostgreSQL) | Already in use; unifies risk reads + lead writes |
| **Caching** | `st.cache_data` with TTL | In-memory cache, auto-refreshes on configurable interval |
| **Secrets** | `.streamlit/secrets.toml` + env vars | Native Streamlit support, works locally and in cloud |
| **Deployment** | Streamlit Cloud or Docker | Simple deployment for internal tool |

---

## File Structure (Proposed)

```
cx-sales-agent/
├── app.py                      # Streamlit main app (multipage entry)
├── requirements.txt            # Dependencies (streamlit, supabase, psycopg2-binary, pandas, python-dotenv)
├── .env                        # Secrets (gitignored)
├── .gitignore
├── queries.sql                 # Reference: all Redshift queries (documentation)
├── supabase-schema.sql         # Reference: Supabase schema (documentation)
├── test_connections.py         # Connection validation script
├── data/
│   ├── redshift.py             # Redshift connection + cached query functions
│   └── supabase_client.py      # Supabase connection (audiences, risk matrix, leads)
├── eligibility/
│   ├── engine.py               # Core eligibility logic + unified lookup
│   └── products.py             # Product definitions and metadata
├── leads/
│   ├── models.py               # Lead data models
│   ├── storage.py              # Lead CRUD via Supabase
│   └── commission.py           # Commission calculation
├── pages/                      # Streamlit multipage app
│   ├── 1_🔍_User_Lookup.py    # Agent lookup + eligibility view
│   ├── 2_📋_My_Leads.py       # Agent's lead history
│   ├── 3_📊_Dashboard.py      # Performance dashboard
│   └── 4_⚙️_Admin.py          # Admin / commission view
├── talk_tracks/
│   ├── quick.md
│   ├── future_fund.md
│   ├── tapi.md
│   ├── esim.md
│   └── reserve.md
└── tests/
    ├── test_eligibility.py
    └── test_data_connections.py
```

---

## Workflow Dependency Graph

```
Phase 1: Live Data + Engine    Phase 2: UI               Phase 3: Leads          Phase 4: Deploy
──────────────────────────    ──────────                 ───────────             ────────────────
                                                       
[1.1 Project Setup]      ──→ [2.1 User Lookup] ──→ [3.1 Lead Pipeline]──→ [4.1 Deployment]
        │                          │                      │                       │
[1.2 Redshift Layer]     ──→ [2.2 Eligibility UI]   [3.2 Conversion] ──→ [4.2 Performance]
        │                          │                      │                       │
[1.3 Risk Matrix]        ──→ [2.3 Lead Capture]    [3.3 Commission]  ──→ [4.3 Talk Tracks]
        │                          │                                              │
[1.4 Eligibility Engine] ──→ [2.4 Agent Session]                          [4.4 Ops Readiness]
        │                       
[1.5 Data Validation]
```

---

## Next Steps

All Phase 1 blockers are resolved. Ready to build:

1. **NOW** → Implement `data/redshift.py` and `data/supabase_client.py` (data layer)
2. **NOW** → Implement `eligibility/engine.py` (eligibility logic)
3. **NOW** → Validate eligibility counts against Excel snapshots
4. **THEN** → Phase 2: Build the Streamlit UI (user lookup, eligibility cards, lead capture)
