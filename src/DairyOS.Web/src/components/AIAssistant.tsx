import { useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Loader2,
  Search,
  ShieldCheck,
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

const SUGGESTED_QUESTIONS = [
  'How do I record a missed milk entry for the correct date?',
  'What was milk production in July?',
  'What was the average and maximum COP/L in September?',
  'How many calves have been delivered and how many mortalities were recorded?',
  'A cow has fever and reduced appetite. What conditions should the veterinarian assess?',
  'Why is Feed Cost / L unavailable for a period?',
  'What should I know about mastitis and when is it urgent?',
  'Give me the complete checklist for recording a milk sale.',
  'How do vaccination and breeding records affect the animal passport?',
  'How can I run a read-only system health check safely?',
];

const ROLES = [
  'Operator',
  'Supervisor',
  'Finance',
  'Veterinary / Health',
  'Technical',
] as const;

type Role = (typeof ROLES)[number];

type RelatedItem = {
  id: string;
  title: string;
  domain: string;
  capability: string;
  question: string;
  review_status: string;
  anchor_validation: string;
};

type AssistantResponse = {
  question: string;
  answer_type: string;
  scope: string;
  title: string;
  answer: string;
  expanded_explanation: string;
  role?: Role;
  role_guidance?: Record<string, string>;
  selected_role_guidance?: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
  next_actions: string[];
  exceptions_recovery: string[];
  effects: string[];
  safety: string;
  sources: string[];
  related: RelatedItem[];
  matched_items?: RelatedItem[];
  review?: {
    status: string;
    note: string;
    source_files: string[];
    source_authority: string[];
    implementation_anchors: Record<string, unknown>;
    implementation_validation: { status: string; issues: string[] };
  };
  coverage?: {
    items: number;
    domains: string[];
    read_only: boolean;
  };
  conversation_id?: string;
  tool_results?: Record<string, Record<string, unknown>>;
};

const field: CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: '#1e293b',
  border: '1px solid #334155',
  color: '#fff',
  borderRadius: 6,
  padding: '9px 10px',
  fontSize: 11,
  lineHeight: 1.45,
};

const smallButton = (active = false): CSSProperties => ({
  background: active ? '#0c4a6e' : '#1e293b',
  color: '#e2e8f0',
  border: active ? '1px solid #38bdf8' : '1px solid #334155',
  borderRadius: 6,
  padding: '7px 9px',
  cursor: 'pointer',
  fontSize: 10,
  fontWeight: 800,
  textAlign: 'left',
});

const heading: CSSProperties = {
  color: '#38bdf8',
  fontSize: 9,
  fontWeight: 900,
  letterSpacing: 0.8,
  textTransform: 'uppercase',
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 7, padding: 11 }}>
      <div style={heading}>{title}</div>
      <div style={{ marginTop: 7 }}>{children}</div>
    </section>
  );
}

function StringList({ values, ordered = false }: { values: string[]; ordered?: boolean }) {
  if (!values.length) return <div style={{ color: '#64748b', fontSize: 10 }}>None recorded in this guidance item.</div>;
  const List = ordered ? 'ol' : 'ul';
  return (
    <List style={{ margin: ordered ? '0 0 0 18px' : '0 0 0 16px', padding: 0, color: '#cbd5e1', fontSize: 11, lineHeight: 1.55 }}>
      {values.map((value, index) => <li key={`${value}-${index}`} style={{ marginBottom: 3 }}>{value}</li>)}
    </List>
  );
}

function LiveEvidence({ results }: { results: Record<string, Record<string, unknown>> }) {
  const entries = Object.entries(results).filter(([name, value]) => name !== 'read_safety_policy' && value && value.read_only === true);
  if (!entries.length) return null;
  return (
    <Section title="Read-only live evidence">
      <div style={{ display: 'grid', gap: 7 }}>
        {entries.map(([name, value]) => {
          const evidence = (value.evidence || value) as Record<string, unknown>;
          const metric = String(evidence.metric || name);
          const headline = metric === 'milk_production'
            ? `Milk production: ${evidence.total_litres ?? 'unavailable'} litres`
            : metric === 'reproduction_and_calf_lifecycle'
              ? `Calving events: ${evidence.actual_calving_events ?? 0}; calf records: ${evidence.calf_animal_records ?? 0}`
              : metric === 'mortality'
                ? `Mortality events: ${evidence.mortality_events ?? 0}; current deceased records: ${evidence.currently_deceased_animals ?? 0}`
                : metric === 'health_insight'
                  ? `Possible health conditions returned: ${Array.isArray(evidence.probable_conditions) ? evidence.probable_conditions.length : 0}`
                  : name.replaceAll('_', ' ');
          return (
            <div key={name} style={{ background: '#111827', border: '1px solid #334155', borderRadius: 6, padding: 8 }}>
              <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 800, textTransform: 'capitalize' }}>{headline}</div>
              <div style={{ color: '#86efac', fontSize: 9, marginTop: 3 }}>Database read-only guard: active</div>
              <details style={{ marginTop: 5, color: '#94a3b8', fontSize: 9 }}>
                <summary>Inspect supporting evidence</summary>
                <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto', margin: '6px 0 0', color: '#cbd5e1' }}>{JSON.stringify(value, null, 2).slice(0, 12000)}</pre>
              </details>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

export default function AIAssistant() {
  const [question, setQuestion] = useState('');
  const [role, setRole] = useState<Role>('Operator');
  const [answer, setAnswer] = useState<AssistantResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const ask = async (nextQuestion = question) => {
    const trimmed = nextQuestion.trim();
    if (trimmed.length < 2) {
      setError('Enter a question with enough detail for a grounded answer.');
      return;
    }
    setQuestion(trimmed);
    setBusy(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/ai-assistant/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed, role, conversation_id: conversationId }),
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(payload?.detail || `AI Assistant unavailable (HTTP ${response.status}).`);
      }
      const nextAnswer = payload as AssistantResponse;
      setAnswer(nextAnswer);
      if (nextAnswer.conversation_id) setConversationId(nextAnswer.conversation_id);
    } catch (requestError) {
      setAnswer(null);
      setError(requestError instanceof Error ? requestError.message : 'AI Assistant request failed.');
    } finally {
      setBusy(false);
    }
  };

  const clear = async () => {
    const previousConversationId = conversationId;
    setQuestion('');
    setAnswer(null);
    setError('');
    setConversationId(null);
    if (previousConversationId) {
      await fetch(`${API_BASE}/ai-assistant/conversations/${encodeURIComponent(previousConversationId)}`, { method: 'DELETE' }).catch(() => undefined);
    }
  };

  return (
    <section style={{ background: '#0f172a', border: '1px solid #1f2937', borderRadius: 8, padding: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div>
          <div style={{ ...heading, display: 'flex', alignItems: 'center', gap: 6 }}><Bot size={14} />AI Assistant</div>
          <h3 style={{ margin: '4px 0', fontSize: 17 }}>Ask a question in your own words</h3>
          <div style={{ color: '#94a3b8', fontSize: 10, maxWidth: 700 }}>
            AI Assistant matches your question to the versioned DairyOS knowledge base, then develops a complete answer with context, checklist, expected outcome, downstream effects, exceptions, and next action.
          </div>
        </div>
        <div style={{ display: 'inline-flex', gap: 5, alignItems: 'center', color: '#bbf7d0', fontSize: 9, fontWeight: 800 }}><ShieldCheck size={14} />READ ONLY · LIVE DATA ON REQUEST</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 170px', gap: 8, marginTop: 13, alignItems: 'end' }}>
        <label style={{ ...heading, color: '#94a3b8', letterSpacing: 0 }}>
          Your question
          <div style={{ position: 'relative', marginTop: 4 }}>
            <Search size={14} style={{ position: 'absolute', left: 9, top: 10, color: '#64748b' }} />
            <textarea
              aria-label="Ask AI Assistant"
              value={question}
              onChange={event => setQuestion(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void ask();
                }
              }}
              placeholder="Example: What happens after I enter a late milk record?"
              rows={2}
              style={{ ...field, paddingLeft: 29, resize: 'vertical' }}
            />
          </div>
        </label>
        <label style={{ ...heading, color: '#94a3b8', letterSpacing: 0 }}>
          Perspective
          <select aria-label="AI Assistant perspective" value={role} onChange={event => setRole(event.target.value as Role)} style={{ ...field, marginTop: 4 }}>
            {ROLES.map(option => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
      </div>
      <div style={{ display: 'flex', gap: 7, marginTop: 8, flexWrap: 'wrap' }}>
        <button type="button" onClick={() => void ask()} disabled={busy} style={{ ...smallButton(true), background: '#0369a1', opacity: busy ? 0.65 : 1 }}>
          {busy ? <Loader2 size={12} className="dairyos-spin" /> : <Bot size={12} />} {busy ? 'AI Assistant is developing an answer…' : 'Ask AI Assistant'}
        </button>
        <button type="button" onClick={() => void clear()} style={smallButton()}>Clear</button>
      </div>

      {error && <div style={{ marginTop: 10, background: '#450a0a', border: '1px solid #7f1d1d', color: '#fecaca', borderRadius: 6, padding: 8, fontSize: 10 }}>{error}</div>}

      {!answer && !busy && (
        <div style={{ marginTop: 14 }}>
          <div style={{ ...heading, color: '#94a3b8', letterSpacing: 0 }}>Try a question</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 6, marginTop: 7 }}>
            {SUGGESTED_QUESTIONS.map(suggestion => (
              <button key={suggestion} type="button" onClick={() => void ask(suggestion)} style={smallButton()}>{suggestion}<ArrowRight size={11} style={{ float: 'right', marginTop: 1, color: '#38bdf8' }} /></button>
            ))}
          </div>
        </div>
      )}

      {answer && (
          <div style={{ display: 'grid', gap: 9, marginTop: 14 }}>
          {answer.tool_results && <LiveEvidence results={answer.tool_results} />}
          <section style={{ background: '#111827', border: '1px solid #334155', borderRadius: 7, padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
              <div style={{ color: '#a78bfa', fontSize: 14, fontWeight: 900, display: 'flex', alignItems: 'center', gap: 6 }}><Bot size={16} />{answer.title}</div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                <span style={{ background: '#312e81', color: '#ddd6fe', borderRadius: 4, padding: '4px 6px', fontSize: 8, fontWeight: 900 }}>{answer.answer_type}</span>
                <span style={{ background: '#1e293b', color: '#cbd5e1', borderRadius: 4, padding: '4px 6px', fontSize: 8 }}>{answer.scope}</span>
              </div>
            </div>
            <div style={{ marginTop: 10, fontSize: 13, lineHeight: 1.55, color: '#f8fafc' }}>{answer.answer}</div>
            <div style={{ marginTop: 9, color: '#cbd5e1', fontSize: 11, lineHeight: 1.55 }}>{answer.expanded_explanation}</div>
            {answer.selected_role_guidance && <div style={{ marginTop: 10, padding: 9, background: '#0c4a6e', border: '1px solid #075985', borderRadius: 6, color: '#e0f2fe', fontSize: 10 }}><strong>{answer.role || role} perspective:</strong> {answer.selected_role_guidance}</div>}
          </section>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 9 }}>
            <Section title="Before you begin"><StringList values={answer.preconditions} /></Section>
            <Section title="Complete SOP / checklist"><StringList values={answer.steps} ordered /></Section>
            <Section title="Expected outcome"><div style={{ color: '#e2e8f0', fontSize: 11, lineHeight: 1.55 }}>{answer.expected_result}</div></Section>
            <Section title="What happens next"><StringList values={answer.next_actions} /></Section>
            <Section title="Exceptions and recovery"><StringList values={answer.exceptions_recovery} /></Section>
            <Section title="Where the fact goes"><StringList values={answer.effects} /></Section>
          </div>

          <section style={{ background: '#1c1917', border: '1px solid #78350f', borderRadius: 7, padding: 11, color: '#fde68a', fontSize: 10, lineHeight: 1.55 }}>
            <div style={{ fontWeight: 900, display: 'flex', alignItems: 'center', gap: 5 }}><AlertTriangle size={13} />Safety boundary</div>
            <div style={{ marginTop: 5 }}>{answer.safety}</div>
          </section>

          {answer.review && <Section title="Source and review status">
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
              <span style={{ color: '#e2e8f0', fontSize: 10 }}>Corpus status: <strong>{answer.review.status}</strong></span>
              <span style={{ color: answer.review.implementation_validation.status === 'VALIDATED' ? '#86efac' : '#fde68a', fontSize: 10, display: 'inline-flex', alignItems: 'center', gap: 4 }}><CheckCircle2 size={11} />Anchors: {answer.review.implementation_validation.status}</span>
            </div>
            <div style={{ color: '#94a3b8', fontSize: 9, lineHeight: 1.5 }}>{answer.review.note}</div>
            <div style={{ marginTop: 6, color: '#64748b', fontSize: 9 }}>Sources: {answer.review.source_authority.join(' · ') || answer.review.source_files.join(' · ')}</div>
          </Section>}

          {!!answer.related.length && <Section title="Related questions">
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {answer.related.map(item => <button key={item.id} type="button" onClick={() => void ask(item.question)} style={smallButton()}>{item.title}<ArrowRight size={11} style={{ marginLeft: 5, verticalAlign: -1, color: '#38bdf8' }} /></button>)}
            </div>
          </Section>}

          {answer.coverage && <div style={{ color: '#64748b', fontSize: 9 }}>Grounded against {answer.coverage.items} normalized knowledge items across {answer.coverage.domains.length} domains. Live operational data and logs are read only when the question requires them; missing authority is shown as unavailable.</div>}
        </div>
      )}
    </section>
  );
}
