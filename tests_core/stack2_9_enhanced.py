#!/usr/bin/env python3
"""
Stack 2.9 - Full Enhanced Version with All Features
"""
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import torch

# Enhancement modules
from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer, EmpathyEngine
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import FeedbackCollector, PerformanceMonitor
from enhancements.technical import DevOpsTools, CodeAnalyzer, DebuggingAssistant
from enhancements import get_config

# Load model
model_path = Path("/Users/walidsobhi/stack-2-9-final-model")

print("=" * 50)
print("Stack 2.9 - Enhanced Edition")
print("=" * 50)

# Initialize enhancement modules
print("\n[1/4] Loading NLP modules...")
intent_detector = IntentDetector()
entity_recognizer = EntityRecognizer()
print("  ✓ Intent Detection")
print("  ✓ Entity Recognition")

print("\n[2/4] Loading Knowledge Graph...")
rag_engine = RAGEngine()
rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant trained on code and technical content")
rag_engine.add_document("commands", "Commands: help, debug, analyze, devops, quit")
print("  ✓ RAG Engine")

print("\n[3/4] Loading Emotional Intelligence...")
sentiment_analyzer = SentimentAnalyzer()
empathy_engine = EmpathyEngine()
print("  ✓ Sentiment Analysis")
print("  ✓ Empathy Engine")

print("\n[4/4] Loading Technical Capabilities...")
devops_tools = DevOpsTools()
code_analyzer = CodeAnalyzer()
debugging_assistant = DebuggingAssistant()
print("  ✓ DevOps Tools")
print("  ✓ Code Analyzer")
print("  ✓ Debugging Assistant")

# Other systems
conversation_manager = ConversationStateManager()
feedback_collector = FeedbackCollector()
performance_monitor = PerformanceMonitor()

print("\n" + "=" * 50)

# Load model
print("\nLoading model...")
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    str(model_path),
    torch_dtype=torch.float16,
    device_map="cpu",
    local_files_only=True
)

tokenizer = AutoTokenizer.from_pretrained(
    str(model_path),
    local_files_only=True
)
tokenizer.pad_token = "<|endoftext|>"

if torch.cuda.is_available():
    model = model.to("cuda")

# Setup session
conversation_manager.create_session()
performance_monitor.increment_session_count()

print("✓ Stack 2.9 Ready!\n")

# Demo function
def demo_feature(name, func):
    print(f"\n--- {name} ---")
    try:
        result = func()
        print(result)
    except Exception as e:
        print(f"Error: {e}")

# Interactive chat
while True:
    try:
        print("\n" + "=" * 40)
        print("Commands: test, debug <error>, analyze <code>, devops, quit")
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        # Handle special commands
        if user_input.lower() == 'test':
            print("\n=== TESTING ALL ENHANCEMENTS ===\n")

            # Test Intent Detection
            demo_feature("Intent Detection", lambda: intent_detector.detect_intent("Write a function to calculate fibonacci"))

            # Test Entity Recognition
            demo_feature("Entity Recognition", lambda: entity_recognizer.recognize_entities("My email is test@example.com"))

            # Test Sentiment
            demo_feature("Sentiment Analysis", lambda: sentiment_analyzer.analyze_sentiment("I'm frustrated with this bug"))

            # Test RAG
            demo_feature("RAG Context", lambda: rag_engine.retrieve_as_context("what can you do", 200))

            # Test Code Analysis
            sample_code = "def hello():\n    print('hello')\n    x = 1"
            demo_feature("Code Analysis", lambda: code_analyzer.get_code_summary(sample_code))

            # Test DevOps
            demo_feature("DevOps - Docker", lambda: devops_tools.generate_dockerfile("python", "3.11"))

            # Test Debugging
            demo_feature("Debugging", lambda: debugging_assistant.analyze_error("NameError: name 'x' is not defined"))

            print("\n=== ALL TESTS COMPLETE ===")
            continue

        # Debug command
        if user_input.lower().startswith("debug "):
            error = user_input[6:]
            analysis = debugging_assistant.analyze_error(error)
            print(f"\nError Type: {analysis['error_type']}")
            print(f"Description: {analysis['description']}")
            print("\nCommon Causes:")
            for cause in analysis['common_causes']:
                print(f"  - {cause}")
            print("\nSuggested Fixes:")
            for fix in analysis['suggested_fixes']:
                print(f"  - {fix}")
            continue

        # Analyze code command
        if user_input.lower().startswith("analyze "):
            code = user_input[8:]
            summary = code_analyzer.get_code_summary(code)
            print(f"\nLanguage: {summary['language']}")
            print(f"Lines of Code: {summary['complexity']['lines_of_code']}")
            print(f"Complexity: {summary['complexity']['cyclomatic_complexity']}")
            print(f"Maintainability: {summary['maintainability_index']:.1f}/100")
            if summary['issues']:
                print("Issues:")
                for issue in summary['issues'][:3]:
                    print(f"  - {issue['type']}: {issue['message']}")
            continue

        # DevOps command
        if user_input.lower().startswith("devops"):
            parts = user_input.split()
            if len(parts) > 1:
                template = devops_tools.generate_dockerfile(parts[1] if len(parts) > 1 else "python")
            else:
                template = devops_tools.generate_dockerfile()
            print(f"\n{template}")
            continue

        # Normal chat with enhancements
        # 1. Detect intent
        intent = intent_detector.detect_intent(user_input)

        # 2. Detect sentiment
        sentiment = sentiment_analyzer.analyze_sentiment(user_input)

        # 3. Get RAG context
        rag_context = rag_engine.retrieve_as_context(user_input, 300)

        # Build prompt with enhancements
        prompt_parts = ["You are Stack 2.9, an expert AI coding assistant."]

        if rag_context:
            prompt_parts.append(f"Context: {rag_context}")

        # Add emotional tone guidance
        if sentiment['sentiment'] == 'negative':
            prompt_parts.append("Be empathetic and understanding.")
        elif sentiment['sentiment'] == 'positive':
            prompt_parts.append("Be enthusiastic and helpful.")

        prompt_parts.append(f"\n\nUser: {user_input}\nAssistant:")

        full_prompt = "\n".join(prompt_parts)

        # Generate
        inputs = tokenizer(full_prompt, return_tensors='pt')
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.4,
            pad_token_id=tokenizer.eos_token_id
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        # Apply empathy if needed
        if sentiment['sentiment'] == 'negative':
            response = empathy_engine.generate_empathetic_response(user_input, response)

        print(f"\n[Intent: {intent['intent']}] [Sentiment: {sentiment['sentiment']}]")
        print(f"AI: {response}")

        # Track metrics
        performance_monitor.increment_message_count()

    except KeyboardInterrupt:
        break

# Show stats
stats = performance_monitor.get_session_stats()
print(f"\n\nSession Stats: {stats['total_messages']} messages")
print("Stack 2.9 Enhanced - Session Complete!")