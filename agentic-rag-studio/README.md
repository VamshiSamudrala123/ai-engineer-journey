# Papertrail — Agentic RAG for PDFs

An end-to-end PDF research app inspired by [Aman Kharwal's walkthrough](https://amanxai.com/2026/07/08/build-an-end-to-end-agentic-rag-system/). I wanted to make the document search process inspectable instead of trusting a model's answer at face value.

## Features

- Upload multiple **text-based PDFs** (up to 8, 12 MB each).
- Page-aware text extraction, overlapping chunks, MiniLM embeddings and ChromaDB vector search.
- CrewAI agent can invoke document search tools repeatedly before answering.
- Answers have citation markers; expand actual filename/page/excerpt evidence below.
- Conversation history stays in the browser session and can be exported as JSON.
- Retrieval evaluation: label queries and compute Hit@k and MRR@k, with results export.
- Choose OpenAI, local Ollama, or a search-only mode that needs no LLM key.

## Run it locally

Python 3.11 or 3.12 recommended.

1. Clone https://github.com/VamshiSamudrala123/ai-engineer-journey
2. Change directory into agentic-rag-studio.
3. Create and activate a Python virtual environment.
4. Install with: python -m pip install -r requirements.txt
5. Start: streamlit run app.py
6. Upload PDFs and select an answer provider in the sidebar.

For OpenAI: paste a valid API key into the sidebar or put it in a local .streamlit/secrets.toml (use the example file as a template). Do NOT commit keys. API usage may cost money.

For Ollama: install Ollama, pull the llama3.2 model with 'ollama pull llama3.2', and ensure the Ollama server is running on localhost:11434. Ollama works for local installations, not a remote Community Cloud app.

The first run downloads the sentence embedding model. Local CPU works for a few PDFs but can be slow.

## Evaluate search

Use the Retrieval evaluation tab, with one JSON object per line, such as:

    {"question":"What was revenue?","expected_source":"annual.pdf","expected_text":"revenue"}
    {"question":"Which risks are mentioned?","expected_source":"annual.pdf"}

At least one expected label is required. A hit means a single returned passage matches every provided label. Hit@k = fraction of questions with a hit in the first k results. MRR@k = mean reciprocal rank of the first relevant result. These are **retrieval** metrics, not answer quality scores; human-labeled examples matter.

Run tests: python -m pytest tests -q (install pytest).

## Deploy on Streamlit Community Cloud

1. Open https://share.streamlit.io and create a new GitHub-backed app.
2. Select repository VamshiSamudrala123/ai-engineer-journey, branch main, entrypoint agentic-rag-studio/app.py.
3. Set Python 3.11 or 3.12 if the deploy interface allows it.
4. In the app's Secrets settings, enter OPENAI_API_KEY = "your-key", or type your key into the app sidebar. Never push it to GitHub.
5. Deploy and test with a text-based PDF. The free instance may have limited RAM for embedding models.

## Design notes and limitations

Text extraction preserves the page number. Semantic search uses sentence-transformers/all-MiniLM-L6-v2 and an in-memory ChromaDB collection. CrewAI builds a tool-using retrieval agent; only actually retrieved evidence is shown in the UI. The LLM may still misinterpret documents or produce inaccurate citation claims, so verify source excerpts. PDFs are untrusted content. Scanned PDFs need OCR. Document collections and chats are session-only, not production persistence. A production release also needs authentication, upload security, quotas, and systematic groundedness evaluation.

Project files: app.py (UI), agentic_rag.py (core), tests/test_core.py (tests), requirements.txt (dependencies), .streamlit (configuration).
