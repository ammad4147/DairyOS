import React, { useEffect, useMemo, useState } from 'react';
import { Download, Eye, FileSpreadsheet, FileText, Printer } from 'lucide-react';
import { farmToday } from '../utils/farmDate';
import { apiUrl } from '../config/api';
import { readApiPayload } from '../api/response';

type DomainKey = 'ANIMALS' | 'MILK' | 'MILK_QUALITY' | 'FEED' | 'FINANCE' | 'BREEDING' | 'SEMEN' | 'HEALTH' | 'VACCINATION' | 'COML' | 'WHOLE_FARM';
type Format = 'PDF' | 'XLSX' | 'CSV';
type Preview = { dataset_status?: string; authority_status?: string; record_count?: number; columns?: string[]; rows?: Record<string, unknown>[]; summary?: Record<string, unknown>; warnings?: string[] };
type ReportDefinition = { id: string; domain: DomainKey; name: string; authority: string; periods: string[]; filters: string[]; scopeNote: string };

const domains: { key: DomainKey; label: string }[] = [
  { key: 'ANIMALS', label: 'Animals' }, { key: 'MILK', label: 'Milk' }, { key: 'MILK_QUALITY', label: 'Milk Quality' },
  { key: 'FEED', label: 'Feed / TMR' }, { key: 'FINANCE', label: 'Finance' }, { key: 'BREEDING', label: 'Breeding' },
  { key: 'SEMEN', label: 'Semen Inventory' }, { key: 'HEALTH', label: 'Health' }, { key: 'VACCINATION', label: 'Vaccination' },
  { key: 'COML', label: 'COML / COP' }, { key: 'WHOLE_FARM', label: 'Whole Farm' },
];

const reports: ReportDefinition[] = [
  { id: 'animal-register', domain: 'ANIMALS', name: 'Animal Register', authority: 'Animal master records, lifecycle status, disposition history, and governed category mapping.', periods: ['Current herd'], filters: ['Category', 'Status'], scopeNote: 'Supports the current herd across all six canonical DairyOS categories. Historical herd reconstruction is not currently authoritative.' },
  { id: 'animal-population', domain: 'ANIMALS', name: 'Animal Population by Category', authority: 'Animal category authority with active/inactive disposition semantics.', periods: ['Current herd'], filters: ['Status'], scopeNote: 'Counts the current herd as Milking Cows, Dry Cows, Heifers, Female Calves, Male Calves, and Bulls. Historical population reconstruction is not currently authoritative.' },
  { id: 'animal-lifecycle', domain: 'ANIMALS', name: 'Animal Entry / Lifecycle Report', authority: 'Animal registration, acquisition, lifecycle, disposition, and operational event records.', periods: ['Date range', 'Custom period'], filters: ['Category', 'Event type'], scopeNote: 'Shows additions, category transitions, exits, and governed lifecycle events where authority exists.' },
  { id: 'animal-passport', domain: 'ANIMALS', name: 'Individual Animal Passport', authority: 'Lifetime Animal Passport read model and animal-scoped operational histories.', periods: ['As of date', 'Current herd'], filters: ['Animal ID'], scopeNote: 'Generates Passport output from the selected animal authority rather than the modal chrome.' },
  { id: 'daily-milk', domain: 'MILK', name: 'Daily Milk Production', authority: 'Milk production rows, milking session records, corrections, and disposition authority.', periods: ['Today', 'Yesterday', 'Operational Date', 'Date range'], filters: ['Session', 'Category', 'Animal ID', 'Milking cohort'], scopeNote: 'Keeps MORNING, AFTERNOON, EVENING, and all-session views distinct.' },
  { id: 'milk-animal', domain: 'MILK', name: 'Milk Production by Animal', authority: 'Per-animal milk production and milking-frequency history.', periods: ['Date range', 'Month', 'Custom period'], filters: ['Animal ID', 'Milking cohort'], scopeNote: 'Prevents misleading comparison of twice- and thrice-milked animals.' },
  { id: 'milk-disposition', domain: 'MILK', name: 'Milk Disposition / Reconciliation', authority: 'Milk production, sold/domestic/calf/wastage/withdrawal disposition records, and correction history.', periods: ['Date range', 'Month'], filters: ['Disposition type', 'Status'], scopeNote: 'Separates saleable, withdrawal, wastage, and unaccounted milk.' },
  { id: 'milk-quality-log', domain: 'MILK_QUALITY', name: 'Milk Quality Log', authority: 'Milk quality samples with recorded status, operator, timestamps, and revision history.', periods: ['Date range', 'Operational Date', 'Month'], filters: ['Sample type', 'Status'], scopeNote: 'Central replacement for the former popup-dependent Milk Quality print path.' },
  { id: 'quality-summary', domain: 'MILK_QUALITY', name: 'Milk Quality Summary', authority: 'Recorded milk quality samples and governed quality thresholds.', periods: ['Date range', 'Month'], filters: ['Sample type'], scopeNote: 'Summarizes available fat, SNF, and quality classification fields only.' },
  { id: 'current-tmr', domain: 'FEED', name: 'Current TMR', authority: 'Governed TMR stage/category authority and Finance-backed ingredient pricing where available.', periods: ['Current herd', 'Operational Date'], filters: ['Category', 'Ingredient'], scopeNote: 'Distinguishes formulation, ration, cost, consumption, and inventory movement.' },
  { id: 'historical-tmr', domain: 'FEED', name: 'Historical TMR / Feed Cost', authority: 'Daily TMR snapshots, feed records, feed inventory movements, and cost basis.', periods: ['As of date', 'Date range'], filters: ['Category', 'Ingredient'], scopeNote: 'Uses historical TMR/feed authority instead of today’s ration for old dates.' },
  { id: 'finance-ledger', domain: 'FINANCE', name: 'Transaction Ledger', authority: 'Finance ledger, classifier, settlement status, VOID rules, and COP attribution.', periods: ['Date range', 'Month', 'Custom period'], filters: ['Transaction type', 'Status', 'Category', 'Counterparty'], scopeNote: 'VOID rows remain available for audit while excluded from active totals.' },
  { id: 'financial-summary', domain: 'FINANCE', name: 'Income and Expense Summary', authority: 'Governed Finance calculations and transaction classifier.', periods: ['Date range', 'Month', 'Current Year'], filters: ['Category', 'Payment state'], scopeNote: 'Requires Finance permission and must reconcile independently to source rows.' },
  { id: 'breeding-cycle', domain: 'BREEDING', name: 'Reproductive Cycle History', authority: 'Breeding lifecycle records, cycle attribution, PD results, pregnancy loss, and calving events.', periods: ['Date range', 'As of date'], filters: ['Animal ID', 'Technician', 'Event type'], scopeNote: 'Does not merge failed historical cycles into later successful cycles.' },
  { id: 'breeding-performance', domain: 'BREEDING', name: 'Pregnancy and AI Performance', authority: 'Cycle-aware breeding analytics and semen usage links.', periods: ['Date range', 'Custom period'], filters: ['Technician', 'Semen type', 'Semen lot'], scopeNote: 'Pregnancy ratio must use governed successful-cycle attribution.' },
  { id: 'semen-stock', domain: 'SEMEN', name: 'Semen Stock Balance', authority: 'Semen lots, purchases, stock movements, breeding usage, and Finance purchase links.', periods: ['As of date', 'Date range'], filters: ['Semen type', 'Lot', 'Supplier'], scopeNote: 'Purchased, used, and available balances reconcile to stock movements.' },
  { id: 'health-cases', domain: 'HEALTH', name: 'Health Cases and Treatments', authority: 'Health cases, observations, treatments, withdrawal references, and animal IDs.', periods: ['Date range', 'As of date'], filters: ['Animal ID', 'Case status', 'Severity'], scopeNote: 'Animal-specific reports include only records attributed to the selected animal.' },
  { id: 'withdrawal', domain: 'HEALTH', name: 'Withdrawal Periods', authority: 'Treatment records, withdrawal calculation source, and active health state.', periods: ['Operational Date', 'Date range'], filters: ['Animal ID', 'Status'], scopeNote: 'Separates active withdrawal from resolved clinical history.' },
  { id: 'vaccination-schedule', domain: 'VACCINATION', name: 'Vaccination Schedule and Due Status', authority: 'Vaccination records, administered state, schedule rows, due and overdue dates.', periods: ['Operational Date', 'Date range', 'Custom period'], filters: ['Animal ID', 'Vaccine', 'Schedule status'], scopeNote: 'Future schedules stay in Reporting and do not alter today’s Dashboard attention rules.' },
  { id: 'coml-period', domain: 'COML', name: 'Period COML / COP', authority: 'Locked COML records, historical TMR snapshots, milk denominator, and Finance OPEX attribution.', periods: ['Month', 'Custom period'], filters: ['Lock status', 'Cost component'], scopeNote: 'Missing authority stays incomplete rather than being treated as zero.' },
  { id: 'whole-farm-snapshot', domain: 'WHOLE_FARM', name: 'Complete Farm Snapshot', authority: 'Cross-domain authoritative projections as of the selected operational date.', periods: ['Snapshot Date'], filters: ['Major sections'], scopeNote: 'Central report: herd, milk, quality, feed, finance, breeding, semen, health, vaccination, COML/COP, and operational attention.' },
];

const canonicalCategories = ['All animals', 'Milking', 'Dry', 'Heifer', 'Female Calf', 'Male Calf', 'Bull'];
const sessions = ['All sessions', 'MORNING', 'AFTERNOON', 'EVENING'];
const cohorts = ['All eligible animals', '2x milking cohort', '3x milking cohort', 'Individual animal'];
const formats: Format[] = ['PDF', 'XLSX', 'CSV'];
const field: React.CSSProperties = { width: '100%', boxSizing: 'border-box', background: '#1e293b', color: '#fff', padding: 8, border: '1px solid #334155', borderRadius: 5, fontSize: 10 };
const label: React.CSSProperties = { fontSize: 9, color: '#94a3b8', display: 'block', marginBottom: 4, fontWeight: 800, textTransform: 'uppercase' };
const card: React.CSSProperties = { background: '#111827', border: '1px solid #1f2937', borderRadius: 8, padding: 12, minWidth: 0 };
const button = (bg = '#0284c7'): React.CSSProperties => ({ background: bg, color: '#fff', border: 0, borderRadius: 5, padding: '8px 10px', fontSize: 10, fontWeight: 800, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 });
const htmlEscape = (value: unknown) => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] || char));

export default function ReportingTab() {
  const today = useMemo(() => farmToday(), []);
  const [domain, setDomain] = useState<DomainKey>('WHOLE_FARM');
  const availableReports = reports.filter(report => report.domain === domain);
  const [reportId, setReportId] = useState('whole-farm-snapshot');
  const report = availableReports.find(item => item.id === reportId) ?? availableReports[0];
  const [startDate, setStartDate] = useState(today); const [endDate, setEndDate] = useState(today); const [asOfDate, setAsOfDate] = useState(today);
  const [category, setCategory] = useState('All animals'); const [session, setSession] = useState('All sessions'); const [cohort, setCohort] = useState('All eligible animals'); const [animalId, setAnimalId] = useState('');
  const [format, setFormat] = useState<Format>('PDF'); const [previewed, setPreviewed] = useState(false); const [preview, setPreview] = useState<Preview | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const snapshot = domain === 'WHOLE_FARM';

  useEffect(() => { setPreview(null); setPreviewed(false); setError(''); }, [reportId, startDate, endDate, asOfDate, category, session, cohort, animalId]);
  const selectDomain = (next: DomainKey) => { setDomain(next); setReportId(reports.find(item => item.domain === next)?.id ?? ''); setPreviewed(false); };
  const filename = `DairyOS-${report.name.replace(/[^A-Za-z0-9]+/g, '-')}-${asOfDate}.${format.toLowerCase()}`;
  const requestBody = () => ({
    report_id: report.id, domain,
    period_mode: snapshot ? 'SNAPSHOT_DATE' : report.periods[0] === 'Current herd' ? 'CURRENT_HERD' : report.periods[0] === 'Today' ? 'TODAY' : report.periods[0] === 'Yesterday' ? 'YESTERDAY' : report.periods[0] === 'Operational Date' ? 'OPERATIONAL_DATE' : report.periods[0] === 'As of date' ? 'AS_OF_DATE' : report.periods[0] === 'Month' ? 'MONTH' : report.periods[0] === 'Current Year' ? 'CURRENT_YEAR' : 'DATE_RANGE',
    operational_date: asOfDate, as_of_date: asOfDate, snapshot_date: asOfDate, start_date: startDate, end_date: endDate,
    filters: { ...(category !== 'All animals' ? { category } : {}), ...(session !== 'All sessions' ? { session } : {}), ...(cohort !== 'All eligible animals' ? { milking_cohort: cohort } : {}), ...(animalId ? { animal_id: animalId } : {}) },
  });
  const loadDataset = async (): Promise<Preview> => {
    const response = await fetch(apiUrl('/farm/reporting/preview'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestBody()) });
    return readApiPayload(response, 'Report data could not be loaded');
  };
  const requestPreview = async () => { setLoading(true); setError(''); try { const data = await loadDataset(); setPreview(data); setPreviewed(true); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Report preview could not be loaded.'); setPreview(null); setPreviewed(false); } finally { setLoading(false); } };

  const printableHtml = (data: Preview) => {
    const columns = data.columns || (data.rows?.[0] ? Object.keys(data.rows[0]) : []); const rows = data.rows || [];
    const filters = [`As of: ${asOfDate}`, ...(snapshot ? [`Snapshot: ${asOfDate}`] : [`Period: ${startDate} to ${endDate}`]), ...(category !== 'All animals' ? [`Category: ${category}`] : []), ...(session !== 'All sessions' ? [`Session: ${session}`] : []), ...(cohort !== 'All eligible animals' ? [`Milking cohort: ${cohort}`] : []), ...(animalId ? [`Animal ID: ${animalId}`] : [])];
    const summary = Object.entries(data.summary || {}).map(([key, value]) => `<div><b>${htmlEscape(key)}</b>: ${htmlEscape(typeof value === 'object' ? JSON.stringify(value) : value)}</div>`).join('');
    const table = rows.length ? `<table><thead><tr>${columns.map(column => `<th>${htmlEscape(column)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${columns.map(column => `<td>${htmlEscape(row[column])}</td>`).join('')}</tr>`).join('')}</tbody></table>` : '<p>No records match the selected report controls.</p>';
    return `<!doctype html><html><head><meta charset="utf-8"><title>${htmlEscape(report.name)}</title><style>@page{margin:12mm}body{font:11px Arial,sans-serif;color:#111;margin:0}h1{font-size:18px;margin:0 0 5px}.meta{margin:2px 0;color:#444}.summary{margin:10px 0;padding:8px;border:1px solid #bbb}table{width:100%;border-collapse:collapse;margin-top:10px;table-layout:auto}th,td{border:1px solid #bbb;padding:5px;text-align:left;vertical-align:top;word-break:break-word}th{background:#eee}thead{display:table-header-group}.authority{font-size:9px;color:#555;margin-top:8px}</style></head><body><h1>DairyOS — ${htmlEscape(report.name)}</h1><div class="meta">${htmlEscape(domains.find(item => item.key === domain)?.label || domain)} · ${htmlEscape(filters.join(' · '))}</div><div class="meta">Dataset: ${htmlEscape(data.dataset_status || 'UNKNOWN')} · Records: ${htmlEscape(data.record_count ?? rows.length)}</div>${summary ? `<div class="summary">${summary}</div>` : ''}${table}<div class="authority">Authority: ${htmlEscape(report.authority)}</div></body></html>`;
  };

  const printReport = async () => {
    setLoading(true); setError('');
    try {
      const data = await loadDataset(); setPreview(data); setPreviewed(true);
      const frame = document.createElement('iframe'); frame.setAttribute('title', 'DairyOS report print'); frame.style.position = 'fixed'; frame.style.right = '0'; frame.style.bottom = '0'; frame.style.width = '0'; frame.style.height = '0'; frame.style.border = '0';
      document.body.appendChild(frame); const printWindow = frame.contentWindow; const printDocument = frame.contentDocument;
      if (!printWindow || !printDocument) throw new Error('Unable to prepare the report print document.');
      printDocument.open(); printDocument.write(printableHtml(data)); printDocument.close();
      window.setTimeout(() => { try { printWindow.focus(); printWindow.print(); } finally { window.setTimeout(() => frame.remove(), 500); } }, 50);
    } catch (printError) { setError(printError instanceof Error ? printError.message : 'Report could not be printed.'); } finally { setLoading(false); }
  };

  const saveReport = async () => {
    setLoading(true); setError('');
    try {
      const data = await loadDataset(); setPreview(data); setPreviewed(true);
      const response = await fetch(apiUrl(`/farm/reporting/export?format=${encodeURIComponent(format)}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestBody()) });
      if (!response.ok) { const detail = await response.text(); throw new Error(detail || 'Report export could not be generated.'); }
      const exportedCount = response.headers.get('X-DairyOS-Record-Count');
      const exportedReport = response.headers.get('X-DairyOS-Report-Id');
      const exportedStatus = response.headers.get('X-DairyOS-Dataset-Status');
      if (exportedReport !== report.id || exportedCount !== String(data.record_count ?? data.rows?.length ?? 0) || exportedStatus !== data.dataset_status) throw new Error('Report export reconciliation failed. Refresh and retry.');
      const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url);
    } catch (saveError) { setError(saveError instanceof Error ? saveError.message : 'Report could not be saved.'); } finally { setLoading(false); }
  };

  const showAnimal = ['ANIMALS', 'MILK', 'BREEDING', 'HEALTH', 'VACCINATION'].includes(domain); const showCategory = ['ANIMALS', 'MILK', 'FEED'].includes(domain); const showSession = domain === 'MILK'; const showCohort = domain === 'MILK';
  return <div style={{ display: 'grid', gap: 12 }}>
    <section style={card}><div style={{ display: 'grid', gridTemplateColumns: '190px 1fr 1fr 130px', gap: 9, alignItems: 'end' }}>
      <div><label style={label}>Domain</label><select value={domain} onChange={event => selectDomain(event.target.value as DomainKey)} style={field}>{domains.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}</select></div>
      <div><label style={label}>Report</label><select value={report.id} onChange={event => { setReportId(event.target.value); setPreviewed(false); }} style={field}>{availableReports.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div>
      <div><label style={label}>{snapshot ? 'Snapshot Date' : 'As Of / Operational Date'}</label><input type="date" value={asOfDate} onChange={event => setAsOfDate(event.target.value)} style={field} /></div>
      <div><label style={label}>Format</label><select value={format} onChange={event => setFormat(event.target.value as Format)} style={field}>{formats.map(item => <option key={item}>{item}</option>)}</select></div>
    </div></section>
    <section style={card}><div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,minmax(0,1fr))', gap: 9, alignItems: 'end' }}>
      {!snapshot && <div><label style={label}>Start Date</label><input type="date" value={startDate} onChange={event => setStartDate(event.target.value)} style={field} /></div>}{!snapshot && <div><label style={label}>End Date</label><input type="date" value={endDate} onChange={event => setEndDate(event.target.value)} style={field} /></div>}
      {showCategory && <div><label style={label}>Category</label><select value={category} onChange={event => setCategory(event.target.value)} style={field}>{canonicalCategories.map(item => <option key={item}>{item}</option>)}</select></div>}{showSession && <div><label style={label}>Session</label><select value={session} onChange={event => setSession(event.target.value)} style={field}>{sessions.map(item => <option key={item}>{item}</option>)}</select></div>}{showCohort && <div><label style={label}>Milking Cohort</label><select value={cohort} onChange={event => setCohort(event.target.value)} style={field}>{cohorts.map(item => <option key={item}>{item}</option>)}</select></div>}{showAnimal && <div><label style={label}>Animal ID</label><input value={animalId} onChange={event => setAnimalId(event.target.value)} placeholder="All applicable" style={field} /></div>}
      <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}><button type="button" onClick={requestPreview} disabled={loading} style={button('#0369a1')}><Eye size={13} />{loading ? 'Loading...' : 'Preview Report'}</button><button type="button" onClick={printReport} disabled={loading} style={button('#475569')}><Printer size={13} />Print</button><button type="button" onClick={saveReport} disabled={loading} style={button('#059669')}>{format === 'XLSX' ? <FileSpreadsheet size={13} /> : format === 'CSV' ? <Download size={13} /> : <FileText size={13} />}Save {format}</button></div>
    </div></section>
    <section id="dairyos-report-preview" style={{ ...card, background: '#0b1220' }}><div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'start', flexWrap: 'wrap' }}><div><div style={{ color: '#38bdf8', fontWeight: 900, fontSize: 15 }}>{report.name}</div><div style={{ color: '#94a3b8', fontSize: 10, marginTop: 3 }}>{domains.find(item => item.key === domain)?.label} · {snapshot ? `Snapshot date ${asOfDate}` : `${startDate} to ${endDate}`}</div></div><div style={{ color: error ? '#fca5a5' : previewed ? '#86efac' : '#fde68a', fontSize: 10, fontWeight: 900 }}>{error || (previewed ? `${preview?.dataset_status || 'PREVIEW READY'} · ${preview?.record_count ?? 0} records` : 'SELECT PREVIEW')}</div></div>
      <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1.2fr .8fr', gap: 10 }}><div style={{ borderTop: '1px solid #1f2937', paddingTop: 9 }}><div style={{ ...label, marginBottom: 6 }}>Authority</div><div style={{ color: '#e2e8f0', fontSize: 11, lineHeight: 1.45 }}>{report.authority}</div><div style={{ ...label, margin: '12px 0 6px' }}>Scope</div><div style={{ color: '#cbd5e1', fontSize: 11, lineHeight: 1.45 }}>{report.scopeNote}</div></div><div style={{ borderTop: '1px solid #1f2937', paddingTop: 9 }}><div style={label}>Applicable Controls</div><div style={{ color: '#cbd5e1', fontSize: 10, marginTop: 6 }}>Periods: {report.periods.join(', ')}</div><div style={{ color: '#cbd5e1', fontSize: 10, marginTop: 5 }}>Filters: {report.filters.join(', ')}</div><div style={{ color: '#64748b', fontSize: 9, marginTop: 8 }}>Report generation is read-only. Operational record dates and workflow-specific selectors remain in their original tabs.</div></div></div>
      {preview?.warnings?.map(warning => <div key={warning} style={{ marginTop: 10, color: '#fcd34d', fontSize: 10 }}>{warning}</div>)}{preview?.rows && preview.rows.length > 0 && <div style={{ marginTop: 12, overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}><thead><tr>{(preview.columns || Object.keys(preview.rows[0])).map(column => <th key={column} style={{ textAlign: 'left', padding: 7, color: '#94a3b8', borderTop: '1px solid #1f2937' }}>{column}</th>)}</tr></thead><tbody>{preview.rows.slice(0, 100).map((row, index) => <tr key={index}>{(preview.columns || Object.keys(row)).map(column => <td key={column} style={{ padding: 7, color: '#e2e8f0', borderTop: '1px solid #1f2937' }}>{String(row[column] ?? '')}</td>)}</tr>)}</tbody></table></div>}
    </section>
    <section style={card}><div style={{ fontSize: 12, fontWeight: 900, color: '#cbd5e1', marginBottom: 8 }}>Report Catalog and Authority Matrix</div><div style={{ overflowX: 'auto' }}><table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 860, fontSize: 10 }}><thead><tr style={{ color: '#94a3b8', textAlign: 'left' }}><th>Domain</th><th>Reports</th><th>Authority</th><th>Filters</th><th>Periods</th><th>Output</th></tr></thead><tbody>{domains.map(item => { const rows = reports.filter(reportItem => reportItem.domain === item.key); return <tr key={item.key} style={{ borderTop: '1px solid #1f2937', verticalAlign: 'top' }}><td style={{ padding: 8, fontWeight: 900, color: '#e2e8f0' }}>{item.label}</td><td style={{ padding: 8 }}>{rows.map(row => row.name).join(', ')}</td><td style={{ padding: 8, color: '#94a3b8' }}>{rows[0]?.authority}</td><td style={{ padding: 8 }}>{Array.from(new Set(rows.flatMap(row => row.filters))).join(', ')}</td><td style={{ padding: 8 }}>{Array.from(new Set(rows.flatMap(row => row.periods))).join(', ')}</td><td style={{ padding: 8 }}>PDF, XLSX, CSV, Print</td></tr>; })}</tbody></table></div></section>
  </div>;
}
