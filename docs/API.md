# Stack AI API Reference

This document provides a professional API reference for the `stack_ai` package, detailing the core tool registry, base tool architecture, and specialized enhancement modules.

---

## 🛠️ Tool Architecture

The tool system is designed for extensibility, allowing developers to register custom capabilities that can be invoked by the AI agent.

### `ToolRegistry`
The `ToolRegistry` is a singleton that manages the lifecycle and invocation of tools.

**Class Signature:** `class ToolRegistry`

#### Methods
- `register(tool: BaseTool) -> None`
  - Registers a tool instance. The tool must have a non-empty `name`.
  - **Throws:** `ValueError` if tool name is empty.
- `get(name: str) -> BaseTool | None`
  - Retrieves a registered tool by its unique name.
- `list() -> list[str]`
  - Returns a list of all registered tool names.
- `list_tools() -> dict[str, dict[str, Any]]`
  - Returns a mapping of tool names to their metadata, including `name`, `description`, and `input_schema`.
- `call(name: str, input_data: dict[str, Any]) -> Any`
  - A convenience method that retrieves a tool and executes it in one step.
  - **Throws:** `KeyError` if the tool is not found.
- `unregister(name: str) -> bool`
  - Removes a tool from the registry. Returns `True` if the tool existed.

**Lifecycle:**
1. **Initialization:** The registry is instantiated as a singleton via `get_registry()` or the global `tool_registry` instance.
2. **Registration:** Tools inheriting from `BaseTool` are instantiated and added via `register()`.
3. **Discovery:** The AI agent calls `list_tools()` to understand available capabilities and their required parameters.
4. **Execution:** The agent provides parameters, which are passed to `call()`, triggering the tool's internal validation and execution logic.

---

### `BaseTool`
The abstract base class for all tools in Stack 2.9.

**Class Signature:** `class BaseTool(ABC, Generic[TInput, TOutput])`

#### Required Implementation
- `name: str`: Unique identifier for the tool.
- `description: str`: Human-readable description used by the AI for tool selection.
- `execute(self, input_data: TInput) -> ToolResult[TOutput]`: The core logic of the tool. Must return a `ToolResult`.

#### Optional Overrides
- `input_schema: dict`: JSON schema defining the expected input parameters.
- `output_schema: dict`: JSON schema defining the tool's output.
- `validate_input(self, input_data: dict) -> tuple[bool, str | None]`: Validates input before execution.
- `is_enabled() -> bool`: Determines if the tool is currently available.
- `map_result_to_message(self, result: TOutput, tool_use_id: str | None = None) -> str`: Formats the result for display.

#### Helper Methods
- `call(self, input_data: dict[str, Any]) -> ToolResult[TOutput]`
  - The high-level wrapper that orchestrates: `validate_input` $\rightarrow$ `execute` $\rightarrow$ `timing`.
  - Supports both synchronous and asynchronous `execute` methods.

#### Data Structures
- `ToolResult`: Contains `success` (bool), `data` (Any), `error` (str | None), and `duration_seconds` (float).
- `ToolParam`: Defines a parameter with `name`, `description`, `type`, `required`, and `default`.

---

## 🚀 Implementing a Custom Tool

To create a new tool, subclass `BaseTool` and implement the `execute` method.

### Implementation Guide
1. **Define Metadata**: Set the `name` and `description` as class attributes.
2. **Define Schema**: Implement the `input_schema` property to tell the AI what parameters are needed.
3. **Implement Execution**: Override the `execute` method to perform the tool's logic.
4. **Register**: Add the tool instance to the global registry.

**Example:**
```python
from stack_ai.tools.base import BaseTool, ToolResult
from stack_ai.tools.registry import tool_registry

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs basic arithmetic operations"

    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "sub"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            }
        }

    def execute(self, input_data):
        op = input_data.get("operation")
        a, b = input_data.get("a", 0), input_data.get("b", 0)
        result = a + b if op == "add" else a - b
        return ToolResult(data=result)

tool_registry.register(CalculatorTool())
```

---

## 🧠 Enhancement Modules

Stack 2.9 includes specialized modules to enhance the AI's cognitive capabilities.

### 🎭 Emotional Intelligence (EI)
Focused on understanding and responding to user emotions.

#### `SentimentAnalyzer`
Analyzes text for sentiment and specific emotional markers.
- `analyze_sentiment(text: str, return_scores: bool = True) -> Dict`: Returns sentiment (positive/negative/neutral), confidence score, and detected emotions.
- `detect_emotions(text: str) -> List[Dict]`: Returns the top 3 detected emotions and their scores.
- `get_tone_adjustment(text: str) -> str`: Recommends a tone (e.g., "empathetic", "supportive") based on the user's state.

#### `EmpathyEngine`
Generates empathetic responses and adjusts tone.
- `generate_empathetic_response(user_message: str, base_response: str) -> str`: Wraps a base response with empathetic prefixes and reassurance.
- `get_response_tone(user_message: str) -> Dict`: Provides a full analysis of the recommended tone and user emotional state.

### 🕸️ Knowledge Graph
Provides structured memory and relationship tracking.

#### `KnowledgeGraph`
A graph-based representation of entities and their relationships using `networkx`.
- `add_entity(entity_id, entity_type, properties=None)`: Adds a node to the graph.
- `add_relationship(source_id, target_id, relationship_type, properties=None)`: Creates a directed edge between entities.
- `find_similar_entities(entity_id, max_results=5)`: Uses Jaccard-like similarity based on common neighbors to find related entities.
- `get_subgraph(entity_ids, depth=1)`: Extracts a local neighborhood around specific entities for context.

#### `RAGEngine`
Retrieval-Augmented Generation for accessing unstructured document data.
- `add_document(doc_id, content, metadata=None, embedding=None)`: Indexes a document.
- `retrieve(query, top_k=None, use_keyword_index=True)`: Returns the most relevant documents using a hybrid of keyword and vector similarity.
- `retrieve_as_context(query, max_context_length=1000)`: Formats retrieved documents into a single string for LLM context windows.

### ✍️ NLP Modules
Advanced Natural Language Processing for text understanding.

#### `ContextualEmbedder`
Generates high-dimensional vectors using BERT/RoBERTa.
- `get_embedding(text, layer=-1)`: Returns the mean of the last hidden state for a given text.
- `compute_similarity(text1, text2, method="cosine")`: Calculates the similarity between two texts.

#### `EntityRecognizer`
Extracts named entities using a hybrid of Transformers and Regex.
- `recognize_entities(text)`: Extracts a list of entities (PERSON, ORGANIZATION, LOCATION, EMAIL, etc.) with their positions and scores.
- `extract_entities_by_type(text, entity_type)`: Filters entities by a specific type.

#### `IntentDetector`
Maps user input to specific goal-oriented intents.
- `detect_intent(text)`: Returns the primary intent (e.g., `code_request`, `debug_request`, `explain`) and confidence score.
- `detect_multiple_intents(text)`: Identifies all intents that exceed the confidence threshold.
