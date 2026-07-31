export type AnalystIntent = 'morning_brief' | 'deep_dive' | 'research' | 'unknown';

export type EvidenceRefDisplay = {
  id: string;
  title: string;
  sourceType?: string;
  source_type?: string;
  url?: string | null;
};

export type JuliaMessage = {
  id: string;
  role: 'user' | 'julia';
  text: string;
  intent?: AnalystIntent;
  evidenceRefs?: EvidenceRefDisplay[];
  contextScope?: string[];
  confidence?: number;
  limitations?: string[];
  timestamp: string;
};

export type AnalystChatClientMessage = {
  type: 'message';
  payload: {
    session_id: string;
    text: string;
    timestamp: string;
  };
};

export type AnalystChatResponseMessage = {
  type: 'response';
  payload: {
    session_id: string;
    intent: AnalystIntent;
    text: string;
    evidence_refs: EvidenceRefDisplay[];
    context_scope: string[];
    confidence: number;
    limitations: string[];
    timestamp: string;
  };
};

export type AnalystChatErrorMessage = {
  type: 'error';
  payload: {
    message: string;
    recoverable: boolean;
    timestamp: string;
  };
};

export type AnalystChatProtocolMessage =
  | AnalystChatClientMessage
  | AnalystChatResponseMessage
  | AnalystChatErrorMessage;

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';
