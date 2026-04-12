import os
from typing import List, Dict, Any
from stack.voice.voice_client import VoiceClient

# Simulated StackAgent to mirror the expected behavior of the system
# This allows the demo to run without needing the full agent infrastructure
class MockTool:
    def __init__(self, name, behavior):
        self.name = name
        self.behavior = behavior
    def __call__(self, **kwargs):
        print(f"[Tool Execution] Calling {self.name} with {kwargs}")
        return self.behavior(**kwargs)

def mock_task_list(**kwargs):
    # Simulates the result of calling the TaskList tool
    return {
        "success": True,
        "tasks": [
            {"id": "1", "subject": "Extract Evaluation Metrics", "status": "pending"},
            {"id": "10", "subject": "Professional Packaging", "status": "pending"},
            {"id": "19", "subject": "Voice Integration Showcase", "status": "pending"},
            {"id": "21", "subject": "Complete API Documentation", "status": "pending"},
        ]
    }

class StackAgent:
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self.tools = {
            "TaskList": MockTool("TaskList", mock_task_list),
        }
        print(f"StackAgent initialized for workspace: {workspace}")

    def process_command(self, command: str):
        print(f"\nUser Command: {command}")
        print("-" * 40)

        # Simulated Reasoning Flow
        print("\nReasoning: The user is asking about the status of current tasks. I should use the TaskList tool to retrieve the current state of the project.")

        # Call the TaskList tool
        result = self.tools["TaskList"]()

        if result.get("success"):
            tasks = result.get("tasks", [])
            task_summary = "\n".join([f"- {t['subject']} ({t['status']})" for t in tasks])
            response_text = f"Here is the status of your current tasks:\n\n{task_summary}"
            print(f"\nAgent Response: {response_text}")
            return response_text
        else:
            return "I'm sorry, I couldn't retrieve the task list at the moment."

def main():
    # 1. Initialize Voice Client and StackAgent
    # Using default local voice server address
    voice_client = VoiceClient(base_url="http://localhost:8000")
    agent = StackAgent(workspace="/Users/walidsobhi/stack-2.9")

    # 2. Simulate a voice command
    voice_command = "What is the status of my current tasks?"
    print(f"Simulating voice input: '{voice_command}'")

    # 3. Use StackAgent to process the command
    response_text = agent.process_command(voice_command)

    # 4. Send the resulting text back to the voice server for synthesis
    print("\nGenerating audio response...")
    try:
        # Using 'default' voice model
        audio_data = voice_client.synthesize(text=response_text, voice_name="default")

        # Save the resulting audio to a file for verification
        output_file = "demo_voice_response.wav"
        voice_client.download_audio(audio_data, output_file)
        print(f"Success! Voice response saved to {output_file}")
    except Exception as e:
        print(f"Error during audio synthesis: {e}")
        print("Note: Make sure the voice server is running (python stack/voice/voice_server.py)")

if __name__ == "__main__":
    main()
