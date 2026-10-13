"""A terminal chatbot with Gemini conversation memory for the current run."""

import os
import sys


DEFAULT_MODEL = "gemini-3.5-flash-lite"


def api_error_message(code):
    """Explain API failures without printing the request or secret credentials."""
    if code in (401, 403):
        return "Check your Gemini API key and project permissions."
    if code == 404:
        return "Model unavailable. Set GEMINI_MODEL to a model your project can use."
    if code == 429:
        return "Gemini quota or rate limit reached. Check AI Studio usage before retrying."
    if code == 400:
        return "Gemini rejected the request. Check your API key and model configuration."
    return "Gemini could not complete the request. Please try again later."


def run_chat(chat, client, model, config):
    """Keep using the same SDK chat so earlier messages remain in context."""
    import httpx
    from google.genai import errors

    print("🤖 General AI Assistant V2")
    print("Commands: /help, /clear, /exit")
    print("Ask me anything!\n")

    while True:
        try:
            
            message = input("You: ").strip()
            command = message.lower()

            # Exit the chatbot
            if command in {"exit", "quit", "/exit", "/quit"}:
                print("Goodbye!")
                return 0

            # Display available commands
            if command == "/help":
                print("\nAvailable commands:")
                print("/help  - Show available commands")
                print("/clear - Reset conversation memory")
                print("/exit  - Exit the chatbot\n")
                continue

            # Clear conversation history
            if command == "/clear":
                chat = client.chats.create(
                    model=model,
                    config=config,
                )
                print("Conversation memory cleared!\n")
                continue

            # Handle empty messages
            if not message:
                print("Please enter a message.\n")
                continue

            response = chat.send_message(message)
            if response.text and response.text.strip():
                print(f"\nAI: {response.text.strip()}\n")
            else:
                print("Gemini returned no text. Try rephrasing your question.\n")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0
        except errors.APIError as error:
            print(f"API error ({error.code}): {api_error_message(error.code)}\n")
            if error.code in (400, 401, 403, 404):
                return 1
        except httpx.TimeoutException:
            print("The request timed out. Please try again.\n")
        except httpx.TransportError:
            print("Connection failed. Check your internet connection and try again.\n")


def main():
    """Validate configuration, create one client, and close it when finished."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Missing GEMINI_API_KEY. Configure it in your terminal before running.")
        print("See day-02-ai-chatbot/README.md for setup instructions.")
        return 1

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Install dependencies: python -m pip install -r day-02-ai-chatbot/requirements.txt")
        return 1

    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    try:
        # The SDK timeout is in milliseconds. Explicit settings select AI Studio
        # even if this terminal also has Vertex AI environment variables.
        with genai.Client(
            api_key=api_key,
            vertexai=False,
            http_options=types.HttpOptions(timeout=30_000),
        ) as client:
            
            config = types.GenerateContentConfig(
                system_instruction=(
                    "You are a friendly, helpful general-purpose "
                    "AI assistant. Help with everyday questions, "
                    "learning, writing, brainstorming, planning, "
                    "programming, and problem-solving. "
                    "Give clear answers with useful examples. "
                    "Ask clarifying questions when necessary. "
                    "Acknowledge uncertainty and avoid making up facts. "
                    "Do not claim access to real-time information "
                    "unless tools explicitly provide it."
                ),
                max_output_tokens=1024,
            )

            chat = client.chats.create(
                model=model,
                config=config,
            )
            print(f"Model: {model}\n")
            return run_chat(chat, client, model, config)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except ValueError:
        print("Could not initialize Gemini. Check your key and model configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
