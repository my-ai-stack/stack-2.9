# Stack 2.9 Voice Integration Module

A comprehensive voice integration module that connects the Stack 2.9 coding assistant with voice cloning and text-to-speech capabilities.

## Architecture Overview

This integration provides a complete voice-enabled coding assistant workflow:

```
Voice Input → Speech-to-Text → Stack 2.9 API → Text Response → Text-to-Speech → Voice Output
     ↑                                                                       ↓
Voice Cloning ← Voice Models ← FastAPI Service ← Python Client ← Integration Layer
```

### Core Components

1. **voice_server.py** - FastAPI voice service with endpoints for:
   - `POST /clone` - Clone voice from audio samples
   - `POST /synthesize` - Text-to-speech with cloned voices  
   - `GET /voices` - List available voice models

2. **voice_client.py** - Python client for interacting with the voice API

3. **stack_voice_integration.py** - Main integration with Stack 2.9
   - `voice_chat()` - Complete voice conversation workflow
   - `voice_command()` - Voice command execution
   - `streaming_voice_chat()` - Real-time voice streaming

4. **integration_example.py** - Usage examples and demonstrations

## Setup Instructions

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Coqui TTS (for voice synthesis)
- Optional: Vosk (for speech-to-text)

### Installation

1. **Clone the voice models directory:**
   ```bash
   mkdir -p voice_models audio_files
   ```

2. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn requests pydantic
   ```

3. **For GPU support (optional):**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Running the Services

1. **Start the voice services:**
   ```bash
   docker-compose up -d
   ```

2. **Start the FastAPI server:**
   ```bash
   cd stack-2.9-voice
   uvicorn voice_server:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:8000/voices
   ```

## API Reference

### Voice Server API

#### `GET /voices`
List all available voice models.

**Response:**
```json
{
  "voices": ["default", "custom_voice"],
  "count": 2
}
```

#### `POST /clone`
Clone a voice from an audio sample.

**Request:**
```json
{
  "voice_name": "my_custom_voice"
}
```

**Response:**
```json
{
  "success": true,
  "voice_name": "my_custom_voice",
  "message": "Voice model created successfully"
}
```

#### `POST /synthesize`
Generate speech with a cloned voice.

**Request:**
```json
{
  "text": "Hello, this is a test.",
  "voice_name": "my_custom_voice"
}
```

**Response:** Raw audio data (wav format)

#### `POST /synthesize_stream`
Stream speech synthesis (for real-time applications).

**Request:** Same as `/synthesize`

**Response:** Streaming audio data

### Stack Voice Integration

#### `voice_chat(prompt_audio_path, voice_name)`
Complete voice conversation workflow.

**Parameters:**
- `prompt_audio_path`: Path to input audio file
- `voice_name`: Name of the voice model to use

**Returns:** Audio data of the response

#### `voice_command(command, voice_name)`
Execute a voice command and get spoken response.

**Parameters:**
- `command`: Voice command string
- `voice_name`: Name of the voice model to use

**Returns:** Audio data of the response

#### `streaming_voice_chat(prompt_audio_path, voice_name)`
Real-time streaming voice conversation.

**Parameters:** Same as `voice_chat`

## Example Workflows

### 1. Basic Voice Chat
```python
from stack_voice_integration import StackWithVoice

# Initialize integration
stack_voice = StackWithVoice(
    stack_api_url="http://localhost:5000",
    voice_api_url="http://localhost:8000"
)

# Start voice conversation
response_audio = stack_voice.voice_chat("user_prompt.wav", "default")
```

### 2. Voice Command to Code Generation
```python
# Execute voice command
response_audio = stack_voice.voice_command(
    "Create a Python class for a banking system",
    "default"
)
```

### 3. Streaming Voice Responses
```python
# Start streaming conversation
stack_voice.streaming_voice_chat("user_prompt.wav", "default")
```

## Performance Notes

### Voice Cloning
- **Input format:** WAV, MP3 (converted internally)
- **Processing time:** ~30 seconds per voice model
- **Model size:** ~10-50MB per voice
- **Quality:** Depends on input audio quality and duration

### Text-to-Speech
- **Processing speed:** ~100-200 chars/second
- **Latency:** ~1-2 seconds for short responses
- **Audio format:** 22kHz WAV (adjustable)
- **Voice quality:** Coqui XTTS provides natural-sounding voices

### Integration Overhead
- **Total latency:** ~3-5 seconds for complete voice chat
- **Memory usage:** ~1-2GB for voice models
- **CPU usage:** ~20-30% during synthesis

## Error Handling

The integration includes comprehensive error handling:

- **Voice cloning failures:** Returns descriptive error messages
- **TTS synthesis errors:** Falls back to default voice
- **API connection issues:** Implements retry logic
- **Audio format errors:** Automatic format conversion

## Security Considerations

- **Audio data:** Processed locally, not stored permanently
- **Voice models:** Encrypted at rest
- **API authentication:** Implement API keys in production
- **Input validation:** All user inputs are sanitized

## Troubleshooting

### Common Issues

1. **Voice cloning fails:**
   - Ensure audio quality is good (clear speech, minimal background noise)
   - Check that audio duration is at least 30 seconds
   - Verify input format is supported

2. **TTS synthesis is slow:**
   - Check GPU availability for acceleration
   - Reduce audio quality settings
   - Optimize model loading

3. **API connection errors:**
   - Verify all services are running
   - Check network connectivity
   - Review firewall settings

### Debug Mode

Enable debug logging for detailed output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Real-time speech-to-text integration
- [ ] Multi-language support
- [ ] Voice activity detection
- [ ] Adaptive bitrate streaming
- [ ] Voice emotion and intonation control
- [ ] Batch voice processing
- [ ] Cloud voice model storage

## License

This project is part of the Stack 2.9 voice integration ecosystem.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Enable debug logging for detailed error information