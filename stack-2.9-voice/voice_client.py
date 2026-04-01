import requests
from typing import Optional, BinaryIO
import io

class VoiceClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def clone_voice(self, audio_sample_path: str, voice_name: str) -> dict:
        """Clone voice from audio sample file"""
        try:
            with open(audio_sample_path, 'rb') as audio_file:
                files = {'file': audio_file}
                data = {"voice_name": voice_name}
                
                response = self.session.post(
                    f"{self.base_url}/clone",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                return response.json()
                
        except requests.RequestException as e:
            raise Exception(f"Voice cloning failed: {str(e)}")
    
    def synthesize(self, text: str, voice_name: str, stream: bool = False) -> Optional[bytes]:
        """Generate speech with cloned voice"""
        try:
            data = {
                "text": text,
                "voice_name": voice_name
            }
            
            if stream:
                # For streaming, you might want to use Response.iter_content()
                # This is a placeholder for actual streaming implementation
                response = self.session.post(
                    f"{self.base_url}/synthesize_stream",
                    json=data,
                    stream=True
                )
                response.raise_for_status()
                
                # Collect all chunks (for demonstration)
                audio_data = b""
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_data += chunk
                return audio_data
                
            else:
                response = self.session.post(
                    f"{self.base_url}/synthesize",
                    json=data
                )
                response.raise_for_status()
                
                return response.content
                
        except requests.RequestException as e:
            raise Exception(f"Text-to-speech failed: {str(e)}")
    
    def list_voices(self) -> list:
        """List available voice models"""
        try:
            response = self.session.get(f"{self.base_url}/voices")
            response.raise_for_status()
            
            data = response.json()
            return data.get("voices", [])
            
        except requests.RequestException as e:
            raise Exception(f"Failed to list voices: {str(e)}")
    
    def download_audio(self, audio_data: bytes, output_path: str) -> None:
        """Save audio data to file"""
        try:
            with open(output_path, 'wb') as f:
                f.write(audio_data)
        except Exception as e:
            raise Exception(f"Failed to save audio file: {str(e)}")

# Example usage
if __name__ == "__main__":
    client = VoiceClient()
    
    print("Testing voice client...")
    
    # List available voices
    voices = client.list_voices()
    print(f"Available voices: {voices}")
    
    # Clone a voice (you need to provide an actual audio file)
    # result = client.clone_voice("sample_audio.wav", "my_voice")
    # print(f"Clone result: {result}")
    
    # Synthesize speech
    # audio_data = client.synthesize("Hello, this is a test of the voice cloning system.", "my_voice")
    # if audio_data:
    #     client.download_audio(audio_data, "output.wav")
    #     print("Audio saved to output.wav")