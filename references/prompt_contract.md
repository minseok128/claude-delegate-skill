# Prompt Contract

Write a temporary prompt file before invoking `claude_bridge.py run`.

Use this layout:

```md
# Claude Delegate Request

Mode: <review|adversarial-review|implementation-plan>
Goal: <one sentence>
Repository: <repo name or path>

## Constraints
- Summarize only the AGENTS.md rules that matter for this task.
- Mention forbidden actions or sensitive paths if relevant.
- State whether Claude must remain read-only.

## Context
- Target files: <path list>
- Diff summary: <short summary or diff excerpt>
- Errors/tests: <only if relevant>
- Prior attempts: <only if relevant>

## Requested Output
Return JSON that matches the provided schema exactly.
Keep findings concrete and action-oriented.
Do not modify files.
```

Keep the prompt compact. Prefer excerpts and summaries over full file dumps.
