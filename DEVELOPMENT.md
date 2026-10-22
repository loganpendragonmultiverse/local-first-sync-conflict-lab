# Development contract

Produce deterministic, local evidence about declared three-way JSON merge policies without presenting the simulation as a production synchronization engine.

Preserve JSON Pointer evidence, input and result fingerprints, explicit unresolved conflicts, atomic array behavior, replacement-safe output, and honest limitations. Every feature release must update tests, version metadata, changelog, README claims, repository metadata, release artifacts, and the Forge catalog together.

## 1.1.0 improvement session

Fix deletion-versus-null handling and add visual conflict choices, hash-bound replay and opt-in keyed-array identity contracts.

The HTML review shows base/local/remote values with explicit absence indicators and lets you download selected local/remote decisions. --replay accepts that version 1 plan only when all three input SHA-256 hashes match, using manual policy and the saved keyed_arrays contract. --keyed-arrays maps JSON pointers (root or object-field arrays) to a non-empty string identity field; duplicate/missing identities are rejected. Keyed arrays merge fields by identity, retain base order then new local/remote IDs, and explicitly ignore reorder-only changes. Other arrays stay atomic. Deletion remains distinct from null and resolved deletions no longer become unserializable copied sentinels. Reports contain source values and remain local simulations, not production synchronization engines.

Local formatting, lint, strict types and regression tests pass. Public release completion requires the protected CI/CodeQL matrix, tagged artifacts and matching Forge catalog/detail deployment.

## 1.2.0 value redaction

--redact-values removes source value fields and merged data before rendering any format. Detailed output stays compatible. Redacted reviews preserve path/presence/classification evidence and hash-bound choices, while marking merged application data unavailable. Paths and keyed identity metadata remain potentially sensitive.

## 1.2.1 — typed and bounded review inputs

JSON booleans are distinct from numeric values during recursive comparison, including atomic arrays. Integer and floating spellings of the same finite JSON number compare equally; fingerprints still bind canonical serialized inputs. Selected conflict values are copied into results. Keyed-array contracts must be valid JSON Pointers addressing arrays in at least one snapshot, and every present target must be an array. Contracts apply only to root arrays or object-field arrays; array-contained traversal is not inferred. A missing contract path is an error rather than a silent fallback.

Files are limited to 10 MiB, JSON to 128 nesting levels and integers to 1,000 digits. Duplicate object keys, nonfinite numbers, malformed replay plans, cyclic/non-JSON library values and symlink paths are rejected. Reports require a new destination in an existing directory and use exclusive creation. These checks prevent accidental replacement; they do not claim hostile concurrent filesystem guarantees.

Markdown uses literal path spans and a content-safe JSON fence. HTML starts with existing resolved sides selected, so its downloaded manual replay plan preserves those decisions; users can change or clear each choice. Detailed and value-redacted reports retain their documented privacy boundaries. Installed examples are under `share/doc/local-first-sync-conflict-lab/examples` in the installation prefix. Source input files are never updated.

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
