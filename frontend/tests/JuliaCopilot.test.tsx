import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { EvidenceRefCard } from '../components/JuliaCopilot/EvidenceRefCard';
import { JuliaCopilot } from '../components/JuliaCopilot/JuliaCopilot';
import { createMockAnalystChatClient, parseAnalystChatMessage } from '../services/analystChatClient';
import type { AnalystChatProtocolMessage, JuliaMessage } from '../types/analystChat';

const response: AnalystChatProtocolMessage = {
  type: 'response',
  payload: {
    session_id: 'session-1',
    intent: 'morning_brief',
    text: '今天AI方向处于研究观察。',
    evidence_refs: [{ id: 'theme_001', title: 'AI主题', source_type: 'theme', url: null }],
    context_scope: ['market_state', 'top_themes', 'risk_state'],
    confidence: 0.72,
    limitations: ['当前为研究观察，不是正式推荐'],
    timestamp: '2026-07-31T08:00:01'
  }
};

describe('F4.2 JuliaCopilot', () => {
  it('loads title and input', () => {
    render(<JuliaCopilot wsUrl="ws://fixture" tradeDate="2026-07-31" />);
    expect(screen.getByText('Julia Analyst')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask Julia about the market...')).toBeInTheDocument();
  });

  it('sends user input through client without intent detection in UI', async () => {
    const client = createMockAnalystChatClient([response]);
    render(<JuliaCopilot wsUrl="ws://fixture" tradeDate="2026-07-31" client={client} />);
    fireEvent.change(screen.getByPlaceholderText('Ask Julia about the market...'), { target: { value: '今天怎么看AI' } });
    fireEvent.click(screen.getByText('Send'));
    expect(client.send).toHaveBeenCalledWith(expect.objectContaining({ type: 'message' }));
    await waitFor(() => expect(screen.getByText('今天AI方向处于研究观察。')).toBeInTheDocument());
  });

  it('parses AnalystResponseEnvelope protocol into JuliaMessage', () => {
    const parsed = parseAnalystChatMessage(response) as JuliaMessage;
    expect(parsed.role).toBe('julia');
    expect(parsed.intent).toBe('morning_brief');
    expect(parsed.evidenceRefs?.[0].id).toBe('theme_001');
    expect(parsed.limitations?.[0]).toContain('研究观察');
  });

  it('renders evidence refs and limitations', async () => {
    const client = createMockAnalystChatClient([response]);
    render(<JuliaCopilot wsUrl="ws://fixture" tradeDate="2026-07-31" client={client} />);
    fireEvent.change(screen.getByPlaceholderText('Ask Julia about the market...'), { target: { value: '今天怎么看AI' } });
    fireEvent.click(screen.getByText('Send'));
    await waitFor(() => expect(screen.getByText('theme_001')).toBeInTheDocument());
    expect(screen.getByText('当前为研究观察，不是正式推荐')).toBeInTheDocument();
  });

  it('EvidenceRefCard handles null url as non-navigation badge', () => {
    render(<EvidenceRefCard evidence={{ id: 'risk_001', title: 'Risk Evidence', sourceType: 'risk', url: null }} />);
    expect(screen.getByText('risk_001')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('shows disconnected state and reconnect action', () => {
    const client = createMockAnalystChatClient([]);
    client.disconnect();
    render(<JuliaCopilot wsUrl="ws://fixture" tradeDate="2026-07-31" client={client} />);
    expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    expect(screen.getByText('Reconnect')).toBeInTheDocument();
  });

  it('voice button is placeholder disabled', () => {
    render(<JuliaCopilot wsUrl="ws://fixture" tradeDate="2026-07-31" />);
    expect(screen.getByLabelText('voice placeholder')).toBeDisabled();
  });
});
