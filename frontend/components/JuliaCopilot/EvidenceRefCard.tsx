import React from 'react';
import type { EvidenceRefDisplay } from '../../types/analystChat';

export function EvidenceRefCard({ evidence }: { evidence: EvidenceRefDisplay }) {
  const source = evidence.sourceType ?? evidence.source_type ?? 'evidence';
  const body = (
    <span className="julia-evidence-card">
      <strong>{evidence.id}</strong>
      <span>{evidence.title}</span>
      <em>{source}</em>
    </span>
  );
  if (evidence.url) {
    return <a href={evidence.url}>{body}</a>;
  }
  return <span>{body}</span>;
}
