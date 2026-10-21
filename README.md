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

Everything runs locally without accounts, telemetry, cloud storage, or network requests. Reports may reproduce conflicting input values so they can contain sensitive data and must be protected accordingly.

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

## Value-redacted review reports (1.2)

`sync-conflict-lab base.json local.json remote.json --redact-values --format html --output review.html`
produces a metadata-only review. The same flag applies to JSON and Markdown. Source
values and the merged snapshot are omitted, including values in embedded HTML data.
Paths, classifications, presence/absence, counts, selected sides, keyed-array contracts
and fingerprints remain. Null is present; deletion is absent. HTML still downloads a
hash-bound local/remote choice plan, which can be replayed with the original inputs.

Redacted reports are labeled `redacted-review-report`; `merge_available` is false
because they contain no merged application data. `simulated_merge_available` retains
the policy outcome, and a result fingerprint remains when computed. Default detailed
reports and replay plans keep their existing format. Replay normally produces a
detailed report; pass `--redact-values` again for a redacted replay report.

Redaction does not hide object keys, JSON Pointer paths, keyed-array identity values,
identity field names, counts or hashes. Treat those as potentially sensitive metadata;
hashes are not encryption and can be guessed for low-entropy inputs. This flag omits
source values, not all information about a snapshot, and makes no claim that a report
is safe for unrestricted publication. It does not edit or upload source snapshots.

## 1.2.1 — typed and bounded review inputs

JSON booleans are distinct from numeric values during recursive comparison, including atomic arrays. Integer and floating spellings of the same finite JSON number compare equally; fingerprints still bind canonical serialized inputs. Selected conflict values are copied into results. Keyed-array contracts must be valid JSON Pointers addressing arrays in at least one snapshot, and every present target must be an array. Contracts apply only to root arrays or object-field arrays; array-contained traversal is not inferred. A missing contract path is an error rather than a silent fallback.

Files are limited to 10 MiB, JSON to 128 nesting levels and integers to 1,000 digits. Duplicate object keys, nonfinite numbers, malformed replay plans, cyclic/non-JSON library values and symlink paths are rejected. Reports require a new destination in an existing directory and use exclusive creation. These checks prevent accidental replacement; they do not claim hostile concurrent filesystem guarantees.

Markdown uses literal path spans and a content-safe JSON fence. HTML starts with existing resolved sides selected, so its downloaded manual replay plan preserves those decisions; users can change or clear each choice. Detailed and value-redacted reports retain their documented privacy boundaries. Installed examples are under `share/doc/local-first-sync-conflict-lab/examples` in the installation prefix. Source input files are never updated.

## 1.2.2: Release artifact verification

The tag workflow checks that the stable tag, project metadata and runtime version agree before building. It runs the full existing quality suite and dependency audit, verifies wheel and source-distribution metadata, and writes SHA256SUMS from those exact two payloads. Native PR/main checks and independent installed-artifact acceptance remain required before publication. This maintenance release preserves runtime behavior and supported Python versions.
