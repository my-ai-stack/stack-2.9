"""
Stack 2.9 - Web UI Chat
Simple web interface using Streamlit
"""
import streamlit as st
import os
import requests
import json

# Configure page
st.set_page_config(
    page_title="Stack 2.9",
    page_icon="💻",
    layout="wide"
)

# Title
st.title("💻 Stack 2.9")
st.caption("AI Coding Assistant")

# Sidebar settings
with st.sidebar:
    st.header("Settings")

    model = st.selectbox(
        "Model",
        ["minimax-m2.5:cloud", "qwen2.5-coder:1.5b"],
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
                import json
                # Use local Ollama - your minimax is registered there
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model,
                        "messages": [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120,
                    stream=False
                )

                if response.status_code == 200:
                    text = response.text.strip()
                    # Try to parse each line until we get content
                    assistant_msg = ""
                    for line in text.split('\n'):
                        if line.strip():
                            try:
                                result = json.loads(line)
                                content = result.get("message", {}).get("content", "")
                                if content:
                                    assistant_msg = content
                                    break
                            except:
                                continue

                    if not assistant_msg:
                        assistant_msg = text
                else:
                    assistant_msg = f"Error: {response.status_code}\n{response.text[:200]}"

            except Exception as e:
                assistant_msg = f"Connection Error: {str(e)}\n\nMake sure Ollama is running with: ollama serve"

        st.markdown(assistant_msg)
        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})