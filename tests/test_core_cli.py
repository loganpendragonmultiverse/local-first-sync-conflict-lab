import json
from pathlib import Path

import pytest

from local_first_sync_conflict_lab.cli import main
from local_first_sync_conflict_lab.core import render_json, render_markdown, simulate


def snapshots() -> tuple[dict, dict, dict]:
    base = {"name": "A", "settings": {"theme": "light", "density": "normal"}, "tabs": [1]}
    local = {"name": "Local", "settings": {"theme": "light", "density": "compact"}, "tabs": [1, 2]}
    remote = {"name": "Remote", "settings": {"theme": "dark", "density": "normal"}, "tabs": [1, 3]}
    return base, local, remote


def test_manual_classifies_field_level_changes_and_conflicts() -> None:
    report = simulate(*snapshots())
    assert report["summary"] == {
        "non_conflicting_changes": 2,
        "conflicts": 2,
        "unresolved_conflicts": 2,
        "merge_available": False,
    }
    assert {item["path"] for item in report["conflicts"]} == {"/name", "/tabs"}
    assert "Merged snapshot available: no" in render_markdown(report)
    assert '"schema_version": 1' in render_json(report)


@pytest.mark.parametrize(
    ("strategy", "name"), [("prefer-local", "Local"), ("prefer-remote", "Remote")]
)
def test_preference_strategies_produce_replayable_merge(strategy: str, name: str) -> None:
    report = simulate(*snapshots(), strategy=strategy)
    assert report["merged"]["name"] == name
    assert report["summary"]["merge_available"] is True
    assert len(report["merged_sha256"]) == 64


def test_newest_snapshot_requires_ordered_timestamps() -> None:
    report = simulate(
        *snapshots(),
        strategy="newest-snapshot",
        local_updated_at="2026-08-03T12:00:00Z",
        remote_updated_at="2026-08-03T13:00:00Z",
    )
    assert report["newest_snapshot"] == "remote"
    with pytest.raises(ValueError, match="requires both"):
        simulate(*snapshots(), strategy="newest-snapshot")
    with pytest.raises(ValueError, match="must differ"):
        simulate(
            *snapshots(),
            strategy="newest-snapshot",
            local_updated_at="2026-08-03T12:00:00Z",
            remote_updated_at="2026-08-03T12:00:00+00:00",
        )


def test_invalid_inputs() -> None:
    with pytest.raises(TypeError, match="objects or arrays"):
        simulate({}, {}, "bad")
    with pytest.raises(ValueError, match="strategy"):
        simulate({}, {}, {}, strategy="magic")
    with pytest.raises(ValueError, match="UTC offset"):
        simulate(
            {},
            {},
            {},
            strategy="newest-snapshot",
            local_updated_at="2026-01-01",
            remote_updated_at="2026-01-02",
        )


def test_cli_exit_codes_and_replacement_safety(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    paths = []
    for name, data in zip(("base", "local", "remote"), snapshots(), strict=True):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        paths.append(path)
    assert main([*(str(path) for path in paths), "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["summary"]["unresolved_conflicts"] == 2
    output = tmp_path / "report.json"
    assert (
        main(
            [
                *(str(path) for path in paths),
                "--strategy",
                "prefer-local",
                "--format",
                "json",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert main([*(str(path) for path in paths), "--output", str(output)]) == 2
