# Stack 2.9 - Git Push Commands

## Quick Start (one-liner)

```bash
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9

# Initialize git (if not already)
git init
git add .
git commit -m "feat: initial Stack 2.9 release

- Training pipeline with LoRA fine-tuning
- vLLM deployment with Docker
- Voice integration module
- Evaluation suite with benchmarks
- 519 training examples (4k code pairs + 306 advanced patterns)
- Complete documentation and CI/CD"

# Add GitHub remote (HTTPS)
git remote add origin https://github.com/my-ai-stack/stack-2.9.git

# Or use SSH (recommended if you have SSH keys)
# git remote add origin git@github.com:my-ai-stack/stack-2.9.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step-by-Step with Verification

1. **Verify repository integrity first:**
   ```bash
   ./verify_repo.sh
   ```
   
   All ✅ should appear. Fix any ❌ before proceeding.

2. **Initialize and commit:**
   ```bash
   git init
   git add .
   git status  # Review what will be committed
   git commit -m "Your commit message"
   ```

3. **Add remote:**
   ```bash
   # HTTPS
   git remote add origin https://github.com/my-ai-stack/stack-2.9.git
   
   # OR SSH (preferred)
   # git remote add origin git@github.com:my-ai-stack/stack-2.9.git
   ```

4. **Push:**
   ```bash
   git push -u origin main
   ```

5. **Verify on GitHub:**
   Visit: https://github.com/my-ai-stack/stack-2.9

## Important Notes

- **Large files**: Training data (~100MB+) may need Git LFS
  ```bash
  git lfs install
  git lfs track "training-data/**/*.jsonl"
  git add .gitattributes
  ```
- **.env file**: Not committed (in .gitignore) - copy `.env.example` to `.env` locally
- **Model weights**: Not included - you'll train and upload separately to Hugging Face

## After Push

1. Enable GitHub Pages (Settings → Pages)
2. Add repository topics: `ai`, `llm`, `coding-assistant`, `voice`, `open-source`
3. Invite collaborators
4. Create first release (v0.1.0)
5. Submit to OpenRouter with link to repo

---

**Ready?** Run those commands and let me know if anything fails!