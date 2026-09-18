import { useState } from 'react';
import { Bot } from 'lucide-react';
import { apiUrl } from '../config/api';

type Evidence = { id: string; title: string; unreviewed: boolean };

type AssistantReply = {
  stage: string;
  decision: string;
  text: string | null;
  answer: string | null;
  evidence: Evidence[];
  unreviewed: boolean;
};

export default function AIAssistant() {
  const [question, setQuestion] = useState('');
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    const asked = question.trim();
    if (!asked || busy) return;
    setBusy(true);
    setError(null);
    setReply(null);
    try {
      // The Assistant lives outside the /farm namespace on purpose. /farm is
      // where operational farm data is served, and the Assistant has no route
      // to any of it, so putting it there would misdescribe the boundary.
      //
      // apiUrl, rather than a bare relative path: the UI and the API share an
      // origin in the packaged application but not under the Vite dev server,
      // and this helper exists because hand-written paths produced silently
      // wrong URLs before.
      const response = await fetch(apiUrl('/assistant/ask'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: asked }),
      });
      const body = await response.json();
      if (!response.ok) {
        setError(typeof body?.detail === 'string' ? body.detail : 'The AI Assistant is unavailable.');
      } else {
        setReply(body as AssistantReply);
      }
    } catch {
      setError('The AI Assistant could not be reached.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        border: '1px solid #334155',
        borderRadius: 8,
        padding: 16,
        background: '#0f172a',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontWeight: 700,
          marginBottom: 10,
        }}
      >
        <Bot size={16} />
        AI Assistant
      </div>

      <div style={{ lineHeight: 1.6 }}>
        Ask how DairyOS works: a workflow, a term, or how a figure is calculated.
      </div>

      <div style={{ lineHeight: 1.6, marginTop: 8 }}>
        The Assistant does not access DairyOS operational data or farm records, so it
        cannot answer questions about this farm's animals, yields or finances.
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') ask(); }}
          placeholder="How do I record a missed milking session?"
          maxLength={600}
          style={{
            flex: 1,
            background: '#111827',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '8px 10px',
            color: '#e2e8f0',
            fontSize: 13,
          }}
        />
        <button
          onClick={ask}
          disabled={busy || question.trim().length === 0}
          style={{
            background: busy ? '#1f2937' : '#1d4ed8',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '8px 14px',
            color: '#e2e8f0',
            fontSize: 13,
            fontWeight: 700,
            cursor: busy ? 'default' : 'pointer',
          }}
        >
          {busy ? 'Asking' : 'Ask'}
        </button>
      </div>

      {error && (
        <div style={{ lineHeight: 1.6, marginTop: 12, color: '#f87171', fontSize: 13 }}>
          {error}
        </div>
      )}

      {reply && (
        <div style={{ marginTop: 12 }}>
          {/* Only "text" is rendered. The response also carries diagnostic
              fields naming what a withheld answer got wrong, and those can
              contain the very figure that was withheld. */}
          <div style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap', fontSize: 13 }}>
            {reply.text ?? 'No answer was produced.'}
          </div>

          {reply.unreviewed && (
            <div style={{ marginTop: 8, fontSize: 11, color: '#fbbf24' }}>
              Based on knowledge that has not completed review.
            </div>
          )}

          {reply.evidence?.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 11, color: '#64748b' }}>
              Sources: {reply.evidence.map((e) => e.id).join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
