import React from 'react';

interface TimelineEvent {
  id?: string;
  category?: string;
  status?: string;
  severity?: string;
  date?: string;
  title?: string;
  details?: string;
  [key: string]: any;
}

interface EventTimelineProps {
  events: TimelineEvent[];
  onNavigate?: (tab: string) => void;
}

export default function EventTimeline({ events, onNavigate }: EventTimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div style={{ color: '#64748b', fontSize: 12, padding: '20px 0', textAlign: 'center' }}>
        No health / welfare events found for this animal.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {events.map((event, index) => (
        <div
          key={event.id || index}
          style={{
            background: '#0f172a',
            border: '1px solid #1e293b',
            borderLeft: `3px solid ${event.severity === 'critical' ? '#ef4444' : event.status === 'Active' ? '#f59e0b' : '#334155'}`,
            borderRadius: 6,
            padding: '10px 12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 'bold', color: '#e2e8f0' }}>
              {event.title || event.condition || event.category || 'Event'}
            </span>
            <span style={{ fontSize: 11, color: '#64748b' }}>{event.date || ''}</span>
          </div>
          {event.details && (
            <div style={{ fontSize: 11, color: '#94a3b8' }}>{event.details}</div>
          )}
          <div style={{ marginTop: 6, display: 'flex', gap: 8 }}>
            {event.status && (
              <span style={{ fontSize: 10, color: '#94a3b8', background: '#1e293b', padding: '2px 6px', borderRadius: 4 }}>
                {event.status}
              </span>
            )}
            {event.category && onNavigate && (
              <button
                onClick={() => onNavigate(event.category === 'breeding' ? 'breeding' : 'health')}
                style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: 10, cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
              >
                Open {event.category}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
