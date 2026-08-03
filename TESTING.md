# Testing

Run `python -m pip install -e ".[dev]"`, then `ruff format --check .`, `ruff check .`, `mypy src`, `pytest`, `python -m pip_audit`, and `python -m build`.

Tests cover field-level classification, atomic arrays, manual conflicts, local and remote preferences, timestamp ordering, replay hashes, invalid snapshots and timestamps, Markdown and JSON reports, CLI exit codes, and replacement-safe output.
