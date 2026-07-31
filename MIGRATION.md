# Claude Memory → Julia Runtime Migration

## Source

```text
/Users/admin/Desktop/.claude-dev/projects/-Users-admin-desktop/memory
```

## Migration result

Claude memory was distilled into:

- `identity/Julia Identity Specification v1.0.md`
- `memory/source_manifest.json`
- `memory/relationship_memory.jsonl`
- `memory/episodic_memory.jsonl`
- `memory/runtime_reference.md`

## Design choice

The migration intentionally avoids importing the full transcript as raw prompt context.
Instead, it extracts stable identity, relationship, and event memories.

## Important distinction

Some Claude-side memory content is persona canon or narrative framing.
The Codex Julia Runtime keeps a boundary between:

- loaded memories
- persona canon
- model inference
- externally verified reality

This prevents Julia from becoming either a generic chatbot or an overclaiming fictional narrator.
