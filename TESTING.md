# Testing

Run `python -m pip install -e ".[dev]"`, then `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, `python -m pip_audit`, and `python -m build`.

Tests cover field-level classification, atomic arrays, manual conflicts, local and remote preferences, timestamp ordering, replay hashes, invalid snapshots and timestamps, Markdown and JSON reports, CLI exit codes, and replacement-safe output.

## 1.1.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.

## 1.2.0 regression acceptance

Check sentinel values are absent from JSON, Markdown, HTML text and embedded payloads. Check downloaded choice plans remain value-free and hash-bound; null/deletion, keyed arrays, counts, default reports and replay stay correct.

The downloaded-plan regression executes the actual HTML script with Node 22 and a minimal DOM/download harness. CI installs Node; Python-only environments skip this one browser-script test. Run it through pytest with Node available.

## 1.2.1 — typed and bounded review inputs

JSON booleans are distinct from numeric values during recursive comparison, including atomic arrays. Integer and floating spellings of the same finite JSON number compare equally; fingerprints still bind canonical serialized inputs. Selected conflict values are copied into results. Keyed-array contracts must be valid JSON Pointers addressing arrays in at least one snapshot, and every present target must be an array. Contracts apply only to root arrays or object-field arrays; array-contained traversal is not inferred. A missing contract path is an error rather than a silent fallback.

Files are limited to 10 MiB, JSON to 128 nesting levels and integers to 1,000 digits. Duplicate object keys, nonfinite numbers, malformed replay plans, cyclic/non-JSON library values and symlink paths are rejected. Reports require a new destination in an existing directory and use exclusive creation. These checks prevent accidental replacement; they do not claim hostile concurrent filesystem guarantees.

Markdown uses literal path spans and a content-safe JSON fence. HTML starts with existing resolved sides selected, so its downloaded manual replay plan preserves those decisions; users can change or clear each choice. Detailed and value-redacted reports retain their documented privacy boundaries. Installed examples are under `share/doc/local-first-sync-conflict-lab/examples` in the installation prefix. Source input files are never updated.

Run the original suite with Node 22 available so both actual HTML download-script regressions execute. New cases cover nested boolean/numeric comparisons, root/escaped keyed contracts, malformed contracts/replay, strict JSON and destination races. Exact tagged wheel and source-distribution acceptance must use installed imports and console commands outside the checkout; test the installed examples and all three browser engines at desktop/mobile widths before release.

## 1.2.2: Release artifact verification

The tag workflow checks that the stable tag, project metadata and runtime version agree before building. It runs the full existing quality suite and dependency audit, verifies wheel and source-distribution metadata, and writes SHA256SUMS from those exact two payloads. Native PR/main checks and independent installed-artifact acceptance remain required before publication. This maintenance release preserves runtime behavior and supported Python versions.

## 1.3.0: Booking application rule

Use the opt-in root `booking-order` rule after complete field merging. It requires
same-day zero-padded HH:MM start < end; it deliberately provides no general schema
or timezone engine. Invalid candidates are withheld and exit 1. Unresolved field
conflicts leave validation not-evaluated. Default reports and version 1 replay are
compatible; enabled HTML exports use strict version 2 plans retaining the rule.

Regression acceptance covers independently valid edits combining into an invalid
booking, valid combined state, malformed/missing/equal/overnight times, unresolved
conflicts, all report formats, redaction, CLI exit codes, immutable sources and
outputs, and execution of the actual HTML download script followed by CLI replay.
Run the full quality suite, audit, build, installed wheel/source acceptance and
browser engines at desktop/mobile sizes before publishing. All simulator scope
and metadata privacy boundaries remain in effect.
