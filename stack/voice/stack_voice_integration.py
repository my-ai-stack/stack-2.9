import requests
from typing import Optional, Union
import io
import json
from voice_client import VoiceClient

class StackWithVoice:
    def __init__(self, stack_api_url: str, voice_api_url: str = "http://localhost:8000"):
        self.stack_api_url = stack_api_url
        self.voice_client = VoiceClient(voice_api_url)
        self.session = requests.Session()
        
        # Cache for voice models to avoid repeated API calls
        self._voice_cache = {}
    
    def _get_stack_response(self, prompt: str) -> str:
        """Get response from Stack 2.9 API"""
        try:
            response = self.session.post(
                f"{self.stack_api_url}/api/chat",
                json={"prompt": prompt, "model": "stack-2.9"},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
            
        except requests.RequestException as e:
            raise Exception(f"Stack API request failed: {str(e)}")
    
    def _get_voice_model(self, voice_name: str) -> Optional[dict]:
        """Get voice model info from cache or API"""
        if voice_name in self._voice_cache:
            return self._voice_cache[voice_name]
        
        try:
            voices = self.voice_client.list_voices()
            for voice in voices:
                if voice == voice_name:
                    self._voice_cache[voice_name] = {"name": voice_name}
                    return {"name": voice_name}
            return None
        except Exception as e:
            print(f"Warning: Failed to get voice models: {e}")
            return None
    
    def voice_chat(self, prompt_audio_path: str, voice_name: str = "default") -> Optional[bytes]:
        """Complete voice chat workflow: audio → text → response → audio"""
        # Step 1: Convert audio to text (placeholder - in real implementation, use speech-to-text)
        print(f"Converting audio to text: {prompt_audio_path}")
        prompt_text = self._audio_to_text(prompt_audio_path)
        if not prompt_text:
            return None
        
        print(f"User prompt: {prompt_text}")
        
        # Step 2: Get response from Stack 2.9
        print("Getting response from Stack 2.9...")
        response_text = self._get_stack_response(prompt_text)
        
        if not response_text:
            return None
        
        print(f"Stack response: {response_text}")
        
        # Step 3: Convert response to audio
        print(f"Generating voice response with voice: {voice_name}")
        audio_data = self.voice_client.synthesize(response_text, voice_name)
        
        return audio_data
    
    def _audio_to_text(self, audio_path: str) -> str:
        """Convert audio to text (placeholder implementation)"""
        # In a real implementation, you would use a speech-to-text service
        # For now, return a placeholder or read from a text file with the same name
        text_path = audio_path.replace(".wav", ".txt").replace(".mp3", ".txt")
        
        if os.path.exists(text_path):
            with open(text_path, 'r') as f:
                return f.read().strip()
        
        # Fallback: return a generic prompt
        return "This is a test voice prompt."
    
    def voice_command(self, command: str, voice_name: str = "default") -> Optional[bytes]:
        """Execute voice command and get spoken response"""
        print(f"Executing voice command: {command}")
        
        # In a real implementation, you would parse the command and execute appropriate actions
        # For now, just pass it to Stack 2.9 as-is
        response_text = self._get_stack_response(command)
        
        if not response_text:
            return None
        
        print(f"Command response: {response_text}")
        
        # Generate voice response
        audio_data = self.voice_client.synthesize(response_text, voice_name)
        
        return audio_data
    
    def streaming_voice_chat(self, prompt_audio_path: str, voice_name: str = "default") -> None:
        """Stream voice chat (placeholder implementation)"""
        print("Starting streaming voice chat...")
        
        # Get initial response
        prompt_text = self._audio_to_text(prompt_audio_path)
        response_text = self._get_stack_response(prompt_text)
        
        if not response_text:
            print("No response received")
            return
        
        print("Streaming response:")
        print(response_text)
        
        # In a real streaming implementation, you would:
        # 1. Stream audio chunks to speech-to-text
        # 2. Send partial prompts to Stack 2.9
        # 3. Stream partial responses to TTS
        # 4. Play audio as it's generated
        
        # For now, just generate the complete response
        audio_data = self.voice_client.synthesize(response_text, voice_name, stream=True)
        
        # Save to file for demonstration
        output_path = "./streaming_response.wav"
        self.voice_client.download_audio(audio_data, output_path)
        print(f"Streaming response saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    stack_voice = StackWithVoice(
        stack_api_url="http://localhost:5000",  # Example Stack 2.9 API URL
        voice_api_url="http://localhost:8000"
    )
    
    print("Testing Stack with Voice integration...")
    
    # Test voice chat
    # audio_data = stack_voice.voice_chat("test_prompt.wav", "default")
    # if audio_data:
    #     stack_voice.voice_client.download_audio(audio_data, "stack_response.wav")
    #     print("Voice chat response saved to stack_response.wav")
    
    # Test voice command
    # audio_data = stack_voice.voice_command("Write a Python function to calculate factorial", "default")
    # if audio_data:
    #     stack_voice.voice_client.download_audio(audio_data, "command_response.wav")
    #     print("Voice command response saved to command_response.wav")
    
    # Test streaming
    # stack_voice.streaming_voice_chat("test_prompt.wav", "default")