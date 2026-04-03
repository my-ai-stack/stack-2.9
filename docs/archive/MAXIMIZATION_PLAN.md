# Maximization Plan for src/ Content

## Current State Analysis
- **src/** is a complete, production-ready AI coding assistant (Claude Code competitor)
- ~300k+ lines of TypeScript
- Features: REPL, MCP, plugins, agents, remote sessions, teleport, worktrees
- Python side: voice cloning prototype + mystack-pilot (two separate projects)

## Strategic Opportunities

### 1. Differentiate src/ (OpenClaw) - Add Unique Value

Since the codebase is already comprehensive, focus on **unique features** Claude Code doesn't have:

**A. Voice Integration (Your Secret Weapon)**
- Create `VoiceCloneTool` and `VoiceSynthesisTool`
- Connect to your Python voice cloning backend
- Use cases:
  - Voice-controlled coding ("Hey Code, refactor this function")
  - TTS responses (listen to explanations)
  - Personalized voices for teams
- Files to create/modify:
  - `src/tools/VoiceCloneTool/VoiceCloneTool.ts` - clone voice from audio
  - `src/tools/VoiceSynthesisTool/VoiceSynthesisTool.ts` - text-to-speech
  - `src/services/voice/` - voice API client
  - Integrate with tool pipeline in `src/tools.ts`

**B. Enhanced Code Intelligence**
- Add RAG over your codebase (already has indexing in mystack-pilot)
- Integrate mystack-pilot's code index as MCP server
- Better cross-file understanding
- Files: `src/services/codeIntelligence/`, MCP server wrapper

**C. Visual/Diagram Generation**
- Add PlantUML, Mermaid, graphviz support
- Generate architecture diagrams from code
- `src/tools/DiagramTool/` - create visuals

**D. Improved Testing & Quality**
- Auto-generate tests (mystack-pilot hints at this)
- Code coverage analysis
- Mutation testing integration

### 2. Unify Python Projects

**Problem**: Voice cloning and mystack-pilot are separate
**Solution**: Merge into one coherent product

```
mystack-pilot/
├── voice/              # Move voice cloning here
│   ├── clone.py
│   ├── synthesize.py
│   └── api.py          # REST/WebSocket server
├── indexing/           # Already exists
├── llm/                # Multi-provider support
├── cli.py              # Main CLI (mystack)
└── pyproject.toml
```

**Integrations:**
- mystack CLI gains `--voice` flag for voice I/O
- mystack chat mode can speak responses
- mystack can accept voice commands
- Shared index: voice search through codebase ("find where we handle auth")

### 3. Platform Strategy for Each Component

| Component | Target Platform | Strategy |
|-----------|----------------|----------|
| OpenClaw (src/) | GitHub (already) + OpenRouter | - List as CLI tool <br> - Offer cloud-hosted SaaS <br> - Enterprise plugins |
| Voice Cloning | Hugging Face + HF Spaces | - Upload fine-tuned model <br> - Free inference API <br> - Upgrade to paid for higher limits |
| mystack-pilot | PyPI + GitHub | - `pip install mystack-pilot` <br> - Voice addon package <br> - VS Code extension |

### 4. Specific File-Level Improvements

**High-Value Files to Enhance:**

1. **`src/tools.ts`** - Tool registry
   - Add voice tools (CloneVoiceTool, SpeakTextTool)
   - Add codebase search tool (using mystack index)
   - Add diagram generation

2. **`src/skills/`** - Skills system
   - Create voice skill: "voice-mode" toggle
   - Create diagram skill: "@diagram class architecture"
   - Create test-generation skill

3. **Python: `voice-cloning/clone_voice.py`**
   - Improve with Coqui XTTS or YourTTS (better quality)
   - Add emotion/style control
   - Export to ONNX for faster inference
   - Add API server (FastAPI)

4. **Python: `mystack-pilot/src/indexing/CodeIndexer.js`** (actually TypeScript based on path)
   - Optimize for large codebases
   - Add semantic search (embeddings)
   - Cross-language support (Python, JS, TS, Go, Rust)

### 5. Quick Wins This Week

**For src/ (TypeScript):**
- [ ] Add 1 voice tool (simple TTS using system `say` or `espeak` first)
- [ ] Add code search tool (grep + ripgrep wrapper)
- [ ] Write docs: TOOL_DEVELOPMENT.md
- [ ] Create example plugin: "my-first-voice-tool"

**For Python:**
- [ ] Merge voice cloning into mystack-pilot structure
- [ ] Add `mystack voice --clone` command
- [ ] Create FastAPI wrapper for voice API
- [ ] Deploy voice API to Hugging Face Spaces (free)

**Cross-cutting:**
- [ ] Write README showing how to combine all pieces
- [ ] Create demo video: "Voice-controlled AI coding"
- [ ] Submit to Product Hunt as "Claude Code + Voice"

### 6. Technical Debt & Optimization

**src/ Performance:**
- Large bundle size (135ms imports) - consider lazy loading more
- File watchers (settings, skills) - debounce more aggressively
- MCP server connections - parallelize better

**Python:**
- Voice models are large - implement progressive loading
- Index can be slow - add incremental updates
- Add caching (Redis) for API

### 7. Go-to-Market Snippet

**Elevator Pitch:**
> "OpenClaw is a voice-enabled AI coding assistant that clones your voice, searches your codebase intelligently, and automates repetitive tasks. Unlike Claude Code, we let you code hands-free with custom voices and built-in RAG."

**Tagline Options:**
- "Your voice, your code, your rules"
- "Code by voice, search by thought"
- "The vocal coding assistant"

## Recommended Priority

1. **Voice tool in src/** → unique differentiator (1-2 days)
2. **Unify Python projects** → cleaner architecture (2-3 days)
3. **Deploy voice API on HF** → free hosting, good discovery (1 day)
4. **Optimize src/** → improve UX (ongoing)
5. **Write docs** → attract contributors (1 week)

## Files to Create/Modify (Immediate)

1. `src/tools/VoiceCloneTool/VoiceCloneTool.ts` - Clone voice
2. `src/tools/VoiceSynthesisTool/VoiceSynthesisTool.ts` - TTS
3. `src/services/voice/VoiceApiClient.ts` - Python backend client
4. `mystack-pilot/voice/` directory (move Python code here)
5. `mystack-pilot/api/voice_api.py` - FastAPI server
6. `DEPLOYMENT.md` - How to deploy each component
7. `INTEGRATION.md` - How pieces fit together

---

**Bottom Line**: You have three powerful components. Integrate them into a **voice-first AI coding platform** that's unique in the market. Start with the voice tool in src/, then connect the backend.
