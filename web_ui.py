"""
Stack 2.9 - Web UI Chat
Simple web interface using Streamlit
"""
import streamlit as st
from typing import List, Dict
import os

# Configure page
st.set_page_config(
    page_title="Stack 2.9",
    page_icon="💻",
    layout="wide"
)

# Model configuration
MODEL_NAME = os.environ.get("MODEL_NAME", "minimax-m2.5:cloud")
PROVIDER = os.environ.get("MODEL_PROVIDER", "ollama")

# Title
st.title("💻 Stack 2.9")
st.caption("AI Coding Assistant")

# Sidebar settings
with st.sidebar:
    st.header("Settings")

    model = st.selectbox(
        "Model",
        ["minimax-m2.5:cloud", "qwen2.5-coder:1.5b", "llama3"],
        index=0
    )

    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 100, 4096, 2048, 100)

    st.divider()

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm Stack 2.9, your AI coding assistant. How can I help?"}
    ]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                import requests

                # Call Ollama API
                response = requests.post(
                    f"http://localhost:11434/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    assistant_msg = result["message"]["content"]
                else:
                    assistant_msg = f"Error: {response.status_code}"

            except Exception as e:
                assistant_msg = f"Error: {str(e)}"

        st.markdown(assistant_msg)
        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})