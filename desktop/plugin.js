import { createElement as h, useState } from 'react'
import { host, useQuery, useValue, ROUTES_AREA, SIDEBAR_NAV_AREA, PALETTE_AREA, gatewayActivationEpoch } from '@hermes/plugin-sdk'

const styles = {
  page: { color: 'var(--ui-text-primary)', maxWidth: 1100, margin: '0 auto', padding: '32px 28px', fontFamily: 'inherit' },
  muted: { color: 'var(--ui-text-secondary)', lineHeight: 1.6 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 16 },
  card: { border: '1px solid var(--ui-stroke-secondary)', borderRadius: 16, padding: 22, marginBottom: 18 },
  label: { fontSize: 12, letterSpacing: 1.2, textTransform: 'uppercase', color: 'var(--ui-text-secondary)', marginBottom: 12 },
  value: { fontSize: 32, fontWeight: 650, lineHeight: 1.2, letterSpacing: -1 },
  button: { padding: '9px 14px', borderRadius: 10, border: '1px solid var(--ui-stroke-secondary)', cursor: 'pointer', color: 'inherit', background: 'transparent' },
  badge: { display: 'inline-block', fontSize: 11, padding: '4px 8px', borderRadius: 6, background: 'color-mix(in srgb, var(--ui-accent) 13%, transparent)', color: 'var(--ui-accent)', fontWeight: 650 },
}
const fmt = (n, digits=3) => Number.isFinite(n) ? n.toLocaleString('en-US', {maximumFractionDigits: digits}) : 'Unknown'
const small = text => h('p', {style: {...styles.muted, fontSize: 12, marginBottom: 0}}, text)
const metric = (label, value, detail) => h('section', {style: styles.card}, h('div', {style: styles.label}, label), h('div', {style: styles.value}, value), small(detail))

export function Comparison({report}) {
  if (!report) return h('section', {style: styles.card}, h('h2', null, 'Can the same work use less energy?'), h('p', {style: styles.muted}, 'Run the reproducible comparison with a local model. Hermes Watt checks every answer before showing an efficiency result.'), small('No comparison has been recorded for this profile yet. Instructions: scripts/benchmark.py --help'))
  const rows = [report.baseline, report.candidate]
  const maximum = Math.max(...rows.map(r => r.median_joules || 0), 0.001)
  return h('section', {style: {...styles.card, borderColor: 'var(--ui-accent)'}},
    h('div', {style: styles.label}, 'Same task. Checked answers.'),
    h('h2', {style:{margin:'0 0 8px', fontSize:25}}, report.verdict === 'lower_energy' ? `${fmt(report.observed_reduction_percent, 1)}% lower local energy in this experiment` : 'Comparison recorded — no saving claim'),
    h('p', {style: styles.muted}, report.explanation),
    ...rows.map((r, index) => h('div', {key:r.label, style:{marginTop:20}},
      h('div', {style:{display:'flex', justifyContent:'space-between', gap:16, marginBottom:8}}, h('strong',null,r.label), h('span',null,r.median_joules === null ? "Unknown local energy" : `${fmt(r.median_joules / 3600,5)} Wh · estimated`)),
      h('div',{style:{height:12, borderRadius:8, background:'color-mix(in srgb, var(--ui-text-secondary) 12%, transparent)'}},h('div',{style:{height:'100%',borderRadius:8,width:`${Math.max(1,100*r.median_joules/maximum)}%`,background:index ? 'var(--ui-accent)' : 'var(--ui-text-secondary)'}})),
      small(`${r.passed}/${r.checked} answers correct · ${r.runs} repetitions · median ${fmt(r.median_seconds,1)}s`))),
    h('details', {style:{marginTop:22}}, h('summary',{style:{cursor:'pointer'}},'What this comparison proves'),
      small(report.scope), small(report.limitations), small(`Model: ${report.model} · Method: ${report.method}`), small(`Workload fingerprint: ${report.workload_sha256}`)))
}

export function WattPage({ctx}) {
  const profile = useValue(host.state.profile)
  useValue(host.state.gateway)
  const epoch = gatewayActivationEpoch()
  const [selected, setSelected] = useState(null)
  const overview = useQuery({queryKey:['hermes-watt',profile,epoch,'overview'], queryFn:()=>ctx.rest('/overview', {timeoutMs:10000}), retry:1, staleTime:0, gcTime:0, refetchInterval:10000, refetchIntervalInBackground:false})
  const comparison = useQuery({queryKey:['hermes-watt',profile,epoch,'comparison'], queryFn:()=>ctx.rest('/comparison', {timeoutMs:10000}), retry:1, staleTime:0, gcTime:0})
  const data=overview.data
  const receipts=data?.receipts || []
  const chosen=receipts.find(r=>r.id===selected) || receipts[0]
  return h('main',{style:styles.page},
    h('header',{style:{display:'flex',alignItems:'center',justifyContent:'space-between',gap:20,marginBottom:30}},
      h('div',null,h('div',{style:styles.label},'HERMES WATT'),h('h1',{style:{fontSize:36,fontWeight:650,letterSpacing:-1.2,margin:'0 0 10px'}},'Good work. Less waste.'),h('p',{style:styles.muted},'Understand the energy behind your tasks. Keep the quality.')),
      h('button',{style:styles.button,disabled:overview.isFetching,onClick:()=>{overview.refetch();comparison.refetch()}},overview.isFetching?'Refreshing…':'Refresh')),
    overview.isError ? h('section',{style:styles.card,role:'alert'},h('h2',null,'The energy ledger is unavailable'),h('p',{style:styles.muted},'Enable the Hermes Watt agent plugin for this profile, then refresh. Your tasks can keep running.')) : null,
    overview.isLoading ? h('p',{role:'status',style:styles.muted},'Loading local receipts…') : null,
    data ? h('div',{style:styles.grid},
      metric('Local CPU + GPU',data.summary.estimated_local_wh===null?'Unknown':`${fmt(data.summary.estimated_local_wh,5)} Wh`,`${data.summary.included_energy_windows} non-overlapping windows · estimated`),
      metric('Provider inference','Unknown','No provider energy telemetry. Local activity is not a cloud measurement.'),
      metric('Observed requests',fmt(data.summary.requests,0),`${data.summary.tasks} task receipts · linked background calls included`)) : null,
    data ? small(data.summary.scope) : null,
    data && data.accounting_complete === false ? h('p',{role:'status',style:styles.muted},'Some request events are missing. The observed count is a lower bound.') : null,
    h('div',{style:{height:24}}),
    comparison.isError ? h('section',{style:styles.card,role:'alert'},h('h2',null,'Comparison unavailable'),small('Refresh to retry. No energy saving is inferred from missing evidence.')) : h(Comparison,{report:comparison.data?.comparison}),
    h('section',{style:styles.card},h('h2',{style:{marginTop:0}},'Your task receipts'),
      receipts.length ? h('div',{style:{overflowX:'auto'}},h('table',{style:{width:'100%',borderCollapse:'collapse',fontSize:13}},
        h('thead',null,h('tr',null,...['Task','State','Requests','Local energy'].map(x=>h('th',{key:x,style:{textAlign:'left',padding:'10px 8px',color:'var(--ui-text-secondary)',fontWeight:500}},x)))),
        h('tbody',null,...receipts.map((r,i)=>h('tr',{key:r.id,style:{borderTop:'1px solid var(--ui-stroke-secondary)'}},
          h('td',{style:{padding:'12px 8px'}},h('button',{onClick:()=>setSelected(r.id),style:{...styles.button,padding:0,border:0,textAlign:'left'}},new Date(r.started*1000).toLocaleTimeString('en-GB'),h('div',{style:{fontSize:11,color:'var(--ui-text-secondary)',marginTop:4}},r.model))),
          h('td',{style:{padding:'12px 8px'}},r.status),h('td',{style:{padding:'12px 8px'}},r.requests),
          h('td',{style:{padding:'12px 8px'}},r.energy.wh===null?'Unknown':`${fmt(r.energy.wh,5)} Wh`,r.energy.wh!==null?h('div',{style:{fontSize:11,color:'var(--ui-text-secondary)'}},r.energy.overlap?'Estimated · overlapping':'Estimated'):null))))))
      : h('p',{style:styles.muted},'Run a task with Hermes Watt enabled. Its receipt will appear here. Local energy is opt-in in the plugin settings.')),
    chosen ? h('section',{style:styles.card},h('span',{style:styles.badge},'RECEIPT DETAILS'),h('p',null,`${chosen.requests} requests · ${chosen.failed_requests} failed · ${chosen.auxiliary_requests} background · ${fmt(chosen.duration_s,1)}s`),...chosen.tips.map(t=>h('p',{key:t,style:styles.muted},t)),h('details',null,h('summary',{style:{cursor:'pointer'}},'Measurement boundary'),small(chosen.energy.scope),small(chosen.energy.limitation),small(`Quality: ${chosen.quality}. Missing measurement: ${chosen.reason || 'none'}.`))) : null,
    h('footer',{style:{...styles.muted,fontSize:12,padding:'4px 0 20px'}},data?.privacy || 'Local metadata only. No prompt text, responses or telemetry uploads.'))
}

export default {
  id:'hermes-watt', name:'Hermes Watt',
  register(ctx) {
    ctx.registerMany([
      {id:'page',area:ROUTES_AREA,data:{path:'/hermes-watt'},render:()=>h(WattPage,{ctx})},
      {id:'nav',area:SIDEBAR_NAV_AREA,data:{path:'/hermes-watt',label:'Hermes Watt',codicon:'pulse'}},
      {id:'open',area:PALETTE_AREA,data:{id:'hermes-watt.open',label:'Open Hermes Watt',keywords:['energy','watt','sustainability'],run:()=>host.navigate('/hermes-watt')}}
    ])
  }
}
