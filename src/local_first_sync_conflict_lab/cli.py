from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import STRATEGIES, render_json, render_markdown, simulate


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
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = simulate(
            _load(args.base),
            _load(args.local),
            _load(args.remote),
            args.strategy,
            args.local_updated_at,
            args.remote_updated_at,
        )
        rendered = render_json(report) if args.format == "json" else render_markdown(report)
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
