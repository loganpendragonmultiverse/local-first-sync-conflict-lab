import json
import re
import subprocess
from pathlib import Path

import pytest

from local_first_sync_conflict_lab.cli import main
from local_first_sync_conflict_lab.core import render_markdown, simulate
from local_first_sync_conflict_lab.review import render_html


@pytest.mark.parametrize(
    "base,local,remote",
    [(0, False, 1), (False, 0, True), ([0], [False], [1]), ({"v": 0}, {"v": False}, {"v": 1})],
)
def test_json_booleans_never_equal_numbers(base, local, remote):
    report = simulate({"x": base}, {"x": local}, {"x": remote})
    assert report["summary"]["unresolved_conflicts"] == 1
    assert report["conflicts"][0]["path"] == "/x" or isinstance(base, dict)
    assert simulate(
        {"x": base}, {"x": local}, {"x": remote}, choices={report["conflicts"][0]["path"]: "local"}
    )["merged"] == {"x": local}


def test_json_number_equality_and_input_detachment():
    assert simulate({"x": 1}, {"x": 1.0}, {"x": 2})["changes"][0]["classification"] == "remote-only"
    local = {"x": [1, 2]}
    report = simulate({"x": [0]}, local, {"x": [3]}, strategy="prefer-local")
    report["merged"]["x"].append(9)
    assert local == {"x": [1, 2]}


@pytest.mark.parametrize(
    "contract", [{"/typo": "id"}, {"x": "id"}, {"/x~2": "id"}, {"/x~": "id"}, {"/x": "id"}]
)
def test_keyed_contract_cannot_silently_miss_or_address_nonarray(contract):
    with pytest.raises(ValueError):
        simulate({"x": {}}, {"x": {}}, {"x": {}}, keyed_arrays=contract)


def test_root_and_escaped_keyed_arrays_remain_supported():
    a = [{"id": "a/b~c", "v": 0}]
    b = [{"id": "a/b~c", "v": 1}]
    c = [{"id": "a/b~c", "v": 2}]
    r = simulate(a, b, c, keyed_arrays={"": "id"}, choices={"/a~1b~0c/v": "local"})
    assert r["merged"] == b
    key = "x/y~z"
    r = simulate({key: a}, {key: b}, {key: c}, keyed_arrays={"/x~1y~0z": "id"})
    assert r["conflicts"][0]["path"] == "/x~1y~0z/a~1b~0c/v"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"redact_values": "false"},
        {"local_updated_at": 4},
        {"choices": {"x": "local"}},
        {"strategy": []},
    ],
)
def test_library_malformed_parameters_remain_actionable(kwargs):
    with pytest.raises((ValueError, TypeError)):
        simulate({}, {}, {}, **kwargs)


def test_cli_strict_json_and_replay_versions_preserve_sources(tmp_path, capsys):
    paths = []
    for name, value in [("base", 0), ("local", False), ("remote", 1)]:
        p = tmp_path / (name + ".json")
        p.write_text(json.dumps({"x": value}))
        paths.append(str(p))
    assert main([*paths, "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    plan = {
        "version": 1,
        "input_sha256": report["input_sha256"],
        "keyed_arrays": {},
        "choices": {"/x": "local"},
    }
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps(plan))
    assert main([*paths, "--replay", str(replay), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["merged"]["x"] is False
    replay.write_text(json.dumps({**plan, "version": True}))
    assert main([*paths, "--replay", str(replay)]) == 2
    Path(paths[0]).write_text('{"x":0,"x":1}')
    assert main(paths) == 2
    assert Path(paths[0]).read_text() == '{"x":0,"x":1}'


def test_markdown_source_fences_and_paths_are_literal():
    report = simulate({"a`b": 0}, {"a`b": "```\n<img src=x>"}, {"a`b": 2})
    text = render_markdown(report)
    assert "``/a`b``" in text
    assert "````json" in text
    assert "</script><img" not in render_html(report)


def test_resolved_policy_is_preselected_in_actual_download_script(tmp_path):
    import shutil

    if shutil.which("node") is None:
        pytest.skip("Node required")
    report = simulate({"x": 0}, {"x": 1}, {"x": 2}, strategy="prefer-remote")
    html = render_html(report)
    payload = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)[0]
    harness = """const assert=require('node:assert/strict');const select={dataset:{index:'0'},value:''};const nodes={report:{textContent:process.argv[1]},download:{},status:{}};global.document={getElementById:id=>nodes[id],querySelectorAll:()=>[select],createElement:()=>({click(){}})};global.URL={createObjectURL:()=>'',revokeObjectURL(){}};global.Blob=class{constructor(parts){global.saved=JSON.parse(parts[0]);}};global.setTimeout=()=>{};"""
    checks = "assert.equal(select.value,'remote');nodes.download.onclick();assert.equal(global.saved.choices['/x'],'remote');"
    subprocess.run(
        ["node", "-e", harness + payload + checks, json.dumps(report)],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("endpoint", ["0001-01-01T00:00:00+23:00", "9999-12-31T23:00:00-23:00"])
def test_offset_endpoint_overflow_is_actionable_and_source_safe(tmp_path, capsys, endpoint):
    with pytest.raises(ValueError, match="UTC timestamp"):
        simulate(
            {"x": 0},
            {"x": 1},
            {"x": 2},
            strategy="newest-snapshot",
            local_updated_at=endpoint,
            remote_updated_at="2026-10-21T00:00:00Z",
        )
    paths = []
    for name, value in [("base", 0), ("local", 1), ("remote", 2)]:
        p = tmp_path / (name + ".json")
        p.write_text(json.dumps({"x": value}))
        paths.append(p)
    before = [p.read_bytes() for p in paths]
    output = tmp_path / "report.json"
    assert (
        main(
            [
                *[str(p) for p in paths],
                "--strategy",
                "newest-snapshot",
                "--local-updated-at",
                endpoint,
                "--remote-updated-at",
                "2026-10-21T00:00:00Z",
                "--output",
                str(output),
            ]
        )
        == 2
    )
    error = capsys.readouterr().err
    assert "UTC timestamp" in error and "Traceback" not in error
    assert [p.read_bytes() for p in paths] == before and not output.exists()
