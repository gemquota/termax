# Q31 — Aquarium and Pulse Experimental Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** development/0.1.4-contract-foundation

## Decision

Accepted selections: **F, H, E**.

- **F — SIXEL-enhanced Aquarium:** combine ASCII environments with SIXEL images, animated sprites, layered scenes, and richer visual effects.
- **H — Unified experimental environment:** combine Aquarium, Pulse, procedural generation, visual effects, simulations, and event-driven behaviour into one framework.
- **E — Multi-environment simulation:** run several independent visual ecosystems or simulations inside different workspace panels.

## Product direction

Unify Aquarium and Pulse as distinct experiences built on shared event, scene, simulation, and rendering infrastructure. Support multiple independent environments in a workspace, with SIXEL-enhanced presentation where positively detected and explicitly enabled. Preserve the original lightweight ASCII experience as a complete fallback.

## Proposed architecture

- **Experimental Environment Host:** owns environment instances, lifecycle, isolation boundaries, resource budgets, and workspace placement.
- **Event Adapter:** consumes validated TERMAX command and system events; events are data and cannot trigger privileged actions.
- **Simulation Runtime:** advances independent environments using bounded, deterministic update steps where possible.
- **Aquarium Environment:** models organisms, environment state, interactions, and event-driven behaviours.
- **Pulse Environment:** classifies activity streams and maps event patterns into visual feedback, waveforms, and effects.
- **Procedural Scene Generator:** produces bounded terrain, particles, sprites, patterns, and visual scene data.
- **TVF Scene Adapter:** maps environment output into backend-independent layers and scenes.
- **SIXEL Asset Pipeline:** supplies optional raster sprites, images, and frame sequences through the TVF SIXEL backend.
- **Workspace Environment Manager:** starts, pauses, resumes, stops, and arranges multiple independent environment instances.
- **Resource Governor:** enforces per-environment and aggregate CPU, memory, frame-rate, output, and duration limits.

## Multi-environment behaviour

- Each environment has an independent identifier, configuration, state, lifecycle, and resource budget.
- One slow or failed environment must not stall unrelated command execution or other environments.
- Environments can be paused, resumed, reset, and closed independently.
- Workspace layouts may host multiple environments, but aggregate budgets must prevent resource multiplication from overwhelming Android devices.
- State persistence is opt-in, bounded, versioned, and recoverable; transient sessions need not write state to disk.

## Event model and safety

- Consume only explicitly exposed, validated event streams with source and timestamp metadata.
- Treat command output, imported sprites, scene definitions, and external events as untrusted data.
- No environment may execute shell commands, approve actions, alter permissions, or infer user consent from a visual event.
- Map event classes to effects through declarative configuration, not arbitrary shell hooks.
- Redact sensitive event content before it reaches visual panels or persistent history.
- Make event subscriptions visible and individually disableable.

## SIXEL-enhanced rendering

- ASCII/Unicode rendering remains the baseline and must be usable independently.
- SIXEL is selected only after conservative capability verification and explicit user enablement.
- Use bounded sprite dimensions, frame counts, palette sizes, encoded output, and render time.
- Support static assets before animation; add animated sprites only after scheduler, cancellation, and terminal restoration are proven.
- Detect multiplexer uncertainty and provide a documented test path rather than claiming universal passthrough.
- Restore terminal state on normal exit, exceptions, interruption, and cancellation.

## Delivery sequence

1. **0.1.4:** define environment, event subscription, simulation-step, scene-output, and resource-budget contracts.
2. **0.1.5:** consolidate Aquarium and Pulse event interfaces while retaining their existing standalone entry points.
3. **0.1.6:** add a shared ASCII/Unicode scene adapter and one independent environment lifecycle.
4. **0.1.7:** add multiple isolated environment instances with aggregate resource limits.
5. **0.1.8:** integrate TVF layers and static SIXEL assets behind explicit capability gates.
6. **0.1.9:** prototype bounded animation and procedural effects with cancellation and restoration tests.
7. **0.2.x:** expand simulations, reactive behaviours, richer sprite systems, persistent profiles, and composable workspace scenes.

## Acceptance criteria

- Aquarium and Pulse remain independently usable.
- Multiple environments can run, pause, resume, reset, and stop independently.
- Per-environment and aggregate resource budgets are enforced.
- Failure in one environment does not corrupt other environments or the shell.
- Events are validated, provenance-labelled, and treated as untrusted data.
- Visual event mappings cannot execute commands or grant capabilities.
- ASCII/Unicode fallback is complete and graphics remain optional.
- SIXEL is capability-verified, explicitly enabled, bounded, and cancellation-safe.
- Terminal state is restored across tested exit paths.
- No shell startup files or installed TERMAX 0.1.0 files are modified by this decision.

## Status clarification

This document records accepted product direction and proposed implementation sequencing. The unified environment host, multi-instance simulation runtime, SIXEL-enhanced Aquarium, and shared Pulse integration are not yet implemented.