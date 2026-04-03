import time
import os
from voice_client import VoiceClient
from stack_voice_integration import StackWithVoice

# Configuration
STACK_API_URL = "http://localhost:5000"
VOICE_API_URL = "http://localhost:8000"
DEFAULT_VOICE = "default"

# Initialize clients
voice_client = VoiceClient(VOICE_API_URL)
stack_voice = StackWithVoice(STACK_API_URL, VOICE_API_URL)

# Helper function to play audio (placeholder)
def play_audio(audio_data: bytes) -> None:
    """Play audio data (placeholder implementation)"""
    output_path = "./output.wav"
    voice_client.download_audio(audio_data, output_path)
    print(f"Audio saved to {output_path}")
    print("To play audio, use: open output.wav (macOS) or your preferred audio player")

# Example 1: Basic voice chat
print("\n=== Example 1: Basic Voice Chat ===")
print("This example simulates a voice conversation with the coding assistant.")
print("In a real implementation, you would provide actual audio files.")

# Create a test prompt audio file (placeholder)
test_prompt = "How do I create a REST API in Python using FastAPI?"
with open("test_prompt.txt", 'w') as f:
    f.write(test_prompt)

print(f"\nTest prompt: {test_prompt}")

# Simulate voice chat
print("\nSimulating voice chat...")
response_audio = stack_voice.voice_chat("test_prompt.wav", DEFAULT_VOICE)

if response_audio:
    play_audio(response_audio)
    print("\nVoice chat completed successfully!")
else:
    print("\nVoice chat failed or no response received")

# Example 2: Voice command to code generation
print("\n\n=== Example 2: Voice Command to Code Generation ===")
print("This example shows how to use voice commands to generate code.")

code_command = "Create a Python class for a banking system with account management"
print(f"\nVoice command: {code_command}")

# Simulate voice command
print("\nExecuting voice command...")
command_response = stack_voice.voice_command(code_command, DEFAULT_VOICE)

if command_response:
    play_audio(command_response)
    print("\nVoice command executed successfully!")
else:
    print("\nVoice command failed or no response received")

# Example 3: Streaming voice responses
print("\n\n=== Example 3: Streaming Voice Responses ===")
print("This example demonstrates streaming voice responses.")

streaming_prompt = "Explain how to implement machine learning in Python"
print(f"\nStreaming prompt: {streaming_prompt}")

# Simulate streaming voice chat
print("\nStarting streaming voice chat...")
stack_voice.streaming_voice_chat("test_prompt.wav", DEFAULT_VOICE)

print("\nStreaming voice chat completed!")

# Example 4: Error handling
print("\n\n=== Example 4: Error Handling ===")
print("This example demonstrates error handling in the voice integration.")

# Test with invalid voice name
print("\nTesting with invalid voice name...")
try:
    invalid_response = stack_voice.voice_chat("test_prompt.wav", "nonexistent_voice")
    if invalid_response:
        play_audio(invalid_response)
except Exception as e:
    print(f"Error handled correctly: {e}")

# Test with empty prompt
print("\nTesting with empty prompt...")
try:
    empty_response = stack_voice.voice_chat("empty_prompt.wav", DEFAULT_VOICE)
    if empty_response:
        play_audio(empty_response)
except Exception as e:
    print(f"Error handled correctly: {e}")

# Example 5: Voice model management
print("\n\n=== Example 5: Voice Model Management ===")
print("This example shows how to manage voice models.")

print("\nListing available voices...")
available_voices = voice_client.list_voices()
print(f"Available voices: {available_voices}")

# Note: Voice cloning requires actual audio files
# print("\nCloning a new voice...")
# clone_result = voice_client.clone_voice("my_audio_sample.wav", "custom_voice")
# print(f"Clone result: {clone_result}")

print("\nAll examples completed!")
print("\n=== Next Steps ===")
print("1. Implement actual speech-to-text for audio_to_text()")
print("2. Integrate with real Stack 2.9 API")
print("3. Add proper audio playback functionality")
print("4. Implement streaming TTS properly")
print("5. Add voice model training with Coqui TTS")