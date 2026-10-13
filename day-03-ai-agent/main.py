"""Terminal entry point for the Gemini study planner."""

import os


DEFAULT_MODEL = "gemini-3.5-flash-lite"


def api_error_message(code):
    if code in (401, 403):
        return "Check GEMINI_API_KEY and your project permissions."
    if code == 404:
        return "Model unavailable. Set GEMINI_MODEL to a model your account can use."
    if code == 429:
        return "Gemini quota reached. Check AI Studio usage before retrying."
    if code == 400:
        return "Gemini rejected the request. Check your model and configuration."
    return "Gemini could not complete the request. Please try again later."


def run_terminal(agent):
    import httpx
    from google.genai import errors
    from agent import AgentError

    print("Study Planner Agent | /help, /clear, /exit")
    while True:
        agent.trace = []
        try:
            question = input("\nYou: ").strip()
            if question.lower() in {"exit", "quit", "/exit", "/quit"}:
                print("Goodbye!")
                return 0
            if question.lower() == "/help":
                print("Ask about study time and pending tasks. /clear resets chat; /exit closes the app.")
                continue
            if question.lower() == "/clear":
                agent.clear()
                print("Conversation cleared.")
                continue
            answer = agent.ask(question)
            print(f"\nAssistant: {answer}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0
        except AgentError as error:
            print(error)
        except errors.APIError as error:
            print(api_error_message(error.code))
            if error.code in (400, 401, 403, 404):
                return 1
        except httpx.TimeoutException:
            print("The request timed out. Try again.")
        except httpx.TransportError:
            print("Connection failed. Check your internet connection.")
        finally:
            # A confirmed write remains saved even if the next model request fails.
            for entry in agent.trace:
                print(f"Tool: {entry['tool']} -> {entry.get('result', entry.get('error'))}")


def confirm_update(task):
    print(f"\nMark '{task['title']}' (ID: {task['id']}) as complete?")
    return input("Type yes to confirm; anything else cancels: ").strip().lower() == "yes"


def main(version=4):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("Missing GEMINI_API_KEY. See day-03-ai-agent/README.md for setup.")
        return 1
    try:
        from google import genai
        from google.genai import types
        from agent import StudyAgent
        from tasks import TaskError, local_task_store
    except ImportError:
        print("Install dependencies: python -m pip install -r day-03-ai-agent/requirements.txt")
        return 1
    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
    try:
        with genai.Client(api_key=key, vertexai=False,
                          http_options=types.HttpOptions(timeout=30_000)) as client:
            store = local_task_store() if version >= 4 else None
            return run_terminal(StudyAgent(client, model, version=version,
                                           task_store=store, confirm=confirm_update if version >= 4 else None))
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except ValueError:
        print("Could not initialize Gemini. Check your configuration.")
        return 1
    except TaskError as error:
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
