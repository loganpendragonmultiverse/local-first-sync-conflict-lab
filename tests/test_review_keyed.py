import copy
import json
from pathlib import Path

import pytest

from local_first_sync_conflict_lab.cli import main
from local_first_sync_conflict_lab.core import simulate
from local_first_sync_conflict_lab.review import render_html


def test_deletion_null_and_resolved_deletion():
    assert simulate({"x": 1}, {}, {"x": 1})["merged"] == {}
    assert simulate({"x": 1}, {"x": 1}, {})["merged"] == {}
    assert simulate({"x": 1}, {}, {})["merged"] == {}
    report = simulate({"x": 1}, {}, {"x": None}, choices={"/x": "local"})
    assert report["merged"] == {} and report["summary"]["unresolved_conflicts"] == 0
    assert not report["conflicts"][0]["presence"]["local"]
    assert report["conflicts"][0]["presence"]["remote"]
    assert simulate({"x": 1}, {}, {"x": None}, choices={"/x": "remote"})["merged"] == {"x": None}


def test_keyed_fields_order_and_duplicate_rejection():
    base = {"items": [{"id": "a", "x": 1, "y": 1}, {"id": "b", "x": 0}]}
    local = {"items": [{"id": "b", "x": 0}, {"id": "a", "x": 2, "y": 1}]}
    remote = copy.deepcopy(base)
    remote["items"][0]["y"] = 2
    report = simulate(base, local, remote, keyed_arrays={"/items": "id"})
    assert report["merged"]["items"] == [{"id": "a", "x": 2, "y": 2}, {"id": "b", "x": 0}]
    assert simulate(base, local, remote)["summary"]["unresolved_conflicts"] == 1
    assert (
        simulate(
            base, base, {"items": list(reversed(base["items"]))}, keyed_arrays={"/items": "id"}
        )["merged"]
        == base
    )
    for bad in ([{"id": "a"}, {"id": "a"}], [{"id": 1}], [None]):
        with pytest.raises(ValueError):
            simulate({"items": bad}, {"items": bad}, {"items": bad}, keyed_arrays={"/items": "id"})
    # Delete versus edit stays an explicit identity conflict.
    report = simulate(
        base, {"items": []}, remote, keyed_arrays={"/items": "id"}, choices={"/items/a": "remote"}
    )
    assert report["merged"]["items"] == [{"id": "a", "x": 1, "y": 2}]


def test_replay_hashes_and_html(tmp_path: Path):
    snapshots = [{"x": "base"}, {"x": "</script><img src=x>"}, {"x": None}]
    paths = []
    for name, data in zip(("base", "local", "remote"), snapshots):
        path = tmp_path / (name + ".json")
        path.write_text(json.dumps(data))
        paths.append(str(path))
    report = simulate(*snapshots)
    html = render_html(report)
    assert "</script><img" not in html
    assert "Download replay plan" in html
    output = tmp_path / "review.html"
    assert main([*paths, "--format", "html", "--output", str(output)]) == 1
    plan = {
        "version": 1,
        "input_sha256": report["input_sha256"],
        "choices": {"/x": "local"},
        "keyed_arrays": {},
    }
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps(plan))
    assert main([*paths, "--replay", str(replay), "--format", "json"]) == 0
    assert main([*paths, "--replay", str(replay), "--strategy", "prefer-local"]) == 2
    for mutation in ({"version": 2}, {**plan, "input_sha256": {}}, {**plan, "choices": None}):
        replay.write_text(json.dumps(mutation))
        assert main([*paths, "--replay", str(replay)]) == 2
    contract = tmp_path / "contract.json"
    contract.write_text("[]")
    assert main([*paths, "--keyed-arrays", str(contract)]) == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"choices": []},
        {"choices": {"/x": "guess"}},
        {"choices": {"/missing": "local"}},
        {"keyed_arrays": []},
        {"keyed_arrays": {"": ""}},
        {"local_updated_at": "invalid"},
    ],
)
def test_invalid_contracts(kwargs):
    with pytest.raises((ValueError, TypeError)):
        simulate({"x": 1}, {"x": 2}, {"x": 3}, **kwargs)
