#!/usr/bin/env python3
"""
Stack 2.9 - Full Enhanced Chat with All Modules
"""
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import torch
import json
import time

# ============= Load Model =============
model_path = Path("/Users/walidsobhi/stack-2-9-final-model")

print("Loading tokenizer...")
from transformers import PreTrainedTokenizerFast
tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(model_path / "tokenizer.json"))
tokenizer.pad_token = "<|endoftext|>"
tokenizer.eos_token = "<|endoftext|>"

print("Loading config...")
with open(model_path / "config.json") as f:
    config_dict = json.load(f)

print("Loading model...")
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    str(model_path),
    torch_dtype=torch.float16,
    device_map="cpu",
    local_files_only=True
)
tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
tokenizer.pad_token = "<|endoftext|>"

if torch.cuda.is_available():
    model = model.to("cuda")

# ============= Load Enhancement Modules =============
print("\nLoading enhancement modules...")

from enhancements.nlp import IntentDetector, EntityRecognizer
from enhancements.knowledge_graph import RAGEngine
from enhancements.emotional_intelligence import SentimentAnalyzer, EmpathyEngine
from enhancements.collaboration import ConversationStateManager
from enhancements.learning import FeedbackCollector, PerformanceMonitor
from enhancements.technical import DevOpsTools, CodeAnalyzer, DebuggingAssistant

# Initialize all modules
intent_detector = IntentDetector()
entity_recognizer = EntityRecognizer()
rag_engine = RAGEngine()
sentiment_analyzer = SentimentAnalyzer()
empathy_engine = EmpathyEngine()
conv_manager = ConversationStateManager()
feedback_collector = FeedbackCollector()
perf_monitor = PerformanceMonitor()
devops_tools = DevOpsTools()
code_analyzer = CodeAnalyzer()
debugger = DebuggingAssistant()

# Seed RAG
rag_engine.add_document("intro", "Stack 2.9 is an AI coding assistant that helps with programming, debugging, and technical questions.")
rag_engine.add_document("commands", "Commands: quit, exit, feedback, analyze:<code>, debug:<error>")

print("✓ Intent Detection")
print("✓ Entity Recognition")
print("✓ RAG Engine")
print("✓ Sentiment Analysis")
print("✓ Empathy Engine")
print("✓ Conversation Manager")
print("✓ Feedback Collector")
print("✓ Performance Monitor")
print("✓ DevOps Tools")
print("✓ Code Analyzer")
print("✓ Debugging Assistant")

print("\n" + "=" * 50)
print("Stack 2.9 - FULLY ENHANCED")
print("=" * 50)

# ============= Chat Loop =============
conv_manager.create_session()
perf_monitor.increment_session_count()

last_user_input = None
last_response = None

while True:
    try:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        # === Handle Special Commands ===

        # Feedback
        if user_input.lower() == 'feedback':
            print("Rate last response (1-5): ", end="")
            try:
                rating = int(input().strip())
                if 1 <= rating <= 5:
                    feedback_collector.add_feedback("rating", last_user_input or "", last_response or "", rating=rating)
                    print("✓ Thanks for feedback!")
            except:
                print("Invalid rating")
            continue

        # Code Analysis
        if user_input.lower().startswith("analyze:"):
            code = user_input[8:].strip()
            summary = code_analyzer.get_code_summary(code)
            print(f"\n📊 Code Analysis:")
            print(f"   Language: {summary['language']}")
            print(f"   Lines: {summary['complexity']['lines_of_code']}")
            print(f"   Complexity: {summary['complexity']['cyclomatic_complexity']}")
            print(f"   Issues: {summary['issue_count']}")
            print(f"   Maintainability: {summary['maintainability_index']:.1f}/100")
            if summary['suggestions']:
                print(f"   Suggestions: {summary['suggestions']}")
            continue

        # Debug Error
        if user_input.lower().startswith("debug:"):
            error = user_input[6:].strip()
            analysis = debugger.analyze_error(error)
            print(f"\n🔧 Debug Analysis:")
            print(f"   Error: {analysis['error_type']}")
            print(f"   Description: {analysis['description']}")
            print(f"   Common causes: {analysis['common_causes']}")
            for step in analysis['debug_steps'][:4]:
                print(f"   {step}")
            continue

        # Intent Detection
        intent = intent_detector.detect_intent(user_input)

        # Entity Recognition
        entities = entity_recognizer.recognize_entities(user_input)

        # Sentiment Analysis
        sentiment = sentiment_analyzer.analyze_sentiment(user_input)

        # RAG Context
        rag_context = rag_engine.retrieve_as_context(user_input, 300)

        # === Generate Response ===
        start_time = time.time()

        # Build prompt with enhancements
        system = "You are Stack 2.9, an expert AI coding assistant."
        if rag_context:
            system += f"\nContext: {rag_context}"
        if sentiment['sentiment'] == 'negative':
            system += "\nBe empathetic and supportive."
        elif sentiment['sentiment'] == 'positive':
            system += "\nBe enthusiastic and positive."

        prompt = f"{system}\n\nUser: {user_input}\nAssistant:"
        inputs = tokenizer(prompt, return_tensors='pt')
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")

        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            temperature=0.4,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

        response_time = time.time() - start_time

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()

        # Apply empathy if needed
        if sentiment['sentiment'] == 'negative':
            response = empathy_engine.generate_empathetic_response(user_input, response)

        # === Show Info ===
        print(f"\n[Intent: {intent['intent']}]", end="")
        if entities:
            print(f" [Entities: {', '.join([e['type'] for e in entities[:3]])}]", end="")
        if sentiment['sentiment'] != 'neutral':
            print(f" [Mood: {sentiment['sentiment']}]", end="")
        print(f" [{response_time:.2f}s]\n")

        print(f"AI: {response}")

        # === Track ===
        last_user_input = user_input
        last_response = response
        conv_manager.add_message("user", user_input)
        conv_manager.add_message("assistant", response)
        perf_monitor.increment_message_count()
        perf_monitor.record_response_time(response_time)

    except KeyboardInterrupt:
        break

# Stats
stats = perf_monitor.get_session_stats()
print(f"\n{'='*50}")
print(f"Session complete!")
print(f"Messages: {stats['total_messages']}")
print(f"Avg response time: {perf_monitor.get_average_response_time():.2f}s")
print(f"{'='*50}")