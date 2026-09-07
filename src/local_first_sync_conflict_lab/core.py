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


def _merge(
    base: Any,
    local: Any,
    remote: Any,
    path: str,
    strategy: str,
    newest: str | None,
    changes: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    choices: dict[str, str],
    keyed_arrays: dict[str, str],
) -> Any:
    if path in keyed_arrays and all(isinstance(item, list) for item in (base, local, remote)):
        identity = keyed_arrays[path]
        maps = [{item[identity]: item for item in array} for array in (base, local, remote)]
        order = list(dict.fromkeys(key for mapping in maps for key in mapping))
        combined = _merge(
            maps[0],
            maps[1],
            maps[2],
            path,
            strategy,
            newest,
            changes,
            conflicts,
            choices,
            keyed_arrays,
        )
        return [combined[key] for key in order if key in combined]
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
                choices,
                keyed_arrays,
            )
            if child is not MISSING:
                result[key] = child
        return result

    if local == remote:
        if local != base:
            changes.append(
                {"path": path, "classification": "same-change", "value": _display(local)}
            )
        return MISSING if local is MISSING else copy.deepcopy(local)
    if local == base:
        changes.append({"path": path, "classification": "remote-only", "value": _display(remote)})
        return MISSING if remote is MISSING else copy.deepcopy(remote)
    if remote == base:
        changes.append({"path": path, "classification": "local-only", "value": _display(local)})
        return MISSING if local is MISSING else copy.deepcopy(local)

    selected = choices.get(path) or (
        "local"
        if strategy == "prefer-local"
        else "remote"
        if strategy == "prefer-remote"
        else newest
    )
    resolution = local if selected == "local" else remote if selected == "remote" else MISSING
    conflicts.append(
        {
            "path": path,
            "classification": "both-changed",
            "base": _display(base),
            "presence": {
                "base": base is not MISSING,
                "local": local is not MISSING,
                "remote": remote is not MISSING,
            },
            "local": _display(local),
            "remote": _display(remote),
            "resolution": selected or "unresolved",
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
    choices: dict[str, str] | None = None,
    keyed_arrays: dict[str, str] | None = None,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of: {', '.join(sorted(STRATEGIES))}")
    if not all(isinstance(item, (dict, list)) for item in (base, local, remote)):
        raise TypeError("base, local, and remote snapshots must be JSON objects or arrays")
    choices = {} if choices is None else choices
    keyed_arrays = {} if keyed_arrays is None else keyed_arrays
    if not isinstance(choices, dict) or any(
        not isinstance(p, str) or v not in ("local", "remote") for p, v in choices.items()
    ):
        raise ValueError("choices must map conflict JSON pointers to local or remote")
    if not isinstance(keyed_arrays, dict) or any(
        not isinstance(p, str) or not isinstance(k, str) or not k for p, k in keyed_arrays.items()
    ):
        raise ValueError("keyed_arrays must map JSON pointers to non-empty identity field names")

    def validate_arrays(value: Any, path: str = "") -> None:
        if path in keyed_arrays and isinstance(value, list):
            identity = keyed_arrays[path]
            keys = []
            for item in value:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get(identity), str)
                    or not item[identity]
                ):
                    raise ValueError("keyed array entries require a non-empty string identity")
                keys.append(item[identity])
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate keyed array identity")
        if isinstance(value, dict):
            for key, child in value.items():
                validate_arrays(child, path + "/" + key.replace("~", "~0").replace("/", "~1"))

    for snapshot in (base, local, remote):
        validate_arrays(snapshot)
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
    merged = _merge(
        base, local, remote, "", strategy, newest, changes, conflicts, choices, keyed_arrays
    )
    if set(choices) - {item["path"] for item in conflicts}:
        raise ValueError("choices contain paths that are not current conflicts")
    unresolved = sum(item["resolution"] == "unresolved" for item in conflicts)
    report: dict[str, Any] = {
        "schema_version": 1,
        "project": PROJECT,
        "strategy": strategy,
        "choices": choices,
        "keyed_arrays": keyed_arrays,
        "array_order": "base identities first, then new local identities, then new remote identities; reorder-only changes are ignored for keyed arrays",
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
        "boundary": "Arrays are atomic unless explicitly keyed by a string identity. Scalars remain atomic; application semantics are not inferred.",
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
