# Q28 — Rust Language Preference for Native Visualisation

**Status:** Preference recorded; implementation scope not yet selected  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** `development/0.1.4-contract-foundation`

## Clarification

The earlier reference to Go was a typo. If TERMAX adds a second implementation language for performance-sensitive native components, **Rust is the user's preferred candidate**.

This is a language preference, not approval to add Rust as a mandatory runtime dependency and not a decision that a native subsystem must be built.

## Design implications to evaluate

- Keep the existing Python runtime as the orchestration and compatibility layer unless a measured workload justifies moving a component.
- Evaluate Rust for performance-sensitive rendering, graph layout, image processing, telemetry aggregation, and other bounded native workloads.
- Prefer a narrow, versioned boundary between Python and Rust. Candidate approaches include a standalone helper process with a structured protocol or a native extension; choose only after measuring build, packaging, debugging, and runtime trade-offs.
- Preserve a pure-Python or text-based fallback for core functionality where practical.
- Treat Termux/Android ARM64 build and distribution constraints as first-class requirements.
- Do not introduce Rust merely for novelty. Establish a benchmark and a concrete capability gap before selecting components for migration.
- Rust must not become a mandatory prerequisite for using the existing TERMAX 0.1.0 installation.

## Open decision

The specific Rust-backed visualisation capabilities and integration model remain open pending the Q28 feature selections and subsequent feasibility work.
