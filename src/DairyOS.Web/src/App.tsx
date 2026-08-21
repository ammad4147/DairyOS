import React, { useState, useEffect } from 'react';
import UnifiedDashboard from './components/UnifiedDashboard';
import FinanceTab from './components/FinanceTab';
import FeedTab from './components/FeedTab';
import CMPL from './components/CMPL';
import Analytics from './components/Analytics';
import SettingsTab from './components/SettingsTab';
import AuditTab from './components/AuditTab';
import MilkTab from './components/MilkTab';
import HealthTab from './components/HealthTab';
import BreedingTab from './components/BreedingTab';
import LoginModal from './components/LoginModal';
import AnimalPassportModal from './components/AnimalPassportModal';
import { AlertAuditProvider, useAlertAudit } from './context/AlertAuditContext';
import {
  LayoutDashboard, DollarSign, Wheat, Calculator, BarChart3,
  Milk, HeartPulse, Activity, Users, Settings, Plus, Award,
  Bell, Clock, ChevronRight, CheckCircle2, ShieldAlert, LogOut
} from 'lucide-react';
import './App.css';

function MainAppShell() {
  const [currentUser, setCurrentUser] = useState<{ username: string; role: string; fullName: string } | null>(() => {
    const saved = localStorage.getItem('dairyos_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedPassportAnimalId, setSelectedPassportAnimalId] = useState<string | null>(null);
  const [autoOpenYieldModal, setAutoOpenYieldModal] = useState(false);

  // Dynamic Farm Identity
  const [farmName, setFarmName] = useState(() => localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [farmLocation, setFarmLocation] = useState(() => localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');

  // Real-time Clock
  const [currentTime, setCurrentTime] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const { alerts, markResolved, activeCount } = useAlertAudit();
  const [showNotifications, setShowNotifications] = useState(false);

  const handleOpenYieldEntry = () => {
    setAutoOpenYieldModal(true);
    setCurrentView('milk');
  };

  const handleLogout = () => {
    localStorage.removeItem('dairyos_token');
    localStorage.removeItem('dairyos_user');
    setCurrentUser(null);
  };

  // Herd Animals Data
  const [animals, setAnimals] = useState([
    { id: 'TD-001', breed: 'Holstein Friesian', category: 'Milking Cows', age: '4 Years', status: 'Healthy', frequency: 'TWICE_DAILY', earTag: 'PK-LHR-001' },
    { id: 'TD-002', breed: 'Sahiwal Cross', category: 'Milking Cows', age: '5 Years', status: 'Healthy', frequency: 'THRICE_DAILY', earTag: 'PK-LHR-002' },
    { id: 'TD-003', breed: 'Cholistani', category: 'Milking Cows', age: '3 Years', status: 'Healthy', frequency: 'TWICE_DAILY', earTag: 'PK-LHR-003' },
    { id: 'TD-004', breed: 'Nili-Ravi (Buffalo)', category: 'Dry Cows', age: '6 Years', status: 'Under Treatment', frequency: 'NONE', earTag: 'PK-LHR-004' },
    { id: 'TD-005', breed: 'Holstein Cross', category: 'Heifers', age: '18 Months', status: 'Growing', frequency: 'NONE', earTag: 'PK-LHR-005' },
    { id: 'TD-006', breed: 'Sahiwal', category: 'Female Calves', age: '3 Months', status: 'Weaned', frequency: 'NONE', earTag: 'PK-LHR-006' },
    { id: 'TD-007', breed: 'Holstein', category: 'Male Calves', age: '2 Months', status: 'Fattening', frequency: 'NONE', earTag: 'PK-LHR-007' },
    { id: 'TD-008', breed: 'Sahiwal Sire', category: 'Bulls', age: '4 Years', status: 'Active Breeding', frequency: 'NONE', earTag: 'PK-LHR-008' },
    { id: 'TD-009', breed: 'Holstein Purebred', category: 'Milking Cows', age: '4.5 Years', status: 'Healthy', frequency: 'THRICE_DAILY', earTag: 'PK-LHR-009' },
    { id: 'TD-014', breed: 'Jersey Cross', category: 'Milking Cows', age: '3.5 Years', status: 'Healthy', frequency: 'THRICE_DAILY', earTag: 'PK-LHR-014' },
  ]);

  const [showAnimalModal, setShowAnimalModal] = useState(false);
  const [newBreed, setNewBreed] = useState('Holstein Friesian');
  const [newCategory, setNewCategory] = useState('Milking Cows');
  const [newAge, setNewAge] = useState('3 Years');
  const [newFrequency, setNewFrequency] = useState('TWICE_DAILY');

  const handleAddAnimal = (e: React.FormEvent) => {
    e.preventDefault();
    const nextSeq = animals.length + 1;
    const autoId = `TD-${nextSeq.toString().padStart(3, '0')}`;
    setAnimals([
      { id: autoId, breed: newBreed, category: newCategory, age: newAge, status: 'Healthy', frequency: newCategory === 'Milking Cows' ? newFrequency : 'NONE', earTag: `PK-LHR-${autoId.split('-')[1]}` },
      ...animals
    ]);
    setShowAnimalModal(false);
  };

  if (!currentUser) {
    return <LoginModal onLoginSuccess={(u) => setCurrentUser(u)} />;
  }

  return (
    <div className="app-shell" style={{ display: 'flex', height: '100vh', background: '#0b0f19', color: '#f8fafc', overflow: 'hidden', fontFamily: 'sans-serif' }}>

      {/* SIDEBAR NAVIGATION */}
      <div className="sidebar" style={{ width: '235px', background: '#111827', borderRight: '1px solid #1f2937', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>

        {/* BRANDING HEADER (Updates dynamically from Settings) */}
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: '13px' }}>
            {farmName.split(' ').map(w => w[0]).slice(0, 3).join('') || 'BDF'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <h1 style={{ margin: 0, fontSize: '13px', fontWeight: 'bold', color: '#fff', letterSpacing: '0.2px', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }} title={farmName}>
              {farmName}
            </h1>
            <span style={{ fontSize: '10px', color: '#94a3b8', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }} title={farmLocation}>
              {farmLocation}
            </span>
          </div>
        </div>

        {/* NAVIGATION LINKS */}
        <nav style={{ padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '3px', flex: 1, overflowY: 'auto' }}>
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
            <Users size={15} /> Animal Records & Passport
          </button>

          <button onClick={() => setCurrentView('milk')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'milk' ? '#1e293b' : 'transparent', color: currentView === 'milk' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Milk size={15} /> Milk Production & Farm Yield
          </button>

          <button onClick={() => setCurrentView('health')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'health' ? '#1e293b' : 'transparent', color: currentView === 'health' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <HeartPulse size={15} /> Health & Treatments
          </button>

          <button onClick={() => setCurrentView('breeding')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'breeding' ? '#1e293b' : 'transparent', color: currentView === 'breeding' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Activity size={15} /> Breeding & Gestation
          </button>

          <div style={{ margin: '10px 0 4px 12px', fontSize: '10px', fontWeight: 'bold', color: '#64748b', textTransform: 'uppercase' }}>System Governance</div>

          <button onClick={() => setCurrentView('audit')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'audit' ? '#1e293b' : 'transparent', color: currentView === 'audit' ? '#ef4444' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <ShieldAlert size={15} color={currentView === 'audit' ? '#ef4444' : '#94a3b8'} /> Warning Audit Register
          </button>

          <button onClick={() => setCurrentView('settings')} style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '8px 12px', background: currentView === 'settings' ? '#1e293b' : 'transparent', color: currentView === 'settings' ? '#38bdf8' : '#94a3b8', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
            <Settings size={15} /> Settings
          </button>
        </nav>
      </div>

      {/* MAIN VIEWPORT */}
      <div className="main-viewport" style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, boxSizing: 'border-box' }}>

        {/* TOPLINE HEADER */}
        <header style={{ height: '54px', background: '#111827', borderBottom: '1px solid #1f2937', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', boxSizing: 'border-box', position: 'relative', zIndex: 50 }}>

          <div style={{ minWidth: '40px' }} />

          {/* TOP-MIDDLE LIVE CLOCK */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0f172a', border: '1px solid #1e293b', padding: '5px 12px', borderRadius: '20px', fontSize: '11px', color: '#cbd5e1' }}>
            <Clock size={13} color="#38bdf8" />
            <span style={{ fontWeight: 'bold', color: '#fff' }}>
              {currentTime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
            <span style={{ color: '#64748b' }}>•</span>
            <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 'bold' }}>
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>

          {/* TOP-RIGHT ACTIONS */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>

            {/* Notification Bell (Direct navigation to Audit Register) */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                style={{ position: 'relative', background: '#1e293b', border: '1px solid #334155', padding: '6px', borderRadius: '50%', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                title="Operational Alerts"
              >
                <Bell size={15} />
                {activeCount > 0 && (
                  <span style={{ position: 'absolute', top: '-2px', right: '-2px', minWidth: '15px', height: '15px', background: '#ef4444', borderRadius: '50%', color: '#fff', fontSize: '9px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 2px' }}>
                    {activeCount}
                  </span>
                )}
              </button>

              {/* Actionable Notification Popover */}
              {showNotifications && (
                <div style={{ position: 'absolute', right: 0, top: '38px', width: '380px', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.75)', padding: '12px', zIndex: 100 }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#fff', borderBottom: '1px solid #1f2937', paddingBottom: '6px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Active Warnings ({activeCount})</span>
                    <button onClick={() => { setCurrentView('audit'); setShowNotifications(false); }} style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '10px', cursor: 'pointer', textDecoration: 'underline' }}>
                      Open Full Audit Register
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '340px', overflowY: 'auto' }}>
                    {alerts.filter(a => a.status !== 'RESOLVED').map(n => {
                      const isReinstated = n.status === 'REINSTATED';
                      return (
                        <div
                          key={n.id}
                          onClick={() => { setCurrentView('audit'); setShowNotifications(false); }}
                          style={{
                            fontSize: '11px',
                            background: isReinstated ? 'rgba(239, 68, 68, 0.3)' : '#161f30',
                            padding: '8px 10px',
                            borderRadius: '6px',
                            borderLeft: `3px solid ${isReinstated ? '#dc2626' : (n.currentLevel === 'RED' ? '#ef4444' : '#f59e0b')}`,
                            border: isReinstated ? '1px solid #ef4444' : 'none',
                            cursor: 'pointer'
                          }}
                        >
                          <div style={{ color: isReinstated ? '#fee2e2' : '#e2e8f0', fontWeight: 'bold' }}>
                            {isReinstated && '🚨 '} {n.title}
                          </div>
                          <div style={{ fontSize: '10px', color: isReinstated ? '#fca5a5' : '#94a3b8', margin: '3px 0' }}>{n.details}</div>
                          <div style={{ fontSize: '9px', color: '#38bdf8', marginTop: '4px' }}>Click to view in Audit Register →</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Gear Icon for Settings */}
            <button
              onClick={() => setCurrentView('settings')}
              style={{ background: currentView === 'settings' ? '#38bdf8' : '#1e293b', border: '1px solid #334155', padding: '6px', borderRadius: '50%', color: currentView === 'settings' ? '#0f172a' : '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              title="Settings"
            >
              <Settings size={15} />
            </button>

            {/* User Profile Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#1e293b', border: '1px solid #334155', padding: '3px 10px', borderRadius: '20px' }}>
              <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#38bdf8', color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '11px' }}>
                {currentUser.fullName.split(' ').map(n => n[0]).slice(0, 2).join('')}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', lineHeight: '1.1', textAlign: 'left' }}>
                <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#fff' }}>{currentUser.fullName}</span>
                <span style={{ fontSize: '9px', color: '#34d399' }}>{currentUser.role}</span>
              </div>
              <button onClick={handleLogout} title="Log Out" style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0 0 0 4px', display: 'flex', alignItems: 'center' }}>
                <LogOut size={13} />
              </button>
            </div>

          </div>
        </header>

        {/* CONTENT AREA */}
        <main style={{ flex: 1, overflowY: 'auto', background: '#0b0f19' }}>
          {currentView === 'dashboard' && (
            <UnifiedDashboard
              onNavigate={(v) => setCurrentView(v)}
              onOpenYieldModal={handleOpenYieldEntry}
              onOpenPassport={(id) => setSelectedPassportAnimalId(id)}
            />
          )}
          {currentView === 'finance' && <FinanceTab />}
          {currentView === 'feed' && <FeedTab />}
          {currentView === 'cmpl' && <CMPL />}
          {currentView === 'analytics' && <Analytics />}
          {currentView === 'audit' && <AuditTab />}
          {currentView === 'settings' && (
            <SettingsTab
              onFarmProfileUpdate={(p) => {
                setFarmName(p.farmName);
                setFarmLocation(p.location);
              }}
            />
          )}
          {currentView === 'milk' && (
            <MilkTab
              initialOpenModal={autoOpenYieldModal}
              onModalClose={() => setAutoOpenYieldModal(false)}
            />
          )}
          {currentView === 'health' && <HealthTab />}
          {currentView === 'breeding' && <BreedingTab onOpenPassport={(id) => setSelectedPassportAnimalId(id)} />}

          {/* ANIMAL RECORDS & PASSPORT */}
          {currentView === 'animals' && (
            <div style={{ padding: '20px', color: '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Herd Animals Register & Biological Passports</h2>
                  <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Click any Animal ID to view the full biological passport, pedigree family tree, and lactation timeline.</p>
                </div>
                <button onClick={() => setShowAnimalModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                  <Plus size={15}/> Register Animal
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #38bdf8' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Total Herd Count</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>{animals.length} Head</div>
                </div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #34d399' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Milking Cows</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399' }}>{animals.filter(a => a.category === 'Milking Cows').length}</div>
                </div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Dry Cows & Heifers</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f59e0b' }}>{animals.filter(a => a.category === 'Dry Cows' || a.category === 'Heifers').length}</div>
                </div>
                <div style={{ background: '#111827', border: '1px solid #1f2937', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a78bfa' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8' }}>Calves & Bulls</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#a78bfa' }}>{animals.filter(a => a.category === 'Female Calves' || a.category === 'Male Calves' || a.category === 'Bulls').length}</div>
                </div>
              </div>

              <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#161f30', borderBottom: '1px solid #1f2937', textAlign: 'left', color: '#94a3b8' }}>
                      <th style={{ padding: '10px 14px' }}>Animal ID / Tag</th>
                      <th style={{ padding: '10px 14px' }}>Breed</th>
                      <th style={{ padding: '10px 14px' }}>Herd Category</th>
                      <th style={{ padding: '10px 14px' }}>Age</th>
                      <th style={{ padding: '10px 14px' }}>Milking Frequency</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Health Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {animals.map((a) => (
                      <tr key={a.id} style={{ borderBottom: '1px solid #1a2234' }}>
                        <td style={{ padding: '10px 14px' }}>
                          <button onClick={() => setSelectedPassportAnimalId(a.id)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, fontSize: '12px', textDecoration: 'underline' }} title={"Tag: " + a.earTag}>
                            {a.id}
                          </button>
                        </td>
                        <td style={{ padding: '10px 14px', color: '#fff' }}>{a.breed}</td>
                        <td style={{ padding: '10px 14px', color: '#cbd5e1' }}>{a.category}</td>
                        <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{a.age}</td>
                        <td style={{ padding: '10px 14px', color: '#38bdf8' }}>{a.frequency}</td>
                        <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                          <span style={{ background: a.status === 'Healthy' ? 'rgba(52, 211, 153, 0.2)' : 'rgba(239, 68, 68, 0.2)', color: a.status === 'Healthy' ? '#34d399' : '#f87171', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>{a.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ANIMAL PASSPORT MODAL */}
      {selectedPassportAnimalId && (
        <AnimalPassportModal animalId={selectedPassportAnimalId} onClose={() => setSelectedPassportAnimalId(null)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <AlertAuditProvider>
      <MainAppShell />
    </AlertAuditProvider>
  );
}
