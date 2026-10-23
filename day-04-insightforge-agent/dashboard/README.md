# InsightForge AI V3 — UI Preview

A polished Apple-inspired **visual preview** for the existing Python/DuckDB/Gemini project.

## Run locally

Requirements: Node.js >=20.19 or >=22.12 and npm.

From the `dashboard` directory:

```bash
npm install
npm run dev
```

Open the local URL displayed in the terminal (normally http://127.0.0.1:5173).

## What works

- Responsive overview, payment analysis, account investigation, and AI intelligence pages
- Spring transitions, hover states, keyboard focus, reduced-motion accommodations
- Sort payment groups by volume or synthetic label percentage; filter groups
- Sample investigation prompt selector (pre-fills input)
- All shown dataset figures are static values from the user's verified Kaggle synthetic dataset output

## Not yet connected

- Metrics and account investigations are **static previews**, not live queries
- The assistant submit button is intentionally disabled; it does not pretend to call Gemini
- Next: create a FastAPI backend wrapping the existing `tool_registry.py`/`gemini_agent.py`, keeping `GEMINI_API_KEY` exclusively on the Python server

## Privacy

Never place the `GEMINI_API_KEY` in frontend source files or any variable prefixed `VITE_`. Frontend variables are accessible to users of the site. Keep your Python `.env` in the project root; its existing `.gitignore` should exclude it.
