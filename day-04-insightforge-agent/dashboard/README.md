# InsightForge — React Dashboard

I built this dashboard to explore the banking tools and Gemini assistant without switching between terminal commands.

I used React and Vite for the frontend and connected it to the FastAPI backend.

## What I added

- **Overview:** I displayed dataset statistics and payment charts from backend queries.
- **Payment analysis:** I compared transaction activity and synthetic label percentages across payment formats and currencies.
- **Account investigation:** I added bank and account lookups, then a PDF download based on validated investigation results.
- **Chat:** I connected natural-language questions to the Gemini agent, passed follow-up context, and displayed approved tool names and statuses.

I also added Markdown responses, loading states, error handling, retry, a New Conversation button, and responsive layouts.

## How I ran it

I used Node.js 22, matching CI. After setting up the dataset and starting FastAPI on port 8000, I ran these commands from the repository root:

```bash
cd day-04-insightforge-agent/dashboard
npm ci
npm run dev
```

I opened [the local dashboard](http://127.0.0.1:5173/). The Vite development proxy forwarded `/api` requests to `http://127.0.0.1:8000`.

I checked the production build from this directory with:

```bash
npm run build
```

For deployment preparation, I configured FastAPI to serve the generated `dist` files and API on the same origin. I had not verified a cloud deployment for V3.9.

## How I handled data and credentials

I kept Gemini credentials on the Python server and out of the frontend.

The main metrics and payment charts used backend queries with cached summaries. Account lookups queried the selected account. The featured account card remained a labeled static example.

I used synthetic banking records throughout. The laundering labels described generated dataset annotations and did not establish real-world wrongdoing.

Conversation history stayed in browser memory and was lost on refresh. The activity feed displayed tool names and statuses without exposing their arguments or raw results.

I documented the [full setup and architecture in the main project README](../README.md). The [V3.9 CI run](https://github.com/VamshiSamudrala123/ai-engineer-journey/actions/runs/40591396566) passed the Python checks and React build.
