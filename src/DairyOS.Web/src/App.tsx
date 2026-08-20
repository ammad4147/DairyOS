import { useEffect, useMemo, useState } from "react";
import UnifiedDashboard from "./components/UnifiedDashboard";
import AnimalRegistry from "./components/AnimalRegistry";
import UnifiedOperationalTab from "./components/UnifiedOperationalTab";
import Settings from "./components/Settings";
import CMPLTab from "./components/CMPL";
import AnalyticsTab from "./components/Analytics";
import { Bell, Settings as SettingsIcon, User } from "lucide-react";
import type { OperationalEntryConfig } from "./components/OperationalEntryPanel";
import "./App.css";
import { apiUrl } from "./config/api";

type ViewId = "command" | "animals" | "milk" | "feed" | "health" | "breeding" | "workforce" | "inventory" | "equipment" | "finance" | "analytics" | "cmpl" | "alerts" | "settings";
type OperationalTabId = Exclude<ViewId, "command" | "settings" | "cmpl" | "analytics">;
type NavigationItem = { id: ViewId; label: string; description: string; endpoint?: string; selector?: string; mode?: "cards" | "entries" | "decisions" | "state"; entry?: OperationalEntryConfig };

const operatorField = { name: "operator", label: "Operator", type: "text" as const, required: true };
const animalField = { name: "animal_id", label: "Animal", type: "animal" as const, required: true };
const entryConfigs: Record<string, OperationalEntryConfig> = {
  milk: { endpoint: "/farm/milk", title: "Record Milk", description: "Enter yield", fields: [animalField, operatorField] },
  feed: { endpoint: "/farm/feed", title: "Record Feed", description: "Record consumption", fields: [{ name: "feed_type", label: "Feed Type", type: "text", required: true }, { name: "quantity_kg", label: "Quantity (kg)", type: "number", required: true }, operatorField] },
  health: { endpoint: "/farm/health-observations", title: "Record Health", description: "Health observation", fields: [animalField, { name: "observation", label: "Observation", type: "textarea", required: true }, { name: "severity", label: "Severity", type: "select", required: true, options: ["NORMAL", "ELEVATED", "HIGH", "CRITICAL"] }, operatorField] },
  breeding: { endpoint: "/farm/breeding", title: "Record Reproduction", description: "Reproduction event", fields: [animalField, { name: "event_type", label: "Event", type: "select", required: true, options: ["heat_detected", "insemination", "pregnancy_diagnosis", "calving"] }, operatorField] },
  workforce: { endpoint: "/farm/workforce", title: "Record Workforce", description: "Workforce activity", fields: [{ name: "worker_id", label: "Worker ID", type: "text", required: true }, { name: "activity", label: "Activity", type: "text", required: true }, operatorField] },
  inventory: { endpoint: "/farm/inventory", title: "Record Inventory", description: "Stock movement", fields: [{ name: "item", label: "Item", type: "text", required: true }, { name: "quantity", label: "Quantity", type: "number", required: true }, { name: "movement_type", label: "Movement", type: "select", required: true, options: ["RECEIPT", "CONSUMPTION"] }, operatorField] },
  equipment: { endpoint: "/farm/equipment", title: "Record Equipment", description: "Equipment activity", fields: [{ name: "equipment_id", label: "Equipment ID", type: "text", required: true }, { name: "activity", label: "Activity", type: "text", required: true }, operatorField] },
  finance: { endpoint: "/farm/financial", title: "Record Finance", description: "Financial tx", fields: [{ name: "transaction_type", label: "Type", type: "select", required: true, options: ["INCOME", "EXPENSE"] }, { name: "amount", label: "Amount", type: "number", required: true }, operatorField] },
};

const navigation: NavigationItem[] = [
  { id: "command", label: "Dashboard", description: "Live farm operational picture" },
  { id: "animals", label: "Animals", description: "Herd and animal records", endpoint: "/farm/animals", mode: "cards" },
  { id: "milk", label: "Milk", description: "Milk recording", endpoint: "/farm/milk", mode: "entries", entry: entryConfigs.milk },
  { id: "feed", label: "Feeding", description: "Feeding activity", endpoint: "/farm/feed", mode: "entries", entry: entryConfigs.feed },
  { id: "health", label: "Health", description: "Health observations", endpoint: "/farm/health-observations", mode: "entries", entry: entryConfigs.health },
  { id: "breeding", label: "Breeding", description: "Reproduction events", endpoint: "/farm/breeding", mode: "entries", entry: entryConfigs.breeding },
  { id: "workforce", label: "Workforce", description: "Workforce activity", endpoint: "/farm/workforce", mode: "entries", entry: entryConfigs.workforce },
  { id: "inventory", label: "Inventory", description: "Stock movements", endpoint: "/farm/inventory", mode: "entries", entry: entryConfigs.inventory },
  { id: "equipment", label: "Equipment", description: "Equipment maintenance", endpoint: "/farm/equipment", mode: "entries", entry: entryConfigs.equipment },
  { id: "finance", label: "Finance", description: "Financial transactions", endpoint: "/farm/financial", mode: "entries", entry: entryConfigs.finance },
  { id: "cmpl", label: "CMPL", description: "Cost of Milk Production Scenarios" },
  { id: "analytics", label: "Analytics", description: "Dairy KPI indicators based on actual data" },
  { id: "alerts", label: "Alerts & Decisions", description: "Actionable items", endpoint: "/dashboard", selector: "operational_decisions", mode: "decisions" },
  { id: "settings", label: "Settings", description: "Farm identity, documents, and controls" }
];

function TopBarClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  return (
    <div className="topbar-center">
      <div className="date-main">{time.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</div>
      <div className="time-sub">{time.toLocaleTimeString()}</div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<ViewId>("command");
  const [farmName, setFarmName] = useState("Shed 1");
  const [location, setLocation] = useState("Lahore, Punjab, Pakistan");

  const loadSettings = () => {
    fetch(apiUrl("/settings")).then(r => r.json()).then(p => {
      if (p.farm_name) setFarmName(p.farm_name);
      if (p.location) setLocation(p.location);
    }).catch(() => {});
  };

  useEffect(() => { loadSettings(); }, []);

  const activeNav = useMemo(() => navigation.find(n => n.id === view) ?? navigation[0], [view]);
  const selectView = (nextView: ViewId) => { setView(nextView); };

  // This function allows the Settings component to update the Top Bar instantly
  const handleGlobalUpdate = (newName: string, newLocation: string) => {
    if (newName) setFarmName(newName);
    if (newLocation) setLocation(newLocation);
  };

  return (
    <div className="dairyos-shell">
      <header className="dairyos-topbar">
        <div className="topbar-left">
          <span className="brand-mark">D</span>
          <div className="brand-text">
            <span className="brand-title">DairyOS</span>
            <span className="brand-location">{farmName} ({location})</span>
          </div>
        </div>
        
        <TopBarClock />
        
        <div className="topbar-right">
          <button className="icon-btn" onClick={() => selectView('alerts')} title="Alerts"><Bell size={18} /></button>
          <button className="icon-btn" onClick={() => selectView('settings')} title="Settings"><SettingsIcon size={18} /></button>
          <button className="user-avatar" style={{ border: 'none', cursor: 'pointer', outline: 'none' }} onClick={() => selectView('settings')} title="User Management">
            <User size={14} color="#94a3b8" />
          </button>
        </div>
      </header>
      
      <div className="dairyos-body">
        <aside className="dairyos-sidebar">
          <div className="sidebar-heading">OPERATIONS</div>
          <nav>
            {navigation.map(item => (
              <button key={item.id} className={`nav-item ${view === item.id ? "active" : ""}`} onClick={() => selectView(item.id)}>
                {item.label}
                {item.id === "alerts" && <span className="nav-badge">!</span>}
              </button>
            ))}
          </nav>
        </aside>
        
        <main className="dairyos-main">
          {view === "command" && <UnifiedDashboard onNavigate={selectView as any} />}
          {view === "animals" && <AnimalRegistry onNavigate={selectView as any} />}
          
          {view === "settings" && (
            <>
              <div className="page-heading">
                <h1>Settings & Users</h1>
                <p>Farm identity, user management, and operational controls</p>
              </div>
              <Settings onUpdateGlobal={handleGlobalUpdate} />
            </>
          )}
          
          {view === "cmpl" && <><div className="page-heading"><h1>CMPL</h1><p>Cost of Milk Production per Liter</p></div><CMPLTab /></>}
          {view === "analytics" && <><div className="page-heading"><h1>Analytics</h1><p>Standard Dairy KPIs</p></div><AnalyticsTab /></>}
          
          {!['command', 'animals', 'settings', 'cmpl', 'analytics'].includes(view) && (
            <>
              <div className="page-heading">
                <h1>{activeNav.label}</h1>
                <p>{activeNav.description}</p>
              </div>
              <UnifiedOperationalTab title={activeNav.label} tabId={activeNav.id as OperationalTabId} endpoint={activeNav.endpoint} selector={activeNav.selector} mode={activeNav.mode ?? "state"} entry={activeNav.entry} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
