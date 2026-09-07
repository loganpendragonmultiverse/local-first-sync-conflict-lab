# Development contract

Produce deterministic, local evidence about declared three-way JSON merge policies without presenting the simulation as a production synchronization engine.

Preserve JSON Pointer evidence, input and result fingerprints, explicit unresolved conflicts, atomic array behavior, replacement-safe output, and honest limitations. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release artifacts, and the Forge catalog together.

## 1.1.0 improvement session

Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.

The HTML review shows base/local/remote values with explicit absence indicators and lets you download selected local/remote decisions. --replay accepts that version 1 plan only when all three input SHA-256 hashes match, using manual policy and the saved keyed_arrays contract. --keyed-arrays maps JSON pointers (root or object-field arrays) to a non-empty string identity field; duplicate/missing identities are rejected. Keyed arrays merge fields by identity, retain base order then new local/remote IDs, and explicitly ignore reorder-only changes. Other arrays stay atomic. Deletion remains distinct from null and resolved deletions no longer become unserializable copied sentinels. Reports contain source values and remain local simulations, not production synchronization engines.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.
