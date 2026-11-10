# TERMAX Q23 Decision Record: Adaptive Performance and Resource Management

Status: accepted architectural direction  
Decision: Q23 selections A, C, H  
Target: 0.1.4 contract foundation and 0.2.x runtime evolution  
Compatibility: existing TERMAX 0.1.0 installation remains protected.

## 1. Accepted priorities

- **A. Adaptive resource management** — dynamically manage CPU, memory, storage, battery, and concurrency in response to device conditions.
- **C. Performance profiling and diagnostics** — measure startup time, command latency, memory use, bottlenecks, and component overhead.
- **H. Unified adaptive performance platform** — coordinate resource observation, profiling, scheduling policy, storage efficiency, and runtime adaptation through one coherent platform.

The implementation priority is dependable measurement and safe adaptation, not speculative optimisation. TERMAX must explain why it changes a workload limit or recommends an action. Resource controls must remain bounded, reversible where possible, and subordinate to user and security policy.

## 2. Proposed architecture

The TERMAX Adaptive Performance Platform (TAPP) coordinates these proposed services:

1. **Resource Monitor** samples CPU load, memory pressure, free storage, battery state when available, and active workload counts.
2. **Performance Profiler** measures startup duration, command and task latency, memory footprint, component overhead, and selected I/O timings.
3. **Resource Policy Manager** applies configured budgets and device-aware operating limits. It cannot weaken security policy or override explicit user limits.
4. **Workload Coordinator** consumes resource budgets and task priority metadata to avoid unsafe contention. Advanced scheduling remains dependent on the later task/worker runtime.
5. **Storage Efficiency Service** reports cache, index, artifact, and database usage and prepares maintenance recommendations. Destructive cleanup requires preview and approval.
6. **Adaptive Runtime Controller** selects conservative operating modes when pressure is detected and records the reason, inputs, and resulting limits.
7. **Performance Diagnostics Reporter** correlates measurements, identifies likely bottlenecks, and produces reproducible reports.
8. **Telemetry and Retention Controller** bounds sampling frequency, history size, and storage overhead.

TAPP integrates with the task/worker contracts, observability system, configuration resolver, execution governance, and resilience platform. It is not an authority source: security policy, capability grants, and user approvals remain independent.

## 3. Resource model and operating modes

Initial resource dimensions:

- CPU utilisation and available processing capacity.
- Resident memory and memory-pressure indicators available to the process.
- Free storage, configured quotas, and estimated write requirements.
- Battery state and power-saving signals only where reliable platform data exists.
- Active task count, worker count, concurrency, and expected workload cost.
- Runtime duration and user-configured execution budgets.

Proposed operating modes:

- **NORMAL** — use configured defaults within current budgets.
- **CONSERVATIVE** — reduce concurrency and defer nonessential work under pressure.
- **LOW_RESOURCE** — prioritise core interactive responsiveness and suspend optional expensive work.
- **RECOVERY** — reserve resources for integrity checks, journal inspection, and bounded recovery tasks.
- **USER_PINNED** — respect an explicit user-selected profile unless doing so would violate a hard safety or platform constraint; report any unavoidable limitation.

Mode changes must be observable and explainable. Hysteresis or equivalent stabilisation prevents rapid mode-flapping when measurements hover near thresholds. Missing or unreliable telemetry must not be treated as proof that resources are plentiful.

## 4. Profiling and diagnostics rules

- Establish baseline measurements before claiming an optimisation improved performance.
- Use monotonic timing for durations and wall-clock timestamps for human-readable reports.
- Record measurement method, sampling interval, runtime version, device context when available, and confidence/limitations.
- Separate measured facts from inferred bottlenecks and recommendations.
- Keep profiling opt-in or bounded where it could add noticeable overhead.
- Redact secrets and avoid collecting command arguments or file contents unless explicitly required and approved.
- Support text reports first; visual dashboards are a later presentation layer.
- Compare like-for-like runs and disclose environmental differences.
- Do not promise precise battery or system-wide CPU telemetry when Android/Termux does not expose reliable measurements.

## 5. Safety and resource governance

- Hard limits from security policy and user configuration take precedence over adaptive recommendations.
- The adaptive controller may reduce resource use automatically within an approved policy envelope.
- Increasing concurrency, expanding storage use, enabling network transfer, or extending execution time must respect existing approvals and budgets.
- Cleanup is preview-first; caches may be recreated, but user data and the only known-good backup are never treated as disposable cache.
- Profiling and monitoring must have their own CPU, memory, storage, and sampling budgets.
- If telemetry fails, use conservative configured defaults and report degraded observability.
- Android background execution remains best-effort and bounded; no always-on daemon is required.

## 6. Initial contracts and data

Proposed versioned records:

- ResourceSnapshot: timestamp, source, available measurements, units, sampling metadata, confidence, and missing-field reasons.
- ResourceBudget: task/profile scope, CPU and memory limits where enforceable, storage ceiling, concurrency ceiling, runtime deadline, and policy provenance.
- PerformanceSample: operation identifier, duration, resource observations, runtime/build identity, and measurement method.
- PerformanceReport: baseline reference, sample window, findings, confidence, limitations, and recommendations.
- AdaptiveModeDecision: previous and selected mode, triggering evidence, policy constraints, effective limits, and decision timestamp.

Unknown measurements remain unknown; they are not silently filled with guessed values. Schema validation and deterministic tests are required before runtime consumers act on these records.

## 7. Roadmap changes

### 0.1.4 Foundation and contracts
- Define resource snapshot, resource budget, performance sample, performance report, and adaptive mode decision schemas.
- Specify measurement units, missing-data semantics, sampling limits, and provenance.
- Define operating-mode transitions, hysteresis, hard-limit precedence, and conservative fallback behaviour.
- Add deterministic tests for invalid measurements, missing telemetry, budget precedence, mode transitions, and report redaction.
- Document which Android/Termux metrics are available versus optional or unavailable.
- Preserve the 0.1.0 installation and keep profiling/monitoring opt-in during early implementation.

### 0.2.0 Core runtime
- Implement lightweight local resource snapshots and bounded performance timing.
- Add configurable resource budgets and conservative operating modes.
- Persist only bounded, redacted performance history.
- Expose text diagnostics and explainable recommendations.

### 0.2.1 Plugin lifecycle
- Allow plugins to declare estimated resource requirements and optional profiling hooks.
- Enforce per-plugin budgets through the execution gateway where enforceable.
- Prevent plugin telemetry from bypassing redaction, retention, or capability policy.

### 0.2.2 Developer SDK
- Expose resource snapshot, budget inspection, timing, and report APIs.
- Provide deterministic test fixtures for resource pressure and missing telemetry.
- Document measurement overhead and the limits of process-level resource enforcement.

### 0.2.3 Visual engine
- Add optional resource and performance dashboards.
- Distinguish measured values, estimates, unavailable metrics, and recommendations.
- Keep plain-text output fully supported.

### 0.2.4 Command palette
- Add commands to inspect current budgets, profile selected operations, view reports, and choose supported operating modes.
- Require confirmation for actions that increase resource consumption or perform cleanup.

### 0.2.5 Persistent workspaces
- Track workspace-level cache and artifact usage.
- Attribute measurements to project/workspace tasks where reliable.
- Keep cleanup preview-first and protect user changes and recovery points.

### 0.2.6 Android and external integrations
- Add optional Android telemetry adapters only when the relevant API is present and permission is granted.
- Treat battery, thermal, and system-wide metrics as unavailable unless verified on the device.
- Keep remote profiling and telemetry export disabled unless explicitly configured.

### 0.2.7 Event engine and automation
- Publish resource-pressure and performance events.
- Permit bounded adaptive responses such as lowering concurrency or deferring optional work.
- Add resource-aware scheduling policies after task and worker contracts are implemented.

### 0.2.8 Agent orchestration
- Let agents request profiles and inspect resource reports within granted scope.
- Allow agents to recommend tuning but not bypass budgets or security policy.
- Require independent verification for claimed performance improvements.

### 0.2.9 Release candidate
- Test memory pressure, low storage, interrupted profiling, noisy measurements, telemetry loss, and mode-flapping.
- Verify profiling overhead remains within configured limits.
- Verify no adaptive action exceeds policy or user budgets.
- Compare benchmark baselines and publish limitations.
- Block release if monitoring leaks secrets, cleanup can damage user data, or performance claims lack reproducible evidence.

## 8. Acceptance criteria

The Q23 performance foundation is acceptable only when tests demonstrate:

- missing or unreliable metrics are represented explicitly;
- resource budgets cannot be weakened by adaptive logic;
- mode transitions are deterministic and do not oscillate under noisy inputs;
- profiling records measurement method and runtime context;
- monitoring overhead is bounded;
- diagnostic output is redacted;
- cleanup cannot silently remove user data or protected recovery points;
- low-resource mode preserves core interactive functionality;
- performance improvements are supported by comparable measurements;
- the existing 0.1.0 installation remains untouched.
