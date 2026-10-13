
import os

import httpx
import streamlit as st
from google import genai
from google.genai import errors, types


st.set_page_config(
    page_title="My AI Assistant",
    page_icon="🤖",
)

st.title("🤖 My AI Assistant")
st.caption("Powered by Google Gemini")

# Read settings without exposing the API key.
api_key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"

if not api_key:
    st.error("GEMINI_API_KEY is missing. Configure it in your terminal.")
    st.stop()

# Instructions for our general-purpose assistant.
config = types.GenerateContentConfig(
    system_instruction=(
        "You are a friendly general AI assistant. "
        "Help with learning, writing, coding, planning, "
        "and everyday questions. Explain clearly and "
        "acknowledge uncertainty."
    ),
    max_output_tokens=1024,
)

# Create one Gemini client per Streamlit session.
if "client" not in st.session_state:
    st.session_state.client = genai.Client(
        api_key=api_key,
        vertexai=False,
        http_options=types.HttpOptions(timeout=30000),
    )

# Create a chat session only once.
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model=model,
        config=config,
    )

# Store visible messages between reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset visible messages AND Gemini conversation memory.
if st.button("🆕 New Chat"):
    st.session_state.messages = []
    st.session_state.chat = st.session_state.client.chats.create(
        model=model,
        config=config,
    )

# Display previous conversation messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Receive a new user message.
user_question = st.chat_input("Ask me anything!")

if user_question and user_question.strip():
    user_question = user_question.strip()

    with st.chat_message("user"):
        st.write(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat.send_message(
                    user_question
                )

                answer = response.text

                if answer and answer.strip():
                    st.write(answer)

                    # Remember only successful exchanges.
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_question,
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                    })
                else:
                    st.warning("Gemini returned no text. Try again.")

            except errors.APIError as error:
                if error.code in (401, 403):
                    st.error("Check your Gemini API key and permissions.")
                elif error.code == 404:
                    st.error("The selected Gemini model is unavailable.")
                elif error.code == 429:
                    st.error("Gemini rate limit or quota reached.")
                else:
                    st.error("Gemini could not complete the request.")

            except httpx.TimeoutException:
                st.error("Request timed out. Please try again.")

            except httpx.TransportError:
                st.error("Connection failed. Check your internet connection.")

            except Exception as error:
                st.error(
                    f"Request failed. Error type: {type(error).__name__}"
                )
