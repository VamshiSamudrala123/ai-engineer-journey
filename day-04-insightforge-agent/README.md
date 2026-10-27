# InsightForge AI — Banking Intelligence Agent

An AI-powered banking intelligence application built with Python,
Google Gemini, DuckDB, FastAPI, and React.

InsightForge analyzes synthetic financial transactions, investigates
individual accounts, and lets users ask questions in natural language.

## Current version

V3.6 — Portfolio Polish

## Features

- Live banking dataset statistics from DuckDB
- Payment format and currency analysis
- Account investigation by bank ID and account number
- Gemini AI assistant with function calling
- Three approved banking tools
- Multiple tool calls and bounded error recovery
- Conversation memory for follow-up questions
- Visible tool names and execution statuses
- New Conversation button
- Improved chat error handling and retry
- Automated Python tests

## Architecture

React / Vite dashboard
        |
        v
FastAPI backend
        |
        +-- DuckDB banking analysis
        |
        +-- Gemini AI agent
                |
                +-- Tool registry
                |
                +-- Dataset overview
                +-- Payment analysis
                +-- Account investigation

Gemini API credentials remain on the Python server.

## Dataset

The project uses the synthetic IBM Anti-Money Laundering
banking dataset available through Kaggle.

Place the required CSV files in:

    data/raw/HI-Small_Trans.csv
    data/raw/HI-Small_accounts.csv

Dataset files are excluded from Git.

The transactions are synthetic. Generated laundering labels
are not proof of real-world financial wrongdoing.

## Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r day-04-insightforge-agent/requirements.txt
```

Create a private `.env` file inside `day-04-insightforge-agent`:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit real API keys or banking CSV files.

## Start the backend

From the project directory:

```bash
cd day-04-insightforge-agent
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Health endpoint:

    http://127.0.0.1:8000/api/health

## Start the dashboard

In a second terminal:

```bash
cd day-04-insightforge-agent/dashboard
npm install
npm run dev
```

Open:

    http://127.0.0.1:5173/

Use a supported Node.js version for Vite 7.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/health | Backend health |
| GET | /api/overview | Banking dataset metrics |
| GET | /api/payments | Payment group statistics |
| POST | /api/accounts/investigate | Account investigation |
| POST | /api/chat | Gemini AI conversation |

## Automated testing

From the InsightForge project directory:

```bash
python -m unittest discover -s tests -q
```

The V3.5 baseline includes 53 Python test methods.

Build the dashboard:

```bash
cd dashboard
npm run build
```

## Current limitations

- The featured account card and some explanatory text use
  verified static example values.
- Conversation history is bounded and held in browser memory;
  it is not persisted across refreshes.
- Tool activity shows approved tool names and status,
  not a full execution trace.
- Research workflows and PDF export are not implemented.
- InsightForge-specific GitHub Actions CI is planned.
- Production deployment has not been verified.

## Roadmap

- V3.7: Continuous integration
- V3.8: Analytical research and PDF reports
- V3.9: Deployment
- V4.0: Portfolio release
