# TERMAX Q25 Decision Record: Interoperability and Integration Platform

Status: accepted architectural direction  
Decision: Q25 selections C, H, A  
Target: 0.1.4 contract foundation and 0.2.x runtime evolution  
Compatibility: existing TERMAX 0.1.0 installation remains protected.

## 1. Accepted priorities

- **C. Import, export and portability** — move projects, configurations, memory, artifacts, and workspace data between environments.
- **H. Unified interoperability platform** — coordinate APIs, developer tools, portability, remote connectivity, events, integration discovery, and standards.
- **A. Unified integration API** — provide consistent interfaces for external services, local tools, plugins, and TERMAX subsystems.

The accepted direction prioritises portable data and stable contracts before building a large catalogue of integrations. Integrations must be replaceable, explicitly configured, and governed by the existing capability and execution policy layers. Interoperability must not become a back door around security controls.

## 2. Proposed architecture

The TERMAX Interoperability and Integration Platform (TIIP) coordinates these proposed services:

1. **Integration API Gateway** provides versioned, documented interfaces for local tools, plugins, external services, and TERMAX subsystems.
2. **Adapter Registry** records adapter identity, version, supported protocol, compatibility, dependencies, declared capabilities, trust state, and lifecycle.
3. **Import and Export Manager** handles portable project, workspace, configuration, memory, and artifact bundles with manifests and schema validation.
4. **Portability and Migration Engine** maps source formats to target formats, reports unsupported fields and lossy transformations, and previews changes before import.
5. **Protocol and Format Adapters** implement narrowly scoped integrations for documented open formats and protocols.
6. **Remote Connectivity Broker** manages explicitly configured remote endpoints and worker connections, with authentication, scope, and data-transfer consent.
7. **Integration Event Bridge** translates approved external events into typed TERMAX events and applies deduplication, validation, rate limits, and provenance.
8. **Compatibility and Contract Validator** checks API versions, schemas, adapter compatibility, and migration requirements before activation.
9. **Integration Audit and Health Monitor** records lifecycle actions, connection state, transfer summaries, failures, and policy decisions without storing secret values.

TIIP is an interoperability layer, not an authority source. Every adapter operation that accesses files, executes processes, uses network access, reads secrets, or dispatches workers must pass through the capability broker and execution governance layer.

## 3. Unified integration API

The API should expose stable contracts for:

- adapter discovery and metadata;
- capability and permission declarations;
- connection configuration and health checks;
- typed request/response operations;
- event subscription and publication;
- import/export and migration previews;
- artifact references and transfer;
- lifecycle operations such as validate, enable, disable, update, and remove.

API versions are explicit. Consumers reject unsupported major versions and may accept compatible minor versions according to declared compatibility rules. Adapters cannot silently expand their declared capabilities during an update; changed permissions require renewed validation and approval.

## 4. Portability and data exchange

Portable bundles should be self-describing and independently verifiable. A proposed bundle manifest records:

- bundle identifier and schema version;
- source TERMAX/runtime and adapter versions;
- creation timestamp;
- included logical datasets and paths;
- excluded items and exclusion reasons;
- artifact sizes and checksums;
- data classifications and retention metadata;
- migration requirements and known compatibility constraints;
- integrity validation status.

Import is preview-first. The preview reports conflicts, unsupported fields, schema migrations, path mapping, data classification, and potentially lossy transformations. Import must not overwrite active user data without explicit approval and a recoverable plan.

Export excludes credentials, tokens, private keys, and other secrets by default. Secret transfer, if ever supported, belongs to a separate verified mechanism with explicit user action and a documented key recovery model. A checksum establishes integrity evidence, not confidentiality or source authenticity.

Portable formats should favour documented, inspectable structures such as JSON and Markdown where suitable, alongside binary artifacts with manifests. TERMAX must preserve unknown fields when safe and report when a conversion cannot preserve them.

## 5. Remote and event integration boundaries

Remote connectivity is optional and disabled until configured. Before data leaves the device, TERMAX identifies the destination, data scope, purpose, and required capabilities. Authentication material is held by the secret-management boundary and excluded from logs and portable bundles.

External events are untrusted input. The event bridge validates schemas, source identity, replay/deduplication identifiers, size limits, and rate limits. An incoming event may create a task request or notification, but it cannot directly approve privileged actions or bypass policy evaluation.

Network adapters must support bounded timeouts, cancellation, retry rules, and explicit handling of partial transfer. Retries are allowed only when the operation is safe or carries an idempotency key.

## 6. Trust, lifecycle and compatibility

Proposed adapter lifecycle:

DISCOVERED -> VALIDATED -> STAGED -> ENABLED -> DISABLED -> REMOVED

Additional states include QUARANTINED, INCOMPATIBLE, and REVOKED.

Validation includes manifest/schema checks, API compatibility, dependency inspection, declared capability review, provenance/signature checks where available, and staging tests. A signature supports publisher/integrity verification relative to a key; it does not prove that adapter code is safe.

Adapters are isolated by policy and execution scope. A subprocess or Proot environment is not represented as a strong operating-system sandbox on ordinary Termux. Remote workers require endpoint authentication and explicit data-sharing approval.

## 7. Roadmap changes

### 0.1.4 Foundation and contracts
- Define adapter manifest, integration API envelope, portable bundle manifest, migration preview, and external event schemas.
- Specify API versioning, compatibility rules, capability declarations, and adapter lifecycle states.
- Define import/export exclusion defaults, data classification, integrity evidence, and lossy-migration reporting.
- Add deterministic tests for malformed bundles, checksum mismatch, unsupported schemas, unknown fields, and capability escalation attempts.
- Preserve 0.1.0 data and shell configuration; do not activate unreviewed adapters.

### 0.2.0 Core runtime
- Implement the minimal versioned integration API and adapter registry.
- Add local adapter discovery and validation without automatic execution.
- Implement portable manifest generation and read-only import previews.
- Keep network integrations optional and disabled by default.

### 0.2.1 Plugin lifecycle
- Connect plugin lifecycle to adapter validation, staging, trust state, and capability declarations.
- Require renewed permission review when an update changes declared capabilities.
- Add quarantine and rollback paths for incompatible or failed adapters.

### 0.2.2 Developer SDK
- Expose typed adapter interfaces, API version negotiation, event envelopes, and portability hooks.
- Provide test fixtures for protocol errors, partial transfers, duplicate events, and schema migrations.
- Document idempotency, timeouts, cancellation, provenance, and capability requirements.

### 0.2.3 Visual engine
- Show adapter health, trust state, version compatibility, and transfer validation.
- Distinguish configured, connected, enabled, quarantined, and unavailable states.
- Preserve plain-text diagnostics.

### 0.2.4 Command palette
- Add guided adapter inspection, connection configuration, export, import preview, and migration review.
- Require explicit approval for activation, remote transfer, and overwrite operations.

### 0.2.5 Persistent workspaces
- Add portable workspace bundles covering selected metadata, configuration, Git references, and artifact manifests.
- Preserve user changes, untracked files, and exclusions through explicit inclusion rules.
- Support cross-device restore previews without assuming identical paths or dependencies.

### 0.2.6 Android and external integrations
- Add optional platform adapters only when APIs and permissions are verified.
- Add authenticated remote endpoints with explicit network and data-sharing consent.
- Keep local-first operation fully functional without remote connectivity.

### 0.2.7 Event engine and automation
- Add validated event bridges, subscriptions, deduplication, and bounded retry policies.
- Ensure external events can request work but cannot authorise privileged actions.
- Add audit and health signals for adapter failures and partial operations.

### 0.2.8 Agent orchestration
- Allow agents to discover compatible adapters and prepare integration plans within their granted scope.
- Require policy approval for data export, remote dispatch, secret access, or adapter activation.
- Preserve provenance for externally sourced data and independently verify imported artifacts.

### 0.2.9 Release candidate
- Test corrupted and incompatible bundles, interrupted exports/imports, partial remote transfers, replayed events, revoked credentials, and adapter update permission changes.
- Verify secret exclusion, data classification, migration previews, and recovery from failed imports.
- Verify no integration bypasses capability checks, approval, audit, or transaction handling.
- Block release if imports can silently overwrite user data or untrusted events can trigger privileged execution.

## 8. Acceptance criteria

The Q25 interoperability foundation is acceptable only when tests demonstrate:

- APIs are versioned and reject unsupported major versions;
- adapters cannot self-grant or silently expand capabilities;
- portable bundles are self-describing and integrity-checked;
- import previews expose conflicts and lossy transformations;
- secrets are excluded from normal export and diagnostics;
- interrupted transfers are not reported as successful;
- external events are validated, deduplicated, and treated as untrusted;
- remote data transfer requires explicit scope and consent;
- unknown fields are preserved when safe or reported as unsupported;
- the existing TERMAX 0.1.0 installation and user data remain untouched.
