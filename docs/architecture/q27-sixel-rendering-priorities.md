# Q27 — SIXEL Rendering Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture foundation  
**Parent decision:** [Q26 — Experimental Visual Systems and Rendering Architecture](q26-experimental-visual-systems-and-rendering.md)  
**Branch:** `development/0.1.4-contract-foundation`

## Decision

Accepted selections: **H, E, C**.

- **H — Everything, modularly:** pursue a complete graphics subsystem with independent capabilities and progressive implementation.
- **E — Visual effects engine:** support transitions, fades, scrolling, particle effects, reactive visualisations, and procedural graphics.
- **C — Interactive visual scenes:** support layered images, charts, text overlays, dynamic panels, and coordinated redraw.

The combined direction is a modular SIXEL-capable visual runtime, not a monolithic renderer and not a requirement that every terminal support every effect.

## Design principles

1. **Progressive capability:** static image rendering is the foundation; scenes, effects, and animation build on stable lower layers.
2. **Backend independence:** scene and effect definitions must not depend directly on SIXEL escape-sequence details. SIXEL is one rendering backend; text/ANSI remains a first-class fallback.
3. **Composable scenes:** images, charts, text, panels, and effects are independent layers with explicit bounds, ordering, refresh policies, and lifecycle.
4. **Interactive control:** scenes must support keyboard-first navigation, pause/resume, cancellation, focus, and deterministic teardown.
5. **Bounded rendering:** frame rate, output bytes, image dimensions, particle counts, history, CPU, and memory must have configurable hard limits.
6. **Graceful degradation:** unsupported effects are simplified or omitted with a clear fallback; they must never corrupt terminal state or block core interaction.
7. **User-controlled spectacle:** animations and effects are opt-in, reduce-motion aware, and disableable per session.

## Proposed runtime components

- **Scene Graph:** owns scene nodes, layer hierarchy, geometry, visibility, clipping, and z-order.
- **Frame Scheduler:** coordinates frame timing, dirty-region updates, throttling, and cancellation.
- **Effect Registry:** exposes versioned, capability-declared effects such as fades, transitions, scrolling, particles, and procedural patterns.
- **Interaction Controller:** routes keyboard input, focus, selection, pause/resume, and scene-level actions.
- **Compositor:** combines scene layers and maps them to backend-specific output.
- **SIXEL Encoder Adapter:** converts bounded raster frames into SIXEL output and tracks palette and terminal constraints.
- **Fallback Renderer:** maps scene elements to ANSI, Unicode, and plain-text representations when graphics are unavailable.
- **Resource Governor:** enforces CPU, memory, frame-rate, output-size, and duration budgets.
- **Scene Diagnostics:** reports active backend, detected capabilities, dropped frames, render time, and fallback reasons.

## Scene and effect contract expectations

A scene definition should describe content and intent rather than raw terminal escape sequences. Each layer should declare:
- stable identifier and type;
- bounds and layout constraints;
- z-order and clipping behaviour;
- visibility and refresh policy;
- resource budget and fallback representation;
- interaction and accessibility metadata where applicable.

An effect should declare:
- stable identifier and version;
- supported renderer capabilities;
- parameters with validated ranges;
- start, update, pause, resume, and cleanup lifecycle;
- resource and output budgets;
- reduced-motion alternative;
- deterministic cancellation and failure behaviour.

Untrusted scene or effect definitions are data, not executable plugins. Any future executable extension mechanism requires a separate security design and explicit capability policy.

## SIXEL implementation sequence

1. Validate capability detection and terminal-state restoration independently of visual effects.
2. Implement bounded static SIXEL rendering and deterministic image placement.
3. Implement a rectangular scene/layer model with text and ANSI fallback.
4. Add coordinated redraw and interactive scene input without animation.
5. Add a frame scheduler and one simple transition effect with strict frame/output limits.
6. Add further effects incrementally: fade, scroll, particle systems, and procedural/reactive visualisations.
7. Add animated image sequences only after cancellation, palette handling, timing, resource governance, and terminal cleanup pass acceptance tests.

## Operational constraints

- SIXEL remains explicitly opt-in until reliable capability detection and restoration are demonstrated on supported Termux/terminal combinations.
- Do not infer SIXEL support from truecolour, terminal name, or successful ANSI output.
- Multiplexers such as Zellij may affect graphics protocol passthrough; detect/report uncertainty and provide documented test modes rather than claiming universal support.
- Never emit graphics control sequences into pipes, redirected output, logs, or non-TTY sessions.
- Always restore cursor, attributes, screen mode, and other terminal state on exit, error, interruption, and cancellation.
- Enforce conservative defaults suitable for Android resource and battery constraints.
- Keep visual effects nonessential to filesystem operations, shell access, diagnostics, and recovery.
- Do not modify shell startup files or the installed TERMAX 0.1.0 runtime as part of this work.

## Roadmap implications

- **0.1.4:** scene, layer, effect, capability, and renderer contracts; text fallback; terminal restoration tests.
- **0.1.5:** backend registry, ANSI/Unicode rendering, static scene composition.
- **0.1.6:** explicit opt-in static SIXEL rendering and image conversion adapter.
- **0.1.7:** scene graph, layer compositor, focus and interaction controller.
- **0.1.8:** frame scheduler, bounded redraw, pause/resume/cancel lifecycle.
- **0.1.9:** initial effect API and a small set of low-cost effects.
- **0.2.x:** richer procedural/reactive effects, animated image sequences, advanced dashboards, and additional graphics backends after device-level validation.

## Acceptance criteria

- Scene definitions are backend-independent and validated.
- Unsupported layers/effects degrade to a useful text/ANSI representation.
- Interactive scenes remain keyboard accessible and cancellable.
- Effect lifecycle cleanup runs on normal completion, error, interruption, and cancellation.
- CPU, memory, output bytes, frame rate, and duration are bounded.
- Reduced-motion settings and per-session disable controls work.
- Terminal state is restored under all tested exit paths.
- SIXEL capability is positively verified rather than inferred.
- No graphics output is emitted to redirected/non-TTY streams.
- The core application remains usable with all graphics and effects disabled.

## Status clarification

This document records accepted architectural direction and proposed sequencing. It does **not** claim that the scene graph, effects engine, SIXEL renderer, or animation runtime has been implemented.
