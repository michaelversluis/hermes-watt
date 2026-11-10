import assert from 'node:assert/strict'
import React, {act, StrictMode} from 'react'
import {createRoot} from 'react-dom/client'
import {QueryClient, QueryClientProvider} from '@tanstack/react-query'
import {ExperimentPanel} from '../desktop/plugin.js'

const tick = () => new Promise(resolve => setTimeout(resolve, 20))
const deferred = () => {let resolve;const promise=new Promise(r=>{resolve=r});return {promise,resolve}}
const button = (el,label) => [...el.querySelectorAll('button')].find(n=>n.textContent===label)

async function fixture({post, initial={job:null,configured:true,model:'test'}}={}) {
 const calls=[]
 const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:Infinity},mutations:{retry:false}}})
 const state={value:initial}
 const ctx={rest:async(path,options={})=>{calls.push({path,...options});if(options.method==='POST')return post(path,options,state);return state.value}}
 const el=document.createElement('div');document.body.append(el)
 const root=createRoot(el)
 let completed=0
 const render=async(profile='first')=>{await act(async()=>{root.render(<StrictMode><QueryClientProvider client={client}><ExperimentPanel key={profile} ctx={ctx} scope={[profile,0]} onComplete={()=>{completed++}}/></QueryClientProvider></StrictMode>);await tick()});await act(tick)}
 const close=async()=>{await act(async()=>root.unmount());client.clear();el.remove()}
 await render()
 return {el,client,ctx,state,calls,render,close,completed:()=>completed}
}

// Explicit consent, synchronous double-click, fixed payload, cancellation and completion refresh.
const pending=deferred()
const f=await fixture({post:async(path,options,state)=>{
 if(path.endsWith('/cancel')){state.value={...state.value,job:{...state.value.job,status:'cancelling'}};return {job:state.value.job}}
 await pending.promise
 state.value={...state.value,job:{id:options.body.request_id,status:'running',phase:'warmup',done:0,total:10}}
 return {job:state.value.job}
}})
assert(button(f.el,'Test a lower-energy approach').disabled)
await act(async()=>f.el.querySelector('input[type=checkbox]').click())
assert(!button(f.el,'Test a lower-energy approach').disabled)
await act(async()=>{const b=button(f.el,'Test a lower-energy approach');b.click();b.click();await tick()})
assert.equal(f.calls.filter(c=>c.method==='POST').length,1)
const payload=f.calls.find(c=>c.method==='POST').body
assert.deepEqual(Object.keys(payload).sort(),['consent','repetitions','request_id','workload'])
assert.equal(payload.consent,true)
assert.equal(payload.workload,'tickets')
assert.equal(payload.repetitions,5)
assert.match(payload.request_id,/^[a-f0-9]{32}$/)
assert(button(f.el,'Testing…').disabled)
await act(async()=>{pending.resolve();await tick()});await act(tick)
assert(f.el.textContent.includes('Warming up both approaches'))
await act(async()=>{button(f.el,'Stop test').click();await tick()});await act(tick)
assert(button(f.el,'Stopping…').disabled)
await act(async()=>f.client.setQueryData(['hermes-watt','first',0,'experiment'],{...f.state.value,job:{...f.state.value.job,status:'completed'}}))
await act(tick)
assert.equal(f.completed(),1)
await f.close()

// Late POST resolution after profile navigation cannot refresh the old profile.
const late=deferred()
const g=await fixture({post:()=>late.promise})
await act(async()=>g.el.querySelector('input[type=checkbox]').click())
await act(async()=>{button(g.el,'Test a lower-energy approach').click();await tick()})
await g.render('second')
assert(!g.el.querySelector('input[type=checkbox]').checked)
assert(button(g.el,'Test a lower-energy approach').disabled)
const before=g.calls.length
await act(async()=>{late.resolve({job:{status:'running'}});await tick()});await act(tick)
assert.equal(g.calls.length,before)
assert.equal(g.completed(),0)
await g.close()

// Failed and interrupted jobs stop spinners and preserve the prior report messaging.
for(const status of ['failed','interrupted','cancelled']){
 const h=await fixture({initial:{configured:true,model:'test',job:{id:'a',status}}})
 assert(h.el.textContent.includes('previous result is preserved'))
 assert(!button(h.el,'Testing…'))
 await h.close()
}
console.log('Desktop interaction: consent, double-click, bounded payload, cancel, StrictMode completion, profile change and failed jobs — passed')
