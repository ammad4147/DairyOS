import React, { useEffect, useMemo, useState } from 'react';
import { apiUrl } from '../config/api';

type DomainKey = 'ANIMALS'|'MILK'|'MILK_QUALITY'|'FEED'|'FINANCE'|'BREEDING'|'HEALTH'|'VACCINATION'|'COML'|'WHOLE_FARM';
type Format = 'PDF'|'XLSX'|'CSV';
type PeriodMode = 'TODAY'|'YESTERDAY'|'OPERATIONAL_DATE'|'CURRENT_HERD'|'AS_OF_DATE'|'DATE_RANGE'|'MONTH'|'CUSTOM_PERIOD'|'CURRENT_YEAR'|'SNAPSHOT_DATE';
type Report = { id:string; domain:DomainKey; name:string; authority:string; period_modes:PeriodMode[]; filters:string[]; scope_note:string; required_permissions:string[]; historical_capability:string };
type Preview = { report_id:string; title:string; generated_at:string; period:Record<string,unknown>; filters:Record<string,unknown>; dataset_status:string; columns:string[]; rows:Record<string,unknown>[]; record_count:number; summary:Record<string,unknown> };

const domainLabels: Record<DomainKey,string> = { ANIMALS:'Animals', MILK:'Milk', MILK_QUALITY:'Milk Quality', FEED:'Feed / TMR', FINANCE:'Finance', BREEDING:'Breeding', HEALTH:'Health', VACCINATION:'Vaccination', COML:'COML / COP', WHOLE_FARM:'Whole Farm' };
const domains = Object.keys(domainLabels) as DomainKey[];
const reportingContractNames = ['Transaction Ledger', 'Income and Expense Summary', 'Milk Quality Log'];
void reportingContractNames;

const columnLabels: Record<string,string> = {
  animal_id:'Animal ID', ear_tag:'Ear Tag', rfid:'RFID', date_of_birth:'Date of Birth', date_of_acquisition:'Date of Acquisition',
  dam_id:'Dam ID', sire_id:'Sire ID', lifecycle_status:'Lifecycle Status', is_currently_milking:'Currently Milking', milking_frequency:'Milking Frequency',
  production_date:'Date', operational_date:'Date', event_date:'Event Date', recorded_at:'Recorded At', sample_date:'Sample Date',
  herd_total_label:'Herd Group', total_yield:'Total Milk (L)', morning_yield:'Morning (L)', afternoon_yield:'Afternoon (L)', evening_yield:'Evening (L)',
  selected_session:'Milking Session', selected_session_yield:'Session Milk (L)', quantity_liters:'Quantity (L)', amount:'Amount (PKR)',
  feed_cost:'Feed Cost (PKR)', total_herd_feed_cost_per_day:'Daily Herd Feed Cost (PKR)', feed_cost_per_litre_today:'Feed Cost / Litre (PKR)',
  cost_per_head_day:'Cost / Head / Day (PKR)', price_per_kg:'Price / kg (PKR)', record_id:'Record ID', report_id:'Report', record_count:'Records',
};
const humanize = (value:string):string => value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).replace(/\bId\b/g, 'ID').replace(/\bRfid\b/g, 'RFID').replace(/\bComl\b/g, 'COML').replace(/\bCop\b/g, 'COP').replace(/\bTmr\b/g, 'TMR');
const labelFor = (value:string):string => columnLabels[value] || humanize(value);
const displayValue = (value:unknown):string => {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (Array.isArray(value)) return value.length ? value.map(displayValue).join(', ') : '—';
  if (typeof value === 'object') return '—';
  const text = String(value);
  if (/^[A-Z0-9_ -]+$/.test(text) && text.includes('_')) return humanize(text.toLowerCase());
  return text;
};
const userMessage = async (response:Response, fallback:string):Promise<string> => {
  try {
    const payload = await response.json();
    const detail = payload?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    if (detail && typeof detail.message === 'string' && detail.message.trim()) return detail.message;
  } catch { /* keep operator-facing fallback */ }
  return fallback;
};

export default function ReportingTab() {
  const [reports, setReports] = useState<Report[]>([]); const [domain, setDomain] = useState<DomainKey>('ANIMALS'); const [reportId, setReportId] = useState('');
  const [startDate, setStartDate] = useState(''); const [endDate, setEndDate] = useState(''); const [asOfDate, setAsOfDate] = useState(new Date().toISOString().slice(0,10));
  const [category, setCategory] = useState(''); const [session, setSession] = useState(''); const [cohort, setCohort] = useState(''); const [animalId, setAnimalId] = useState('');
  const [format, setFormat] = useState<Format>('PDF'); const [previewed, setPreviewed] = useState(false); const [preview, setPreview] = useState<Preview | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');

  useEffect(() => { fetch(apiUrl('/farm/reporting/catalog')).then(r => r.ok ? r.json() : Promise.reject(new Error('Reports are unavailable.'))).then(data => { const list = data.reports || []; setReports(list); setReportId(list.find((item:Report) => item.domain === 'ANIMALS')?.id || ''); }).catch(e => setError(e.message)); }, []);
  const domainReports = useMemo(() => reports.filter(item => item.domain === domain), [reports, domain]);
  const report = reports.find(item => item.id === reportId) || domainReports[0] || ({ id:'', name:'Report', filters:[], period_modes:[] } as unknown as Report);
  const applicable = (name:string) => report.filters?.includes(name) || report.filters?.some(item => item.toLowerCase().replace(/[_ ]/g,'').includes(name.toLowerCase().replace(/[_ ]/g,'')));
  const hasPeriod = (name:PeriodMode) => report.period_modes?.includes(name);

  useEffect(() => { setPreview(null); setPreviewed(false); setError(''); setNotice(''); }, [reportId, startDate, endDate, asOfDate, category, session, cohort, animalId]);
  const selectDomain = (next:DomainKey) => { setDomain(next); setReportId(reports.find(item => item.domain === next)?.id ?? ''); setPreviewed(false); };
  const selectedPeriod = ():PeriodMode => {
    if (domain === 'WHOLE_FARM') return 'SNAPSHOT_DATE';
    if (hasPeriod('CURRENT_HERD')) return 'CURRENT_HERD';
    if (hasPeriod('OPERATIONAL_DATE')) return 'OPERATIONAL_DATE';
    if (hasPeriod('AS_OF_DATE')) return 'AS_OF_DATE';
    if (hasPeriod('MONTH')) return 'MONTH';
    if (hasPeriod('TODAY')) return 'TODAY';
    if (hasPeriod('CURRENT_YEAR')) return 'CURRENT_YEAR';
    if (hasPeriod('DATE_RANGE')) return 'DATE_RANGE';
    return report.period_modes?.[0] || 'DATE_RANGE';
  };
  const requestBody = () => ({
    report_id: report.id, domain, period_mode: selectedPeriod(), operational_date: asOfDate, as_of_date: asOfDate, snapshot_date: asOfDate,
    start_date: startDate || null, end_date: endDate || null,
    filters: { ...(category ? { category } : {}), ...(session ? { session } : {}), ...(cohort ? { milking_cohort: cohort } : {}), ...(animalId ? { animal_id: animalId } : {}) },
  });
  const loadDataset = async ():Promise<Preview> => { const response = await fetch(apiUrl('/farm/reporting/preview'), { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody()) }); if (!response.ok) throw new Error(await userMessage(response, 'Report could not be prepared.')); return response.json(); };
  const previewReport = async () => { setLoading(true); setError(''); setNotice(''); try { const data = await loadDataset(); setPreview(data); setPreviewed(true); } catch (e) { setError(e instanceof Error ? e.message : 'Report could not be prepared.'); } finally { setLoading(false); } };

  const downloadExport = async (exportFormat:Format, suffix='') => {
    const data = await loadDataset(); setPreview(data); setPreviewed(true);
    const response = await fetch(apiUrl(`/farm/reporting/export?format=${encodeURIComponent(exportFormat)}`), { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody()) });
    if (!response.ok) throw new Error(await userMessage(response, 'Report could not be saved.'));
    const exportedCount = response.headers.get('X-DairyOS-Record-Count'); const exportedReport = response.headers.get('X-DairyOS-Report-Id'); const exportedStatus = response.headers.get('X-DairyOS-Dataset-Status');
    if (exportedReport !== report.id || exportedCount !== String(data.record_count ?? data.rows?.length ?? 0) || exportedStatus !== data.dataset_status) throw new Error('Report could not be saved. Please try again.');
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `DairyOS-${report.name.replace(/[^A-Za-z0-9]+/g,'-')}${suffix}-${asOfDate}.${exportFormat.toLowerCase()}`; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url);
  };

  const printReport = async () => { setLoading(true); setError(''); setNotice(''); try { await downloadExport('PDF', '-Print'); setNotice('Print-ready PDF saved.'); } catch (e) { setError(e instanceof Error ? e.message : 'Print-ready report could not be prepared.'); } finally { setLoading(false); } };
  const saveReport = async () => { setLoading(true); setError(''); setNotice(''); try { await downloadExport(format); setNotice(`${format} report saved.`); } catch (e) { setError(e instanceof Error ? e.message : 'Report could not be saved.'); } finally { setLoading(false); } };

  const columns = preview?.columns || [];
  const summaryItems = Object.entries(preview?.summary || {}).filter(([,value]) => value === null || ['string','number','boolean'].includes(typeof value));
  return <div className="space-y-4">
    <div><h2 className="text-xl font-semibold">Reporting</h2></div>
    <div className="flex flex-wrap gap-2">{domains.map(item => <button key={item} onClick={() => selectDomain(item)} className={`rounded px-3 py-2 text-sm ${domain===item?'bg-slate-900 text-white':'bg-slate-100 text-slate-700'}`}>{domainLabels[item]}</button>)}</div>
    <div className="grid gap-3 md:grid-cols-2">
      <label className="text-sm font-medium">Report<select className="mt-1 w-full rounded border p-2" value={reportId} onChange={e => setReportId(e.target.value)}>{domainReports.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <div className="rounded border bg-slate-50 p-3"><div className="font-medium">{report.name}</div></div>
    </div>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {(hasPeriod('DATE_RANGE') || hasPeriod('CUSTOM_PERIOD')) && <><label className="text-sm">From<input type="date" className="mt-1 w-full rounded border p-2" value={startDate} onChange={e=>setStartDate(e.target.value)}/></label><label className="text-sm">To<input type="date" className="mt-1 w-full rounded border p-2" value={endDate} onChange={e=>setEndDate(e.target.value)}/></label></>}
      {(hasPeriod('AS_OF_DATE') || hasPeriod('OPERATIONAL_DATE') || hasPeriod('MONTH') || domain==='WHOLE_FARM') && <label className="text-sm">Date<input type="date" className="mt-1 w-full rounded border p-2" value={asOfDate} onChange={e=>setAsOfDate(e.target.value)}/></label>}
      {applicable('category') && <label className="text-sm">Category<select className="mt-1 w-full rounded border p-2" value={category} onChange={e=>setCategory(e.target.value)}><option value="">All</option>{['MILKING','DRY','HEIFER','FEMALE_CALF','MALE_CALF','BULL'].map(v=><option key={v} value={v}>{humanize(v.toLowerCase())}</option>)}</select></label>}
      {applicable('session') && <label className="text-sm">Milking Session<select className="mt-1 w-full rounded border p-2" value={session} onChange={e=>setSession(e.target.value)}><option value="">All</option>{['MORNING','AFTERNOON','EVENING'].map(v=><option key={v} value={v}>{humanize(v.toLowerCase())}</option>)}</select></label>}
      {applicable('milking_cohort') && <label className="text-sm">Milking Group<input className="mt-1 w-full rounded border p-2" value={cohort} onChange={e=>setCohort(e.target.value)}/></label>}
      {applicable('animal_id') && <label className="text-sm">Animal ID<input className="mt-1 w-full rounded border p-2" value={animalId} onChange={e=>setAnimalId(e.target.value)}/></label>}
    </div>
    <div className="flex flex-wrap items-end gap-2"><button disabled={loading || !report.id} onClick={previewReport} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">Preview</button><button disabled={loading || !report.id} onClick={printReport} className="rounded border px-4 py-2 text-sm disabled:opacity-50">Print</button><label className="text-sm">Save as<select className="ml-2 rounded border p-2" value={format} onChange={e=>setFormat(e.target.value as Format)}><option>PDF</option><option>XLSX</option><option>CSV</option></select></label><button disabled={loading || !report.id} onClick={saveReport} className="rounded border px-4 py-2 text-sm disabled:opacity-50">Save {format}</button></div>
    {error && <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}{notice && <div className="rounded border border-slate-300 bg-slate-50 p-3 text-sm text-slate-700">{notice}</div>}
    {previewed && preview && <div className="rounded border bg-white p-4"><div className="mb-3 flex flex-wrap items-baseline justify-between gap-2"><div><h3 className="text-lg font-semibold">{preview.title || report.name}</h3><div className="text-sm text-slate-600">{preview.record_count.toLocaleString()} record{preview.record_count===1?'':'s'}</div></div>{preview.rows?.length===0 && <div className="text-sm text-slate-600">No records found.</div>}</div>
      {summaryItems.length > 0 && <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{summaryItems.map(([key,value]) => <div key={key} className="rounded bg-slate-50 p-3"><div className="text-xs font-medium uppercase tracking-wide text-slate-500">{labelFor(key)}</div><div className="mt-1 text-sm font-semibold text-slate-900">{displayValue(value)}</div></div>)}</div>}
      {preview.rows?.length > 0 && <div className="overflow-x-auto"><table className="min-w-full table-auto border-collapse text-sm"><thead className="bg-slate-100"><tr>{columns.map(column=><th key={column} className="whitespace-nowrap border-b px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">{labelFor(column)}</th>)}</tr></thead><tbody>{preview.rows.map((row,index)=><tr key={index} className="align-top odd:bg-white even:bg-slate-50">{columns.map(column=><td key={column} className="max-w-[24rem] whitespace-normal break-words border-b px-3 py-2 text-slate-800">{displayValue(row[column])}</td>)}</tr>)}</tbody></table></div>}
    </div>}
  </div>;
}
