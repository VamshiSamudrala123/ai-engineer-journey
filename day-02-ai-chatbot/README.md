# Gemini AI Chatbot V1

A Python terminal chatbot that calls Gemini and keeps conversation history during the current run.

## Setup on macOS

Use Python 3.10 or newer. Run these commands from the repository root in the VS Code terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r day-02-ai-chatbot/requirements.txt
```

Create or copy your own key from [Google AI Studio](https://aistudio.google.com/api-keys). Check your project's billing status and quota before making requests. API availability and free-tier eligibility depend on the model and project.

Enter the key privately in your current terminal; Python's hidden prompt works in both Bash and Zsh:

```bash
export GEMINI_API_KEY="$(python -c 'import getpass; print(getpass.getpass("Gemini API key: "))')"
```

Do not put the key in Python files or commit it to Git. This command keeps it out of the command text saved in shell history. Configure it again after opening a new terminal. The app reads the environment variable; it does not load a `.env` file.

## Run

```bash
python day-02-ai-chatbot/main.py
```

The default model is `gemini-3.5-flash-lite`. Google currently recommends it or `gemini-3.8-flash` for new projects; older 2.5 models have restricted access for new users. You can choose another available model:

```bash
export GEMINI_MODEL=gemini-3.8-flash
```

Type `exit` or `quit` to finish. Ctrl+C and Ctrl+D also exit cleanly. Blank input is rejected without making an API request. Authentication and model errors stop with an explanation; quota, timeout, and connection errors let you try another message. Raw exception messages are not printed because they may contain request details.

Conversation history is managed by the SDK chat and lasts only for the running program. Prompts and previous messages are sent to Google; restarting the program starts a fresh conversation. Longer conversations use more input tokens. No conversations are saved to disk.

## Understand the code

- `main()` checks configuration and creates the Gemini client with a 30-second request timeout.
- `client.chats.create()` creates one conversation, with instructions and a response token limit.
- `run_chat()` reads messages in a loop and sends them through that same chat.
- `chat.send_message()` returns Gemini's response; `response.text` holds the answer.
- `api_error_message()` turns API status codes into useful instructions.
- The `if __name__ == "__main__"` block starts the app only when this file is run directly.

## Tests

Run the offline tests and syntax check:

```bash
python -m unittest discover -s day-02-ai-chatbot -p 'test_*.py' -v
python -m py_compile day-02-ai-chatbot/main.py
```

The tests use simulated SDK/API responses; they do not use a real key or spend quota. They check configuration, blank input, conversation reuse, exit commands, empty responses, API failures, timeouts, and connection failures. A passing test suite does not confirm that your account can access Gemini.

With your real key configured, test this conversation:

1. `My favorite programming language is Python.`
2. `What is my favorite programming language?` — verify it recalls Python.
3. Enter an empty message — verify it asks for a message.
4. Type `exit` — verify it exits.
5. Restart and ask about your favorite language — verify there is no saved memory.

If an error appears, use its status code and instructions. Never share the API key. After finishing, remove it from the terminal environment:

```bash
unset GEMINI_API_KEY
```

## References

- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models)
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)
- [Gemini API setup](https://ai.google.dev/gemini-api/docs/get-started)
