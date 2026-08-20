import { useState, useEffect } from "react";
import { apiUrl } from "../config/api";
import "./Settings.css";

interface SettingsProps {
  onUpdateGlobal?: (farmName: string, location: string) => void;
}

export default function Settings({ onUpdateGlobal }: SettingsProps) {
  const [farmName, setFarmName] = useState("Shed 1");
  const [location, setLocation] = useState("Lahore, Punjab, Pakistan");
  const [prefix, setPrefix] = useState("TD");
  
  // User Management State
  const [users, setUsers] = useState<{id: string, name: string, role: string}[]>([
    { id: "1", name: "Ammad Hassan", role: "Administrator" },
    { id: "2", name: "Dr. Vet", role: "Veterinarian" },
    { id: "3", name: "Farm Manager", role: "Operator" }
  ]);
  const [newUserName, setNewUserName] = useState("");
  const [newUserRole, setNewUserRole] = useState("Operator");

  const [docsOpen, setDocsOpen] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  // Load existing settings if backend supports it
  useEffect(() => {
    fetch(apiUrl("/settings")).then(r => r.json()).then(p => {
      if (p.farm_name) setFarmName(p.farm_name);
      if (p.location) setLocation(p.location);
      if (p.animal_id_prefix) setPrefix(p.animal_id_prefix);
    }).catch(() => {});
  }, []);

  const handleSaveIdentity = async () => {
    setStatusMsg("Saving identity...");
    try {
      await fetch(apiUrl("/settings"), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ farm_name: farmName, location: location, animal_id_prefix: prefix })
      });
      setStatusMsg("Settings saved successfully.");
      if (onUpdateGlobal) onUpdateGlobal(farmName, location);
    } catch {
      setStatusMsg("Settings saved locally.");
      if (onUpdateGlobal) onUpdateGlobal(farmName, location);
    }
    setTimeout(() => setStatusMsg(""), 3000);
  };

  const handleAddUser = () => {
    if (newUserName.trim() !== "") {
      setUsers([...users, { id: Date.now().toString(), name: newUserName.trim(), role: newUserRole }]);
      setNewUserName("");
    }
  };

  const handleRemoveUser = (idToRemove: string) => {
    setUsers(users.filter(u => u.id !== idToRemove));
  };

  return (
    <div className="settings-page" style={{ padding: '24px' }}>
      
      {/* FARM IDENTITY & LOCATION */}
      <section className="settings-card">
        <h2>Farm Identity & Location</h2>
        <div className="settings-field-row" style={{ marginTop: '16px' }}>
          <label>Farm Name <input value={farmName} onChange={e => setFarmName(e.target.value)} /></label>
          <label>Location <input value={location} onChange={e => setLocation(e.target.value)} /></label>
        </div>
        <div className="settings-field-row" style={{ marginTop: '12px' }}>
          <label>Animal ID Prefix <input value={prefix} maxLength={6} onChange={e => setPrefix(e.target.value.toUpperCase())} /></label>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '16px' }}>
          <button className="settings-primary-button" onClick={handleSaveIdentity}>Save Identity</button>
          {statusMsg && <span style={{ color: '#34d399', fontSize: '12px', fontWeight: 'bold' }}>{statusMsg}</span>}
        </div>
      </section>

      {/* USER MANAGEMENT */}
      <section className="settings-card" style={{ marginTop: '24px' }}>
        <h2>User Management</h2>
        <p className="settings-hint">Add or remove operating users and assign roles.</p>
        
        <div style={{ marginTop: '16px', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '12px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', textAlign: 'left', color: '#64748b' }}>
                <th style={{ paddingBottom: '8px' }}>User Name</th>
                <th style={{ paddingBottom: '8px' }}>Role</th>
                <th style={{ paddingBottom: '8px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '10px 0', color: '#e2e8f0', fontWeight: 'bold' }}>{u.name}</td>
                  <td style={{ padding: '10px 0', color: '#94a3b8' }}>{u.role}</td>
                  <td style={{ padding: '10px 0', textAlign: 'right' }}>
                    <button onClick={() => handleRemoveUser(u.id)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>REMOVE</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '16px', alignItems: 'flex-end' }}>
          <label style={{ flex: 1 }}>New User Name<input value={newUserName} onChange={e => setNewUserName(e.target.value)} placeholder="e.g. John Doe" /></label>
          <label style={{ flex: 1 }}>Role
            <select value={newUserRole} onChange={e => setNewUserRole(e.target.value)} style={{ width: '100%', padding: '8px', background: '#161f30', border: '1px solid #374151', color: '#fff', borderRadius: '4px' }}>
              <option>Administrator</option>
              <option>Veterinarian</option>
              <option>Operator</option>
            </select>
          </label>
          <button className="settings-secondary-button" onClick={handleAddUser} disabled={!newUserName.trim()} style={{ height: '36px' }}>Add User</button>
        </div>
      </section>

      {/* DOCUMENTS ACCORDION */}
      <section className="settings-card" style={{ marginTop: '24px', borderLeft: '4px solid #38bdf8' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setDocsOpen(!docsOpen)}>
          <h2 style={{ margin: 0 }}>Operating Manuals & SOPs</h2>
          <span style={{ color: '#94a3b8', fontSize: '12px' }}>{docsOpen ? 'Hide' : 'Show'} Documents</span>
        </div>
        
        {docsOpen && (
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #1f2937' }}>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '13px', textDecoration: 'underline' }}>1. Technical Operating Manual v2.1 (PDF)</button></li>
              <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '13px', textDecoration: 'underline' }}>2. Farm Staff Daily SOPs (PDF)</button></li>
              <li><button style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', fontSize: '13px', textDecoration: 'underline' }}>3. Emergency Health Intervention Guidelines (PDF)</button></li>
            </ul>
          </div>
        )}
      </section>

      {/* RESET PROTECTION */}
      <section className="settings-card settings-danger-card" style={{ marginTop: '24px' }}>
        <h2>Reset Protection</h2>
        <p className="settings-hint">Ensure test data reset is protected by password before going live.</p>
        <button className="settings-danger-button">Enable Protection</button>
      </section>
    </div>
  );
}
