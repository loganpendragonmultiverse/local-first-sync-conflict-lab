import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from local_first_sync_conflict_lab.cli import main
from local_first_sync_conflict_lab.core import render_json, render_markdown, simulate
from local_first_sync_conflict_lab.review import render_html

SECRET = "PRIVATE_SENTINEL_93</script><img src=x>"


def snapshots():
    return (
        {"x": SECRET + "base", "changed": "old", "unchanged": SECRET},
        {"x": SECRET + "local", "changed": SECRET, "unchanged": SECRET},
        {"x": SECRET + "remote", "changed": "old", "unchanged": SECRET},
    )


@pytest.mark.parametrize("strategy", ["manual", "prefer-local", "prefer-remote"])
def test_redacted_values_absent_from_all_formats_and_merge_data(strategy):
    inputs = snapshots()
    before = copy.deepcopy(inputs)
    detailed = simulate(*inputs, strategy=strategy)
    redacted = simulate(*inputs, strategy=strategy, redact_values=True)
    assert redacted["artifact_kind"] == "redacted-review-report"
    assert "merged" not in redacted
    assert redacted["summary"]["merge_available"] is False
    assert (
        redacted["summary"]["simulated_merge_available"] == detailed["summary"]["merge_available"]
    )
    assert redacted["input_sha256"] == detailed["input_sha256"]
    for key in ("conflicts", "unresolved_conflicts", "non_conflicting_changes"):
        assert redacted["summary"][key] == detailed["summary"][key]
    assert redacted["conflicts"][0]["path"] == "/x"
    assert redacted["changes"][0]["classification"] == "local-only"
    for text in (render_json(redacted), render_markdown(redacted), render_html(redacted)):
        assert "PRIVATE_SENTINEL_93" not in text
        assert "&lt;img src=x&gt;" not in text
    payload = json.loads(
        re.search(
            r'<script type="application/json" id="report">(.*?)</script>',
            render_html(redacted),
            re.DOTALL,
        ).group(1)
    )
    assert payload == redacted
    assert inputs == before
    assert "report_mode" not in detailed
    assert "present" not in detailed["changes"][0]
    assert "PRIVATE_SENTINEL_93" in render_json(detailed)


def test_null_and_deletion_preserve_presence_in_changes_and_conflicts():
    report = simulate(
        {"x": 1, "deleted": 2, "null": 3},
        {"deleted": 2, "null": None},
        {"x": None, "null": 3},
        redact_values=True,
    )
    assert report["conflicts"][0]["presence"] == {"base": True, "local": False, "remote": True}
    changes = {item["path"]: item for item in report["changes"]}
    assert changes["/deleted"]["present"] is False
    assert changes["/null"]["present"] is True
    html = render_html(report)
    assert "[DELETED / absent]" in html and "[REDACTED — present]" in html


def test_keyed_array_choices_replay_and_result_hash_remain_bound(tmp_path, capsys):
    inputs = [
        {"items": [{"id": "a", "value": SECRET + suffix}]} for suffix in ("base", "local", "remote")
    ]
    report = simulate(
        *inputs,
        keyed_arrays={"/items": "id"},
        choices={"/items/a/value": "local"},
        redact_values=True,
    )
    assert report["conflicts"][0]["path"] == "/items/a/value"
    assert report["summary"]["unresolved_conflicts"] == 0
    assert len(report["merged_sha256"]) == 64
    assert "PRIVATE_SENTINEL_93" not in render_html(report)
    plan = {
        "version": 1,
        "input_sha256": report["input_sha256"],
        "keyed_arrays": report["keyed_arrays"],
        "choices": report["choices"],
    }
    paths = []
    for index, value in enumerate(inputs):
        path = tmp_path / f"{index}.json"
        path.write_text(json.dumps(value))
        paths.append(str(path))
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps(plan))
    assert main([*paths, "--replay", str(replay), "--redact-values", "--format", "json"]) == 0
    replayed = json.loads(capsys.readouterr().out)
    assert replayed["merged_sha256"] == report["merged_sha256"]
    assert "merged" not in replayed
    assert "PRIVATE_SENTINEL_93" not in json.dumps(replayed)


@pytest.mark.parametrize("format", ["json", "markdown", "html"])
def test_cli_redaction_exit_codes_and_source_preservation(tmp_path, format):
    paths = []
    for index, value in enumerate(snapshots()):
        path = tmp_path / f"{index}.json"
        path.write_text(json.dumps(value))
        paths.append(str(path))
    before = [Path(path).read_bytes() for path in paths]
    output = tmp_path / "report"
    assert main([*paths, "--redact-values", "--format", format, "--output", str(output)]) == 1
    assert "PRIVATE_SENTINEL_93" not in output.read_text()
    assert main([*paths, "--redact-values", "--output", str(output)]) == 2
    assert [Path(path).read_bytes() for path in paths] == before


@pytest.mark.skipif(
    shutil.which("node") is None, reason="Node required for downloaded-plan execution test"
)
def test_actual_html_download_script():
    html = render_html(simulate(*snapshots(), redact_values=True))
    subprocess.run(
        ["node", str(Path(__file__).with_name("review_export.mjs"))],
        input=html,
        text=True,
        check=True,
        capture_output=True,
    )
