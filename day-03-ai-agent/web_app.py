"""A small Streamlit interface with separate tasks for each browser session."""

import os

import streamlit as st

from main import DEFAULT_MODEL, api_error_message
from tasks import TaskError, TaskStore, SAMPLE_TASKS, load_tasks


def render_trace(trace):
    if trace:
        with st.expander("Tools used"):
            for entry in trace:
                st.write(entry["tool"])
                st.json(entry)


def main():
    st.set_page_config(page_title="Study Planner", page_icon="📚", layout="centered")
    st.title("Study Planner")
    st.caption("Work out your study time, plan pending tasks, and track what you finish.")

    if "task_store" not in st.session_state:
        try:
            st.session_state.task_store = TaskStore(load_tasks(SAMPLE_TASKS))
        except TaskError as error:
            st.error(str(error))
            st.stop()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = st.sidebar.text_input("Gemini model", value=os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL)
    model = model.strip() or DEFAULT_MODEL
    st.sidebar.caption("Tasks stay in this browser session. A new chat keeps task progress.")
    agent = st.session_state.get("agent")
    if agent is not None and agent.model != model:
        agent.model = model
        agent.clear()
        st.session_state.messages = []

    if st.sidebar.button("New chat"):
        st.session_state.messages = []
        if agent is not None:
            agent.clear()
        st.rerun()
    if st.sidebar.button("Reset sample tasks"):
        st.session_state.task_store = TaskStore(load_tasks(SAMPLE_TASKS))
        if agent is not None:
            agent.task_store = st.session_state.task_store
            agent.clear()
        st.session_state.messages = []
        st.rerun()

    pending = st.session_state.task_store.list_pending_tasks()["tasks"]
    st.sidebar.subheader("Pending tasks")
    if pending:
        for task in pending:
            st.sidebar.write(f"{task['title']} · {task['estimated_minutes']} min")
    else:
        st.sidebar.write("All tasks are complete.")

    if not key:
        st.info("Set GEMINI_API_KEY in your terminal, then restart Streamlit. See the project README.")
    else:
        from agent import StudyAgent
        if agent is None:
            agent = StudyAgent(None, model, version=4, task_store=st.session_state.task_store)
            st.session_state.agent = agent

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_trace(message.get("trace", []))

    if agent is not None:
        for task_id, task in list(agent.pending_updates.items()):
            with st.container(border=True):
                st.write(f"Mark '{task['title']}' (ID: {task_id}) as complete?")
                approve, cancel = st.columns(2)
                approved = approve.button("Confirm completion", key=f"approve-{task_id}")
                cancelled = cancel.button("Cancel", key=f"cancel-{task_id}")
                if approved or cancelled:
                    try:
                        result = agent.resolve_update(task_id, approve=approved)
                        message = (f"Completed: {task['title']}" if result["status"] == "completed"
                                   else f"Update cancelled: {task['title']}")
                    except TaskError as error:
                        message = str(error)
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.rerun()

    question = st.chat_input("Try: Plan 90 minutes a day for 5 days", disabled=(
        not key or bool(agent and agent.pending_updates)
    ))
    if question:
        import httpx
        from google import genai
        from google.genai import errors, types
        from agent import AgentError

        st.session_state.messages.append({"role": "user", "content": question})
        agent.trace = []
        try:
            # A client is opened only for this request and always closed afterward.
            with st.spinner("Planning..."):
                with genai.Client(api_key=key, vertexai=False,
                                  http_options=types.HttpOptions(timeout=30_000)) as client:
                    agent.client = client
                    answer = agent.ask(question)
        except AgentError as error:
            answer = str(error)
        except errors.APIError as error:
            answer = api_error_message(error.code)
        except httpx.TimeoutException:
            answer = "The request timed out. Try again."
        except httpx.TransportError:
            answer = "Connection failed. Check your internet connection."
        except ValueError:
            answer = "Could not initialize Gemini. Check the model and key configuration."
        finally:
            agent.client = None
        st.session_state.messages.append({"role": "assistant", "content": answer,
                                          "trace": list(agent.trace)})
        st.rerun()


if __name__ == "__main__":
    main()
