# RTMP Integration Plan for Stack 2.9

**Objective**: Replace the legacy MCP‑based tool layer with a native Python‑centric tool system while preserving existing functionality and enabling easier extension.

---

## 1. Architecture Overview (text diagram)
```
+-------------------+          +--------------------+          +-------------------+
|  Stack 2.9 Core   |  <----> |  Tool Registry     |  <----> |  Python Tool Impl |
| (models, prompts) |          | (register/unregister) |      | (functions)      |
+-------------------+          +--------------------+          +-------------------+
         ^                                 ^                       ^
         |                                 |                       |
         |                                 |                       |
         |            +--------------------+-----------------------+
         |            |  Tool Invocation Layer (async)          |
         |            |  - validates input (zod -> pydantic)   |
         |            |  - checks permissions                  |
         |            |  - streams progress & result            |
         |            +----------------------------------------+
         |
         v
+-------------------+          +--------------------+          +-------------------+
|   MCP Bridge      |  (legacy) |  MCP Integration   |  (keep for backward) |
+-------------------+          +--------------------+          +-------------------+
```
*The new system runs entirely in Python, mirroring the API surface of the existing `MCPTool` class but using native classes.*

---

## 2. Implementation Phases

### Phase 0 – Prep & Tool Discovery
1. **Add a `tools/` package** under `stack-2.9/src/` (e.g. `src/tools`).
2. Create a **base `Tool` abstract class** defining:
   - `name`, `description`, `input_schema` (pydantic), `output_schema`.
   - `call(self, **params) -> Any` (may be async).
   - Optional hooks: `validate`, `check_permissions`, `is_destructive`, `summary`.
3. Add a **`tool_registry.py`** singleton with:
   - `register(tool: Tool)`
   - `unregister(name: str)`
   - `get(name: str) -> Tool`
   - `list() -> List[Tool]`
4. Implement **auto‑loader** that scans `src/tools/**` for subclasses of `Tool` and registers them at import time (mirrors RTMP's `loadAgentsDir`).
5. Write **unit tests** for registry behavior.

### Phase 1 – Core Tool System
1. **Define schema handling** using **pydantic** (lightweight, validates JSON schemas). Provide a helper `zod_to_pydantic` if needed for future port‑over.
2. Implement **`ToolInvoker`** class:
   - `async invoke(name, params, context)`
   - Performs input validation, permission check, runs `tool.call()`.
   - Streams progress via async generator (`yield progress`).
3. Add **permission framework** similar to RTMP's `checkPermissions`:
   - Global policy file `tools/permissions.yaml` (allow/deny patterns).
   - `PermissionChecker` reads the policy, supports `always_allow`, `always_deny`, `ask_user`.
4. Create **example native tools** mirroring MCP built‑ins:
   - `ReadFileTool`, `WriteFileTool`, `WebSearchTool`, `RunCommandTool`, `GitTool`.
   - Each lives in its own module under `src/tools/`.
5. Update **Stack entrypoint** (`stack-2.9/stack.py` or CLI) to import the registry and expose the new tool list to the LLM prompt (replace MCP `list_tools`).

### Phase 2 – Migration Layer (MCP Compatibility)
1. Keep the existing **`MCPIntegration`** class but make it a thin wrapper around the new registry:
   - On `register_tool`, forward to `tool_registry.register`.
   - On `call_tool`, forward to `ToolInvoker.invoke`.
2. Add **adapter classes** for each legacy MCP tool that simply subclass the new `Tool` and delegate to the original implementation (e.g., `LegacyReadFileAdapter`). This ensures any existing agent definitions continue to work.
3. Write **migration script** `scripts/migrate_mcp_tools.py` that:
   - Loads all legacy MCP tools (from `RTMP/tools`).
   - Generates stub Python classes in `src/tools/` with matching signatures.
   - Updates `enhancements/collaboration/mcp_integration.py` to use the new registry.
4. Run integration tests to confirm both legacy and native tools are discoverable.

### Phase 3 – Full Cut‑over & Cleanup
1. Update **prompt generation** (`agentToolUtils` etc.) to pull tool definitions from the Python registry instead of MCP metadata.
2. Deprecate the MCP client in `collaboration/mcp_integration.py`:
   - Mark as `deprecated` with warning logs.
   - Remove automatic auto‑registration of MCP tools.
3. Remove the `RTMP/tools` directory from the repo (or archive it under `legacy/`).
4. Extend documentation and add **migration guide** for developers.
5. bump version to `2.9.1`.

---

## 3. File Structure for New Tool System
```
stack-2.9/
├─ src/
│  ├─ tools/
│  │  ├─ __init__.py               # registers all tools on import
│  │  ├─ base.py                    # abstract Tool class
│  │  ├─ registry.py                # singleton registry implementation
│  │  ├─ invoker.py                 # ToolInvoker handling validation & permissions
│  │  ├─ permissions.yaml           # policy file (allow/deny patterns)
│  │  ├─ read_file.py               # native ReadFileTool
│  │  ├─ write_file.py              # native WriteFileTool
│  │  ├─ web_search.py              # native WebSearchTool (uses web_search tool)
│  │  ├─ run_command.py            # native RunCommandTool (subprocess)
│  │  └─ git_tool.py                # native GitTool (uses GitPython or subprocess)
│  └─ enhancements/
│     └─ collaboration/
│        ├─ __init__.py
│        ├─ mcp_integration.py      # thin wrapper -> registry
│        └─ conversation_state.py
├─ docs/
│  └─ rtmp-integration-plan.md      # <-- this file
└─ scripts/
   └─ migrate_mcp_tools.py          # migration helper
```

---

## 4. Migration Path
| Step | Action | Outcome |
|------|--------|---------|
| 1️⃣   | Add native registry & base classes | Core infrastructure ready |
| 2️⃣   | Implement native equivalents of all built‑in MCP tools | Feature parity |
| 3️⃣   | Wrap legacy tools with adapters & register them via the new registry | Zero‑breakage for existing agents |
| 4️⃣   | Switch `list_tools` calls to `registry.list()` | Prompt now reflects native tools |
| 5️⃣   | Deprecate MCP client, remove old `RTMP/tools` folder | Clean codebase |
| 6️⃣   | Update documentation & version bump | Done |

---

## 5. Security & Permissions
- **Schema validation** via pydantic ensures only expected fields reach the implementation.
- **PermissionChecker** reads `tools/permissions.yaml`:
  ```yaml
  always_allow:
    - read_file
    - web_search
  always_deny:
    - run_command: "*"
  ask_user:
    - write_file
    - git_operation
  ```
- Hooks can raise `PermissionDenied` which bubbles up to the LLM as a tool‑use error message.
- All destructive tools (`write_file`, `git_operation`, `run_command` with `sudo`) must be marked `is_destructive=True` to trigger explicit user confirmation.

---

## 6. Documentation & Testing
- Add **docstrings** to each tool class (auto‑generated API reference via `pydoc`).
- Write **pytest** suites covering:
  - Registry CRUD
  - Input validation failures
  - Permission matrix (allow/deny/ask)
  - End‑to‑end invocation through `ToolInvoker`.
- Update `README.md` with a *“Native Tool System”* section describing how to add new tools.

---

## 7. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Regression of existing agents relying on MCP metadata format | Breaks user workflows | Keep adapter layer until next major release; run full suite of agent integration tests. |
| Permission policy mis‑configuration causing silent denial | User confusion | Fail fast with clear error messages; add a startup sanity check that all tools have a permission rule. |
| Performance regression due to Python validation overhead | Slower turn latency | Cache compiled pydantic models; benchmark against MCP’s JSON‑schema validation (expected to be comparable). |

---

## 8. Next Steps
1. Commit the skeleton (`src/tools/` with base classes & registry).
2. Implement `ReadFileTool` and `WriteFileTool` as proof‑of‑concept.
3. Run the migration script to generate adapters for the remaining MCP tools.
4. Update the Stack entrypoint to expose the new tool list.
5. Iterate on tests and documentation.

---

*Prepared by the sub‑agent tasked with RTMP integration.*
