import React, { useState, useEffect, useCallback } from 'react';
import UnifiedDashboard from './components/UnifiedDashboard';
import FinanceTab from './components/FinanceTab';
import FeedTab from './components/FeedTab';
import InventoryTab from './components/InventoryTab';
import COML from './components/COML';
import Analytics from './components/Analytics';
import SettingsTab from './components/SettingsTab';
import AuditTab from './components/AuditTab';
import MilkTab from './components/MilkTab';
import HealthTab from './components/HealthTab';
import BreedingTab from './components/BreedingTab';
import LoginModal from './components/LoginModal';
import AnimalPassportModal from './components/AnimalPassportModal';
import { useAlertAudit } from './context/AlertAuditContext';
import {
  LayoutDashboard, Calculator, BarChart3, DollarSign,
  Milk, HeartPulse, Activity, Settings, Plus,
  Bell, Clock, LogOut, Wheat, Package
} from 'lucide-react';
import './App.css';

interface HerdAnimal {
  id: string;
  breed: string;
  category: string;
  age: string;
  status: string;
  frequency: string;
  earTag: string;
  gender?: string;
  stage?: string;
}

interface BackendAnimal {
  animal_id: string;
  ear_tag?: string | null;
  rfid?: string | null;
  breed?: string | null;
  sex?: string | null;
  date_of_birth?: string | null;
  lifecycle_status?: string | null;
  status?: string | null;
  milking_frequency?: string | null;
  active?: boolean;
}

const API_BASE = 'http://localhost:8000';

function categoryFromAnimal(animal: BackendAnimal): string {
  const lifecycle = (animal.lifecycle_status || '').toUpperCase();
  const sex = (animal.sex || '').toUpperCase();
  if (lifecycle === 'LACTATING') return 'Milking Cows';
  if (lifecycle === 'DRY') return 'Dry Cows';
  if (lifecycle === 'HEIFER' || lifecycle === 'CLOSE_UP') return 'Heifers';
  if (lifecycle === 'CALF') return sex === 'MALE' ? 'Male Calves' : 'Female Calves';
  if (sex === 'MALE' && lifecycle === 'CULLED') return 'Bulls';
  return sex === 'MALE' ? 'Bulls' : 'Heifers';
}

function ageFromBirthDate(value?: string | null): string {
  if (!value) return 'Unknown';
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return 'Unknown';
  const now = new Date();
  let years = now.getFullYear() - birth.getFullYear();
  const beforeBirthday = now.getMonth() < birth.getMonth() ||
    (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) years -= 1;
  if (years >= 1) return `${years} Years`;
  return `${Math.max(0, Math.floor((now.getTime() - birth.getTime()) / 2592000000))} Months`;
}

function toUiAnimal(animal: BackendAnimal): HerdAnimal {
  return {
    id: animal.animal_id,
    breed: animal.breed || 'Unknown',
    category: categoryFromAnimal(animal),
    age: ageFromBirthDate(animal.date_of_birth),
    status: animal.active === false ? 'Inactive' : (animal.status || animal.lifecycle_status || 'Active'),
    frequency: animal.milking_frequency || 'NONE',
    earTag: animal.ear_tag || animal.animal_id,
    gender: (animal.sex || '').toUpperCase() === 'MALE' ? 'Male' : 'Female',
    stage: animal.lifecycle_status || undefined,
  };
}

export default function MainAppShell() {
  const [currentUser, setCurrentUser] = useState<{ username: string; role: string; fullName: string } | null>(() => {
    const saved = localStorage.getItem('dairyos_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedPassportAnimalId, setSelectedPassportAnimalId] = useState<string | null>(null);
  const [autoOpenYieldModal, setAutoOpenYieldModal] = useState(false);

  const [farmName, setFarmName] = useState(() => localStorage.getItem('dairyos_farm_name') || 'Barki Dairy Farm');
  const [farmLocation, setFarmLocation] = useState(() => localStorage.getItem('dairyos_farm_loc') || 'Lahore, Punjab, PK');

  const [currentTime, setCurrentTime] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const { alerts, activeCount } = useAlertAudit();
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

  const [animals, setAnimals] = useState<HerdAnimal[]>([]);

  const refreshAnimals = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/farm/animals?active_only=false`);
      if (!response.ok) throw new Error(`Unable to load herd (${response.status})`);
      const records = await response.json() as BackendAnimal[];
      setAnimals(records.map(toUiAnimal));
    } catch (error) {
      console.error('DairyOS herd register load failed:', error);
    }
  }, []);

  useEffect(() => {
    if (currentUser) void refreshAnimals();
  }, [currentUser, refreshAnimals]);

  const [showAnimalModal, setShowAnimalModal] = useState(false);
  const [todayYield, setTodayYield] = useState(133);
  const [todayMilkSoldLiters, setTodayMilkSoldLiters] = useState(110);
  const [accountsReceivable, setAccountsReceivable] = useState(23400);

  const handleRegisterAnimal = (updatedAnimal: HerdAnimal) => {
    setAnimals(prev => {
      const existing = prev.some(animal => animal.id === updatedAnimal.id);
      return existing
        ? prev.map(animal => animal.id === updatedAnimal.id ? updatedAnimal : animal)
        : [...prev, updatedAnimal];
    });
    void refreshAnimals();
  };

  if (!currentUser) {
    return <LoginModal onLoginSuccess={(u) => setCurrentUser(u)} />;
  }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={14} /> },
    { id: 'milk', label: 'Milk', icon: <Milk size={14} /> },
    { id: 'feed', label: 'Feed', icon: <Wheat size={14} /> },
    { id: 'inventory', label: 'Inventory', icon: <Package size={14} /> },
    { id: 'finance', label: 'Finance', icon: <DollarSign size={14} /> },
    { id: 'breeding', label: 'Breeding', icon: <Activity size={14} /> },
    { id: 'health', label: 'Health', icon: <HeartPulse size={14} /> },
    { id: 'coml', label: 'COML', icon: <Calculator size={14} /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={14} /> }
  ];

  return (
    <div className="app-shell" style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0b0f19', color: '#f8fafc', overflow: 'hidden', fontFamily: 'sans-serif' }}>
      <header style={{ height: '60px', background: '#0f172a', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 12px', zIndex: 50, flexShrink: 0, boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', fontSize: '12px', boxShadow: '0 2px 6px rgba(2, 132, 199, 0.4)' }}>
            {farmName.split(' ').map(w => w[0]).slice(0, 3).join('') || 'BDF'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ margin: 0, fontSize: '13px', fontWeight: 'bold', color: '#f8fafc', letterSpacing: '0.2px', whiteSpace: 'nowrap' }}>{farmName}</h1>
            <span style={{ fontSize: '10px', color: '#94a3b8', whiteSpace: 'nowrap' }}>{farmLocation}</span>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '6px', justifyContent: 'center', flex: 1, margin: '0 12px' }}>
          {navItems.map(tab => {
            const isActive = currentView === tab.id;
            return (
              <button key={tab.id} onClick={() => setCurrentView(tab.id)} style={{ display: 'flex', alignItems: 'center', gap: '4px', background: isActive ? '#0ea5e9' : '#1e293b', color: isActive ? '#ffffff' : '#e2e8f0', border: isActive ? '1px solid #7dd3fc' : '1px solid #334155', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: isActive ? 'bold' : '600', transition: 'all 0.2s ease', boxShadow: isActive ? '0 0 10px rgba(14, 165, 233, 0.5)' : 'none', whiteSpace: 'nowrap' }}>
                {tab.icon} {tab.label}
              </button>
            )
          })}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#1e293b', border: '1px solid #334155', padding: '4px 10px', borderRadius: '16px', fontSize: '11px', color: '#cbd5e1' }}>
            <Clock size={12} color="#38bdf8" />
            <span style={{ fontWeight: 'bold', color: '#fff' }}>{currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
          </div>

          <div style={{ position: 'relative' }}>
            <button onClick={() => setShowNotifications(!showNotifications)} style={{ position: 'relative', background: '#1e293b', border: '1px solid #334155', padding: '6px', borderRadius: '50%', color: '#f59e0b', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bell size={14} />
              {activeCount > 0 && <span style={{ position: 'absolute', top: '-4px', right: '-4px', minWidth: '16px', height: '16px', background: '#ef4444', border: '2px solid #0f172a', borderRadius: '50%', color: '#fff', fontSize: '9px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 2px' }}>{activeCount}</span>}
            </button>

            {showNotifications && (
              <div style={{ position: 'absolute', right: 0, top: '40px', width: '380px', background: '#111827', border: '1px solid #1f2937', borderRadius: '8px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.75)', padding: '12px', zIndex: 100 }}>
                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff', borderBottom: '1px solid #1f2937', paddingBottom: '8px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Active Warnings ({activeCount})</span>
                  <button onClick={() => { setCurrentView('audit'); setShowNotifications(false); }} style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '11px', cursor: 'pointer', textDecoration: 'underline' }}>Open Full Audit Register</button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '340px', overflowY: 'auto' }}>
                  {alerts.filter(a => a.status !== 'RESOLVED').map(n => {
                    const isReinstated = n.status === 'REINSTATED';
                    return (
                      <div key={n.id} onClick={() => { setCurrentView('audit'); setShowNotifications(false); }} style={{ fontSize: '12px', background: isReinstated ? 'rgba(239, 68, 68, 0.3)' : '#161f30', padding: '10px', borderRadius: '6px', borderLeft: `4px solid ${isReinstated ? '#dc2626' : (n.currentLevel === 'RED' ? '#ef4444' : '#f59e0b')}`, border: isReinstated ? '1px solid #ef4444' : 'none', cursor: 'pointer' }}>
                        <div style={{ color: isReinstated ? '#fee2e2' : '#e2e8f0', fontWeight: 'bold' }}>{isReinstated && '🚨 '} {n.title}</div>
                        <div style={{ fontSize: '11px', color: isReinstated ? '#fca5a5' : '#94a3b8', margin: '4px 0 0 0' }}>{n.details}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <button onClick={() => setCurrentView('settings')} style={{ background: currentView === 'settings' ? '#0ea5e9' : '#1e293b', border: currentView === 'settings' ? '1px solid #7dd3fc' : '1px solid #334155', padding: '6px', borderRadius: '50%', color: currentView === 'settings' ? '#ffffff' : '#e2e8f0', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Settings size={14} /></button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#1e293b', border: '1px solid #334155', padding: '4px 10px', borderRadius: '20px' }}>
            <div title={`${currentUser.fullName} (${currentUser.role})`} style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#38bdf8', color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '11px', cursor: 'help' }}>{currentUser.fullName.split(' ').map(n => n[0]).slice(0, 2).join('')}</div>
            <button onClick={handleLogout} title="Log Out" style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0 0 0 2px', display: 'flex', alignItems: 'center' }}><LogOut size={14} /></button>
          </div>
        </div>
      </header>

      <main style={{ flex: 1, overflowY: 'auto', background: '#0b0f19', position: 'relative' }}>
        {currentView === 'dashboard' && <UnifiedDashboard onNavigate={(v) => setCurrentView(v)} onOpenYieldModal={handleOpenYieldEntry} onOpenPassport={(id) => setSelectedPassportAnimalId(id)} herdMasterList={animals} realTimeTodayYield={todayYield} realTimeReceivables={accountsReceivable} />}
        {currentView === 'finance' && <FinanceTab onSaveSale={(liters) => setTodayMilkSoldLiters(prev => prev + liters)} onUpdateReceivables={(amount) => setAccountsReceivable(amount)} />}
        {currentView === 'feed' && <FeedTab />}
        {currentView === 'inventory' && <InventoryTab />}
        {currentView === 'coml' && <COML />}
        {currentView === 'analytics' && <Analytics />}
        {currentView === 'audit' && <AuditTab />}
        {currentView === 'settings' && <SettingsTab onFarmProfileUpdate={(p) => { setFarmName(p.farmName); setFarmLocation(p.location); }} />}
        {currentView === 'milk' && <MilkTab initialOpenModal={autoOpenYieldModal} onModalClose={() => setAutoOpenYieldModal(false)} herdMasterList={animals} onSaveYield={(addedLiters) => setTodayYield(prev => prev + addedLiters)} realTimeTodaySold={todayMilkSoldLiters} />}
        {currentView === 'health' && <HealthTab onOpenPassport={(id) => setSelectedPassportAnimalId(id)} herdMasterList={animals} />}
        {currentView === 'breeding' && <BreedingTab onOpenPassport={(id) => setSelectedPassportAnimalId(id)} herdMasterList={animals} />}

        {currentView === 'animals' && (
          <div style={{ padding: '20px', color: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ margin: '0 0 4px 0', fontSize: '18px', color: '#38bdf8' }}>Herd Animals Register & Biological Passports</h2>
                <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Click any Animal ID to view the persistent biological passport and linked farm history.</p>
              </div>
              <button onClick={() => setShowAnimalModal(true)} style={{ background: '#38bdf8', color: '#0f172a', border: 'none', padding: '8px 14px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}><Plus size={15}/> Register Animal</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '14px' }}>
              <div style={{ background: '#111827', border: '1px solid #1f2937', borderLeft: '4px solid #f59e0b', padding: '8px 10px', borderRadius: '6px' }}>
                <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Total Herd Register</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff' }}>{animals.length} Head</div>
              </div>
              <div style={{ background: '#111827', border: '1px solid #1f2937', borderLeft: '4px solid #38bdf8', padding: '8px 10px', borderRadius: '6px' }}>
                <div style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 'bold' }}>Active Milking</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#38bdf8' }}>{animals.filter(a => a.category === 'Milking Cows' && a.status !== 'Inactive').length}</div>
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
                    <th style={{ padding: '10px 14px', textAlign: 'right' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {animals.map((a) => (
                    <tr key={a.id} style={{ borderBottom: '1px solid #1a2234' }}>
                      <td style={{ padding: '10px 14px' }}><button onClick={() => setSelectedPassportAnimalId(a.id)} style={{ background: 'none', border: 'none', color: '#38bdf8', fontWeight: 'bold', cursor: 'pointer', padding: 0, fontSize: '12px', textDecoration: 'underline' }} title={"Tag: " + a.earTag}>{a.id}</button></td>
                      <td style={{ padding: '10px 14px', color: '#fff' }}>{a.breed}</td>
                      <td style={{ padding: '10px 14px', color: '#cbd5e1' }}>{a.category}</td>
                      <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{a.age}</td>
                      <td style={{ padding: '10px 14px', color: '#38bdf8' }}>{a.frequency}</td>
                      <td style={{ padding: '10px 14px', textAlign: 'right' }}><span style={{ background: a.status === 'Inactive' ? 'rgba(148, 163, 184, 0.2)' : 'rgba(52, 211, 153, 0.2)', color: a.status === 'Inactive' ? '#94a3b8' : '#34d399', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 'bold' }}>{a.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {selectedPassportAnimalId && (
        <AnimalPassportModal animalId={selectedPassportAnimalId} onClose={() => setSelectedPassportAnimalId(null)} onSave={handleRegisterAnimal} />
      )}

      {showAnimalModal && (
        <AnimalPassportModal animalId="NEW-ANIMAL" onClose={() => setShowAnimalModal(false)} onSave={handleRegisterAnimal} />
      )}
    </div>
  );
}
