import React, { useEffect, useMemo, useState } from 'react';
import { Building, KeyRound, Mail, Save, ShieldCheck, Sliders, UserCheck, UserPlus, UserX } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { hasPermission } from '../auth';

interface SettingsTabProps { onFarmProfileUpdate?: (profile: { farmName: string; location: string }) => void; }
type UserRow = { id:number; username:string; role:string; active:boolean };
type Profile = UserRow & { job_title:string|null; personal_email:string|null; permissions:string[] };
type Matrix = { permissions:string[]; groups:Record<string,string[]>; roles:Record<string,{description:string;permissions:string[]}> };
type EmailConfig = { configured:boolean; source?:string; sender_email?:string; sender_display_name?:string; smtp_host?:string; smtp_port?:number; smtp_username?:string; use_tls?:boolean; password_configured?:boolean };
const API_BASE=API_BASE_URL||'http://127.0.0.1:8000';

export default function SettingsTab({ onFarmProfileUpdate }: SettingsTabProps) {
  const [activeTab,setActiveTab]=useState<'FARM'|'STANDARDS'|'USERS'|'EMAIL'|'SECURITY'>('FARM');
  const [farmName,setFarmName]=useState(localStorage.getItem('dairyos_farm_name')||'Barki Dairy Farm');
  const [location,setLocation]=useState(localStorage.getItem('dairyos_farm_loc')||'Lahore, Punjab, PK');
  const [timezone,setTimezone]=useState(localStorage.getItem('dairyos_timezone')||'Asia/Karachi (PKT +05:00)');
  const [users,setUsers]=useState<UserRow[]>([]),[matrix,setMatrix]=useState<Matrix|null>(null),[selected,setSelected]=useState<Profile|null>(null);
  const [newUsername,setNewUsername]=useState(''),[newPassword,setNewPassword]=useState(''),[newRole,setNewRole]=useState('CUSTOM'),[newTitle,setNewTitle]=useState(''),[newEmail,setNewEmail]=useState('');
  const [permissions,setPermissions]=useState<string[]>([]);
  const [emailConfig,setEmailConfig]=useState<EmailConfig>({configured:false}),[emailPassword,setEmailPassword]=useState(''),[testRecipient,setTestRecipient]=useState('');
  const [currentPassword,setCurrentPassword]=useState(''),[replacementPassword,setReplacementPassword]=useState(''),[replacementPassword2,setReplacementPassword2]=useState('');
  const [error,setError]=useState(''),[message,setMessage]=useState('');
  const canUsers=hasPermission('users.view');
  const canEmail=hasPermission('settings.email');

  const loadUsers=async()=>{if(!canUsers)return;setError('');try{const [u,m]=await Promise.all([fetch(`${API_BASE}/users`),fetch(`${API_BASE}/authz/matrix`)]);if(!u.ok||!m.ok)throw new Error('User administration is unavailable.');setUsers((await u.json()).users??[]);setMatrix(await m.json())}catch(e){setError(e instanceof Error?e.message:'Unable to load users.')}};
  const loadEmail=async()=>{if(!canEmail)return;try{const r=await fetch(`${API_BASE}/settings/email`);if(r.ok)setEmailConfig(await r.json())}catch(e){console.error(e)}};
  useEffect(()=>{if(activeTab==='USERS')void loadUsers();if(activeTab==='EMAIL')void loadEmail()},[activeTab]);

  const applyPreset=(role:string)=>setPermissions(matrix?.roles?.[role]?.permissions??[]);
  const togglePermission=(permission:string)=>setPermissions(prev=>prev.includes(permission)?prev.filter(p=>p!==permission):[...prev,permission]);
  const selectedCount=permissions.length;
  const allPermissions=useMemo(()=>matrix?.permissions??[],[matrix]);

  const handleSaveFarm=()=>{localStorage.setItem('dairyos_farm_name',farmName);localStorage.setItem('dairyos_farm_loc',location);onFarmProfileUpdate?.({farmName,location});window.dispatchEvent(new Event('storage'));setMessage('Farm profile saved successfully.')};
  const handleSaveStandards=()=>{localStorage.setItem('dairyos_timezone',timezone);setMessage('Standards saved successfully.')};

  const createUser=async(e:React.FormEvent)=>{e.preventDefault();setError('');setMessage('');try{
    const r=await fetch(`${API_BASE}/users`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:newUsername,password:newPassword,role:newRole})});
    const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to create user.');
    const p=await fetch(`${API_BASE}/authz/users/${encodeURIComponent(newUsername)}/profile`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_title:newTitle||null,personal_email:newEmail||null,permissions})});
    const pd=await p.json();if(!p.ok)throw new Error(pd.detail||'User was created but the access profile could not be saved.');
    setNewUsername('');setNewPassword('');setNewTitle('');setNewEmail('');setNewRole('CUSTOM');setPermissions([]);setMessage(`User ${d.username} created with ${pd.permissions.length} enabled permissions.`);await loadUsers();
  }catch(e){setError(e instanceof Error?e.message:'Unable to create user.')}};

  const openUser=async(username:string)=>{try{const r=await fetch(`${API_BASE}/authz/users/${encodeURIComponent(username)}/profile`);const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to load user profile.');setSelected(d);setPermissions(d.permissions??[])}catch(e){setError(e instanceof Error?e.message:'Unable to load user profile.')}};
  const saveUserProfile=async()=>{if(!selected)return;setError('');setMessage('');try{const r=await fetch(`${API_BASE}/authz/users/${encodeURIComponent(selected.username)}/profile`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({job_title:selected.job_title||null,personal_email:selected.personal_email||null,permissions})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to save user access.');setSelected({...selected,...d});setMessage(`Access saved for ${d.username}.`);await loadUsers()}catch(e){setError(e instanceof Error?e.message:'Unable to save user access.')}};
  const setActive=async(u:UserRow)=>{setError('');setMessage('');try{const r=await fetch(`${API_BASE}/authz/users/${encodeURIComponent(u.username)}/active`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:!u.active})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to update user.');setMessage(`${d.username} is now ${d.active?'active':'disabled'}.`);await loadUsers()}catch(e){setError(e instanceof Error?e.message:'Unable to update user.')}};
  const saveEmail=async()=>{setError('');setMessage('');try{const r=await fetch(`${API_BASE}/settings/email`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...emailConfig,smtp_password:emailPassword||undefined})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to save email settings.');setEmailConfig(d);setEmailPassword('');setMessage('DairyOS sender settings saved.')}catch(e){setError(e instanceof Error?e.message:'Unable to save email settings.')}};
  const sendTest=async()=>{setError('');setMessage('');try{const r=await fetch(`${API_BASE}/settings/email/test`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recipient:testRecipient})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Test email failed.');setMessage(`Test email sent to ${d.recipient}.`)}catch(e){setError(e instanceof Error?e.message:'Test email failed.')}};
  const changePassword=async()=>{setError('');setMessage('');if(!replacementPassword||replacementPassword!==replacementPassword2){setError('New passwords must be present and match.');return;}try{const r=await fetch(`${API_BASE}/me/password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:currentPassword,new_password:replacementPassword})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Unable to change password.');setCurrentPassword('');setReplacementPassword('');setReplacementPassword2('');setMessage(`Password changed for ${d.username}.`)}catch(e){setError(e instanceof Error?e.message:'Unable to change password.')}};

  return <div style={{padding:24,color:'#fff',height:'100%',overflowY:'auto'}}>
    <h2 style={{color:'#38bdf8',marginBottom:20}}>System Settings</h2>
    <div style={{display:'flex',gap:20,marginBottom:20,borderBottom:'1px solid #1f2937',flexWrap:'wrap'}}>
      <button onClick={()=>setActiveTab('FARM')} style={tabStyle(activeTab==='FARM')}><Building size={13}/>Farm Profile</button>
      <button onClick={()=>setActiveTab('STANDARDS')} style={tabStyle(activeTab==='STANDARDS')}><Sliders size={13}/>Standards</button>
      {canUsers&&<button onClick={()=>setActiveTab('USERS')} style={tabStyle(activeTab==='USERS')}><ShieldCheck size={13}/>Users & Access</button>}
      {canEmail&&<button onClick={()=>setActiveTab('EMAIL')} style={tabStyle(activeTab==='EMAIL')}><Mail size={13}/>Email</button>}
      <button onClick={()=>setActiveTab('SECURITY')} style={tabStyle(activeTab==='SECURITY')}><KeyRound size={13}/>Security</button>
    </div>
    {error&&<div style={{background:'#450a0a',border:'1px solid #7f1d1d',color:'#fecaca',padding:10,borderRadius:6,marginBottom:12,fontSize:11}}>{error}</div>}
    {message&&<div style={{background:'#064e3b',border:'1px solid #065f46',color:'#a7f3d0',padding:10,borderRadius:6,marginBottom:12,fontSize:11}}>{message}</div>}
    {activeTab==='FARM'&&<div style={{background:'#111827',padding:20,borderRadius:8,maxWidth:440}}><label style={label}>Farm Name</label><input value={farmName} onChange={e=>setFarmName(e.target.value)} style={field}/><label style={label}>Location</label><input value={location} onChange={e=>setLocation(e.target.value)} style={field}/><button onClick={handleSaveFarm} style={button}><Save size={14}/>Save Farm</button></div>}
    {activeTab==='STANDARDS'&&<div style={{background:'#111827',padding:20,borderRadius:8,maxWidth:440}}><label style={label}>Timezone</label><select value={timezone} onChange={e=>setTimezone(e.target.value)} style={field}><option>Asia/Karachi (PKT +05:00)</option><option>UTC</option></select><button onClick={handleSaveStandards} style={button}><Save size={14}/>Save Standards</button></div>}
    {activeTab==='SECURITY'&&<section style={{...card,maxWidth:520}}><h3 style={title}><KeyRound size={14}/>Change My Password</h3><div style={muted}>Change the current account password. For the default admin account, the new password is persisted securely without modifying the deployment environment file.</div><label style={label}>Current password</label><input type="password" value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)} style={field}/><label style={label}>New password</label><input type="password" value={replacementPassword} onChange={e=>setReplacementPassword(e.target.value)} style={field}/><label style={label}>Confirm new password</label><input type="password" value={replacementPassword2} onChange={e=>setReplacementPassword2(e.target.value)} style={field}/><button onClick={changePassword} style={button}><KeyRound size={14}/>Change Password</button></section>}
    {activeTab==='USERS'&&canUsers&&<div style={{display:'grid',gridTemplateColumns:'minmax(260px,360px) minmax(0,1fr)',gap:14,alignItems:'start'}}>
      <div style={{display:'grid',gap:14}}>
        <section style={card}><h3 style={title}>Users</h3>{users.map(u=><div key={u.id} style={row}><div style={{flex:1,cursor:'pointer'}} onClick={()=>void openUser(u.username)}><strong>{u.username}</strong><div style={muted}>{u.role==='CUSTOM'?'Custom access':u.role} {u.active?'• Active':'• Disabled'}</div></div><button onClick={()=>void setActive(u)} style={{...small,color:u.active?'#fca5a5':'#86efac'}}>{u.active?<UserX size={13}/>:<UserCheck size={13}/>} {u.active?'Disable':'Enable'}</button></div>)}{users.length===0&&<div style={empty}>No persisted users found.</div>}</section>
        <form onSubmit={createUser} style={card}>
          <h3 style={title}><UserPlus size={14}/> Add User</h3>
          <input required placeholder="Username" value={newUsername} onChange={e=>setNewUsername(e.target.value)} style={field}/>
          <input required type="password" placeholder="Temporary password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} style={field}/>
          <input placeholder="Job title / designation (optional)" value={newTitle} onChange={e=>setNewTitle(e.target.value)} style={field}/>
          <input type="email" placeholder="Personal email (optional)" value={newEmail} onChange={e=>setNewEmail(e.target.value)} style={field}/>
          <label style={label}>Access preset (optional)</label>
          <select value={newRole} onChange={e=>{setNewRole(e.target.value);applyPreset(e.target.value)}} style={field}><option value="CUSTOM">Custom — define permissions manually</option><option value="OWNER">Owner preset</option><option value="MANAGER">Manager preset</option><option value="MILKER">Milker preset</option></select>
          <div style={muted}>The preset is only a starting point. A custom user is not limited to any predefined job category.</div>
          <button type="submit" style={button}><UserPlus size={14}/>Create User</button>
        </form>
      </div>
      <div style={{display:'grid',gap:14}}>
        {selected&&<section style={card}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:12}}><div><h3 style={title}>Access Profile — {selected.username}</h3><div style={muted}>{selected.role==='CUSTOM'?'Custom access':selected.role} {selected.job_title?`• ${selected.job_title}`:''}</div></div><button type="button" onClick={()=>setSelected(null)} style={small}>Close</button></div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,marginBottom:12}}><input placeholder="Job title / designation" value={selected.job_title??''} onChange={e=>setSelected({...selected,job_title:e.target.value})} style={field}/><input type="email" placeholder="Personal email (optional)" value={selected.personal_email??''} onChange={e=>setSelected({...selected,personal_email:e.target.value})} style={field}/></div>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}><strong style={{fontSize:12}}>Visibility & Entry Permissions</strong><span style={muted}>{selectedCount} enabled</span></div>
          {matrix&&Object.entries(matrix.groups).map(([group,groupPermissions])=><div key={group} style={{borderTop:'1px solid #1f2937',padding:'10px 0'}}><div style={{fontSize:11,fontWeight:700,marginBottom:6}}>{group}</div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:6}}>{groupPermissions.map(permission=><label key={permission} style={{display:'flex',alignItems:'center',gap:6,fontSize:9,color:'#cbd5e1',background:'#0f172a',padding:'6px 8px',borderRadius:5,border:'1px solid #1e293b'}}><input type="checkbox" checked={permissions.includes(permission)} onChange={()=>togglePermission(permission)}/>{permission}</label>)}</div></div>)}
          <div style={{display:'flex',gap:8,marginTop:10}}><button onClick={saveUserProfile} style={button}><Save size={14}/>Save Access</button><button type="button" onClick={()=>setPermissions(allPermissions)} style={small}>Grant All</button><button type="button" onClick={()=>setPermissions([])} style={small}>Clear All</button></div>
        </section>}
        {!selected&&<section style={card}><h3 style={title}>Flexible Access Model</h3><div style={muted}>Job titles describe the person. Saved permissions determine what the person can see, enter, edit, approve, or administer. OWNER/MANAGER/MILKER are optional presets, not limits on the types of users you can create.</div><div style={{marginTop:12,fontSize:10,color:'#94a3b8'}}>Select a user on the left to edit their profile.</div></section>}
      </div>
    </div>}
    {activeTab==='EMAIL'&&canEmail&&<div style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(320px,420px)',gap:14,alignItems:'start'}}>
      <section style={card}><h3 style={title}>DairyOS Sender</h3><div style={muted}>All nightly digests and DairyOS-generated email are sent using this identity. Database settings override deployment defaults.</div><label style={label}>From email</label><input type="email" value={emailConfig.sender_email??''} onChange={e=>setEmailConfig({...emailConfig,sender_email:e.target.value})} style={field}/><label style={label}>Display name</label><input value={emailConfig.sender_display_name??''} onChange={e=>setEmailConfig({...emailConfig,sender_display_name:e.target.value})} style={field}/><label style={label}>SMTP host</label><input value={emailConfig.smtp_host??''} onChange={e=>setEmailConfig({...emailConfig,smtp_host:e.target.value})} style={field}/><div style={{display:'grid',gridTemplateColumns:'120px 1fr',gap:8}}><div><label style={label}>Port</label><input type="number" value={emailConfig.smtp_port??587} onChange={e=>setEmailConfig({...emailConfig,smtp_port:Number(e.target.value)})} style={field}/></div><div><label style={label}>SMTP username</label><input value={emailConfig.smtp_username??''} onChange={e=>setEmailConfig({...emailConfig,smtp_username:e.target.value})} style={field}/></div></div><label style={label}>SMTP password {emailConfig.password_configured&&'(stored)'}</label><input type="password" value={emailPassword} onChange={e=>setEmailPassword(e.target.value)} placeholder={emailConfig.password_configured?'Leave blank to keep current password':''} style={field}/><label style={{display:'flex',gap:7,alignItems:'center',fontSize:10,color:'#cbd5e1',marginBottom:12}}><input type="checkbox" checked={emailConfig.use_tls!==false} onChange={e=>setEmailConfig({...emailConfig,use_tls:e.target.checked})}/>Use TLS</label><button onClick={saveEmail} style={button}><Mail size={14}/>Save Email Settings</button></section>
      <section style={card}><h3 style={title}>Send Test Email</h3><div style={muted}>Verify the SMTP connection immediately rather than waiting for the nightly job.</div><input type="email" placeholder="Test recipient" value={testRecipient} onChange={e=>setTestRecipient(e.target.value)} style={field}/><button disabled={!testRecipient} onClick={()=>void sendTest()} style={button}><Mail size={14}/>Send Test</button><div style={{marginTop:12,fontSize:10,color:emailConfig.configured?'#86efac':'#fca5a5'}}>{emailConfig.configured?'Sender configuration is available.':'Sender configuration is not complete.'}</div></section>
    </div>}
  </div>;
}

const label:React.CSSProperties={fontSize:10,color:'#94a3b8',display:'block',marginBottom:4};
const field:React.CSSProperties={width:'100%',boxSizing:'border-box',background:'#1e293b',color:'#fff',padding:8,marginBottom:10,border:'1px solid #334155',borderRadius:5};
const button:React.CSSProperties={background:'#38bdf8',padding:'8px 12px',border:'none',cursor:'pointer',fontWeight:'bold',display:'inline-flex',alignItems:'center',gap:5,borderRadius:5};
const card:React.CSSProperties={background:'#111827',padding:16,borderRadius:8,border:'1px solid #1f2937'};
const title:React.CSSProperties={fontSize:13,margin:'0 0 10px',display:'flex',alignItems:'center',gap:6};
const row:React.CSSProperties={display:'flex',alignItems:'center',gap:8,padding:'9px 0',borderBottom:'1px solid #1f2937'};
const muted:React.CSSProperties={fontSize:9,color:'#64748b'};
const small:React.CSSProperties={background:'#1e293b',border:'1px solid #334155',color:'#cbd5e1',padding:'6px 8px',borderRadius:4,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:4};
const empty:React.CSSProperties={padding:12,color:'#64748b',fontSize:10};
const tabStyle=(active:boolean):React.CSSProperties=>({background:'none',border:0,color:active?'#38bdf8':'#94a3b8',padding:10,cursor:'pointer',borderBottom:active?'2px solid #38bdf8':'2px solid transparent',display:'inline-flex',alignItems:'center',gap:5});