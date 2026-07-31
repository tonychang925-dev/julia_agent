# Phase 3.7.5.1 — Context Provenance Runtime Report

Date: 2026-07-29
Status: APPROVED / FROZEN
Scope: block-level provenance, lineage validation, exclusion trace, inference labeling, audit serialization

## 1. Objective

Every context block that enters JuliaContext / Context Assembly must be able to answer:

```text
来自哪里？
谁说的？
什么时候说的？
为什么被选中？
谁注入的？
权限多高？
有没有经过推断？
```

Main chain:

```text
Raw Source
   ↓
Retrieval / Projection
   ↓
Provenance Builder
   ↓
Provenance Validation
   ↓
Context Block
   ↓
JuliaContext
```

## 2. Implemented Modules

```text
runtime/context_os/provenance/
├── provenance_type.py
├── provenance_record.py
├── provenance_chain.py
├── provenance_builder.py
├── provenance_validator.py
├── provenance_decision.py
├── provenance_audit.py
└── __init__.py
```

Integrated:

```text
runtime/evidence/semantic_retriever.py
```

Tests:

```text
tests/test_phase3751_context_provenance_runtime.py
```

## 3. Core Objects

### ContextSourceType

Frozen v1 source types:

```text
CURRENT_USER
RECENT_TRANSCRIPT
CONVERSATION_ARCHIVE
SESSION_STATE
TASK_STATE
COMPACT_STATE
GOVERNED_MEMORY
CLAUDE_DIARY
RUNTIME_INFERENCE
PROVIDER_OUTPUT
```

### ContextProvenanceRecord

```python
@dataclass(frozen=True)
class ContextProvenanceRecord:
    provenance_id: str
    context_block_id: str
    source_type: str
    source_id: str
    source_version: str | None
    speaker: str | None
    authority: float
    confidence: float
    retrieval_reason: tuple[str, ...]
    injection_reason: str
    injected_by: str
    current_task_relevance: float
    cognitive_scope: str | None
    created_at: str
    decision: str = "included"
    exclusion_reason: str | None = None
    excluded_domains: tuple[str, ...] = ()
    inferred: bool = False
```

### ContextProvenanceChain

Serializable chain of included/excluded provenance records.

### ProvenanceBuilder

Builds records for:

- current Tony input;
- ranked semantic evidence;
- exclusion decisions;
- runtime inference.

Important boundary:

```text
Provenance records authority. It does not raise authority.
```

### ProvenanceValidator

Validates:

- required fields;
- source type correctness;
- provider output cannot speak as Tony;
- runtime inference must be labeled `RUNTIME_INFERENCE`;
- current user must be Tony.

## 4. Semantic Evidence Integration

`SemanticContextRetriever.prompt_section()` now emits:

```json
{
  "provenance_chain": {},
  "provenance_validation": {}
}
```

Each ranked evidence source gets provenance with:

```text
source_type
source_id
speaker
authority
confidence
retrieval_reason
injection_reason
injected_by
current_task_relevance
cognitive_scope
```

## 5. Acceptance Results

| TC | Description | Status |
| --- | --- | --- |
| TC-3751-001 | Current User Authority | PASS |
| TC-3751-002 | Archive Lineage | PASS |
| TC-3751-003 | Governed Memory Lineage | PASS |
| TC-3751-004 | Provider Output Isolation | PASS |
| TC-3751-005 | Runtime Inference Label | PASS |
| TC-3751-006 | Exclusion Trace | PASS |
| TC-3751-007 | Compact Lineage | PASS |
| TC-3751-008 | Resurrection Lineage | PASS |
| TC-3751-009 | Provider Independence | PASS |
| TC-3751-010 | Audit Serialization | PASS |
| TC-3751-011 | Semantic Retriever emits provenance chain | PASS |

## 6. Verification

### Targeted

```bash
python3 -m unittest -v tests.test_phase3751_context_provenance_runtime
```

```text
Ran 11 tests in 0.366s
OK
```

### Context / E2E Key Regression

```bash
python3 -m unittest -v \
  tests.test_phase3751_context_provenance_runtime \
  tests.test_e2e_alpha_input_and_routing_fixes \
  tests.test_action_e2e_alpha_runtime \
  tests.test_phase361015_context_os_integration_benchmark \
  tests.test_phase35_context_compiler
```

```text
Ran 32 tests in 2.102s
OK
```

### Full Regression

```bash
python3 -m unittest discover -s tests
```

```text
Ran 451 tests in 57.124s
OK
```

## 7. Boundary Guarantees

### Current User vs Provider Output

PASS. `CURRENT_USER` and `PROVIDER_OUTPUT` are distinct authority classes. Provider output cannot be validated as Tony evidence.

### Runtime Inference Labeling

PASS. Runtime inference must use `RUNTIME_INFERENCE`; it cannot masquerade as user/archive/memory evidence.

### Exclusion Provenance

PASS. The runtime can serialize excluded records with reason, scope, and blocked domains. This becomes the verification base for Phase 3.7.5.2 Memory Router.

### Authority Preservation

PASS. ProvenanceBuilder records authority from source/ranking policy and does not increase it based on repetition.

## 8. Freeze Notes

### NOTE-3751-001 — Mandatory ContextBlock Provenance

Context Provenance becomes mandatory metadata for every ContextBlock entering JuliaContext.

### NOTE-3751-002 — Retrieval Score Does Not Change Authority

Retrieval relevance score must not modify source authority. Authority remains owned by source policy.

### NOTE-3751-003 — Provider Output Requires Runtime Classification

Provider-generated content cannot become evidence without explicit Runtime classification.

### NOTE-3751-004 — Memory Router Must Consume Provenance

Future Memory Router decisions must consume provenance, not raw retrieval result.

### NOTE-3751-005 — Provenance Immutability

Provenance chain is immutable after Context Projection.

## 9. Risks / Limitations

| Risk | Status | Note |
| --- | --- | --- |
| JuliaContext dataclass not yet schema-expanded with provenance field | Accepted | v1 integrates provenance through semantic metadata to avoid breaking ContextCompiler contracts |
| Projection-level provenance not yet attached to every projection block | Pending | Next integration can wrap projection blocks once Memory Router lands |
| Exclusion provenance is implemented but not yet driven by real Memory Router | Pending | Phase 3.7.5.2 will produce real exclusions |

## 10. Final Decision

Phase 3.7.5.1 is accepted and frozen.

```text
Context Provenance Runtime implemented
Block-level lineage implemented
Exclusion provenance implemented
Runtime inference labeling implemented
Provider output isolation implemented
Audit serialization implemented
Semantic retriever provenance integration implemented
```

Freeze status:

```text
Decision: ACCEPT
Status: APPROVED / FROZEN
Frozen Boundary: No Context enters JuliaContext without provenance identity.
```

Next phase after approval:

```text
Phase 3.7.5.2 — Memory Router
```
