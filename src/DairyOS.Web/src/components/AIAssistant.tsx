import { Bot } from 'lucide-react';

export default function AIAssistant() {
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
        AI Assistan
      </div>

      <div style={{ lineHeight: 1.6 }}>
        The previous AI Assistant has been retired.
      </div>

      <div style={{ lineHeight: 1.6, marginTop: 8 }}>
        A new knowledge-only AI Assistant is being developed from zero for
        DairyOS capability exploration, operator education and approved dairy
        knowledge.
      </div>

      <div style={{ lineHeight: 1.6, marginTop: 8 }}>
        The new Assistant will not access DairyOS operational data or farm records.
      </div>
    </div>
  );
}
