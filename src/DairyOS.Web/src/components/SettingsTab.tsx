import React, { useEffect, useState } from 'react';
import { Building, ShieldCheck, Sliders, Save, UserPlus, UserX, UserCheck } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { getStoredUser, hasPermission } from '../auth';

interface SettingsTabProps { onFarmProfileUpdate?: (profile: { farmName: string; location: string }) => void; }
type UserRow = { id:number; username:string; role:string; active:boolean };
type Matrix = { permissions:string[]; roles:Record<string,{description:string;permissions:string[]}> };
const API_BASE=API_BASE_URL||'http://127.0.0.1:8000';

export default function SettingsTab({ onFarmProfileUpdate }: SettingsTabProps) {
  const [activeTab,setActiveTab]=useState<'FARM'|'STANDARDS'|'USERS'>('FARM');
  const [farmName,setFarmName]=useState(localStorage.getItem('dairyos_farm_name')||'Barki Dairy Farm');
  const [location,setLocation]=useState(localStorage.getItem('dairyos_farm_loc')||'Lahore, Punjab, PK');
  const [timezone,setTimezone]=useState(localStorage.getItem('dairyos_timezone')||'Asia/Karachi (PKT +05:00)');
  const [users,setUsers]=useState<UserRow[]>([]),[matrix,setMatrix]=useState<Matrix|null>(null),[newUsername,setNewUsername]=useState(''),[newPassword,setNewPassword]=useState(''),[newRole,setNewRole]=useState('MANAGER'),[error,setError]=useState(''),[message,setMessage]=useState('');
  const isOwner=hasPermission('users.view');

  const loadUsers=async()=>{if(!isOwner)return;setError('');try{const [u,m]=await Promise.all([fetch(`${API_BASE}/auth/users`),fetch(`${API_BASE}/authz/matrix`)]);if(!u.ok||!m.ok)throw new Error('User administration is unavailable.');setUsers((await u.json()).users??[]);setMatrix(await m.json())}catch(e){setError(e instanceof Error?e.message:'Unable to load users.')}};
  useEffect(()=>{if(activeTab==='USERS')void loadUsers()},[activeTab]);
  const handleSaveFarm=()=>{localStorage.setItem('dairyos_farm_name',farmName);localStorage.setItem('dairyos_farm_loc',location);onFarmProfileUpdate?.({farmName,location});window.dispatchEvent(new Event('storage'));setMessage('Farm profile saved successfully.')};
  const handleSaveStandards=()=>{localStorage.setItem('dairyos_timezone',timezone);setMessage('Standards saved successfully.')};
  const createUser=async(e:React.FormEvent)=>{e.preventDefault();setError('');setMessage('');try{const r=await fetch(`${API_BASE}/auth/users`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:newUsername,password:newPassword,role:newRole})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to create user.');setNewUsername('');setNewPassword('');setMessage(`User ${d.username} created.`);await loadUsers()}catch(e){setError(e instanceof Error?e.message:'Unable to create user.')}};
  const setActive=async(u:UserRow)=>{setError('');setMessage('');try{const r=await fetch(`${API_BASE}/authz/users/${encodeURIComponent(u.username)}/active`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:!u.active})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to update user.');setMessage(`${d.username} is now ${d.active?'active':'disabled'}.`);await loadUsers()}catch(e){setError(e instanceof Error?e.message:'Unable to update user.')}};

  return <div style={{padding:24,color:'#fff',height:'100%',overflowY:'auto'}}>
    <h2 style={{color:'#38bdf8',marginBottom:20}}>System Settings</h2>
    <div style={{display:'flex',gap:20,marginBottom:20,borderBottom:'1px solid #1f2937',flexWrap:'wrap'}}>
      <button onClick={()=>setActiveTab('FARM')} style={{background:'none',border:0,color:activeTab==='FARM'?'#38bdf8':'#94a3b8',padding:10,cursor:'pointer',borderBottom:activeTab==='FARM'?'2px solid #38bdf8':'none'}}><Building size={13} style={{marginRight:5,verticalAlign:'middle'}}/>Farm Profile</button>
      <button onClick={()=>setActiveTab('STANDARDS')} style={{background:'none',border:0,color:activeTab==='STANDARDS'?'#38bdf8':'#94a3b8',padding:10,cursor:'pointer',borderBottom:activeTab==='STANDARDS'?'2px solid #38bdf8':'none'}}><Sliders size={13} style={{marginRight:5,verticalAlign:'middle'}}/>Standards</button>
      {isOwner&&<button onClick={()=>setActiveTab('USERS')} style={{background:'none',border:0,color:activeTab==='USERS'?'#38bdf8':'#94a3b8',padding:10,cursor:'pointer',borderBottom:activeTab==='USERS'?'2px solid #38bdf8':'none'}}><ShieldCheck size={13} style={{marginRight:5,verticalAlign:'middle'}}/>Users & Access</button>}
    </div>
    {error&&<div style={{background:'#450a0a',border:'1px solid #7f1d1d',color:'#fecaca',padding:10,borderRadius:6,marginBottom:12,fontSize:11}}>{error}</div>}
    {message&&<div style={{background:'#064e3b',border:'1px solid #065f46',color:'#a7f3d0',padding:10,borderRadius:6,marginBottom:12,fontSize:11}}>{message}</div>}
    {activeTab==='FARM'&&<div style={{background:'#111827',padding:20,borderRadius:8,maxWidth:440}}><label style={{fontSize:11,color:'#94a3b8'}}>Farm Name</label><input value={farmName} onChange={e=>setFarmName(e.target.value)} style={field}/><label style={{fontSize:11,color:'#94a3b8'}}>Location</label><input value={location} onChange={e=>setLocation(e.target.value)} style={field}/><button onClick={handleSaveFarm} style={button}><Save size={14}/>Save Farm</button></div>}
    {activeTab==='STANDARDS'&&<div style={{background:'#111827',padding:20,borderRadius:8,maxWidth:440}}><label style={{fontSize:11,color:'#94a3b8'}}>Timezone</label><select value={timezone} onChange={e=>setTimezone(e.target.value)} style={field}><option>Asia/Karachi (PKT +05:00)</option><option>UTC</option></select><button onClick={handleSaveStandards} style={button}><Save size={14}/>Save Standards</button></div>}
    {activeTab==='USERS'&&isOwner&&<div style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(320px,420px)',gap:14,alignItems:'start'}}>
      <section style={card}><h3 style={title}>Users</h3>{users.map(u=><div key={u.id} style={row}><div style={{flex:1}}><strong>{u.username}</strong><div style={muted}>{u.role} • {u.active?'Active':'Disabled'}</div></div><button onClick={()=>void setActive(u)} style={{...small, color:u.active?'#fca5a5':'#86efac'}}>{u.active?<UserX size={13}/>:<UserCheck size={13}/>} {u.active?'Disable':'Enable'}</button></div>)}{users.length===0&&<div style={empty}>No persisted users found.</div>}</section>
      <div style={{display:'grid',gap:14}}>
        <form onSubmit={createUser} style={card}><h3 style={title}>Add User</h3><input required placeholder="Username" value={newUsername} onChange={e=>setNewUsername(e.target.value)} style={field}/><input required type="password" placeholder="Temporary password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} style={field}/><select value={newRole} onChange={e=>setNewRole(e.target.value)} style={field}>{Object.keys(matrix?.roles||{OWNER:{},MANAGER:{},MILKER:{}}).map(role=><option key={role}>{role}</option>)}</select><button type="submit" style={button}><UserPlus size={14}/>Create User</button></form>
        <section style={card}><h3 style={title}>Permission Matrix</h3>{matrix&&Object.entries(matrix.roles).map(([role,data])=><div key={role} style={{marginBottom:12,paddingBottom:10,borderBottom:'1px solid #1f2937'}}><strong>{role}</strong><div style={muted}>{data.description}</div><div style={{display:'flex',flexWrap:'wrap',gap:4,marginTop:6}}>{data.permissions.map(p=><span key={p} style={{fontSize:8,padding:'3px 5px',background:'#1e293b',border:'1px solid #334155',borderRadius:4,color:'#cbd5e1'}}>{p}</span>)}</div></div>)}</section>
      </div>
    </div>}
  </div>;
}

const field:React.CSSProperties={width:'100%',boxSizing:'border-box',background:'#1e293b',color:'#fff',padding:8,marginBottom:10,border:'1px solid #334155',borderRadius:5};
const button:React.CSSProperties={background:'#38bdf8',padding:'8px 12px',border:'none',cursor:'pointer',fontWeight:'bold',display:'inline-flex',alignItems:'center',gap:5,borderRadius:5};
const card:React.CSSProperties={background:'#111827',padding:16,borderRadius:8,border:'1px solid #1f2937'};
const title:React.CSSProperties={fontSize:13,margin:'0 0 10px'};
const row:React.CSSProperties={display:'flex',alignItems:'center',gap:8,padding:'9px 0',borderBottom:'1px solid #1f2937'};
const muted:React.CSSProperties={fontSize:9,color:'#64748b'};
const small:React.CSSProperties={background:'#1e293b',border:'1px solid #334155',color:'#cbd5e1',padding:'6px 8px',borderRadius:4,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:4};
const empty:React.CSSProperties={padding:12,color:'#64748b',fontSize:10};
