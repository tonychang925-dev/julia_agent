import { describe, expect, it } from 'vitest';
import {
  createMockAnalystChatClient,
  parseAnalystChatMessage,
} from '../services/analystChatClient';
import type { AnalystChatProtocolMessage } from '../types/analystChat';

const protocolResponse: AnalystChatProtocolMessage = {
  type: 'response',
  payload: {
    session_id: 'session-ui-1',
    intent: 'deep_dive',
    text: 'AI主题需要继续核验证据。',
    evidence_refs: [
      { id: 'event_007', title: 'AI事件证据', source_type: 'event', url: 'https://example.test/evidence/event_007' },
    ],
    context_scope: ['target_evidence', 'theme_evidence'],
    confidence: 0.61,
    limitations: ['证据链仍需补充'],
    timestamp: '2026-07-31T08:05:00',
  },
};

describe('F4.2 analystChatClient protocol', () => {
  it('parses response protocol without frontend financial reasoning', () => {
    const parsed = parseAnalystChatMessage(protocolResponse);
    expect(parsed?.id).toBe('session-ui-1-2026-07-31T08:05:00');
    expect(parsed?.role).toBe('julia');
    expect(parsed?.intent).toBe('deep_dive');
    expect(parsed?.contextScope).toEqual(['target_evidence', 'theme_evidence']);
    expect(parsed?.evidenceRefs?.[0].sourceType).toBe('event');
  });

  it('ignores non-response protocol messages', () => {
    expect(parseAnalystChatMessage({
      type: 'error',
      payload: { message: 'fixture', recoverable: true, timestamp: '2026-07-31T08:05:02' },
    })).toBeNull();
  });

  it('mock client records outgoing messages and returns queued responses', async () => {
    const client = createMockAnalystChatClient([protocolResponse]);
    client.send({
      type: 'message',
      payload: {
        session_id: 'session-ui-1',
        text: '为什么关注AI',
        timestamp: '2026-07-31T08:05:01',
      },
    });
    expect(client.sentMessages?.[0].payload.text).toBe('为什么关注AI');
    expect(await client.nextMessage()).toEqual(expect.objectContaining({ text: 'AI主题需要继续核验证据。' }));
  });

  it('mock client exposes deterministic connection lifecycle', () => {
    const client = createMockAnalystChatClient([]);
    expect(client.state).toBe('connected');
    client.disconnect();
    expect(client.state).toBe('disconnected');
    client.reconnect();
    expect(client.state).toBe('connected');
  });
});
