# TERMAX Q24 Decision Record: Human Interaction and Interface Platform

Status: accepted architectural direction  
Decision: Q24 selections C, G, H  
Target: 0.1.4 contract foundation and 0.2.x runtime evolution  
Compatibility: existing TERMAX 0.1.0 installation remains protected.

## 1. Accepted priorities

- **C. Adaptive visual layouts** — panels, split views, dashboards, and layouts that respond to terminal dimensions.
- **G. Personalisation and workspace identity** — themes, keymaps, layouts, interaction preferences, and per-project interface settings.
- **H. Unified human interaction layer** — coordinate navigation, command palette, layouts, accessibility, help, notifications, and personalisation in one consistent experience.

The selected direction makes the interface adaptive and configurable without making visual complexity a requirement for core operation. Keyboard and plain-text workflows remain first-class. A project may have a distinct presentation identity, but project configuration cannot grant capabilities or weaken security policy.

## 2. Proposed architecture

The TERMAX Human Interaction Platform (THIP) coordinates these proposed services:

1. **Interaction Coordinator** routes user input and maintains consistent interaction state across terminal surfaces.
2. **Layout Engine** manages panels, split views, tabular regions, dashboards, resizing, and responsive fallback layouts.
3. **Theme and Appearance Manager** resolves colour, typography, symbols, spacing, and motion preferences with terminal capability detection.
4. **Workspace Presentation Profiles** bind permitted visual and interaction preferences to projects and workspaces.
5. **Command Palette Adapter** exposes commands and contextual actions through a consistent discovery and invocation surface.
6. **Notification and Activity Surface** presents task progress, approvals, agent activity, diagnostics, and system events with severity and provenance.
7. **Accessibility and Text Fallback Adapter** preserves readable output, keyboard operation, reduced-motion behaviour, and plain-text alternatives.
8. **Help and Discovery Service** provides contextual documentation and progressively disclosed controls.
9. **Terminal Capability Registry** detects dimensions, colour support, Unicode behaviour, and optional graphics protocols without assuming support from unrelated capabilities.

THIP integrates with the visual engine, command palette, workspace manager, event system, task orchestrator, and configuration manager. It is a presentation and interaction layer, not an execution authority.

## 3. Adaptive layout model

Layouts are composed from named regions and reusable components rather than fixed terminal coordinates. The layout engine should:

- respond to terminal resize events where the host exposes them;
- define minimum useful dimensions for panels and dashboards;
- collapse or reorder regions when space is constrained;
- preserve essential status and interaction controls in compact layouts;
- avoid corrupting command output or stealing terminal input;
- support saved layouts and per-workspace layout preferences;
- fall back to sequential text output when interactive layout support is unavailable.

Proposed layout modes include COMPACT, SPLIT, DASHBOARD, and FOCUS. These are presentation modes, not execution profiles or security boundaries.

## 4. Personalisation and workspace identity

Personalisation settings may include:

- theme and colour palette;
- key bindings and command aliases within supported interfaces;
- panel arrangement and default layout;
- density, spacing, and text presentation;
- reduced-motion and visual-effects preferences;
- notification verbosity and grouping;
- workspace-specific presentation identity.

Configuration follows the established TERMAX configuration precedence. Workspace preferences may override ordinary presentation defaults only within the allowed schema. They cannot override security policy, capability grants, approval requirements, or hard resource limits.

Profiles should be portable, versioned, validated, and previewable before import. Missing themes, unsupported symbols, or unavailable terminal features must degrade gracefully rather than prevent startup.

## 5. Interaction and accessibility requirements

- Keyboard operation remains available for core workflows.
- Interactive surfaces must have predictable focus order and visible focus state.
- Critical state must not be communicated by colour alone.
- Motion and animation can be reduced or disabled.
- Plain-text output remains supported for every essential status and command.
- Terminal dimensions and capability changes must not destroy user input or task state.
- Notifications distinguish informational events from warnings, failures, and approval requests.
- Approval prompts identify the action, target scope, risk, and consequences; they must not be disguised as ordinary notifications.
- The interface never treats visual confirmation as execution authorisation unless the explicit approval workflow records it.

## 6. Proposed contracts

Initial versioned interface records:

- LayoutDefinition: layout ID, schema version, named regions, constraints, component references, and fallback order.
- ThemeProfile: theme ID, palette, contrast metadata, typography preferences, and supported feature requirements.
- WorkspacePresentationProfile: workspace ID, layout/theme references, keymap reference, density, motion, and notification preferences.
- TerminalCapabilities: dimensions, colour depth where detectable, Unicode/character-set observations, and independently detected graphics protocols.
- InteractionEvent: event ID, input source, action, focus target, timestamp, and correlation references.
- NotificationRecord: event reference, severity, source, summary, optional detail reference, expiry, and acknowledgement state.

All imported profiles are untrusted data until validated. Theme and layout files cannot contain executable plugin code or implicit command hooks.

## 7. Roadmap changes

### 0.1.4 Foundation and contracts
- Define layout, theme, workspace presentation, terminal capability, interaction event, and notification schemas.
- Specify responsive breakpoints, minimum region constraints, focus behaviour, and text fallbacks.
- Define presentation configuration precedence and restrictions against weakening security policy.
- Add deterministic tests for malformed profiles, narrow terminal dimensions, missing capabilities, and fallback layouts.
- Preserve existing Zsh, Powerlevel10k, and user shell configuration; do not rewrite startup files.

### 0.2.0 Core runtime
- Implement a small interaction coordinator and text-first layout primitives.
- Add terminal dimension and capability detection with safe unknown states.
- Implement profile loading, validation, and preview without changing the active 0.1.0 installation.
- Keep core commands usable without a full-screen interface.

### 0.2.1 Plugin lifecycle
- Define optional plugin UI contribution points and component metadata.
- Validate UI contributions against supported component contracts.
- Keep plugin UI declarative by default; execution still passes through the capability and policy gateways.

### 0.2.2 Developer SDK
- Expose layout, theme, workspace presentation, notification, and interaction event interfaces.
- Provide fixtures for terminal sizes, unsupported colour/Unicode features, and plain-text rendering.
- Document focus and input ownership rules for extensions.

### 0.2.3 Visual engine
- Integrate adaptive panels, split views, dashboards, theme profiles, and workspace identity.
- Add compact and focus layouts plus resize handling.
- Keep plain-text status and non-interactive rendering available.

### 0.2.4 Command palette
- Integrate contextual commands with the shared interaction model.
- Support keyboard navigation, focus management, and command discovery.
- Keep approval prompts distinct and explicit.

### 0.2.5 Persistent workspaces
- Persist workspace presentation profiles and layout preferences.
- Support export/import with schema validation and preview.
- Keep presentation identity separate from project execution authority and secrets.

### 0.2.6 Android and external integrations
- Detect available terminal and Android capabilities without assuming optional APIs exist.
- Add optional notification adapters only with explicit permission and platform support.
- Preserve a functional terminal-only mode.

### 0.2.7 Event engine and automation
- Route task, agent, diagnostic, and system events into the activity surface.
- Add grouping, acknowledgement, and bounded notification retention.
- Ensure notification handling never silently approves or executes an action.

### 0.2.8 Agent orchestration
- Allow agents to publish progress and request user attention through typed events.
- Keep agent-generated interface content labelled by source and trust.
- Require the normal approval workflow for privileged actions.

### 0.2.9 Release candidate
- Test narrow/wide terminal dimensions, resize interruptions, missing optional capabilities, profile corruption, focus handling, and text fallback.
- Verify critical status is not conveyed by colour alone.
- Verify imported themes/layouts cannot execute code or alter policy.
- Verify no automatic shell startup modification or 0.1.0 replacement occurs.
- Block release if essential workflows become unusable without graphics or if notifications can be mistaken for approvals.

## 8. Acceptance criteria

The Q24 interaction foundation is acceptable only when tests demonstrate:

- layouts adapt to supported terminal dimensions and degrade predictably;
- plain-text mode retains all essential functionality;
- theme and workspace profiles are versioned, validated, and previewable;
- workspace presentation settings cannot weaken security or execution policy;
- terminal capabilities are detected independently rather than inferred;
- keyboard focus and input ownership are predictable;
- critical state is not represented by colour alone;
- notifications cannot grant approval or trigger privileged actions;
- imported presentation profiles cannot execute code;
- the existing TERMAX 0.1.0 installation and shell configuration remain untouched.
