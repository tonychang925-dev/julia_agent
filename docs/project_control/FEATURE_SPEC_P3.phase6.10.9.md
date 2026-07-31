# FEATURE_SPEC P3.phase6.10.9 — Julia Session / Task State Runtime

## Status
✅ Implemented / PASS

## Motivation
Julia Context OS already has Truth Layer, Projection, Mutation, and Conflict Resolution. The remaining gap before Async Session Memory Worker is explicit ownership of working-state facts: what project Julia is in, what phase is active, what constraints are persistent, what task is currently being completed, and what next actions remain.

This phase separates Claude-style `Session State` from `Task State` while preserving Julia's Cognitive Ownership Principle.

## Core Principle

Session State ≠ Memory  
Task State ≠ Conversation

- **Session State**: durable working environment, project context, design principles, architecture decisions, persistent constraints, active goals.
- **Task State**: current objective, status, progress, decisions, blockers, next actions.
- **Memory Runtime** remains the governed long-term memory authority.
- **Conversation Archive** remains the lived transcript/evidence source.

## Added Modules

```text
runtime/context_os/state/
├── __init__.py
├── session_state.py
├── task_state.py
├── state_store.py
├── state_transition.py
├── state_projection.py
└── state_manager.py
```

## Main Data Models

### JuliaSessionState

```python
JuliaSessionState(
    session_id,
    project_context,
    architecture_decisions,
    persistent_constraints,
    active_goals,
)
```

### JuliaTaskState

```python
JuliaTaskState(
    task_id,
    objective,
    status,
    progress,
    decisions,
    blockers,
    next_actions,
)
```

## Runtime Integration

- `ContextProjectionInputs` now accepts:
  - `session_state: JuliaSessionState | None`
  - `task_state: JuliaTaskState | None`
- `ContextProjector` projects these into model-facing `ContextBlock`s:
  - `session_state`
  - `active_task`
- `JuliaStateManager` provides persistence, projection, and mutation application.
- `SessionTaskStateTransitionEngine` applies authorized context mutations while rejecting protected identity/relationship/persona targets.

## Acceptance Criteria

- Session state persists across runtime restart.
- Task state persists progress, decisions, blockers, and next actions.
- Ordinary memory/evidence does not pollute Session State.
- Conflict priority preserves current Tony instruction over task/session/memory.
- Projection remains provider-independent.
- Context mutations update Session/Task but cannot mutate protected identity fields.

## Tests

`tests/test_phase36109_session_task_state_runtime.py`

- TC-36109-001 Session Persistence
- TC-36109-002 Task Resume
- TC-36109-003 Memory Isolation
- TC-36109-004 Conflict Priority
- TC-36109-005 Provider Independence
- TC-36109-006 Protected Mutation Rejection

## Validation

```bash
python3 -m unittest tests.test_phase36109_session_task_state_runtime -v
python3 -m unittest discover -s tests
```

Result:

```text
Ran 367 tests
OK
```
