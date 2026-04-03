# 🚀 Pushing to GitHub (my-ai-stack/stack-2.9)

This guide walks through creating the repository on GitHub and pushing the local code.

## Prerequisites

- You have a GitHub account with admin access to the **my-ai-stack** organization
- Git is installed locally
- You have configured SSH or HTTPS credentials for GitHub

## Steps

### 1. Create the Repository on GitHub

**Option A: Via Web Interface**
1. Go to https://github.com/organizations/my-ai-stack/repositories/new
2. Repository name: `stack-2.9`
3. Description: "Open-source voice-enabled AI coding assistant based on Qwen2.5-Coder-32B"
4. Choose:
   - ☑ Public (recommended for open source)
   - ☐ Private (if you want to restrict access)
   - ☑ Initialize with a README? **NO** (we already have one)
5. Click "Create repository"

**Option B: Via GitHub CLI** (if you have `gh` installed)
```bash
gh repo create my-ai-stack/stack-2.9 \
  --public \
  --description "Open-source voice-enabled AI coding assistant based on Qwen2.5-Coder-32B" \
  --source . \
  --remote origin
```

### 2. Connect Local Repository to GitHub

From the `stack-2.9` directory:

```bash
cd /Users/walidsobhi/.openclaw/workspace/stack-2.9

# If you used Option B above, this is already done. For Option A:
git init
git add .
git commit -m "feat: initial Stack 2.9 release

- Training pipeline with LoRA fine-tuning
- vLLM deployment with Docker
- Voice integration module
- Evaluation suite with benchmarks
- 519 training examples with advanced patterns
- Complete documentation and CI/CD"

# Add GitHub remote (replace with your actual repo URL)
git remote add origin https://github.com/my-ai-stack/stack-2.9.git

# Or via SSH (if you have SSH keys set up):
# git remote add origin git@github.com:my-ai-stack/stack-2.9.git
```

### 3. Push to GitHub

```bash
# Push main branch
git branch -M main
git push -u origin main

# Push all tags (if any)
git push --tags
```

### 4. Verify

Visit: https://github.com/my-ai-stack/stack-2.9

You should see all files:
- README.md with badges
- All subdirectories (training, deploy, voice, docs, eval)
- Documentation
- Makefile for easy builds

### 5. Post-Push Setup (Optional but Recommended)

#### Enable GitHub Pages (for docs)
1. Go to repo Settings → Pages
2. Source: "GitHub Actions" or "main branch /docs folder"
3. Save → docs will be at https://my-ai-stack.github.io/stack-2.9/

#### Add Repository Topics
Add these topics to improve discoverability:
- `ai`, `llm`, `coding-assistant`, `voice`, `open-source`, `qwen`, `vllm`, `fine-tuning`, `training-data`, `huggingface`, `openrouter`

#### Configure Repository Features
- Settings → Features → enable Discussions, Projects, Wiki as needed

#### Set Up GitHub Actions Secrets (if needed)
If CI/CD needs additional secrets (like Hugging Face token):
1. Settings → Secrets and variables → Actions
2. Add:
   - `HF_TOKEN` - Hugging Face API token
   - `OPENROUTER_API_KEY` - OpenRouter API key (for testing)

#### Add Collaborators
Invite team members:
- Settings → Collaborators and teams → Add people

### 6. Update OpenRouter Submission

In `stack-2.9-docs/OPENROUTER_SUBMISSION.md`, update:
- Repository URL: `https://github.com/my-ai-stack/stack-2.9`
- Date of submission
- Point of contact

Email the submission to OpenRouter or submit via their form.

### 7. Share with Community

Once pushed:
- Announce on Discord/Twitter/LinkedIn
- Submit to Hacker News, r/MachineLearning, etc.
- Engage with Hugging Face community
- Reach out to OpenRouter for listing

## Troubleshooting

**Error: remote: Repository not found.**
- Check you have permission to create repos in **my-ai-stack** org
- Verify you're using the correct org name
- Try SSH instead of HTTPS

**Error: remote: Permission to my-ai-stack/stack-2.9.git denied**
- You need admin access to the org
- Contact org admin to grant permissions

**Large files failing to push**
- Training data might be too large (~100MB+)
- Consider using Git LFS for large files:
  ```bash
  git lfs install
  git lfs track "training-data/advanced-patterns/*.jsonl"
  git add .gitattributes
  ```

**Hitting GitHub rate limits**
- Use SSH instead of HTTPS
- Authenticate properly with gh CLI

## Next Steps After Push

1. ✅ Create GitHub repo and push code
2. ✅ Enable issues, discussions, wiki
3. ▶️  Start training on GPU (if available)
4. ▶️  Push trained model to Hugging Face
5. ▶️  Submit to OpenRouter
6. ▶️  Create community (Discord)
7. ▶️  Iterate on training data and evaluation

---

**Ready?** Run the git commands above and let me know if you hit any issues!