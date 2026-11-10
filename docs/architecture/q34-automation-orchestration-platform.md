# Q34 — Automation and Orchestration Priorities

**Status:** Accepted direction  
**Milestone:** 0.1.4 architecture exploration  
**Branch:** development/0.1.4-contract-foundation

## Decision

Accepted selections: **H, F, A**.

- **H — Unified orchestration platform:** combine visual workflows, event triggers, specialist agents, adaptive execution, and live monitoring.
- **F — Interactive automation observatory:** inspect workflow execution through live graphs, event streams, execution traces, and resource metrics.
- **A — Visual workflow designer:** construct workflows by connecting commands, events, conditions, and actions in an interactive node graph.

## Product direction

Create a unified, inspectable orchestration platform with a visual-first workflow authoring experience and a live execution observatory. Workflows are versioned declarative definitions. Execution is handled by a bounded runtime that validates capabilities, records provenance, exposes state, and supports cancellation and recovery.

## Proposed architecture

- **Workflow Definition Model:** versioned graph schema for triggers, inputs, conditions, transformations, actions, outputs, error paths, and resource constraints.
- **Visual Workflow Designer:** node-and-edge editor with validation, keyboard navigation, textual inspection, and accessible non-graphical authoring fallback.
- **Workflow Compiler and Validator:** checks graph structure, types, cycles, dependencies, capability requirements, and resource bounds before execution.
- **Orchestration Runtime:** schedules eligible workflow nodes, manages dependencies, concurrency, cancellation, retries, timeouts, and partial failure.
- **Event Trigger Adapter:** subscribes to explicitly enabled Command Observatory, system, workspace, and architecture events.
- **Action and Connector Registry:** exposes approved commands and integration actions through typed, versioned contracts.
- **Capability and Consent Broker:** grants each workflow only the explicitly approved capabilities required for its actions.
- **Execution Journal:** records workflow version, inputs (with secret redaction), node transitions, outputs, provenance, errors, and cancellation state.
- **Automation Observatory:** live graph highlighting, event stream, execution trace, logs, resource metrics, and per-node inspection.
- **Adaptive Scheduler:** selects execution concurrency and resource policy within hard user-defined limits and current device constraints.
- **Agent Adapter Layer:** allows specialist agents to participate as constrained workflow nodes, without bypassing the capability broker.
- **Import, Export and Package Validator:** handles portable workflow definitions with schema checks, provenance, dependency reports, and untrusted-import treatment.

## Workflow semantics

- Workflow definitions are declarative data, not executable plugin code.
- Validate the complete graph and required capabilities before starting actions.
- Require explicit approval for privileged, destructive, external, or irreversible actions.
- Support dry-run/preview for workflows whose actions can be safely simulated.
- Make retries idempotency-aware; never blindly retry a non-idempotent action.
- Bound concurrency, queue depth, execution time, output size, memory, and persistent journal growth.
- Cancellation stops future work and requests cooperative cancellation from active nodes; report actions that cannot be rolled back.
- Persist resumable checkpoints only for workflows whose action semantics support safe recovery.

## Security and trust model

- Imported workflows, agent output, event payloads, and connector data are untrusted.
- No workflow or agent can grant itself capabilities or approve its own privileged actions.
- Shell execution is a separately declared capability, disabled unless explicitly granted for the specific workflow/action.
- Secrets are passed through protected references where supported, not embedded in ordinary workflow exports or logs.
- All actions carry source, approval, and execution provenance.
- Visual editor presentation does not imply trust or permission.
- Default posture is local, on-demand, user-visible execution; remote execution is separately configured and disabled by default.

## Delivery sequence

1. **0.1.4:** define workflow graph, node/action, capability, execution journal, and observability contracts.
2. **0.1.5:** implement text-based workflow schema, validator, and static graph inspection.
3. **0.1.6:** add bounded sequential runtime with cancellation and execution journal.
4. **0.1.7:** add event triggers and Command Observatory integration behind explicit subscriptions.
5. **0.1.8:** add TVF-backed visual workflow designer and live execution graph.
6. **0.1.9:** add resource metrics, adaptive scheduling, import/export validation, and constrained agent-node interface.
7. **0.2.x:** expand concurrency, recovery, specialist-agent adapters, integrations, and workflow package ecosystem.

## Acceptance criteria

- Workflow definitions are versioned, declarative, inspectable, and validated before execution.
- Invalid graphs and missing capabilities prevent execution.
- Visual authoring has a text-based accessible fallback.
- Runtime exposes node state, errors, outputs, and provenance in a live observatory.
- Users can cancel workflows and inspect incomplete or irreversible actions.
- Resource limits are enforced independently of adaptive scheduling.
- Privileged and destructive actions require explicit approval.
- Imported workflows cannot execute during import or validation.
- Agent nodes cannot bypass capability checks or approve their own actions.
- Secrets are excluded from normal exports and redacted from durable logs.
- No changes are made to installed TERMAX 0.1.0 or shell startup files.

## Status clarification

This document records accepted product direction and proposed implementation sequencing. The unified orchestration runtime, visual workflow designer, and automation observatory are not yet implemented.