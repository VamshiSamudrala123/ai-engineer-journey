
## V3 — Web-Based AI Assistant

The V3 chatbot uses Streamlit and Google Gemini.

### Features
- Browser-based AI chat interface
- Conversation memory during the current session
- Previous messages displayed as chat bubbles
- New Chat button to reset the conversation
- Secure Gemini API key configuration

### Run the web application

Install dependencies:

```bash
python -m pip install -r day-02-ai-chatbot/requirements.txt
```

Set GEMINI_API_KEY securely in your terminal using the
instructions earlier in this README.

Start the web app:

```bash
python -m streamlit run day-02-ai-chatbot/web_app.py
```

Open http://localhost:8501 in your browser.

Conversations are stored in Streamlit session state
and are not saved permanently by the application.