---
name: claude-delegate-skill
description: Spawn a fresh subagent that performs exactly one bounded Claude Code CLI delegation and returns a concise report. Use when the user explicitly asks for Claude, wants a second opinion, requests adversarial review, asks for an alternative implementation plan, or orchestrates a multi-reviewer fan-out with one slot powered by Claude. The orchestrator must not call `claude_bridge.py` from the main thread — always delegate the run to a subagent that follows this skill. Not for ordinary edits or tasks Codex can complete directly.
---

# Claude Delegate Skill

You are a subagent spawned by the orchestrator (Codex main) to run exactly one Claude delegation — a `review`, `adversarial-review`, or `implementation-plan`. Complete the delegation, return a concise report to the orchestrator, and stop. Your scope is this single call; the orchestrator remains the primary executor and verifier.

## Expected Runtime

A single `claude_bridge.py run` invocation routinely takes **several minutes**, **5+ minutes is normal**, and **runs of up to 15 minutes are possible** for `adversarial-review` or `implementation-plan` over a non-trivial diff. This is expected — Claude is doing multi-turn reasoning and tool use against the repo.

When running `claude_bridge.py`:

- **Wait calmly.** Do not assume the call is hung just because it has not returned in 30–60 seconds. There is no progress output until the run finishes.
- **Set a generous Bash timeout.** When you call `./scripts/claude_bridge.py run` from a Bash tool, pass an explicit timeout of **at least 900000 ms (15 minutes)**. The default 2-minute timeout will almost always cut a real run short. If your harness caps Bash at 10 minutes, run the bridge in the background instead of waiting inline.
- **Do not kill and retry on a hunch.** If the run is still going, it is still working. Only abort if you have concrete evidence of a stuck process (e.g., zero CPU for minutes, or a known auth/CLI failure visible in another channel).
- **Run `doctor.sh` only when there is a real signal of trouble** (auth error, malformed JSON, CLI flag error). Do not pre-emptively re-run it because the main call "feels slow."

## Workflow

1. Read the active task, the relevant `AGENTS.md` instructions, and only the local context Claude actually needs.
2. Pick exactly one mode. Read [references/modes.md](./references/modes.md) if the correct mode is not obvious.
3. Prepare a temporary prompt file that follows [references/prompt_contract.md](./references/prompt_contract.md).
4. Run `./scripts/doctor.sh` before the first use in a session, or after any Claude CLI failure.
5. Call `./scripts/claude_bridge.py run` with:
   - `--mode review` or `--mode adversarial-review` plus `--settings ./scripts/settings/review.json`
   - `--mode implementation-plan` plus `--settings ./scripts/settings/plan.json`
   - the matching schema from `./scripts/schemas/`
   - `--session ephemeral` unless the user explicitly asks to keep a named Claude session
   - default budgets and turn limits are already generous; only override when the task clearly needs more or less
   - **Bash timeout ≥ 900000 ms (15 min).** Expect the call to run for minutes; see "Expected Runtime" above.
6. Read the output JSON file and treat it as advisory input, not as final truth.
7. Report back to the orchestrator in this order:
   - one-paragraph summary
   - key findings or risks
   - recommended next action for the orchestrator

## Operating Rules

- Keep the delegated task narrow. Delegate review, adversarial review, or implementation planning only.
- Keep the context bundle small. Prefer target files, current diff, failing tests, and a short repository note over whole-file dumps.
- Keep Claude read-only by default. Use `plan` permission mode, `--no-session-persistence`, and restricted tools unless the user explicitly requests a different contract.
- Keep repository-specific build, test, and policy rules in `AGENTS.md`. Summarize only the parts Claude needs inside the prompt file.
- Reject automatic escalation. If Claude suggests file edits, include them in your report; the orchestrator applies writes, not you.
- Re-run `doctor` after authentication errors, CLI flag errors, or malformed JSON output.

## Prompt Construction

Write the temporary prompt file in imperative form and include only:

- mode and goal
- relevant repository constraints from `AGENTS.md`
- target files or diff excerpts
- failing tests or error output, if relevant
- explicit instruction to return JSON that matches the provided schema

Do not include hidden conclusions like "the bug is in X" unless the user already supplied that framing.

## Output Handling

- `claude_bridge.py run` writes the normalized structured output to the `--output` path.
- On success, read that file and synthesize the result for the orchestrator.
- On failure, inspect the wrapper stderr/stdout summary first, then retry with:
  - tighter context
  - a larger `--max-turns`
  - a slightly larger `--max-budget-usd`
  - `./scripts/doctor.sh` if the failure looks environmental

## Resources

- [references/modes.md](./references/modes.md): mode selection and expected outputs
- [references/prompt_contract.md](./references/prompt_contract.md): temporary prompt-file contract
- `scripts/claude_bridge.py`: bounded Claude CLI wrapper
- `scripts/doctor.sh`: quick health check entrypoint
- `scripts/settings/*.json`: Claude permission profiles
- `scripts/schemas/*.json`: JSON output contracts
