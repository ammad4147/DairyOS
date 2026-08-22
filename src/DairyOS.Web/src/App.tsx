import React, { useState, useEffect, useCallback } from 'react';
import UnifiedDashboard from './components/UnifiedDashboardClean';
import FinanceTab from './components/FinanceTabClean';
import FeedTab from './components/FeedTabClean';
import COML from './components/COML';
import Analytics from './components/Analytics';
import SettingsTab from './components/SettingsTab';
import AuditTab from './components/AuditTab';
import MilkTab from './components/MilkTabClean';
import HealthTab from './components/HealthTab';
import BreedingTab from './components/BreedingTab';
import LoginModal from './components/LoginModal';
import AnimalPassportModal from './components/AnimalPassportModal';
import { useAlertAudit } from './context/AlertAuditContext';
import { LayoutDashboard, Calculator, BarChart3, DollarSign, Milk, HeartPulse, Activity, Settings, Plus, Bell, Clock, LogOut, Wheat } from 'lucide-react';
import './App.css';

interface HerdAnimal { id: string; breed: string; category: string; age: string; status: string; frequency: string; earTag: string; gender?: string; stage?: string; }
interface BackendAnimal { animal_id: string; ear_tag?: string | null; breed?: string | null; sex?: string | null; date_of_birth?: string | null; lifecycle_status?: string | null; status?: string | null; milking_frequency?: string | null; active?: boolean; }
const API_BASE = 'http://localhost:8000';

function categoryFromAnimal(a: BackendAnimal) { const life=(a.lifecycle_status||'').toUpperCase(); const sex=(a.sex||'').toUpperCase(); if(life==='LACTATING')return 'Milking Cows'; if(life==='DRY')return 'Dry Cows'; if(life==='HEIFER'||life==='CLOSE_UP')return 'Heifers'; if(life==='CALF')return sex==='MALE'?'Male Calves':'Female Calves'; if(sex==='MALE'&&life==='CULLED')return 'Bulls'; return sex==='MALE'?'Bulls':'Heifers'; }
function ageFromBirthDate(value?: string|null) { if(!value)return 'Unknown'; const birth=new Date(value); if(Number.isNaN(birth.getTime()))return 'Unknown'; const now=new Date(); let years=now.getFullYear()-birth.getFullYear(); if(now.getMonth()<birth.getMonth()||(now.getMonth()===birth.getMonth()&&now.getDate()<birth.getDate()))years--; if(years>=1)return `${years} Years`; return `${Math.max(0,Math.floor((now.getTime()-birth.getTime())/2592000000))} Months`; }
function toUiAnimal(a: BackendAnimal): HerdAnimal { return { id:a.animal_id, breed:a.breed||'Unknown', category:categoryFromAnimal(a), age:ageFromBirthDate(a.date_of_birth), status:a.active===false?'Inactive':(a.status||a.lifecycle_status||'Active'), frequency:a.milking_frequency||'NONE', earTag:a.ear_tag||a.animal_id, gender:(a.sex||'').toUpperCase()==='MALE'?'Male':'Female', stage:a.lifecycle_status||undefined }; }

type ComlReminder = { month_label:string; has_official:boolean; reminder_due:boolean; reminder_status:string } | null;

export default function MainAppShell() {
  const [currentUser,setCurrentUser]=useState<{username:string;role:string;fullName:string}|null>(()=>{const saved=localStorage.getItem('dairyos_user');return saved?JSON.parse(saved):null;});
  const [currentView,setCurrentView]=useState('dashboard');
  const [selectedPassportAnimalId,setSelectedPassportAnimalId]=useState<string|null>(null);
  const [autoOpenYieldModal,setAutoOpenYieldModal]=useState(false);
  const [farmName,setFarmName]=useState(()=>localStorage.getItem('dairyos_farm_name')||'Barki Dairy Farm');
  const [farmLocation,setFarmLocation]=useState(()=>localStorage.getItem('dairyos_farm_loc')||'Lahore, Punjab, PK');
  const [currentTime,setCurrentTime]=useState(new Date());
  const [animals,setAnimals]=useState<HerdAnimal[]>([]);
  const [showNotifications,setShowNotifications]=useState(false);
  const [showAnimalModal,setShowAnimalModal]=useState(false);
  const [todayYield,setTodayYield]=useState(133);
  const [accountsReceivable,setAccountsReceivable]=useState(23400);
  const [comlReminder,setComlReminder]=useState<ComlReminder>(null);
  const { alerts, activeCount }=useAlertAudit();
  const notificationCount=activeCount+(comlReminder?.reminder_due&&!comlReminder?.has_official?1:0);

  useEffect(()=>{const timer=setInterval(()=>setCurrentTime(new Date()),1000);return()=>clearInterval(timer);},[]);
  const refreshAnimals=useCallback(async()=>{try{const r=await fetch(`${API_BASE}/farm/animals?active_only=false`);if(!r.ok)throw new Error('herd load');const records=await r.json() as BackendAnimal[];setAnimals(records.map(toUiAnimal));}catch(e){console.error('DairyOS herd register load failed:',e);}},[]);
  const refreshComlReminder=useCallback(async()=>{try{const r=await fetch(`${API_BASE}/farm/coml/current`);if(r.ok)setComlReminder(await r.json() as ComlReminder);}catch{setComlReminder(null);}},[]);
  useEffect(()=>{if(currentUser){void refreshAnimals();void refreshComlReminder();}},[currentUser,refreshAnimals,refreshComlReminder]);

  if(!currentUser)return <LoginModal onLoginSuccess={u=>setCurrentUser(u)}/>;
  const navItems=[
    {id:'dashboard',label:'Dashboard',icon:<LayoutDashboard size={13}/>},
    {id:'milk',label:'Milk',icon:<Milk size={13}/>},
    {id:'feed',label:'Feed',icon:<Wheat size={13}/>},
    {id:'finance',label:'Finance',icon:<DollarSign size={13}/>},
    {id:'breeding',label:'Breeding',icon:<Activity size={13}/>},
    {id:'health',label:'Health',icon:<HeartPulse size={13}/>},
    {id:'coml',label:'COML',icon:<Calculator size={13}/>},
    {id:'analytics',label:'Analytics',icon:<BarChart3 size={13}/>},
  ];
  const handleRegisterAnimal=(updated:HerdAnimal)=>{setAnimals(prev=>prev.some(a=>a.id===updated.id)?prev.map(a=>a.id===updated.id?updated:a):[...prev,updated]);void refreshAnimals();};
  const handleLogout=()=>{localStorage.removeItem('dairyos_token');localStorage.removeItem('dairyos_user');setCurrentUser(null);};
  const openYield=()=>{setAutoOpenYieldModal(true);setCurrentView('milk');};

  return <div className="app-shell" style={{height:'100vh',display:'flex',flexDirection:'column',background:'#0b0f19',color:'#f8fafc',overflow:'hidden',fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif'}}>
    <header style={{height:58,flexShrink:0,background:'#0f172a',borderBottom:'1px solid #1e293b',display:'flex',alignItems:'center',gap:10,padding:'0 10px',overflow:'hidden'}}>
      <div style={{display:'flex',alignItems:'center',gap:7,flexShrink:0}}><div style={{width:30,height:30,borderRadius:6,background:'#0284c7',display:'grid',placeItems:'center',fontSize:10,fontWeight:800}}>{farmName.split(' ').map(w=>w[0]).slice(0,3).join('')||'BDF'}</div><div><div style={{fontSize:12,fontWeight:800,whiteSpace:'nowrap'}}>{farmName}</div><div style={{fontSize:9,color:'#94a3b8',whiteSpace:'nowrap'}}>{farmLocation}</div></div></div>
      <nav style={{flex:1,minWidth:0,display:'flex',justifyContent:'center',gap:4,overflowX:'auto',scrollbarWidth:'none'}}>{navItems.map(tab=><button key={tab.id} onClick={()=>setCurrentView(tab.id)} style={{display:'inline-flex',alignItems:'center',gap:4,flexShrink:0,background:currentView===tab.id?'#0ea5e9':'#1e293b',color:'#fff',border:'1px solid #334155',padding:'5px 8px',borderRadius:5,fontSize:10,fontWeight:currentView===tab.id?800:600,cursor:'pointer'}}>{tab.icon}{tab.label}</button>)}</nav>
      <div style={{display:'flex',alignItems:'center',gap:6,flexShrink:0}}><div style={{fontSize:9,color:'#cbd5e1',background:'#1e293b',border:'1px solid #334155',padding:'4px 7px',borderRadius:12}}><Clock size={10} style={{verticalAlign:'middle',marginRight:4}}/>{currentTime.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'})}</div><div style={{position:'relative'}}><button onClick={()=>setShowNotifications(v=>!v)} style={{position:'relative',background:'#1e293b',border:'1px solid #334155',padding:6,borderRadius:'50%',color:'#f59e0b',cursor:'pointer'}}><Bell size={12}/>{notificationCount>0&&<span style={{position:'absolute',top:-4,right:-4,minWidth:15,height:15,borderRadius:'50%',background:'#ef4444',border:'2px solid #0f172a',fontSize:8,display:'grid',placeItems:'center'}}>{notificationCount}</span>}</button>{showNotifications&&<div style={{position:'absolute',right:0,top:34,width:'min(360px,80vw)',background:'#111827',border:'1px solid #334155',borderRadius:8,padding:10,zIndex:1000,boxShadow:'0 15px 30px rgba(0,0,0,.45)'}}><div style={{fontSize:11,fontWeight:800,marginBottom:7}}>Notifications</div>{comlReminder?.reminder_due&&!comlReminder?.has_official&&<button onClick={()=>{setCurrentView('coml');setShowNotifications(false);}} style={{display:'block',width:'100%',textAlign:'left',background:'rgba(245,158,11,.08)',border:'1px solid #f59e0b',borderRadius:5,padding:8,color:'#fcd34d',fontSize:9,marginBottom:6}}>Monthly COML reminder: {comlReminder.month_label} has no official locked value.</button>}{alerts.filter(a=>a.status!=='RESOLVED').map(a=><button key={a.id} onClick={()=>{setCurrentView('audit');setShowNotifications(false);}} style={{display:'block',width:'100%',textAlign:'left',background:'#161f30',border:'1px solid #334155',borderRadius:5,padding:8,color:'#e2e8f0',fontSize:9,marginBottom:5}}><b>{a.title}</b><div style={{color:'#94a3b8',marginTop:3}}>{a.details}</div></button>)}{notificationCount===0&&<div style={{fontSize:9,color:'#64748b'}}>No active notifications.</div>}</div>}</div><button onClick={()=>setCurrentView('settings')} style={{background:'#1e293b',border:'1px solid #334155',padding:6,borderRadius:'50%',color:'#e2e8f0',cursor:'pointer'}}><Settings size={12}/></button><div style={{display:'flex',alignItems:'center',gap:6,background:'#1e293b',border:'1px solid #334155',padding:'3px 7px',borderRadius:16}}><div style={{width:22,height:22,borderRadius:'50%',background:'#38bdf8',color:'#0f172a',display:'grid',placeItems:'center',fontSize:9,fontWeight:800}}>{currentUser.fullName.split(' ').map(n=>n[0]).slice(0,2).join('')}</div><button onClick={handleLogout} style={{background:'none',border:0,color:'#94a3b8',cursor:'pointer'}}><LogOut size={12}/></button></div></div>
    </header>

    <main style={{flex:1,minHeight:0,overflowY:'auto',overflowX:'hidden',background:'#0b0f19'}}>
      {currentView==='dashboard'&&<UnifiedDashboard onNavigate={v=>setCurrentView(v)} onOpenYieldModal={openYield} onOpenPassport={id=>setSelectedPassportAnimalId(id)} herdMasterList={animals} realTimeTodayYield={todayYield} realTimeReceivables={accountsReceivable}/>} 
      {currentView==='finance'&&<FinanceTab/>}
      {currentView==='feed'&&<FeedTab/>}
      {currentView==='coml'&&<COML/>}
      {currentView==='analytics'&&<Analytics/>}
      {currentView==='audit'&&<AuditTab/>}
      {currentView==='settings'&&<SettingsTab onFarmProfileUpdate={p=>{setFarmName(p.farmName);setFarmLocation(p.location);}}/>}
      {currentView==='milk'&&<MilkTab initialOpenModal={autoOpenYieldModal} onModalClose={()=>setAutoOpenYieldModal(false)} herdMasterList={animals} onSaveYield={litres=>setTodayYield(v=>v+litres)}/>} 
      {currentView==='health'&&<HealthTab onOpenPassport={id=>setSelectedPassportAnimalId(id)} herdMasterList={animals}/>} 
      {currentView==='breeding'&&<BreedingTab onOpenPassport={id=>setSelectedPassportAnimalId(id)} herdMasterList={animals}/>} 
      {currentView==='animals'&&<div style={{padding:14,overflowX:'auto'}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10}}><div><div style={{fontSize:16,fontWeight:800,color:'#38bdf8'}}>Herd Animals Register</div><div style={{fontSize:9,color:'#94a3b8'}}>Persistent biological passports and linked history.</div></div><button onClick={()=>setShowAnimalModal(true)} style={{background:'#38bdf8',border:0,borderRadius:5,padding:'7px 10px',fontSize:9,fontWeight:800,cursor:'pointer'}}><Plus size={12} style={{verticalAlign:'middle',marginRight:4}}/>Register Animal</button></div><div style={{background:'#111827',border:'1px solid #1f2937',borderRadius:8,overflow:'auto'}}><table style={{width:'100%',minWidth:700,borderCollapse:'collapse',fontSize:10}}><thead><tr style={{background:'#161f30',color:'#94a3b8',textAlign:'left'}}><th style={{padding:8}}>Animal</th><th style={{padding:8}}>Breed</th><th style={{padding:8}}>Category</th><th style={{padding:8}}>Age</th><th style={{padding:8}}>Frequency</th><th style={{padding:8}}>Status</th></tr></thead><tbody>{animals.map(a=><tr key={a.id} style={{borderTop:'1px solid #1a2234'}}><td style={{padding:8}}><button onClick={()=>setSelectedPassportAnimalId(a.id)} style={{background:'none',border:0,padding:0,color:'#38bdf8',fontSize:10,cursor:'pointer',textDecoration:'underline'}}>{a.id}</button></td><td style={{padding:8}}>{a.breed}</td><td style={{padding:8,color:'#cbd5e1'}}>{a.category}</td><td style={{padding:8,color:'#94a3b8'}}>{a.age}</td><td style={{padding:8,color:'#38bdf8'}}>{a.frequency}</td><td style={{padding:8,color:a.status==='Inactive'?'#94a3b8':'#34d399'}}>{a.status}</td></tr>)}</tbody></table></div></div>}
    </main>

    {selectedPassportAnimalId&&<AnimalPassportModal animalId={selectedPassportAnimalId} onClose={()=>setSelectedPassportAnimalId(null)} onSave={handleRegisterAnimal}/>} 
    {showAnimalModal&&<AnimalPassportModal animalId="NEW-ANIMAL" onClose={()=>setShowAnimalModal(false)} onSave={handleRegisterAnimal}/>} 
  </div>;
}
