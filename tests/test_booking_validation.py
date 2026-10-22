import json
import shutil
import subprocess
from pathlib import Path

import pytest

from local_first_sync_conflict_lab.cli import main
from local_first_sync_conflict_lab.core import render_json, render_markdown, simulate
from local_first_sync_conflict_lab.review import render_html

BASE = {"start": "09:00", "end": "17:00"}
LOCAL = {"start": "14:00", "end": "17:00"}
REMOTE = {"start": "09:00", "end": "12:00"}
RULE = {"application_rule": "booking-order"}


def test_independent_valid_edits_produce_invalid_combination():
    for side in (LOCAL, REMOTE):
        report = simulate(BASE, side, BASE, **RULE)
        assert report["summary"]["application_valid"] is True
        assert report["merged"] == side
    legacy = simulate(BASE, LOCAL, REMOTE)
    assert legacy["merged"] == {"start": "14:00", "end": "12:00"}
    assert "application_validation" not in legacy
    assert "application_valid" not in legacy["summary"]
    for redact in (False, True):
        report = simulate(BASE, LOCAL, REMOTE, redact_values=redact, **RULE)
        assert report["summary"]["conflicts"] == 0
        assert report["summary"]["non_conflicting_changes"] == 2
        assert report["summary"]["application_valid"] is False
        assert report["summary"]["merge_available"] is False
        assert report["application_validation"]["status"] == "invalid"
        assert "merged" not in report and "merged_sha256" not in report
        for render in (render_json, render_markdown, render_html):
            assert "invalid" in render(report)
        if redact:
            for render in (render_json, render_markdown, render_html):
                assert "14:00" not in render(report)
                assert "12:00" not in render(report)


@pytest.mark.parametrize(
    "booking",
    [
        {},
        [],
        {"start": None, "end": "17:00"},
        {"start": "9:00", "end": "17:00"},
        {"start": "24:00", "end": "25:00"},
        {"start": "12:60", "end": "17:00"},
        {"start": "12:00", "end": "12:00"},
        {"start": "23:00", "end": "01:00"},
    ],
)
def test_invalid_booking_shape_or_order(booking):
    report = simulate(booking, booking, booking, **RULE)
    assert report["application_validation"]["status"] == "invalid"
    assert "merged" not in report


def test_valid_merge_and_unresolved_validation():
    remote = {"start": "09:00", "end": "16:00"}
    report = simulate(BASE, LOCAL, remote, **RULE)
    assert report["merged"] == {"start": "14:00", "end": "16:00"}
    assert report["summary"]["application_valid"] is True
    assert report["application_validation"]["issues"] == []
    redacted = simulate(BASE, LOCAL, remote, redact_values=True, **RULE)
    assert redacted["summary"]["simulated_merge_available"] is True
    assert redacted["summary"]["merge_available"] is False
    report = simulate(BASE, LOCAL, {"start": "15:00", "end": "17:00"}, **RULE)
    assert report["application_validation"]["status"] == "not-evaluated"
    assert report["summary"]["application_valid"] is None
    assert report["summary"]["merge_available"] is False
    with pytest.raises(ValueError, match="application_rule"):
        simulate(BASE, BASE, BASE, application_rule="unknown")


@pytest.mark.parametrize("fmt", ["json", "markdown", "html"])
@pytest.mark.parametrize("redact", [False, True])
def test_cli_reports_replay_and_source_preservation(tmp_path, fmt, redact):
    paths = []
    originals = []
    for name, snapshot in zip(("base", "local", "remote"), (BASE, LOCAL, REMOTE)):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(snapshot))
        paths.append(str(path))
        originals.append(path.read_bytes())
    out = tmp_path / f"report.{fmt}"
    args = [*paths, "--application-rule", "booking-order", "--format", fmt, "--output", str(out)]
    if redact:
        args.append("--redact-values")
    assert main(args) == 1
    assert "invalid" in out.read_text()
    assert main(args) == 2  # Existing report is protected.
    report = simulate(BASE, LOCAL, REMOTE, **RULE)
    plan = {
        "version": 2,
        "input_sha256": report["input_sha256"],
        "choices": {},
        "keyed_arrays": {},
        "application_rule": "booking-order",
    }
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps(plan))
    assert main([*paths, "--replay", str(replay)]) == 1
    assert main([*paths, "--replay", str(replay), "--application-rule", "booking-order"]) == 2
    for mutation in (
        {"application_rule": None},
        {"application_rule": "unknown"},
        {"input_sha256": {}},
        {"version": 1},
    ):
        replay.write_text(json.dumps({**plan, **mutation}))
        assert main([*paths, "--replay", str(replay)]) == 2
    assert [Path(path).read_bytes() for path in paths] == originals
    Path(paths[2]).write_text(json.dumps(BASE))
    assert main([*paths, "--application-rule", "booking-order"]) == 0


def test_actual_html_download_preserves_rule(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node required for actual download script")
    report = simulate(BASE, LOCAL, REMOTE, redact_values=True, **RULE)
    harness = Path(__file__).with_name("booking_export.mjs")
    result = subprocess.run(
        [node, str(harness)], input=render_html(report), text=True, capture_output=True, check=True
    )
    plan = json.loads(result.stdout)
    assert plan == {
        "version": 2,
        "input_sha256": report["input_sha256"],
        "choices": {},
        "keyed_arrays": {},
        "application_rule": "booking-order",
    }
    paths = []
    for name, snapshot in zip(("base", "local", "remote"), (BASE, LOCAL, REMOTE)):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(snapshot))
        paths.append(str(path))
    replay = tmp_path / "download.json"
    replay.write_text(result.stdout)
    assert main([*paths, "--replay", str(replay)]) == 1


def test_resolved_conflict_revalidates_selected_candidate(tmp_path):
    remote = {"start": "10:00", "end": "12:00"}
    report = simulate(BASE, LOCAL, remote, **RULE)
    assert report["application_validation"]["status"] == "not-evaluated"
    for side, valid in (("local", False), ("remote", True)):
        resolved = simulate(BASE, LOCAL, remote, choices={"/start": side}, **RULE)
        assert resolved["summary"]["application_valid"] is valid
        paths = []
        for name, snapshot in zip(("base", "local", "remote"), (BASE, LOCAL, remote)):
            path = tmp_path / f"{name}.json"
            path.write_text(json.dumps(snapshot))
            paths.append(str(path))
        replay = tmp_path / "replay.json"
        replay.write_text(
            json.dumps(
                {
                    "version": 2,
                    "input_sha256": report["input_sha256"],
                    "choices": {"/start": side},
                    "keyed_arrays": {},
                    "application_rule": "booking-order",
                }
            )
        )
        assert main([*paths, "--replay", str(replay)]) == (0 if valid else 1)
