# claude-delegate

A bounded "specialist lane" skill that delegates a single task to the local Claude Code CLI and returns schema-validated JSON.

Three modes: `review`, `adversarial-review`, `implementation-plan`.

Use it when you want a second opinion, a red-team pass, or an alternative plan — not for ordinary edits.

## Setup

- `claude` CLI installed on `PATH` and logged in (`claude auth status` → `loggedIn: true`)
- `python3` available (the bridge script is invoked via `python3`)
- Drop this directory into your skills folder (e.g. `~/.codex/skills/claude-delegate` or `~/.claude/skills/claude-delegate`)
- Run `./scripts/doctor.sh` once to verify CLI, auth, and a JSON smoke test

## Usage

- Entry point: [`SKILL.md`](./SKILL.md)
- Wrapper: [`scripts/claude_bridge.py`](./scripts/claude_bridge.py) (`run` / `doctor` subcommands)

A single run typically takes several minutes (5+ min is normal, up to 15 min is possible). When invoking via Bash, use a timeout of at least 15 minutes.
