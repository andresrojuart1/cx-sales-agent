# Operations Runbook

## Run Locally

```bash
cd "/Users/andresrojas/Python codes/cx-sales-agent"
python3 -m streamlit run app.py
```

## Update and Deploy

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

If Streamlit Cloud does not refresh automatically:

1. Open the app in Streamlit Cloud
2. Click `Manage app`
3. Use `Reboot app`

## Update Secrets in Streamlit Cloud

Open:

1. App settings
2. `Secrets`
3. Paste the current TOML content
4. Save

Important:

- local `.streamlit/secrets.toml` does not deploy through git
- any change to admin emails must also be updated in Streamlit Cloud secrets

## Clear Cache

From the sidebar:

- click `Refresh Data`

This clears `st.cache_data` and reloads live data on the next query.

## Troubleshooting

### Google login fails

Check:

- correct `redirect_uri` in secrets
- same redirect authorized in Google Cloud
- correct Workspace domain

### Supabase issues

Check:

- `supabase.url`
- `supabase.key`
- table access still valid

### Redshift issues

Check:

- host, db, user, password
- user still has `SELECT` on required tables

### App deploy works locally but not in Streamlit Cloud

Check:

- latest commit is pushed to `main`
- Streamlit Cloud is connected to the right repo/branch
- deploy secrets are updated
- use `Reboot app`

## Admin-Only Lead Deletion

Lead deletion is only available in `Dashboard` for configured admin emails.

Admin resolution comes from:

1. `auth.lead_admin_emails` in secrets
2. fallback allowlist in [`shared.py`](/Users/andresrojas/Python%20codes/cx-sales-agent/shared.py)

## Current Production-Like URL

Example fork deployment:

- `https://cx-sales-agent-v2.streamlit.app`
