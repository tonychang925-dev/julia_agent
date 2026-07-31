import React, { useMemo, useState } from 'react';
import { createAnalystChatClient, type AnalystChatClient } from '../../services/analystChatClient';
import type { AnalystChatClientMessage, JuliaMessage as JuliaMessageModel } from '../../types/analystChat';
import { JuliaMessage } from './JuliaMessage';

type JuliaCopilotProps = {
  wsUrl: string;
  tradeDate: string;
  client?: AnalystChatClient;
};

export function JuliaCopilot({ wsUrl, tradeDate, client: providedClient }: JuliaCopilotProps) {
  const client = useMemo(() => providedClient ?? createAnalystChatClient(wsUrl), [providedClient, wsUrl]);
  const [text, setText] = useState('');
  const [messages, setMessages] = useState<JuliaMessageModel[]>([]);
  const [, setTick] = useState(0);
  const connection = client.state;

  async function handleSend() {
    const trimmed = text.trim();
    if (!trimmed) return;
    const timestamp = new Date().toISOString();
    const userMessage: JuliaMessageModel = {
      id: `user-${timestamp}`,
      role: 'user',
      text: trimmed,
      timestamp,
    };
    setMessages((current) => [...current, userMessage]);
    setText('');
    const outgoing: AnalystChatClientMessage = {
      type: 'message',
      payload: { session_id: tradeDate, text: trimmed, timestamp },
    };
    client.send(outgoing);
    const response = await client.nextMessage();
    if (response) setMessages((current) => [...current, response]);
  }

  function reconnect() {
    client.reconnect();
    setTick((value) => value + 1);
  }

  return (
    <section className="julia-copilot" aria-label="Julia Analyst Copilot">
      <header>
        <h2>Julia Analyst</h2>
        <span>{connection}</span>
        {connection !== 'connected' ? <button onClick={reconnect}>Reconnect</button> : null}
      </header>
      <div className="julia-message-list">
        {messages.map((message) => <JuliaMessage key={message.id} message={message} />)}
      </div>
      <footer>
        <input
          placeholder="Ask Julia about the market..."
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button onClick={handleSend}>Send</button>
        <button aria-label="voice placeholder" disabled>🎙</button>
      </footer>
    </section>
  );
}
