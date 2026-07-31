import React from 'react';
import type { JuliaMessage as JuliaMessageModel } from '../../types/analystChat';
import { EvidenceRefCard } from './EvidenceRefCard';

export function JuliaMessage({ message }: { message: JuliaMessageModel }) {
  return (
    <article className={`julia-message julia-message-${message.role}`}>
      <header>
        <strong>{message.role === 'julia' ? 'Julia' : 'Tony'}</strong>
        {message.intent ? <span>{message.intent}</span> : null}
        <time>{message.timestamp}</time>
      </header>
      <p>{message.text}</p>
      {message.limitations?.length ? (
        <section aria-label="limitations">
          {message.limitations.map((item) => <div key={item}>{item}</div>)}
        </section>
      ) : null}
      {message.evidenceRefs?.length ? (
        <section aria-label="evidence refs">
          {message.evidenceRefs.map((item) => <EvidenceRefCard key={item.id} evidence={item} />)}
        </section>
      ) : null}
    </article>
  );
}
