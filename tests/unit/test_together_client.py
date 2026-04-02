"""
Tests for Together AI model client.
"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add stack-2.9-eval directory to path to import model_client directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "stack-2.9-eval"))

from model_client import (
    TogetherClient,
    BaseModelClient,
    ChatMessage,
    GenerationResult,
    create_model_client
)


def test_together_client_init_with_api_key():
    """Test initialization with explicit API key."""
    client = TogetherClient(api_key="test-key", model="togethercomputer/Qwen2.5-Coder-32B-Instruct")
    assert client.api_key == "test-key"
    assert client.model == "togethercomputer/Qwen2.5-Coder-32B-Instruct"
    assert client.base_url == "https://api.together.xyz/v1"


def test_together_client_init_with_env_var():
    """Test initialization with environment variable."""
    os.environ["TOGETHER_API_KEY"] = "env-key"
    try:
        client = TogetherClient()
        assert client.api_key == "env-key"
    finally:
        del os.environ["TOGETHER_API_KEY"]


def test_together_client_init_without_api_key():
    """Test that initialization fails without API key."""
    # Ensure env var is not set
    if "TOGETHER_API_KEY" in os.environ:
        del os.environ["TOGETHER_API_KEY"]
    with pytest.raises(ValueError, match="Together API key required"):
        TogetherClient()


def test_together_client_get_model_name():
    """Test get_model_name returns the model."""
    client = TogetherClient(api_key="test-key", model="test-model")
    assert client.get_model_name() == "test-model"


def test_together_client_generate_success():
    """Test successful generate call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].text = "Hello, world!"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = MagicMock()
    mock_response.usage.completion_tokens = 5
    mock_response.model_dump.return_value = {"mock": "response"}

    with patch('model_client.OpenAI') as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        client = TogetherClient(api_key="test-key")
        result = client.generate("Say hello")

        assert result.text == "Hello, world!"
        assert result.model == client.model
        assert result.tokens == 5
        assert result.finish_reason == "stop"
        assert result.raw_response == {"mock": "response"}
        mock_client.completions.create.assert_called_once()
        call_args = mock_client.completions.create.call_args
        assert call_args.kwargs["model"] == client.model
        assert call_args.kwargs["prompt"] == "Say hello"


def test_together_client_generate_failure():
    """Test generate call failure."""
    with patch('model_client.OpenAI') as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.completions.create.side_effect = Exception("API error")
        mock_openai_cls.return_value = mock_client

        client = TogetherClient(api_key="test-key")
        with pytest.raises(Exception, match="API error"):
            client.generate("test")


def test_together_client_chat_success():
    """Test successful chat call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "Chat response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = MagicMock()
    mock_response.usage.completion_tokens = 10
    mock_response.model_dump.return_value = {"mock": "chat"}

    with patch('model_client.OpenAI') as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        client = TogetherClient(api_key="test-key")
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!"),
        ]
        result = client.chat(messages)

        assert result.text == "Chat response"
        assert result.model == client.model
        assert result.tokens == 10
        assert result.finish_reason == "stop"
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == client.model
        assert len(call_args.kwargs["messages"]) == 2
        assert call_args.kwargs["messages"][0] == {"role": "user", "content": "Hello"}
        assert call_args.kwargs["messages"][1] == {"role": "assistant", "content": "Hi there!"}


def test_together_client_chat_with_tools():
    """Test chat call with tools."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = ""
    mock_response.choices[0].finish_reason = "tool_calls"
    mock_response.usage = MagicMock()
    mock_response.usage.completion_tokens = 0
    mock_response.model_dump.return_value = {}

    with patch('model_client.OpenAI') as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        client = TogetherClient(api_key="test-key")
        messages = [ChatMessage(role="user", content="What's the weather?")]
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {}
            }
        }]
        result = client.chat(messages, tools=tools)

        assert result.text == ""
        call_args = mock_client.chat.completions.create.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == tools


def test_together_client_base_url():
    """Test that the client uses Together's base URL."""
    client = TogetherClient(api_key="test-key")
    assert client.base_url == "https://api.together.xyz/v1"
    # Check that the OpenAI client is initialized with this base_url
    with patch('model_client.OpenAI') as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.completions.create.return_value = MagicMock(
            choices=[MagicMock(text="ok", finish_reason="stop")],
            usage=MagicMock(completion_tokens=1),
            model_dump=lambda: {}
        )
        mock_openai_cls.return_value = mock_client
        client.generate("test")
        mock_openai_cls.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.together.xyz/v1",
            timeout=120
        )


def test_together_client_default_model():
    """Test default model when none provided."""
    # Without env var
    client = TogetherClient(api_key="test-key")
    assert client.model == "togethercomputer/Qwen2.5-Coder-32B-Instruct"

    # With env var
    os.environ["TOGETHER_MODEL"] = "custom/model"
    try:
        client = TogetherClient(api_key="test-key")
        assert client.model == "custom/model"
    finally:
        del os.environ["TOGETHER_MODEL"]


def test_create_model_client_together():
    """Test factory function creates TogetherClient."""
    client = create_model_client("together", api_key="test-key")
    assert isinstance(client, TogetherClient)
    assert client.api_key == "test-key"
    assert client.model == "togethercomputer/Qwen2.5-Coder-32B-Instruct"

    # Test with custom model
    client = create_model_client("together", model="custom/model", api_key="key")
    assert client.model == "custom/model"


def test_create_model_client_together_from_env():
    """Test factory reads env vars."""
    os.environ["TOGETHER_API_KEY"] = "env-key"
    os.environ["TOGETHER_MODEL"] = "env/model"
    try:
        client = create_model_client("together")
        assert client.api_key == "env-key"
        assert client.model == "env/model"
    finally:
        del os.environ["TOGETHER_API_KEY"]
        del os.environ["TOGETHER_MODEL"]
