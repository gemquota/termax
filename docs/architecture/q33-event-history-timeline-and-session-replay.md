# Q33 — Event History, Replay and Experimentation Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** development/0.1.4-contract-foundation

## Decision

Accepted selections: **F, B**.

- **F — Visual timeline explorer:** navigate an interactive timeline connecting commands, processes, system activity, architecture events, and visual scenes.
- **B — Full session replay:** reconstruct command sessions, output streams, activity timelines, and visual workspace states.

## Product direction

Build an event-history and replay subsystem that makes TERMAX activity inspectable as a coherent timeline. Users should be able to move through recorded sessions, correlate related events across subsystems, and reconstruct supported visual states. The first priority is faithful historical inspection, not speculative simulation or arbitrary re-execution.

## Proposed architecture

- **Event Envelope Contract:** a versioned event structure with event ID, event type, source, timestamp, session/workspace correlation IDs, schema version, and provenance.
- **Event Recorder:** captures explicitly enabled event sources with bounded buffering, backpressure, and visible recording status.
- **Session Index:** groups command lifecycle events, stdout/stderr records, process observations, system activity, architecture observations, and visual scene checkpoints.
- **Timeline Query Engine:** supports chronological navigation, filtering, correlation, and bounded range queries.
- **Replay Coordinator:** advances through recorded events in timestamp/order sequence and emits historical view-model updates without executing the original commands.
- **Output Reconstruction Adapter:** preserves stdout/stderr distinction, ordering metadata, truncation markers, and available stream content.
- **Visual State Checkpoint Adapter:** records supported scene/workspace snapshots so replay can reconstruct historical presentation without depending on live system state.
- **TVF Timeline Renderer:** presents the timeline and correlated event lanes through text-first and optional graphical backends.
- **Retention and Redaction Controller:** applies configurable storage limits, retention periods, sensitive-data redaction, and explicit export controls.

## Replay semantics

- Replay is read-only and must never re-run shell commands, scripts, plugins, or external actions.
- Recorded output is historical data, not executable input or instructions.
- Preserve event ordering and original timestamps; explicitly label missing, delayed, truncated, or reordered records.
- Distinguish reconstructed state from live state at all times.
- Where a visual state cannot be reconstructed exactly, show an incomplete-reconstruction indicator rather than fabricating details.
- Seeking and playback speed changes must not block the live shell or command execution.

## Recording, privacy and resilience

- Recording is explicit and visibly indicated; event sources can be enabled or disabled independently.
- Use bounded buffers and storage quotas, with clear drop/truncation markers under pressure.
- Redact secrets and sensitive command output before durable storage by default.
- Do not persist raw environment secrets, credentials, or unrestricted process environments.
- Retention is configurable; provide preview before export and safe deletion of selected recordings.
- Recording failures must not interfere with the underlying command or shell.
- Support interrupted sessions and partial recordings without corrupting the index.

## Delivery sequence

1. **0.1.4:** define event envelope, session correlation, timeline query, replay, checkpoint, and retention contracts.
2. **0.1.5:** record Command Observatory lifecycle events and bounded output metadata.
3. **0.1.6:** implement session indexing and a text-first timeline explorer.
4. **0.1.7:** add read-only session replay and output reconstruction.
5. **0.1.8:** correlate system, architecture, and workspace events where supported.
6. **0.1.9:** add TVF timeline lanes and visual checkpoint reconstruction.
7. **0.2.x:** expand searchable history, cross-session comparisons, richer replay controls, and optional deterministic simulation integrations as separately approved capabilities.

## Acceptance criteria

- Timeline events include source, timestamp, type, and correlation metadata where available.
- Users can filter and navigate recorded sessions without accessing live command execution controls.
- Replay reconstructs supported history without invoking commands or external actions.
- Original stdout/stderr distinction and ordering metadata are preserved where captured.
- Truncation, missing events, and incomplete visual reconstruction are explicitly indicated.
- Recording can be disabled and does not block or alter command execution.
- Storage, buffering, and retention are bounded and observable.
- Sensitive data is redacted before durable recording by default.
- Text-first inspection remains fully usable without SIXEL or other graphics protocols.
- No changes are made to installed TERMAX 0.1.0 or shell startup files.

## Deferred scope

Q33 did not select the simulation sandbox, what-if experimentation, or deterministic experiment runner as priorities. Those capabilities are not implied by this decision and require separate design approval.

## Status clarification

This document records accepted product direction and proposed implementation sequencing. The unified event-history timeline, full session reconstruction, and replay coordinator are not yet implemented.