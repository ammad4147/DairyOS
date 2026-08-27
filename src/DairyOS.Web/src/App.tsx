import React, { useCallback, useEffect, useState } from 'react';
import UnifiedDashboard from './components/UnifiedDashboard';
import AnimalPassportModal from './components/AnimalPassportModal';
import { API_BASE_URL } from './config/api';
import { useAlertAudit } from './context/AlertAuditContext';
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

const API_BASE = API_BASE_URL || 'http://127.0.0.1:8000';

function categoryFromAnimal(animal: BackendAnimal): string {
  const lifecycle = (animal.lifecycle_status || '').toUpperCase();
  const sex = (animal.sex || '').toUpperCase();
  if (lifecycle === 'LACTATING') return 'Milking Cows';
  if (lifecycle === 'DRY') return 'Dry Cows';
  if (lifecycle === 'HEIFER' || lifecycle === 'CLOSE_UP') return sex === 'MALE' ? 'Bulls' : 'Heifers';
  if (lifecycle === 'CALF') return sex === 'MALE' ? 'Male Calves' : 'Female Calves';
  return sex === 'MALE' ? 'Bulls' : 'Heifers';
}

function ageFromBirthDate(value?: string | null): string {
  if (!value) return 'Unknown';
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return 'Unknown';
  const now = new Date();
  let years = now.getFullYear() - birth.getFullYear();
  const before = now.getMonth() < birth.getMonth()
    || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (before) years -= 1;
  if (years >= 1) return `${years} Years`;
  return `${Math.max(0, Math.floor((now.getTime() - birth.getTime()) / 2592000000))} Months`;
}

function toUiAnimal(animal: BackendAnimal): HerdAnimal {
  return {
    id: animal.animal_id,
    breed: animal.breed || 'Unknown',
    category: categoryFromAnimal(animal),
    age: ageFromBirthDate(animal.date_of_birth),
    status: animal.active === false ? (animal.status || 'Inactive') : (animal.status || animal.lifecycle_status || 'Active'),
    frequency: animal.milking_frequency || 'NONE',
    earTag: animal.ear_tag || animal.animal_id,
    gender: (animal.sex || '').toUpperCase() === 'MALE' ? 'Male' : 'Female',
    stage: animal.lifecycle_status || undefined,
  };
}

export default function MainAppShell() {
  const [animals, setAnimals] = useState<BackendAnimal[]>([]);
  const [farmName, setFarmName] = useState('DairyOS');
  const [farmLocation, setFarmLocation] = useState('');
  const [selectedPassportAnimalId, setSelectedPassportAnimalId] = useState<string | null>(null);
  const [todayYield, setTodayYield] = useState(0);
  const [accountsReceivable, setAccountsReceivable] = useState(0);
  useAlertAudit();

  const refreshAnimals = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/farm/animals?active_only=false`);
      if (!response.ok) throw new Error(`Unable to load herd (${response.status})`);
      setAnimals(await response.json() as BackendAnimal[]);
    } catch (error) {
      console.error('DairyOS herd register load failed:', error);
    }
  }, []);

  useEffect(() => {
    const storedName = localStorage.getItem('dairyos_farm_name');
    const storedLocation = localStorage.getItem('dairyos_farm_loc');
    if (storedName) setFarmName(storedName);
    if (storedLocation) setFarmLocation(storedLocation);
    void refreshAnimals();
  }, [refreshAnimals]);

  const handleFarmProfileUpdate = (profile: { farmName: string; location: string }) => {
    setFarmName(profile.farmName);
    setFarmLocation(profile.location);
    localStorage.setItem('dairyos_farm_name', profile.farmName);
    localStorage.setItem('dairyos_farm_loc', profile.location);
  };

  const herdMasterList = animals.map(toUiAnimal);

  return (
    <div
      className="app-shell"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        minWidth: 0,
        background: '#0b0f19',
        color: '#f8fafc',
        overflow: 'hidden',
        fontFamily: 'sans-serif',
      }}
    >
      <header
        style={{
          height: 60,
          background: '#0f172a',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          alignItems: 'center',
          padding: '0 12px',
          zIndex: 50,
          flexShrink: 0,
          boxShadow: '0 4px 6px -1px rgba(0,0,0,.3)',
          minWidth: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 6,
              background: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 'bold',
              fontSize: 12,
            }}
          >
            DOS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ margin: 0, fontSize: 13, fontWeight: 'bold', whiteSpace: 'nowrap' }}>{farmName}</h1>
            <span style={{ fontSize: 10, color: '#94a3b8', whiteSpace: 'nowrap' }}>{farmLocation}</span>
          </div>
        </div>
      </header>

      <main
        style={{
          flex: 1,
          minHeight: 0,
          minWidth: 0,
          overflow: 'hidden',
          background: '#0b0f19',
          position: 'relative',
        }}
      >
        <UnifiedDashboard
          onOpenPassport={setSelectedPassportAnimalId}
          herdMasterList={herdMasterList}
          realTimeTodayYield={todayYield}
          realTimeReceivables={accountsReceivable}
        />
      </main>

      {selectedPassportAnimalId && (
        <AnimalPassportModal
          animalId={selectedPassportAnimalId}
          onClose={() => setSelectedPassportAnimalId(null)}
          onSave={refreshAnimals}
        />
      )}
    </div>
  );
}
