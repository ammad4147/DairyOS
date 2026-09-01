import React from 'react';
import { useAnimalContext } from '../../context/AnimalContext';

export default function AnimalSearchBar() {
  const { selectedAnimalId, setSelectedAnimalId } = useAnimalContext();

  return (
    <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 12 }}>
      <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 'bold', display: 'block', marginBottom: 6 }}>
        Search / Select Animal
      </label>
      <input
        type="text"
        placeholder="Enter Animal ID..."
        value={selectedAnimalId || ''}
        onChange={(e) => setSelectedAnimalId(e.target.value.trim() || null)}
        style={{
          width: '100%',
          boxSizing: 'border-box',
          background: '#0f172a',
          border: '1px solid #334155',
          color: '#f8fafc',
          padding: '8px 10px',
          borderRadius: 6,
          fontSize: 13,
        }}
      />
    </div>
  );
}
