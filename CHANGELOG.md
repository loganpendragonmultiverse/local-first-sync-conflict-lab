# Changelog

## 1.3.0 — 2026-10-22

- Demonstrate independently valid booking edits that combine into invalid start/end ordering.
- Add opt-in `booking-order` post-merge validation with explicit valid/invalid/not-evaluated status, withheld invalid results and CLI exit 1.
- Preserve the application rule in strict version 2 HTML replay exports; keep default behavior and version 1 plans compatible.
- Cover report formats, redaction, source/output protection and real HTML download/replay behavior; ship booking examples in distributions.

## 1.2.2 — 2026-10-21

- Require tag, package and runtime version identity before release builds.
- Run complete quality checks and dependency audit in the pinned tag workflow.
- Verify built wheel/source metadata and publish checksums over the exact payloads.
- Preserve the previous public release, runtime behavior and native support matrix.

## 1.2.1 - 2026-10-21

- Distinguish booleans from numbers in three-way comparisons and reject ineffective keyed-array contracts.
- Validate bounded strict JSON and replay plans, and preserve source files and existing destinations.
- Preserve resolved choices in HTML downloads and render literal Markdown with safe evidence fences.
- Ship installed examples and complete release documentation.

## 1.2.0 - 2026-10-15

- Add opt-in value-redacted JSON, Markdown and HTML reviews that omit source values and merged application data.
- Retain presence/absence, paths, classifications, counts, fingerprints and hash-bound local/remote choices.
- Label redacted artifacts explicitly and document visible metadata and replay privacy limits.

## 1.1.0 - 2026-09-07

- Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.
- Added regression coverage for the audited behavior and invalid inputs.

## 1.0.0 - 2026-08-03

- Added three-way JSON comparison with same-change, local-only, remote-only, and both-changed classifications.
- Added manual, prefer-local, prefer-remote, and newest-snapshot simulations with explicit unresolved conflicts.
- Added JSON Pointer evidence, deterministic input and merged-result fingerprints, Markdown and JSON output, safe CLI exit codes, tests, and cross-platform release packaging.
