# Q32 — Architecture Explorer Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** development/0.1.4-contract-foundation

## Decision

Accepted selections: **H, E, G**.

- **H — Unified architecture intelligence:** combine source analysis, dependency graphs, execution traces, runtime topology, and change-impact exploration.
- **E — Automated architecture discovery:** inspect repositories and configuration files to construct architecture maps and identify undocumented relationships.
- **G — Interactive system topology:** combine Android, Termux, shell, filesystem, installed tools, and TERMAX components into one navigable map.

## Product direction

Build the Architecture Explorer as a unified, evidence-backed model of the software and runtime environment. It should discover what can be established from source files, configuration, package metadata, and explicitly collected runtime observations, then present those relationships as navigable maps. It is not merely a directory tree and must not pretend that inferred relationships are verified facts.

## Proposed architecture

- **Discovery Coordinator:** schedules bounded, user-initiated scans of approved roots and records scan scope.
- **Source and Configuration Indexer:** extracts files, symbols, declarations, imports, configuration keys, and references without executing inspected content.
- **Environment Inventory Adapter:** collects supported Android, Termux, shell, filesystem, and installed-tool metadata through read-only probes.
- **Evidence and Provenance Store:** records each observation with source path, timestamp, scanner/version, confidence, and evidence type.
- **Architecture Graph Model:** represents components, files, packages, tools, services, configuration, and relationships in a versioned graph.
- **Relationship Resolver:** distinguishes directly observed edges from inferred or unresolved relationships.
- **Topology View Adapter:** maps the host environment and TERMAX components into interactive, backend-independent TVF scenes.
- **Search and Navigation Service:** supports filtering, symbol lookup, relationship traversal, and source-location navigation.
- **Change Impact Analyzer:** identifies graph neighbours and dependency paths potentially affected by a proposed change; it reports candidates, not guaranteed outcomes.
- **Export and Snapshot Manager:** exports redacted, bounded architecture snapshots and compares snapshots across scans.

## Evidence model

- Every node and edge carries provenance and a status such as OBSERVED, INFERRED, DECLARED, STALE, or UNKNOWN.
- Direct source references and configuration declarations must remain distinguishable from heuristic inferences.
- Missing telemetry or inaccessible paths are UNKNOWN, not evidence of absence.
- Scans record included roots, excluded paths, permissions, errors, and incomplete coverage.
- Runtime topology is a timestamped snapshot, not a claim of continuous monitoring unless an explicit observer is running.

## Safety and privacy

- Discovery is read-only by default and never executes discovered scripts, plugins, build files, or configuration content.
- Filesystem roots are explicitly scoped; symlinks, special files, oversized files, and archive expansion are handled with conservative limits.
- Secrets and sensitive values are redacted before persistence or export; raw environment values are not indexed by default.
- No automatic changes to shell startup files, package installations, service state, or project files.
- Architecture data and imported snapshots are untrusted input and cannot grant capabilities or trigger privileged actions.
- Runtime probes are bounded, visible, cancellable, and compatible with Android background-process constraints.

## Delivery sequence

1. **0.1.4:** define graph, evidence, provenance, scan-scope, and inventory contracts.
2. **0.1.5:** implement read-only repository and configuration discovery with a text-based graph representation.
3. **0.1.6:** add Termux/Android/shell/tool inventory adapters and explicit coverage reporting.
4. **0.1.7:** add graph navigation, search, filtering, and evidence inspection.
5. **0.1.8:** add TVF topology scenes and cross-layer views of host environment and TERMAX components.
6. **0.1.9:** add snapshot comparison and evidence-backed change-impact exploration.
7. **0.2.x:** integrate runtime event traces, richer graph layouts, optional SIXEL rendering, and extensible discovery adapters.

## Acceptance criteria

- A scan is read-only, bounded, cancellable, and reports its scope and incomplete coverage.
- Discovered files and declarations are not executed.
- Every relationship can be inspected with provenance and evidence status.
- Inferred relationships are visibly distinguished from observed relationships.
- The model can represent Android, Termux, shell, filesystem, installed tools, and TERMAX components without conflating their evidence sources.
- Sensitive values are redacted from durable indexes and exports by default.
- Architecture snapshots can be compared without modifying the scanned system.
- Text output remains fully functional; graphical rendering is an optional TVF presentation layer.
- No changes are made to installed TERMAX 0.1.0 or shell startup files.

## Status clarification

This document records accepted product direction and proposed implementation sequencing. Automated discovery, unified topology modelling, architecture graph navigation, and change-impact analysis are not yet implemented.