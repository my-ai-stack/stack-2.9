import os
import requests
import json
from typing import Any, Dict

# ==============================================================================
# INSTRUCTIONS TO RUN THE VOICE SERVER:
# ------------------------------------------------------------------------------
# 1. Ensure you have the required dependencies installed:
#    pip install fastapi uvicorn pydantic requests
#
# 2. Start the Voice Server by running the following command in a separate terminal:
#    python /Users/walidsobhi/stack-2.9/stack/voice/voice_server.py
#
# 3. The server will start by default on http://0.0.0.0:8000
# ==============================================================================

class MockTool:
    """A simple tool implementation to simulate agent capabilities."""
    def __init__(self, name, behavior):
        self.name = name
        self.behavior = behavior
    def __call__(self, **kwargs):
        print(f"[Tool Execution] Calling {self.name} with {kwargs}")
        return self.behavior(**kwargs)

def mock_get_weather(city: str):
    """Simulated weather tool."""
    return {"success": True, "result": f"The weather in {city} is sunny and 25°C."}

class StackAgent:
    """
    Simulated StackAgent that manages tool execution and integrates
    with the voice synthesis path.
    """
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self.tools = {
            "get_weather": MockTool("get_weather", mock_get_weather),
        }
        print(f"StackAgent initialized for workspace: {workspace}")

    def execute_command(self, text: str) -> str:
        """
        Analyzes a text command, executes the appropriate tool,
        and returns a natural language response.
        """
        print(f"\nProcessing Command: {text}")

        # Simple intent parsing for the demo
        if "weather in" in text.lower():
            city = text.lower().split("weather in")[-1].strip()
            result = self.tools["get_weather"](city=city)
            response_text = result["result"]
        else:
            response_text = "I'm sorry, I don't know how to handle that request."

        return response_text

class VoiceIntegrationClient:
    """
    Handles communication with the Voice Server for synthesis.
    Mirrors the functionality of VoiceApiClient.ts.
    """
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def synthesize(self, text: str, voice_name: str = "default"):
        """
        Sends text to the voice server and receives audio data.
        """
        print(f"\n[Voice Synthesis] Sending text to server: '{text}' using voice '{voice_name}'")
        payload = {
            "text": text,
            "voice_name": voice_name
        }
        try:
            response = requests.post(f"{self.api_url}/synthesize", json=payload)
            if response.status_code == 200:
                print(f"[Voice Synthesis] Received {len(response.content)} bytes of audio data.")
                return response.content
            else:
                print(f"[Voice Synthesis] Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[Voice Synthesis] Connection error: {e}")
            return None

def run_voice_demo():
    # 1. Initialize StackAgent
    agent = StackAgent(workspace="/Users/walidsobhi/stack-2.9")

    # 2. Initialize Voice Integration Client
    voice_client = VoiceIntegrationClient()

    # 3. Simulate a voice command (STT result)
    # In a real scenario, this would come from the voice_server's recording endpoint
    simulated_voice_command = "What is the weather in San Francisco?"
    print(f"\n--- Simulated Voice Input: '{simulated_voice_command}' ---")

    # 4. Agent processes the command and executes a tool
    result_text = agent.execute_command(simulated_voice_command)
    print(f"Agent Result: {result_text}")

    # 5. Return the result through the voice synthesis path
    audio_data = voice_client.synthesize(result_text)

    if audio_data:
        print("\nDemo Success: Result synthesized into audio and ready for playback.")
    else:
        print("\nDemo Failed: Could not synthesize audio. Is the voice server running?")

if __name__ == "__main__":
    run_voice_demo()
