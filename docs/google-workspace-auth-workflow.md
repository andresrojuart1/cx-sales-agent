# Google Workspace Auth Implementation Workflow

> Project: CX Sales Agent (Streamlit)  
> Scope: Require Google sign-in and allow access only for `@getonop.com` accounts.  
> Authorization policy: Any authenticated `@getonop.com` user can access all currently visible app data.  
> Delivery style: Local-first validation, then deployment hardening.

---

## 1) Objective

Replace the current manual name-based access with real authentication using Streamlit OIDC (`st.login`, `st.user`, `st.logout`), and enforce a single authorization rule:

- Allow access if `st.user.email` ends with `@getonop.com`
- Deny access to all other emails

No role-based segmentation is included in this phase.

---

## 2) Non-Goals (for this phase)

- No granular RBAC (agent/admin/manager)
- No per-record access filtering
- No masking changes beyond current UI behavior
- No mandatory Streamlit Cloud deployment during implementation

---

## 3) Dependencies and Prerequisites

### 3.1 Google Cloud / Workspace setup

- Create or reuse OAuth client in Google Cloud Console
- Configure consent screen (internal or external, based on Workspace policy)
- Add authorized redirect URIs:
  - Local: `http://localhost:8501/oauth2callback`
  - Production (later): `https://<your-streamlit-domain>/oauth2callback`

### 3.2 Python dependencies

Update `requirements.txt` to include the `authlib` library required by Streamlit's native OIDC:

```
streamlit
authlib>=1.3.2
supabase
psycopg2-binary
pandas
python-dotenv
```

Alternatively, use `streamlit[auth]` instead of separate `streamlit` + `authlib` entries.

### 3.3 Streamlit auth configuration

Set auth secrets in `.streamlit/secrets.toml` (local) and secure deployment secrets (later):

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "LONG_RANDOM_SECRET"   # Must be cryptographically random, >= 32 chars

[auth.google]
client_id = "GOOGLE_CLIENT_ID"
client_secret = "GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Generate `cookie_secret` with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3.4 App config

- Domain allowlist value: `getonop.com` (or environment variable override)

### 3.5 Supabase schema update

Add an `agent_email` column to the `cx_leads` table before deploying auth changes:

```sql
ALTER TABLE cx_leads ADD COLUMN agent_email TEXT;
```

This column will become the primary key for lead ownership (more reliable than `agent_name`, which is a display name and may not be unique).

---

## 4) Implementation Plan

### Phase A — Authentication guard and shared policy

1. Create a shared guard function in `shared.py`:
   - If not logged in, show "Sign in with Google" and call `st.login("google")`
   - If logged in but email is not `@getonop.com`, block page and offer sign-out
   - If authorized, set identity fields in session state:
     - `agent_name` from `st.user.name` (fallback to email prefix)
     - `agent_email` from `st.user.email`
   - If `st.user.email` is `None` or empty, fail closed: show error, offer sign-out

2. **Execution order constraint**: The guard must not call `st.login()` or render any widget before `st.set_page_config()` on pages that use it. Two options:
   - (a) Move `st.set_page_config()` into `render_sidebar()` itself (only `app.py` calls it today), or
   - (b) Ensure every page calls `st.set_page_config()` before `render_sidebar()`
   
   Option (b) is safer — it matches the current pattern.

3. Update sidebar behavior:
   - Show authenticated identity (name + email)
   - Add sign-out button (`st.logout()`)
   - Remove the "Your Name" text input entirely
   - Keep cache refresh control

4. Apply this guard from all pages through `render_sidebar()` so each page enforces auth consistently.

5. **Cookie expiry**: Configure session duration to ~8 hours (0.33 days) instead of the Streamlit default of 30 days. This limits the exposure window for an app handling PII and financial data. *(Note: Streamlit's native OIDC uses a fixed 30-day cookie. If shorter sessions are required, this must be enforced via application-level checks — e.g., storing login timestamp in session state and comparing on each page load.)*

Exit criteria:
- Unauthenticated users cannot access app content.
- Non-`@getonop.com` users are denied.
- Guard handles missing email claim gracefully (fail closed).
- Authorized users can proceed normally.

---

### Phase B — Migrate lead ownership to email-based identity

This phase must run **before** removing legacy name input, so both old and new leads remain accessible during the transition.

1. Update `save_lead()` in `data/supabase_client.py`:
   - Accept and persist `agent_email` alongside `agent_name`
   - `agent_email` becomes the authoritative ownership field
   - `agent_name` is kept for display purposes only

2. Update `get_leads()` in `data/supabase_client.py`:
   - Filter by `agent_email` instead of `agent_name` when fetching "My Leads"
   - Fall back to `agent_name` match for legacy leads that have no `agent_email`

3. Backfill existing leads (one-time manual step):
   - Map known agents' free-text names to their `@getonop.com` emails
   - Run an UPDATE query on the `cx_leads` table to populate `agent_email` for historical records:
     ```sql
     UPDATE cx_leads SET agent_email = 'jane.doe@getonop.com' WHERE agent_name = 'Jane Doe';
     -- Repeat for each known agent
     ```

4. Update the Dashboard page (`pages/3_Dashboard.py`):
   - "Leads by Agent" grouping should use `agent_name` for display but be aware that old rows may have different name formats
   - Consider coalescing: display `agent_name` where available, fall back to email prefix

Exit criteria:
- New leads are saved with both `agent_name` and `agent_email`.
- "My Leads" page filters by authenticated email and shows both old and new leads.
- Dashboard displays agent stats without fragmentation from the name format change.

---

### Phase C — Remove legacy pseudo-auth assumptions

1. Remove "enter your name" gating from pages:
   - `app.py` — remove the `if not st.session_state.get("agent_name")` check and prompt
   - `pages/1_User_Lookup.py` — remove the `agent_name` warning/stop block
   - `pages/2_My_Leads.py` — remove the `agent_name` warning/stop block
   - `pages/3_Dashboard.py` — note: this page **never had name gating**; it currently loads for any visitor. After this phase it is protected solely by the auth guard in `render_sidebar()`.

2. Update `pages/1_User_Lookup.py` lead submission:
   - Pass `agent_email` from session state to `save_lead()` alongside `agent_name`

3. Update `pages/2_My_Leads.py`:
   - Source `agent_name` and `agent_email` from session state (set by auth guard)
   - Pass `agent_email` to `get_leads()` for filtering

Exit criteria:
- No page depends on manual identity entry.
- All identity display and writes are sourced from authenticated user info.
- Every page is protected by the centralized auth guard.

---

### Phase D — Local validation (required before deployment)

#### Functional checks

1. Unauthenticated visit:
   - Expected: prompt to sign in, no data access
2. Valid Workspace account (`@getonop.com`):
   - Expected: app loads, all existing data/features accessible
3. Non-Workspace or different domain account:
   - Expected: blocked with access denied message
4. Sign-out:
   - Expected: session cleared, user returned to login gate
5. Multipage behavior:
   - Expected: all pages enforce same auth rule
6. Lead ownership continuity:
   - Expected: agent can see both old (backfilled) and new leads on "My Leads"
7. Dashboard integrity:
   - Expected: "Leads by Agent" chart shows agents without duplicate entries

#### Regression checks

1. User lookup still works (search, profile card, eligibility)
2. Lead submission still works (saves with `agent_email`)
3. Dashboard and leads pages still load with correct data
4. Lead status updates still work

Exit criteria:
- All functional and regression checks pass locally.

---

### Phase E — Deployment readiness (after local pass)

1. Add production redirect URI in Google OAuth client
2. Set production secrets securely (Streamlit Cloud secrets manager or platform env vars)
3. Verify login/logout/domain policy in production
4. Confirm no auth secrets are committed to git (`.streamlit/secrets.toml` in `.gitignore`)
5. Verify HTTPS is enforced (Streamlit Cloud handles this; other platforms may need explicit SSL config)

Exit criteria:
- Production auth flow mirrors local behavior.
- Only `@getonop.com` users can access.
- All secrets are managed outside source control.

---

## 5) Quality Gates

- Gate 1: Auth required globally (no page is accessible without login)
- Gate 2: Domain policy enforced from `@getonop.com` email suffix check
- Gate 3: Legacy manual name input removed from all pages
- Gate 4: No secrets in source control (`.gitignore` verified)
- Gate 5: Lead ownership uses `agent_email` — no data loss from migration
- Gate 6: Local test checklist completed (functional + regression)
- Gate 7: `requirements.txt` includes `authlib>=1.3.2`

---

## 6) Rollback Plan

If auth integration blocks intended users:

1. Revert auth-related app changes (guard function, sidebar)
2. Restore previous manual flow temporarily
3. Fix OAuth redirect/secrets/domain checks
4. Re-run local checklist before re-applying

Note: The `agent_email` column addition and lead backfill are non-destructive — they do not need to be rolled back. The `agent_name` column remains intact throughout.

---

## 7) Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OAuth redirect mismatch | Login fails entirely | Keep local and prod callback URLs explicitly registered in Google Cloud Console. |
| Missing email claim from provider | Users blocked unexpectedly | Validate `st.user.email` exists; fail closed with clear error message if missing. |
| Partial page protection | Data exposed on unguarded page | Centralize guard in `render_sidebar()`, which every page already calls. |
| Lead attribution breakage | Agents lose access to old leads | Backfill `agent_email` on existing leads before removing legacy name input (Phase B). |
| `st.set_page_config` ordering | Runtime error on page load | Ensure every page calls `st.set_page_config()` before `render_sidebar()`. |
| Shared `st.cache_data` across users | Agent A sees data cached by Agent B | Accepted risk — all authenticated agents have the same data access level. No per-user cache isolation needed for this phase. |
| Cookie duration too long (30 days default) | Extended exposure window if device is compromised | If shorter sessions are needed, implement app-level login timestamp check. Document as accepted risk for Phase 1. |

---

## 8) Decision Record

- Chosen auth mechanism: Streamlit native OIDC with Google provider (`st.login`/`st.logout`/`st.user`)
- Chosen authorization model: Domain-based allowlist (`@getonop.com`)
- Chosen identity key for lead ownership: `agent_email` (unique, stable) over `agent_name` (display-only)
- Environment strategy: Local-first validation before Streamlit Cloud deployment
- Accepted risk: `st.cache_data` is global across users (same access level, no isolation needed)
- Accepted risk: 30-day cookie duration (Streamlit default) — shorter sessions deferred to future phase

