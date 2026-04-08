# Stack 2.9 HuggingFace Space
# Fine-tuned code assistant powered by Qwen2.5-Coder-1.5B

app = gr.Blocks(title="Stack 2.9")

with app:
    gr.Markdown("""
    # 💻 Stack 2.9 - Code Assistant
    Fine-tuned on Stack Overflow data · 1.5B parameters · Qwen2.5-Coder base
    
    ---
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Stack 2.9", height=500)
            msg = gr.Textbox(
                label="Your message",
                placeholder="Ask me to write or explain code...",
                lines=3
            )
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear")
        
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            temperature = gr.Slider(0.1, 1.5, 0.7, label="Temperature")
            max_tokens = gr.Slider(64, 2048, 1024, step=64, label="Max tokens")
            system_prompt = gr.Textbox(
                value="You are Stack 2.9, a helpful coding assistant.",
                label="System prompt",
                lines=2
            )
            gr.Markdown("### 📊 Model Info")
            gr.Markdown("""
            - **Base**: Qwen2.5-Coder-1.5B
            - **Fine-tuned**: Stack Overflow Q&A
            - **Context**: 32K tokens
            - **License**: Apache 2.0
            """)

    def respond(message, history, system, temp, tokens):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        model_name = "my-ai-stack/Stack-2-9-finetuned"
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=tokens, temperature=temp, do_sample=True, pad_token_id=tokenizer.pad_token_id)
        response = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
        return response

    submit_btn.click(respond, inputs=[msg, chatbot, system_prompt, temperature, max_tokens], outputs=chatbot)
    msg.submit(respond, inputs=[msg, chatbot, system_prompt, temperature, max_tokens], outputs=chatbot)
    clear_btn.click(lambda: None, outputs=chatbot)

app.launch()