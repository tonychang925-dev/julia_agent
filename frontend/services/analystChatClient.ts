import type {
  AnalystChatClientMessage,
  AnalystChatProtocolMessage,
  ConnectionState,
  JuliaMessage,
} from '../types/analystChat';

export type AnalystChatClient = {
  state: ConnectionState;
  sentMessages?: AnalystChatClientMessage[];
  connect: () => void;
  send: (message: AnalystChatClientMessage) => void;
  disconnect: () => void;
  reconnect: () => void;
  nextMessage: () => Promise<JuliaMessage | null>;
};

export function parseAnalystChatMessage(message: AnalystChatProtocolMessage): JuliaMessage | null {
  if (message.type !== 'response') return null;
  return {
    id: `${message.payload.session_id}-${message.payload.timestamp}`,
    role: 'julia',
    text: message.payload.text,
    intent: message.payload.intent,
    evidenceRefs: message.payload.evidence_refs.map((ref) => ({
      id: ref.id,
      title: ref.title,
      sourceType: ref.sourceType ?? ref.source_type,
      url: ref.url ?? null,
    })),
    contextScope: message.payload.context_scope,
    confidence: message.payload.confidence,
    limitations: message.payload.limitations,
    timestamp: message.payload.timestamp,
  };
}

export function createAnalystChatClient(wsUrl: string): AnalystChatClient {
  let socket: WebSocket | null = null;
  const listeners: Array<(message: JuliaMessage | null) => void> = [];
  const client: AnalystChatClient = {
    state: 'disconnected',
    connect() {
      client.state = 'connecting';
      socket = new WebSocket(wsUrl);
      socket.onopen = () => { client.state = 'connected'; };
      socket.onclose = () => { client.state = 'disconnected'; };
      socket.onerror = () => { client.state = 'error'; };
      socket.onmessage = (event) => {
        const parsed = parseAnalystChatMessage(JSON.parse(event.data));
        listeners.splice(0).forEach((resolve) => resolve(parsed));
      };
    },
    send(message) {
      socket?.send(JSON.stringify(message));
    },
    disconnect() {
      client.state = 'disconnected';
      socket?.close();
      socket = null;
    },
    reconnect() {
      client.disconnect();
      client.connect();
    },
    nextMessage() {
      return new Promise((resolve) => listeners.push(resolve));
    },
  };
  return client;
}

export function createMockAnalystChatClient(messages: AnalystChatProtocolMessage[]): AnalystChatClient {
  const queue = [...messages];
  const client: AnalystChatClient = {
    state: 'connected',
    sentMessages: [],
    connect() { client.state = 'connected'; },
    send(message) { client.sentMessages?.push(message); },
    disconnect() { client.state = 'disconnected'; },
    reconnect() { client.state = 'connected'; },
    async nextMessage() {
      const next = queue.shift();
      return next ? parseAnalystChatMessage(next) : null;
    },
  };
  return client;
}
