import React, { useState } from 'react';
import { Database, Plus, Search, ShieldCheck, Activity, HeartPulse, Milk } from 'lucide-react';

interface AnimalRegistryProps {
  onOpenPassport: (tagId: string) => void;
}

export default function AnimalRegistry({ onOpenPassport }: AnimalRegistryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // Standardized herd category list
  const categories = ['Milking', 'Dry', 'Heifer', 'Female Calf', 'Male Calf', 'Bull'];

  const animals = [
    { tagId: 'TD-001', category: 'Milking', breed: 'Holstein Friesian', status: 'Active', lactationDays: 120, yield: '38.5 L' },
    { tagId: 'TD-004', category: 'Milking', breed: 'Jersey Cross', status: 'Withdrawal', lactationDays: 45, yield: '24.0 L' },
    { tagId: 'TD-009', category: 'Dry', breed: 'Sahiwal', status: 'Resting', lactationDays: 0, yield: '0.0 L' },
    { tagId: 'TD-012', category: 'Heifer', breed: 'Holstein Friesian', status: 'Growing', lactationDays: 0, yield: '0.0 L' },
    { tagId: 'TD-015', category: 'Female Calf', breed: 'Jersey Cross', status: 'Healthy', lactationDays: 0, yield: '0.0 L' },
    { tagId: 'TD-018', category: 'Bull', breed: 'Sahiwal Sire', status: 'Active', lactationDays: 0, yield: '0.0 L' },
  ];

  const filteredAnimals = animals.filter(a => {
    const matchesSearch = a.tagId.toLowerCase().includes(searchTerm.toLowerCase()) || a.breed.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || a.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div style={{ padding: '24px', color: '#fff' }}>
      {/* Header & Entry Point */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ color: '#38bdf8', margin: '0 0 4px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={22} /> Animal Registry & Passports
          </h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
            Standardized herd composition, category filtering, and comprehensive lifetime passports.
          </p>
        </div>
        
        <button 
          onClick={() => onOpenPassport('NEW-ANIMAL')}
          style={{ background: '#0284c7', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(2, 132, 199, 0.3)' }}
        >
          <Plus size={16} /> Enter Animal & Prepare Passport
        </button>
      </div>

      {/* Herd Category Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '12px', marginBottom: '24px' }}>
        <div 
          onClick={() => setSelectedCategory('ALL')}
          style={{ background: selectedCategory === 'ALL' ? '#1e293b' : '#111827', border: '1px solid ' + (selectedCategory === 'ALL' ? '#38bdf8' : '#1f2937'), padding: '14px', borderRadius: '8px', cursor: 'pointer', textAlign: 'center' }}
        >
          <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>TOTAL HERD</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginTop: '4px' }}>{animals.length}</div>
        </div>

        {categories.map(cat => {
          const count = animals.filter(a => a.category === cat).length;
          const isSelected = selectedCategory === cat;
          return (
            <div 
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{ background: isSelected ? '#1e293b' : '#111827', border: '1px solid ' + (isSelected ? '#38bdf8' : '#1f2937'), padding: '14px', borderRadius: '8px', cursor: 'pointer', textAlign: 'center' }}
            >
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>{cat.toUpperCase()}</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#38bdf8', marginTop: '4px' }}>{count}</div>
            </div>
          );
        })}
      </div>

      {/* Search & Filter Bar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', background: '#111827', padding: '12px', borderRadius: '8px', border: '1px solid #1f2937' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, background: '#1e293b', padding: '8px 12px', borderRadius: '6px' }}>
          <Search size={16} color="#94a3b8" />
          <input 
            type="text" 
            placeholder="Search by Tag ID or Breed..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: '#fff', outline: 'none', width: '100%', fontSize: '13px' }}
          />
        </div>
      </div>

      {/* Animal Table */}
      <div style={{ background: '#111827', borderRadius: '8px', border: '1px solid #1f2937', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#1e293b', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '12px 16px' }}>Tag ID</th>
              <th style={{ padding: '12px 16px' }}>Category</th>
              <th style={{ padding: '12px 16px' }}>Breed</th>
              <th style={{ padding: '12px 16px' }}>Status</th>
              <th style={{ padding: '12px 16px' }}>Avg Yield</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAnimals.map((animal) => (
              <tr key={animal.tagId} style={{ borderBottom: '1px solid #1f2937' }}>
                <td style={{ padding: '14px 16px', fontWeight: 'bold', color: '#38bdf8' }}>{animal.tagId}</td>
                <td style={{ padding: '14px 16px' }}>{animal.category}</td>
                <td style={{ padding: '14px 16px' }}>{animal.breed}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', background: '#064e3b', color: '#34d399' }}>
                    {animal.status}
                  </span>
                </td>
                <td style={{ padding: '14px 16px' }}>{animal.yield}</td>
                <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                  <button 
                    onClick={() => onOpenPassport(animal.tagId)}
                    style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', padding: '6px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    View Passport
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
