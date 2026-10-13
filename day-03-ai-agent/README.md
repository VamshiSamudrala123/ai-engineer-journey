# Project 03: Study Planner Agent

This project starts with a simple study-time calculator. The next checkpoints
will let Gemini choose tools, read a task list, and request confirmed updates.

## V1: a tool without a model

From the repository root:

```bash
python day-03-ai-agent/v1.py
python -m unittest discover -s day-03-ai-agent -p 'test_*.py' -v
```

Try 90 minutes and 5 days. The result is 450 minutes, or 7.5 hours.
Try a negative value too; the function should reject it.

The calculation belongs to Python. Later, the model will request this same
function using structured arguments. Keeping the calculation separate makes
it easier to tell a tool bug from a model mistake.

## V2: Gemini chooses the tool

Use Python 3.10 or newer. From the repository root, activate your virtual
environment and install the dependencies:

```bash
python -m pip install -r day-03-ai-agent/requirements.txt
```

On macOS, enter your key without adding it to shell history:

```bash
read -s -p "Gemini API key: " GEMINI_API_KEY; echo
export GEMINI_API_KEY
python day-03-ai-agent/v2.py
```

The default is `gemini-3.5-flash-lite`, matching Project 02. You can select
another available model with `export GEMINI_MODEL="your-model-id"`.

Ask: "I can study 90 minutes each day for 5 days. How much time is that?"
The terminal shows the tool result and then Gemini's explanation.

`agent.py` describes the function with a JSON schema and disables automatic
execution in the SDK. The controller checks the name and arguments, runs
the calculator, and sends the result back. It preserves the model's original
response parts and call IDs, which matter when continuing a Gemini tool call.
It stops after five tool rounds or eight tool executions per question.

`/clear` resets conversation history. `/exit` closes the client.

The scripted tests exercise the real controller with a fake SDK boundary;
they do not contact Gemini or prove how reliably the live model chooses tools.

## V3: read tasks and make a plan

```bash
python day-03-ai-agent/v3.py
```

Ask: "I have 90 minutes each day for 5 days. What is pending, and how should
I use that time?" Then ask a follow-up such as "What if I only have two days?"

`tasks.json` is a sample list. Each entry has an ID, title, estimate in minutes,
and a `done` flag. `list_pending_tasks` reads unfinished entries.
`build_study_plan` fills each day in file order, splitting a long task across
days when necessary. It reports work that does not fit and unused time.
The model explains this calculated plan; it does not invent task estimates.

The task reader validates JSON before using it. Task text is treated as data.
V3 reads the sample file and never marks anything complete.
