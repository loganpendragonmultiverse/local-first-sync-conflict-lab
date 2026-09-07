# Local-First Sync Conflict Lab

[![CI](https://github.com/loganpendragonmultiverse/local-first-sync-conflict-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/local-first-sync-conflict-lab/actions/workflows/ci.yml)

Simulate and explain a three-way synchronization merge from base, local, and remote JSON snapshots. The local CLI classifies same, local-only, remote-only, and both-changed values; records replayable input hashes; and can model manual, prefer-local, prefer-remote, or newest-snapshot policies.

## Three-minute start

```bash
python -m pip install .
sync-conflict-lab examples/base.json examples/local.json examples/remote.json
sync-conflict-lab examples/base.json examples/local.json examples/remote.json --strategy prefer-local --format json --output result.json
```

Exit code `1` means manual conflicts remain unresolved, `0` means the selected policy produced a complete simulated result, and `2` means the inputs or command were invalid. Existing reports are never overwritten.

## Merge model

Objects are compared recursively by JSON Pointer path. Independent field changes merge automatically. Arrays and scalar values are atomic because positional or domain-aware merging would otherwise guess application semantics. The newest-snapshot strategy requires two distinct timezone-aware ISO 8601 timestamps and applies the newer side only where both sides changed.

## Privacy and limitations

Everything runs locally without accounts, telemetry, storage, or network requests. Reports may reproduce conflicting input values so they can contain sensitive data and must be protected accordingly.

This is a deterministic policy simulator, not a production synchronization engine or CRDT. It does not infer identities inside arrays, validate an application's schema, guarantee convergence across repeated real-world operations, contact a server, or write merged data back into an application.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src
pytest
python -m pip_audit
python -m build
```

Python 3.10 or newer is supported on Windows, macOS, and Linux. Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Version 1.1.0: reviewed improvements

Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.

```bash
sync-conflict-lab base.json local.json remote.json --format html --output review.html
```

The HTML review shows base/local/remote values with explicit absence indicators and lets you download selected local/remote decisions. --replay accepts that version 1 plan only when all three input SHA-256 hashes match, using manual policy and the saved keyed_arrays contract. --keyed-arrays maps JSON pointers (root or object-field arrays) to a non-empty string identity field; duplicate/missing identities are rejected. Keyed arrays merge fields by identity, retain base order then new local/remote IDs, and explicitly ignore reorder-only changes. Other arrays stay atomic. Deletion remains distinct from null and resolved deletions no longer become unserializable copied sentinels. Reports contain source values and remain local simulations, not production synchronization engines.
