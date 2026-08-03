from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

PROJECT = "local-first-sync-conflict-lab"
MISSING = object()
STRATEGIES = {"manual", "prefer-local", "prefer-remote", "newest-snapshot"}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _parse_time(value: str | None, label: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _display(value: Any) -> Any:
    return {"missing": True} if value is MISSING else copy.deepcopy(value)


def _resolve(local: Any, remote: Any, strategy: str, newest: str | None) -> Any:
    if strategy == "prefer-local" or newest == "local":
        return local
    if strategy == "prefer-remote" or newest == "remote":
        return remote
    return MISSING


def _merge(
    base: Any,
    local: Any,
    remote: Any,
    path: str,
    strategy: str,
    newest: str | None,
    changes: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> Any:
    if local == remote:
        if local != base:
            changes.append(
                {"path": path, "classification": "same-change", "value": _display(local)}
            )
        return copy.deepcopy(local)
    if local == base:
        changes.append({"path": path, "classification": "remote-only", "value": _display(remote)})
        return copy.deepcopy(remote)
    if remote == base:
        changes.append({"path": path, "classification": "local-only", "value": _display(local)})
        return copy.deepcopy(local)

    if all(isinstance(item, dict) for item in (base, local, remote)):
        result: dict[str, Any] = {}
        keys = sorted(set(base) | set(local) | set(remote))
        for key in keys:
            child = _merge(
                base.get(key, MISSING),
                local.get(key, MISSING),
                remote.get(key, MISSING),
                f"{path}/{key.replace('~', '~0').replace('/', '~1')}",
                strategy,
                newest,
                changes,
                conflicts,
            )
            if child is not MISSING:
                result[key] = child
        return result

    resolution = _resolve(local, remote, strategy, newest)
    conflicts.append(
        {
            "path": path,
            "classification": "both-changed",
            "base": _display(base),
            "local": _display(local),
            "remote": _display(remote),
            "resolution": "unresolved"
            if resolution is MISSING
            else ("local" if resolution == local else "remote"),
        }
    )
    return resolution


def simulate(
    base: Any,
    local: Any,
    remote: Any,
    strategy: str = "manual",
    local_updated_at: str | None = None,
    remote_updated_at: str | None = None,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of: {', '.join(sorted(STRATEGIES))}")
    if not all(isinstance(item, (dict, list)) for item in (base, local, remote)):
        raise TypeError("base, local, and remote snapshots must be JSON objects or arrays")
    newest: str | None = None
    local_time = _parse_time(local_updated_at, "local_updated_at")
    remote_time = _parse_time(remote_updated_at, "remote_updated_at")
    if strategy == "newest-snapshot":
        if local_time is None or remote_time is None:
            raise ValueError("newest-snapshot requires both timestamps")
        if local_time == remote_time:
            raise ValueError("newest-snapshot timestamps must differ")
        newest = "local" if local_time > remote_time else "remote"
    changes: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    merged = _merge(base, local, remote, "", strategy, newest, changes, conflicts)
    unresolved = sum(item["resolution"] == "unresolved" for item in conflicts)
    report: dict[str, Any] = {
        "schema_version": 1,
        "project": PROJECT,
        "strategy": strategy,
        "newest_snapshot": newest,
        "input_sha256": {"base": _digest(base), "local": _digest(local), "remote": _digest(remote)},
        "summary": {
            "non_conflicting_changes": len(changes),
            "conflicts": len(conflicts),
            "unresolved_conflicts": unresolved,
            "merge_available": merged is not MISSING and unresolved == 0,
        },
        "changes": sorted(changes, key=lambda item: item["path"]),
        "conflicts": sorted(conflicts, key=lambda item: item["path"]),
        "boundary": "Arrays and scalar values are treated atomically; the lab simulates declared policies and does not infer application semantics.",
    }
    if report["summary"]["merge_available"]:
        report["merged"] = merged
        report["merged_sha256"] = _digest(merged)
    return report


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Local-First Sync Conflict Report",
        "",
        f"Strategy: `{report['strategy']}`",
        f"Conflicts: {summary['conflicts']} ({summary['unresolved_conflicts']} unresolved)",
        f"Merged snapshot available: {'yes' if summary['merge_available'] else 'no'}",
        "",
        "## Conflicts",
        "",
    ]
    lines += [
        f"- `{item['path'] or '/'}` — {item['resolution']}" for item in report["conflicts"]
    ] or ["- None"]
    lines += ["", "## Evidence", "", f"```json\n{render_json(report).rstrip()}\n```", ""]
    return "\n".join(lines)
