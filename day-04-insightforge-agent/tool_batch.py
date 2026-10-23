
from google.genai import types

from tool_registry import AVAILABLE_TOOLS, execute_tool


MAX_CALLS_PER_BATCH = 3


def run_tool_batch(function_calls):
    """Execute a bounded batch of approved tool requests."""

    calls = list(function_calls or [])

    if not calls:
        raise ValueError("No function calls received")

    if len(calls) > MAX_CALLS_PER_BATCH:
        raise ValueError("Too many tool calls in one batch")

    requests = []

    # Validate all tool requests before executing.
    for call in calls:
        name = getattr(call, "name", None)
        arguments = getattr(call, "args", None)

        if name not in AVAILABLE_TOOLS:
            raise ValueError("Unapproved tool requested")

        if arguments is None:
            arguments = {}

        if not isinstance(arguments, dict):
            raise ValueError("Invalid tool arguments")

        requests.append((name, arguments))

    response_parts = []
    trace = []

    for name, arguments in requests:
        print(f"Executing tool: {name}")

        try:
            result = execute_tool(name, arguments)

        except (ValueError, TypeError):
            # Return a safe error without internal details.
            payload = {
                "error": {
                    "code": "INVALID_ARGUMENTS",
                    "message": (
                        "Tool arguments were rejected. "
                        "Check the tool schema and retry."
                    ),
                }
            }
            status = "error"

        else:
            payload = {"result": result}
            status = "success"

        response_parts.append(
            types.Part.from_function_response(
                name=name,
                response=payload,
            )
        )

        trace.append({
            "tool": name,
            "arguments": arguments,
            "status": status,
        })

    return response_parts, trace