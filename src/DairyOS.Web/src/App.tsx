import { useState } from 'react';
import UnifiedDashboard from './components/UnifiedDashboard';
import FinanceTab from './components/FinanceTab';
import FeedTab from './components/FeedTab';
import CMPL from './components/CMPL';
import Analytics from './components/Analytics';
import SettingsTab from './components/SettingsTab';
import { LayoutDashboard, DollarSign, Wheat, Calculator, BarChart3, Milk, HeartPulse, Activity, Users, Settings, Plus, X } from 'lucide-react';
import './App.css';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard');

  // Operational Data States with Entry capability
  const [animals, setAnimals] = useState([
    { id: 'COW-102', breed: 'Holstein Friesian', category: 'Milking', age: '4 Years', status: 'Healthy', yield: '38.5 L' },
    { id: 'COW-215', breed: 'Sahiwal Cross', category: 'Milking', age: '5 Years', status: 'Healthy', yield: '36.2 L' },
    { id: 'COW-044', breed: 'Cholistani', category: 'Milking', age: '3 Years', status: 'Healthy', yield: '35.0 L' },
    { id: 'COW-310', breed: 'Nili-Ravi (Buffalo)', category: 'Dry', age: '6 Years', status: 'Monitoring', yield: '0 L' },
    { id: 'HEIFER-08', breed: 'Holstein Cross', category: 'Heifers', age: '18 Months', status: 'Growing', yield: '-' },
    { id: 'CALF-F12', breed: 'Sahiwal', category: 'Female Calves', age: '3 Months', status: 'Weaned', yield: '-' },
    { id: 'CALF-M04', breed: 'Holstein', category: 'Male Calves', age: '2 Months', status: 'Fattening', yield: '-' },
    { id: 'BULL-01', breed: 'Sahiwal Sire', category: 'Bulls', age: '4 Years', status: 'Active Breeding', yield: '-' }
  ]);

  const [milkLogs, setMilkLogs] = useState([
    { tag: 'COW-102', morning: '20.2 L', evening: '18.3 L', total: '38.5 L', date: '2026-08-20' },
    { tag: 'COW-215', morning: '19.0 L', evening: '17.2 L', total: '36.2 L', date: '2026-08-20' },
    { tag: 'COW-044', morning: '18.5 L', evening: '16.5 L', total: '35.0 L', date: '2026-08-20' },
    { tag: 'COW-118', morning: '5.2 L', evening: '3.9 L', total: '9.1 L', date: '2026-08-20' }
  ]);

  const [healthLogs, setHealthLogs] = useState([
    { tag: 'COW-310', issue: 'Clinical Mastitis', treatment: 'Intramammary Antibiotics', veterinarian: 'Dr. Aslam', status: 'Under Treatment' },
    { tag: 'COW-044', issue: 'Slight Fever (103.2°F)', treatment: 'Antipyretic Injection', veterinarian: 'Dr. Aslam', status: 'Recovered' },
    { tag: 'ALL', issue: 'Foot & Mouth Vaccination', treatment: 'Annual Booster Shot', veterinarian: 'Farm Staff', status: 'Completed (185 Doses)' }
  ]);

  const [breedingLogs, setBreedingLogs] = useState([
    { tag: 'COW-112', event: 'Standing Heat Detected', sire: 'Sahiwal Elite Sire #4', status: 'Ready for AI' },
    { tag: 'COW-089', event: 'Artificial Insemination (AI)', sire: 'Holstein Proven Line', status: 'Waiting Pregnancy Check' },
    { tag: 'COW-155', event: 'Pregnancy Diagnosis (PD)', sire: 'Confirmed Pregnant (60 Days)', status: 'Gestating' }
  ]);

  // Modal Entry States
  const [showAnimalModal, setShowAnimalModal] = useState(false);
  const [newAnimalId, setNewAnimalId] = useState('');
  const [newBreed, setNewBreed] = useState('Holstein Friesian');
  const [newCategory, setNewCategory] = useState('Milking');
  const [newAge, setNewAge] = useState('3 Years');

  const [showMilkModal, setShowMilkModal] = useState(false);
  const [milkTag, setMilkTag] = useState('COW-102');
  const [morningYield, setMorningYield] = useState('');
  const [eveningYield, setEveningYield] = useState('');

  const [showHealthModal, setShowHealthModal] = useState(false);
  const [healthTag, setHealthTag] = useState('COW-310');
  const [healthIssue, setHealthIssue] = useState('');
  const [treatment, setTreatment] = useState('');

  const [showBreedModal, setShowBreedModal] = useState(false);
  const [breedTag, setBreedTag] = useState('COW-112');
  const [breedEvent, setBreedEvent] = useState('Standing Heat Detected');
  const [sireLine, setSireLine] = useState('Sahiwal Elite Sire');

  const handleAddAnimal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAnimalId) return;
    setAnimals([{ id: newAnimalId, breed: newBreed, category: newCategory, age: newAge, status: 'Healthy', yield: newCategory === 'Milking' ? '25.0 L' : '-' }, ...animals]);
    setShowAnimalModal(false);
    setNewAnimalId('');
  };

  const handleAddMilk = (e: React.FormEvent) => {
    e.preventDefault();
    const m = parseFloat(morningYield) || 0;
    const ev = parseFloat(eveningYield) || 0;
    const total = (m + ev).toFixed(1) + ' L';
    setMilkLogs([{ tag: milkTag, morning: m + ' L', evening: ev + ' L', total, date: '2026-08-20' }, ...milkLogs]);
    setShowMilkModal(false);
    setMorningYield('');
    setEveningYield('');
  };

  const handleAddHealth = (e: React.FormEvent) => {
    e.preventDefault();
    if (!healthIssue) return;
    setHealthLogs([{ tag: healthTag, issue: healthIssue, treatment, veterinarian: 'Dr. Aslam', status: 'Under Treatment' }, ...healthLogs]);
    setShowHealthModal(false);
    setHealthIssue('');
    setTreatment('');
  };

  const handleAddBreed = (e: React.FormEvent) => {
    e.preventDefault();
    setBreedingLogs([{ tag: breedTag, event: breedEvent, sire: sireLine, status: 'Active Tracking' }, ...breedingLogs]);
    setShowBreedModal(false);
  };

  return (
    <div className="app-shell" style={{ display: 'flex', height: '100vh', background: '#0b0f19', color: '#f8fafc', overflow: 'hidden', fontFamily: 'sans-serif' }}>
      
      {/* SIDEBAR NAVIGATION */}
      <div className="sidebar" style={{ width: '230px', background: '#111827', borderRight: '1px solid #1f2937', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Milk size={22} color="#38bdf8" />
          <h1 style={{ margin: 0, fontSize: '15px', fontWeight: 'bold', color: '#fff' }}>DairyOS Farm Mgmt</h1>
        </div>

        <nav style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, overflowY: 'auto' }}>
          <button onClick={() => setCurrentView('dashboard')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '9px 12px', background: currentView === 'dashboard' ? '#1e293b' : 'transparent', color: currentView === 'dashboard' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'left' }}>
            <LayoutDashboard size={16} /> Main Dashboard
          </button>
          
          <button onClick={() => setCurrentView('finance')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '9px 12px', background: currentView === 'finance' ? '#1e293b' : 'transparent', color: currentView === 'finance' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'left' }}>
            <DollarSign size={16} /> Finance & Ledger
          </button>

          <button onClick={() => setCurrentView('feed')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '9px 12px', background: currentView === 'feed' ? '#1e293b' : 'transparent', color: currentView === 'feed' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'left' }}>
            <Wheat size={16} /> Feed & Nutrition
          </button>

          <button onClick={() => setCurrentView('cmpl')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '9px 12px', background: currentView === 'cmpl' ? '#1e293b' : 'transparent', color: currentView === 'cmpl' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'left' }}>
            <Calculator size={16} /> CMPL Calculator
          </button>

          <button onClick={() => setCurrentView('analytics')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '9px 12px', background: currentView === 'analytics' ? '#1e293b' : 'transparent', color: currentView === 'analytics' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'left' }}>
            <BarChart3 size={16} /> Analytics & KPIs
          </button>

          <div style={{ margin: '10px 0 4px 12px', fontSize: '10px', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' }}>Operational Modules</div>

          <button onClick={() => setCurrentView('animals')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'animals' ? '#1e293b' : 'transparent', color: currentView === 'animals' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Users size={15} /> Animal Records
          </button>

          <button onClick={() => setCurrentView('milk')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'milk' ? '#1e293b' : 'transparent', color: currentView === 'milk' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Milk size={15} /> Milk Production Logs
          </button>

          <button onClick={() => setCurrentView('health')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'health' ? '#1e293b' : 'transparent', color: currentView === 'health' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <HeartPulse size={15} /> Health & Vaccination
          </button>

          <button onClick={() => setCurrentView('breeding')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'breeding' ? '#1e293b' : 'transparent', color: currentView === 'breeding' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Activity size={15} /> Breeding & Reproduction
          </button>

          <button onClick={() => setCurrentView('settings')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'settings' ? '#1e293b' : 'transparent', color: currentView === 'settings' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left', marginTop: '10px' }}>
            <Settings size={15} /> Settings
          </button>
        </nav>

        <div style={{ padding: '12px', borderTop: '1px solid #1f2937', fontSize: '10px', color: '#64748b' }}>
          <div>Operator: Ammad Hassan</div>
          <div>Location: Lahore, PK</div>
        </div>
      </div>

      {/* MAIN VIEWPORT */}
      <div className="main-viewport" style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, boxSizing: 'border-box' }}>
        
        {/* TOP HEADER BAR */}
        <header style={{ height: '55px', background: '#111827', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', boxSizing: 'border-box' }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#fff', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {currentView === 'dashboard' && 'Main Farm Dashboard'}
            {currentView === 'finance' && 'Commercial Dairy Financial Ledger & Receivables'}
            {currentView === 'feed' && 'Feed Inventory & Ration Management'}
            {currentView === 'cmpl' && 'Cost of Milk Production per Liter (CMPL)'}
            {currentView === 'analytics' && 'Operational Analytics & Herd Productivity'}
            {currentView === 'animals' && 'Animal Demographics & Herd Register'}
            {currentView === 'milk' && 'Milk Production Audit & Yield Logs'}
            {currentView === 'health' && 'Animal Health & Vaccination Records'}
            {currentView === 'breeding' && 'Reproductive Lifecycle & Insemination Records'}
            {currentView === 'settings' && 'System Configuration & Settings'}
          </div>
          <div style={{ fontSize: '11px', color: '#34d399', background: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)', padding: '4px 10px', borderRadius: '20px', fontWeight: 'bold' }}>
            ● System Online & Secure
          </div>
        </header>

        {/* CONTENT AREA */}
        <main style={{ flex: 1, overflowY: 'auto', background: '#0b0f19' }}>
          {currentView === 'dashboard' && <UnifiedDashboard onNavigate={(v) => setCurrentView(v)} />}
          {currentView === 'finance' && <FinanceTab />}
          {currentView === 'feed' && <FeedTab />}
          {currentView === 'cmpl' && <CMPL />}
          {currentView === 'analytics' && <Analytics />}
          {currentView === 'settings' && <SettingsTab />}

          {/* 1. ANIMAL RECORDS */}
          {currentView === 'animals' && (
            <div style={{ padding: '20px', color: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Herd Animals Register</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Comprehensive listing of all active adult cows, heifers, calves, and bulls.</p>
                </div>
                <button onClick={() => setShowAnimalModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                  <Plus size={15}/> Register New Animal
                </button>
              </div>

              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Total Herd Count</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>{animals.length} Head</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Milking Cows</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399' }}>{animals.filter(a => a.category === 'Milking').length}</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Dry & Heifers</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f59e0b' }}>{animals.filter(a => a.category === 'Dry' || a.category === 'Heifers').length}</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a855f7' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Calves & Bulls</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#a855f7' }}>{animals.filter(a => a.category.includes('Calves') || a.category === 'Bulls').length}</div></div>
              </div>

              <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                      <th style={{ padding: '10px' }}>Animal Tag ID</th>
                      <th style={{ padding: '10px' }}>Breed</th>
                      <th style={{ padding: '10px' }}>Category</th>
                      <th style={{ padding: '10px' }}>Age</th>
                      <th style={{ padding: '10px' }}>Status</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Current Yield</th>
                    </tr>
                  </thead>
                  <tbody>
                    {animals.map(a => (
                      <tr key={a.id} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '10px', fontWeight: 'bold', color: '#38bdf8' }}>{a.id}</td>
                        <td style={{ padding: '10px', color: '#e2e8f0' }}>{a.breed}</td>
                        <td style={{ padding: '10px', color: '#cbd5e1' }}>{a.category}</td>
                        <td style={{ padding: '10px', color: '#94a3b8' }}>{a.age}</td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ background: a.status === 'Healthy' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(56, 189, 248, 0.2)', color: a.status === 'Healthy' ? '#34d399' : '#38bdf8', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>
                            {a.status}
                          </span>
                        </td>
                        <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#fff' }}>{a.yield}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 2. MILK PRODUCTION LOGS */}
          {currentView === 'milk' && (
            <div style={{ padding: '20px', color: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Milk Production Audit & Yield Logs</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Individual milking animal yield records for morning and evening parlor sessions.</p>
                </div>
                <button onClick={() => setShowMilkModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                  <Plus size={15}/> Log Yield Session
                </button>
              </div>

              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Today's Total Yield</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>1,236 Liters</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Average Yield / Cow</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399' }}>8.7 Liters</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Milking Animals Count</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fb923c' }}>142 Head</div></div>
              </div>

              <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                      <th style={{ padding: '10px' }}>Animal Tag ID</th>
                      <th style={{ padding: '10px' }}>Morning Session</th>
                      <th style={{ padding: '10px' }}>Evening Session</th>
                      <th style={{ padding: '10px' }}>Date</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Total Daily Yield</th>
                    </tr>
                  </thead>
                  <tbody>
                    {milkLogs.map((m, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '10px', fontWeight: 'bold', color: '#38bdf8' }}>{m.tag}</td>
                        <td style={{ padding: '10px', color: '#e2e8f0' }}>{m.morning}</td>
                        <td style={{ padding: '10px', color: '#e2e8f0' }}>{m.evening}</td>
                        <td style={{ padding: '10px', color: '#94a3b8' }}>{m.date}</td>
                        <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#34d399' }}>{m.total}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. HEALTH & VACCINATION */}
          {currentView === 'health' && (
            <div style={{ padding: '20px', color: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Health & Vaccination Module</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Active veterinary treatments, mastitis logs, and herd vaccination schedules.</p>
                </div>
                <button onClick={() => setShowHealthModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                  <Plus size={15}/> Log Health Treatment
                </button>
              </div>

              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Sick Animals Under Treatment</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fca5a5' }}>4 Head</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Vaccination Completed</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399' }}>185 Doses</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Vaccination Due</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fcd34d' }}>12 Doses</div></div>
              </div>

              <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                      <th style={{ padding: '10px' }}>Animal / Group</th>
                      <th style={{ padding: '10px' }}>Health Issue / Event</th>
                      <th style={{ padding: '10px' }}>Treatment Protocol</th>
                      <th style={{ padding: '10px' }}>Attending Vet</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {healthLogs.map((h, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '10px', fontWeight: 'bold', color: '#38bdf8' }}>{h.tag}</td>
                        <td style={{ padding: '10px', color: '#fca5a5' }}>{h.issue}</td>
                        <td style={{ padding: '10px', color: '#e2e8f0' }}>{h.treatment}</td>
                        <td style={{ padding: '10px', color: '#94a3b8' }}>{h.veterinarian}</td>
                        <td style={{ padding: '10px', textAlign: 'right' }}>
                          <span style={{ background: h.status.includes('Completed') || h.status.includes('Recovered') ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: h.status.includes('Completed') || h.status.includes('Recovered') ? '#34d399' : '#fca5a5', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>
                            {h.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. BREEDING & REPRODUCTION */}
          {currentView === 'breeding' && (
            <div style={{ padding: '20px', color: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Breeding & Reproductive Records</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Heat detection, artificial insemination (AI) records, and pregnancy diagnosis milestones.</p>
                </div>
                <button onClick={() => setShowBreedModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                  <Plus size={15}/> Record Breeding Event
                </button>
              </div>

              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #fb923c' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Active Heat Detected</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fb923c' }}>6 Head</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #60a5fa' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Inseminated (Waiting PD)</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#60a5fa' }}>14 Head</div></div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a855f7' }}><div style={{ fontSize: '10px', color: '#94a3b8' }}>Confirmed Pregnant</div><div style={{ fontSize: '16px', fontWeight: 'bold', color: '#a855f7' }}>88 Head</div></div>
              </div>

              <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1f2937', textAlign: 'left', background: '#161f30' }}>
                      <th style={{ padding: '10px' }}>Animal Tag ID</th>
                      <th style={{ padding: '10px' }}>Reproductive Event</th>
                      <th style={{ padding: '10px' }}>Sire / Lineage</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Milestone Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {breedingLogs.map((b, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '10px', fontWeight: 'bold', color: '#38bdf8' }}>{b.tag}</td>
                        <td style={{ padding: '10px', color: '#fb923c' }}>{b.event}</td>
                        <td style={{ padding: '10px', color: '#e2e8f0' }}>{b.sire}</td>
                        <td style={{ padding: '10px', textAlign: 'right', fontWeight: 'bold', color: '#34d399' }}>{b.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* MODALS FOR DATA ENTRY */}
      {showAnimalModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <form onSubmit={handleAddAnimal} style={{ background: '#111827', border: '1px solid #374151', padding: '20px', borderRadius: '8px', width: '380px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0, color: '#fff', fontSize: '15px' }}>Register New Animal</h3><button type="button" onClick={() => setShowAnimalModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Animal Tag ID</label><input type="text" required value={newAnimalId} onChange={e => setNewAnimalId(e.target.value)} placeholder="e.g. COW-501" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Breed</label><input type="text" value={newBreed} onChange={e => setNewBreed(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Category</label><select value={newCategory} onChange={e => setNewCategory(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px' }}><option value="Milking">Milking</option><option value="Dry">Dry</option><option value="Heifers">Heifers</option><option value="Female Calves">Female Calves</option><option value="Male Calves">Male Calves</option><option value="Bulls">Bulls</option></select></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Age</label><input type="text" value={newAge} onChange={e => setNewAge(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', marginTop: '6px' }}>Save Animal Record</button>
          </form>
        </div>
      )}

      {showMilkModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <form onSubmit={handleAddMilk} style={{ background: '#111827', border: '1px solid #374151', padding: '20px', borderRadius: '8px', width: '380px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0, color: '#fff', fontSize: '15px' }}>Log Parlor Yield Session</h3><button type="button" onClick={() => setShowMilkModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Animal Tag ID</label><input type="text" value={milkTag} onChange={e => setMilkTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Morning Session (Liters)</label><input type="number" step="0.1" required value={morningYield} onChange={e => setMorningYield(e.target.value)} placeholder="0.0" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Evening Session (Liters)</label><input type="number" step="0.1" required value={eveningYield} onChange={e => setEveningYield(e.target.value)} placeholder="0.0" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', marginTop: '6px' }}>Save Yield Log</button>
          </form>
        </div>
      )}

      {showHealthModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <form onSubmit={handleAddHealth} style={{ background: '#111827', border: '1px solid #374151', padding: '20px', borderRadius: '8px', width: '380px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0, color: '#fff', fontSize: '15px' }}>Log Health Treatment</h3><button type="button" onClick={() => setShowHealthModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Animal Tag ID / Group</label><input type="text" value={healthTag} onChange={e => setHealthTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Health Issue / Symptom</label><input type="text" required value={healthIssue} onChange={e => setHealthIssue(e.target.value)} placeholder="e.g. Mild Lameness" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Treatment Protocol</label><input type="text" value={treatment} onChange={e => setTreatment(e.target.value)} placeholder="e.g. Antibiotic Spray" style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', marginTop: '6px' }}>Save Health Log</button>
          </form>
        </div>
      )}

      {showBreedModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 10000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <form onSubmit={handleAddBreed} style={{ background: '#111827', border: '1px solid #374151', padding: '20px', borderRadius: '8px', width: '380px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}><h3 style={{ margin: 0, color: '#fff', fontSize: '15px' }}>Record Breeding Event</h3><button type="button" onClick={() => setShowBreedModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}><X size={18}/></button></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Animal Tag ID</label><input type="text" value={breedTag} onChange={e => setBreedTag(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Reproductive Event</label><select value={breedEvent} onChange={e => setBreedEvent(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px' }}><option value="Standing Heat Detected">Standing Heat Detected</option><option value="Artificial Insemination (AI)">Artificial Insemination (AI)</option><option value="Pregnancy Diagnosis (PD)">Pregnancy Diagnosis (PD)</option></select></div>
            <div><label style={{ fontSize: '11px', color: '#94a3b8' }}>Sire / Lineage</label><input type="text" value={sireLine} onChange={e => setSireLine(e.target.value)} style={{ width: '100%', background: '#1e293b', color: '#fff', border: '1px solid #374151', padding: '7px', borderRadius: '4px', fontSize: '11px', boxSizing: 'border-box' }} /></div>
            <button type="submit" style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '12px', marginTop: '6px' }}>Save Breeding Record</button>
          </form>
        </div>
      )}

    </div>
  );
}
