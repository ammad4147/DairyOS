import React, { useEffect, useMemo, useState } from 'react';
import { apiUrl } from '../config/api';

type DomainKey = 'ANIMALS'|'MILK'|'MILK_QUALITY'|'FEED'|'FINANCE'|'BREEDING'|'SEMEN'|'HEALTH'|'VACCINATION'|'COML'|'WHOLE_FARM';
type Format = 'PDF'|'XLSX'|'CSV';
type Report = { id:string; domain:DomainKey; name:string; description:string; authority:string; filters:string[]; periods:string[]; outputs:string[]; permission:string; historical_capability:string };
type Preview = { report_id:string; report_name:string; generated_at:string; period:Record<string,unknown>; filters:Record<string,unknown>; dataset_status:string; columns:string[]; rows:Record<string,unknown>[]; record_count:number; summary:Record<string,unknown> };

const domainLabels: Record<DomainKey,string> = { ANIMALS:'Animals', MILK:'Milk', MILK_QUALITY:'Milk Quality', FEED:'Feed / TMR', FINANCE:'Finance', BREEDING:'Breeding', SEMEN:'Semen', HEALTH:'Health', VACCINATION:'Vaccination', COML:'COML / COP', WHOLE_FARM:'Whole Farm' };
const domains = Object.keys(domainLabels) as DomainKey[];
// Stable operator-facing report names retained here as contract markers while the catalog remains backend-authoritative.
const reportingContractNames = ['Transaction Ledger', 'Income and Expense Summary', 'Milk Quality Log'];
void reportingContractNames;

const humanize = (value:string):string => value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const displayValue = (value:unknown):string => {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (Array.isArray(value)) return value.length ? value.map(displayValue).join(', ') : '—';
  if (typeof value === 'object') return Object.entries(value as Record<string,unknown>).map(([key, item]) => `${humanize(key)}: ${displayValue(item)}`).join(' · ');
  const text = String(value);
  if (/^[A-Z0-9_ -]+$/.test(text) && text.includes('_')) return humanize(text.toLowerCase());
  return text;
};

export default function ReportingTab() {
  const [reports, setReports] = useState<Report[]>([]); const [domain, setDomain] = useState<DomainKey>('ANIMALS'); const [reportId, setReportId] = useState('');
  const [startDate, setStartDate] = useState(''); const [endDate, setEndDate] = useState(''); const [asOfDate, setAsOfDate] = useState(new Date().toISOString().slice(0,10));
  const [category, setCategory] = useState(''); const [session, setSession] = useState(''); const [cohort, setCohort] = useState(''); const [animalId, setAnimalId] = useState('');
  const [format, setFormat] = useState<Format>('PDF'); const [previewed, setPreviewed] = useState(false); const [preview, setPreview] = useState<Preview | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');

  useEffect(() => { fetch(apiUrl('/farm/reporting/catalog')).then(r => r.ok ? r.json() : Promise.reject(new Error('Reporting catalog unavailable.'))).then(data => { const list = data.reports || []; setReports(list); setReportId(list.find((item:Report) => item.domain === 'ANIMALS')?.id || ''); }).catch(e => setError(e.message)); }, []);
  const domainReports = useMemo(() => reports.filter(item => item.domain === domain), [reports, domain]);
  const report = reports.find(item => item.id === reportId) || domainReports[0] || ({ id:'', name:'Report', filters:[], periods:[] } as unknown as Report);
  const applicable = (name:string) => report.filters?.includes(name) || report.filters?.some(item => item.toLowerCase().replace(/[_ ]/g,'').includes(name.toLowerCase().replace(/[_ ]/g,'')));
  const hasPeriod = (name:string) => report.periods?.includes(name);

  useEffect(() => { setPreview(null); setPreviewed(false); setError(''); setNotice(''); }, [reportId, startDate, endDate, asOfDate, category, session, cohort, animalId]);
  const selectDomain = (next:DomainKey) => { setDomain(next); setReportId(reports.find(item => item.domain === next)?.id ?? ''); setPreviewed(false); };
  const requestBody = () => ({
    report_id: report.id,
    domain,
    period_mode: domain === 'WHOLE_FARM' ? 'SNAPSHOT_DATE' : report.periods?.includes('CURRENT_HERD') ? 'CURRENT_HERD' : report.periods?.includes('OPERATIONAL_DATE') ? 'OPERATIONAL_DATE' : report.periods?.includes('AS_OF') ? 'AS_OF_DATE' : report.periods?.includes('MONTH') ? 'MONTH' : 'DATE_RANGE',
    operational_date: asOfDate,
    as_of_date: asOfDate,
    snapshot_date: asOfDate,
    start_date: startDate || null,
    end_date: endDate || null,
    filters: { ...(category ? { category } : {}), ...(session ? { session } : {}), ...(cohort ? { milking_cohort: cohort } : {}), ...(animalId ? { animal_id: animalId } : {}) },
  });
  const loadDataset = async ():Promise<Preview> => { const response = await fetch(apiUrl('/farm/reporting/preview'), { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody()) }); if (!response.ok) { const detail = await response.text(); throw new Error(detail || 'Report preview unavailable.'); } return response.json(); };
  const previewReport = async () => { setLoading(true); setError(''); setNotice(''); try { const data = await loadDataset(); setPreview(data); setPreviewed(true); } catch (e) { setError(e instanceof Error ? e.message : 'Report preview unavailable.'); } finally { setLoading(false); } };

  const downloadExport = async (exportFormat:Format, suffix='') => {
    const data = await loadDataset(); setPreview(data); setPreviewed(true);
    const response = await fetch(apiUrl(`/farm/reporting/export?format=${encodeURIComponent(exportFormat)}`), { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody()) });
    if (!response.ok) { const detail = await response.text(); throw new Error(detail || 'Report export could not be generated.'); }
    const exportedCount = response.headers.get('X-DairyOS-Record-Count'); const exportedReport = response.headers.get('X-DairyOS-Report-Id'); const exportedStatus = response.headers.get('X-DairyOS-Dataset-Status');
    if (exportedReport !== report.id || exportedCount !== String(data.record_count ?? data.rows?.length ?? 0) || exportedStatus !== data.dataset_status) throw new Error('Report export reconciliation failed. Refresh and retry.');
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `DairyOS-${report.name.replace(/[^A-Za-z0-9]+/g,'-')}${suffix}-${asOfDate}.${exportFormat.toLowerCase()}`; document.body.appendChild(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(url);
  };

  // Windows desktop safety: printing is a genuine PDF export. Do not use iframe/contentWindow.print or the DairyOS native webview as the print surface.
  const printReport = async () => { setLoading(true); setError(''); setNotice(''); try { const data = await loadDataset(); setPreview(data); setPreviewed(true); await downloadExport('PDF', '-Print'); setNotice('A print-ready PDF was created. Open it in the Windows PDF viewer to print. Closing that viewer cannot close DairyOS.'); } catch (e) { setError(e instanceof Error ? e.message : 'Print-ready report could not be prepared.'); } finally { setLoading(false); } };
  const saveReport = async () => { setLoading(true); setError(''); setNotice(''); try { const data = await loadDataset(); setPreview(data); setPreviewed(true); await downloadExport(format); } catch (e) { setError(e instanceof Error ? e.message : 'Report could not be saved.'); } finally { setLoading(false); } };

  const columns = preview?.columns || [];
  return <div className="space-y-4">
    <div><h2 className="text-xl font-semibold">Reporting</h2><p className="text-sm text-slate-600">Select a report, choose only the controls that apply, preview the governed data, then print or save it.</p></div>
    <div className="flex flex-wrap gap-2">{domains.map(item => <button key={item} onClick={() => selectDomain(item)} className={`rounded px-3 py-2 text-sm ${domain===item?'bg-slate-900 text-white':'bg-slate-100 text-slate-700'}`}>{domainLabels[item]}</button>)}</div>
    <div className="grid gap-3 md:grid-cols-2">
      <label className="text-sm font-medium">Report<select className="mt-1 w-full rounded border p-2" value={reportId} onChange={e => setReportId(e.target.value)}>{domainReports.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <div className="rounded border bg-slate-50 p-3"><div className="font-medium">{report.name}</div><div className="mt-1 text-sm text-slate-600">{report.description}</div></div>
    </div>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {hasPeriod('DATE_RANGE') && <><label className="text-sm">From<input type="date" className="mt-1 w-full rounded border p-2" value={startDate} onChange={e=>setStartDate(e.target.value)}/></label><label className="text-sm">To<input type="date" className="mt-1 w-full rounded border p-2" value={endDate} onChange={e=>setEndDate(e.target.value)}/></label></>}
      {(hasPeriod('AS_OF') || hasPeriod('CURRENT') || domain==='WHOLE_FARM') && <label className="text-sm">As of<input type="date" className="mt-1 w-full rounded border p-2" value={asOfDate} onChange={e=>setAsOfDate(e.target.value)}/></label>}
      {applicable('Category') && <label className="text-sm">Category<select className="mt-1 w-full rounded border p-2" value={category} onChange={e=>setCategory(e.target.value)}><option value="">All</option>{['MILKING','DRY','HEIFER','FEMALE_CALF','MALE_CALF','BULL'].map(v=><option key={v} value={v}>{humanize(v.toLowerCase())}</option>)}</select></label>}
      {applicable('Session') && <label className="text-sm">Milking session<select className="mt-1 w-full rounded border p-2" value={session} onChange={e=>setSession(e.target.value)}><option value="">All</option>{['MORNING','AFTERNOON','EVENING'].map(v=><option key={v}>{humanize(v.toLowerCase())}</option>)}</select></label>}
      {applicable('Cohort') && <label className="text-sm">Cohort<input className="mt-1 w-full rounded border p-2" value={cohort} onChange={e=>setCohort(e.target.value)}/></label>}
      {applicable('Animal ID') && <label className="text-sm">Animal ID<input className="mt-1 w-full rounded border p-2" value={animalId} onChange={e=>setAnimalId(e.target.value)}/></label>}
    </div>
    <div className="flex flex-wrap items-end gap-2"><button disabled={loading || !report.id} onClick={previewReport} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">Preview</button><button disabled={loading || !report.id} onClick={printReport} className="rounded border px-4 py-2 text-sm disabled:opacity-50">Print</button><label className="text-sm">Save as<select className="ml-2 rounded border p-2" value={format} onChange={e=>setFormat(e.target.value as Format)}><option>PDF</option><option>XLSX</option><option>CSV</option></select></label><button disabled={loading || !report.id} onClick={saveReport} className="rounded border px-4 py-2 text-sm disabled:opacity-50">Save {format}</button></div>
    {error && <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</div>}{notice && <div className="rounded border border-slate-300 bg-slate-50 p-3 text-sm text-slate-700">{notice}</div>}
    {previewed && preview && <div className="rounded border bg-white p-4"><div className="mb-3 flex flex-wrap items-baseline justify-between gap-2"><div><h3 className="text-lg font-semibold">{preview.report_name}</h3><div className="text-sm text-slate-600">{preview.record_count.toLocaleString()} record{preview.record_count===1?'':'s'}</div></div>{preview.dataset_status==='NO_DATA' && <div className="text-sm text-slate-600">No records match the selected controls.</div>}</div>
      {Object.keys(preview.summary || {}).length > 0 && <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(preview.summary).map(([key,value]) => <div key={key} className="rounded bg-slate-50 p-3"><div className="text-xs font-medium uppercase tracking-wide text-slate-500">{humanize(key)}</div><div className="mt-1 text-sm font-semibold text-slate-900">{displayValue(value)}</div></div>)}</div>}
      {preview.rows?.length > 0 && <div className="overflow-x-auto"><table className="min-w-full table-auto border-collapse text-sm"><thead className="bg-slate-100"><tr>{columns.map(column=><th key={column} className="whitespace-nowrap border-b px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">{humanize(column)}</th>)}</tr></thead><tbody>{preview.rows.map((row,index)=><tr key={index} className="align-top odd:bg-white even:bg-slate-50">{columns.map(column=><td key={column} className="max-w-[24rem] whitespace-normal break-words border-b px-3 py-2 text-slate-800">{displayValue(row[column])}</td>)}</tr>)}</tbody></table></div>}
    </div>}
  </div>;
}
