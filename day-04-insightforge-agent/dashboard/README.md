# InsightForge AI — React Dashboard

The frontend for InsightForge AI, built with React and Vite.

## Dashboard sections

1. Overview — live banking statistics and payment chart
2. Payment analysis — live payment-format and currency data
3. Account investigation — live DuckDB account lookups
4. AI intelligence — Gemini chat with banking tools

## AI assistant features

- Natural-language questions
- Follow-up conversation context
- Markdown-formatted responses
- Approved tool activity labels
- New Conversation button
- Error messages and question retry

## Run locally

Start the FastAPI backend first.

From this directory:

```bash
npm install
npm run dev
```

Visit http://127.0.0.1:5173/

Vite proxies `/api` requests to FastAPI on port 8000.

## Verify the build

```bash
npm run build
```

## Data and security

- Synthetic banking data only
- Gemini credentials stay on the backend
- No API keys in React environment variables
- Some featured content remains static example data

See the parent README for full setup, dataset requirements,
API endpoints, automated tests, and current limitations.
