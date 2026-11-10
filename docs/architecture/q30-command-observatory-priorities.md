# Q30 — Command Observatory Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** development/0.1.4-contract-foundation

## Decision

Accepted selections: **A, H, C**.

- **A — Live command tracking:** track commands as they start, execute, finish, fail, or get interrupted, with duration and exit status.
- **H — Complete observability platform:** combine command lifecycle, output visualisation, process/resource context, timelines, and diagnostics in a modular platform.
- **C — Live output visualisation:** stream command output into classified panels, activity feeds, alerts, and visual event displays.

## Product direction

The Command Observatory is a user-visible, event-driven view of command execution. It should make active and recent work understandable without changing shell semantics or hiding original command output.

The first release prioritises reliable lifecycle events and live output presentation. Process trees, replay, multi-session coordination, and advanced diagnostics remain later extensions.

## Proposed components

- **Command Lifecycle Observer:** records start, running, completion, failure, interruption, exit status, and duration when observable.
- **Output Stream Adapter:** captures or receives stdout/stderr through explicit integration points and preserves stream identity and ordering metadata.
- **Output Classifier:** categorises output conservatively (ordinary output, warning, error, progress, or structured event) while retaining original text.
- **Activity Event Bus:** distributes validated lifecycle and output events to subscribed workspace panels.
- **Observatory View Model:** builds bounded current-session and recent-session state for UI consumers.
- **Timeline Panel:** displays timestamped command and output events.
- **Visual Output Panels:** render text-first output, with optional TVF visual treatments where supported.
- **Retention and Redaction Controller:** caps event history and applies configured redaction before persistence or export.

## Event model expectations

A command event should carry, where available: event identifier and schema version; session and command correlation identifiers; event type and timestamp; redacted command display metadata; lifecycle state and exit status when known; stream identity and sequence metadata for output events; and source/provenance with confidence where observation is incomplete.

Unknown lifecycle information must remain unknown. Silence is not proof of successful completion, and an absent exit status is not zero.

## Output handling

- Preserve stdout and stderr as distinct streams.
- Preserve original output and ordering metadata; classification is an additional annotation, not a replacement.
- Do not execute, interpret, or trust command output as instructions.
- Apply bounded buffering, line/byte limits, and backpressure so noisy processes cannot exhaust memory or freeze the UI.
- Support pause/resume of visual updates without blocking the underlying command.
- Keep normal terminal output usable if the Observatory is disabled or fails.
- Redact sensitive data before durable storage or export; define explicit retention limits.

## Shell integration strategy

Prefer explicit, minimal integration points that can report lifecycle events reliably. Avoid rewriting user shell startup files or replacing existing shell behaviour. Initial support should target the known Termux/Zsh environment while retaining a plain CLI fallback.

If a command is launched outside an observable integration path, the Observatory must report that lifecycle data is unavailable rather than imply complete coverage.

## Delivery sequence

1. **0.1.4:** define command lifecycle, output event, session, and observatory view-model contracts.
2. **0.1.5:** implement a text-first lifecycle observer for explicitly launched TERMAX commands.
3. **0.1.6:** add bounded stdout/stderr stream adapters and event ordering tests.
4. **0.1.7:** add activity feed and timeline panels with filtering.
5. **0.1.8:** add conservative output classification, preserving source text and provenance.
6. **0.1.9:** integrate TVF panels and optional visual event treatments.
7. **0.2.x:** expand to process/resource context, multi-session views, replay, and evidence-based diagnostics.

## Acceptance criteria

- Lifecycle state and exit status are reported only when actually observed.
- stdout and stderr remain distinguishable.
- Output order and source provenance are retained.
- Buffering, history, and redraw work are bounded.
- Observatory failure does not break the command or shell.
- Output is treated as untrusted data, never executable instruction.
- Sensitive data is redacted before persistence/export according to policy.
- No shell startup files are silently rewritten.
- Visual features are optional; text-first operation remains complete.
- Missing observation coverage is explicitly reported.
- Existing TERMAX 0.1.0 and user shell configuration remain untouched.

## Status clarification

This document records accepted product direction and proposed implementation sequencing. The Command Observatory is not yet implemented.