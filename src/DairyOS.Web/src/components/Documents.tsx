export default function DocumentsTab() {
  return (
    <div style={{ padding: '20px' }}>
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', padding: '20px' }}>
        <h2 style={{ fontSize: '16px', margin: '0 0 16px 0' }}>Operating Manuals & SOPs</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '14px', textDecoration: 'underline' }}>1. Technical Operating Manual</button></li>
          <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '14px', textDecoration: 'underline' }}>2. Farm Staff SOPs</button></li>
          <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '14px', textDecoration: 'underline' }}>3. Health Intervention Guidelines</button></li>
        </ul>
      </div>
    </div>
  );
}
