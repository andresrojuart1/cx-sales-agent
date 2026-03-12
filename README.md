# CX Sales Agent

Internal Streamlit app for CX agents to:

- look up contractors
- validate product eligibility
- create and manage leads
- monitor conversion and estimated MRR

## Stack

- `Streamlit`
- `Supabase`
- `Amazon Redshift`
- `Google Workspace / OIDC`

## Pages

- `User Lookup`
  Search a contractor by CR code, email, or name and review product eligibility.
- `My Leads`
  Review and update leads owned by the current agent.
- `Dashboard`
  Review team performance, conversion, product mix, and estimated MRR.

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

Create or update `.streamlit/secrets.toml` with:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "LONG_RANDOM_SECRET"
lead_admin_emails = ["mrojas@getontop.com"]

[auth.google]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[redshift]
host = "..."
port = 5439
dbname = "..."
user = "..."
password = "..."

[supabase]
url = "..."
key = "..."
```

Notes:

- `.streamlit/secrets.toml` is ignored by git.
- The local Google redirect must be authorized in Google Cloud:
  `http://localhost:8501/oauth2callback`

### 3. Run locally

```bash
python3 -m streamlit run app.py
```

## Deployment

The app is deployed from GitHub to Streamlit Community Cloud.

Typical flow:

```bash
git add .
git commit -m "Your change"
git push origin main
```

Then either wait for auto-redeploy or use `Reboot app` in Streamlit Cloud.

## Secrets Required in Streamlit Cloud

At minimum:

- `auth.redirect_uri`
- `auth.cookie_secret`
- `auth.lead_admin_emails`
- `auth.google.client_id`
- `auth.google.client_secret`
- `redshift.*`
- `supabase.url`
- `supabase.key`

## Admin Access

Lead deletion in `Dashboard` is restricted to admin emails.

Sources of truth:

- `auth.lead_admin_emails` in Streamlit secrets
- fallback allowlist in [`shared.py`](/Users/andresrojas/Python%20codes/cx-sales-agent/shared.py)

## MRR Logic

Estimated product MRR is defined in [`eligibility/products.py`](/Users/andresrojas/Python%20codes/cx-sales-agent/eligibility/products.py).

Current values:

- `Quick`: `11.9`
- `Future Fund`: `3.0`
- `Reserve`: `14.9`
- `Tapi`: `1.6`
- `e-Sim`: `5.0`

Dashboard MRR only counts `Converted` leads.

## Known Functional Note

`Reserve` business logic should be validated with stakeholders before changing it further. The current implementation has been intentionally left pending business confirmation.

## Useful Docs

- [`docs/operations.md`](/Users/andresrojas/Python%20codes/cx-sales-agent/docs/operations.md)
- [`docs/business-rules.md`](/Users/andresrojas/Python%20codes/cx-sales-agent/docs/business-rules.md)
- [`docs/google-workspace-auth-workflow.md`](/Users/andresrojas/Python%20codes/cx-sales-agent/docs/google-workspace-auth-workflow.md)
- [`docs/pii_table_migration.md`](/Users/andresrojas/Python%20codes/cx-sales-agent/docs/pii_table_migration.md)
