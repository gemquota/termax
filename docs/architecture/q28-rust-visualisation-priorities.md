# Q28 — Rust Visualisation Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** `development/0.1.4-contract-foundation`

## Decision

Accepted selections: **D, E, H**.

- **D — Native terminal UI engine:** high-performance interactive panels, dashboards, charts, and keyboard navigation.
- **E — SIXEL graphics bridge:** Rust-generated raster frames, image processing, and visual assets for the TERMAX compositor.
- **H — Unified Rust toolkit:** a modular native subsystem combining graph processing, rendering, telemetry, and visualisation.

The earlier Go reference was a typo. Rust is the preferred candidate if TERMAX adds a second implementation language. This decision selects capability priorities, not a mandatory Rust dependency or an immediate rewrite.

## Proposed native subsystem

Working name: **TRV (TERMAX Rust Visualisation)**.

TRV should be a modular native toolkit behind a narrow, versioned boundary. It should provide reusable primitives to the Python orchestration layer rather than duplicate the whole TERMAX application.

### Initial modules

1. **Terminal UI Core:** layout primitives, panels, tables, charts, keyboard event handling, focus, resize handling, and accessible text fallback.
2. **Raster and Image Pipeline:** bounded image decoding, scaling, cropping, quantisation, dithering, palette preparation, and frame generation.
3. **SIXEL Bridge:** encode raster frames and scene assets for the TVF compositor; report protocol/backend constraints and failures.
4. **Visualisation Primitives:** graph layout, timeline data, chart geometry, and reusable scene structures.
5. **Telemetry Adapter:** accept bounded, timestamped telemetry snapshots from Python; do not independently collect privileged or hidden system data.
6. **Interop Layer:** versioned message schemas and a stable interface for Python-to-Rust calls.

## Integration principles

- Keep Python as the orchestration, configuration, plugin, and integration layer.
- Evaluate a standalone helper process with structured messages against a native extension only after measuring packaging, performance, debugging, and failure-isolation trade-offs.
- Keep Rust optional during early adoption; core TERMAX operation and text fallback must remain usable without a Rust binary.
- Do not migrate functionality merely to increase the number of languages.
- Benchmark the target workload on Termux ARM64 before claiming a performance advantage.
- Avoid unbounded copies of large image buffers across the Python/Rust boundary.
- Version the interop protocol and reject incompatible messages safely.
- No native module may bypass capability policy or grant permissions.

## Termux and Android constraints

- ARM64 Termux build and execution are primary compatibility targets.
- Build tooling, binary size, startup latency, memory footprint, and distribution/update strategy must be measured.
- Native crashes must not corrupt shell state or the Python orchestration process where process isolation is selected.
- The Rust component must respect Android resource pressure and bounded execution.
- Preserve the installed TERMAX 0.1.0 runtime; do not make Rust a prerequisite for it.

## Delivery sequence

1. Define interop schemas and benchmark cases.
2. Prototype a minimal Rust executable that accepts a bounded scene/raster request and returns deterministic output or a SIXEL payload.
3. Compare subprocess and extension integration approaches using real Termux ARM64 measurements.
4. Implement one terminal UI primitive and one raster pipeline operation.
5. Integrate the SIXEL bridge with TVF's backend registry and fallback planner.
6. Expand into charts, graphs, dashboards, and richer terminal UI only after acceptance tests.

## Acceptance criteria

- Python-only operation remains supported.
- Rust interface is versioned and validates all input sizes and fields.
- Native failures are contained and produce actionable diagnostics.
- ARM64 build and runtime behaviour are verified on Termux.
- Image and frame processing enforce memory, dimensions, and time limits.
- SIXEL output is emitted only when the capability has been verified and the user has enabled it.
- Text/ANSI fallback remains functional.
- Performance claims include reproducible baseline measurements.
- No changes are made to the installed 0.1.0 runtime as part of this decision.

## Status clarification

This document records accepted priorities and a proposed architecture. TRV is not yet implemented, and no choice between subprocess and native-extension integration has been finalized.
