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
