# Q29 — TERMAX Signature Visual Experience

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** `development/0.1.4-contract-foundation`

## Decision

Accepted priorities: **H, A, D**.

- **H — Unified TERMAX Visual Workspace:** a configurable environment combining observability, diagrams, simulations, graphics, dashboards, and interactive scenes.
- **A — TERMAX Command Observatory:** a live command centre for running commands, process trees, resource consumption, execution timelines, and activity streams.
- **D — Visual Code and Architecture Explorer:** interactive exploration of source trees, call graphs, dependencies, execution paths, and module relationships.

The unified workspace is the overall experience; the Command Observatory and Architecture Explorer are flagship applications within it.

## Product concept

TERMAX should provide a cohesive, keyboard-first visual workstation that can move between operational observability and software architecture exploration without sacrificing the reliability and composability of its terminal foundation.

The workspace is not a replacement shell. It is a presentation and interaction layer over existing commands, tools, and TERMAX services.

## Proposed workspace model

- **Workspace Shell:** manages panels, tabs, split layouts, focus, navigation, and workspace profiles.
- **Command Observatory:** displays command lifecycle, exit status, duration, output streams, and explicitly permitted process/resource telemetry.
- **Process and Resource Views:** render process relationships and bounded CPU, memory, storage, battery, and network snapshots.
- **Architecture Explorer:** indexes project structure and renders dependency relationships, module maps, call graphs, and event flows where evidence is available.
- **Scene Host:** embeds TVF scenes, SIXEL content, charts, and visual effects using backend capability detection.
- **Activity Timeline:** presents timestamped command, task, and system events with filtering and retention controls.
- **Context Inspector:** displays details for the selected process, command, file, module, dependency, or graph node.
- **Workspace Profiles:** persist layout and presentation preferences without granting capabilities or changing security policy.

## Command Observatory requirements

- Command events must distinguish observed lifecycle facts from inferred process relationships.
- Command output remains available in ordinary terminal form; visualisation is supplementary.
- Process inspection is read-only by default. Termination or signal actions require a separate explicit user action and confirmation.
- Resource metrics include timestamps, source, and availability state; missing metrics are not treated as zero.
- Output capture and history are bounded and redact configured sensitive data.
- No background daemon is required for the initial implementation. Sessions are on-demand, visible, and recoverable.

## Architecture Explorer requirements

- Distinguish parsed source facts, static-analysis results, runtime observations, and inferred relationships.
- Show provenance and confidence for generated relationships; do not invent call edges when static analysis cannot establish them.
- Support large repositories through incremental indexing, filtering, and bounded graph rendering.
- Treat source files and project metadata as untrusted input. Indexing must not execute project code.
- Preserve text-based navigation and exportable graph data when visual protocols are unavailable.

## Technology boundaries

- Python remains responsible for orchestration, configuration, command integration, and service coordination.
- TVF provides backend-independent scenes, layers, and rendering lifecycle.
- TRV is the optional Rust companion for performance-sensitive terminal UI, raster processing, and visualisation primitives, subject to measured benefit.
- SIXEL is an optional visual backend, never a prerequisite for the workspace.
- Text/ANSI/Unicode modes remain complete and usable.
- No feature may infer permission from visibility or from a workspace profile.

## Delivery sequence

1. **0.1.4:** define workspace, panel, activity event, command lifecycle, and architecture graph contracts.
2. **0.1.5:** implement a text-first workspace shell and static panel layout.
3. **0.1.6:** add command activity capture and bounded execution timeline.
4. **0.1.7:** add read-only process/resource views with provenance.
5. **0.1.8:** add project indexing and architecture graph data model.
6. **0.1.9:** add text/ANSI graph explorer and evidence-labelled relationships.
7. **0.2.x:** integrate TVF scenes, SIXEL rendering, TRV acceleration where justified, richer dashboards, workspace profiles, and interactive graph layouts.

## Acceptance criteria

- Core shell and command workflows remain usable without the visual workspace.
- Workspace panels are keyboard accessible and adapt to terminal dimensions.
- Command lifecycle and resource observations include provenance and timestamps.
- Process and architecture relationships distinguish facts from inference.
- Sensitive output handling and history retention are bounded and configurable.
- Process controls are not triggered by passive selection or visualisation.
- Source indexing never executes project code.
- Graphics backends are capability-gated and optional.
- Low-resource mode can disable expensive updates and effects.
- Workspace profiles cannot grant capabilities or weaken security policy.
- Existing TERMAX 0.1.0 installation and user shell configuration remain untouched.

## Status clarification

This document records accepted product direction and a proposed delivery sequence. The workspace, Command Observatory, and Architecture Explorer are not yet implemented.
