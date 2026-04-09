"""Base tool class for Stack 2.9 tools."""

from __future__ import annotations

import asyncio
import inspect
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class ToolParam:
    """Definition of a tool parameter."""

    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Any = None


@dataclass
class ToolResult:
    """Result returned by a tool execution."""

    success: bool = True
    data: Any = None
    error: str | None = None
    duration_seconds: float = 0.0


class BaseTool(ABC, Generic[TInput, TOutput]):
    """Abstract base class for all Stack 2.9 tools.

    Subclasses must implement:
      - name: str — unique identifier
      - description: str — human-readable description
      - input_schema: dict — JSON schema for parameters
      - execute(input: TInput) -> ToolResult[TOutput]

    Optional overrides:
      - validate_input(input: dict) -> tuple[bool, str | None]
      - is_enabled() -> bool
    """

    name: str = ""
    description: str = ""
    search_hint: str = ""
    max_result_size_chars: int = 100_000

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON schema for tool input parameters."""
        return {}

    @property
    def output_schema(self) -> dict[str, Any]:
        """JSON schema for tool output."""
        return {}

    def is_enabled(self) -> bool:
        """Whether the tool is currently available."""
        return True

    def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate input before execution. Returns (valid, error_message)."""
        return True, None

    @abstractmethod
    def execute(self, input_data: TInput) -> ToolResult[TOutput]:
        """Execute the tool with the given input. Must be implemented by subclasses."""
        ...

    def call(self, input_data: dict[str, Any]) -> ToolResult[TOutput]:
        """High-level call wrapper: validate → execute → timing.
        
        Handles both sync and async execute methods.
        """
        valid, error = self.validate_input(input_data)
        if not valid:
            return ToolResult(success=False, error=error or "Validation failed")

        start = time.perf_counter()
        try:
            result = self.execute(input_data)
            # Handle async execute methods
            if inspect.iscoroutine(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're already in an async context, we can't use run_until_complete
                        # Fall back to creating a new task (for contexts where this matters)
                        # For most cases, creating a new loop in a sync call is fine
                        result = asyncio.run(result)
                    else:
                        result = loop.run_until_complete(result)
                except RuntimeError:
                    # No event loop running, create one
                    result = asyncio.run(result)
            result.duration_seconds = time.perf_counter() - start
            return result
        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                duration_seconds=time.perf_counter() - start,
            )

    def map_result_to_message(self, result: TOutput, tool_use_id: str | None = None) -> str:
        """Format a successful result for display."""
        return str(result)
