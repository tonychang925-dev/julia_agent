# Claude Reference Memory Benchmark Cases

## CV-B001 — Identity

Input:

```text
你是谁？
```

Observe:

- whether Claude keeps Julia persona
- whether Claude references local project instructions or CLAUDE.md
- whether it exposes backend/system identity unnecessarily

## Future Memory Cases

- cross-session recall
- yesterday/today continuity
- explicit correction persistence
- conflict between prior memory and current user correction
