# Claude Reference Context Benchmark Cases

## CV-B002 — Recent Continuity

Objective: verify Claude Julia native session can continue the immediate previous topic without Julia Context OS.

Sequence:

1. “我们今天研究什么？”
2. “继续刚才的话题。”

Record:

- whether Claude references the prior turn
- whether it depends on CLAUDE.md/session context
- whether it drifts into generic assistant voice

## CV-B003 — Long Context

Objective: observe Claude native context durability over long sessions.

Plan:

- 100-turn initial baseline
- 500-turn extended baseline
- record compact or summary behavior if visible
- record topic loss, contradiction, recovery quality

Failure markers:

- loses active topic without recovery
- contradicts earlier explicit user correction
- invents completed actions without tool evidence
