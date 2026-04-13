# claude-delegate-skill

A bounded "specialist lane" skill. The orchestrator (Codex main) **spawns a fresh subagent**, and that subagent runs a single `claude_bridge.py` call against the local Claude Code CLI, returning schema-validated JSON.

Three modes: `review`, `adversarial-review`, `implementation-plan`.

Use it when you want a second opinion, a red-team pass, or an alternative plan — not for ordinary edits. Always route through a subagent; do not call the bridge script from the main thread.

## Composition

The skill is designed to slot into multi-reviewer fan-outs. Example:

> "Review this PR. Spawn 3 subagents for different angles; one should follow `$claude-delegate-skill` for a Claude-backed pass."

Each subagent reads `SKILL.md`, performs one delegation, and reports back. Parallel spawns keep reviewer contexts isolated from each other and from the orchestrator.

## Setup

- `claude` CLI installed on `PATH` and logged in (`claude auth status` → `loggedIn: true`)
- `python3` available (the bridge script is invoked via `python3`)
- Drop this directory into your skills folder (e.g. `~/.codex/skills/claude-delegate-skill` or `~/.claude/skills/claude-delegate-skill`)
- Run `./scripts/doctor.sh` once to verify CLI, auth, and a JSON smoke test

## Usage

- Entry point: [`SKILL.md`](./SKILL.md)
- Wrapper: [`scripts/claude_bridge.py`](./scripts/claude_bridge.py) (`run` / `doctor` subcommands)

A single run typically takes several minutes (5+ min is normal, up to 15 min is possible). When invoking via Bash, use a timeout of at least 15 minutes.
