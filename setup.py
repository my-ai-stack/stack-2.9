from setuptools import setup, find_packages

setup(
    name="stack-ai",
    version="2.9.0",
    description="Stack AI - Advanced AI tools and enhancements",
    author="Walid Sobhi",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "stack-cli>=2.9.0",
        "gradio>=4.12.0",
        "huggingface_hub>=0.20.0",
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "peft>=0.8.0",
        "accelerate>=0.25.0",
        "bitsandbytes>=0.41.0",
        "datasets>=2.14.0",
        "trl>=0.7.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "openai>=1.3.0",
        "anthropic>=0.18.0",
        "requests>=2.31.0",
        "faiss-cpu>=1.7.0",
        "pyyaml>=6.0",
        "tqdm>=4.66.0",
        "ddgs>=1.0.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black", "isort"],
    },
)
