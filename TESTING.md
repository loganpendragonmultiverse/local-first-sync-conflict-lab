# Testing

Run `python -m pip install -e ".[dev]"`, then `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, `python -m pip_audit`, and `python -m build`.

Tests cover field-level classification, atomic arrays, manual conflicts, local and remote preferences, timestamp ordering, replay hashes, invalid snapshots and timestamps, Markdown and JSON reports, CLI exit codes, and replacement-safe output.

## 1.1.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.

## 1.2.0 regression acceptance

Check sentinel values are absent from JSON, Markdown, HTML text and embedded payloads. Check downloaded choice plans remain value-free and hash-bound; null/deletion, keyed arrays, counts, default reports and replay stay correct.

The downloaded-plan regression executes the actual HTML script with Node 22 and a minimal DOM/download harness. CI installs Node; Python-only environments skip this one browser-script test. Run it through pytest with Node available.
