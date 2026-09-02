import React, { useEffect, useMemo, useState } from 'react';
import { Ban, Edit3, Printer, Search } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
const API_BASE=API_BASE_URL||'http://127.0.0.1:8000';
type MasterCategory='FEED'|'OPEX';type LedgerFilter='ALL'|MasterCategory;type ExploreView='COMBINED'|'REVENUE'|'EXPENSES';type PeriodMode='MONTH'|'CUSTOM';
type TaxonomyResponse={master_categories:MasterCategory[];taxonomies:Record<string,Record<string,string[]>>;items:Record<MasterCategory,string[]>};
type Transaction={id:number;transaction_type:string;category:string;master_category?:MasterCategory|null;sub_category?:string|null;custom_specification?:string|null;amount:number;quantity?:number|null;unit?:string|null;unit_rate?:number|null;date?:string|null;reference?:string|null;payment_method?:string|null;counterparty?:string|null;vendor_name?:string|null;notes?:string|null;status?:string|null;due_date?:string|null;settled_date?:string|null};
type HerdAnimal={id:string;breed:string;category:string;status:string};type Props={onSaveSale?:(liters:number)=>void;onUpdateReceivables?:(amount:number)=>void;herdMasterList?:HerdAnimal[]};
const inputStyle:React.CSSProperties={background:'#1e293b',color:'#fff',border:'1px solid #334155',padding:'7px 8px',borderRadius:5,fontSize:11,boxSizing:'border-box',width:'100%'};
const smallButton:React.CSSProperties={background:'#1e293b',border:'1px solid #334155',color:'#cbd5e1',padding:'4px 7px',borderRadius:4,fontSize:9,cursor:'pointer',display:'inline-flex',alignItems:'center',gap:4};
const button=(bg:string):React.CSSProperties=>({background:bg,color:'#fff',border:0,borderRadius:5,padding:'8px 12px',fontSize:10,fontWeight:800,cursor:'pointer'});const pakistanDateFormatter=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Karachi',year:'numeric',month:'2-digit',day:'2-digit'});const today=()=>pakistanDateFormatter.format(new Date());const money=(v:number)=>`PKR ${Number(v||0).toLocaleString('en-PK',{maximumFractionDigits:2})}`;
const voidReasonFromNotes=(notes?:string|null)=>{const matches=Array.from(String(notes??'').matchAll(/REASON=([^\n\r]*)/g));return matches.length?matches[matches.length-1][1].trim():''};
const monthStartFor=(iso:string)=>`${iso.slice(0,7)}-01`;
const monthEndFor=(iso:string)=>{const [y,m]=iso.slice(0,7).split('-').map(Number);return new Date(Date.UTC(y,m,0)).toISOString().slice(0,10)};
const inRange=(value:string|undefined|null,start:string,end:string)=>{const d=String(value||'').slice(0,10);return Boolean(d&&d>=start&&d<=end)};
const isRevenue=(t:Transaction)=>t.transaction_type==='INCOME'||t.transaction_type==='RECEIPT';
const isExpense=(t:Transaction)=>t.transaction_type==='EXPENSE'||t.transaction_type==='PAYMENT';
const activeAmount=(t:Transaction)=>String(t.status||'').toUpperCase()==='VOID'?0:Number(t.amount||0);
const csvCell=(value:unknown)=>`"${String(value??'').replace(/"/g,'""')}"`;

export default function FinanceTab({onSaveSale,onUpdateReceivables,herdMasterList=[]}:Props={}){
 const [transactions,setTransactions]=useState<Transaction[]>([]),[taxonomy,setTaxonomy]=useState<TaxonomyResponse|null>(null),[masterCategory,setMasterCategory]=useState<MasterCategory>('FEED'),[subCategory,setSubCategory]=useState(''),[customSpecification,setCustomSpecification]=useState(''),[quantity,setQuantity]=useState(''),[unit,setUnit]=useState('kg'),[unitRate,setUnitRate]=useState(''),[directAmount,setDirectAmount]=useState(''),[expenseDate,setExpenseDate]=useState(today()),[vendor,setVendor]=useState(''),[paymentMethod,setPaymentMethod]=useState('BANK'),[reference,setReference]=useState(''),[notes,setNotes]=useState(''),[dueDate,setDueDate]=useState(''),[ledgerFilter,setLedgerFilter]=useState<LedgerFilter>('ALL'),[search,setSearch]=useState(''),[loading,setLoading]=useState(true),[saving,setSaving]=useState(false),[error,setError]=useState('');
 const [voidTarget,setVoidTarget]=useState<Transaction|null>(null),[voidReason,setVoidReason]=useState(''),[editTarget,setEditTarget]=useState<Transaction|null>(null),[editSaving,setEditSaving]=useState(false),[revCategory,setRevCategory]=useState('Milk Sales'),[revAnimalId,setRevAnimalId]=useState(''),[revAmount,setRevAmount]=useState(''),[revQty,setRevQty]=useState(''),[revDate,setRevDate]=useState(today()),[revRef,setRevRef]=useState(''),[revCounterparty,setRevCounterparty]=useState(''),[revNotes,setRevNotes]=useState(''),[revStatus,setRevStatus]=useState<'RECEIVED'|'RECEIVABLE'>('RECEIVABLE'),[revDueDate,setRevDueDate]=useState('');
 const [exploreOpen,setExploreOpen]=useState(false),[exploreView,setExploreView]=useState<ExploreView>('COMBINED'),[exploreExpenseFilter,setExploreExpenseFilter]=useState<LedgerFilter>('ALL'),[explorePeriodMode,setExplorePeriodMode]=useState<PeriodMode>('MONTH'),[exploreMonth,setExploreMonth]=useState(today().slice(0,7)),[exploreStart,setExploreStart]=useState(monthStartFor(today())),[exploreEnd,setExploreEnd]=useState(today()),[statusPeriodMode,setStatusPeriodMode]=useState<'ALL'|'MONTH'|'CUSTOM'>('ALL'),[statusMonth,setStatusMonth]=useState(today().slice(0,7)),[statusStart,setStatusStart]=useState(monthStartFor(today())),[statusEnd,setStatusEnd]=useState(today());
 const load=async()=>{setLoading(true);setError('');try{const [ledgerRes,taxRes]=await Promise.all([fetch(`${API_BASE}/farm/finance-ledger`),fetch(`${API_BASE}/farm/finance-ledger/taxonomy`)]);if(!ledgerRes.ok||!taxRes.ok)throw new Error('Finance API unavailable.');const ledger=await ledgerRes.json(),tax=await taxRes.json();setTransactions(ledger.transactions??[]);setTaxonomy(tax)}catch(e){setError(e instanceof Error?e.message:'Unable to load Finance data.')}finally{setLoading(false)}};
 useEffect(()=>{void load()},[]);useEffect(()=>{const items=taxonomy?.items?.[masterCategory]??[];setSubCategory(items[0]??'');setCustomSpecification('')},[masterCategory,taxonomy]);
 const expenseRows=useMemo(()=>transactions.filter(isExpense),[transactions]);const activeExpenseRows=useMemo(()=>expenseRows.filter(t=>t.status!=='VOID'),[expenseRows]);const revenueRows=useMemo(()=>transactions.filter(isRevenue),[transactions]);const activeRevenueRows=useMemo(()=>revenueRows.filter(t=>t.status!=='VOID'),[revenueRows]);
 const currentMonthStart=monthStartFor(today()),currentMonthEnd=monthEndFor(today());
 const currentMonthExpenseRows=useMemo(()=>expenseRows.filter(t=>inRange(t.date,currentMonthStart,currentMonthEnd)),[expenseRows,currentMonthStart,currentMonthEnd]);
 const currentMonthRevenueRows=useMemo(()=>revenueRows.filter(t=>inRange(t.date,currentMonthStart,currentMonthEnd)),[revenueRows,currentMonthStart,currentMonthEnd]);
 const filteredExpenses=useMemo(()=>{const q=search.trim().toLowerCase();const base=ledgerFilter==='ALL'?currentMonthExpenseRows:currentMonthExpenseRows.filter(t=>t.master_category===ledgerFilter);return base.filter(t=>!q||[t.sub_category,t.custom_specification,t.vendor_name,t.counterparty,t.reference,t.notes,t.status].some(v=>String(v??'').toLowerCase().includes(q)))},[currentMonthExpenseRows,ledgerFilter,search]);
 const cashRevenue=activeRevenueRows.filter(t=>['RECEIVED','RECORDED','PAID'].includes(String(t.status))).reduce((s,t)=>s+t.amount,0),receivables=activeRevenueRows.filter(t=>t.status==='RECEIVABLE').reduce((s,t)=>s+t.amount,0),totalExpenses=activeExpenseRows.reduce((s,t)=>s+t.amount,0),payableTotal=activeExpenseRows.filter(t=>t.status==='PAYABLE').reduce((s,t)=>s+t.amount,0),netCash=cashRevenue-totalExpenses;
 const exploreBounds=useMemo(()=>explorePeriodMode==='MONTH'?{start:`${exploreMonth}-01`,end:monthEndFor(`${exploreMonth}-01`)}:{start:exploreStart,end:exploreEnd},[explorePeriodMode,exploreMonth,exploreStart,exploreEnd]);
 const exploredRows=useMemo(()=>transactions.filter(t=>{
   if(!inRange(t.date,exploreBounds.start,exploreBounds.end))return false;
   if(exploreView==='REVENUE'&&!isRevenue(t))return false;
   if(exploreView==='EXPENSES'&&!isExpense(t))return false;
   if(isExpense(t)&&exploreExpenseFilter!=='ALL'&&t.master_category!==exploreExpenseFilter)return false;
   return isRevenue(t)||isExpense(t);
 }).sort((a,b)=>String(a.date||'').localeCompare(String(b.date||''))||a.id-b.id),[transactions,exploreBounds,exploreView,exploreExpenseFilter]);
 const carriedForward=useMemo(()=>transactions.filter(t=>String(t.date||'').slice(0,10)<exploreBounds.start).reduce((sum,t)=>sum+(isRevenue(t)?activeAmount(t):isExpense(t)?-activeAmount(t):0),0),[transactions,exploreBounds.start]);
 const periodRevenue=useMemo(()=>exploredRows.filter(isRevenue).reduce((s,t)=>s+activeAmount(t),0),[exploredRows]);
 const periodExpenses=useMemo(()=>exploredRows.filter(isExpense).reduce((s,t)=>s+activeAmount(t),0),[exploredRows]);
 const periodNet=periodRevenue-periodExpenses,closingBalance=carriedForward+periodNet;
 const statusBounds=useMemo(()=>{
   if(statusPeriodMode==='MONTH')return{start:`${statusMonth}-01`,end:monthEndFor(`${statusMonth}-01`)};
   if(statusPeriodMode==='CUSTOM')return{start:statusStart,end:statusEnd};
   return{start:'0001-01-01',end:today()};
 },[statusPeriodMode,statusMonth,statusStart,statusEnd]);
 const statusRows=useMemo(()=>transactions.filter(t=>inRange(t.date,statusBounds.start,statusBounds.end)),[transactions,statusBounds]);
 const statusRevenue=useMemo(()=>statusRows.filter(isRevenue).reduce((s,t)=>s+activeAmount(t),0),[statusRows]);
 const statusExpenses=useMemo(()=>statusRows.filter(isExpense).reduce((s,t)=>s+activeAmount(t),0),[statusRows]);
 const statusBalance=statusRevenue-statusExpenses;
 const graphMax=Math.max(statusRevenue,statusExpenses,1);
 const saveExploredLedger=()=>{
   const header=['Date','Type','Particulars','Master Category','Counterparty','Reference','Status','Amount'];
   const lines=exploredRows.map(t=>[
     String(t.date||'').slice(0,10),isRevenue(t)?'Revenue':'Expense',t.sub_category||t.category||'',t.master_category||'',t.counterparty||t.vendor_name||'',t.reference||'',t.status||'RECORDED',Number(t.amount||0).toFixed(2)
   ]);
   const summary=[
     [],['Carried Forward','','','','','','',carriedForward.toFixed(2)],
     ['Period Revenue','','','','','','',periodRevenue.toFixed(2)],
     ['Period Expenses','','','','','','',periodExpenses.toFixed(2)],
     ['Period Net','','','','','','',periodNet.toFixed(2)],
     ['Closing Balance','','','','','','',closingBalance.toFixed(2)]
   ];
   const csv=[header,...lines,...summary].map(line=>line.map(csvCell).join(',')).join('\r\n');
   const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
   const url=URL.createObjectURL(blob),a=document.createElement('a');
   a.href=url;a.download=`DairyOS-Finance-Ledger-${exploreBounds.start}-to-${exploreBounds.end}.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
 };

 const ledgerParticulars=(t:Transaction)=>t.sub_category||t.category||'—';
 const ledgerCounterparty=(t:Transaction)=>t.counterparty||t.vendor_name||'—';
 const ledgerReference=(t:Transaction)=>t.reference||'—';
 const ledgerStatus=(t:Transaction)=>t.status||'RECORDED';

 const saveLedgerCsv=(
   title:string,
   rows:Transaction[],
   start:string,
   end:string,
   summary:Record<string,number>={},
 )=>{
   const header=[
     'Date',
     'Type',
     'Particulars',
     'Master Category',
     'Counterparty',
     'Reference',
     'Status',
     'Amount',
   ];

   const detailRows=rows.map(t=>[
     String(t.date||'').slice(0,10),
     isRevenue(t)?'Revenue':'Expense',
     ledgerParticulars(t),
     t.master_category||'',
     ledgerCounterparty(t),
     ledgerReference(t),
     ledgerStatus(t),
     Number(t.amount||0).toFixed(2),
   ]);

   const summaryRows=[
     [],
     ...Object.entries(summary).map(([label,value])=>[
       label,'','','','','','',Number(value||0).toFixed(2),
     ]),
   ];

   const csv=[
     [title],
     ['Reporting Period',`${start} to ${end}`],
     [],
     header,
     ...detailRows,
     ...summaryRows,
   ].map(line=>line.map(csvCell).join(',')).join('\r\n');

   const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});
   const url=URL.createObjectURL(blob);
   const link=document.createElement('a');
   const safeTitle=title
     .replace(/[^A-Za-z0-9]+/g,'-')
     .replace(/^-|-$/g,'');

   link.href=url;
   link.download=`DairyOS-${safeTitle}-${start}-to-${end}.csv`;
   document.body.appendChild(link);
   link.click();
   link.remove();
   URL.revokeObjectURL(url);
 };

 const printLedger=(
   title:string,
   rows:Transaction[],
   start:string,
   end:string,
   summary:Record<string,number>={},
 )=>{
   const popup=window.open('','_blank','width=1100,height=800');

   if(!popup){
     setError(
       'The ledger print window was blocked. Allow pop-ups for DairyOS and try again.'
     );
     return;
   }

   const esc=(value:unknown)=>String(value??'').replace(
     /[&<>"']/g,
     ch=>({
       '&':'&amp;',
       '<':'&lt;',
       '>':'&gt;',
       '"':'&quot;',
       "'":'&#39;',
     } as Record<string,string>)[ch]||ch,
   );

   const tableRows=rows.map(t=>{
     const isVoid=String(t.status||'').toUpperCase()==='VOID';
     const reason=isVoid?voidReasonFromNotes(t.notes):'';

     return `
       <tr class="${isVoid?'void':''}">
         <td>${esc(String(t.date||'').slice(0,10)||'—')}</td>
         <td>${esc(isRevenue(t)?'Revenue':'Expense')}</td>
         <td>
           ${esc(ledgerParticulars(t))}
           ${reason
             ? `<div class="void-reason">VOID: ${esc(reason)}</div>`
             : ''}
         </td>
         <td>${esc(t.master_category||'—')}</td>
         <td>${esc(ledgerCounterparty(t))}</td>
         <td>${esc(ledgerReference(t))}</td>
         <td>${esc(ledgerStatus(t))}</td>
         <td class="amount">${esc(money(Number(t.amount||0)))}</td>
       </tr>
     `;
   }).join('');

   const summaryHtml=Object.keys(summary).length
     ? `
       <div class="summary">
         ${Object.entries(summary).map(([label,value])=>`
           <div class="summary-row">
             <span>${esc(label)}</span>
             <strong>${esc(money(Number(value||0)))}</strong>
           </div>
         `).join('')}
       </div>
     `
     : '';

   popup.document.write(`
     <!doctype html>
     <html>
       <head>
         <meta charset="utf-8">
         <title>${esc(title)}</title>
         <style>
           @page {
             size: A4 landscape;
             margin: 12mm;
           }

           * {
             box-sizing: border-box;
           }

           body {
             margin: 0;
             color: #111827;
             font-family: Arial, Helvetica, sans-serif;
             font-size: 11px;
           }

           h1 {
             margin: 0 0 4px;
             font-size: 18px;
           }

           .period {
             margin-bottom: 14px;
             color: #475569;
           }

           table {
             width: 100%;
             border-collapse: collapse;
           }

           th,
           td {
             padding: 6px 7px;
             border-bottom: 1px solid #cbd5e1;
             text-align: left;
             vertical-align: top;
           }

           th {
             background: #f1f5f9;
             font-size: 9px;
             text-transform: uppercase;
           }

           .amount {
             text-align: right;
             white-space: nowrap;
           }

           tr.void td {
             color: #b91c1c;
             background: #fef2f2;
             text-decoration: line-through;
           }

           tr.void .void-reason {
             text-decoration: none;
           }

           .void-reason {
             margin-top: 3px;
             color: #b91c1c;
             font-size: 9px;
             font-weight: bold;
           }

           .summary {
             width: 380px;
             margin-top: 16px;
             margin-left: auto;
             border-top: 2px solid #334155;
           }

           .summary-row {
             display: flex;
             justify-content: space-between;
             gap: 20px;
             padding: 5px 2px;
             border-bottom: 1px solid #e2e8f0;
           }

           .footer {
             margin-top: 14px;
             color: #64748b;
             font-size: 9px;
           }
         </style>
       </head>

       <body>
         <h1>DairyOS — ${esc(title)}</h1>

         <div class="period">
           Reporting period: ${esc(start)} to ${esc(end)}
         </div>

         <table>
           <thead>
             <tr>
               <th>Date</th>
               <th>Type</th>
               <th>Particulars</th>
               <th>Master Category</th>
               <th>Counterparty</th>
               <th>Reference</th>
               <th>Status</th>
               <th style="text-align:right">Amount</th>
             </tr>
           </thead>

           <tbody>
             ${tableRows || `
               <tr>
                 <td colspan="8">
                   No ledger entries in this selected view.
                 </td>
               </tr>
             `}
           </tbody>
         </table>

         ${summaryHtml}

         <div class="footer">
           Generated from the selected DairyOS ledger only.
           VOID transactions remain visible for audit history and are
           excluded from active totals.
         </div>
       </body>
     </html>
   `);

   popup.document.close();
   popup.focus();

   window.setTimeout(()=>{
     popup.print();
   },250);
 };

 const calculatedAmount=quantity&&unitRate?Number(quantity)*Number(unitRate):Number(directAmount||0);useEffect(()=>{onUpdateReceivables?.(receivables)},[receivables,onUpdateReceivables]);
 const saveExpense=async(e:React.FormEvent)=>{e.preventDefault();setSaving(true);setError('');try{const status=paymentMethod==='CREDIT'?'PAYABLE':'PAID';const r=await fetch(`${API_BASE}/farm/finance-ledger`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({transaction_type:'EXPENSE',master_category:masterCategory,sub_category:subCategory,custom_specification:subCategory==='Other'?customSpecification:null,quantity:quantity?Number(quantity):null,unit:quantity?unit:null,unit_rate:quantity?Number(unitRate):null,amount:calculatedAmount,transaction_date:expenseDate,payment_method:paymentMethod,counterparty:vendor||null,reference:reference||null,notes:notes||null,status,due_date:status==='PAYABLE'?dueDate:null})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Expense could not be saved.');setQuantity('');setUnitRate('');setDirectAmount('');setVendor('');setReference('');setNotes('');setCustomSpecification('');setDueDate('');await load()}catch(e){setError(e instanceof Error?e.message:'Expense save failed.')}finally{setSaving(false)}};
 const animalSaleCategories:Record<string,string>={'Milking Animal Sale':'MILKING_ANIMAL_SALE','Dry Animal Sale':'DRY_ANIMAL_SALE','Heifer Sale':'HEIFER_SALE','Female Calf Sale':'FEMALE_CALF_SALE','Male Calf Sale':'MALE_CALF_SALE','Bull Sale':'BULL_SALE'};
 const isAnimalSale=Boolean(animalSaleCategories[revCategory]);
 const saleEligibleAnimals=useMemo(()=>{if(!isAnimalSale)return [];const wanted:Record<string,string[]>={'Milking Animal Sale':['milking'],'Dry Animal Sale':['dry'],'Heifer Sale':['heifer'],'Female Calf Sale':['female','calf'],'Male Calf Sale':['male','calf'],'Bull Sale':['bull']};const tokens=wanted[revCategory]||[];return herdMasterList.filter(a=>{const hay=`${a.category} ${a.status}`.toLowerCase();return tokens.every(t=>hay.includes(t))})},[herdMasterList,isAnimalSale,revCategory]);
 useEffect(()=>{if(!isAnimalSale){setRevAnimalId('');return}if(revAnimalId&&!saleEligibleAnimals.some(a=>a.id===revAnimalId))setRevAnimalId('')},[isAnimalSale,revAnimalId,saleEligibleAnimals]);
 const saveRevenue=async(e:React.FormEvent)=>{e.preventDefault();const amount=Number(revAmount);if(!(amount>0))return;if(isAnimalSale&&!revAnimalId){setError('Select the Animal ID being sold.');return}setSaving(true);setError('');try{const map:Record<string,string>={'Milk Sales':'MILK_SALES','Organic Manure / Dung':'MANURE_SALES',...animalSaleCategories};const r=await fetch(`${API_BASE}/farm/finance-ledger`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({transaction_type:revStatus==='RECEIVED'?'RECEIPT':'INCOME',category:map[revCategory]??'OTHER_REVENUE',amount,quantity:revQty?Number(revQty):null,unit:revCategory==='Milk Sales'&&revQty?'litres':null,transaction_date:revDate,payment_method:revStatus==='RECEIVABLE'?'CREDIT':'CASH',counterparty:revCounterparty||null,status:revStatus,due_date:revStatus==='RECEIVABLE'?revDueDate:null,reference:revRef||null,notes:isAnimalSale?`${revCategory} — Animal ${revAnimalId}${revNotes?` — ${revNotes}`:''}`:(revNotes||null)})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Revenue could not be saved.');
 if(isAnimalSale){const disposition=await fetch(`${API_BASE}/farm/animals/${encodeURIComponent(revAnimalId)}/disposition`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({disposition:'SOLD',effective_date:revDate,reason:`Recorded through Finance: ${revCategory}`,buyer_or_counterparty:revCounterparty||null,amount,reference:revRef||`FIN-${d.id||'SALE'}`,notes:revNotes||null,operator:'Finance UI'})});if(!disposition.ok){try{await fetch(`${API_BASE}/farm/finance-ledger/${d.id}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:'VOID',reason:'Animal sale disposition failed; Finance row automatically revoked for reconciliation.'})})}catch{}throw new Error((await disposition.text())||'Animal sale could not be linked to the Animal Passport. Finance row was revoked.')}}
 if(revCategory==='Milk Sales'&&revQty)onSaveSale?.(Number(revQty));setRevAnimalId('');setRevAmount('');setRevQty('');setRevRef('');setRevCounterparty('');setRevNotes('');setRevDueDate('');await load()}catch(e){setError(e instanceof Error?e.message:'Revenue save failed.')}finally{setSaving(false)}};

 const updateStatus=async(t:Transaction,status:string,reason?:string)=>{try{const r=await fetch(`${API_BASE}/farm/finance-ledger/${t.id}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status,reason})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Status update failed.');await load()}catch(e){setError(e instanceof Error?e.message:'Status update failed.')}finally{setVoidTarget(null);setVoidReason('')}};
 const saveEdit=async(e:React.FormEvent<HTMLFormElement>)=>{e.preventDefault();if(!editTarget)return;setEditSaving(true);setError('');try{const f=new FormData(e.currentTarget),qty=Number(f.get('quantity')||0),rate=Number(f.get('unit_rate')||0),amount=qty>0?qty*rate:Number(f.get('amount')||0);const r=await fetch(`${API_BASE}/farm/finance-ledger/${editTarget.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({master_category:f.get('master_category'),sub_category:f.get('sub_category'),custom_specification:f.get('custom_specification')||null,quantity:qty>0?qty:null,unit:qty>0?String(f.get('unit')||'kg'):null,unit_rate:qty>0?rate:null,amount,transaction_date:f.get('transaction_date'),payment_method:f.get('payment_method'),counterparty:f.get('counterparty'),reference:f.get('reference'),notes:f.get('notes'),status:f.get('status'),due_date:f.get('due_date')||null})});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Finance entry could not be edited.');setEditTarget(null);await load()}catch(e){setError(e instanceof Error?e.message:'Finance edit failed.')}finally{setEditSaving(false)}};
 return <div style={{padding:14,color:'#fff',height:'100%',overflowY:'auto',overflowX:'hidden',boxSizing:'border-box',minWidth:0}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:10,flexWrap:'wrap',marginBottom:10}}><div><div style={{fontSize:18,fontWeight:800}}>Finance & Accounting</div><div style={{fontSize:10,color:'#94a3b8'}}>Revenue, receivables, expenses, payables and the persistent accounting ledger.</div></div><button type="button" onClick={()=>setExploreOpen(v=>!v)} style={{...button(exploreOpen?'#475569':'#7c3aed'),display:'inline-flex',alignItems:'center',gap:5}}><Search size={11}/>{exploreOpen?'Close Explorer':'Explore Ledgers'}</button></div>
  {error&&<div style={{background:'rgba(239,68,68,.12)',border:'1px solid #ef4444',color:'#fecaca',padding:8,borderRadius:6,marginBottom:10,fontSize:10}}>{error}</div>}
  <div style={{display:'grid',gridTemplateColumns:'repeat(5,minmax(0,1fr))',gap:7,marginBottom:10}}>{[['Cash Revenue',cashRevenue,'#34d399'],['Receivables',receivables,'#f59e0b'],['Payables',payableTotal,'#fb7185'],['Total Expenses',totalExpenses,'#f87171'],['Net Cash Position',netCash,'#38bdf8']].map(([label,value,color])=><div key={String(label)} style={{background:'#111827',border:'1px solid #1f2937',borderLeft:`4px solid ${String(color)}`,borderRadius:7,padding:'9px 10px',minWidth:0}}><div style={{fontSize:8,color:'#94a3b8',textTransform:'uppercase',fontWeight:800}}>{String(label)}</div><div style={{fontSize:15,fontWeight:900,color:String(color),marginTop:3}}>{money(Number(value))}</div></div>)}</div>
  {exploreOpen&&<section style={{...card,marginBottom:10,borderColor:'#7c3aed'}}>
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8,flexWrap:'wrap',marginBottom:8}}>
      <div><div style={{fontSize:12,fontWeight:900,color:'#c4b5fd'}}>Ledger Explorer</div><div style={{fontSize:9,color:'#94a3b8'}}>Historical accounting view. VOID rows remain visible but are excluded from balances.</div></div>
      <div style={{display:'flex',gap:5}}><button type="button" onClick={saveExploredLedger} style={smallButton}>Save CSV</button><button type="button" onClick={()=>printLedger('Finance Ledger Explorer',exploredRows,exploreBounds.start,exploreBounds.end,{'Carried Forward':carriedForward,'Period Revenue':periodRevenue,'Period Expenses':periodExpenses,'Period Net':periodNet,'Closing Balance':closingBalance})} style={smallButton}><Printer size={11}/> Print</button></div>
    </div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:8,marginBottom:8}}>
      <div style={{display:'flex',gap:5,flexWrap:'wrap'}}>{(['COMBINED','REVENUE','EXPENSES'] as ExploreView[]).map(v=><button type="button" key={v} onClick={()=>setExploreView(v)} style={{...smallButton,background:exploreView===v?'#7c3aed':'#1e293b',color:'#fff'}}>{v==='COMBINED'?'Combined':v==='REVENUE'?'Revenue':'Expenses'}</button>)}</div>
      <div style={{display:'flex',gap:5,flexWrap:'wrap',justifyContent:'flex-end'}}>{(['ALL','FEED','OPEX'] as LedgerFilter[]).map(v=><button type="button" key={v} onClick={()=>setExploreExpenseFilter(v)} disabled={exploreView==='REVENUE'} style={{...smallButton,opacity:exploreView==='REVENUE'?.45:1,background:exploreExpenseFilter===v?'#0369a1':'#1e293b',color:'#fff'}}>{v==='ALL'?'All Expenses':v==='FEED'?'Feed-only':'OPEX-only'}</button>)}</div>
    </div>
    <div style={{display:'flex',gap:6,alignItems:'center',flexWrap:'wrap',marginBottom:8}}>
      <button type="button" onClick={()=>setExplorePeriodMode('MONTH')} style={{...smallButton,background:explorePeriodMode==='MONTH'?'#0f766e':'#1e293b',color:'#fff'}}>Month</button>
      <button type="button" onClick={()=>setExplorePeriodMode('CUSTOM')} style={{...smallButton,background:explorePeriodMode==='CUSTOM'?'#0f766e':'#1e293b',color:'#fff'}}>Custom Date Range</button>
      {explorePeriodMode==='MONTH'?<input type="month" value={exploreMonth} onChange={e=>setExploreMonth(e.target.value)} style={{...inputStyle,width:155}}/>:<><input type="date" value={exploreStart} onChange={e=>setExploreStart(e.target.value)} style={{...inputStyle,width:150}}/><span style={{fontSize:9,color:'#64748b'}}>to</span><input type="date" value={exploreEnd} onChange={e=>setExploreEnd(e.target.value)} style={{...inputStyle,width:150}}/></>}
      <span style={{fontSize:9,color:'#94a3b8'}}>{exploreBounds.start} → {exploreBounds.end}</span>
    </div>
    <div style={{display:'grid',gridTemplateColumns:'repeat(5,minmax(0,1fr))',gap:6,marginBottom:8}}>
      {[['Carried Forward',carriedForward,'#94a3b8'],['Period Revenue',periodRevenue,'#34d399'],['Period Expenses',periodExpenses,'#f87171'],['Period Net',periodNet,periodNet>=0?'#38bdf8':'#f87171'],['Closing Balance',closingBalance,closingBalance>=0?'#a78bfa':'#f87171']].map(([label,value,color])=><div key={String(label)} style={{background:'#0f172a',border:'1px solid #1f2937',borderRadius:6,padding:8}}><div style={{fontSize:8,color:'#64748b',textTransform:'uppercase',fontWeight:800}}>{String(label)}</div><div style={{fontSize:12,color:String(color),fontWeight:900,marginTop:2}}>{money(Number(value))}</div></div>)}
    </div>
    <div style={{...ledgerLine,color:'#64748b',fontSize:8,fontWeight:800,textTransform:'uppercase',borderBottom:'1px solid #1f2937',padding:'0 8px 5px'}}><span style={{width:76,flex:'0 0 76px'}}>Date</span><span style={{width:64,flex:'0 0 64px'}}>Type</span><span style={ledgerEllipsis}>Particulars</span><span style={{...ledgerEllipsis,flexBasis:92}}>Counterparty</span><span style={{width:76,flex:'0 0 76px'}}>Status</span><span style={{width:118,flex:'0 0 118px',textAlign:'right'}}>Amount</span></div>
    <div style={{maxHeight:310,overflowY:'auto'}}>{exploredRows.map(r=>{const isVoid=String(r.status||'').toUpperCase()==='VOID',reason=isVoid?voidReasonFromNotes(r.notes):'';return <div key={`${isRevenue(r)?'R':'E'}-${r.id}`} style={{...row,color:isVoid?'#f87171':'#fff',background:isVoid?'rgba(239,68,68,.06)':'transparent'}}><div style={{...ledgerLine,textDecoration:isVoid?'line-through':'none'}}><span style={{width:76,flex:'0 0 76px'}}>{String(r.date||'').slice(0,10)||'—'}</span><span style={{width:64,flex:'0 0 64px',fontWeight:800,color:isRevenue(r)?'#34d399':'#f59e0b'}}>{isRevenue(r)?'REV':'EXP'}</span><span style={ledgerEllipsis}>{r.sub_category||r.category||'—'}</span><span style={{...ledgerEllipsis,flexBasis:92}}>{r.counterparty||r.vendor_name||'—'}</span><span style={{width:76,flex:'0 0 76px',fontWeight:800}}>{r.status||'RECORDED'}</span><strong style={{width:118,flex:'0 0 118px',textAlign:'right'}}>{money(r.amount)}</strong></div>{isVoid&&<span style={{...voidReasonStyle,maxWidth:220}}>VOID: {reason||'See audit trail'}</span>}</div>})}{exploredRows.length===0&&<div style={empty}>No ledger entries in this period/view.</div>}</div>
    <div style={{display:'flex',justifyContent:'space-between',gap:8,flexWrap:'wrap',paddingTop:8,borderTop:'1px solid #1f2937',fontSize:10}}><strong>Period Aggregate: Revenue {money(periodRevenue)} · Expenses {money(periodExpenses)} · Net {money(periodNet)}</strong><strong style={{color:closingBalance>=0?'#a78bfa':'#f87171'}}>Closing: {money(closingBalance)}</strong></div>
  </section>}
  <div style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) minmax(0,1fr)',gap:10,alignItems:'start'}}>
   <div style={{display:'grid',gap:10}}>
    <form onSubmit={saveRevenue} style={card}><div style={sectionTitle}>Record Revenue</div><div style={{display:'grid',gridTemplateColumns:'1.2fr 1fr 1fr',gap:6}}><select value={revCategory} onChange={e=>setRevCategory(e.target.value)} style={inputStyle}><option>Milk Sales</option><option>Organic Manure / Dung</option><option>Milking Animal Sale</option><option>Dry Animal Sale</option><option>Heifer Sale</option><option>Female Calf Sale</option><option>Male Calf Sale</option><option>Bull Sale</option></select><input required type="number" min="0" step="0.01" value={revAmount} onChange={e=>setRevAmount(e.target.value)} style={inputStyle} placeholder="Amount"/><input type="number" min="0" step="0.01" value={revQty} onChange={e=>setRevQty(e.target.value)} style={inputStyle} placeholder="Quantity"/></div>{isAnimalSale&&<div style={{marginTop:6}}><select required value={revAnimalId} onChange={e=>setRevAnimalId(e.target.value)} style={inputStyle}><option value="">Select Animal ID being sold</option>{saleEligibleAnimals.map(a=><option key={a.id} value={a.id}>{a.id} · {a.category} · {a.breed}</option>)}</select><div style={{fontSize:9,color:'#fbbf24',marginTop:3}}>Saving this revenue permanently marks the selected animal SOLD, removes it from active herd strength, and retains its Passport / Final Disposal history.</div></div>}<div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:6,marginTop:6}}><input type="date" value={revDate} onChange={e=>setRevDate(e.target.value)} style={inputStyle}/><select value={revStatus} onChange={e=>setRevStatus(e.target.value as 'RECEIVED'|'RECEIVABLE')} style={inputStyle}><option value="RECEIVABLE">Credit / Receivable</option><option value="RECEIVED">Cash Received</option></select>{revStatus==='RECEIVABLE'?<input required type="date" value={revDueDate} onChange={e=>setRevDueDate(e.target.value)} style={inputStyle}/>:<input value={revRef} onChange={e=>setRevRef(e.target.value)} style={inputStyle} placeholder="Reference"/>}</div>{revStatus==='RECEIVABLE'&&<input value={revRef} onChange={e=>setRevRef(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Reference"/>}<input value={revCounterparty} onChange={e=>setRevCounterparty(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Customer / Buyer"/><input value={revNotes} onChange={e=>setRevNotes(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Notes"/><button disabled={saving} type="submit" style={{...button('#059669'),width:'100%',marginTop:6}}>{saving?'Saving…':'Save Revenue'}</button></form>
    <section style={card}><div style={{...sectionTitle,display:'flex',justifyContent:'space-between',gap:6}}><span>Revenue Ledger</span><div style={{display:'flex',alignItems:'center',gap:5,flexWrap:'wrap'}}><span style={{fontSize:8,color:'#64748b'}}>Current month ? {currentMonthStart} → {currentMonthEnd}</span><button type="button" onClick={()=>saveLedgerCsv('Revenue Ledger',currentMonthRevenueRows,currentMonthStart,currentMonthEnd,{'Active Revenue Total':currentMonthRevenueRows.reduce((s,t)=>s+activeAmount(t),0)})} style={smallButton}>Save CSV</button><button type="button" onClick={()=>printLedger('Revenue Ledger',currentMonthRevenueRows,currentMonthStart,currentMonthEnd,{'Active Revenue Total':currentMonthRevenueRows.reduce((s,t)=>s+activeAmount(t),0)})} style={smallButton}><Printer size={11}/> Print</button></div></div><div style={{...ledgerLine,color:'#64748b',fontSize:8,fontWeight:800,textTransform:'uppercase',borderBottom:'1px solid #1f2937',padding:'0 8px 5px'}}><span style={{width:76,flex:'0 0 76px'}}>Date</span><span style={ledgerEllipsis}>Particulars</span><span style={{...ledgerEllipsis,flexBasis:100}}>Counterparty</span><span style={{...ledgerEllipsis,flexBasis:100}}>Reference</span><span style={{width:76,flex:'0 0 76px'}}>Status</span><span style={{width:118,flex:'0 0 118px',textAlign:'right'}}>Amount</span></div>{currentMonthRevenueRows.slice(0,50).map(r=>{const isVoid=r.status==='VOID',reason=isVoid?voidReasonFromNotes(r.notes):'';return <div key={r.id} style={{...row,color:isVoid?'#f87171':'#fff',background:isVoid?'rgba(239,68,68,.06)':'transparent',borderLeft:isVoid?'2px solid #ef4444':undefined}}><div style={{...ledgerLine,textDecoration:isVoid?'line-through':'none'}}><span style={{width:76,flex:'0 0 76px'}}>{r.date?.slice(0,10)||'—'}</span><span title={r.notes||r.category} style={ledgerEllipsis}>{r.category||'OTHER_REVENUE'}</span><span title={r.counterparty||''} style={{...ledgerEllipsis,flexBasis:100}}>{r.counterparty||'—'}</span><span title={r.reference||''} style={{...ledgerEllipsis,flexBasis:100}}>{r.reference||'—'}</span><span style={{width:76,flex:'0 0 76px',fontWeight:800,color:isVoid?'#f87171':r.status==='RECEIVABLE'?'#f59e0b':'#34d399'}}>{r.status||'RECORDED'}</span><strong style={{width:118,flex:'0 0 118px',textAlign:'right'}}>{money(r.amount)}</strong></div>{isVoid?<span title={reason||'Reason recorded in audit trail'} style={{...voidReasonStyle,maxWidth:190}}>VOID: {reason||'See audit trail'}</span>:<><>{r.status==='RECEIVABLE'&&<button onClick={()=>void updateStatus(r,'RECEIVED')} style={smallButton}>Received</button>}</><button onClick={()=>setVoidTarget(r)} style={{...smallButton,color:'#f87171'}}><Ban size={10}/>Void</button></>}</div>})}{!loading&&currentMonthRevenueRows.length===0&&<div style={empty}>No revenue entries in the current calendar month.</div>}</section>
   </div>
   <div style={{display:'grid',gap:10}}>
    <form onSubmit={saveExpense} style={card}><div style={sectionTitle}>Record Expense</div><div style={{fontSize:9,color:'#64748b',marginBottom:7}}>Feed purchases are entered here and automatically appear in the Feed tab. Other operating expenses remain accounting entries here.</div><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6}}>
  <button
    type="button"
    onClick={()=>setMasterCategory('FEED')}
    style={{
      background:masterCategory==='FEED'?'#0369a1':'#1e293b',
      border:'1px solid',
      borderColor:masterCategory==='FEED'?'#38bdf8':'#334155',
      color:'#fff',
      padding:'10px 10px',
      borderRadius:5,
      fontSize:11,
      fontWeight:800,
      cursor:'pointer'
    }}
  >
    Feed Expenses
  </button>

  <button
    type="button"
    onClick={()=>setMasterCategory('OPEX')}
    style={{
      background:masterCategory==='OPEX'?'#92400e':'#1e293b',
      border:'1px solid',
      borderColor:masterCategory==='OPEX'?'#f59e0b':'#334155',
      color:'#fff',
      padding:'10px 10px',
      borderRadius:5,
      fontSize:11,
      fontWeight:800,
      cursor:'pointer'
    }}
  >
    OPEX
  </button>
</div>

<div style={{marginTop:6}}>
  <select
    required
    value={subCategory}
    onChange={e=>setSubCategory(e.target.value)}
    style={inputStyle}
  >
    {(Object.entries(taxonomy?.taxonomies?.[masterCategory]??{}) as [string,string[]][]).map(([group,items])=>(
      <optgroup key={group} label={group.replace(/_/g,' ')}>
        {items.map(item=>(
          <option key={item} value={item}>{item}</option>
        ))}
      </optgroup>
    ))}
  </select>
</div>{subCategory==='Other'&&<input required value={customSpecification} onChange={e=>setCustomSpecification(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Specification"/>}<input value={vendor} onChange={e=>setVendor(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Vendor / Supplier"/><div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr 1fr',gap:6,marginTop:6}}><input type="number" min="0" step="0.001" value={quantity} onChange={e=>setQuantity(e.target.value)} style={inputStyle} placeholder="Quantity"/><select value={unit} onChange={e=>setUnit(e.target.value)} style={inputStyle}><option>kg</option><option>bag</option><option>ton</option><option>litre</option><option>service</option><option>head</option><option>unit</option></select><input type="number" min="0" step="0.01" value={unitRate} onChange={e=>setUnitRate(e.target.value)} style={inputStyle} placeholder="Unit rate" disabled={!quantity}/><input type="number" min="0" step="0.01" value={quantity?calculatedAmount:directAmount} onChange={e=>quantity?undefined:setDirectAmount(e.target.value)} style={inputStyle} placeholder="Amount" readOnly={Boolean(quantity)}/></div><div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:6,marginTop:6}}><input type="date" value={expenseDate} onChange={e=>setExpenseDate(e.target.value)} style={inputStyle}/><select value={paymentMethod} onChange={e=>setPaymentMethod(e.target.value)} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option value="CREDIT">Credit / Payable</option></select>{paymentMethod==='CREDIT'?<input required type="date" value={dueDate} onChange={e=>setDueDate(e.target.value)} style={inputStyle}/>:<input value={reference} onChange={e=>setReference(e.target.value)} style={inputStyle} placeholder="Reference"/>}</div>{paymentMethod==='CREDIT'&&<input value={reference} onChange={e=>setReference(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Reference"/>}<input value={notes} onChange={e=>setNotes(e.target.value)} style={{...inputStyle,marginTop:6}} placeholder="Notes"/><button disabled={saving} type="submit" style={{...button('#0284c7'),width:'100%',marginTop:6}}>{saving?'Saving…':'Save Expense'}</button></form>
    <section style={card}><div style={{...sectionTitle,display:'flex',justifyContent:'space-between',gap:6}}><span>Accounting Expense Ledger</span><span style={{fontSize:8,color:'#64748b'}}>Current month · {currentMonthStart} → {currentMonthEnd}</span></div><div style={{display:'flex',gap:5,flexWrap:'wrap',marginBottom:7}}>{(['ALL','FEED','OPEX'] as LedgerFilter[]).map(f=><button key={f} onClick={()=>setLedgerFilter(f)} style={{...smallButton,background:ledgerFilter===f?'#0ea5e9':'#1e293b',color:'#fff'}}>{f}</button>)}<div style={{display:'flex',alignItems:'center',gap:4,flex:1,minWidth:150,background:'#1e293b',border:'1px solid #334155',padding:'4px 6px',borderRadius:4}}><Search size={11} color="#94a3b8"/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search ledger…" style={{...inputStyle,border:0,padding:0,background:'transparent'}}/></div><button type="button" onClick={()=>saveLedgerCsv(`Accounting Expense Ledger — ${ledgerFilter}`,filteredExpenses,currentMonthStart,currentMonthEnd,{'Active Expense Total':filteredExpenses.reduce((s,t)=>s+activeAmount(t),0)})} style={smallButton}>Save CSV</button><button type="button" onClick={()=>printLedger(`Accounting Expense Ledger — ${ledgerFilter}`,filteredExpenses,currentMonthStart,currentMonthEnd,{'Active Expense Total':filteredExpenses.reduce((s,t)=>s+activeAmount(t),0)})} style={smallButton}><Printer size={11}/> Print</button></div><div style={{...ledgerLine,color:'#64748b',fontSize:8,fontWeight:800,textTransform:'uppercase',borderBottom:'1px solid #1f2937',padding:'0 8px 5px'}}><span style={{width:76,flex:'0 0 76px'}}>Date</span><span style={ledgerEllipsis}>Particulars</span><span style={{...ledgerEllipsis,flexBasis:100}}>Counterparty</span><span style={{...ledgerEllipsis,flexBasis:100}}>Reference</span><span style={{width:76,flex:'0 0 76px'}}>Status</span><span style={{width:118,flex:'0 0 118px',textAlign:'right'}}>Amount</span></div>{loading?<div style={empty}>Loading persistent ledger…</div>:filteredExpenses.slice(0,100).map(r=>{const isVoid=r.status==='VOID',reason=isVoid?voidReasonFromNotes(r.notes):'',editable=!['VOID','PAID','RECEIVED'].includes(String(r.status));return <div key={r.id} style={{...row,color:isVoid?'#f87171':'#fff',background:isVoid?'rgba(239,68,68,.06)':'transparent',borderLeft:isVoid?'2px solid #ef4444':undefined}}><div style={{...ledgerLine,textDecoration:isVoid?'line-through':'none'}}><span style={{width:76,flex:'0 0 76px'}}>{r.date?.slice(0,10)||'—'}</span><span title={`${r.sub_category||r.category}${r.custom_specification?` — ${r.custom_specification}`:''}`} style={ledgerEllipsis}>{r.sub_category||r.category}{r.custom_specification?` — ${r.custom_specification}`:''}</span><span title={r.vendor_name||r.counterparty||''} style={{...ledgerEllipsis,flexBasis:100}}>{r.vendor_name||r.counterparty||'—'}</span><span title={r.reference||''} style={{...ledgerEllipsis,flexBasis:100}}>{r.reference||'—'}</span><span style={{width:70,flex:'0 0 70px',fontWeight:800}}>{r.status||'RECORDED'}</span><strong style={{width:118,flex:'0 0 118px',textAlign:'right'}}>{money(r.amount)}</strong></div>{isVoid?<span title={reason||'Reason recorded in audit trail'} style={{...voidReasonStyle,maxWidth:190}}>VOID: {reason||'See audit trail'}</span>:<><>{editable&&<button onClick={()=>setEditTarget(r)} style={smallButton}><Edit3 size={10}/></button>}</><button onClick={()=>setVoidTarget(r)} style={{...smallButton,color:'#f87171'}}><Ban size={10}/></button></>}</div>})}{!loading&&filteredExpenses.length===0&&<div style={empty}>No expenses match this view.</div>}</section>
   </div>
  </div>
  <section style={{...card,marginTop:10}}>
   <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8,flexWrap:'wrap',marginBottom:8}}><div><div style={{fontSize:12,fontWeight:900}}>Financial Running Status</div><div style={{fontSize:9,color:'#64748b'}}>Default: beginning of farm operations through today. VOID entries remain visible in ledgers but are excluded here.</div></div><div style={{display:'flex',gap:5,flexWrap:'wrap'}}>{(['ALL','MONTH','CUSTOM'] as const).map(v=><button type="button" key={v} onClick={()=>setStatusPeriodMode(v)} style={{...smallButton,background:statusPeriodMode===v?'#334155':'#1e293b',color:'#fff'}}>{v==='ALL'?'Operations to Date':v==='MONTH'?'Month':'Custom'}</button>)}</div></div>
   {statusPeriodMode==='MONTH'&&<div style={{marginBottom:8}}><input type="month" value={statusMonth} onChange={e=>setStatusMonth(e.target.value)} style={{...inputStyle,width:160}}/></div>}
   {statusPeriodMode==='CUSTOM'&&<div style={{display:'flex',gap:6,alignItems:'center',marginBottom:8,flexWrap:'wrap'}}><input type="date" value={statusStart} onChange={e=>setStatusStart(e.target.value)} style={{...inputStyle,width:150}}/><span style={{fontSize:9,color:'#64748b'}}>to</span><input type="date" value={statusEnd} onChange={e=>setStatusEnd(e.target.value)} style={{...inputStyle,width:150}}/></div>}
   <div style={{fontSize:9,color:'#94a3b8',marginBottom:7}}>Period: {statusBounds.start==='0001-01-01'?'Farm inception':statusBounds.start} → {statusBounds.end}</div>
   <div style={{display:'grid',gridTemplateColumns:'repeat(3,minmax(0,1fr))',gap:7,marginBottom:10}}>{[['Revenues',statusRevenue,'#34d399'],['Expenses',statusExpenses,'#f87171'],['Balance',statusBalance,statusBalance>=0?'#38bdf8':'#f87171']].map(([label,value,color])=><div key={String(label)} style={{background:'#0f172a',border:'1px solid #1f2937',borderLeft:`4px solid ${String(color)}`,borderRadius:7,padding:'9px 10px'}}><div style={{fontSize:8,color:'#94a3b8',textTransform:'uppercase',fontWeight:800}}>{String(label)}</div><div style={{fontSize:15,fontWeight:900,color:String(color),marginTop:3}}>{money(Number(value))}</div></div>)}</div>
   <div style={{fontSize:10,fontWeight:800,marginBottom:6}}>Revenue vs Expense</div>
   <div style={{display:'grid',gridTemplateColumns:'88px 1fr 120px',gap:8,alignItems:'center',fontSize:9}}><span style={{color:'#34d399',fontWeight:800}}>Revenue</span><div style={{height:16,background:'#0f172a',border:'1px solid #1f2937',borderRadius:4,overflow:'hidden'}}><div style={{height:'100%',width:`${(statusRevenue/graphMax)*100}%`,background:'#059669'}}/></div><strong style={{textAlign:'right'}}>{money(statusRevenue)}</strong><span style={{color:'#f87171',fontWeight:800}}>Expenses</span><div style={{height:16,background:'#0f172a',border:'1px solid #1f2937',borderRadius:4,overflow:'hidden'}}><div style={{height:'100%',width:`${(statusExpenses/graphMax)*100}%`,background:'#dc2626'}}/></div><strong style={{textAlign:'right'}}>{money(statusExpenses)}</strong></div>
  </section>
  {editTarget&&<div style={modalBackdrop}><form onSubmit={saveEdit} style={modalCard}><strong style={{fontSize:13}}>Edit Finance Entry #{editTarget.id}</strong><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:6,marginTop:8}}><input name="transaction_date" type="date" defaultValue={editTarget.date?.slice(0,10)} style={inputStyle}/><select name="master_category" defaultValue={editTarget.master_category||'FEED'} style={inputStyle}><option>FEED</option><option>OPEX</option></select><input name="sub_category" defaultValue={editTarget.sub_category||''} style={inputStyle}/><input name="custom_specification" defaultValue={editTarget.custom_specification||''} style={inputStyle}/><input name="quantity" type="number" step="0.001" defaultValue={editTarget.quantity??''} style={inputStyle}/><input name="unit" defaultValue={editTarget.unit||'kg'} style={inputStyle}/><input name="unit_rate" type="number" step="0.01" defaultValue={editTarget.unit_rate??''} style={inputStyle}/><input name="amount" type="number" step="0.01" defaultValue={editTarget.amount} style={inputStyle}/><input name="counterparty" defaultValue={editTarget.vendor_name||''} style={inputStyle} placeholder="Vendor"/><input name="reference" defaultValue={editTarget.reference||''} style={inputStyle} placeholder="Reference"/><select name="payment_method" defaultValue={editTarget.payment_method||'BANK'} style={inputStyle}><option>BANK</option><option>CASH</option><option>MOBILE</option><option>CREDIT</option></select><select name="status" defaultValue={editTarget.status==='PAYABLE'?'PAYABLE':'PAID'} style={inputStyle}><option>PAID</option><option>PAYABLE</option></select><input name="due_date" type="date" defaultValue={editTarget.due_date||''} style={inputStyle}/><input name="notes" defaultValue={editTarget.notes||''} style={inputStyle} placeholder="Notes"/></div><div style={{display:'flex',justifyContent:'flex-end',gap:6,marginTop:8}}><button type="button" onClick={()=>setEditTarget(null)} style={smallButton}>Cancel</button><button disabled={editSaving} type="submit" style={button('#0284c7')}>{editSaving?'Saving…':'Save Changes'}</button></div></form></div>}
  {voidTarget&&<div style={modalBackdrop}><div style={modalCard}><strong style={{color:'#ef4444'}}>Void Finance Entry #{voidTarget.id}</strong><textarea required value={voidReason} onChange={e=>setVoidReason(e.target.value)} placeholder="Reason" style={{...inputStyle,minHeight:70,marginTop:8}}/><div style={{display:'flex',justifyContent:'flex-end',gap:6,marginTop:8}}><button onClick={()=>setVoidTarget(null)} style={smallButton}>Cancel</button><button disabled={!voidReason.trim()} onClick={()=>void updateStatus(voidTarget,'VOID',voidReason)} style={button('#dc2626')}>Confirm Void</button></div></div></div>}
 </div>
}
const card:React.CSSProperties={background:'#111827',border:'1px solid #1f2937',borderRadius:8,padding:10,minWidth:0};const sectionTitle:React.CSSProperties={fontSize:11,fontWeight:800,marginBottom:7};const row:React.CSSProperties={display:'flex',alignItems:'center',gap:8,padding:'7px 8px',borderBottom:'1px solid #1a2234',fontSize:10,minWidth:0};const ledgerLine:React.CSSProperties={display:'flex',alignItems:'center',gap:8,flex:1,minWidth:0,whiteSpace:'nowrap'};const ledgerEllipsis:React.CSSProperties={flex:'1 1 0',minWidth:0,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'};const voidReasonStyle:React.CSSProperties={fontSize:8,color:'#fca5a5',fontWeight:800,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'};const empty:React.CSSProperties={padding:14,color:'#64748b',fontSize:10,textAlign:'center'};const modalBackdrop:React.CSSProperties={position:'fixed',inset:0,background:'rgba(0,0,0,.72)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:1000,padding:16};const modalCard:React.CSSProperties={background:'#111827',border:'1px solid #334155',borderRadius:8,padding:16,width:'min(720px,100%)',maxHeight:'90vh',overflowY:'auto'};
