from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import STRATEGIES, _digest, render_json, render_markdown, simulate
from .review import render_html


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


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
    args = parser.parse_args(argv)
    try:
        base, local, remote = _load(args.base), _load(args.local), _load(args.remote)
        keyed = _load(args.keyed_arrays) if args.keyed_arrays else {}
        choices: object = {}
        if args.replay:
            replay = _load(args.replay)
            if not isinstance(replay, dict) or replay.get("version") != 1:
                raise ValueError("replay must be a version 1 object")
            if replay.get("input_sha256") != {
                "base": _digest(base),
                "local": _digest(local),
                "remote": _digest(remote),
            }:
                raise ValueError("replay source hashes differ")
            if args.strategy != "manual" or args.keyed_arrays:
                raise ValueError(
                    "replay requires manual strategy and uses its own keyed-array contract"
                )
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
        )
        rendered = (
            render_json(report)
            if args.format == "json"
            else render_html(report)
            if args.format == "html"
            else render_markdown(report)
        )
        if args.output:
            if args.output.exists():
                raise ValueError(f"output already exists: {args.output}")
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["summary"]["unresolved_conflicts"] else 0
