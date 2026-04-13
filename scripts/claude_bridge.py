#!/usr/bin/env python3
"""Bounded Claude Code CLI wrapper for the claude-delegate-skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = SKILL_DIR / "scripts" / "settings"
SCHEMAS_DIR = SKILL_DIR / "scripts" / "schemas"

DEFAULTS = {
    "review": {
        "schema": SCHEMAS_DIR / "review.json",
        "settings": SETTINGS_DIR / "review.json",
        "max_turns": 100,
        "max_budget_usd": 50.0,
    },
    "adversarial-review": {
        "schema": SCHEMAS_DIR / "adversarial_review.json",
        "settings": SETTINGS_DIR / "review.json",
        "max_turns": 100,
        "max_budget_usd": 50.0,
    },
    "implementation-plan": {
        "schema": SCHEMAS_DIR / "implementation_plan.json",
        "settings": SETTINGS_DIR / "plan.json",
        "max_turns": 100,
        "max_budget_usd": 50.0,
    },
}


def fail(message: str, code: int = 1) -> int:
    """Print an error message to stderr and return the exit code."""
    print(message, file=sys.stderr)
    return code


def dump_json(path: Path, payload: Any) -> None:
    """Write JSON to disk with a stable, human-readable format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def resolve_claude() -> str:
    """Locate the Claude CLI binary on PATH."""
    claude_path = shutil.which("claude")
    if not claude_path:
        raise FileNotFoundError("claude binary not found in PATH")
    return claude_path


def run_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture its text output."""
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


def normalize_structured_output(stdout: str) -> tuple[Any | None, dict[str, Any] | None]:
    """Extract structured_output from Claude's JSON envelope when present."""
    if not stdout.strip():
        return None, None
    parsed = json.loads(stdout)
    if isinstance(parsed, dict) and "structured_output" in parsed:
        return parsed.get("structured_output"), parsed
    return parsed, parsed if isinstance(parsed, dict) else None


def doctor_command(args: argparse.Namespace) -> int:
    """Verify that Claude CLI is installed, authenticated, and usable."""
    try:
        claude_path = resolve_claude()
    except FileNotFoundError as exc:
        return fail(f"doctor failed: {exc}")

    version = run_process([claude_path, "-v"])
    if version.returncode != 0:
        return fail(f"doctor failed: unable to read Claude version\n{version.stderr.strip()}")

    auth = run_process([claude_path, "auth", "status"])
    if auth.returncode != 0:
        return fail(f"doctor failed: Claude auth check failed\n{auth.stderr.strip()}")

    try:
        auth_payload = json.loads(auth.stdout)
    except json.JSONDecodeError:
        return fail("doctor failed: Claude auth status was not valid JSON")

    if not auth_payload.get("loggedIn"):
        return fail("doctor failed: Claude is installed but not logged in")

    print(f"claude: ok ({claude_path})")
    print(f"version: {version.stdout.strip()}")
    print(f"auth: ok ({auth_payload.get('email', 'unknown account')})")

    if args.skip_smoke:
        print("smoke: skipped")
        return 0

    smoke_schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
        },
        "required": ["ok"],
        "additionalProperties": False,
    }
    smoke_command = [
        claude_path,
        "-p",
        'Return exactly {"ok": true}.',
        "--model",
        args.model,
        "--effort",
        args.effort,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(smoke_schema),
        "--permission-mode",
        "plan",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--tools",
        "",
        "--max-turns",
        str(args.max_turns),
        "--max-budget-usd",
        str(args.max_budget_usd),
    ]
    smoke = run_process(smoke_command)
    if smoke.returncode != 0:
        stderr = smoke.stderr.strip()
        stdout = smoke.stdout.strip()
        detail = stderr or stdout or "unknown Claude CLI error"
        return fail(f"doctor failed: smoke test failed\n{detail}")

    try:
        structured_output, _ = normalize_structured_output(smoke.stdout)
    except json.JSONDecodeError:
        return fail("doctor failed: smoke test did not return valid JSON")

    if structured_output != {"ok": True}:
        return fail("doctor failed: smoke test returned unexpected structured output")

    print("smoke: ok")
    return 0


def run_command(args: argparse.Namespace) -> int:
    """Run a bounded Claude task and persist normalized structured output."""
    try:
        claude_path = resolve_claude()
    except FileNotFoundError as exc:
        return fail(str(exc))

    defaults = DEFAULTS[args.mode]
    prompt_file = Path(args.prompt_file).resolve()
    if not prompt_file.is_file():
        return fail(f"prompt file not found: {prompt_file}")

    schema_path = Path(args.schema).resolve() if args.schema else defaults["schema"]
    settings_path = Path(args.settings).resolve() if args.settings else defaults["settings"]
    output_path = Path(args.output).resolve()

    if not schema_path.is_file():
        return fail(f"schema file not found: {schema_path}")
    if not settings_path.is_file():
        return fail(f"settings file not found: {settings_path}")

    if args.session == "named" and not args.name:
        return fail("--name is required when --session named")

    prompt_text = prompt_file.read_text(encoding="utf-8")
    schema_text = schema_path.read_text(encoding="utf-8")

    command = [
        claude_path,
        "-p",
        prompt_text,
        "--model",
        args.model,
        "--effort",
        args.effort,
        "--output-format",
        "json",
        "--json-schema",
        schema_text,
        "--permission-mode",
        args.permission_mode,
        "--disable-slash-commands",
        "--tools",
        args.tools,
        "--max-turns",
        str(args.max_turns or defaults["max_turns"]),
        "--max-budget-usd",
        str(args.max_budget_usd or defaults["max_budget_usd"]),
        "--settings",
        str(settings_path),
    ]

    if args.session == "ephemeral":
        command.append("--no-session-persistence")
    else:
        command.extend(["--name", args.name])

    result = run_process(command)
    raw_stdout = result.stdout.strip()
    raw_stderr = result.stderr.strip()
    envelope: dict[str, Any] | None = None
    structured_output: Any | None = None

    if raw_stdout:
        try:
            structured_output, envelope = normalize_structured_output(raw_stdout)
        except json.JSONDecodeError:
            pass

    if result.returncode != 0:
        if envelope:
            dump_json(
                output_path,
                {
                    "status": "error",
                    "mode": args.mode,
                    "errors": envelope.get("errors", []),
                    "session_id": envelope.get("session_id"),
                    "raw": envelope,
                },
            )
        return fail(
            "\n".join(
                part
                for part in [
                    f"claude run failed for mode={args.mode}",
                    raw_stderr or None,
                    raw_stdout or None,
                ]
                if part
            )
        )

    if structured_output is None:
        dump_json(
            output_path,
            {
                "status": "error",
                "mode": args.mode,
                "errors": ["missing structured_output in Claude result"],
                "stdout": raw_stdout,
            },
        )
        return fail("claude run failed: missing structured_output in Claude result")

    dump_json(output_path, structured_output)

    summary = {
        "status": "ok",
        "mode": args.mode,
        "output": str(output_path),
        "session_id": envelope.get("session_id") if envelope else None,
        "turns": envelope.get("num_turns") if envelope else None,
        "cost_usd": envelope.get("total_cost_usd") if envelope else None,
    }
    print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Bounded Claude Code CLI wrapper for the claude-delegate-skill.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Verify the local Claude CLI is usable.")
    doctor.add_argument("--skip-smoke", action="store_true", help="Skip the JSON smoke test.")
    doctor.add_argument("--model", default="opus", help="Claude model for the smoke test.")
    doctor.add_argument(
        "--effort",
        default="max",
        choices=["low", "medium", "high", "max"],
        help="Claude effort level for the smoke test.",
    )
    doctor.add_argument("--max-turns", type=int, default=20, help="Smoke test max turns.")
    doctor.add_argument(
        "--max-budget-usd",
        type=float,
        default=10.0,
        help="Smoke test budget cap in USD.",
    )
    doctor.set_defaults(func=doctor_command)

    run = subparsers.add_parser("run", help="Run a bounded Claude delegation.")
    run.add_argument(
        "--mode",
        choices=sorted(DEFAULTS.keys()),
        required=True,
        help="Delegation mode.",
    )
    run.add_argument("--prompt-file", required=True, help="Prompt file to send to Claude.")
    run.add_argument("--schema", help="Override schema path.")
    run.add_argument("--settings", help="Override settings path.")
    run.add_argument("--model", default="opus", help="Claude model name.")
    run.add_argument(
        "--effort",
        default="max",
        choices=["low", "medium", "high", "max"],
        help="Claude effort level.",
    )
    run.add_argument("--max-turns", type=int, help="Override maximum turns.")
    run.add_argument("--max-budget-usd", type=float, help="Override budget cap in USD.")
    run.add_argument(
        "--session",
        choices=["ephemeral", "named"],
        default="ephemeral",
        help="Ephemeral disables Claude session persistence.",
    )
    run.add_argument("--name", help="Named session identifier.")
    run.add_argument(
        "--permission-mode",
        default="plan",
        choices=["default", "acceptEdits", "plan", "auto", "dontAsk", "bypassPermissions"],
        help="Claude permission mode.",
    )
    run.add_argument(
        "--tools",
        default="Bash,Read",
        help='Built-in Claude tools to expose. Use "" to disable all tools.',
    )
    run.add_argument("--output", required=True, help="Path to write the structured output JSON.")
    run.set_defaults(func=run_command)
    return parser


def main() -> int:
    """Parse CLI arguments and dispatch to the selected subcommand."""
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
