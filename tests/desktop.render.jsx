import assert from 'node:assert/strict'
import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {Comparison,WattPage} from '../desktop/plugin.js'

const empty={summary:{estimated_local_wh:null,included_energy_windows:0,requests:0,tasks:0,scope:'No total AI footprint'},receipts:[],privacy:'Local only'}
function page(data){
 const client=new QueryClient()
 client.setQueryData(['hermes-watt','demo',0,'overview'],data)
 client.setQueryData(['hermes-watt','demo',0,'comparison'],{comparison:null})
 return renderToStaticMarkup(<QueryClientProvider client={client}><WattPage ctx={{rest:()=>Promise.reject(new Error('must not fetch during SSR'))}}/></QueryClientProvider>)
}
const initial=page(empty)
assert(initial.includes('Unknown'))
assert(initial.includes('No comparison has been recorded'))
assert(initial.includes('Run a task with Hermes Watt enabled'))
assert(!initial.includes('0 Wh'))
const report={verdict:'inconclusive',explanation:'Quality failed',scope:'Local only',limitations:'Estimated',model:'test',method:'test',workload_sha256:'abc',baseline:{label:'A',median_joules:null,median_seconds:2,passed:0,checked:12,runs:3},candidate:{label:'B',median_joules:null,median_seconds:1,passed:0,checked:12,runs:3}}
const unknown=renderToStaticMarkup(<Comparison report={report}/>)
assert(unknown.includes('Unknown local energy'))
assert(unknown.includes('no saving claim'))
assert(!unknown.includes('0 Wh'))
assert(!unknown.includes('NaN'))
const receipt={id:'x',started:1,status:'completed',model:'<script>unsafe()</script>',requests:2,failed_requests:1,auxiliary_requests:0,duration_s:2,quality:'not assessed',tips:['Inspect failures'],reason:null,energy:{wh:0.01,overlap:false,scope:'CPU + GPU',limitation:'Other processes included'}}
const real=page({...empty,receipts:[receipt]})
assert(real.includes('0.01 Wh'))
assert(real.includes('Inspect failures'))
assert(real.includes('&lt;script&gt;'))
assert(!real.includes('<script>unsafe'))
console.log('Desktop rendering: empty, unknown, comparison gate, receipt, escaping — passed')
