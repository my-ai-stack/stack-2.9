# Benchmark Badges for README.md

Copy these badge markdown lines into your main README to display evaluation scores.

## HumanEval Pass@k Badges

Replace the static badges with dynamic ones after evaluation completes.

### Template (placeholders):

```markdown
[![HumanEval Pass@1](https://img.shields.io/static/v1?label=HumanEval&message=Pass%401&color=yellow)](https://github.com/your-repo)
[![HumanEval Pass@10](https://img.shields.io/static/v1?label=HumanEval&message=Pass%4010&color=yellow)](https://github.com/your-repo)
[![HumanEval Pass@100](https://img.shields.io/static/v1?label=HumanEval&message=Pass%40100&color=orange)](https://github.com/your-repo)
```

### Example with actual scores (update after running evaluation):

If you get 82% Pass@1:
```markdown
[![HumanEval Pass@1: 82%](https://img.shields.io/badge/HumanEval-Pass%401-82%25-yellow?logo=python)](https://github.com/your-repo)
[![HumanEval Pass@10: 89%](https://img.shields.io/badge/HumanEval-Pass%4010-89%25-yellow?logo=python)](https://github.com/your-repo)
[![HumanEval Pass@100: 92%](https://img.shields.io/badge/HumanEval-Pass%40100-92%25-orange?logo=python)](https://github.com/your-repo)
```

## MBPP Badges

### Template:
```markdown
[![MBPP Pass@1](https://img.shields.io/static/v1?label=MBPP&message=Pass%401&color=blue)](https://github.com/your-repo)
[![MBPP Pass@10](https://img.shields.io/static/v1?label=MBPP&message=Pass%4010&color=blue)](https://github.com/your-repo)
[![MBPP Pass@100](https://img.shields.io/static/v1?label=MBPP&message=Pass%40100&color=blue)](https://github.com/your-repo)
```

### Example with actual scores:
If you get 80% Pass@1:
```markdown
[![MBPP Pass@1: 80%](https://img.shields.io/badge/MBPP-Pass%401-80%25-blue?logo=python)](https://github.com/your-repo)
[![MBPP Pass@10: 85%](https://img.shields.io/badge/MBPP-Pass%4010-85%25-blue?logo=python)](https://github.com/your-repo)
[![MBPP Pass@100: 88%](https://img.shields.io/badge/MBPP-Pass%40100-88%25-blue?logo=python)](https://github.com/your-repo)
```

## Auto-generating Badges

After running evaluation, use the scores from the generated summary files:

- `results/humaneval_summary.json` → contains `pass@k` value for HumanEval
- `results/mbpp_summary.json` → contains `pass@k` value for MBPP

You can create a script to auto-update README.md with the latest scores.

## Combined Badges

```markdown
[![HumanEval](https://img.shields.io/badge/HumanEval-164%20problems-green)](https://github.com/your-repo)
[![MBPP](https://img.shields.io/badge/MBPP-500%20problems-green)](https://github.com/your-repo)
```
