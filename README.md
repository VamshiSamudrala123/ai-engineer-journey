# My Engineering Journey

I created this repository to keep track of the projects I built while learning Python, APIs, Gemini, and application development.

I started with small terminal programs. With each project, I added another piece: a browser interface, tool calling, tests, and eventually a separate frontend and backend.

## The projects I built

| Project | What I worked on |
| --- | --- |
| [Day 01 — Python API Explorer](day-01-python-api/) | I retrieved user data from an API, added search, handled errors, and exported results to CSV. |
| [Day 02 — Gemini Chatbot](day-02-ai-chatbot/) | I built a terminal chatbot and a Streamlit interface with conversation memory. |
| [Day 03 — Study Planner Agent](day-03-ai-agent/) | I connected Gemini to calculation and task tools, then added confirmation before task updates. |
| [Day 04 — InsightForge](day-04-insightforge-agent/) | I brought banking analytics, controlled tool calling, FastAPI, React, and PDF reporting together in one application. |

## My main project: InsightForge

I spent the most time on [InsightForge](day-04-insightforge-agent/), a banking intelligence application built around synthetic transaction data.

I used DuckDB to query the records, gave Gemini three approved tools, and built a dashboard for exploring payment activity and individual accounts. I later added follow-up conversation context, visible tool activity, account PDF downloads, and automated checks.

The [project README](day-04-insightforge-agent/README.md) covered the architecture, local setup, testing, and limitations. The [V3.9 CI run](https://github.com/VamshiSamudrala123/ai-engineer-journey/actions/runs/40591396566) passed the Python tests and React production build.

## What I learned along the way

Working through these projects helped me understand how a model, Python functions, data, and a user interface fitted together. I also got more comfortable debugging, writing tests, and reviewing changes through branches and pull requests.

The biggest change in my approach was paying closer attention to what happened after the first successful response: invalid inputs, failed requests, follow-up questions, and whether someone else could run the project.
