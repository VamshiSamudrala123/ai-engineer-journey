# Deploy InsightForge as a free Render portfolio demo

This configuration is for a small, private **fictional-data demo**, not a production banking service. It does not publish the full IBM/Kaggle dataset. The generated figures are made up, and should not be quoted as the original dataset's statistics.

## Preferred: existing Render dashboard

1. Choose **New > Web Service**, and connect `VamshiSamudrala123/ai-engineer-journey`.
2. Select `main` **after merging the accompanying PR**, or select the `deploy/insightforge-free-render-demo` branch to test it first.
3. Runtime: **Docker**. Root directory: `day-04-insightforge-agent`. Dockerfile path: `./Dockerfile`. Build context: `.`.
4. Instance type: **Free ($0/month)**. Do not provision a persistent disk, background worker, or paid database.
5. Health check: `/api/health`.
6. Configure environment variables on Render; never commit secret values to Git:

| Environment variable | Value |
|---|---|
| `INSIGHTFORGE_ENV` | `production` |
| `INSIGHTFORGE_DEMO_DATA` | `true` |
| `INSIGHTFORGE_ACCESS_USERNAME` | choose a demo username |
| `INSIGHTFORGE_ACCESS_PASSWORD` | unique, at least 16 characters |
| `INSIGHTFORGE_ENABLE_CHAT` | `false` to start, change to `true` only when ready |
| `GEMINI_API_KEY` | optional at first; required if chat enabled |

7. Deploy and open `https://YOUR-SERVICE.onrender.com/api/health`. It should return a service health JSON. Health alone does *not* verify the analytics.
8. Open the root URL and enter the username/password. Check the overview, payments, and account lookup (bank ID `3208`, account `8000F4580`). If Gemini chat is desired, configure its key and opt in by setting `INSIGHTFORGE_ENABLE_CHAT=true`.

The repository also includes a root `render.yaml` Blueprint declaring a **free** Docker web service. A Blueprint can create a new service, so review the preview and pricing before applying it. The simpler manual setup above is preferable if you already have a Render service.

## How the demo data works

The Docker startup command calls `generate_demo_data.py` only when `INSIGHTFORGE_DEMO_DATA=true`. The script creates 1,500 fictional transactions and 121 fictional account rows, small enough for basic demonstration. It preserves already existing data rather than overwriting it. `INSIGHTFORGE_DATA_DIR` can still point to a separately provided absolute dataset directory. The large CSV files remain excluded from Docker builds.

The existing frontend includes some static preview elements built around original dataset figures; only data backed by the live `/api` responses represents this small demo dataset. Avoid showing static figures as if they were generated from the demo CSVs.

## Limits

The free instance has tight memory limits, sleeps after inactivity, and does not offer persistent storage. Data files created at startup disappear on restarts but are regenerated identically each time. Full-size dataset processing may exceed free-instance RAM. Even with free hosting, Gemini API usage is governed by Google's own pricing and quotas.

If Render asks for a payment method, first check whether the **Free** instance is selected and whether any paid resource was added. Some account or payment verification requirements cannot be bypassed by repository changes; contact Render support or use another provider if Free is not available for the account.

## Local check

From `day-04-insightforge-agent`:

```bash
INSIGHTFORGE_DEMO_DATA=true python generate_demo_data.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

For the real dataset or actual deployment, leave `INSIGHTFORGE_DEMO_DATA` unset or `false` and configure your data source separately.
