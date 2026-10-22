from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ._io import load_json, preflight_output, write_new_text
from .core import STRATEGIES, _digest, render_json, render_markdown, simulate
from .review import render_html


def _load(path: Path) -> object:
    return load_json(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate a three-way local-first JSON merge.")
    parser.add_argument("base", type=Path)
    parser.add_argument("local", type=Path)
    parser.add_argument("remote", type=Path)
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), default="manual")
    parser.add_argument("--local-updated-at")
    parser.add_argument("--remote-updated-at")
    parser.add_argument("--format", choices=("markdown", "json", "html"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--keyed-arrays", type=Path, help="JSON pointer to string identity field mapping"
    )
    parser.add_argument(
        "--replay", type=Path, help="Hash-bound manual conflict choices exported from HTML"
    )
    parser.add_argument(
        "--redact-values",
        action="store_true",
        help="omit source values and merged data from JSON, Markdown and HTML review reports",
    )
    parser.add_argument(
        "--application-rule",
        choices=("booking-order",),
        help="validate root start/end HH:MM ordering after merge; invalid result exits 1",
    )
    args = parser.parse_args(argv)
    try:
        if args.output:
            preflight_output(args.output)
        base, local, remote = _load(args.base), _load(args.local), _load(args.remote)
        keyed = _load(args.keyed_arrays) if args.keyed_arrays else {}
        choices: object = {}
        application_rule = args.application_rule
        if args.replay:
            replay = _load(args.replay)
            if (
                not isinstance(replay, dict)
                or type(replay.get("version")) is not int
                or replay.get("version") not in (1, 2)
                or set(replay)
                != (
                    {"version", "input_sha256", "choices", "keyed_arrays"}
                    | ({"application_rule"} if replay.get("version") == 2 else set())
                )
            ):
                raise ValueError("replay must be a version 1 or 2 object")
            if replay.get("input_sha256") != {
                "base": _digest(base),
                "local": _digest(local),
                "remote": _digest(remote),
            }:
                raise ValueError("replay source hashes differ")
            if args.strategy != "manual" or args.keyed_arrays or args.application_rule:
                raise ValueError(
                    "replay requires manual strategy and uses its own keyed-array and application-rule contracts"
                )
            application_rule = replay.get("application_rule")
            if replay["version"] == 2 and application_rule != "booking-order":
                raise ValueError("version 2 replay requires booking-order application_rule")
            choices, keyed = replay.get("choices"), replay.get("keyed_arrays")
            if not isinstance(choices, dict) or not isinstance(keyed, dict):
                raise ValueError("replay requires choices and keyed_arrays objects")
        if not isinstance(keyed, dict):
            raise TypeError("keyed arrays must be an object")
        assert isinstance(choices, dict)
        report = simulate(
            base,
            local,
            remote,
            args.strategy,
            args.local_updated_at,
            args.remote_updated_at,
            choices=choices,
            keyed_arrays=keyed,
            redact_values=args.redact_values,
            application_rule=application_rule,
        )
        rendered = (
            render_json(report)
            if args.format == "json"
            else render_html(report)
            if args.format == "html"
            else render_markdown(report)
        )
        if args.output:
            write_new_text(args.output, rendered)
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return (
        1
        if (
            report["summary"]["unresolved_conflicts"]
            or report["summary"].get("application_valid") is False
        )
        else 0
    )
