# Testing

Run `python -m pip install -e ".[dev]"`, then `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, `python -m pip_audit`, and `python -m build`.

Tests cover field-level classification, atomic arrays, manual conflicts, local and remote preferences, timestamp ordering, replay hashes, invalid snapshots and timestamps, Markdown and JSON reports, CLI exit codes, and replacement-safe output.

## 1.1.0 regression acceptance

Run the complete existing suite plus the new regression fixtures. Confirm the documented command produces the selected output, malformed input remains actionable, and source files remain unchanged. Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.
