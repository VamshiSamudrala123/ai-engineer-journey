
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tool_batch import run_tool_batch


# Load the private API key from the project .env file.
load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"

# Safety limits for the AI agent.
MAX_TOOL_ROUNDS = 3
MAX_TOTAL_TOOL_CALLS = 6


INSTRUCTIONS = """
You are InsightForge AI, a banking analytics assistant.

Use the available tools to obtain real results.
Never invent transaction counts, statistics, or tool outputs.

All banking records come from a synthetic dataset.
A laundering label is not proof of real-world criminal activity.

Explain findings clearly and mention relevant limitations.

If a tool reports invalid arguments, correct the arguments
and retry if the tool execution limits allow it.
"""


# Banking tools available to Gemini.
BANKING_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="inspect_banking_data",
            description=(
                "Inspect banking dataset statistics "
                "and date range."
            ),
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
                        "description": (
                            "Number of groups, from 1 to 100."
                        ),
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
                    "bank_id": {
                        "type": "integer",
                    },
                    "account_number": {
                        "type": "string",
                    },
                },
                "required": [
                    "bank_id",
                    "account_number",
                ],
            },
        ),
    ]
)


def ask_agent(client, question):
    """Run a bounded, multi-tool Gemini investigation."""

    user_message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=question)
        ],
    )

    history = [user_message]

    total_tool_calls = 0

    # Allow up to 3 tool rounds plus one final response.
    for round_index in range(MAX_TOOL_ROUNDS + 1):

        # Require a tool on the first round.
        # Afterward, allow Gemini to use tools or answer.
        mode = "ANY" if round_index == 0 else "AUTO"

        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCTIONS,
                tools=[BANKING_TOOLS],
                tool_config=types.ToolConfig(
                    function_calling_config=(
                        types.FunctionCallingConfig(
                            mode=mode
                        )
                    )
                ),
                automatic_function_calling=(
                    types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                ),
            ),
        )

        calls = getattr(
            response,
            "function_calls",
            None,
        ) or []

        # Gemini has stopped requesting tools.
        if not calls:

            if round_index == 0:
                raise RuntimeError(
                    "Expected at least one banking tool call"
                )

            return (
                response.text
                or "No final answer returned."
            )

        # Enforce the maximum number of tool rounds.
        if round_index >= MAX_TOOL_ROUNDS:
            raise RuntimeError(
                "Tool round limit exceeded"
            )

        # Enforce the maximum total tool calls.
        if (
            total_tool_calls + len(calls)
            > MAX_TOTAL_TOOL_CALLS
        ):
            raise RuntimeError(
                "Total tool call limit exceeded"
            )

        # Verify that Gemini returned model content.
        if (
            not response.candidates
            or not response.candidates[0].content
        ):
            raise RuntimeError(
                "Gemini returned no model content"
            )

        print(f"\nTool round {round_index + 1}")

        # Execute approved banking tools.
        # The batch executor validates the requests.
        response_parts, trace = run_tool_batch(calls)

        total_tool_calls += len(calls)

        # Print the execution trace.
        for entry in trace:
            print(
                f"Gemini selected: {entry['tool']}"
            )
            print(
                f"Arguments: {entry['arguments']}"
            )
            print(
                f"Status: {entry['status']}"
            )

        # Count successful and failed tools.
        success_count = sum(
            entry["status"] == "success"
            for entry in trace
        )

        error_count = len(trace) - success_count

        print(
            f"Tool batch complete: "
            f"{success_count} successful, "
            f"{error_count} failed."
        )

        # Preserve Gemini's tool requests.
        history.append(
            response.candidates[0].content
        )

        # Return tool results (or safe argument errors)
        # to Gemini for another round or a final answer.
        history.append(
            types.Content(
                role="user",
                parts=response_parts,
            )
        )

    raise RuntimeError(
        "Investigation did not finish"
    )


def main():
    """Start the InsightForge AI terminal application."""

    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    if not api_key:
        print(
            "GEMINI_API_KEY is missing."
        )
        return

    question = input(
        "Ask InsightForge AI: "
    ).strip()

    if not question:
        print(
            "Please enter a banking question."
        )
        return

    # Create a Gemini client and run the agent.
    with genai.Client(api_key=api_key) as client:
        answer = ask_agent(
            client,
            question,
        )

    print(
        "\n=== InsightForge AI Answer ==="
    )
    print(answer)


if __name__ == "__main__":
    main()
