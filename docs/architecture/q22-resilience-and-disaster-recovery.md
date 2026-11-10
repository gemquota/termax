# TERMAX Q22 Decision Record: Unified Resilience and Recovery

Status: accepted architectural direction  
Decision: Q22 selections A, B, H  
Target: 0.1.4 contract foundation and 0.2.x runtime evolution  
Compatibility: existing TERMAX 0.1.0 installation remains protected.

## 1. Accepted priorities

- **A. Transactional recovery and rollback**
- **B. Automated backup and disaster recovery**
- **H. Unified adaptive resilience platform**

The architecture combines transaction-level recovery with independently verifiable backups and system-wide resilience policy. Backup scheduling, retention, and recovery remain user-governed. The system must distinguish a successful backup operation from a backup that has passed integrity and restore validation.

## 2. Proposed architecture

The TERMAX Resilience and Recovery Platform (TRRP) coordinates the following services:

1. **Transaction Journal** records intent, scope, actor, approval, checkpoints, mutation steps, verification evidence, and final outcome.
2. **Checkpoint Manager** creates scoped recovery points before eligible high-risk changes.
3. **Backup Manager** performs on-demand and policy-scheduled backups, tracks retention, and records backup manifests.
4. **Integrity and Verification Service** validates checksums, manifests, database consistency where supported, and restore viability.
5. **Recovery Orchestrator** prepares restore plans, resolves dependencies, previews effects, executes approved recovery, and verifies the result.
6. **Resilience Monitor** observes component health, detects interrupted operations, and recommends safe recovery actions.
7. **Retention and Policy Controller** applies user-defined schedules, exclusions, storage limits, retention windows, and approval requirements.
8. **Recovery Audit Log** preserves the evidence and decisions needed to understand what happened.

The platform integrates with the existing execution governance and security policy layers. It cannot grant itself permissions or bypass approval requirements.

## 3. Transaction lifecycle

Eligible mutations use this lifecycle:

`PREPARE -> PREFLIGHT -> CHECKPOINT -> APPROVE -> EXECUTE -> VERIFY -> COMMIT`

On failure, the transaction enters one of:

- `ROLLBACK_REQUIRED`: reversible operations can be safely reverted.
- `RECOVERY_REQUIRED`: restore from a verified checkpoint is required.
- `COMPENSATION_REQUIRED`: an external or irreversible side effect requires a compensating action.
- `MANUAL_REVIEW`: recovery safety cannot be established automatically.

Every transition is journaled. A transaction is not marked committed until post-change verification succeeds. Recovery itself is a new auditable transaction.

Rollback is not promised for irreversible external effects, remote actions, messages already delivered, or other side effects outside the transaction's control. The system must report residual effects and any required compensation.

## 4. Backup model

Support two initiation modes:

- **On-demand:** user requests a backup or a pre-change checkpoint.
- **Policy-scheduled:** bounded scheduled work runs only when platform conditions permit.

Backup sets are versioned and described by manifests. A manifest records:

- backup and source identifiers;
- creation timestamp and schema version;
- included paths or logical datasets;
- excluded paths and exclusion reasons;
- file sizes and SHA-256 checksums;
- source component versions;
- encryption state and key reference, if a verified encryption adapter is configured;
- retention class and expiry policy;
- validation status and validation timestamp.

A backup is not marked `VERIFIED` solely because copying finished. Validation includes manifest parsing, checksum checks, required-file presence, and restore testing into a separate staging location. Database-specific consistency checks are performed only when the relevant backend supports them.

## 5. Recovery flow

1. Detect and classify the failure or requested restore.
2. Identify candidate recovery points and their validation status.
3. Check compatibility, required dependencies, available storage, and data classification.
4. Generate a restore preview with affected paths, overwrite conflicts, exclusions, and expected residual effects.
5. Obtain the required user approval.
6. Create a pre-recovery checkpoint where feasible.
7. Restore into staging or a separate destination first.
8. Verify checksums, structure, and application-level health.
9. Promote only after verification and approval.
10. Record outcome, evidence, and any unresolved effects.

Default behaviour is preview-first. Never overwrite the active TERMAX 0.1.0 installation or launcher as part of automatic recovery.

## 6. Proposed storage layout

```text
~/.local/share/termax/
  resilience/
    config/
      backup-policy.json
      retention-policy.json
    journal/
      transactions.sqlite3
    manifests/
      backups/
      checkpoints/
    backups/
      objects/
    checkpoints/
      objects/
    staging/
    reports/
    logs/
```

This is a proposed target layout for the new runtime. It must not be created by modifying the protected 0.1.0 installation during design or contract work.

Large backup payloads should be stored separately from manifests and indexes. SQLite stores transaction metadata and recovery state; JSON manifests provide portable, inspectable descriptions. Hashes detect accidental or malicious modification but do not provide confidentiality. Encryption requires a verified adapter and a documented key recovery model.

## 7. Scheduling and Android constraints

Scheduled backups are best-effort, bounded operations. Android may suspend or terminate Termux processes, so:

- no always-on daemon is required;
- jobs persist enough state to detect interruption;
- interrupted backups are marked incomplete and never presented as verified;
- work resumes only when the operation is safe and idempotent;
- CPU, memory, storage, battery, and runtime budgets are configurable;
- user-visible status and explicit on-demand execution remain available;
- backup work must not assume unrestricted background execution.

The default schedule should be conservative and user-configurable. The system should recommend an on-demand checkpoint before high-risk changes even if scheduled backup is disabled.

## 8. Retention, privacy, and integrity

- Exclude credentials, tokens, private keys, and other secrets by default.
- Record exclusions without copying secret values into logs or reports.
- Allow explicit secure-secret backup only through a separate verified mechanism and explicit user action.
- Enforce storage quotas and retention policies without deleting the only known-good recovery point.
- Never prune a recovery point that is referenced by an active transaction.
- Preserve immutable manifests and verify checksums before restore.
- Quarantine corrupt, incomplete, or untrusted backup sets.
- Treat a checksum as integrity evidence, not proof of source authenticity or safety.
- Support export and import with schema validation, provenance, and preview.

## 9. Failure and resilience states

Transaction states include `PREPARED`, `CHECKPOINTED`, `APPROVED`, `EXECUTING`, `VERIFYING`, `COMMITTED`, `ROLLBACK_REQUIRED`, `RECOVERY_REQUIRED`, `COMPENSATION_REQUIRED`, `FAILED`, and `MANUAL_REVIEW`.

Backup states include `QUEUED`, `RUNNING`, `INCOMPLETE`, `VALIDATING`, `VERIFIED`, `QUARANTINED`, `EXPIRED`, and `RESTORED`.

Silence or process termination is never interpreted as success. State transitions must be idempotent or guarded by transaction identifiers and compare-and-set/version checks to avoid duplicate execution.

## 10. Roadmap changes

### 0.1.4 Foundation and contracts
- Define transaction and backup manifest schemas.
- Define recovery and backup state machines.
- Specify checkpoint scope, retention policy, exclusion rules, and integrity evidence.
- Define restore-preview and approval contracts.
- Add interruption and crash-recovery test scenarios.
- Preserve the existing 0.1.0 baseline and document non-destructive staging rules.

### 0.2.0 Core runtime
- Implement transaction journal interfaces and local persistence.
- Implement a basic checkpoint manager for TERMAX-owned staging data.
- Add backup manifest generation and checksum verification.
- Add recovery preview/report generation.
- Keep backup execution on-demand initially; no background daemon dependency.

### 0.2.1 Plugin lifecycle
- Add plugin-owned data declarations and backup/restore hooks.
- Validate plugin backup scope against permissions.
- Prevent plugins from silently excluding or exporting protected data.

### 0.2.2 Developer SDK
- Expose transaction, checkpoint, backup-manifest, integrity, and recovery-preview interfaces.
- Add test fixtures for interrupted and partially completed operations.
- Document idempotency and compensation requirements for extensions.

### 0.2.3 Visual engine
- Show backup progress, validation state, checkpoint history, and recovery status.
- Distinguish incomplete, verified, quarantined, and expired backups visually.
- Preserve plain-text status output.

### 0.2.4 Command palette
- Add guided backup, checkpoint, inspect, verify, and restore-preview workflows.
- Require explicit confirmation before destructive restore or retention changes.

### 0.2.5 Persistent workspaces
- Snapshot project metadata, task references, configuration, Git state, and selected artifacts.
- Integrate workspace snapshots with transaction journal references.
- Preserve user changes and untracked files according to explicit inclusion rules.

### 0.2.6 Android and external integrations
- Add verified Android storage adapters where available.
- Explore optional remote backup targets with explicit network and data-sharing approval.
- Keep remote targets optional and avoid exporting secrets by default.

### 0.2.7 Event engine and automation
- Add bounded scheduled backups and health-triggered checkpoint recommendations.
- Resume only safe, idempotent interrupted jobs.
- Add retention automation with protected recovery-point rules.

### 0.2.8 Agent orchestration
- Allow agents to request checkpoints and prepare recovery plans.
- Agents may not approve their own high-risk recovery actions.
- Use independent verification for restore outcomes and preserve audit provenance.

### 0.2.9 Release candidate
- Test crash interruption, partial copy, corruption, disk exhaustion, permission denial, incompatible manifests, and failed restore.
- Verify retention safety and secret exclusion.
- Conduct independent recovery and security review.
- Block release if recovery can silently overwrite protected user data or report an unverified backup as healthy.

## 11. Acceptance criteria

The resilience foundation is not accepted until tests demonstrate:

- transaction journaling survives process interruption;
- duplicate execution requests do not repeat non-idempotent work;
- incomplete backups cannot be labelled verified;
- checksum mismatch triggers quarantine;
- restore preview identifies conflicts and affected targets;
- restore runs in staging before promotion;
- retention never removes the only protected recovery point;
- secrets are excluded from normal backup and diagnostic output;
- recovery outcomes distinguish rollback, restore, compensation, and manual review;
- existing 0.1.0 installation paths remain untouched.
