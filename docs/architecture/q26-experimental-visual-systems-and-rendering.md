# Q26 — Experimental Visual Systems and Rendering Architecture

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture foundation  
**Branch:** `development/0.1.4-contract-foundation`

## Decision

The selected priorities are **A, H, F, D, G, C**. All six selections are retained; the three-choice limit was a UI guardrail, not a reason to discard a coherent set of related capabilities.

1. **A — Advanced SIXEL engine:** native SIXEL rendering, image sequences, animation, colour management, terminal capability detection, and graceful fallbacks.
2. **H — Unified visualisation framework:** a pluggable rendering engine with multiple backends and automatic capability detection.
3. **F — Layered graphics compositor:** coordinated composition of SIXEL imagery, text, charts, panels, and animations.
4. **D — Visual filesystem explorer:** rich previews, metadata panels, syntax-aware previews, and interactive file operations.
5. **G — Visual experimentation lab:** isolated experiments for terminal protocols, renderers, animation, performance, and effects.
6. **C — Live visual dashboards:** adaptive real-time views for CPU, memory, storage, battery, network, and processes.

## Architectural direction

Build a unified visualisation framework (working name **TVF — TERMAX Visualisation Framework**) with a capability-aware renderer registry and compositing model. It must not assume that a terminal's colour support implies SIXEL, Kitty graphics, or any other image protocol support.

### Proposed subsystems

- **Capability Detector:** probes terminal identity and supported features conservatively; records evidence, confidence, and probe method.
- **Renderer Registry:** registers text/ANSI, Unicode/box-drawing, SIXEL, and future graphics backends with explicit capability requirements.
- **Scene and Layer Model:** represents panels, text, images, charts, overlays, animation frames, z-order, clipping, and layout constraints.
- **Compositor:** coordinates scene layout and backend output, with deterministic teardown and terminal-state restoration.
- **SIXEL Backend:** handles encoding/decoding boundaries, palette and colour constraints, raster attributes, image placement, frame sequences, and output limits.
- **Dashboard Adapter:** supplies bounded telemetry snapshots and streaming updates to visual components.
- **Explorer Adapter:** exposes safe preview providers for images, text, source code, metadata, and supported document types.
- **Experiment Lab:** runs opt-in renderer/protocol experiments in isolated temporary sessions and records reproducible results.
- **Fallback Planner:** chooses the richest verified backend available, then degrades to ANSI/Unicode/plain text without corrupting terminal state.

## SIXEL engineering requirements

- SIXEL is an explicit backend capability, never inferred from truecolour or terminal branding alone.
- Probe conservatively and avoid emitting disruptive escape sequences into non-interactive output, logs, pipes, or unsupported multiplexers.
- Respect terminal multiplexers and nested sessions; report when a multiplexer may intercept or strip graphics protocols.
- Bound image dimensions, encoded bytes, frame counts, palette sizes, and render time.
- Support static images first; add animation only after frame timing, cleanup, cancellation, and resource budgets are tested.
- Keep image conversion optional and provider-based (for example, Chafa when its build supports SIXEL); missing encoders must produce a clear fallback, not an installation attempt.
- Restore cursor position, attributes, and alternate-screen state on success, error, interruption, and cancellation.
- Never make SIXEL necessary for core navigation or diagnostics.

## Layering and composition

The scene model should separate content from rendering. A chart, image, status panel, or explorer preview should describe its content and constraints; the selected backend determines how it is rendered. Layers need explicit bounds, z-order, clipping, refresh policy, and resource budgets. The first implementation should prefer rectangular regions and deterministic redraw over complicated terminal pixel-coordinate assumptions.

## Live dashboards

Dashboard data is sampled on demand or through bounded user-visible sessions. Telemetry must carry timestamps and availability states; missing data is unknown, not zero. Sampling rates, retained history, and redraw frequency must be capped. Dashboard rendering must not starve interactive input or materially degrade low-resource operation.

## Explorer integration

Preview providers are read-only by default and must not execute files, shell hooks, or embedded content. File operations remain separate explicit actions with preview/confirmation and recoverability. Large or hostile files require size limits and safe truncation. SIXEL previews are optional and must have text/metadata fallbacks.

## Experiment lab

Experiments are opt-in and must:
- run without changing the user's shell startup files or installed 0.1.0 runtime;
- record terminal, multiplexer, device, renderer, encoder, and test conditions;
- provide a safe reset/cleanup path;
- use bounded CPU, memory, output, and duration budgets;
- distinguish a detected capability from a successfully rendered and visually verified capability.

## Compatibility and safety constraints

- Preserve the known-working 0.1.0 installation and current Zsh/Powerlevel10k configuration.
- Do not install optional packages automatically.
- Do not assume Termux:GUI, SIXEL support, or pixel graphics support.
- Do not treat terminal output as a security boundary; previews and imported visual assets are untrusted data.
- No visual component may grant capabilities, approve privileged operations, or conceal critical state.
- Plain-text and keyboard-first operation remain first-class.
- All renderers must support cancellation and terminal-state restoration.

## Delivery sequence

1. **0.1.4:** define renderer, capability, scene, layer, and preview-provider contracts; build protocol detection tests and text fallback.
2. **0.1.5:** implement renderer registry and ANSI/Unicode backend; add terminal-state safety tests.
3. **0.1.6:** implement static SIXEL backend behind explicit opt-in; validate with known test terminals and encoders.
4. **0.1.7:** implement rectangular layer compositor and scene lifecycle.
5. **0.1.8:** integrate explorer preview providers and safe image metadata handling.
6. **0.1.9:** add dashboard widgets and bounded telemetry refresh.
7. **0.2.x:** add animation, richer charts, experiment lab UX, additional graphics protocols, and advanced adaptive layouts after backend-specific acceptance tests.

## Acceptance criteria

- Unsupported or uncertain graphics capability always falls back safely.
- Truecolour detection never counts as SIXEL detection.
- SIXEL output is opt-in until reliable capability detection and restoration are proven.
- Static image rendering is bounded and cancellation-safe.
- Terminal state is restored after normal exit, exceptions, and interruption.
- Layer composition is deterministic and does not corrupt keyboard input.
- Explorer previews are read-only and never execute file content.
- Dashboard sampling and redraw are bounded and degrade under resource pressure.
- Experiment results are reproducible and identify their environment.
- Plain-text operation remains fully usable.
- No changes are made to the installed 0.1.0 runtime as part of this architecture decision.

## Status clarification

This document records accepted architectural direction and a proposed delivery sequence. It does **not** claim that these subsystems have been implemented.
