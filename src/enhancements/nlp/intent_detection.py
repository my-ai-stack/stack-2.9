"""
Intent Detection Module

Detects user intent from text for better conversational understanding.
"""

from typing import List, Dict, Optional, Any
import re
from collections import defaultdict


class IntentDetector:
    """Detect user intent from natural language input."""

    # Common intents with associated keywords and patterns
    DEFAULT_INTENTS = {
        "greeting": {
            "keywords": ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"],
            "patterns": [r"^hi(?: there)?", r"^hello", r"^hey", r"^good (?:morning|afternoon|evening)"],
        },
        "farewell": {
            "keywords": ["bye", "goodbye", "see you", "later", "quit", "exit", "good night"],
            "patterns": [r"^(?:good )?bye", r"see you", r"(?:good )?night", r"^later"],
        },
        "help": {
            "keywords": ["help", "assist", "support", "can you", "how do i", "how to", "what can you do"],
            "patterns": [r"^help", r"can you .*(?:help|do)", r"how (?:do|can) i", r"what can you"],
        },
        "question": {
            "keywords": ["what", "how", "why", "when", "where", "who", "which", "?"],
            "patterns": [r"^(?:what|how|why|when|where|who|which)", r"\?$"],
        },
        "code_request": {
            "keywords": ["write", "code", "create", "implement", "function", "class", "script", "program"],
            "patterns": [r"(?:write|create|implement|generate) .*(?:code|function|class|script)"],
        },
        "debug_request": {
            "keywords": ["debug", "fix", "error", "bug", "issue", "problem", "broken", "not working", "crash"],
            "patterns": [r"(?:debug|fix) .*(?:error|bug|issue)", r"(?:there(?:'s| is) an? )?error", r"(?:not working|crash|broken)"],
        },
        "refactor": {
            "keywords": ["refactor", "improve", "optimize", "clean", "simplify", "restructure"],
            "patterns": [r"(?:refactor|improve|optimize|clean(?: up)?)"],
        },
        "explain": {
            "keywords": ["explain", "describe", "tell me about", "what is", "how does", "what does"],
            "patterns": [r"(?:explain|describe|tell me about|what is|how does)"],
        },
        "search": {
            "keywords": ["search", "find", "look up", "google", "web search"],
            "patterns": [r"(?:search|find|look up)"],
        },
        "analysis": {
            "keywords": ["analyze", "review", "check", "test", "evaluate", "compare"],
            "patterns": [r"(?:analyze|review|check|test|evaluate|compare)"],
        },
        "tool_use": {
            "keywords": ["use tool", "run command", "execute", "shell", "bash"],
            "patterns": [r"(?:run|execute) .*(?:command|shell)", r"bash", r"shell"],
        },
        "learning": {
            "keywords": ["learn", "teach me", "train", "understand", "study"],
            "patterns": [r"(?:learn|teach me|train)"],
        },
        "feedback": {
            "keywords": ["feedback", "rating", "opinion", "suggest", "improve", "better"],
            "patterns": [r"(?:feedback|rating|opinion|suggest|improve)"],
        },
        "clarification": {
            "keywords": ["clarify", "repeat", "restate", "what do you mean", "explain more"],
            "patterns": [r"(?:clarify|repeat|what do you mean)", r"(?:could you|can you) (?:repeat|clarify)"],
        },
    }

    def __init__(
        self,
        custom_intents: Optional[Dict[str, Dict[str, List[str]]]] = None,
        confidence_threshold: float = 0.3,
    ):
        """
        Initialize the intent detector.

        Args:
            custom_intents: Custom intent definitions
            confidence_threshold: Minimum confidence for intent detection
        """
        self.intents = self.DEFAULT_INTENTS.copy()
        if custom_intents:
            self.intents.update(custom_intents)
        self.confidence_threshold = confidence_threshold
        self._keyword_cache: Dict[str, float] = {}

    def detect_intent(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary intent from text.

        Args:
            text: Input text

        Returns:
            Dictionary with 'intent', 'confidence', and 'alternatives'
        """
        text_lower = text.lower().strip()

        intent_scores = defaultdict(float)

        # Check each intent
        for intent_name, intent_config in self.intents.items():
            # Check keywords
            for keyword in intent_config.get("keywords", []):
                if keyword.lower() in text_lower:
                    intent_scores[intent_name] += 1.0

            # Check patterns
            for pattern in intent_config.get("patterns", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    intent_scores[intent_name] += 1.5

        # Normalize scores
        if intent_scores:
            max_score = max(intent_scores.values())
            if max_score > 0:
                for intent in intent_scores:
                    intent_scores[intent] /= max_score

        # Sort by score
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: -x[1]
        )

        if not sorted_intents or sorted_intents[0][1] < self.confidence_threshold:
            return {
                "intent": "general",
                "confidence": 1.0,
                "alternatives": [],
            }

        primary_intent = sorted_intents[0][0]
        alternatives = [
            {"intent": intent, "confidence": score}
            for intent, score in sorted_intents[1:4]
            if score >= self.confidence_threshold
        ]

        return {
            "intent": primary_intent,
            "confidence": sorted_intents[0][1],
            "alternatives": alternatives,
        }

    def detect_multiple_intents(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect multiple intents from text.

        Args:
            text: Input text

        Returns:
            List of intent dictionaries with scores
        """
        text_lower = text.lower().strip()
        intent_scores = defaultdict(float)

        for intent_name, intent_config in self.intents.items():
            for keyword in intent_config.get("keywords", []):
                if keyword.lower() in text_lower:
                    intent_scores[intent_name] += 1.0

            for pattern in intent_config.get("patterns", []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    intent_scores[intent_name] += 1.5

        # Return all intents above threshold
        results = [
            {"intent": intent, "confidence": score}
            for intent, score in intent_scores.items()
            if score >= self.confidence_threshold
        ]

        if not results:
            return [{"intent": "general", "confidence": 1.0}]

        return sorted(results, key=lambda x: -x["confidence"])

    def add_intent(
        self,
        intent_name: str,
        keywords: List[str],
        patterns: Optional[List[str]] = None,
    ) -> None:
        """
        Add a custom intent.

        Args:
            intent_name: Name of the intent
            keywords: List of keywords
            patterns: List of regex patterns
        """
        self.intents[intent_name] = {
            "keywords": keywords,
            "patterns": patterns or [],
        }

    def get_intent_description(self, intent: str) -> str:
        """Get a description of what an intent means."""
        descriptions = {
            "greeting": "User is greeting the assistant",
            "farewell": "User is saying goodbye",
            "help": "User is asking for help or assistance",
            "question": "User is asking a question",
            "code_request": "User wants code to be written",
            "debug_request": "User needs help debugging an issue",
            "refactor": "User wants code to be improved or refactored",
            "explain": "User wants an explanation of something",
            "search": "User wants to search for information",
            "analysis": "User wants code or content analyzed",
            "tool_use": "User wants to execute a command or tool",
            "learning": "User wants to learn something",
            "feedback": "User is providing feedback",
            "clarification": "User wants clarification on something",
            "general": "General conversational input",
        }
        return descriptions.get(intent, f"Intent: {intent}")

    def __repr__(self) -> str:
        return f"IntentDetector(num_intents={len(self.intents)}, threshold={self.confidence_threshold})"