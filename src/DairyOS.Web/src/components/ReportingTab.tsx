import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ChevronDown, ChevronUp, Columns3, FileSpreadsheet, FileText, Printer, RefreshCw, Table2 } from 'lucide-react';
import { apiUrl } from '../config/api';
import './Reporting.css';

/* Reporting workspace: Area -> Report -> Parameters -> Generate -> Analyse -> Export / Print.
   Every figure, column, filter and total comes from the /farm/reports API. Nothing is calculated here. */

type ColumnType = 'text' | 'integer' | 'number' | 'litres' | 'kg' | 'money' | 'rate' | 'percent' | 'date' | 'datetime' | 'status' | 'days';
type Column = { key: string; label: string; type: ColumnType; group: string; tier: 'default' | 'optional' | 'advanced'; total: boolean };
type Option = { value: string; label: string };
type FilterDef = { key: string; label: string; kind: 'select' | 'text' | 'animal' | 'toggle'; options: Option[]; options_source: string | null; required: boolean; default: string | boolean | null; help: string | null };
type ReportDef = { id: string; area: string; title: string; purpose: string; authority: string; period: 'none' | 'as_of' | 'range'; default_period: string; filters: FilterDef[]; columns: Column[]; basis: string };
type Area = { id: string; title: string; description: string; reports: ReportDef[] };
type Catalog = { operational_today: string; period_modes: Option[]; quarters: { value: number; label: string }[]; option_sources: Record<string, Option[]>; export_formats: string[]; areas: Area[] };
type Drill = { report_id: string; label: string; filters: Record<string, string>; period?: PeriodSpec };
type Row = Record<string, unknown> & { _drill?: Drill; _emphasis?: string };
type Paging = { page: number; page_size: number; pages: number; total_rows: number; sort_key: string | null; sort_dir: 'asc' | 'desc' | null };
type Section = { id: string; title: string; note: string | null; primary: boolean; columns: Column[]; rows: Row[]; totals: (Record<string, unknown> & { _label?: string }) | null; row_count: number; paging: Paging | null; empty_message: string | null };
type Metric = { key: string; label: string; value: unknown; type: ColumnType; hint: string | null };
type Control = { check: string; expected: unknown; actual: unknown; difference: unknown; type: ColumnType; status: string };
type Result = { report: { id: string; title: string; purpose: string; authority: string }; period: { label: string }; generated_at: string; filters_applied: { label: string; value: string }[]; summary: Metric[]; sections: Section[]; notes: string[]; reconciliation: Control[] };
type PeriodSpec = { mode?: string; year?: number; month?: number; quarter?: number; start_date?: string; end_date?: string; as_of_date?: string };
type ExportFormat = 'PDF' | 'XLSX' | 'CSV';
type DesktopWindow = Window & { pywebview?: { api?: { save_reporting_export?: (filename: string, format: ExportFormat, payload: string) => Promise<{ status: 'SAVED' | 'CANCELLED'; bytes?: number }> } } };

const NUMERIC = new Set<ColumnType>(['integer', 'number', 'litres', 'kg', 'money', 'rate', 'percent', 'days']);
const DECIMALS: Partial<Record<ColumnType, number>> = { integer: 0, days: 0, number: 2, litres: 2, kg: 3, money: 2, rate: 4, percent: 1 };
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const SHORT_MONTHS = MONTHS.map(name => name.slice(0, 3));
const PAGE_SIZE = 100;

export function formatReportValue(value: unknown, type: ColumnType, withCurrency = false): string {
  if (value === null || value === undefined || value === '') return '';
  if (type === 'date') {
    const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
    return match ? `${match[3]}-${SHORT_MONTHS[Number(match[2]) - 1]}-${match[1]}` : String(value);
  }
  if (type === 'datetime') return String(value).replace('T', ' ').slice(0, 16);
  if (NUMERIC.has(type)) {
    const number = Number(value);
    if (!Number.isFinite(number)) return String(value);
    const digits = DECIMALS[type] ?? 2;
    const text = number.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
    if (type === 'money' && withCurrency) return `PKR ${text}`;
    return type === 'percent' ? `${text}%` : text;
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

async function failure(response: Response, fallback: string): Promise<string> {
  try {
    const detail = (await response.json())?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  } catch { /* keep the operator-facing fallback */ }
  return fallback;
}

function toBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let offset = 0; offset < bytes.length; offset += 0x8000) binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  return btoa(binary);
}

export default function ReportingTab() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [areaId, setAreaId] = useState('herd');
  const [report, setReport] = useState<ReportDef | null>(null);
  const [period, setPeriod] = useState<PeriodSpec>({});
  const [filters, setFilters] = useState<Record<string, string | boolean>>({});
  const [columns, setColumns] = useState<string[] | null>(null);
  const [showColumns, setShowColumns] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const requestSeq = useRef(0);

  useEffect(() => {
    fetch(apiUrl('/farm/reports/catalog'))
      .then(response => (response.ok ? response.json() : Promise.reject(new Error('The report catalogue is unavailable.'))))
      .then((data: Catalog) => setCatalog(data))
      .catch(e => setError(e instanceof Error ? e.message : 'The report catalogue is unavailable.'));
  }, []);

  const area = useMemo(() => catalog?.areas.find(item => item.id === areaId) ?? catalog?.areas[0] ?? null, [catalog, areaId]);
  const today = catalog?.operational_today ?? '';
  const year = Number(today.slice(0, 4)) || new Date().getFullYear();
  const years = useMemo(() => Array.from({ length: 8 }, (_, index) => year + 1 - index), [year]);

  const body = useCallback((target: ReportDef, spec: PeriodSpec, values: Record<string, string | boolean>, selected: string[] | null,
    sorting: { key: string; dir: 'asc' | 'desc' } | null, pageNumber: number) => ({
    report_id: target.id, period: spec,
    filters: Object.fromEntries(Object.entries(values).filter(([, value]) => value !== '' && value !== null && value !== undefined)),
    ...(selected ? { columns: selected } : {}),
    ...(sorting ? { sort_key: sorting.key, sort_dir: sorting.dir } : {}),
    page: pageNumber, page_size: PAGE_SIZE,
  }), []);

  const generate = useCallback(async (target: ReportDef, spec: PeriodSpec, values: Record<string, string | boolean>, selected: string[] | null,
    sorting: { key: string; dir: 'asc' | 'desc' } | null, pageNumber: number) => {
    const missing = target.filters.find(item => item.required && !String(values[item.key] ?? '').trim());
    if (missing) { setResult(null); setError(''); setNotice(`Enter ${missing.label} and select Generate.`); return; }
    if (spec.mode === 'CUSTOM' && (!spec.start_date || !spec.end_date)) { setResult(null); setNotice('Select both From Date and To Date.'); return; }
    const sequence = ++requestSeq.current;
    setBusy(true); setError(''); setNotice('');
    try {
      const response = await fetch(apiUrl('/farm/reports/run'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body(target, spec, values, selected, sorting, pageNumber)) });
      if (!response.ok) throw new Error(await failure(response, 'The report could not be generated.'));
      const data: Result = await response.json();
      if (sequence === requestSeq.current) setResult(data);
    } catch (e) {
      if (sequence === requestSeq.current) { setResult(null); setError(e instanceof Error ? e.message : 'The report could not be generated.'); }
    } finally { if (sequence === requestSeq.current) setBusy(false); }
  }, [body]);

  const openReport = useCallback((target: ReportDef, presetFilters: Record<string, string> = {}, presetPeriod?: PeriodSpec) => {
    const spec: PeriodSpec = presetPeriod ?? (target.period === 'range' ? { mode: target.default_period, year, month: Number(today.slice(5, 7)) || 1, quarter: Math.floor(((Number(today.slice(5, 7)) || 1) - 1) / 3) + 1 }
      : target.period === 'as_of' ? { as_of_date: today } : {});
    const values: Record<string, string | boolean> = {};
    target.filters.forEach(item => { values[item.key] = item.kind === 'toggle' ? Boolean(item.default) : String(item.default ?? ''); });
    Object.assign(values, presetFilters);
    setAreaId(target.area); setReport(target); setPeriod(spec); setFilters(values); setColumns(null); setSort(null); setPage(1);
    setShowColumns(false); setShowAdvanced(false); setResult(null); setError(''); setNotice('');
    void generate(target, spec, values, null, null, 1);
  }, [generate, today, year]);

  const rerun = (next: { spec?: PeriodSpec; values?: Record<string, string | boolean>; selected?: string[] | null; sorting?: { key: string; dir: 'asc' | 'desc' } | null; pageNumber?: number } = {}) => {
    if (!report) return;
    void generate(report, next.spec ?? period, next.values ?? filters, next.selected === undefined ? columns : next.selected,
      next.sorting === undefined ? sort : next.sorting, next.pageNumber ?? page);
  };

  const changePeriod = (patch: PeriodSpec) => { const spec = { ...period, ...patch }; setPeriod(spec); setPage(1); rerun({ spec, pageNumber: 1 }); };
  const changeFilter = (key: string, value: string | boolean, immediate: boolean) => {
    const values = { ...filters, [key]: value }; setFilters(values);
    if (immediate) { setPage(1); rerun({ values, pageNumber: 1 }); }
  };
  const changeSort = (key: string) => {
    const sorting = sort?.key === key && sort.dir === 'asc' ? { key, dir: 'desc' as const } : { key, dir: 'asc' as const };
    setSort(sorting); setPage(1); rerun({ sorting, pageNumber: 1 });
  };
  const changePage = (pageNumber: number) => { setPage(pageNumber); rerun({ pageNumber }); };
  const activeColumns = columns ?? report?.columns.filter(item => item.tier === 'default').map(item => item.key) ?? [];
  const toggleColumn = (key: string) => {
    if (!report) return;
    const chosen = activeColumns.includes(key) ? activeColumns.filter(item => item !== key) : [...activeColumns, key];
    if (chosen.length === 0) { setNotice('A report needs at least one column.'); return; }
    const ordered = report.columns.map(item => item.key).filter(item => chosen.includes(item));
    setColumns(ordered); rerun({ selected: ordered });
  };
  const resetColumns = () => { setColumns(null); rerun({ selected: null }); };

  const drill = (target: Drill) => {
    const definition = catalog?.areas.flatMap(item => item.reports).find(item => item.id === target.report_id);
    if (definition) openReport(definition, target.filters, target.period);
  };

  const exportReport = async (format: ExportFormat) => {
    if (!report) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const response = await fetch(apiUrl(`/farm/reports/export?format=${format}`), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body(report, period, filters, columns, sort, 1)) });
      if (!response.ok) throw new Error(await failure(response, 'The report could not be exported.'));
      const blob = await response.blob();
      const named = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') || '');
      const filename = named?.[1] || `DairyOS-${report.title.replace(/[^A-Za-z0-9]+/g, '-')}.${format.toLowerCase()}`;
      const save = (window as DesktopWindow).pywebview?.api?.save_reporting_export;
      if (save) {
        const saved = await save(filename, format, toBase64(await blob.arrayBuffer()));
        if (saved.status === 'SAVED') setNotice(`${filename} saved.`);
      } else {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url; anchor.download = filename; document.body.appendChild(anchor); anchor.click(); anchor.remove();
        URL.revokeObjectURL(url); setNotice(`${filename} downloaded.`);
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'The report could not be exported.'); }
    finally { setBusy(false); }
  };
  /* Print is a print-ready PDF. DairyOS never calls the native webview print
     dialog: the desktop shell does not support it reliably. */
  const printReport = async () => { await exportReport('PDF'); };

  if (!catalog) return <div className="rpt"><p className="rpt-muted">{error || 'Loading the report catalogue…'}</p></div>;

  /* ------------------------------------------------------------ catalogue */
  if (!report) {
    return (
      <div className="rpt">
        <header className="rpt-head"><div><h2>Reporting</h2><p className="rpt-muted">Choose an area, then the report that answers your question. Every report opens with sensible defaults.</p></div></header>
        <nav className="rpt-areas" aria-label="Reporting areas">
          {catalog.areas.map(item => <button key={item.id} type="button" className={item.id === area?.id ? 'rpt-area active' : 'rpt-area'} onClick={() => setAreaId(item.id)}>{item.title}<span>{item.reports.length}</span></button>)}
        </nav>
        {error && <div className="rpt-error" role="alert">{error}</div>}
        {area && <>
          <p className="rpt-area-note">{area.description}</p>
          <div className="rpt-cards">
            {area.reports.map(item => <button key={item.id} type="button" className="rpt-card" onClick={() => openReport(item)}>
              <Table2 size={16} aria-hidden /><strong>{item.title}</strong><span>{item.purpose}</span>
            </button>)}
          </div>
        </>}
      </div>
    );
  }

  /* --------------------------------------------------------------- report */
  const groups = report.columns.reduce<Record<string, Column[]>>((map, item) => { if (item.tier !== 'advanced' || showAdvanced) (map[item.group] ||= []).push(item); return map; }, {});
  const hasAdvanced = report.columns.some(item => item.tier === 'advanced');
  const optionsFor = (item: FilterDef): Option[] => (item.options_source ? catalog.option_sources[item.options_source] ?? [] : item.options);

  return (
    <div className="rpt">
      <header className="rpt-head rpt-no-print">
        <div>
          <button type="button" className="rpt-back" onClick={() => { setReport(null); setResult(null); setError(''); setNotice(''); }}><ArrowLeft size={14} aria-hidden />{area?.title ?? 'Reports'}</button>
          <h2>{report.title}</h2><p className="rpt-muted">{report.purpose}</p>
        </div>
        <div className="rpt-actions">
          <button type="button" onClick={() => rerun()} disabled={busy}><RefreshCw size={14} aria-hidden />Generate</button>
          <button type="button" onClick={() => void printReport()} disabled={busy || !result}><Printer size={14} aria-hidden />Print</button>
          <button type="button" onClick={() => void exportReport('PDF')} disabled={busy || !result}><FileText size={14} aria-hidden />PDF</button>
          <button type="button" onClick={() => void exportReport('XLSX')} disabled={busy || !result}><FileSpreadsheet size={14} aria-hidden />Excel</button>
          <button type="button" onClick={() => void exportReport('CSV')} disabled={busy || !result}><FileSpreadsheet size={14} aria-hidden />CSV</button>
        </div>
      </header>

      <section className="rpt-params rpt-no-print" aria-label="Report parameters">
        {report.period === 'range' && <>
          <label>Period<select value={period.mode ?? report.default_period} onChange={e => changePeriod({ mode: e.target.value })}>{catalog.period_modes.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          {period.mode === 'MONTH' && <label>Month<select value={period.month} onChange={e => changePeriod({ month: Number(e.target.value) })}>{MONTHS.map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></label>}
          {period.mode === 'QUARTER' && <label>Quarter<select value={period.quarter} onChange={e => changePeriod({ quarter: Number(e.target.value) })}>{catalog.quarters.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>}
          {(period.mode === 'MONTH' || period.mode === 'QUARTER' || period.mode === 'CALENDAR_YEAR') && <label>Year<select value={period.year} onChange={e => changePeriod({ year: Number(e.target.value) })}>{years.map(item => <option key={item} value={item}>{item}</option>)}</select></label>}
          {period.mode === 'CUSTOM' && <>
            <label>From Date<input type="date" value={period.start_date ?? ''} onChange={e => changePeriod({ start_date: e.target.value })} /></label>
            <label>To Date<input type="date" value={period.end_date ?? ''} onChange={e => changePeriod({ end_date: e.target.value })} /></label>
          </>}
        </>}
        {report.period === 'as_of' && <label>As of Date<input type="date" value={period.as_of_date ?? today} onChange={e => changePeriod({ as_of_date: e.target.value })} /></label>}
        {report.filters.map(item => item.kind === 'toggle'
          ? <label key={item.key} className="rpt-toggle"><input type="checkbox" checked={Boolean(filters[item.key])} onChange={e => changeFilter(item.key, e.target.checked, true)} />{item.label}</label>
          : item.kind === 'select'
            ? <label key={item.key}>{item.label}<select value={String(filters[item.key] ?? '')} onChange={e => changeFilter(item.key, e.target.value, true)}>{!item.required && item.default === null && <option value="">All</option>}{optionsFor(item).map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
            : <label key={item.key}>{item.label}{item.required ? ' *' : ''}<input value={String(filters[item.key] ?? '')} placeholder={item.kind === 'animal' ? 'e.g. TD-0001' : ''} onChange={e => changeFilter(item.key, e.target.value, false)} onKeyDown={e => { if (e.key === 'Enter') { setPage(1); rerun({ pageNumber: 1 }); } }} onBlur={() => rerun({ pageNumber: 1 })} /></label>)}
        {report.columns.length > 0 && <button type="button" className="rpt-columns-button" onClick={() => setShowColumns(open => !open)} aria-expanded={showColumns}><Columns3 size={14} aria-hidden />Customize Columns</button>}
      </section>

      {showColumns && <section className="rpt-columns rpt-no-print" aria-label="Customize columns">
        {Object.entries(groups).map(([group, items]) => <fieldset key={group}><legend>{group}</legend>{items.map(item => <label key={item.key}><input type="checkbox" checked={activeColumns.includes(item.key)} onChange={() => toggleColumn(item.key)} />{item.label}</label>)}</fieldset>)}
        <div className="rpt-columns-foot">
          <button type="button" onClick={resetColumns}>Restore default columns</button>
          {hasAdvanced && <label className="rpt-toggle"><input type="checkbox" checked={showAdvanced} onChange={e => setShowAdvanced(e.target.checked)} />Show record administration fields</label>}
        </div>
      </section>}

      {error && <div className="rpt-error" role="alert">{error}</div>}
      {notice && <div className="rpt-notice" role="status">{notice}</div>}
      {busy && !result && <p className="rpt-muted">Generating report…</p>}

      {result && <article className={busy ? 'rpt-result rpt-busy' : 'rpt-result'}>
        <div className="rpt-title">
          <h3>{result.report.title}</h3>
          <p>{result.period.label}{result.filters_applied.map(item => ` · ${item.label}: ${item.value}`).join('')}</p>
          <p className="rpt-muted">Generated {String(result.generated_at).replace('T', ' ').slice(0, 16)}</p>
        </div>

        {result.summary.length > 0 && <div className="rpt-tiles">{result.summary.map(item => <div key={item.key} className="rpt-tile" title={item.hint ?? undefined}>
          <span>{item.label}</span><strong>{formatReportValue(item.value, item.type, true) || 'Not available'}</strong>{item.hint && <em>{item.hint}</em>}
        </div>)}</div>}

        {result.sections.map(section => <section key={section.id} className="rpt-section">
          <h4>{section.title}{section.primary && section.paging ? <span>{section.paging.total_rows.toLocaleString()} record{section.paging.total_rows === 1 ? '' : 's'}</span> : null}</h4>
          {section.note && <p className="rpt-muted">{section.note}</p>}
          {section.rows.length === 0 ? <p className="rpt-empty">{section.empty_message || 'No records match the selected parameters.'}</p> : <div className="rpt-table-wrap"><table className="rpt-table">
            <thead><tr>{section.columns.map(column => {
              const sorted = section.primary && section.paging?.sort_key === column.key ? section.paging.sort_dir : null;
              return <th key={column.key} className={NUMERIC.has(column.type) ? 'num' : ''} aria-sort={sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : undefined}>
                {section.primary ? <button type="button" onClick={() => changeSort(column.key)}>{column.label}{sorted === 'asc' ? <ChevronUp size={12} aria-hidden /> : sorted === 'desc' ? <ChevronDown size={12} aria-hidden /> : null}</button> : column.label}
              </th>;
            })}</tr></thead>
            <tbody>{section.rows.map((row, index) => <tr key={index} className={[row._emphasis === 'total' ? 'strong' : '', row._drill ? 'drill' : ''].join(' ').trim() || undefined}
              onClick={row._drill ? () => drill(row._drill as Drill) : undefined} title={row._drill ? `Open supporting detail: ${row._drill.label}` : undefined}>
              {section.columns.map(column => <td key={column.key} className={NUMERIC.has(column.type) ? 'num' : column.type === 'status' ? 'status' : ''}>{formatReportValue(row[column.key], column.type)}</td>)}
            </tr>)}</tbody>
            {section.totals && <tfoot><tr>{section.columns.map((column, index) => {
              const text = formatReportValue(section.totals?.[column.key], column.type);
              return <td key={column.key} className={NUMERIC.has(column.type) ? 'num' : ''}>{index === 0 && !text ? section.totals?._label ?? 'Total' : text}</td>;
            })}</tr></tfoot>}
          </table></div>}
          {section.primary && section.paging && section.paging.pages > 1 && <div className="rpt-paging rpt-no-print">
            <button type="button" disabled={busy || section.paging.page <= 1} onClick={() => changePage(section.paging!.page - 1)}>Previous</button>
            <span>Page {section.paging.page} of {section.paging.pages}</span>
            <button type="button" disabled={busy || section.paging.page >= section.paging.pages} onClick={() => changePage(section.paging!.page + 1)}>Next</button>
            <em>Totals cover every record. Exports include every record.</em>
          </div>}
        </section>)}

        {result.reconciliation.length > 0 && <section className="rpt-section">
          <h4>Reconciliation Controls</h4>
          <div className="rpt-table-wrap"><table className="rpt-table"><thead><tr><th>Control</th><th className="num">Expected</th><th className="num">Actual</th><th className="num">Difference</th><th>Result</th></tr></thead>
            <tbody>{result.reconciliation.map(item => <tr key={item.check}><td>{item.check}</td><td className="num">{formatReportValue(item.expected, item.type, true)}</td><td className="num">{formatReportValue(item.actual, item.type, true)}</td><td className="num">{formatReportValue(item.difference, item.type, true)}</td><td className={item.status === 'PASS' ? 'pass' : 'fail'}>{item.status === 'PASS' ? 'Agrees' : 'Difference'}</td></tr>)}</tbody></table></div>
        </section>}

        {result.notes.length > 0 && <section className="rpt-notes"><h4>Notes</h4><ul>{result.notes.map(note => <li key={note}>{note}</li>)}</ul></section>}
        <p className="rpt-authority">Source: {result.report.authority}</p>
      </article>}
    </div>
  );
}
