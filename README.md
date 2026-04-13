# claude-delegate

A bounded "specialist lane" skill that delegates a single task to the local Claude Code CLI and returns schema-validated JSON.

Three modes: `review`, `adversarial-review`, `implementation-plan`.

Use it when you want a second opinion, a red-team pass, or an alternative plan — not for ordinary edits.

- Entry point: [`SKILL.md`](./SKILL.md)
- Wrapper: [`scripts/claude_bridge.py`](./scripts/claude_bridge.py) (`run` / `doctor` subcommands)
- Health check: `./scripts/doctor.sh`

A single run typically takes several minutes (5+ min is normal). When invoking via Bash, use a timeout of at least 10 minutes.
