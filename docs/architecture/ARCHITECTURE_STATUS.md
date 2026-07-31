# Julia Agent Architecture Status

> Status: Frozen Architecture Constitution  
> Current Baseline: `phase-f4.3-pre-complete`  
> Main Commit Baseline: `c1426d8`  
> Date: 2026-07-31

## 1. Architecture Identity

`julia_agent` is a **general-purpose Agent Runtime architecture**.

It is not a financial-only agent.

```text
Julia Agent = General Agent OS
Financial = First Production Domain Provider
```

## 2. Frozen Principles

### 2.1 Single Context Authority

Julia Context OS is the single model-visible context authority.

No domain may own its own Context OS.

### 2.2 Domain Provider Isolation

Domain providers provide:

- facts;
- evidence;
- capability results;
- domain object references;
- domain governance metadata.

Domain providers do not own:

- Context lifecycle;
- Memory lifecycle;
- Learning loop;
- prompt assembly;
- token budget;
- Julia identity;
- Julia action governance.

### 2.3 Evidence-driven Capability

All domain conclusions that enter Julia-facing outputs must preserve evidence identity.

Financial domain uses `EvidenceRef`. Future domains must define equivalent evidence references or map to Julia `ContextBlock.evidence_ids` / `source_refs`.

### 2.4 Workbench Action Contract

Application surfaces carry intent pointers and object references, not large context payloads.

Correct:

```json
{
  "action": "ask_why",
  "object_type": "theme",
  "object_id": "9043089"
}
```

Incorrect:

```json
{
  "theme": {},
  "events": [],
  "stocks": [],
  "evidence": []
}
```

### 2.5 No Domain-owned Context OS

Financial, healthcare, coding, and personal assistant domains must integrate through Domain Provider interfaces.

## 3. Current Domains

| Domain | Status | Notes |
|---|---|---|
| Financial | First Production Domain Provider | Backed by `ai_theme_app` / analyst gateway contracts. |
| Healthcare | Future possible domain | Not implemented. Must use Domain Provider model. |
| Coding | Future possible domain | Not implemented. Must use Domain Provider model. |
| Personal Assistant | Future possible domain | Not implemented. Must use Domain Provider model. |

## 4. Branch Strategy

| Branch | Status | Meaning |
|---|---|---|
| `main` | Frozen Production Baseline | Approved docs/contracts/runtime slices only. |
| `codex/full-agent-architecture-migration` | DO NOT MERGE | Architecture evaluation snapshot only. |
| future `codex/a*/...` | Migration candidates | Small architecture-governed migrations only. |

## 5. Migration Status

Runtime migration from the full snapshot is:

```text
NOT STARTED
```

Current next phase:

```text
A1 — Runtime Boundary Audit & Architecture Inventory
```

Future planned phases:

```text
A2 Context OS Core Migration
A3 Domain Provider Interface
A4 Financial Provider Binding
A5 Workbench Context Actions
A6 Voice Adapter
```

## 6. Review Gate

Any future PR must declare which layer it touches:

1. Julia Core;
2. Domain Provider;
3. Application Surface;
4. Runtime Artifact;
5. Private / Local Data.

PRs that introduce domain-owned context planning, prompt assembly, memory lifecycle, or token budgeting violate the architecture constitution.
