import React, { useState, useEffect, useCallback } from 'react';
import UnifiedDashboard from './components/UnifiedDashboard';
import FinanceTab from './components/FinanceTab';
import FeedTab from './components/FeedTab';
import COML from './components/COML';
import Analytics from './components/Analytics';
import SettingsTab from './components/SettingsTab';
import AuditTab from './components/AuditTab';
import MilkTab from './components/MilkTab';
import HealthTab from './components/HealthTab';
import BreedingTab from './components/BreedingTab';
import AnimalTab from './components/AnimalTab';
import LoginModal from './components/LoginModal';
import AnimalPassportModal from './components/AnimalPassportModal';
import { API_BASE_URL } from './config/api';
import { useAlertAudit } from './context/AlertAuditContext';
import { clearAuth, getStoredUser, hasPermission, saveUser, installAuthenticatedFetch } from './auth';
import type { AuthUser } from './auth';
import { LayoutDashboard, Calculator, BarChart3, DollarSign, Milk, HeartPulse, Activity, Settings, Bell, LogOut, Wheat, Users } from 'lucide-react';
import './App.css';
if (typeof window !== 'undefined') installAuthenticatedFetch();

interface HerdAnimal { id:string; breed:string; category:string; age:string; status:string; frequency:string; earTag:string; gender?:string; stage?:string }
interface BackendAnimal { animal_id:string; ear_tag?:string|null; rfid?:string|null; breed?:string|null; sex?:string|null; date_of_birth?:string|null; lifecycle_status?:string|null; status?:string|null; milking_frequency?:string|null; active?:boolean; dam_id?:string|null; sire_id?:string|null; location?:string|null; production_group?:string|null }
const API_BASE=API_BASE_URL||'http://127.0.0.1:8000';
function categoryFromAnimal(animal:BackendAnimal){const lifecycle=(animal.lifecycle_status||'').toUpperCase(),sex=(animal.sex||'').toUpperCase();if(lifecycle==='LACTATING')return 'Milking Cows';if(lifecycle==='DRY')return 'Dry Cows';if(lifecycle==='HEIFER'||lifecycle==='CLOSE_UP')return sex==='MALE'?'Bulls':'Heifers';if(lifecycle==='CALF')return sex==='MALE'?'Male Calves':'Female Calves';return sex==='MALE'?'Bulls':'Heifers'}
function ageFromBirthDate(value?:string|null){if(!value)return 'Unknown';const birth=new Date(value);if(Number.isNaN(birth.getTime()))return 'Unknown';const now=new Date();let years=now.getFullYear()-birth.getFullYear();const before=now.getMonth()<birth.getMonth()||(now.getMonth()===birth.getMonth()&&now.getDate()<birth.getDate());if(before)years-=1;if(years>=1)return `${years} Years`;return `${Math.max(0,Math.floor((now.getTime()-birth.getTime())/2592000000))} Months`}
function toUiAnimal(animal:BackendAnimal):HerdAnimal{return{id:animal.animal_id,breed:animal.breed||'Unknown',category:categoryFromAnimal(animal),age:ageFromBirthDate(animal.date_of_birth),status:animal.active===false?(animal.status||'Inactive'):(animal.status||animal.lifecycle_status||'Active'),frequency:animal.milking_frequency||'NONE',earTag:animal.ear_tag||animal.animal_id,gender:(animal.sex||'').toUpperCase()==='MALE'?'Male':'Female',stage:animal.lifecycle_status||undefined}}

export default function MainAppShell(){
 const [currentUser,setCurrentUser]=useState<AuthUser|null>(()=>getStoredUser());
 const [currentView,setCurrentView]=useState('dashboard'),[selectedPassportAnimalId,setSelectedPassportAnimalId]=useState<string|null>(null),[autoOpenYieldModal,setAutoOpenYieldModal]=useState(false);
 const [farmName,setFarmName]=useState(()=>localStorage.getItem('dairyos_farm_name')||'Barki Dairy Farm'),[farmLocation,setFarmLocation]=useState(()=>localStorage.getItem('dairyos_farm_loc')||'Lahore, Punjab, PK');
 const {alerts,activeCount}=useAlertAudit();const [showNotifications,setShowNotifications]=useState(false);
 const [animals,setAnimals]=useState<BackendAnimal[]>([]);const [showAnimalModal,setShowAnimalModal]=useState(false),[todayYield,setTodayYield]=useState(0),[todayMilkSoldLiters,setTodayMilkSoldLiters]=useState(0),[accountsReceivable,setAccountsReceivable]=useState(0);
 const refreshAnimals=useCallback(async()=>{if(!hasPermission('animals.view',currentUser))return;try{const response=await fetch(`${API_BASE}/farm/animals?active_only=false`);if(!response.ok)throw new Error(`Unable to load herd (${response.status})`);setAnimals(await response.json() as BackendAnimal[])}catch(error){console.error('DairyOS herd register load failed:',error)}},[currentUser]);
 useEffect(()=>{
  if(!currentUser||currentUser.permissions?.length)return;
  let active=true;
  const token=localStorage.getItem('dairyos_token');
  void fetch(`${API_BASE}/authz/permissions`,{
   headers: token ? {Authorization:`Bearer ${token}`} : undefined,
  }).then(async response=>{
   if(!response.ok)return;
   const data=await response.json();
   if(active){
    const updated={...currentUser,permissions:data.permissions??[]};
    saveUser(updated);
    setCurrentUser(updated);
   }
  }).catch(()=>{});
  return()=>{active=false};
 },[currentUser?.username]);
 useEffect(()=>{if(currentUser)void refreshAnimals()},[currentUser,refreshAnimals]);
 const handleOpenYieldEntry=()=>{if(hasPermission('milk.create',currentUser)){setAutoOpenYieldModal(true);setCurrentView('milk')}};
 const handleLogout=()=>{clearAuth();setCurrentUser(null)};const handleRegisterAnimal=()=>{void refreshAnimals()};
 const herdMasterList=animals.map(toUiAnimal);
 if(!currentUser)return <LoginModal onLoginSuccess={u=>setCurrentUser(u as AuthUser)}/>;
 const navItems=[
  {id:'dashboard',label:'Dashboard',permission:'dashboard.view',icon:<LayoutDashboard size={14}/>},
  {id:'animals',label:'Animals',permission:'animals.view',icon:<Users size={14}/>},
  {id:'milk',label:'Milk',permission:'milk.view',icon:<Milk size={14}/>},
  {id:'feed',label:'Feed',permission:'feed.view',icon:<Wheat size={14}/>},
  {id:'finance',label:'Finance',permission:'finance.view',icon:<DollarSign size={14}/>},
  {id:'breeding',label:'Breeding',permission:'breeding.view',icon:<Activity size={14}/>},
  {id:'health',label:'Health',permission:'health.view',icon:<HeartPulse size={14}/>},
  {id:'coml',label:'COML',permission:'coml.view',icon:<Calculator size={14}/>},
  {id:'analytics',label:'Analytics',permission:'analytics.view',icon:<BarChart3 size={14}/>},
 ].filter(tab=>hasPermission(tab.permission,currentUser));
 const canSettings=hasPermission('settings.view',currentUser);
 const canAudit=hasPermission('audit.view',currentUser);
 return <div className="app-shell" style={{display:'flex',flexDirection:'column',height:'100vh',minWidth:0,background:'#0b0f19',color:'#f8fafc',overflow:'hidden',fontFamily:'sans-serif'}}>
  <header style={{height:60,background:'#0f172a',borderBottom:'1px solid #1e293b',display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 12px',zIndex:50,flexShrink:0,boxShadow:'0 4px 6px -1px rgba(0,0,0,.3)',minWidth:0}}>
   <div style={{display:'flex',alignItems:'center',gap:8,flexShrink:0}}><div style={{width:32,height:32,borderRadius:6,background:'#0284c7',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontWeight:'bold',fontSize:12}}>{farmName.split(' ').map(w=>w[0]).slice(0,3).join('')||'BDF'}</div><div style={{display:'flex',flexDirection:'column'}}><h1 style={{margin:0,fontSize:13,fontWeight:'bold',whiteSpace:'nowrap'}}>{farmName}</h1><span style={{fontSize:10,color:'#94a3b8',whiteSpace:'nowrap'}}>{farmLocation}</span></div></div>
   <nav style={{display:'flex',gap:6,justifyContent:'center',flex:1,minWidth:0,margin:'0 12px',overflowX:'auto',overflowY:'hidden',scrollbarWidth:'thin'}}>{navItems.map(tab=>{const isActive=currentView===tab.id;return <button key={tab.id} onClick={()=>setCurrentView(tab.id)} style={{display:'flex',alignItems:'center',gap:4,flex:'0 0 auto',background:isActive?'#0ea5e9':'#1e293b',color:isActive?'#fff':'#e2e8f0',border:isActive?'1px solid #7dd3fc':'1px solid #334155',padding:'6px 10px',borderRadius:6,cursor:'pointer',fontSize:11,fontWeight:isActive?'bold':'600',whiteSpace:'nowrap'}}>{tab.icon} {tab.label}</button>})}</nav>
   <div style={{display:'flex',alignItems:'center',gap:8,flexShrink:0}}><div style={{position:'relative'}}><button onClick={()=>setShowNotifications(!showNotifications)} style={{position:'relative',background:'#1e293b',border:'1px solid #334155',padding:6,borderRadius:'50%',color:'#f59e0b',cursor:'pointer',display:'flex'}}><Bell size={14}/>{activeCount>0&&<span style={{position:'absolute',top:-4,right:-4,minWidth:16,height:16,background:'#ef4444',border:'2px solid #0f172a',borderRadius:'50%',color:'#fff',fontSize:9,fontWeight:'bold',display:'flex',alignItems:'center',justifyContent:'center'}}>{activeCount}</span>}</button>{showNotifications&&<div style={{position:'absolute',right:0,top:40,width:380,maxWidth:'min(380px,calc(100vw - 20px))',background:'#111827',border:'1px solid #1f2937',borderRadius:8,boxShadow:'0 20px 25px -5px rgba(0,0,0,.75)',padding:12,zIndex:100}}><div style={{fontSize:12,fontWeight:'bold',borderBottom:'1px solid #1f2937',paddingBottom:8,marginBottom:8,display:'flex',justifyContent:'space-between',alignItems:'center',gap:8}}><span>Active Warnings ({activeCount})</span>{canAudit&&<button onClick={()=>{setCurrentView('audit');setShowNotifications(false)}} style={{background:'none',border:'none',color:'#38bdf8',fontSize:11,cursor:'pointer',textDecoration:'underline'}}>Open Full Audit Register</button>}</div><div style={{display:'flex',flexDirection:'column',gap:8,maxHeight:340,overflowY:'auto'}}>{alerts.filter(a=>a.status!=='RESOLVED').map(n=>{const isReinstated=n.status==='REINSTATED';return <div key={n.id} onClick={()=>canAudit&&setCurrentView('audit')} style={{fontSize:11,background:isReinstated?'rgba(239,68,68,.3)':'#161f30',padding:9,borderRadius:6,borderLeft:`4px solid ${isReinstated?'#dc2626':n.currentLevel==='RED'?'#ef4444':'#f59e0b'}`,cursor:canAudit?'pointer':'default'}}><div style={{color:isReinstated?'#fee2e2':'#e2e8f0',fontWeight:'bold'}}>{isReinstated&&'ðŸš¨ '}{n.title}</div><div style={{fontSize:10,color:isReinstated?'#fca5a5':'#94a3b8',marginTop:4}}>{n.details}</div></div>})}</div></div>}</div>
    {canSettings&&<button onClick={()=>setCurrentView('settings')} style={{background:currentView==='settings'?'#0ea5e9':'#1e293b',border:currentView==='settings'?'1px solid #7dd3fc':'1px solid #334155',padding:6,borderRadius:'50%',color:'#e2e8f0',cursor:'pointer',display:'flex'}}><Settings size={14}/></button>}
    <button
    type="button"
    onClick={handleLogout}
    title={`Signed in as ${currentUser.fullName} (${currentUser.role}). Click to sign out.`}
    style={{
      display:'flex',
      alignItems:'center',
      gap:8,
      background:'#1e293b',
      border:'1px solid #334155',
      padding:'4px 8px',
      borderRadius:20,
      color:'#e2e8f0',
      cursor:'pointer'
    }}
  >
    <div
      style={{
        width:24,
        height:24,
        borderRadius:'50%',
        background:'#38bdf8',
        color:'#0f172a',
        display:'flex',
        alignItems:'center',
        justifyContent:'center',
        fontWeight:'bold',
        fontSize:11
      }}
    >
      {currentUser.fullName.split(' ').map(n=>n[0]).slice(0,2).join('')}
    </div>
    <span style={{fontSize:10,fontWeight:700}}>{currentUser.role}</span>
    <LogOut size={14} color="#94a3b8"/>
  </button>
   </div>
  </header>
  <main style={{flex:1,minHeight:0,minWidth:0,overflowY:'auto',overflowX:'hidden',background:'#0b0f19',position:'relative'}}>
   {currentView==='dashboard'&&hasPermission('dashboard.view',currentUser)&&<UnifiedDashboard onNavigate={v=>hasPermission(`${v}.view`,currentUser)&&setCurrentView(v)} onOpenYieldModal={handleOpenYieldEntry} onOpenPassport={id=>hasPermission('animals.view',currentUser)&&setSelectedPassportAnimalId(id)} herdMasterList={herdMasterList} realTimeTodayYield={todayYield} realTimeReceivables={accountsReceivable}/>}
   {currentView==='animals'&&hasPermission('animals.view',currentUser)&&<AnimalTab animals={animals} onOpenPassport={id=>setSelectedPassportAnimalId(id)} onRegister={()=>hasPermission('animals.create',currentUser)&&setShowAnimalModal(true)} onRefresh={refreshAnimals}/>}
   {currentView==='finance'&&hasPermission('finance.view',currentUser)&&<FinanceTab onSaveSale={liters=>setTodayMilkSoldLiters(prev=>prev+liters)} onUpdateReceivables={setAccountsReceivable}/>}
   {currentView==='feed'&&hasPermission('feed.view',currentUser)&&<FeedTab/>}
   {currentView==='coml'&&hasPermission('coml.view',currentUser)&&<COML/>}{currentView==='analytics'&&hasPermission('analytics.view',currentUser)&&<Analytics/>}{currentView==='audit'&&canAudit&&<AuditTab/>}{currentView==='settings'&&canSettings&&<SettingsTab onFarmProfileUpdate={p=>{setFarmName(p.farmName);setFarmLocation(p.location)}}/>}
   {currentView==='milk'&&hasPermission('milk.view',currentUser)&&<MilkTab initialOpenModal={autoOpenYieldModal} onModalClose={()=>setAutoOpenYieldModal(false)} herdMasterList={herdMasterList} onSaveYield={added=>setTodayYield(prev=>prev+added)} realTimeTodaySold={todayMilkSoldLiters}/>}
   {currentView==='health'&&hasPermission('health.view',currentUser)&&<HealthTab onOpenPassport={id=>setSelectedPassportAnimalId(id)} herdMasterList={herdMasterList}/>} {currentView==='breeding'&&hasPermission('breeding.view',currentUser)&&<BreedingTab onOpenPassport={id=>setSelectedPassportAnimalId(id)} herdMasterList={herdMasterList}/>}
  </main>
  {selectedPassportAnimalId&&hasPermission('animals.view',currentUser)&&<AnimalPassportModal animalId={selectedPassportAnimalId} onClose={()=>setSelectedPassportAnimalId(null)} onSave={handleRegisterAnimal}/>} {showAnimalModal&&hasPermission('animals.create',currentUser)&&<AnimalPassportModal animalId="NEW-ANIMAL" onClose={()=>setShowAnimalModal(false)} onSave={handleRegisterAnimal}/>}
 </div>
}
