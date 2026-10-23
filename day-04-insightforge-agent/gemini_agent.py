
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tool_registry import execute_tool

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"


INSTRUCTIONS = """
You are InsightForge AI, a banking analytics assistant.
Use the available tools to obtain real results.
Never invent transaction counts, statistics, or tool outputs.
All banking records come from a synthetic dataset.
A laundering label is not proof of real-world criminal activity.
Explain findings clearly and mention relevant limitations.
"""

BANKING_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="inspect_banking_data",
            description="Inspect banking dataset statistics and date range.",
            parameters_json_schema={
                "type": "object",
                "properties": {},
            },
        ),
        types.FunctionDeclaration(
            name="analyze_payment_formats",
            description=(
                "Analyze transactions grouped by payment format "
                "and currency, including synthetic laundering labels."
            ),
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of groups, from 1 to 100.",
                    }
                },
            },
        ),
        types.FunctionDeclaration(
            name="investigate_account",
            description=(
                "Investigate transaction counts for one account "
                "identified by numeric bank ID and account number."
            ),
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "bank_id": {"type": "integer"},
                    "account_number": {"type": "string"},
                },
                "required": ["bank_id", "account_number"],
            },
        ),
    ]
)


def ask_agent(client, question):
    """Perform one Gemini-selected tool call and explain its result."""

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=question)],
    )

    first_response = client.models.generate_content(
        model=MODEL,
        contents=[user_message],
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCTIONS,
            tools=[BANKING_TOOLS],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY"
                )
            ),
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(disable=True)
            ),
        ),
    )

    calls = first_response.function_calls or []

    if len(calls) != 1:
        raise RuntimeError(
            f"Expected one tool call, received {len(calls)}"
        )

    call = calls[0]
    arguments = dict(call.args or {})

    print(f"\nGemini selected: {call.name}")
    print(f"Arguments: {arguments}")

    result = execute_tool(call.name, arguments)

    print("Banking tool executed successfully.")

    function_response = types.Part.from_function_response(
        name=call.name,
        response={"result": result},
    )

    history = [
        user_message,
        first_response.candidates[0].content,
        types.Content(role="user", parts=[function_response]),
    ]

    final_response = client.models.generate_content(
        model=MODEL,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCTIONS,
            tools=[BANKING_TOOLS],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="NONE"
                )
            ),
        ),
    )

    return final_response.text or "No final answer returned."


def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        print("GEMINI_API_KEY is missing.")
        return

    question = input("Ask InsightForge AI: ").strip()

    if not question:
        print("Please enter a banking question.")
        return

    with genai.Client(api_key=api_key) as client:
        answer = ask_agent(client, question)

    print("\n=== InsightForge AI Answer ===")
    print(answer)


if __name__ == "__main__":
    main()
